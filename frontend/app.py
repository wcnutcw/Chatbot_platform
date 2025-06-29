import streamlit as st
import requests
from pymongo import MongoClient
import pinecone
import os
from dotenv import load_dotenv
from pathlib import Path
import logging

# ตั้งค่าตำแหน่งของไฟล์ .env สำหรับโหลดตัวแปรสภาพแวดล้อม
current_directory = os.getcwd()
env_path = Path(current_directory).parent / 'venv' / '.env'
load_dotenv(dotenv_path=env_path)

# แสดงหัวข้อของหน้า
st.title("📂 Backend management UI")

# สร้าง toggle switch
enabled = st.toggle("เปิดใช้งาน AI Assistant", value=st.session_state.get("ai_assistant_enabled", False))

# ตรวจสอบว่าค่ามีการเปลี่ยนแปลงไหม
if enabled != st.session_state.get("ai_assistant_enabled", False):
    st.session_state.ai_assistant_enabled = enabled
    try:
        res = requests.post("http://localhost:8000/toggle_switch", json={"enable": enabled})
        if res.status_code == 200:
            st.success(f"สถานะ AI Assistant ถูก {'เปิดใช้งาน' if enabled else 'ปิดใช้งาน'}")
        else:
            st.error(f"ไม่สามารถอัปเดตสถานะ AI Assistant: {res.text}")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอัปเดตสถานะ AI Assistant: {e}")

# เลือกประเภทฐานข้อมูล
db_type = st.selectbox("เลือกประเภทฐานข้อมูล", ["MongoDB", "Pinecone"], key="db_type_selectbox")

# ตัวแปรสำหรับจัดการเซสชัน
session_ready = False
show_file_uploader = True
index_name = None
namespace = None
db_name = None
collection_name = None

# โหลดข้อมูลสำหรับการวิเคราะห์อารมณ์
url_emotional = os.getenv("url_emotional")
api_key_aiforthai_emotional = os.getenv("api_key_aiforthai_emotional")

# การตั้งค่า MongoDB
mongo_action_labels = {
    "เลือกข้อมูลที่มีอยู่แล้ว": "เลือกข้อมูลที่มีอยู่แล้ว",
    "สร้างที่จัดเก็บข้อมูลใหม่": "สร้างที่จัดเก็บข้อมูลใหม่",
    "อัพเดตข้อมูลเพิ่มเติม": "อัพเดตข้อมูลเพิ่มเติม"
}
mongo_action_keys = list(mongo_action_labels.keys())

if db_type == "MongoDB":
    MONGO_URI = st.text_input("MongoDB Connection URI:", value="mongodb://localhost:27017")
    action = st.radio("ต้องการดำเนินการอะไร?", mongo_action_keys)

    try:
        client = MongoClient(MONGO_URI)

        if action in ("เลือกข้อมูลที่มีอยู่แล้ว", "อัพเดตข้อมูลเพิ่มเติม"):
            db_list = client.list_database_names()
            if db_list:
                db_name = st.selectbox("เลือกฐานข้อมูล MongoDB:", db_list)
                if db_name:
                    db = client[db_name]
                    collection_list = db.list_collection_names()
                    if collection_list:
                        collection_name = st.selectbox("เลือก Collection MongoDB:", collection_list)
                    else:
                        collection_name = None
                else:
                    collection_name = None
            else:
                db_name = None
                collection_name = None

            show_file_uploader = action == "อัพเดตข้อมูลเพิ่มเติม"

        else:
            db_name = st.text_input("กรอกชื่อฐานข้อมูล MongoDB ใหม่:")
            collection_name = st.text_input("กรอกชื่อ Collection MongoDB ใหม่:")
            show_file_uploader = True

    except Exception as e:
        st.error(f"ไม่สามารถเชื่อมต่อกับ MongoDB: {e}")
        db_name = None
        collection_name = None
        show_file_uploader = True

# การตั้งค่า Pinecone
elif db_type == "Pinecone":
    PINECONE_API_KEY = st.text_input("Pinecone API Key:", type="password")
    PINECONE_ENV = st.text_input("Pinecone Environment:", value="us-west1-gcp")

    pinecone_action_labels = {
        "เลือกข้อมูลที่มีอยู่แล้ว": "เลือกข้อมูลที่มีอยู่แล้ว",
        "สร้างที่จัดเก็บข้อมูลใหม่": "สร้างที่จัดเก็บข้อมูลใหม่"
    }
    pinecone_action_keys = list(pinecone_action_labels.keys())

    create_new_pinecone = st.radio("คุณต้องการสร้าง Pinecone index ใหม่หรือเลือกที่มีอยู่แล้ว?", pinecone_action_keys)

    indexes = []
    if PINECONE_API_KEY and PINECONE_ENV:
        try:
            pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
            indexes = pinecone.list_indexes()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อกับ Pinecone: {e}")
            indexes = []

    if create_new_pinecone == "เลือกข้อมูลที่มีอยู่แล้ว":
        if indexes:
            index_name = st.selectbox("เลือก Pinecone Index:", indexes)
            show_file_uploader = False
        else:
            st.warning("ไม่พบ Pinecone indexes ในบัญชีของคุณ.")
            index_name = None
            show_file_uploader = True
    else:
        index_name = st.text_input("ชื่อ Pinecone Index:")
        show_file_uploader = True

    namespace = st.text_input("Pinecone Namespace:", value="default-namespace")

# ฟังก์ชันอัปโหลดไฟล์
if show_file_uploader:
    uploaded_files = st.file_uploader(
        "อัปโหลดไฟล์ (PDF, Word)",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )
else:
    uploaded_files = None

# การอัปเดตข้อมูลใน MongoDB
if db_type == "MongoDB" and action == "อัพเดตข้อมูลเพิ่มเติม" and uploaded_files:
    if st.button("Upload and Upsert Files"):
        multipart_files = [
            ("files", (file.name, file.getvalue())) for file in uploaded_files
        ]
        data = {
            "db_type": db_type,
            "db_name": db_name,
            "collection_name": collection_name
        }
        res = requests.post("http://localhost:8000/upsert", files=multipart_files, data=data)
        if res.status_code == 200:
            st.success("การอัปเดตข้อมูลเสร็จสมบูรณ์")
        else:
            st.error(f"ไม่สามารถอัปเดตข้อมูล: {res.status_code} - {res.text}")

# เริ่มต้นเซสชันการค้นหา
if (not uploaded_files) or (not show_file_uploader):
    if db_type == "MongoDB" and action == "เลือกข้อมูลที่มีอยู่แล้ว":
        if db_name and collection_name:
            if st.button("Start Query Session"):
                data = {
                    "db_type": db_type,
                    "db_name": db_name,
                    "collection_name": collection_name
                }
                res = requests.post("http://localhost:8000/start_session", data=data)
                if res.status_code == 200:
                    st.session_state.session_id = res.json()["session_id"]
                    st.success("เซสชันเริ่มต้น! คุณสามารถถามคำถามได้แล้ว")
                    session_ready = True
                else:
                    st.error(f"ไม่สามารถเริ่มต้นเซสชันได้: {res.status_code} {res.text}")
        else:
            st.info("กรุณาเลือกหรือกรอกชื่อฐานข้อมูลและคอลเลกชั่น MongoDB")

    elif db_type == "Pinecone":
        if index_name:
            if st.button("Start Query Session"):
                data = {
                    "db_type": db_type,
                    "index_name": index_name,
                    "namespace": namespace
                }
                res = requests.post("http://localhost:8000/start_session", data=data)
                if res.status_code == 200:
                    st.session_state.session_id = res.json()["session_id"]
                    st.success("เซสชันเริ่มต้น! คุณสามารถถามคำถามได้แล้ว")
                    session_ready = True
                else:
                    st.error(f"ไม่สามารถเริ่มต้นเซสชันได้: {res.status_code} {res.text}")
        else:
            st.info("กรุณาเลือกหรือลองใส่ชื่อ Pinecone index")

# ส่วนการถามคำถาม
if "session_id" in st.session_state or session_ready:
    question = st.text_input("ถามคำถามเกี่ยวกับข้อมูลของคุณ:")

    max_emotion = ""
    if question:
        try:
            url = f"{url_emotional}"
            headers = {"apikey": f"{api_key_aiforthai_emotional}"}
            params = {"text": question}
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    result = data.get("result", {})
                    max_emotion = max(result, key=result.get)
        except Exception as e:
            logging.error(f"เกิดข้อผิดพลาดในการเรียก API อารมณ์: {e}")

    if st.button("ถาม"):
        res = requests.post(
            "http://localhost:8000/query",
            params={
                "session_id": st.session_state.session_id,
                "question": question,
                "emotional": max_emotion
            }
        )
        if res.status_code == 200:
            st.write("คำตอบ:")
            st.success(res.json()["response"])
        else:
            st.error("การถามคำถามล้มเหลว.")
