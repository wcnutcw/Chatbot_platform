# ใช้ Python 3.13-slim เป็นฐาน
FROM python:3.13-slim

# ตั้งค่า directory สำหรับโปรเจค
WORKDIR /app

# คัดลอกโฟลเดอร์ frontend และ main_backend มาใน container
COPY frontend /app/frontend
COPY main_backend /app/main_backend

# คัดลอกไฟล์ requirements.txt จาก root directory ของโปรเจค
COPY requirements.txt /app/requirements.txt

# ติดตั้ง dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# รันทั้งสอง service (Streamlit + Backend) ใน container
CMD sh -c "streamlit run /app/frontend/app.py --server.port=80 --server.address=0.0.0.0 & python /app/main_backend/main.py"
