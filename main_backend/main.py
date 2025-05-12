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

current_directory = os.getcwd()
print("Current Directory:", current_directory)  # พิมพ์ที่อยู่ปัจจุบัน

# ปรับเส้นทางไปยังไฟล์ .env ในโฟลเดอร์ venv
env_path = Path(current_directory).parent / 'venv' / '.env'
print("Env Path:", env_path)  # พิมพ์เส้นทางที่ไปยัง .env

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
            model="gpt-4",
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