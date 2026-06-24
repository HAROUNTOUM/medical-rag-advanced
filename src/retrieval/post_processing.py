import numpy as np
from src.embeddings.embedder import embed


def cosine_similarity(vec_a, vec_b):
    """Computes the cosine similarity between two vectors."""
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def compress_context(
    query: str, docs: list[dict], threshold: float = 0.76
) -> list[dict]:
    """
    Filters retrieved documents based on embedding similarity to the query.
    This acts as a 'Contextual Compression' step to remove irrelevant fluff.
    """
    if not docs:
        return []

    print(
        f"🗜️ Compressing context (original docs: {len(docs)}) against similarity threshold {threshold}..."
    )
    query_embedding = embed(query)

    compressed_docs = []
    for doc in docs:
        doc_text = doc.get("text", "")
        if not doc_text:
            continue

        doc_embedding = embed(doc_text)
        sim_score = cosine_similarity(query_embedding, doc_embedding)

        if sim_score >= threshold:
            compressed_docs.append(doc)

    print(f"✂️ Context compressed down to {len(compressed_docs)} highly relevant docs.")
    return compressed_docs
