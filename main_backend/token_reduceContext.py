import tiktoken
from typing import List

def get_encoding(model_name="gpt-4o-mini"):
    return tiktoken.encoding_for_model(model_name)

def count_tokens(text: str, model="gpt-4o-mini") -> int:
    encoding = get_encoding(model)
    return len(encoding.encode(text))

def extractive_summarize(text: str, keywords: List[str]) -> str:
    # เลือกเฉพาะบรรทัดที่มี keyword
    if not keywords:
        return text
    lines = text.splitlines()
    selected = []
    for line in lines:
        for kw in keywords:
            if kw.lower() in line.lower():
                selected.append(line)
                break
    return "\n".join(selected)

def reduce_context(
    text: str,
    max_tokens: int,
    keywords: List[str] = None,
    model_name: str = "gpt-4o-mini"
) -> str:
    """
    - ถ้าใส่ keywords จะ filter เฉพาะ span สำคัญก่อน
    - แล้ว truncate context ให้ไม่เกิน max_tokens
    """
    encoding = get_encoding(model_name)
    # Step 1: extractive summarize
    if keywords:
        text = extractive_summarize(text, keywords)
    # Step 2: truncate ตามจำนวน token ที่ต้องการ
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return encoding.decode(tokens[:max_tokens])
