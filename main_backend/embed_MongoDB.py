import asyncio
import os
from pathlib import Path
import base64
from io import BytesIO
import pandas as pd
from dotenv import load_dotenv
from openai import AsyncOpenAI
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import torch
import tiktoken

# --- โหลดค่า .env ---
current_directory = os.getcwd()
env_path = Path(current_directory).parent / 'venv' / '.env'
load_dotenv(dotenv_path=env_path, override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client_openai = AsyncOpenAI(api_key=OPENAI_API_KEY)
EMBEDDING_MODEL = os.getenv("EMBEDDING", "text-embedding-3-small")
MAX_TOKEN_LENGTH = 350      # ปรับขนาด chunk ลงให้ละเอียดขึ้น
CHUNK_STRIDE = 200          # ขยับทีละ 200 token (overlap 150 token)

cache_dir = "./my_model_cache"
HF_TOKEN = os.getenv("HF_TOKEN", "")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", token=HF_TOKEN, cache_dir=cache_dir)
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", token=HF_TOKEN, cache_dir=cache_dir)

def get_tokenizer_openai(model="text-embedding-3-small"):
    return tiktoken.encoding_for_model(model)

tokenizer_openai = get_tokenizer_openai(EMBEDDING_MODEL)

def split_text_to_token_chunks_with_overlap(text, tokenizer, max_token_len=350, stride=200):
    tokens = tokenizer.encode(text)
    chunks = []
    i = 0
    while i < len(tokens):
        chunk_tokens = tokens[i:i+max_token_len]
        if not chunk_tokens:
            break
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        i += stride
    return chunks

def check_chunks_max_token_openai(batch, tokenizer, max_token_len):
    for idx, text in enumerate(batch):
        token_len = len(tokenizer.encode(text))
        if token_len > max_token_len:
            print(f"❗ Chunk {idx} length: {token_len} > {max_token_len} tokens")
        else:
            print(f"✓ Chunk {idx} length: {token_len} tokens OK")

async def embed_batch(batch, embed_model):
    check_chunks_max_token_openai(batch, tokenizer_openai, MAX_TOKEN_LENGTH)
    safe_batch = []
    for text in batch:
        tokens = tokenizer_openai.encode(text)
        if len(tokens) > MAX_TOKEN_LENGTH:
            tokens = tokens[:MAX_TOKEN_LENGTH]
            text = tokenizer_openai.decode(tokens)
        safe_batch.append(text)
    response = await client_openai.embeddings.create(model=embed_model, input=safe_batch)
    embeddings = [item.embedding for item in response.data]
    print(f"⚠️ จำนวน embeddings ที่ได้รับ: {len(embeddings)}")
    return embeddings

async def batch_process_embedding_async(text_list, embed_model, batch_size=100):
    tasks = []
    for i in range(0, len(text_list), batch_size):
        batch = text_list[i:i + batch_size]
        tasks.append(embed_batch(batch, embed_model))
    results = await asyncio.gather(*tasks)
    embeddings = [embedding for batch in results for embedding in batch]
    print(f"✅ สร้าง embeddings ทั้งหมด {len(embeddings)} vectors")
    return embeddings

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

async def embed_result_all(result, embed_model):
    combined_text_list = []
    image_embeddings = []

    if isinstance(result, pd.DataFrame):
        for _, row in result.iterrows():
            row_text = "\n".join(f"{k}: {v}" for k, v in row.items())
            row_chunks = split_text_to_token_chunks_with_overlap(row_text, tokenizer_openai, max_token_len=MAX_TOKEN_LENGTH, stride=CHUNK_STRIDE)
            for i, c in enumerate(row_chunks):
                print(f"chunk[{i}]: {c[:60].replace('\n',' ')} ...")   # debug
            combined_text_list.extend(row_chunks)

    elif isinstance(result, dict):
        if "pages" in result and isinstance(result["pages"], list):
            for idx, page_text in enumerate(result["pages"]):
                page_chunks = split_text_to_token_chunks_with_overlap(page_text, tokenizer_openai, max_token_len=MAX_TOKEN_LENGTH, stride=CHUNK_STRIDE)
                print(f"PDF Page {idx+1}: {len(page_chunks)} chunks")
                combined_text_list.extend(page_chunks)

        if "paragraphs" in result and isinstance(result["paragraphs"], list):
            for idx, para_text in enumerate(result["paragraphs"]):
                para_chunks = split_text_to_token_chunks_with_overlap(para_text, tokenizer_openai, max_token_len=MAX_TOKEN_LENGTH, stride=CHUNK_STRIDE)
                print(f"DOCX Paragraph {idx+1}: {len(para_chunks)} chunks")
                combined_text_list.extend(para_chunks)

        text_data = result.get("text", "")
        if isinstance(text_data, str) and text_data.strip():
            text_chunks = split_text_to_token_chunks_with_overlap(text_data, tokenizer_openai, max_token_len=MAX_TOKEN_LENGTH, stride=CHUNK_STRIDE)
            combined_text_list.extend(text_chunks)
        elif isinstance(text_data, list):
            for idx, t in enumerate(text_data):    
                t_chunks = split_text_to_token_chunks_with_overlap(str(t), tokenizer_openai, max_token_len=MAX_TOKEN_LENGTH, stride=CHUNK_STRIDE)
                combined_text_list.extend(t_chunks)

        tables = result.get("tables", [])
        for table in tables:
            table_text = "\n".join([" | ".join(row) for row in table])
            table_chunks = split_text_to_token_chunks_with_overlap(table_text, tokenizer_openai, max_token_len=MAX_TOKEN_LENGTH, stride=CHUNK_STRIDE)
            combined_text_list.extend(table_chunks)

        images_b64 = result.get("images_b64", [])
        if images_b64:
            image_embeddings = embed_clip_images(images_b64)

    print(f"Text chunk ทั้งหมดที่เตรียม embed: {len(combined_text_list)}")
    text_embeddings = await batch_process_embedding_async(combined_text_list, embed_model)
    all_embeddings = text_embeddings + image_embeddings
    print(f"📦 รวมทั้งหมด: {len(text_embeddings)} (text) + {len(image_embeddings)} (images) = {len(all_embeddings)} embeddings")

    # ควร return (embeddings, combined_text_list) เพื่อเก็บ raw_text คู่กับ embedding
    return all_embeddings, combined_text_list
