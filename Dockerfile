# ใช้ Python 3.13 เป็นฐาน
FROM python:3.13-slim

# ตั้งค่า directory สำหรับโปรเจค
WORKDIR /app

# คัดลอกโฟลเดอร์ frontend และ main_backend มาใน container
COPY fontend /app/fontend
COPY main_backend /app/main_backend

# คัดลอกไฟล์ requirements.txt จาก root directory ของโปรเจค
COPY requirements.txt /app/requirements.txt

# ติดตั้ง dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# รันทั้งสองไฟล์ใน container
CMD ["sh", "-c", "python /app/fontend/app.py & python /app/main_backend/main.py"]
