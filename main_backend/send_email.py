import datetime
from email.message import EmailMessage
import os
current_directory = os.getcwd()
print("Current Directory:", current_directory) 
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(current_directory).parent / 'venv' / '.env'
print("Env Path:", env_path)  

load_dotenv(dotenv_path=env_path,override=True)

#TOKEN_FACEBOOK
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")

#EMAIL
EMAIL_ADMIN = os.getenv("EMAIL_ADMIN")
EMAIL_PASS = os.getenv("EMAIL_PASS")


# SEND EMAIL
def send_alert_email(fb_id: str, message: str, timestamp: int):
    dt = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

    user_name = get_facebook_user_name(fb_id, FACEBOOK_ACCESS_TOKEN)
    
    email = EmailMessage()
    email["Subject"] = "แจ้งเตือนจากแชทบอท: ติดต่อเจ้าหน้าที่"
    email["From"] = EMAIL_ADMIN
    email["To"] = EMAIL_ADMIN
    
    email.set_content(f"""
มีการขอ "ติดต่อเจ้าหน้าที่"

👤 ผู้ใช้: {user_name}
🕒 เวลา: {dt}
📝 ข้อความ: {message}""")
    
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADMIN, EMAIL_PASS)
        smtp.send_message(email)



def get_facebook_user_name(fb_id: str, access_token: str) -> str:
    try:
        url = f"https://graph.facebook.com/{fb_id}?fields=first_name,last_name&access_token={access_token}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            first_name = data.get("first_name", "")
            last_name = data.get("last_name", "")
            return f"{first_name} {last_name}".strip()
        else:
            return f"[ไม่สามารถดึงชื่อได้: {fb_id}]"
    except Exception as e:
        return f"[Error: {fb_id}]"