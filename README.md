# 🧠Generative AI for RAG File

## 🐍 Python Version
Python: 3.13.x

## 🚀 Getting Started
📦 1. ติดตั้ง Library
```pip install -r requirements.txt```

🛠️ 2. สร้าง Environment
```python -m venv venv```

🔐 3. ตั้งค่า Environment Variables
สร้างไฟล์ .env ภายในโฟลเดอร์ venv/ แล้วเพิ่มค่า:

<pre>OPENAI_API_KEY=your_openai_api_key
MONGO_URL=your_localhost_or_remote_url
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENV=your_pinecone_environment
EMBEDDING=embedding_model_name_from_openai
HF_TOKEN=your_huggingface_token```</pre>

## 🧪 วิธีรันโปรเจกต์
▶️ รัน Backend (FastAPI)
```cd main_backend```

```uvicorn main:app --reload```

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
