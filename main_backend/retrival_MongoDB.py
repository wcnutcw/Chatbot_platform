import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
from sklearn.decomposition import PCA
from transformers import AutoTokenizer


bert_tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")

# โหลดโมเดล LaBSE สำหรับการสร้าง embeddings
labse_model = SentenceTransformer('sentence-transformers/LaBSE')


def reduce_vector_dimension(vec, target_dim):
    if vec.ndim == 1:
        vec = vec.reshape(1, -1)

    current_dim = vec.shape[1]
    if current_dim == target_dim:
        return vec.flatten()

    if vec.shape[0] == 1:
        # กรณี sample เดียว ให้เลือกตัดหรือ padding
        if current_dim > target_dim:
            reduced = vec[:, :target_dim]
        else:
            pad_width = target_dim - current_dim
            reduced = np.pad(vec, ((0, 0), (0, pad_width)), mode='constant')
    else:
        # มีหลาย sample ใช้ PCA
        pca = PCA(n_components=target_dim)
        reduced = pca.fit_transform(vec)

    return reduced.flatten()



# ฟังก์ชัน cosine similarity ที่รองรับเวกเตอร์ 1D
def cosine_similarity_2(vec1, vec2):
    vec1 = np.array(vec1).flatten()
    vec2 = np.array(vec2).flatten()

    # ตรวจสอบขนาดของเวกเตอร์
    if vec1.shape != vec2.shape:
        raise ValueError(f"Shape mismatch: {vec1.shape} vs {vec2.shape}")

    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 0.0  # ป้องกันหารด้วยศูนย์

    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


# ฟังก์ชันลดจำนวน token โดยใช้ tokenizer ของ BERT
def reduce_token_with_bert(text, max_tokens=512):
    encoded = bert_tokenizer(text, truncation=True, max_length=max_tokens, return_tensors='pt')
    # แปลง token กลับเป็นข้อความหลังตัด token แล้ว
    truncated_text = bert_tokenizer.decode(encoded["input_ids"][0], skip_special_tokens=True)
    return truncated_text

async def retrieve_context_from_mongodb(collection,question: str, top_k: int = 3):
    # สร้าง embedding สำหรับคำถามด้วย LaBSE
    question_vector = labse_model.encode([question], convert_to_numpy=True)

    # ตรวจสอบขนาดของ question_vector
    print(f"Question vector shape: {question_vector.shape}")

    # ดึงข้อมูลจาก MongoDB
    documents = list(collection.find())
    similarities = []
    
    # คำนวณ cosine similarity สำหรับแต่ละเอกสาร
    for doc in documents:
        doc_embedding = np.array(doc["embedding"]).flatten()

        # ตรวจสอบขนาดของ doc_embedding
        print(f"Document embedding shape: {doc_embedding.shape}")

        # ปรับขนาดเวกเตอร์ของ doc["embedding"] ให้ตรงกับขนาดของ question_vector
        target_dim = question_vector.shape[1]  # ใช้ขนาดของ question_vector
        if doc_embedding.shape[0] != target_dim:
            doc_embedding = reduce_vector_dimension(doc_embedding, target_dim)

        # ตรวจสอบขนาดของ doc_embedding หลังจากลดขนาด
        print(f"Reduced document embedding shape: {doc_embedding.shape}")

        # คำนวณ cosine similarity
        score = cosine_similarity_2(question_vector, doc_embedding)
        similarities.append((score, doc))

    # จัดเรียงตามคะแนน similarity
    similarities.sort(reverse=True, key=lambda x: x[0])

    # คืนค่าข้อความที่ถูกลดจำนวนโทเค็น
    reduced_texts = []
    for score, doc in similarities[:top_k]:
        reduced = reduce_token_with_bert(doc["raw_text"])
        reduced_texts.append(reduced)

    return "\n".join(reduced_texts)
