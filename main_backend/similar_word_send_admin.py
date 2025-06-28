from sentence_transformers import SentenceTransformer, util
import numpy as np
import re

# Load the multilingual model
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def is_similar_to_contact_staff(message_text, threshold=0.55):
    """
    Detect contact staff requests using direct string matching with semantic similarity debugging.
    ✅ METHOD 1: Direct string matching (HIGHEST PRIORITY)
    📊 METHOD 2: Semantic similarity (FOR DEBUGGING ONLY)
    """
    if not message_text:
        return False
    
    # Clean the input message
    message_clean = message_text.strip()
    message_lower = message_clean.lower()
    
    print(f"🔍 Analyzing message: '{message_clean}'")
    
    # ✅ METHOD 1: Direct string matching (HIGHEST PRIORITY)
    direct_phrases = [
        "ติดต่อเจ้าหน้าที่",
        "contact staff"
    ]
    
    direct_match_found = False
    for phrase in direct_phrases:
        if phrase.lower() in message_lower:
            print(f"✅ DIRECT MATCH found: '{phrase}' in message")
            direct_match_found = True
            break
    
    # 📊 METHOD 2: Semantic similarity analysis (FOR DEBUGGING ONLY)
    print(f"\n📊 Semantic Analysis (for debugging):")
    
    # Reference phrases for semantic comparison
    reference_phrases = [
        "ติดต่อเจ้าหน้าที่",
        "Contact staff"
    ]
    
    # Calculate embeddings
    message_embedding = model.encode([message_clean])
    reference_embeddings = model.encode(reference_phrases)
    
    # Calculate similarities
    similarities = util.cos_sim(message_embedding, reference_embeddings)[0]
    
    # Find best match
    max_similarity = float(similarities.max())
    best_match_idx = similarities.argmax()
    best_match_phrase = reference_phrases[best_match_idx]
    
    # Show semantic analysis results
    if max_similarity >= threshold:
        print(f"✅ SEMANTIC MATCH found!")
        print(f"   Best match: '{best_match_phrase}'")
        print(f"   Similarity: {max_similarity:.3f} (threshold: {threshold})")
    else:
        print(f"❌ No semantic match found")
        print(f"   Best semantic match: '{best_match_phrase}'")
        print(f"   Similarity: {max_similarity:.3f} (threshold: {threshold})")
    
    # Show all similarities for debugging
    print(f"\n📋 All similarity scores:")
    for i, (phrase, sim) in enumerate(zip(reference_phrases, similarities)):
        status = "✅" if sim >= threshold else "❌"
        print(f"   {status} '{phrase}': {sim:.3f}")
    
    # Final decision based on DIRECT MATCHING ONLY
    if direct_match_found:
        print(f"\n🎯 Final Result: ✅ DETECTED (Direct Match)")
        return True
    else:
        print(f"\n🎯 Final Result: ❌ NOT DETECTED (No Direct Match)")
        return False