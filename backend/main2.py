import os
import pandas as pd
import time
import uuid
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from pinecone import Pinecone, ServerlessSpec
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from tempfile import TemporaryDirectory
import logging
from dotenv import load_dotenv
from embed_2 import *
from cleansing import *

# ENV
load_dotenv()


# OpenAI API key setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Pinecone setup (ensure correct initialization)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
pc = Pinecone(api_key=PINECONE_API_KEY, environment= PINECONE_ENV)

# Embed model
embed = os.getenv("EMBEDDING")

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# API
app = FastAPI()

# MongoDB setup
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["file_agent_db"]
logs_collection = db["upload_logs"]

# POST
agents = {}

@app.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    index_name: str = Form(...),
    namespace: str = Form(...),
):
    try: 

        if not files:
            # logging.error("No files uploaded")
            return JSONResponse(content={"error": "No files uploaded"}, status_code=400)
        
        start_time = time.perf_counter()
        temp_dir = TemporaryDirectory()

        dfs = []
        for uploaded_files in files:
            file_path = os.path.join(temp_dir.name,uploaded_files.filename)
            with open(file_path,"wb") as f:
                f.write(await uploaded_files.read())
            if uploaded_files.filename.endswith(".csv"):
                df = pd.read_csv(file_path)
                dfs.append(df)
            elif uploaded_files.filename.endswith(".xlsx"):
                xls = pd.read_excel(file_path, sheet_name=None)
                for sheet_name, sheet_df in xls.items():
                    dfs.append(sheet_df)

            df_con = pd.concat(dfs, ignore_index=True)
            df_combined = data_cleansing(df_con)

        if not dfs:
            logging.error("No valid files found")
            return JSONResponse(content={"error": "No valid files found"}, status_code=400)
            
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        if index_name in pc.list_indexes().names():
            pc.delete_index(index_name)

        spec = ServerlessSpec(cloud="aws", region=os.getenv("PINECONE_ENV"))
        pc.create_index(name=index_name, dimension=1536, metric="cosine", spec=spec)
        index = pc.Index(index_name)

        embeddings = asyncio.run(embed_all_rows(df_combined))
        vectors = [{
        "id": f"vec-{i}",
                "values": embeddings[i],
                "metadata": df_combined.iloc[i].to_dict()
            } for i in range(len(embeddings))]
        
        index.upsert(vectors=vectors, namespace=namespace)

        # Log upload details to MongoDB
        session_id = str(uuid.uuid4())
        agent = create_pandas_dataframe_agent(
                ChatOpenAI(temperature=0, model="gpt-4"),
                df_combined,
                verbose=True,
                allow_dangerous_code=True 
            )
        

        agents[session_id] = agent
    
        end_time = time.perf_counter()
        processing_time = end_time - start_time
        print(f"{processing_time:.2f} second")
         # Log upload details to MongoDB
        log = {
            "session_id": session_id,
            "files": [f.filename for f in files],
            "index_name": index_name,
            "namespace": namespace,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        logs_collection.insert_one(log)

        return {"session_id": session_id}



    except Exception as e:
        logging.error(f"Error in /upload endpoit: {str(e)}")
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)

@app.post("/query")
async def query(session_id: str, question: str):
    agent = agents.get(session_id)
    if not agent:
        logging.error(f"Invalid session_id: {session_id}")
        return JSONResponse(content={"error": "Invalid session_id"}, status_code=400)

    try:
        logging.debug(f"Running query: {question}")
        question = question + " กรุณาตอบเป็นภาษาไทย"
        response = agent.run(question)
        return {"response": response}
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return JSONResponse(content={"error": "Error processing query"}, status_code=500)