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
EMBEDDING_MODEL = os.getenv("EMBEDDING")
MAX_TOKEN_LENGTH = 512 # Max Token ที่ OpenAI รุ่นนี้รับได้

# ======================
# ฟังก์ชันตัดข้อความตาม Token Limit
# ======================
def safe_cut_text(text, tokenizer, max_token_len=512):
    tokens = tokenizer.encode(text, add_special_tokens=True)  # เพิ่ม special tokens
    if len(tokens) <= max_token_len:
        return text
    else:
        cut_tokens = tokens[:max_token_len]
        decoded_text = tokenizer.decode(cut_tokens, clean_up_tokenization_spaces=True)
        print(f"⚠️ ตัดข้อความจาก {len(tokens)} token → {max_token_len} token")
        return decoded_text
# ======================
# ฟังก์ชันประมวลผลข้อความ batch
# ======================
async def embed_batch(batch, embed_model):
    batch = [safe_cut_text(text, bert_tokenizer) for text in batch]
    response = await client_openai.embeddings.create(model=embed_model, input=batch)
    embeddings = [item.embedding for item in response.data]
    print(f"⚠️ จำนวน embeddings ที่ได้รับ: {len(embeddings)}")
    return embeddings

# ======================
# ฟังก์ชันรันหลาย batch พร้อมกัน
# ======================
async def batch_process_embedding_async(text_list, embed_model, batch_size=100):
    tasks = []
    for i in range(0, len(text_list), batch_size):
        batch = text_list[i:i + batch_size]
        tasks.append(embed_batch(batch, embed_model))
    results = await asyncio.gather(*tasks)
    embeddings = [embedding for batch in results for embedding in batch]
    print(f"✅ สร้าง embeddings ทั้งหมด {len(embeddings)} vectors")
    return embeddings

# ======================
# ฟังก์ชันประมวลผลภาพ base64 → CLIP embedding
# ======================
def embed_clip_images(images_b64):
    embeddings = []
    for idx, img_b64 in enumerate(images_b64):
        try:
            image_data = base64.b64decode(img_b64)
            image = Image.open(BytesIO(image_data)).convert("RGB")
            inputs = clip_processor(images=image, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = clip_model.get_image_features(**inputs)
            img_embedding = outputs.squeeze().cpu().tolist()
            embeddings.append(img_embedding)
            print(f"✅ สร้าง CLIP embedding สำหรับรูปภาพ {idx+1}/{len(images_b64)}")
        except Exception as e:
            print(f"❌ ไม่สามารถประมวลผลรูปภาพ {idx+1}: {e}")
    return embeddings

# ======================
# ฟังก์ชันหลัก: รวมข้อมูล result แล้วสร้าง embeddings
# ======================
async def embed_result_all(result, embed_model):
    combined_text_list = []
    image_embeddings = []

    if isinstance(result, pd.DataFrame):
        for _, row in result.iterrows():
            row_text = "\n".join(f"{k}: {v}" for k, v in row.items())
            safe_text = safe_cut_text(row_text, bert_tokenizer)
            combined_text_list.append(safe_text)

    elif isinstance(result, dict):
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
        if images_b64:
            image_embeddings = embed_clip_images(images_b64)

    # สร้าง text embeddings แบบ async
    text_embeddings = await batch_process_embedding_async(combined_text_list, embed_model)

    # รวมผลลัพธ์ embeddings ทั้งข้อความและภาพ
    all_embeddings = text_embeddings + image_embeddings
    print(f"📦 รวมทั้งหมด: {len(text_embeddings)} (text) + {len(image_embeddings)} (images) = {len(all_embeddings)} embeddings")

    return all_embeddings
