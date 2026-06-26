import weaviate.classes as wvc
from src.embeddings.embedder import embed


def _doctor_filter(doctor_id: str):
    """Build a Weaviate where-filter for doctor_id isolation."""
    return wvc.query.Filter.by_property("doctor_id").equal(str(doctor_id))


def semantic_search_retrieve(query: str, collection, top_k: int = 5, doctor_id: str = "global") -> list[dict]:
    results = collection.query.near_vector(
        near_vector=embed(query),
        limit=top_k,
        filters=_doctor_filter(doctor_id),
        return_metadata=wvc.query.MetadataQuery(distance=True),
    )
    return [{"text": o.properties["text"], "page": o.properties.get("page", 0)} for o in results.objects]


def bm25_retrieve(query: str, collection, top_k: int = 5, doctor_id: str = "global") -> list[dict]:
    results = collection.query.bm25(
        query=query,
        limit=top_k,
        filters=_doctor_filter(doctor_id),
    )
    return [{"text": o.properties["text"], "page": o.properties.get("page", 0)} for o in results.objects]


def hybrid_retrieve(query: str, collection, alpha: float = 0.5, top_k: int = 5, doctor_id: str = "global") -> list[dict]:
    results = collection.query.hybrid(
        query=query,
        vector=embed(query),
        alpha=alpha,
        limit=top_k,
        filters=_doctor_filter(doctor_id),
    )
    return [{"text": o.properties["text"], "page": o.properties.get("page", 0)} for o in results.objects]


def semantic_search_with_reranking(
    query: str,
    rerank_property: str,
    collection,
    rerank_query: str = None,
    top_k: int = 5,
    doctor_id: str = "global",
) -> list[dict]:
    rerank_q = rerank_query if rerank_query else query
    results = collection.query.near_vector(
        near_vector=embed(query),
        limit=max(top_k, 10),
        filters=_doctor_filter(doctor_id),
        return_metadata=wvc.query.MetadataQuery(distance=True),
    )
    docs = [{"text": o.properties["text"], "page": o.properties.get("page", 0)} for o in results.objects]
    query_terms = {term for term in rerank_q.lower().split() if term}
    scored_docs = []
    for doc in docs:
        text_terms = set(doc.get(rerank_property, doc.get("text", "")).lower().split())
        score = len(query_terms & text_terms)
        scored_docs.append((score, doc))
    scored_docs.sort(key=lambda item: item[0], reverse=True)
    return [doc for score, doc in scored_docs[:top_k]]
