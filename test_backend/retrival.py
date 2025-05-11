from langchain_openai import OpenAIEmbeddings
import os 
from openai import AsyncOpenAI
from pinecone import Pinecone

# OpenAI API key setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Pinecone setup (ensure correct initialization)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
pc = Pinecone(api_key=PINECONE_API_KEY, environment= PINECONE_ENV)

# Embed model
embed = os.getenv("EMBEDDING")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def retrieve_context_from_pinecone(question: str, index_name: str, namespace: str, top_k: int = 5):
    embedder = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    question_vector = embedder.embed_query(question)

    index = pc.Index(index_name)
    result = index.query(
        vector=question_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace
    )

    context_chunks = []
    for match in result['matches']:
        metadata = match['metadata']
        context_chunks.append(str(metadata))
    
    return "\n".join(context_chunks)