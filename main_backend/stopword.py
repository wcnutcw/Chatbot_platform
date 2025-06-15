from pythainlp.tokenize import word_tokenize
from pythainlp.corpus.common import thai_stopwords
import spacy

nlp = spacy.load("en_core_web_sm")
THAI_STOPWORDS = set(thai_stopwords())

def extract_keywords_from_query(query, min_len=2):
    words_th = word_tokenize(query, keep_whitespace=False)
    doc_en = nlp(query)
    # Noun, Verb, Adj, Adv, PROPN
    words_en = [token.text for token in doc_en if token.pos_ in {"NOUN", "PROPN", "VERB", "ADJ", "ADV"} and not token.is_stop]
    keywords_th = [w for w in words_th if w not in THAI_STOPWORDS and len(w) >= min_len]
    keywords = list(set(keywords_th + words_en))
    # ถ้าไม่มี keyword ใดๆเลย ส่งคืน []
    return keywords if keywords else []
