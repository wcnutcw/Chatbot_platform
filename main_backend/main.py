from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
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
from send_email import *
from OCR_READ import process_image_and_ocr_then_chat
import requests
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import datetime
import smtplib
from email.message import EmailMessage
from datetime import datetime
from typing import List 
import traceback
from similar_word_send_admin import is_similar_to_contact_staff

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

#TOKEN_FACEBOOK
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")

#EMAIL
EMAIL_ADMIN = os.getenv("EMAIL_ADMIN")
EMAIL_PASS = os.getenv("EMAIL_PASS")

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

#APIKEY_AIFORTHAI
url_emotional=os.getenv("url_emotional")
api_key_aiforthai_emotional=os.getenv("api_key_aiforthai_emotional")

agents = {}

def clean_text(text):
    if not isinstance(text, str):
        text = str(text)
    return (text.encode("utf-8", "ignore")
                .decode("utf-8")
                .replace('\uf70a', '')
                .replace('\uf70b', '')
                .replace('\uf70e', ''))
    
@app.post("/upsert")
async def upsert_data(
    db_type: str = Form(...),
    db_name: str = Form(None),
    collection_name: str = Form(None),
    files: list[UploadFile] = File(...)
):
    try:
        # ตรวจสอบว่าอัปโหลดไฟล์หรือไม่
        if not files or len(files) == 0:
            return JSONResponse(content={"error": "No files uploaded"}, status_code=400)

        # เริ่มนับเวลา
        start_time = time.perf_counter()

        # แปลงไฟล์ที่อัปโหลด
        result_file = await Up_File(files)

        # --- สร้าง DataFrame จาก result_file โดยรองรับทุกกรณี ---
        if "dataframe" in result_file and result_file["dataframe"]:
            df = pd.DataFrame(result_file["dataframe"])
        elif "pages" in result_file and result_file["pages"]:
            df = pd.DataFrame({"page": result_file["pages"]})
        elif "paragraphs" in result_file and result_file["paragraphs"]:
            df = pd.DataFrame({"paragraph": result_file["paragraphs"]})
        else:
            return JSONResponse(content={"error": "No valid text data found"}, status_code=400)

        if df.empty:
            return JSONResponse(content={"error": "Uploaded file is empty"}, status_code=400)

        session_id = str(uuid.uuid4())

        if db_type == "MongoDB":
            if not db_name or not collection_name:
                return JSONResponse(content={"error": "Missing db_name or collection_name for MongoDB"}, status_code=400)

            file_db = mongo_client[db_name]
            collection = file_db[collection_name]

            # เตรียม metadata อ้างอิง row
            metadata_list = []
            for i, row in df.iterrows():
                metadata = row.to_dict()
                metadata_list.append((f"vec-{i}", metadata))

            # สร้าง embeddings และ text chunk
            embeddings, chunk_text_list = await embed_result_all(df, EMBEDDING_MODEL)

            assert len(embeddings) == len(chunk_text_list), "Embeddings and chunk_text_list length mismatch!"

            documents = []
            for idx, (embedding, raw_text) in enumerate(zip(embeddings, chunk_text_list)):
                embedding_float = [float(x) for x in embedding]
                clean_raw = clean_text(raw_text)
                row_idx = idx if idx < len(metadata_list) else 0
                vec_id, metadata = metadata_list[row_idx]
                documents.append({
                    "_id": f"{session_id}-{vec_id}_chunk{idx}",  # unique id ต่อ session
                    "embedding": embedding_float,
                    "metadata": metadata,
                    "raw_text": clean_raw
                })

            # upsert: insert ถ้าใหม่, update ถ้าซ้ำ
            for doc in documents:
                collection.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)

            # วัดเวลา
            end_time = time.perf_counter()
            processing_time = end_time - start_time
            print(f"{processing_time:.2f} seconds")

            # log
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
        logging.error(f"Error in /upsert endpoint: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)

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

        # --- สร้าง DataFrame จาก result_file โดยรองรับทุกกรณี ---
        if "dataframe" in result_file and result_file["dataframe"]:
            df = pd.DataFrame(result_file["dataframe"])
        elif "pages" in result_file and result_file["pages"]:
            df = pd.DataFrame({"page": result_file["pages"]})
        elif "paragraphs" in result_file and result_file["paragraphs"]:
            df = pd.DataFrame({"paragraph": result_file["paragraphs"]})
        else:
            return JSONResponse(content={"error": "No valid text data found"}, status_code=400)

        if df.empty:
            return JSONResponse(content={"error": "Uploaded file is empty"}, status_code=400)

        session_id = str(uuid.uuid4())

        # wait update in the future
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

            file_db = mongo_client[db_name]
            collection = file_db[collection_name]

            # เตรียมข้อมูลหลัก (metadata อ้างอิง row เดิมไว้ก่อน)
            metadata_list = []
            for i, row in df.iterrows():
                metadata = row.to_dict()
                metadata_list.append((f"vec-{i}", metadata))

            # สร้าง embeddings และได้ text chunk ทั้งหมด
            embeddings, chunk_text_list = await embed_result_all(df, EMBEDDING_MODEL)

            # (กรณีต้องการ clean database เดิมก่อน)
            collection.delete_many({})  

            # ตรวจสอบจำนวน chunk และ embedding ว่าตรงกันจริง
            assert len(embeddings) == len(chunk_text_list), "Embeddings and chunk_text_list length mismatch!"

            documents = []
            for idx, (embedding, raw_text) in enumerate(zip(embeddings, chunk_text_list)):
                embedding_float = [float(x) for x in embedding]
                clean_raw = clean_text(raw_text)
                # กำหนด id/metadata แบบ simple: เอาจาก chunk index และ metadata row ต้นทาง
                row_idx = idx if idx < len(metadata_list) else 0  # เผื่อกรณี chunk มากกว่า row
                vec_id, metadata = metadata_list[row_idx]
                documents.append({
                    "_id": f"{vec_id}_chunk{idx}",
                    "embedding": embedding_float,
                    "metadata": metadata,
                    "raw_text": clean_raw
                })

            # เพิ่มข้อมูลลง MongoDB
            if documents:
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
async def query(session_id: str, question: str,emotional:str):
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

        prompt = Prompt_Template(context,question,emotional) 

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


@app.post("/start_session")
async def start_session(
    db_type: str = Form(...),
    index_name: str = Form(None),
    namespace: str = Form(None),
    db_name: str = Form(None),
    collection_name: str = Form(None)
):
    try:
        # สร้าง session_id ใหม่
        session_id = str(uuid.uuid4())

        # ตรวจสอบชนิดฐานข้อมูลและตั้งค่า agent หรือ log ให้เหมาะสม
        if db_type == "Pinecone":
            if not index_name or not namespace:
                return JSONResponse(content={"error": "Missing index_name or namespace for Pinecone"}, status_code=400)

            # ตรวจสอบว่ามี log session เก่า หรือสร้าง agent ใหม่ที่นี่ได้เลย
            # ตัวอย่าง: สร้าง agent สำหรับ Pinecone (ถ้ามีฟังก์ชันสร้าง agent)
            # agents[session_id] = create_pinecone_agent(index_name, namespace)

            # บันทึก log ลง MongoDB (ถ้าต้องการ)
            logs_collection.insert_one({
                "session_id": session_id,
                "db_type": "Pinecone",
                "index_name": index_name,
                "namespace": namespace,
                "timestamp": pd.Timestamp.now().isoformat()
            })

        elif db_type == "MongoDB":
            if not db_name or not collection_name:
                return JSONResponse(content={"error": "Missing db_name or collection_name for MongoDB"}, status_code=400)

            # สร้าง agent สำหรับ MongoDB หรือเตรียม retrieval
            # agents[session_id] = create_mongodb_agent(db_name, collection_name)

            logs_collection.insert_one({
                "session_id": session_id,
                "db_type": "MongoDB",
                "db_name": db_name,
                "collection_name": collection_name,
                "timestamp": pd.Timestamp.now().isoformat()
            })

        else:
            return JSONResponse(content={"error": f"Unsupported db_type: {db_type}"}, status_code=400)

        return {"session_id": session_id}

    except Exception as e:
        logging.error(f"Error in /start_session: {e}")
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)

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

from memory import *
# ฟังก์ชันสำหรับประมวลผลข้อความจาก chatbot
async def process_chatbot_query(sender_id: str, user_message: str, emotional:str):
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
            
            from stopword import extract_keywords_from_query
            keywords = extract_keywords_from_query(user_message)
            keyword_query = " ".join(keywords) if keywords else user_message
            print(f"keywords : {keyword_query}")
            context_bf = await retrieve_context_from_mongodb(collection, keyword_query)
            num_tokens_context = count_tokens(context_bf, model="gpt-4o-mini")
            context = reduce_context(context_bf, num_tokens_context,keywords)
            # print(f"context : {context}")
        else:
            return "ขออภัย เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง"

        # prompt = Prompt_Template(context, user_message)

        # llm = ChatOpenAI(
        #     temperature=0,
        #     model="gpt-4o-mini",
        #     api_key=OPENAI_API_KEY,
        #     streaming=False,  # ปิด streaming สำหรับ Facebook response
        #     callbacks=[StreamingStdOutCallbackHandler()]
        # )


        """  UPDATE MEMORY"""
        response = chat_interactive(session_id,user_message,context,emotional)
        # response = await llm.ainvoke(prompt)
        return response

    except Exception as e:
        logging.error(f"Error in chatbot processing: {e}")
        return "ขออภัย เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง"



# สร้าง set เก็บ message_id ที่ประมวลผลแล้ว (ใช้ในหน่วยความจำเท่านั้น)
processed_message_ids = set()

def is_message_processed(message_id):
    """ตรวจสอบว่า message_id นี้ถูกประมวลผลแล้วหรือไม่"""
    return message_id in processed_message_ids

def mark_message_as_processed(message_id):
    """บันทึก message_id ว่าประมวลผลแล้ว"""
    processed_message_ids.add(message_id)
    
def remove_middle_spaces(text):
# ถ้าทั้งหมดเป็นตัวอักษรเว้นวรรค หรือ ตัวอักษรกับคำ (ภาษาไทย/อังกฤษ)
    return text.replace(" ", "")

from typing import Dict
user_buffers: Dict[str, Dict] = {}    # user_id: {"messages": [], "task": asyncio.Task}
async def handle_user_buffer(user_id: str, sender_id: str, background_tasks: BackgroundTasks):
    await asyncio.sleep(6)  # รอ 6 วิ
    buffer = user_buffers.get(user_id)
    if not buffer or not buffer["messages"]:
        return
    combined_texts = []
    for msg in buffer["messages"]:
        if isinstance(msg, list):
            combined_texts.extend(msg)
        else:
            combined_texts.append(msg)
    final_text_user = "\n".join(combined_texts)

    # วิเคราะห์อารมณ์ (เลือกข้อความแรก)
    max_emotion = None
    try:
        first_message = combined_texts[0] if combined_texts else ""
        if first_message:
            url = f"{url_emotional}"
            headers = {"apikey": f"{api_key_aiforthai_emotional}"}
            params = {"text": first_message}
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    result = data.get("result", {})
                    max_emotion = max(result, key=result.get)
    except Exception as e:
        logging.error(f"Error calling emotional API: {e}")

    try:
        bot_response = await process_chatbot_query(sender_id, final_text_user, max_emotion)
        await send_facebook_message(sender_id, bot_response)
    except Exception as e:
        logging.error(f"Error processing message from {sender_id}: {e}")
        await send_facebook_message(sender_id, "ขออภัยค่ะ/ครับ ขณะนี้ไม่สามารถให้คำตอบได้")
    # ล้าง buffer user
    user_buffers.pop(user_id, None)

# Webhook สำหรับรับข้อความจาก Facebook
from fastapi import Request, Response
import logging

@app.post('/webhook')
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        logging.debug(f"Received Event: {data}")  # เพิ่มการตรวจสอบข้อมูลที่ได้รับ

        if "entry" in data:
            for entry in data["entry"]:
                for messaging_event in entry.get("messaging", []):
                    if "message" not in messaging_event:
                        continue
                    if messaging_event["message"].get("is_echo"):
                        continue
                    sender_id = messaging_event["sender"]["id"]
                    user_id = sender_id
                    message_id = messaging_event["message"].get("mid")
                    
                    if message_id and is_message_processed(message_id):
                        continue
                    
                    user_message = messaging_event["message"].get("text", "").strip()
                    attachments = messaging_event["message"].get("attachments", [])
                    user_message = remove_middle_spaces(user_message)
                    
                    if message_id:
                        mark_message_as_processed(message_id)

                    # เตรียม OCR tasks ถ้ามีรูป
                    ocr_tasks = []
                    if attachments:
                        for attachment in attachments:
                            if attachment.get("type") == "image":
                                image_url = attachment["payload"].get("url")
                                if image_url:
                                    logging.debug(f"Found image attachment, processing OCR: {image_url}")  # ตรวจสอบว่ามีภาพที่ถูกส่ง
                                    ocr_tasks.append(process_image_and_ocr_then_chat(image_url))

                    ocr_texts = []
                    if ocr_tasks:
                        try:
                            logging.debug("Starting OCR processing...")
                            ocr_texts = await asyncio.wait_for(
                                asyncio.gather(*ocr_tasks),
                                timeout=15.0
                            )
                            logging.debug(f"OCR result: {ocr_texts}")
                        except asyncio.TimeoutError:
                            await send_facebook_message(sender_id, 
                            "ขออภัยครับ ขณะนี้ทางบอทของเรายังไม่สามารถตอบคำถามนี้ได้ หากท่านต้องการติดต่อเจ้าหน้าที่ กรุณาพิมพ์ 'ติดต่อเจ้าหน้าที่' พร้อมบอกรายละเอียดและอีเมล ทางเจ้าหน้าที่จะติดต่อกลับหาท่านผ่านทางอีเมลครับ หรือลองพิมพ์คำถามใหม่อย่างละเอียดกับทางบอท เพื่อให้เราสามารถช่วยตอบคำถามได้ดียิ่งขึ้นครับ")

                            ocr_texts = []  # กรณี OCR timeout ให้ตรวจสอบว่าเป็นค่าว่าง

                    # --- ใส่ buffer ---
                    if user_id not in user_buffers:
                        user_buffers[user_id] = {"messages": [], "task": None}
                    if user_message:
                        user_buffers[user_id]["messages"].append(user_message)
                    if ocr_texts:
                        logging.debug(f"Adding OCR texts to buffer: {ocr_texts}")
                        user_buffers[user_id]["messages"].extend(ocr_texts)

                    # ถ้ามีข้อความ "ติดต่อเจ้าหน้าที่" ตอบทันทีไม่ต้องรอ
                    if is_similar_to_contact_staff(user_message):
                        logging.debug(f"Detected 'contact staff' message from user: {user_message}")
                        background_tasks.add_task(send_alert_email, sender_id, user_message, 0)
                        await send_facebook_message(sender_id, 
                                                    "คำขอของท่านได้ถูกส่งไปยังเจ้าหน้าที่เรียบร้อยแล้ว หากคุณยังไม่ได้ระบุรายละเอียดกรุณาพิมพ์คำว่า 'ติดต่อเจ้าหน้าที่' พร้อมข้อมูลและอีเมลที่คุณต้องการให้ติดต่อกลับครับ ขณะนี้คุณมีคำถามเพิ่มเติมที่ต้องการสอบถามกับบอทหรือไม่ครับ?")
                        # เคลียร์ buffer นี้
                        user_buffers.pop(user_id, None)
                        return Response(content="ok", status_code=200)

                    # -- ตั้ง/รีเซต timer task สำหรับ user นี้ --
                    old_task = user_buffers[user_id].get("task")
                    if old_task:
                        old_task.cancel()
                    task = asyncio.create_task(
                        handle_user_buffer(user_id, sender_id, background_tasks)
                    )
                    user_buffers[user_id]["task"] = task

        return Response(content="ok", status_code=200)

    except Exception as e:
        logging.error(f"Error in webhook handler: {e}")
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


