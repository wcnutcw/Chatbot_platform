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

# --- LLM ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=OPENAI_API_KEY
)
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "{system_message}"),
    MessagesPlaceholder("messages")
])
llm_model = prompt_template | llm
store = InMemoryStore()

def clean_context_text(text: str, min_length: int = 30):
    lines = text.split("\n")
    return "\n".join([line.strip() for line in lines if len(line.strip()) > min_length])

# --- Profile Model ---
class Profile(BaseModel):
    name: Optional[str]
    age: Optional[int]
    profession: Optional[str]
    hobby: Optional[List[str]]

structured_llm = prompt_template | llm.with_structured_output(Profile, method="function_calling")

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
# Profile Extraction
# -------------------
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
        'name': None, 'age': None, 'profession': None, 'hobby': []
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

# -------------------
# Chat Core
# -------------------
def ChatNode(state: dict, context, emotional: str, is_first_greeting: bool = False) -> dict:
    global store, llm_model
    user_id = state.get('user_id', 'unknown')
    context_p = ""

    if isinstance(context, list):
        for doc in context:
            content = doc.page_content if hasattr(doc, "page_content") else str(doc)
            context_p += clean_context_text(content) + "\n\n"
    else:
        context_p = clean_context_text(str(context))

    namespace_for_memory = (user_id, "memories")
    profile_str = ""
    user_profile_mem = store.get(namespace_for_memory, key="profile")
    if user_profile_mem:
        pdata = user_profile_mem.value
        profile_str = f"User Profile:\nName: {pdata.get('name')}\nAge: {pdata.get('age')}\nProfession: {pdata.get('profession')}\nHobby: {pdata.get('hobby')}\n\n"

    ltm_msgs = get_longterm_history(user_id)
    ltm_user = get_longterm_user(user_id)
    previous_context = "\n".join([msg["content"] for msg in ltm_msgs])
    previous_context_user = "\n".join([msg["content"] for msg in ltm_user])
    message_content = state["messages"][0]["content"]

    from Prompt import base_system
    intro_hint = "ข้อมูลต่อไปนี้อาจมีส่วนช่วยในการตอบคำถามของผู้ใช้:\n"
    system_message = base_system(
        question=message_content,
        context_p=intro_hint + context_p,
        emotional_p=emotional,
        previous_context=previous_context_user,
        is_first_turn=is_first_greeting
    )
    system_message += "\n\n" + profile_str + "File Context (relevant chunks):\n"

    merged_msgs = ltm_msgs + [m for m in state["messages"] if m not in ltm_msgs]

    # print("🔎 SYSTEM MESSAGE:\n", system_message)
    # print("📚 MERGED MESSAGES:")
    for m in merged_msgs:
        print(f"- {m['role']}: {m['content']}")

    result = llm_model.invoke({
        "system_message": system_message,
        "messages": merged_msgs
    })
    print(f"คำตอบจากLLM : {result}")

    msg_content = result.content if hasattr(result, "content") else str(result)
    msg_to_add = {"role": "assistant", "content": msg_content}
    state["messages"].append(msg_to_add)

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
graph_builder.add_node("GetProfileNode", GetProfileNode)
graph_builder.add_edge(START, "ChatNode")
graph_builder.add_edge("ChatNode", "GetProfileNode")
graph_builder.add_edge("GetProfileNode", END)
graph = graph_builder.compile(checkpointer=MemorySaver())
