from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from pymongo import MongoClient
from langchain_openai import ChatOpenAI
import requests
import logging
import os
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main_backend.retrival_MongoDB import retrieve_context_from_mongodb
from main_backend.retrival_Pinecone import retrieve_context_from_pinecone
from main_backend.token_reduceContext import reduce_context , count_tokens
from main_backend.Prompt import Prompt_Template

app = FastAPI()
# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["file_agent_db"]
logs_collection = db["upload_logs"]

#convert to string (ENV)
FACEBOOK_ACCESS_TOKEN : str
OPENAI_API_KEY : str

FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")

# ฟังก์ชันสำหรับส่งข้อความกลับไปยัง Facebook
async def send_facebook_message(sender_id: str, message: str):
    """Send message back to Facebook Messenger"""
    url = f"https://graph.facebook.com/v13.0/me/messages?access_token={FACEBOOK_ACCESS_TOKEN}"
    
    payload = {
        "recipient": {"id": sender_id},
        "message": {"text": message}
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            logging.error(f"Failed to send Facebook message: {response.text}")
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Error sending Facebook message: {e}")
        return False
    
# ฟังก์ชันสำหรับประมวลผลข้อความจาก chatbot
async def process_chatbot_query(sender_id: str, user_message: str):
    """Process user message through chatbot and return response"""
    try:
        session_id = f"fb_{sender_id}"
        
        # เรียกใช้ฟังก์ชัน query
        log = logs_collection.find_one({"session_id": session_id})
        if not log:
            # ใช้ session ที่มีอยู่แล้วในระบบ (session ล่าสุด)
            log = logs_collection.find_one({}, sort=[("_id", -1)])
            if not log:
                return "ขออภัยค่ะ/ครับ ขณะนี้ไม่สามารถให้คำตอบได้"
            
            print(f"Using existing session for Facebook user {sender_id}: {log.get('session_id', 'unknown')}")

        db_type = log.get("db_type")

        if db_type == "Pinecone":
            index_name = log["index_name"]
            namespace = log["namespace"]
            context = await retrieve_context_from_pinecone(user_message, index_name, namespace)
                
        elif db_type == "MongoDB":
            db_name = log["db_name"]
            collection_name = log["collection_name"]
            file_db = mongo_client[db_name]
            collection = file_db[collection_name]
            
            context_bf = await retrieve_context_from_mongodb(collection, user_message)
            num_tokens_context = count_tokens(context_bf, model="sentence-transformers/LaBSE")
            context = reduce_context(context_bf, num_tokens_context)
        else:
            return "ขออภัย เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง"

        prompt = Prompt_Template(context, user_message)

        llm = ChatOpenAI(
            temperature=0,
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY,
            streaming=False,  # ปิด streaming สำหรับ Facebook response
            callbacks=[StreamingStdOutCallbackHandler()]
        )

        response = await llm.ainvoke(prompt)
        return response.content

    except Exception as e:
        logging.error(f"Error in chatbot processing: {e}")
        return "ขออภัย เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง"

def is_message_processed(message_id: str) -> bool:
    # ตรวจสอบว่ามี message_id นี้อยู่ใน collection หรือไม่
    result = logs_collection.find_one({"message_id": message_id})
    return result is not None

def mark_message_as_processed(message_id: str):
    # บันทึก message_id ลง collection โดยไม่ซ้ำ
    if not is_message_processed(message_id):
        logs_collection.insert_one({"message_id": message_id})

@app.post('/webhook')
async def receive_message(request: Request):
    try:
        data = await request.json()
        print("DEBUG: Received Event:", data)

        if "entry" in data:
            for entry in data["entry"]:
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event["sender"]["id"]

                    # ข้าม event ที่ไม่ใช่ข้อความ
                    if any(key in messaging_event for key in ["postback", "read", "delivery"]):
                        event_type = "read" if "read" in messaging_event else "delivery" if "delivery" in messaging_event else "postback"
                        print(f"Ignored {event_type} event from user {sender_id}")
                        continue
                    
                    # ตรวจสอบว่ามีข้อความหรือไม่
                    if "message" not in messaging_event:
                        print("No message found, skipping...")
                        continue

                    user_message = messaging_event["message"].get("text", "").strip()
                    message_id = messaging_event["message"].get("mid")

                    # ข้ามข้อความเปล่า
                    if not user_message:
                        print("Empty message, skipping...")
                        continue
                    
                    # ข้ามข้อความจาก bot เอง
                    if messaging_event["message"].get("is_echo"):
                        print("Bot echo message, skipping...")
                        continue

                    # ป้องกันข้อความซ้ำ
                    if is_message_processed(message_id):
                        print(f"Duplicate message detected: {message_id}, skipping...")
                        continue

                    # บันทึกว่าข้อความนี้ถูกประมวลผลแล้ว
                    mark_message_as_processed(message_id)

                    print(f"Received message from user {sender_id}: {user_message}")

                    # ประมวลผลข้อความผ่าน chatbot
                    try:
                        bot_response = await process_chatbot_query(sender_id, user_message)
                        
                        # ส่งข้อความกลับไปยัง Facebook
                        success = await send_facebook_message(sender_id, bot_response)
                        
                        if success:
                            print(f"Successfully sent response to user {sender_id}")
                        else:
                            print(f"Failed to send response to user {sender_id}")
                            
                    except Exception as e:
                        logging.error(f"Error processing message from {sender_id}: {e}")
                        # ส่งข้อความแสดงข้อผิดพลาด
                        await send_facebook_message(sender_id, "ขออภัยค่ะ/ครับ ขณะนี้ไม่สามารถให้คำตอบได้")

        return Response(content="ok", status_code=200)
        
    except Exception as e:
        logging.error(f"Error in webhook: {e}")
        return Response(content="error", status_code=500)

# Webhook verification สำหรับ Facebook
@app.get('/webhook')
async def verify_webhook(request: Request):
    verify_token = request.query_params.get('hub.verify_token')
    challenge = request.query_params.get('hub.challenge')
    
    if verify_token == FACEBOOK_ACCESS_TOKEN:  
        return Response(content=challenge, status_code=200)
    else:
        return Response(content="Invalid verification token", status_code=403)