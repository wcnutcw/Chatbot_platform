# ใช้ Python 3.13-slim เป็นฐาน
FROM python:3.13-slim

# อัปเดตแพ็กเกจระบบและติดตั้ง Node.js
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ตั้งค่า work directory
WORKDIR /app

# คัดลอกไฟล์ requirements.txt และติดตั้ง dependencies ของ Python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# --- ส่วนที่เพิ่มเข้ามา ---
# ดาวน์โหลดและติดตั้งโมเดลภาษาอังกฤษของ spaCy
RUN python -m spacy download en_core_web_sm
# หมายเหตุ: สำหรับ PyThaiNLP โดยส่วนใหญ่แล้วโมเดลจะถูกดาวน์โหลดอัตโนมัติเมื่อเรียกใช้ครั้งแรก
# แต่หากมีโมเดลเฉพาะที่ต้องการโหลดล่วงหน้า สามารถเพิ่มคำสั่งได้ที่นี่
# -------------------------

# คัดลอกโปรเจคทั้งหมดเข้ามา
COPY . /app/

# ติดตั้ง dependencies และ build frontend
WORKDIR /app/frontend
RUN npm install && npm run build

# กลับไปที่ root directory ของแอป
WORKDIR /app

# ให้สิทธิ์ execute กับสคริปต์ start.sh
RUN chmod +x /app/start.sh

# คำสั่งเริ่มต้นการทำงานของ container
CMD ["/bin/bash", "/app/start.sh"]
