import nest_asyncio
import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# ENV
load_dotenv()

nest_asyncio.apply()


client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def embed_batch(batch, model="text-embedding-3-small"):
    response = await client.embeddings.create(model=model, input=batch)
    return [item.embedding for item in response.data]

async def embed_all_rows(df, batch_size=100):
    texts = [" ".join(map(str, row.values)) for _, row in df.iterrows()]
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        embeddings = await embed_batch(batch)
        all_embeddings.extend(embeddings)

    return all_embeddings