from dotenv import load_dotenv 
import os
from openai import AsyncOpenAI
# ENV
load_dotenv(dotenv_path="../backend/.env")
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print(print("KEY:", client))