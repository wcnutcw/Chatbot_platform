import streamlit as st
import requests
from pymongo import MongoClient
import pinecone

st.title("📂 Upload your files and Ask Questions!")

db_type = st.selectbox("Select Database Type", ["Pinecone", "MongoDB"])

session_ready = False
show_file_uploader = True

index_name = None
namespace = None
db_name = None
collection_name = None

if db_type == "Pinecone":
    PINECONE_API_KEY = st.text_input("Pinecone API Key:", type="password")
    PINECONE_ENV = st.text_input("Pinecone Environment:", value="us-west1-gcp")

    create_new_pinecone = st.radio(
        "Do you want to create a new Pinecone index or select existing?",
        ("Select existing", "Create new")
    )

    indexes = []
    if PINECONE_API_KEY and PINECONE_ENV:
        try:
            pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
            indexes = pinecone.list_indexes()
        except Exception as e:
            st.error(f"Error connecting to Pinecone: {e}")
            indexes = []

    if create_new_pinecone == "Select existing":
        if indexes:
            index_name = st.selectbox("Select Pinecone Index:", indexes)
            show_file_uploader = False  # ไม่แสดง uploader เพราะเลือกฐานข้อมูลที่มีอยู่จริง
        else:
            st.warning("No Pinecone indexes found in your account.")
            index_name = None
            show_file_uploader = True  # ต้องอัปโหลดไฟล์ถ้ายังไม่มี index
    else:
        index_name = st.text_input("Pinecone Index Name:")
        show_file_uploader = True  # สร้างใหม่ ต้องอัปโหลดไฟล์

    namespace = st.text_input("Pinecone Namespace:", value="default-namespace")

elif db_type == "MongoDB":
    MONGO_URI = st.text_input("MongoDB Connection URI:", value="mongodb://localhost:27017")

    create_new = st.radio("Do you want to create a new database and collection or select existing ones?",
                          ("Select existing", "Create new"))

    try:
        client = MongoClient(MONGO_URI)
        if create_new == "Select existing":
            db_list = client.list_database_names()
            if db_list:
                db_name = st.selectbox("Select MongoDB Database:", db_list)
            else:
                db_name = None

            if db_name:
                db = client[db_name]
                collection_list = db.list_collection_names()
                if collection_list:
                    collection_name = st.selectbox("Select MongoDB Collection:", collection_list)
                else:
                    collection_name = None
                show_file_uploader = False  # เลือกฐานข้อมูลที่มีอยู่จริงไม่ต้องอัปโหลดไฟล์
            else:
                collection_name = None
                show_file_uploader = True
        else:
            db_name = st.text_input("Enter new MongoDB Database Name:")
            collection_name = st.text_input("Enter new MongoDB Collection Name:")
            show_file_uploader = True
    except Exception as e:
        st.error(f"Cannot connect to MongoDB: {e}")
        db_name = None
        collection_name = None
        show_file_uploader = True

# แสดง uploader เฉพาะกรณี show_file_uploader == True
if show_file_uploader:
    uploaded_files = st.file_uploader(
        "Upload files (CSV, Excel, PDF, Word, Images)",
        type=["csv", "xlsx", "pdf", "docx", "png", "jpg"],
        accept_multiple_files=True
    )
else:
    uploaded_files = None

# ปุ่ม Start Query Session เมื่อเลือกฐานข้อมูลที่มีอยู่หรือไม่มีไฟล์อัปโหลด
if (not uploaded_files) or (not show_file_uploader):
    if db_type == "Pinecone":
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
                    st.success("Session started! You can now ask questions.")
                    session_ready = True
                else:
                    st.error(f"Failed to start session: {res.status_code} {res.text}")
        else:
            st.info("Please select or enter a Pinecone index name.")

    elif db_type == "MongoDB":
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
                    st.success("Session started! You can now ask questions.")
                    session_ready = True
                else:
                    st.error(f"Failed to start session: {res.status_code} {res.text}")
        else:
            st.info("Please select or enter MongoDB database and collection.")

# ปุ่ม Upload and Process Files เมื่อมีไฟล์อัปโหลดและ uploader โชว์
if show_file_uploader and uploaded_files:
    if st.button("Upload and Process Files"):
        multipart_files = [
            ("files", (file.name, file.getvalue())) for file in uploaded_files
        ]

        data = {"db_type": db_type}
        if db_type == "Pinecone":
            if not index_name:
                st.error("Please select or enter a Pinecone index name.")
                st.stop()
            data.update({
                "index_name": index_name,
                "namespace": namespace
            })
        elif db_type == "MongoDB":
            if not db_name or not collection_name:
                st.error("Please select or enter MongoDB database and collection.")
                st.stop()
            data.update({
                "db_name": db_name,
                "collection_name": collection_name
            })

        res = requests.post(
            "http://localhost:8000/upload",
            files=multipart_files,
            data=data
        )

        if res.status_code == 200:
            session_id = res.json()["session_id"]
            st.session_state.session_id = session_id
            st.success("Files uploaded successfully! Session ready.")
            session_ready = True
        else:
            st.error(f"Upload failed. Status code: {res.status_code}, Response: {res.text}")

# แสดงช่องถามคำถามเมื่อ session พร้อม
if "session_id" in st.session_state or session_ready:
    question = st.text_input("Ask a question about your data:")
    if st.button("Ask"):
        res = requests.post(
            "http://localhost:8000/query",
            params={
                "session_id": st.session_state.session_id,
                "question": question
            }
        )
        if res.status_code == 200:
            st.write("Answer:")
            st.success(res.json()["response"])
        else:
            st.error("Query failed.")
