README

Python version : 3.13.x

ขั้นตอนการใช้งาน
เริ่มต้น
intstall Library :
pip install -r requirements.txt

ให้มีการสร้าง environment :
python -m venv venv

ต่อมาให้สร้าง ไฟล์ .env ลงในโฟลเดอร์ venv
แล้วใส่
OPENAI_API_KEY= key_nameของคุณ
MONGO_URL= localhostของคุณ
PINECONE_API_KEY= keyของคุณ
PINECONE_ENV= envของคุณบน pinecone

EMBEDDING= ตามที่อยากใช้ของจาก openai

HF_TOKEN= keyจาก HuggingFace


วิธี run: 
cd main_backend
แล้ว  ใช้คำสั่ง  uvicorn main:app --reload

สร้าง Terminal ใหม่ 
cd fontend
แล้วใช้คำสั่ง streamlit run app.py



ถ้ามีปัญหาหรือ error 
ลอง
**อัปเดตหรือถอนการติดตั้งและติดตั้งใหม่:**
ลองถอนการติดตั้ง transformers และ torchvision แล้วติดตั้งใหม่:
pip uninstall transformers torchvision
pip install transformers torchvision

**ตรวจสอบการติดตั้ง ipywidgets:**
ข้อความแจ้งเตือนเกี่ยวกับ IProgress อาจบ่งบอกว่า ipywidgets ไม่ถูกติดตั้งหรือต้องการอัปเดต ให้ติดตั้งหรืออัปเดต ipywidgets ด้วยคำสั่ง:
pip install ipywidgets
jupyter nbextension enable --py widgetsnbextension
ค้นหาเวอร์ชันล่าสุดของ torch:
pip install torch --upgrade

หรือถ้าขาด Library อะไร
ให้ install เพิ่มเติม

