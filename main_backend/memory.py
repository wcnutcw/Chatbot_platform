import os
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from pydantic import BaseModel
from typing_extensions import TypedDict
from typing import List, Optional

from Prompt import *
from typhoon_llm import TyphoonClient  # นำเข้า TyphoonClient

# --- .env ---
load_dotenv()
current_directory = os.getcwd()
env_path = Path(current_directory).parent / 'venv' / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# --- MongoDB ---
MONGO_URI = os.getenv('MONGO_URI')
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['chat_db']

if 'user_logs' not in db.list_collection_names():
    db.create_collection('user_logs')
if 'session_flags' not in db.list_collection_names():
    db.create_collection('session_flags')

userlog_col = db['user_logs']
session_flag_col = db['session_flags']

# --- ใช้ TyphoonClient แทนฟังก์ชัน typhoon_wrapper ---
typhoon_client = TyphoonClient(api_key=os.getenv("TYPHOON_API_KEY"), api_url=os.getenv("TYPHOON_API_URL"))

prompt_template = ChatPromptTemplate.from_messages([
    ("system", "{system_message}"),
    MessagesPlaceholder("messages")
])

# --- Memory ---
store = InMemoryStore()

def clean_context_text(text: str, min_length: int = 30):
    lines = text.split("\n")
    return "\n".join([line.strip() for line in lines if len(line.strip()) > min_length])

# -------------------
# Data Persistence
# -------------------
def log_user_message_mongo(user_id: str, message: str):
    userlog_col.insert_one({
        'user_id': user_id,
        'message': message.strip(),
        'log_type': 'user',
        'ts': int(__import__('time').time())
    })

def get_longterm_history(user_id: str, limit=3):
    cursor = userlog_col.find({'user_id': user_id}).sort('ts', 1).limit(limit * 2)
    messages = [
        {"role": "user" if entry['log_type'] == 'user' else "assistant", "content": entry['message']}
        for entry in cursor if entry['log_type'] in ('user', 'assistant')
    ]
    return messages[-limit*2:] if len(messages) > limit*2 else messages

def get_longterm_user(user_id: str, limit=3):
    cursor = userlog_col.find({'user_id': user_id}).sort('ts', 1).limit(limit * 2)
    messages = [
        {"role": "user", "content": entry['message']}
        for entry in cursor if entry['log_type'] == 'user'
    ]
    return messages[-limit*2:] if len(messages) > limit*2 else messages

def get_is_first_greeting(user_id: str) -> bool:
    entry = session_flag_col.find_one({"user_id": user_id})
    return entry is None or entry.get("is_first_greeting", True)

def set_is_first_greeting_false(user_id: str):
    session_flag_col.update_one(
        {"user_id": user_id},
        {"$set": {"is_first_greeting": False}},
        upsert=True
    )

# -------------------
# Chat Core
# -------------------
def ChatNode(state: dict, context, emotional: str, is_first_greeting: bool = False) -> dict:
    global store, typhoon_client
    user_id = state.get('user_id', 'unknown')
    context_p = ""

    if isinstance(context, list):
        for doc in context:
            content = doc.page_content if hasattr(doc, "page_content") else str(doc)
            context_p += clean_context_text(content) + "\n\n"
    else:
        context_p = clean_context_text(str(context))

    # ดึงข้อความจาก longterm history และ user history
    ltm_msgs = get_longterm_history(user_id)
    ltm_user = get_longterm_user(user_id)
    previous_context = "\n".join([msg["content"] for msg in ltm_msgs])

    message_content = state["messages"][0]["content"]

    intro_hint = "ข้อมูลต่อไปนี้อาจมีส่วนช่วยในการตอบคำถามของผู้ใช้:\n"
    import json
    with open('data.json', 'r', encoding='utf-8') as file:
        data_json = json.load(file)

    # Step 1: ใช้ฟังก์ชัน analyze_question() เพื่อวิเคราะห์คำถาม
    create_context = analyze_question(
        message_content,
        intro_hint + context_p,
        data_json
    )

    # ใช้ TyphoonClient แทน Typhoon response
    ## LLM1 : คัดกรองข้อมูลจากคำถามและ context ที่ได้รับ
    context_new = typhoon_client.get_response(create_context)
    print(f"คำตอบจาก Typhoon 1: {context_new}")

    # Step 2: ใช้ Typhoon หรือ LLM ในการสรุปคำตอบจากข้อมูลที่ได้รับ
    summarized_answer = summarize_answer(
        question=message_content,
        context_p=context_new,
        previous_context=previous_context  # แก้ไขเป็น previous_context แทน previous_context_user
    )

    # ส่งคำขอไปยัง TyphoonClient หรือ LLM ในการประมวลผลคำตอบ
    result = typhoon_client.get_response(summarized_answer)
    print(f"คำตอบจาก Typhoon 2: {result}")

    # Step 3: ใช้ Typhoon หรือ LLM ในการตอบคำถามในบทบาทเจ้าหน้าที่สำนักคอมพิวเตอร์
    system_message_str = base_system(
        question=message_content,
        context_p=result,
        emotional_p=emotional,
        is_first_turn=is_first_greeting
    )

    # ส่งคำขอไปยัง TyphoonClient หรือ LLM ในการประมวลผลคำตอบ
    final_result = typhoon_client.get_response(system_message_str)
    print(f"คำตอบจาก Typhoon 3: {final_result}")

    # เก็บผลลัพธ์ที่ตอบกลับไปในฐานข้อมูล
    msg_content = final_result if isinstance(final_result, str) else str(final_result)
    msg_to_add = {"role": "assistant", "content": msg_content}
    state["messages"].append(msg_to_add)

    # บันทึกผลลัพธ์ที่ตอบกลับไปในฐานข้อมูล
    userlog_col.insert_one({
        'user_id': user_id,
        'message': msg_content,
        'log_type': 'assistant',
        'ts': int(__import__('time').time())
    })

    return state, context

def chat_interactive(user_id: str, user_message, context, emotional):
    is_first_greeting = get_is_first_greeting(user_id)
    log_user_message_mongo(user_id, user_message)

    history = [{"role": "user", "content": user_message}]
    input_state = {"messages": history, "user_id": user_id}

    response_state, _ = ChatNode(input_state, context, emotional, is_first_greeting=is_first_greeting)
    set_is_first_greeting_false(user_id)

    assistant_msgs = [
        msg for msg in response_state["messages"]
        if isinstance(msg, dict) and msg.get("role") == "assistant"
    ]

    if assistant_msgs:
        latest = assistant_msgs[-1]
        userlog_col.insert_one({
            'user_id': user_id,
            'message': latest.get('content'),
            'log_type': 'assistant',
            'ts': int(__import__('time').time())
        })
        return latest.get("content")
    else:
        print("(ไม่มีข้อความตอบกลับ)")
        return "ขออภัยค่ะ ระบบยังไม่สามารถตอบกลับได้ในขณะนี้"

State = TypedDict("State", {"messages": List[dict], "user_id": str})
graph_builder = StateGraph(State)
graph_builder.add_node("ChatNode", ChatNode)
graph_builder.add_edge(START, "ChatNode")
graph_builder.add_edge("ChatNode", END)
graph = graph_builder.compile(checkpointer=MemorySaver())
