import os
import base64
from docx import Document
from PyPDF2 import PdfReader
import pdfplumber
import fitz  # PyMuPDF
import pandas as pd
from fastapi.responses import JSONResponse
from tempfile import TemporaryDirectory
from cleasing import cleansing  # สมมติว่า cleansing ทำความสะอาด DataFrame แล้วคืนกลับ
import logging

# ตั้งค่าการ logging
# logging.basicConfig(level=logging.DEBUG)

def read_docx(path):
    doc = Document(path)
    text = ""
    tables = []
    images_b64 = []

    for para in doc.paragraphs:
        text += para.text + "\n"

    for table in doc.tables:
        table_data = []
        for row in table.rows:
            table_data.append([cell.text.strip() for cell in row.cells])
        tables.append(table_data)

    for shape in doc.inline_shapes:
        try:
            image = shape._inline.graphic.graphicData.pic.blipFill.blip.embed
            image_part = doc.part.related_parts[image]
            image_bytes = image_part.blob
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            images_b64.append(image_b64)
        except Exception as e:
            logging.error(f"❌ Error extracting DOCX image: {e}")
    
    return text.strip(), tables, images_b64


def read_pdf(path):
    text = ""
    tables = []
    images_b64 = []

    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num} ---\n{page_text}"
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
            except Exception as e:
                logging.error(f"❌ Error processing page {page_num}: {e}")

    doc = fitz.open(path)
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            images_b64.append(image_b64)

    return text.strip(), tables, images_b64


async def Up_File(upload_files):
    dfs = []
    text_data = []
    all_tables = []
    all_images_b64 = []

    with TemporaryDirectory() as tmpdir:
        for upload_file in upload_files:
            filename = upload_file.filename
            file_path = os.path.join(tmpdir, filename)

            # Save file to disk temporarily
            with open(file_path, "wb") as f:
                content = await upload_file.read()
                f.write(content)

            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                    dfs.append(df)

                elif filename.endswith('.xlsx'):
                    excel_data = pd.read_excel(file_path, sheet_name=None)
                    for sheet in excel_data.values():
                        dfs.append(sheet)

                elif filename.endswith('.docx'):
                    text, tables, images = read_docx(file_path)
                    text_data.append(f"--- DOCX File: {filename} ---\n{text}")
                    all_tables.extend(tables)
                    all_images_b64.extend(images)

                elif filename.endswith('.pdf'):
                    text, tables, images = read_pdf(file_path)
                    text_data.append(f"--- PDF File: {filename} ---\n{text}")
                    all_tables.extend(tables)
                    all_images_b64.extend(images)

            except Exception as e:
                logging.error(f"❌ Error processing file {filename}: {e}")

    df_combined = pd.DataFrame()  # default กรณีไม่มีอะไรเลย

    if dfs:
        try:
            # ตรวจสอบก่อนว่ามี DataFrame ที่สามารถรวมได้หรือไม่
            df_concat = pd.concat(dfs, ignore_index=True)
            if df_concat.empty:
                return JSONResponse(content={"error": "No valid data in CSV or Excel files"}, status_code=400)
            # เรียกฟังก์ชัน cleansing
            df_combined = cleansing(df_concat)
        except Exception as e:
            logging.error(f"❌ Error during concat or cleansing: {e}")
            return JSONResponse(content={"error": f"Error during concat or cleansing: {str(e)}"}, status_code=400)

    elif text_data:
        df_combined = pd.DataFrame({"text": text_data})

    # ตรวจสอบ df_combined
    if df_combined is None or df_combined.empty:
        return JSONResponse(content={"error": "No valid data after cleansing or file read"}, status_code=400)

    result = {
        "dataframe": df_combined.to_dict(orient="records"),
        "tables": all_tables,
        "images_b64": all_images_b64,
        "text": text_data
    }

    return result
