import aiohttp
import io
from PIL import Image
import pytesseract
import logging

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
        ocr_text = pytesseract.image_to_string(img, lang='tha+eng', config=custom_config).strip()
        return ocr_text

    except Exception as e:
        logging.error(f"Error in OCR processing: {e}")
        return ""
