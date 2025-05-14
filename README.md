README

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


วิธี run
cd main_backend
