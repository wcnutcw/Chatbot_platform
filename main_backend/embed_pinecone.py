import nest_asyncio
import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path

# ENV
current_directory = os.getcwd()
print("Current Directory:", current_directory)  # พิมพ์ที่อยู่ปัจจุบัน

# ปรับเส้นทางไปยังไฟล์ .env ในโฟลเดอร์ venv
env_path = Path(current_directory).parent / 'venv' / '.env'
print("Env Path:", env_path)  # พิมพ์เส้นทางที่ไปยัง .env

load_dotenv(dotenv_path=env_path,override=True)


nest_asyncio.apply()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Embed a batch of texts
async def embed_batch(batch, model="text-embedding-3-small"):
    response = await client.embeddings.create(model=model, input=batch)
    return [item.embedding for item in response.data]

# Embed all rows in the dataframe
async def embed_all_rows(df, batch_size=100):
    # ตรวจสอบว่า df เป็น pandas DataFrame
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input data is not a pandas DataFrame")

    # สร้างข้อความจากแต่ละแถวใน DataFrame
    texts = [" ".join(map(str, row.values)) for _, row in df.iterrows()]
    
    all_embeddings = []

    # ส่งข้อความใน batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        embeddings = await embed_batch(batch)
        all_embeddings.extend(embeddings)

    return all_embeddings

# ตัวอย่างการใช้งาน
async def main():
    # สร้าง DataFrame จากข้อมูลตัวอย่าง
    data = {"column1": ["text1", "text2"], "column2": ["text3", "text4"]}
    df = pd.DataFrame(data)

    embeddings = await embed_all_rows(df)
    print(embeddings)

# รันโปรแกรม
if __name__ == "__main__":
    asyncio.run(main())
