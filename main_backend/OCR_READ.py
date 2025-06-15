import aiohttp
import io
from PIL import Image
import pytesseract
import logging
from Prompt import ocr_system
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from pathlib import Path
import re

current_directory = os.getcwd()
env_path = Path(current_directory).parent / 'venv' / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# คีย์สำหรับ OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=OPENAI_API_KEY
)

def fix_ocr_spacing(text):
    # แก้กรณีเจอภาษาไทย/อังกฤษเว้นผิดตัว-ตัว
    # ถ้าเป็นคำไทย/อังกฤษ เว้นทีละตัว (มี space ทุกตัว) ให้รวมหมด
    # ถ้ามีหลายคำ (เว้นวรรคคำปกติ) ให้เช็คถ้าแต่ละกลุ่มมีแต่ตัวเดียวติด space ให้รวม
    # วิธีนี้จะจับคำที่มีแต่ตัวอักษรโดดๆ ต่อกัน
    return re.sub(r'((?:[ก-๙A-Za-z] ){2,}[ก-๙A-Za-z])', lambda m: m.group(0).replace(" ", ""), text)

async def process_image_and_ocr_then_chat(image_url: str) -> str:
    """
    โหลดรูปภาพจาก URL และทำ OCR อ่านข้อความออกมา คืนข้อความ OCR (ยังไม่วิเคราะห์)
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    logging.error(f"Failed to download image from {image_url}")
                    return ""
                image_bytes = await resp.read()

        img = Image.open(io.BytesIO(image_bytes))
        custom_config = r'--oem 3 --psm 6'
        ocr_text_b = pytesseract.image_to_string(img, lang='tha+eng', config=custom_config).strip()
        ocr_text_b=fix_ocr_spacing(ocr_text_b)
        ocr_text_a = ocr_system(ocr_text_b)
        result = llm.invoke(ocr_text_a)
        # AIMessage
        if hasattr(result, "content"):
            return result.content
        else:
            return str(result)
    except Exception as e:
        logging.error(f"Error processing OCR from image: {e}")
        return ""

