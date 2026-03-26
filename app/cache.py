import json
import os
import numpy as np
from app.embeddings import create_embeddings

CACHE_FILE = "cache.json"
embedding_model = create_embeddings()

THRESHOLD = 0.90

# Load cache
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return []

# Save cache
def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

cache_store = load_cache()

# Cosine similarity
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


#Semantic GET
def get_cached_response(query: str):
    query = query.lower().strip()
    query_emb = embedding_model.embed_query(query)

    best_score = 0
    best_answer = None

    for item in cache_store:
        score = cosine_similarity(query_emb, item["embedding"])

        if score > best_score:
            best_score = score
            best_answer = item["response"]

    if best_score >= THRESHOLD:
        print("Semantic cache hit:", best_score)
        return best_answer

    return None


#  Semantic SET
def set_cached_response(query: str, response: str):
    query = query.lower().strip()
    query_emb = embedding_model.embed_query(query)

    print("Writing to cache file:", query)

    cache_store.append({
        "query": query,
        "embedding": query_emb,
        "response": response
    })

    save_cache(cache_store)