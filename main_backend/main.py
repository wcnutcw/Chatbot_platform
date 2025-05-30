from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pymongo import MongoClient
import pandas as pd
import os
import time
import uuid
import asyncio
from pathlib import Path
# from tempfile import TemporaryDirectory
# import fitz  # PyMuPDF
# from docx import Document
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from pinecone import Pinecone, ServerlessSpec
# from bson import json_util  # สำหรับ serialize object จาก MongoDB
# import json
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from fastapi.middleware.cors import CORSMiddleware
from uploadfile import *
from embed_pinecone import *
from retrival_Pinecone import *
from embed_MongoDB import *
from retrival_MongoDB import *
from Prompt import *
from token_reduceContext import *
import requests
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import datetime

current_directory = os.getcwd()
print("Current Directory:", current_directory) 

env_path = Path(current_directory).parent / 'venv' / '.env'
print("Env Path:", env_path)  

load_dotenv(dotenv_path=env_path,override=True)


nest_asyncio.apply()

# MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["file_agent_db"]
logs_collection = db["upload_logs"]

# Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)

# Embed model
EMBEDDING_MODEL = os.getenv("EMBEDDING")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")

# FastAPI
app = FastAPI()
# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agents = {}

@app.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    db_type: str = Form(...),
    index_name: str = Form(None),
    namespace: str = Form(None),
    db_name: str = Form(None),
    collection_name: str = Form(None)
):
    try:
        # ตรวจสอบว่าอัปโหลดไฟล์หรือไม่
        if not files or len(files) == 0:
            return JSONResponse(content={"error": "No files uploaded"}, status_code=400)

        # เริ่มนับเวลา
        start_time = time.perf_counter()

        # แปลงไฟล์ที่อัปโหลด
        result_file = await Up_File(files)

        # สร้าง DataFrame จากข้อมูลที่แปลง
        df = pd.DataFrame(result_file["dataframe"])

        # ตรวจสอบว่า DataFrame ว่างหรือไม่
        if df.empty:
            return JSONResponse(content={"error": "Uploaded file is empty"}, status_code=400)

        session_id = str(uuid.uuid4())

        # if db_type == "Pinecone":
        #     # ✅ เช็กว่า index_name มีค่าหรือไม่
        #     if not index_name:
        #         return JSONResponse(content={"error": "Missing index_name for Pinecone"}, status_code=400)

        #     if index_name in pc.list_indexes().names():
        #         pc.delete_index(index_name)

        #     spec = ServerlessSpec(cloud="aws", region=PINECONE_ENV)
        #     pc.create_index(name=index_name, dimension=1536, metric="cosine", spec=spec)
        #     index = pc.Index(index_name)

        #     embeddings = await embed_all_rows(df)  # ✅ สมมติว่าฟังก์ชันนี้แก้แล้ว ไม่เช็กผิด
        #     vectors = [{
        #         "id": f"vec-{i}",
        #         "values": embeddings[i],
        #         "metadata": df.iloc[i].to_dict()
        #     } for i in range(len(embeddings))]

        #     index.upsert(vectors=vectors, namespace=namespace)

        #     # Log ลง MongoDB
        #     log = {
        #         "session_id": session_id,
        #         "db_type": "Pinecone",
        #         "files": [f.filename for f in files],
        #         "index_name": index_name,
        #         "namespace": namespace,
        #         "timestamp": pd.Timestamp.now().isoformat()
        #     }
        #     logs_collection.insert_one(log)

        #     agent = create_pandas_dataframe_agent(
        #         ChatOpenAI(temperature=0, model="gpt-4"),
        #         df,
        #         verbose=True,
        #         allow_dangerous_code=True
        #     )
        #     agents[session_id] = agent

        if db_type == "MongoDB":
            if not db_name or not collection_name:
                return JSONResponse(content={"error": "Missing db_name or collection_name for MongoDB"}, status_code=400)

            # เชื่อมต่อกับ MongoDB
            file_db = mongo_client[db_name]
            collection = file_db[collection_name]

            texts = []
            metadata_list = []

            for i, row in df.iterrows():
                metadata = row.to_dict()
                text = "\n".join([f"{k}: {v}" for k, v in metadata.items()])
                texts.append(text)
                metadata_list.append((f"vec-{i}", metadata))

            # ตรวจสอบค่า null ใน DataFrame
            if df.isnull().all(axis=1).any():
                df = df.fillna('')  # หรือจะใช้ dropna() ก็ได้

            # สร้าง embeddings
            embeddings = await embed_result_all(df, EMBEDDING_MODEL)
            
            collection.delete_many({})  
            documents = []
            for (vec_id, metadata), embedding, raw_text in zip(metadata_list, embeddings, texts):
                documents.append({
                    "_id": vec_id,
                    "embedding": embedding,
                    "metadata": metadata,
                    "raw_text": raw_text
                })

            # เพิ่มข้อมูลลง MongoDB
            collection.insert_many(documents)

            # วัดเวลาที่ใช้ในการประมวลผล
            end_time = time.perf_counter()
            processing_time = end_time - start_time
            print(f"{processing_time:.2f} seconds")

            # บันทึก log การประมวลผล
            log = {
                "session_id": session_id,
                "db_type": "MongoDB",
                "files": [f.filename for f in files],
                "db_name": db_name,
                "collection_name": collection_name,
                "timestamp": pd.Timestamp.now().isoformat()
            }
            logs_collection.insert_one(log)

        else:
            return JSONResponse(content={"error": f"Unsupported db_type: {db_type}"}, status_code=400)

        return {"session_id": session_id}

    except Exception as e:
        # การจับข้อผิดพลาด
        logging.error(f"Error in /upload endpoint: {str(e)}")
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)


@app.post("/query")
async def query(session_id: str, question: str):
    try:
        log = logs_collection.find_one({"session_id": session_id})
        if not log:
            return JSONResponse(content={"error": "No matching log found"}, status_code=404)

        db_type = log.get("db_type")

        if db_type == "Pinecone":
            index_name = log["index_name"]
            namespace = log["namespace"]

            context = await retrieve_context_from_pinecone(question, index_name, namespace)
                
        elif db_type == "MongoDB":
            db_name = log["db_name"]
            collection_name = log["collection_name"]
            file_db = mongo_client[db_name]
            collection = file_db[collection_name]

            context_bf = await retrieve_context_from_mongodb(collection, question)
            num_tokens_context = count_tokens(context_bf, model="sentence-transformers/LaBSE")
            context = reduce_context(context_bf, num_tokens_context)

        else:
            return JSONResponse(content={"error": "Invalid db_type"}, status_code=400)

        prompt = Prompt_Template(context,question) 

        llm = ChatOpenAI(
            temperature=0,
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()]
        )

        async def run_async_query(prompt):
            response = await llm.ainvoke(prompt)
            return response.content
        
        response = await run_async_query(prompt)

        return {"response": response}

    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return JSONResponse(content={"error": f"Error processing query: {str(e)}"}, status_code=500)

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
    
 # Wait for future updates to enter the database
def is_message_processed(message_id):
    try:
        with open('processed_messages.txt', 'r') as file:
            processed_messages = file.readlines()
            if message_id + '\n' in processed_messages:
                return True
    except FileNotFoundError:
        pass
    return False

# Wait for editing to enter the database to store the conversation between the user.
def mark_message_as_processed(message_id):
    with open('processed_messages.txt', 'a') as file:
        file.write(message_id + '\n')
    
# Webhook สำหรับรับข้อความจาก Facebook
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