import streamlit as st
import requests

st.title("📂 Upload your files and Ask Questions!")

# เลือกประเภท Database
db_type = st.selectbox("Select Database Type", ["Pinecone", "MongoDB"])

# กำหนด input ตามประเภทของ database
if db_type == "Pinecone":
    index_name = st.text_input("Pinecone Index Name:", value="default-index")
    namespace = st.text_input("Pinecone Namespace:", value="default-namespace")
elif db_type == "MongoDB":
    collection_name = st.text_input("MongoDB Collection Name:", value="default-collection")
    db_name = st.text_input("MongoDB Database Name:", value="default-db")

uploaded_files = st.file_uploader("Upload CSV or Excel files", type=["csv", "xlsx"], accept_multiple_files=True)

# อัปโหลดไฟล์พร้อมข้อมูล config
if uploaded_files:
    if st.button("Upload and Process Files"):
        multipart_files = [
            ("files", (file.name, file.getvalue())) for file in uploaded_files
        ]

        # เตรียมข้อมูลตาม database ที่เลือก
        data = {"db_type": db_type}
        if db_type == "Pinecone":
            data.update({
                "index_name": index_name,
                "namespace": namespace
            })
        elif db_type == "MongoDB":
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
        else:
            st.error("Upload failed.")

# ถ้ามี session แล้ว แสดงช่องถามคำถาม
if "session_id" in st.session_state:
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
