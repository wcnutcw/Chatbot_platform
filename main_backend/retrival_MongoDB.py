import numpy as np
import tiktoken
from sklearn.decomposition import PCA

openai_tokenizer = tiktoken.encoding_for_model("text-embedding-3-small")

def reduce_vector_dimension(vec, target_dim, pca_energy=None):
    if vec.ndim == 1:
        vec = vec.reshape(1, -1)
    current_dim = vec.shape[1]
    if current_dim == target_dim:
        return vec.flatten()
    if vec.shape[0] == 1:
        # Single vector: slice หรือ padding
        if current_dim > target_dim:
            reduced = vec[:, :target_dim]
        else:
            pad_width = target_dim - current_dim
            reduced = np.pad(vec, ((0, 0), (0, pad_width)), mode='constant')
    else:
        if pca_energy is not None and 0 < pca_energy < 1:
            pca = PCA(n_components=pca_energy, svd_solver='full')
        else:
            pca = PCA(n_components=target_dim)
        reduced = pca.fit_transform(vec)
        # Ensure correct dim
        if reduced.shape[1] > target_dim:
            reduced = reduced[:, :target_dim]
        elif reduced.shape[1] < target_dim:
            pad_width = target_dim - reduced.shape[1]
            reduced = np.pad(reduced, ((0,0),(0,pad_width)), mode='constant')
    return reduced.flatten()

def cosine_similarity_2(vec1, vec2):
    vec1 = np.array(vec1).flatten()
    vec2 = np.array(vec2).flatten()
    if vec1.shape != vec2.shape:
        raise ValueError(f"Shape mismatch: {vec1.shape} vs {vec2.shape}")
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 0.0
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def reduce_token_with_openai(text, max_tokens=512):
    tokens = openai_tokenizer.encode(text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return openai_tokenizer.decode(tokens)

async def retrieve_context_from_mongodb(collection, question: str, top_k: int = 5, embedding_model="text-embedding-3-small"):
    from openai import AsyncOpenAI
    client = AsyncOpenAI()
    response = await client.embeddings.create(model=embedding_model, input=[question])
    question_vector = np.array([response.data[0].embedding])
    print(f"Question vector shape: {question_vector.shape}")
    documents = list(collection.find())
    similarities = []
    for doc in documents:
        doc_embedding = np.array(doc["embedding"]).flatten()
        # ปรับขนาด embedding หากจำเป็น
        if doc_embedding.shape[0] != question_vector.shape[1]:
            doc_embedding = reduce_vector_dimension(doc_embedding, question_vector.shape[1])
        score = cosine_similarity_2(question_vector, doc_embedding)
        similarities.append((score, doc))
    similarities.sort(reverse=True, key=lambda x: x[0])
    reduced_texts = []
    for score, doc in similarities[:top_k]:
        reduced = reduce_token_with_openai(doc.get("raw_text", ""))
        print(f"Top doc (score={score:.4f}): {reduced[:100]} ...")
        reduced_texts.append(reduced)
    return "\n".join(reduced_texts)
