import asyncio
import os
from pathlib import Path
import textwrap
import base64
from io import BytesIO
import pandas as pd
from dotenv import load_dotenv
from openai import AsyncOpenAI
from PIL import Image
from transformers import CLIPProcessor, CLIPModel, BertTokenizer
import torch

# --- โหลดค่า .env ---
current_directory = os.getcwd()
print("Current Directory:", current_directory)

env_path = Path(current_directory).parent / 'venv' / '.env'
print("Env Path:", env_path)

load_dotenv(dotenv_path=env_path, override=True)

# --- API Keys ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")  # Huggingface token

# --- สร้าง Clients ---
client_openai = AsyncOpenAI(api_key=OPENAI_API_KEY)

# --- โหลด CLIP Model ---
cache_dir = "./my_model_cache"
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", token=HF_TOKEN, cache_dir=cache_dir)
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", token=HF_TOKEN, cache_dir=cache_dir)

# --- โหลด BERT Tokenizer สำหรับตัด token ---
bert_tokenizer = BertTokenizer.from_pretrained("bert-base-uncased", token=HF_TOKEN, cache_dir=cache_dir, use_fast=True)

# ใช้ Embedding model ตัวนี้
EMBEDDING_MODEL = "text-embedding-3-small"

MAX_TOKEN_LENGTH = 8192 # Max Token ที่ OpenAI รุ่นนี้รับได้

# ======================
# ฟังก์ชันตัดข้อความตาม Token Limit
# ======================
def safe_cut_text(text, tokenizer, max_token_len=MAX_TOKEN_LENGTH):
    tokens = tokenizer.encode(text, add_special_tokens=False)
    if len(tokens) <= max_token_len:
        return text
    else:
        # ตัด tokens ให้เหลือพอดี
        cut_tokens = tokens[:max_token_len]
        decoded_text = tokenizer.decode(cut_tokens)
        print(f"⚠️ ตัดข้อความจาก {len(tokens)} token → {max_token_len} token")
        return decoded_text

# ======================
# ฟังก์ชันประมวลผลข้อความ batch
# ======================
async def embed_batch(batch, embed_model):
    # ตัดข้อความให้ไม่เกิน max_token_len
    batch = [safe_cut_text(text, bert_tokenizer) for text in batch]

    # ส่งข้อมูลไปยัง API
    response = await client_openai.embeddings.create(model=embed_model, input=batch)
    
    # ตรวจสอบผลลัพธ์
    embeddings = [item.embedding for item in response.data]
    print(f"⚠️ จำนวน embeddings ที่ได้รับ: {len(embeddings)}")
    
    if len(embeddings) != len(batch):
        print(f"⚠️ จำนวน embeddings ที่ได้ ({len(embeddings)}) ไม่เท่ากับจำนวนข้อความใน batch ({len(batch)})")
    
    return embeddings

async def batch_process_embedding_async(text_list, embed_model, batch_size=100):
    assert isinstance(text_list, list), "❌ text_list ต้องเป็น list ของข้อความ"
    tasks = []
    for i in range(0, len(text_list), batch_size):
        batch = text_list[i:i + batch_size]
        tasks.append(embed_batch(batch, embed_model))
    
    results = await asyncio.gather(*tasks)
    
    # ตรวจสอบจำนวน embeddings ที่ได้รับ
    embeddings = [embedding for batch in results for embedding in batch]
    print(f"✅ สร้าง embeddings ทั้งหมด {len(embeddings)} vectors")
    
    return embeddings

# ======================
# ฟังก์ชันหลัก: รวมข้อมูล result แล้วสร้าง embeddings
# ======================
async def embed_result_all(result, embed_model):
    combined_text_list = []

    if isinstance(result, pd.DataFrame):
        # กรณี result เป็น DataFrame
        for _, row in result.iterrows():
            row_text = "\n".join(f"{k}: {v}" for k, v in row.items())
            safe_text = safe_cut_text(row_text, bert_tokenizer)
            combined_text_list.append(safe_text)
    elif isinstance(result, dict):
        # กรณี result เป็น dict แบบเดิม
        text_data = result.get("text", "")
        if text_data:
            split_text = textwrap.wrap(text_data, width=800)
            for t in split_text:
                safe_text = safe_cut_text(t, bert_tokenizer)
                combined_text_list.append(safe_text)

        tables = result.get("tables", [])
        for table in tables:
            table_text = "\n".join([" | ".join(row) for row in table])
            split_table = textwrap.wrap(table_text, width=800)
            for t in split_table:
                safe_text = safe_cut_text(t, bert_tokenizer)
                combined_text_list.append(safe_text)

        images_b64 = result.get("images_b64", [])
        for idx, img_b64 in enumerate(images_b64):
            img_text = f"[Image {idx+1}]"
            combined_text_list.append(img_text)
    else:
        raise ValueError("Unsupported input type for embed_result_all")

    if combined_text_list:
        embeddings = await batch_process_embedding_async(combined_text_list, embed_model)
        return embeddings
    else:
        print("❌ ไม่มีข้อมูลให้สร้าง embeddings")
        return []