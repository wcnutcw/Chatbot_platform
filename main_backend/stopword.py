import re
from pythainlp.tokenize import word_tokenize
from pythainlp.corpus.common import thai_stopwords
import spacy
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize as en_word_tokenize

nlp = spacy.load("en_core_web_sm")
THAI_STOPWORDS = set(thai_stopwords())

def extract_keywords_from_query(query, corpus=None, top_k=5, min_len=2):
    """
    ดึง keyword สำคัญจาก query ด้วย BM25 context จาก corpus ทั้งไทยและอังกฤษ
    ถ้าไม่ส่ง corpus เข้ามา จะใช้วิธี POS tagging + stopword แบบเดิม
    """
    # Regular expression สำหรับจับวันที่ (วัน เดือน ปี) และเวลา
    date_pattern = re.compile(r'(\d{1,2})\s*(มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s*(\d{4})')
    time_pattern = re.compile(r'(\d{1,2}[:])?(\d{2})([:])?(\d{2})')  # สำหรับเวลา เช่น 14:30 หรือ 14:30:00

    # ใช้ regex เพื่อแยกวันเดือนปีและเวลา
    date_matches = date_pattern.findall(query)
    time_matches = time_pattern.findall(query)

    # แทนที่วันที่ใน query ด้วยคำว่า [DATE]
    for match in date_matches:
        query = query.replace(f"{match[0]} {match[1]} {match[2]}", "[DATE]")

    # แทนที่เวลาใน query ด้วยคำว่า [TIME]
    for match in time_matches:
        query = query.replace(f"{match[0]}{match[1]}:{match[3]}", "[TIME]")

    # ตัดคำไทย
    words_th = word_tokenize(query, keep_whitespace=False)
    doc_en = nlp(query)
    
    # ตัดคำอังกฤษ
    words_en = [
        token.text for token in doc_en
        if token.pos_ in {"NOUN", "PROPN", "VERB", "ADJ", "ADV"} and not token.is_stop
    ]
    
    # กรองคำที่ไม่ใช่ stopwords และมีความยาวมากกว่าหรือเท่ากับ min_len
    keywords_th = [w for w in words_th if w not in THAI_STOPWORDS and len(w) >= min_len]
    
    # รวมคำทั้งภาษาไทยและอังกฤษ
    base_keywords = list(set(keywords_th + words_en))
    
    # ถ้าไม่มี corpus ใช้วิธีเดิม
    if corpus is None:
        return base_keywords if base_keywords else []

    # ใช้ BM25 ดึง top keyword ที่มี impact กับ corpus
    tokenized_corpus = [word_tokenize(text, keep_whitespace=False) for text in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    
    scores = []
    for word in base_keywords:
        score = bm25.get_scores([word])
        scores.append((word, sum(score)))  # เอา sum score ทุก doc

    # เรียงคะแนน
    ranked_keywords = sorted(scores, key=lambda x: x[1], reverse=True)
    top_keywords = [kw for kw, _ in ranked_keywords[:top_k]]
    return top_keywords if top_keywords else []
