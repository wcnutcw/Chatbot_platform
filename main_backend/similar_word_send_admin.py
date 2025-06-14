#รอพัฒนาในอนาคตต่อไป
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

target_phrases = [
    "ติดต่อเจ้าหน้าที่",
    "แจ้งเจ้าหน้าที่",   
    "ขอคุยกับเจ้าหน้าที่",                    
    "อยากคุยกับแอดมิน",
    "ขอความช่วยเหลือจากเจ้าหน้าที่",
    "แอดมินอยู่ไหม",
    "รบกวนติดต่อเจ้าหน้าที่"
]
target_embeddings = model.encode(target_phrases, convert_to_tensor=True)

def is_similar_to_contact_staff(message_text, threshold=0.7):
    input_embedding = model.encode(message_text, convert_to_tensor=True)
    cosine_scores = util.pytorch_cos_sim(input_embedding, target_embeddings)
    max_score = cosine_scores.max().item()
    return max_score >= threshold


                    
# ในฟังก์ชันหลัก (เช่น fastapi endpoint)
# if is_similar_to_contact_staff(message_text):
#     background_tasks.add_task(send_alert_email, sender_id, message_text, timestamp)
#     await send_facebook_message(sender_id, "กรุณารอเจ้าหน้าที่มาตอบนะครับ")
#     return Response(content="ok", status_code=200)