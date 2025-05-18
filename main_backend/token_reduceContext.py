from transformers import AutoTokenizer
import tiktoken

def count_tokens(text, model):
    # โหลด tokenizer สำหรับโมเดลที่กำหนด
    tokenizer = AutoTokenizer.from_pretrained(model)
    # ใช้ tokenizer ในการแปลงข้อความเป็นโทเค็นและนับจำนวนโทเค็น
    encoded = tokenizer.encode(text, truncation=True, padding=False)
    return len(encoded)

encoding = tiktoken.encoding_for_model("gpt-4o-mini")

def reduce_context(text, num_tokens_context):
    tokens = encoding.encode(text)
    tokens = tokens[:num_tokens_context]
    return encoding.decode(tokens)