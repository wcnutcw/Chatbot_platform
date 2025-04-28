import streamlit as st
import requests

st.title("📂 Upload your files and Ask Questions!")


uploaded_files = st.file_uploader("Upload CSV or Excel files", type=["csv", "xlsx"], accept_multiple_files=True)

index_name = st.text_input("Pinecone Index Name:", value="default-index")
namespace = st.text_input("Pinecone Namespace:", value="default-namespace")

if uploaded_files:
    if st.button("Upload and Process Files"):
        multipart_files = [
            ("files", (file.name, file.getvalue())) for file in uploaded_files
        ]
        data = {
            "index_name": index_name,
            "namespace": namespace
        }
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

# Step 2: Ask questions
if "session_id" in st.session_state:
    question = st.text_input("Ask a question about your data:")
    if st.button("Ask"):
        res = requests.post(
            "http://localhost:8000/query",
            params={"session_id": st.session_state.session_id, "question": question}
        )
        if res.status_code == 200:
            st.write("Answer:")
            st.success(res.json()["response"])
        else:
            st.error("Query failed.")
