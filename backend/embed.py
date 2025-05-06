import os
import logging
from pinecone import Pinecone
from openai import AsyncOpenAI
from dotenv import load_dotenv
import asyncio

#ENV
load_dotenv()

# Pinecone setup (ensure correct initialization)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
pc = Pinecone(api_key=PINECONE_API_KEY, environment= PINECONE_ENV)


# OpenAI API key setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def embed_batch(batch, model="text-embedding-3-small"):
    try:
        response = await client.embeddings.create(model=model, input=batch)
        if hasattr(response, "data") and response.data:
            return [item.embedding for item in response.data]
        else:
            raise ValueError("No 'data' found or 'data' is empty.")
    except Exception as e:
        logging.error(f"Error in embedding batch: {e}")
        return []
    
async def batch_process_embedding_async(text_list, model="text-embedding-3-small", batch_size=100):
    tasks = []
    for i in range(0, len(text_list), batch_size):
        batch = text_list[i:i + batch_size]
        tasks.append(embed_batch(batch, model=model))
    
    results = await asyncio.gather(*tasks)
    
    embeddings = []
    for batch_embeddings in results:
        embeddings.extend(batch_embeddings)

    return embeddings

async def upsert_batch(index, vectors_batch, namespace):
        try:
        # Upsert vectors to Pinecone index in parallel (no await)
            index.upsert(vectors=vectors_batch, namespace=namespace)  # Removed await here
            logging.debug(f"Successfully upserted {len(vectors_batch)} vectors.")
        except Exception as e:
            logging.error(f"Error during upsert batch: {e}")
            raise e  # Re-raise the error to handle it in the calling function

async def parallel_upsert(index, vectors, namespace, batch_size=100):
    tasks = []
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        tasks.append(upsert_batch(index, batch, namespace))
    await asyncio.gather(*tasks)

