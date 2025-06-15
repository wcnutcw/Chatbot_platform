# aiforthai_llm.py
from aift.multimodal import aift_pipeline

# เตรียม LLM
aiforthai_llm = aift_pipeline("aift-text-gen-7b-chat")

def invoke_aiforthai_llm(system_message, messages, **kwargs):
    """
    จำลอง interface ของ llm.invoke (สำหรับใช้งานกับ memory.py)
    """
    # รวม prompt: (context+ประวัติ+คำถามใหม่)
    prompt = ""
    if system_message:
        prompt += f"{system_message.strip()}\n"
    if messages:
        # เอาแค่เนื้อ user คนสุดท้าย
        for msg in messages:
            if isinstance(msg, dict):
                if msg.get("role") == "user":
                    prompt += f"คำถาม: {msg['content']}\n"
                elif msg.get("role") == "assistant":
                    prompt += f"คำตอบก่อนหน้า: {msg['content']}\n"
            elif isinstance(msg, str):
                prompt += msg + "\n"
    result = aiforthai_llm(prompt)
    # คืนค่าเป็น object/str ให้เหมือน LangChain
    if isinstance(result, dict) and "text" in result:
        return type('Obj', (object,), {"content": result["text"], "role": "assistant"})()
    return type('Obj', (object,), {"content": str(result), "role": "assistant"})()
