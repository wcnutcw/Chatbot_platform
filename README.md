## 🧠 การใช้ Long-Term Memory (LTM) ในโปรเจกต์นี้
โปรเจกต์นี้รองรับ Long-Term Memory (LTM) เพื่อให้ AI สามารถ “จำ” หรือ “อ้างอิง” บทสนทนา/ข้อมูลจากอดีตได้อย่างแม่นยำ (เช่น การสนทนาเดิม, ข้อมูลในฐานข้อมูล, เอกสารที่ฝังใน Vector Store ฯลฯ) ซึ่งช่วยให้ระบบตอบสนองได้ชาญฉลาดและมีความต่อเนื่อง

## 💡 LTM คืออะไร?
Long-Term Memory ในที่นี้คือ การเก็บรักษาข้อมูลสำคัญระยะยาว (เช่น บทสนทนา, ข้อความ, reference, embeddings) ลงในฐานข้อมูล เช่น MongoDB หรือ Pinecone เพื่อเรียกใช้งานซ้ำและเชื่อมโยงความรู้เดิมกับสิ่งที่ AI กำลังโต้ตอบ

## 🛠️ วิธีใช้งาน LTM ในโปรเจกต์นี้
1. เตรียม Environment ให้พร้อม
ต้องกำหนด Environment Variables ให้ถูกต้อง (MONGO_URL, PINECONE_API_KEY ฯลฯ)

ดูรายละเอียดการตั้งค่าที่หัวข้อ "Getting Started" ด้านบน

2. หลักการทำงาน
เวลา AI ได้รับ input ใหม่ (เช่น คำถามจากผู้ใช้)
→ ระบบจะดึง context ที่เกี่ยวข้องจาก LTM (MongoDB/Pinecone)
→ AI นำ context เหล่านั้นมาวิเคราะห์และตอบให้ต่อเนื่องกับสิ่งที่ผู้ใช้เคยพูดหรือถามไว้

3. Workflow ตัวอย่าง
ฝังข้อมูล (Embedding)

เมื่ออัพโหลดไฟล์/บทสนทนา ข้อมูลจะถูกสร้าง Embedding แล้วเก็บลง Vector Store (เช่น Pinecone)

ดึง context

เมื่อผู้ใช้ถามคำถาม ระบบจะใช้ Embedding ของคำถาม ไปค้น context ที่ใกล้เคียงที่สุดจาก Vector Store หรือฐานข้อมูล

ตอบโดยอ้างอิงความรู้เดิม

AI นำ context ที่ค้นเจอผนวกกับ prompt ในการสร้างคำตอบ

4. ไฟล์โค้ดสำคัญที่เกี่ยวข้อง
embed_MongoDB.py / retrival_MongoDB.py
สำหรับจัดการ Embedding และ Retrieval จาก MongoDB

embed_pinecone.py / retrival_Pinecone.py
สำหรับ Embedding และ Retrieval จาก Pinecone

Prompt.py
จัดรูปแบบ prompt/ context ที่จะส่งเข้า LLM


## 🐍 Python Version
Python: 3.13.x

## 🚀 Getting Started
🛠️ 1. สร้าง Environment
```python -m venv venv```

📦 2. ติดตั้ง Library ผ่านลงใน environment
```pip install -r requirements.txt```


🔐 3. ตั้งค่า Environment Variables
สร้างไฟล์ .env ภายในโฟลเดอร์ venv/ แล้วเพิ่มค่า:

<pre>OPENAI_API_KEY=your_openai_api_key
MONGO_URL=your_localhost_or_remote_url
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENV=your_pinecone_environment
EMBEDDING=embedding_model_name_from_openai
FACEBOOK_ACCESS_TOKEN = TOKEN_API_FACEBOOK
HF_TOKEN=your_huggingface_token</pre>

## 🧪 วิธีรันโปรเจกต์
▶️ รัน Backend (FastAPI)
```cd main_backend```

```uvicorn main:app --reload --port 8000```

## 🖼️ รัน Frontend (Streamlit)
เปิด Terminal ใหม่:
```cd fontend```

```streamlit run app.py```

## 🛠️ แก้ไขปัญหาที่พบบ่อย
🔄 อัปเดต / ติดตั้งใหม่
หากเกิดปัญหาเกี่ยวกับ transformers หรือ torchvision:
```pip uninstall transformers torchvision```

```pip install transformers torchvision```

## ⚙️ ipywidgets / Jupyter
ปัญหาเกี่ยวกับ IProgress:
```pip install ipywidgets```

```jupyter nbextension enable --py widgetsnbextension```

## 🔥 อัปเกรด PyTorch
ตรวจสอบเวอร์ชันล่าสุดและแก้ไขของ torch:
```pip install torch --upgrade```

## 📚 ติดตั้ง Library ที่ขาด
หากมี error แจ้งว่าขาด library ใด ให้ติดตั้งเพิ่มด้วยคำสั่ง:
```pip install <library_name>```

## 🙋‍♂️ ติดต่อ
หากพบปัญหาหรือข้อเสนอแนะ กรุณาเปิด Issue หรือ pull request
