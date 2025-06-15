import os
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from pydantic import BaseModel
from typing_extensions import TypedDict
from typing import List, Optional


# --- .env ---
load_dotenv()
current_directory = os.getcwd()
env_path = Path(current_directory).parent / 'venv' / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# การเชื่อมต่อ MongoDB
MONGO_URI = os.getenv('MONGO_URI')
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['chat_db']
if 'user_logs' not in db.list_collection_names():
    db.create_collection('user_logs')
userlog_col = db['user_logs']

# คีย์สำหรับ OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# การตั้งค่า LLM (โมเดล OpenAI GPT)
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=OPENAI_API_KEY
)

# แม่แบบ Prompt
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "{system_message}"),
    MessagesPlaceholder("messages")
])
llm_model = prompt_template | llm
store = InMemoryStore()

# --- Profile Model ---
class Profile(BaseModel):
    name: Optional[str]
    age: Optional[int]
    profession: Optional[str]
    hobby: Optional[List[str]]

structured_llm = prompt_template | llm.with_structured_output(Profile, method="function_calling")

# ฟังก์ชันสำหรับบันทึกข้อความของผู้ใช้ลง MongoDB
def log_user_message_mongo(user_id: str, message: str):
    userlog_col.insert_one({
        'user_id': user_id,
        'message': message.strip(),
        'log_type': 'user',
        'ts': int(__import__('time').time())  # Timestamp สำหรับบันทึกเวลา
    })

# ฟังก์ชันสำหรับดึงประวัติข้อความผู้ใช้จาก MongoDB
def get_longterm_history(user_id: str, limit=3):  # ดึงประวัติ 3 ข้อความล่าสุด
    messages = []
    cursor = userlog_col.find({'user_id': user_id}).sort('ts', 1).limit(limit * 2)
    for entry in cursor:
        if entry['log_type'] in ('user', 'assistant'):
            messages.append({
                "role": "user" if entry['log_type'] == 'user' else "assistant",
                "content": entry['message']
            })
    if len(messages) > limit * 2:
        messages = messages[-limit*2:]  # ลบข้อความเก่ามากเกินไป
    return messages

# ฟังก์ชันสำหรับดึงข้อมูลโปรไฟล์ผู้ใช้
def GetProfileNode(state: dict) -> dict:
    global store, structured_llm
    user_id = state.get('user_id', 'unknown')
    namespace_for_memory = (user_id, "memories")
    from Prompt import system_message
    result = structured_llm.invoke({
        "system_message": system_message(state),
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

def ChatNode(state: dict, context, emotional: str, is_first_greeting: bool = False) -> dict:
    global store, llm_model
    user_id = state.get('user_id', 'unknown')
    namespace_for_memory = (user_id, "memories")
    context_p = ""
    
    # สร้างข้อความจาก context ที่มีอยู่
    if isinstance(context, list):
        for doc in context:
            if hasattr(doc, "page_content"):
                context_p += f"{doc.page_content}\n\n"
            else:
                context_p += str(doc) + "\n\n"
    else:
        context_p = str(context)
    
    # ดึงข้อมูลโปรไฟล์จากหน่วยความจำ
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
    
    # ดึงประวัติการสนทนา (previous context) จากฐานข้อมูล
    ltm_msgs = get_longterm_history(user_id, limit=3)  # ดึงประวัติการสนทนาล่าสุด 3 ข้อความ
    previous_context = "\n".join([msg["content"] for msg in ltm_msgs])

    # import json
    # with open('data.json', 'r', encoding='utf-8') as f:
    #     data_json = json.load(f)

    # สร้าง system_message โดยใช้ข้อมูลจาก prompt
    from Prompt import base_system
    system_message = base_system(state["messages"] ,context_p, emotional, previous_context)  # ส่ง combined_context ไป
    system_message += "\n\n" + profile_str + "File Context (relevant chunks):\n"

    # รวมประวัติการสนทนาและข้อความใหม่ใน merged_msgs
    merged_msgs = ltm_msgs + [m for m in state["messages"] if m not in ltm_msgs]

    # เรียกใช้โมเดลเพื่อประมวลผลข้อความ
    result = llm_model.invoke({
        "system_message": system_message,
        "messages": merged_msgs
    })
    
    # ตรวจสอบผลลัพธ์ที่ได้และจัดการ
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
    
    # เพิ่มข้อความใหม่ใน state["messages"]
    state["messages"].append(msg_to_add)
    
    # บันทึกข้อความตอบกลับจากแอสซิสแทนต์ลง MongoDB
    userlog_col.insert_one({
        'user_id': user_id,
        'message': msg_content,
        'log_type': 'assistant',
        'ts': int(__import__('time').time())
    })
    
    return state, context


# ฟังก์ชันหลักในการสนทนา
def chat_interactive(user_id: str, user_message, context, emotional):
    history = []
    is_first_greeting = True
    log_user_message_mongo(user_id, user_message)  # บันทึกข้อความผู้ใช้
    history.append({"role": "user", "content": user_message})
    input_state = {"messages": history, "user_id": user_id}
    response_state, _ = ChatNode(input_state, context, emotional, is_first_greeting)
    is_first_greeting = False

    assistant_msgs = [
        msg for msg in response_state["messages"]
        if isinstance(msg, dict) and msg.get("role") == "assistant"
    ]
    
    if assistant_msgs:
        latest = assistant_msgs[-1]
        
        # บันทึกข้อความตอบกลับจากแอสซิสแทนต์ลง MongoDB
        userlog_col.insert_one({
            'user_id': user_id,
            'message': latest.get('content'),
            'log_type': 'assistant',
            'ts': int(__import__('time').time())
        })
        
        return latest.get("content")
    else:
        print("(ไม่มีข้อความตอบกลับ)")

State = TypedDict("State", {"messages": List[dict], "user_id": str})
graph_builder = StateGraph(State)

graph_builder.add_node("ChatNode", ChatNode)
graph_builder.add_node("GetProfileNode", GetProfileNode)
graph_builder.add_edge(START, "ChatNode")
graph_builder.add_edge("ChatNode", "GetProfileNode")
graph_builder.add_edge("GetProfileNode", END)

graph = graph_builder.compile(checkpointer=MemorySaver())
