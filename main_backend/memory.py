# chat_pdf.py

import os
from dotenv import load_dotenv
from pathlib import Path
# === Import รุ่นใหม่ของ LangChain และ langchain-pinecone ===
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder


# LangGraph memory & workflow
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from pydantic import BaseModel
from typing_extensions import TypedDict
from typing import List, Optional



# โหลดตัวแปรจาก .env
load_dotenv()
# --- โหลดค่า .env ---
current_directory = os.getcwd()
print("Current Directory:", current_directory)

env_path = Path(current_directory).parent / 'venv' / '.env'
print("Env Path:", env_path)

load_dotenv(dotenv_path=env_path, override=True)

# --- API Keys ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,   # 0-1
    openai_api_key=OPENAI_API_KEY
)

prompt_template = ChatPromptTemplate.from_messages([
    ("system", "{system_message}"),
    MessagesPlaceholder("messages")
])
llm_model = prompt_template | llm

# -------------------------------------------------------
# 4) เตรียม InMemoryStore สำหรับเก็บ Profile memory (global)
# -------------------------------------------------------
store = InMemoryStore()
user_id = "1"
namespace_for_memory = (user_id, "memories")

# -------------------------------------------------------
# 5) สร้าง Profile model และ structured_llm สำหรับดึงข้อมูลโปรไฟล์ (global)
# -------------------------------------------------------
class Profile(BaseModel):
    name: Optional[str]
    age: Optional[int]
    profession: Optional[str]
    hobby: Optional[List[str]]

structured_llm = prompt_template | llm.with_structured_output(Profile, method="function_calling")


# -------------------------------------------------------
# Logging user message to file
# -------------------------------------------------------

def log_user_message(message: str):
    with open("user_log.txt", "a", encoding="utf-8") as f:
        f.write(message.strip() + "\n")
# Connect to MongoDB   ( in the furthur set timing  1 day )

# -------------------------------------------------------
# 7) ฟังก์ชัน GetProfileNode (รับแค่ state) ใช้ global store
# -------------------------------------------------------
def GetProfileNode(state: dict) -> dict:
    global store, namespace_for_memory, structured_llm

    system_message = """
    คุณคือเจ้าหน้าที่ฝ่ายตอบคำถามนักศึกษาจากสำนักคอมพิวเตอร์ มหาวิทยาลัยบูรพา
    โปรดวิเคราะห์ข้อมูลและสรุปโปรไฟล์ของผู้สนทนาเท่าที่มีอยู่ในข้อความอย่างสุภาพและรอบคอบ
    หากไม่มีข้อมูลในบางส่วน กรุณาระบุว่า None โดยไม่สมมุติหรือเติมข้อมูลเอง
    Context: {context}
    """
    result = structured_llm.invoke({
        "system_message": system_message.format(context=state["messages"]),
        "messages": [{"role": "user", "content": "get my profile info"}]
    })

    profile_mem = store.get(namespace_for_memory, key="profile")
    profile = profile_mem.value if profile_mem else {
        'name': None,
        'age': None,
        'profession': None,
        'hobby': []
    }

    if not isinstance(profile['hobby'], list):
        profile['hobby'] = list(profile['hobby']) if profile['hobby'] else []

    if result.name:
        profile['name'] = result.name
    if result.age:
        profile['age'] = result.age
    if result.profession:
        profile['profession'] = result.profession

    if result.hobby:
        if isinstance(result.hobby, str):
            if result.hobby not in profile['hobby']:
                profile['hobby'].append(result.hobby)
        elif isinstance(result.hobby, list):
            profile['hobby'] = list(set(profile['hobby']).union(result.hobby))

    store.put(namespace_for_memory, "profile", profile)
    return state

# -------------------------------------------------------
# 8) ฟังก์ชัน ChatNode (ใช้ Pinecone similarity_search ภายใน namespace "test-buu")
# -------------------------------------------------------

def ChatNode(state: dict, context, is_first_greeting: bool = False) -> dict:
    global store, namespace_for_memory, embeddings_model, llm_model, vectorstore

    pdf_context = ""
    if isinstance(context, list):
        for doc in context:
            if hasattr(doc, "page_content"):
                pdf_context += f"{doc.page_content}\n\n"
            else:
                pdf_context += str(doc) + "\n\n"
    else:
        pdf_context = str(context)

    # ดึงข้อมูลโปรไฟล์ผู้ใช้จาก store
    user_profile_mem = store.get(namespace_for_memory, key="profile")
    profile_str = ""
    if user_profile_mem:
        pdata = user_profile_mem.value
        profile_str = (
            f"User Profile:\n"
            f"Name: {pdata.get('name')}\n"
            f"Age: {pdata.get('age')}\n"
            f"Profession: {pdata.get('profession')}\n"
            f"Hobby: {pdata.get('hobby')}\n\n"
        )

    base_system = """
คุณเป็นเจ้าหน้าที่ฝ่ายตอบคำถามนักศึกษาของสำนักคอมพิวเตอร์ มหาวิทยาลัยบูรพา 
ให้ตอบแบบสุภาพ เป็นทางการ ใช้ถ้อยคำไพเราะ อบอุ่น ให้ความรู้สึกเป็นผู้ชายใจดีและช่วยเหลือ
หลังจากกล่าวทักทาย "สวัสดีครับ" ในครั้งแรกแล้ว ให้ตอบโดยไม่ต้องมีสวัสดีในข้อความอีก
ใช้ context จาก memory, prompt, และ history ของการสนทนา
"""
    system_message = base_system + "\n\n" + profile_str + "PDF Context (relevant chunks):\n" + pdf_context

    # เรียกใช้ llm_model เพื่อให้ได้ผลลัพธ์ตอบกลับ
    result = llm_model.invoke({
        "system_message": system_message,
        "messages": state["messages"]
    })

    # ตรวจสอบชนิดของผลลัพธ์ที่ได้มา และเตรียมข้อความตอบกลับ
    if hasattr(result, "content"):
        msg_content = result.content
        msg_to_add = {"role": getattr(result, "role", "assistant"), "content": msg_content}
    elif isinstance(result, dict) and "content" in result:
        msg_content = result["content"]
        msg_to_add = {"role": result.get("role", "assistant"), "content": msg_content}
    elif isinstance(result, str):
        msg_content = result
        msg_to_add = {"role": "assistant", "content": msg_content}
    else:
        msg_to_add = {"role": "assistant", "content": str(result)}

    # เพิ่มข้อความตอบกลับเข้าไปใน state
    state["messages"].append(msg_to_add)
    return state, context



# -------------------------------------------------------
# 9) สร้าง Graph Workflow และ Compile (ไม่ต้องส่ง store พารามิเตอร์)
# -------------------------------------------------------
State = TypedDict("State", {"messages": List[dict]})
graph_builder = StateGraph(State)

graph_builder.add_node("ChatNode", ChatNode)
graph_builder.add_node("GetProfileNode", GetProfileNode)
graph_builder.add_edge(START, "ChatNode")
graph_builder.add_edge("ChatNode", "GetProfileNode")
graph_builder.add_edge("GetProfileNode", END)

graph = graph_builder.compile(checkpointer=MemorySaver())

config = {"configurable": {"thread_id": 123}}

def user_msg(s: str) -> dict:
    return {"role": "user", "content": s}

# -------------------------------------------------------
# 10) ฟังก์ชัน interactive สำหรับทดลองคุย
# -------------------------------------------------------
def chat_interactive(user_message, context):
    history = []   
    is_first_greeting = True
    # print(f"ME :{user_message}")
    log_user_message(user_message)
    history.append(user_msg(user_message))
    input_state = {"messages": history}

    # ส่ง input_state ทั้งหมด ไม่ใช่แค่ user_query
    response_state, _ = ChatNode(input_state, context, is_first_greeting)

    is_first_greeting = False
    assistant_msgs = [
        msg for msg in response_state["messages"]
        if isinstance(msg, dict) and msg.get("role") == "assistant"
    ]
    if assistant_msgs:
        latest = assistant_msgs[-1]
        # print("🤖Assistant:", latest.get("content"))
        history.append(latest)
        return latest.get("content")
    else:
        print("(ไม่มีข้อความตอบกลับ)")



# if __name__ == "__main__":
#     chat_interactive()
