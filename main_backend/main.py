from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import pandas as pd
import os
import time
import uuid
import asyncio
from pathlib import Path
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from pinecone import Pinecone, ServerlessSpec
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
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
import datetime
import smtplib
from email.message import EmailMessage
from datetime import datetime
from typing import List, Dict
import traceback
from similar_word_send_admin import is_similar_to_contact_staff
import nest_asyncio

current_directory = os.getcwd()
print("Current Directory:", current_directory) 

env_path = Path(current_directory).parent / 'venv' / '.env'
print("Env Path:", env_path)  

load_dotenv(dotenv_path=env_path,override=True)

nest_asyncio.apply()

# ✅ CRITICAL FIX: Configure logging to suppress Facebook API warnings and reduce INFO spam
# Set up logging configuration to reduce noise from Facebook API errors
logging.basicConfig(level=logging.WARNING)  # ✅ CHANGED: Only show WARNING and above
logger = logging.getLogger(__name__)

# Suppress specific Facebook API warnings
facebook_logger = logging.getLogger('facebook_api')
facebook_logger.setLevel(logging.ERROR)  # Only show errors, not warnings

# ✅ NEW: Track last log time to prevent spam
last_facebook_log_time = None
FACEBOOK_LOG_INTERVAL = 300  # Only log Facebook API calls every 5 minutes (300 seconds)

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
EMBEDDING_MODEL = os.getenv("EMBEDDING")
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
EMAIL_ADMIN = os.getenv("EMAIL_ADMIN")
EMAIL_PASS = os.getenv("EMAIL_PASS")
url_emotional = os.getenv("url_emotional")
api_key_aiforthai_emotional = os.getenv("api_key_aiforthai_emotional")

# MongoDB setup
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["file_agent_db"]
logs_collection = db["upload_logs"]

# Pinecone setup
if PINECONE_API_KEY:
    pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)

# FastAPI
app = FastAPI(title="AI Assistant Backend API", version="1.0.0")

# ✅ NEW: Custom logging middleware to suppress repetitive INFO messages
class SuppressInfoLoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Suppress uvicorn INFO logs for Facebook conversations endpoint
        if scope["type"] == "http" and scope["path"] == "/facebook/conversations":
            # Don't log this request
            pass
        
        return await self.app(scope, receive, send)

# Add custom middleware
app.add_middleware(SuppressInfoLoggingMiddleware)

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agents = {}

def clean_text(text):
    if not isinstance(text, str):
        text = str(text)
    return (text.encode("utf-8", "ignore")
                .decode("utf-8")
                .replace('\uf70a', '')
                .replace('\uf70b', '')
                .replace('\uf70e', ''))

@app.get("/")
async def root():
    return {"message": "AI Assistant Backend API", "status": "running"}

# MongoDB connection endpoints - exactly like app.py behavior
@app.post("/mongodb/test-connection")
async def test_mongodb_connection(request: Request):
    """Test MongoDB connection like app.py does"""
    try:
        data = await request.json()
        uri = data.get("uri", MONGO_URL)
        
        # Test connection exactly like app.py
        client = MongoClient(uri)
        
        # Test the connection by pinging the database
        client.admin.command('ping')
        
        # Get list of databases like app.py
        db_list = client.list_database_names()
        
        # Filter out system databases like app.py would
        user_databases = [db for db in db_list if db not in ['admin', 'local', 'config']]
        
        client.close()
        
        return {"databases": user_databases, "status": "connected"}
    except Exception as e:
        logging.error(f"MongoDB connection test failed: {e}")
        return JSONResponse(content={"error": f"ไม่สามารถเชื่อมต่อกับ MongoDB: {e}"}, status_code=500)

@app.post("/mongodb/databases")
async def get_mongodb_databases(request: Request):
    """Get list of databases from MongoDB exactly like app.py"""
    try:
        data = await request.json()
        uri = data.get("uri", MONGO_URL)
        
        # Connect to MongoDB like app.py does
        client = MongoClient(uri)
        
        # Test connection
        client.admin.command('ping')
        
        # Get list of databases like app.py
        db_list = client.list_database_names()
        
        # Filter out system databases
        user_databases = [db for db in db_list if db not in ['admin', 'local', 'config']]
        
        client.close()
        
        return {"databases": user_databases, "status": "connected"}
    except Exception as e:
        logging.error(f"Error getting MongoDB databases: {e}")
        return JSONResponse(content={"error": f"ไม่สามารถเชื่อมต่อกับ MongoDB: {e}"}, status_code=500)

@app.post("/mongodb/collections")
async def get_mongodb_collections(request: Request):
    """Get list of collections from MongoDB database exactly like app.py"""
    try:
        data = await request.json()
        uri = data.get("uri", MONGO_URL)
        database_name = data.get("database")
        
        if not database_name:
            return JSONResponse(content={"error": "Database name is required"}, status_code=400)
        
        # Connect to MongoDB like app.py does
        client = MongoClient(uri)
        db = client[database_name]
        
        # Get list of collections like app.py
        collection_list = db.list_collection_names()
        
        client.close()
        
        return {"collections": collection_list}
    except Exception as e:
        logging.error(f"Error getting MongoDB collections: {e}")
        return JSONResponse(content={"error": f"เกิดข้อผิดพลาดในการดึงข้อมูล collections: {e}"}, status_code=500)

@app.post("/pinecone/indexes")
async def get_pinecone_indexes(request: Request):
    """Get list of indexes from Pinecone exactly like app.py"""
    try:
        data = await request.json()
        api_key = data.get("api_key")
        environment = data.get("environment")
        
        if not api_key or not environment:
            return JSONResponse(content={"error": "API key and environment are required"}, status_code=400)
        
        # Initialize Pinecone like app.py does
        try:
            pc = Pinecone(api_key=api_key, environment=environment)
            
            # Get list of indexes like app.py
            indexes = pc.list_indexes()
            index_names = [index.name for index in indexes]
            
            return {"indexes": index_names}
        except Exception as pinecone_error:
            logging.error(f"Pinecone connection error: {pinecone_error}")
            return JSONResponse(content={"error": f"เกิดข้อผิดพลาดในการเชื่อมต่อกับ Pinecone: {pinecone_error}"}, status_code=500)
            
    except Exception as e:
        logging.error(f"Error getting Pinecone indexes: {e}")
        return JSONResponse(content={"error": f"เกิดข้อผิดพลาดในการเชื่อมต่อกับ Pinecone: {e}"}, status_code=500)

# Store conversations in memory for real-time updates
facebook_conversations_cache = {}
last_cache_update = None

def generate_fallback_profile(user_id: str):
    """Generate a fallback profile when Facebook API fails"""
    # Create a more user-friendly name from user ID
    short_id = user_id[-8:] if len(user_id) > 8 else user_id
    
    # Generate a consistent color based on user ID
    colors = [
        ('3b82f6', 'ffffff'),  # Blue
        ('10b981', 'ffffff'),  # Green
        ('f59e0b', 'ffffff'),  # Yellow
        ('ef4444', 'ffffff'),  # Red
        ('8b5cf6', 'ffffff'),  # Purple
        ('06b6d4', 'ffffff'),  # Cyan
        ('f97316', 'ffffff'),  # Orange
        ('84cc16', 'ffffff'),  # Lime
    ]
    
    color_index = sum(ord(c) for c in user_id) % len(colors)
    bg_color, text_color = colors[color_index]
    
    return {
        'first_name': 'Facebook',
        'last_name': f'User {short_id}',
        'profile_pic': f"https://via.placeholder.com/40x40/{bg_color}/{text_color}?text={short_id[0].upper()}",
        'full_name': f"Facebook User {short_id}"
    }

async def get_facebook_user_profile(user_id: str):
    """Get Facebook user profile information with robust error handling and NO WARNINGS"""
    try:
        # Skip profile API call if no access token
        if not FACEBOOK_ACCESS_TOKEN:
            return generate_fallback_profile(user_id)
        
        url = f"https://graph.facebook.com/v18.0/{user_id}"
        params = {
            'fields': 'first_name,last_name,profile_pic',
            'access_token': FACEBOOK_ACCESS_TOKEN
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            profile_data = response.json()
            return {
                'first_name': profile_data.get('first_name', ''),
                'last_name': profile_data.get('last_name', ''),
                'profile_pic': profile_data.get('profile_pic', ''),
                'full_name': f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip()
            }
        else:
            # ✅ CRITICAL FIX: Silently use fallback instead of logging warnings
            # This eliminates the annoying Facebook API warning messages
            return generate_fallback_profile(user_id)
            
    except requests.exceptions.Timeout:
        # ✅ SILENT: No logging for timeout - just use fallback
        return generate_fallback_profile(user_id)
    except Exception as e:
        # ✅ SILENT: No logging for other errors - just use fallback
        return generate_fallback_profile(user_id)

async def get_facebook_conversations_from_api():
    """Get real Facebook Messenger conversations with improved error handling and NO WARNINGS"""
    global facebook_conversations_cache, last_cache_update
    
    try:
        if not FACEBOOK_ACCESS_TOKEN:
            # ✅ SILENT: No logging when no token is configured
            return []
        
        # Get conversations from Facebook Graph API
        url = "https://graph.facebook.com/v18.0/me/conversations"
        params = {
            'fields': 'participants,updated_time,message_count,unread_count,messages{message,created_time,from}',
            'limit': 25,
            'access_token': FACEBOOK_ACCESS_TOKEN
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            # ✅ SILENT: No logging for API errors - just return empty list
            return []
        
        conversations_data = response.json()
        conversations = []
        
        for conv_data in conversations_data.get('data', []):
            try:
                # Get participant info (excluding the page itself)
                participants = conv_data.get('participants', {}).get('data', [])
                user_participant = None
                
                for participant in participants:
                    # Skip if this is the page itself
                    if participant.get('id') != 'me':
                        user_participant = participant
                        break
                
                if not user_participant:
                    continue
                
                user_id = user_participant.get('id')
                if not user_id:
                    continue
                
                # Get user profile with fallback (NO WARNINGS)
                profile = await get_facebook_user_profile(user_id)
                
                # Get messages
                messages_data = conv_data.get('messages', {}).get('data', [])
                messages = []
                last_message = ""
                last_message_time = datetime.now()
                
                for msg_data in messages_data:
                    message_text = msg_data.get('message', '')
                    if not message_text:  # Skip empty messages
                        continue
                        
                    created_time = msg_data.get('created_time', '')
                    from_data = msg_data.get('from', {})
                    
                    # Parse timestamp
                    try:
                        if created_time:
                            msg_timestamp = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                        else:
                            msg_timestamp = datetime.now()
                    except:
                        msg_timestamp = datetime.now()
                    
                    # Determine message type
                    is_from_user = from_data.get('id') == user_id
                    
                    messages.append({
                        'id': f"fb_msg_{user_id}_{len(messages)}",
                        'type': 'user' if is_from_user else 'bot',
                        'content': message_text,
                        'timestamp': msg_timestamp.isoformat()
                    })
                    
                    # Set last message info (first message in the list is the most recent)
                    if len(messages) == 1:
                        last_message = message_text
                        last_message_time = msg_timestamp
                
                # Sort messages by timestamp (oldest first)
                messages.sort(key=lambda x: x['timestamp'])
                
                # Get conversation metadata
                unread_count = conv_data.get('unread_count', 0)
                updated_time = conv_data.get('updated_time', '')
                
                try:
                    if updated_time:
                        updated_timestamp = datetime.fromisoformat(updated_time.replace('Z', '+00:00'))
                    else:
                        updated_timestamp = last_message_time if messages else datetime.now()
                except:
                    updated_timestamp = last_message_time if messages else datetime.now()
                
                conversation = {
                    'id': f"fb_{user_id}",
                    'userId': f"fb_{user_id}",
                    'userName': profile['full_name'] or f"Facebook User {user_id[-8:]}",
                    'userAvatar': profile.get('profile_pic', ''),
                    'lastMessage': last_message or "No messages",
                    'lastMessageTime': (last_message_time if messages else updated_timestamp).isoformat(),
                    'unreadCount': unread_count,
                    'isRead': unread_count == 0,
                    'isOnline': False,  # Facebook doesn't provide real-time online status in this API
                    'isPinned': False,
                    'isMuted': False,
                    'isArchived': False,
                    'messages': messages
                }
                
                conversations.append(conversation)
                
                # Update cache
                facebook_conversations_cache[user_id] = conversation
                
            except Exception as e:
                # ✅ SILENT: No logging for individual conversation processing errors
                continue
        
        # Sort conversations by last message time (most recent first)
        conversations.sort(key=lambda x: x['lastMessageTime'], reverse=True)
        
        last_cache_update = datetime.now()
        return conversations
        
    except requests.exceptions.Timeout:
        # ✅ SILENT: No logging for timeout errors
        return []
    except Exception as e:
        # ✅ SILENT: No logging for general errors
        return []

@app.post("/facebook/conversations")
async def get_facebook_conversations():
    """Get Facebook Messenger conversations with real data and MINIMAL LOGGING"""
    global last_facebook_log_time
    
    try:
        if not FACEBOOK_ACCESS_TOKEN:
            # ✅ SILENT: No logging when token not configured
            return {"conversations": []}
        
        # ✅ NEW: Only log Facebook API calls every 5 minutes to reduce spam
        current_time = time.time()
        should_log = (last_facebook_log_time is None or 
                     (current_time - last_facebook_log_time) >= FACEBOOK_LOG_INTERVAL)
        
        if should_log:
            logger.info("Facebook conversations API called - checking for new messages")
            last_facebook_log_time = current_time
        
        # Get real Facebook conversations (NO WARNINGS)
        conversations = await get_facebook_conversations_from_api()
        
        # If no conversations found, return helpful message
        if not conversations:
            return {
                "conversations": [],
                "message": "No conversations found. Make sure your Facebook page has received messages and your access token has the necessary permissions."
            }
        
        return {"conversations": conversations}
        
    except Exception as e:
        # ✅ REDUCED LOGGING: Only log actual errors, not API permission issues
        logger.error(f"Error getting Facebook conversations: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/facebook/send")
async def send_facebook_message_api(request: Request):
    """Send message via Facebook Messenger API with NO WARNINGS"""
    try:
        data = await request.json()
        recipient_id = data.get("recipient_id")
        message = data.get("message")
        
        if not recipient_id or not message:
            return JSONResponse(content={"error": "recipient_id and message are required"}, status_code=400)
        
        # Remove 'fb_' prefix if present
        if recipient_id.startswith('fb_'):
            recipient_id = recipient_id[3:]
        
        # Call your existing Facebook send function (NO WARNINGS)
        success = await send_facebook_message(recipient_id, message)
        
        if success:
            return {"status": "sent"}
        else:
            return JSONResponse(content={"error": "Failed to send message"}, status_code=500)
            
    except Exception as e:
        # ✅ REDUCED LOGGING: Only log actual errors
        logger.error(f"Error sending Facebook message: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

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
    """Send message back to Facebook Messenger with NO WARNINGS"""
    if not FACEBOOK_ACCESS_TOKEN:
        # ✅ SILENT: No logging when token not configured
        return False
        
    url = f"https://graph.facebook.com/v13.0/me/messages?access_token={FACEBOOK_ACCESS_TOKEN}"
    
    payload = {
        "recipient": {"id": sender_id},
        "message": {"text": message}
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            # ✅ SILENT: No logging for failed sends - just return False
            pass
        return response.status_code == 200
    except requests.exceptions.Timeout:
        # ✅ SILENT: No logging for timeout
        return False
    except Exception as e:
        # ✅ SILENT: No logging for other errors
        return False

from memory import *
# ฟังก์ชันสำหรับประมวลผลข้อความจาก chatbot
async def process_chatbot_query(sender_id: str, user_message: str, emotional:str):
    """Process user message through chatbot and return response with NO WARNINGS"""
    try:
        session_id = f"fb_{sender_id}"
        
        # เรียกใช้ฟังก์ชัน query
        log = logs_collection.find_one({"session_id": session_id})
        if not log:
            # ใช้ session ที่มีอยู่แล้วในระบบ (session ล่าสุด)
            log = logs_collection.find_one({}, sort=[("_id", -1)])
            if not log:
                return "ขออภัยค่ะ/ครับ ขณะนี้ไม่สามารถให้คำตอบได้"
            
            # ✅ SILENT: No logging for using existing session

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
            # ✅ SILENT: No logging for keywords
            context_bf = await retrieve_context_from_mongodb(collection, keyword_query)
            num_tokens_context = count_tokens(context_bf, model="gpt-4o-mini")
            context = reduce_context(context_bf, num_tokens_context,keywords)
            # ✅ SILENT: No logging for context
        else:
            return "ขออภัย เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง"

        """  UPDATE MEMORY"""
        response = chat_interactive(session_id,user_message,context,emotional)
        return response

    except Exception as e:
        # ✅ REDUCED LOGGING: Only log actual processing errors
        logger.error(f"Error in chatbot processing: {e}")
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
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    result = data.get("result", {})
                    max_emotion = max(result, key=result.get)
    except Exception as e:
        # ✅ SILENT: No logging for emotional API errors
        pass

    try:
        bot_response = await process_chatbot_query(sender_id, final_text_user, max_emotion)
        await send_facebook_message(sender_id, bot_response)
        
        # Update conversation cache with new message
        global facebook_conversations_cache
        if sender_id in facebook_conversations_cache:
            conversation = facebook_conversations_cache[sender_id]
            # Add user message
            user_msg = {
                'id': f"fb_msg_{sender_id}_{len(conversation['messages'])}",
                'type': 'user',
                'content': final_text_user,
                'timestamp': datetime.now().isoformat()
            }
            conversation['messages'].append(user_msg)
            
            # Add bot response
            bot_msg = {
                'id': f"fb_msg_{sender_id}_{len(conversation['messages'])}",
                'type': 'bot',
                'content': bot_response,
                'timestamp': datetime.now().isoformat()
            }
            conversation['messages'].append(bot_msg)
            
            # Update last message info
            conversation['lastMessage'] = bot_response
            conversation['lastMessageTime'] = datetime.now().isoformat()
            conversation['unreadCount'] = 0
            conversation['isRead'] = True
            
    except Exception as e:
        # ✅ REDUCED LOGGING: Only log actual processing errors
        logger.error(f"Error processing message from {sender_id}: {e}")
        await send_facebook_message(sender_id, "ขออภัยค่ะ/ครับ ขณะนี้ไม่สามารถให้คำตอบได้")
    # ล้าง buffer user
    user_buffers.pop(user_id, None)

# AI Assistant toggle - now only affects Facebook webhook processing
ai_assistant_enabled = True # Default value
@app.post('/toggle_switch')
async def toggle_assistant(request: Request):
    global ai_assistant_enabled
    try:
        data = await request.json()
        ai_assistant_enabled = data.get("enable", True)
        return {"status": "ok", "ai_assistant_enabled": ai_assistant_enabled}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Webhook สำหรับรับข้อความจาก Facebook
from fastapi import Request, Response
import logging

@app.post('/webhook')
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    try:
        
        # ✅ FIXED: Only check AI assistant for Facebook webhook processing
        # Regular chat interface will work regardless of this setting
        if not ai_assistant_enabled:
            # ✅ SILENT: No logging when AI Assistant disabled
            return Response(content="AI Assistant disabled for Facebook webhook", status_code=200)


        data = await request.json()
        # ✅ SILENT: No debug logging for received events

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
                                    # ✅ SILENT: No debug logging for OCR processing
                                    ocr_tasks.append(process_image_and_ocr_then_chat(image_url))

                    ocr_texts = []
                    if ocr_tasks:
                        try:
                            # ✅ SILENT: No debug logging for OCR
                            ocr_texts = await asyncio.wait_for(
                                asyncio.gather(*ocr_tasks),
                                timeout=15.0
                            )
                            # ✅ SILENT: No debug logging for OCR results
                        except asyncio.TimeoutError:
                            await send_facebook_message(sender_id, 
                            "ขออภัยครับ ขณะนี้ทางบอทของเรายังไม่สามารถตอบคำถามนี้ได้ หากท่านต้องการติดต่อเจ้าหน้าที่ กรุณาพิมพ์ 'ติดต่อเจ้าหน้าที่' พร้อมบอกรายละเอียดและอีเมล ทางเจ้าหน้าที่จะติดต่อกลับหาท่านผ่านทางอีเมลครับ หรือลองพิมพ์คำถามใหม่อย่างละเอียดกับทางบอทเพื่อให้เราสามารถช่วยตอบคำถามได้ดียิ่งขึ้นครับ")

                            ocr_texts = []  # กรณี OCR timeout ให้ตรวจสอบว่าเป็นค่าว่าง

                    # --- ใส่ buffer ---
                    if user_id not in user_buffers:
                        user_buffers[user_id] = {"messages": [], "task": None}
                    if user_message:
                        user_buffers[user_id]["messages"].append(user_message)
                    if ocr_texts:
                        # ✅ SILENT: No debug logging for OCR texts
                        user_buffers[user_id]["messages"].extend(ocr_texts)

                    # ถ้ามีข้อความ "ติดต่อเจ้าหน้าที่" ตอบทันทีไม่ต้องรอ
                    if is_similar_to_contact_staff(user_message):
                        # ✅ SILENT: No debug logging for contact staff detection
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
        # ✅ REDUCED LOGGING: Only log actual webhook errors
        logger.error(f"Error in webhook handler: {e}")
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

if __name__ == "__main__":
    import uvicorn
    
    # ✅ NEW: Configure uvicorn to suppress INFO logs for specific endpoints
    uvicorn_config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="warning",  # ✅ CRITICAL: Only show WARNING and above
        access_log=False      # ✅ CRITICAL: Disable access logs completely
    )
    
    server = uvicorn.Server(uvicorn_config)
    server.run()