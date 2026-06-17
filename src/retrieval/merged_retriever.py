from src.retrieval.graph_retriever import search_knowledge_graph
from src.retrieval.retriever import semantic_search_retrieve


def merged_graph_vector_retrieve(query: str, collection, top_k: int = 5) -> list[dict]:
    """
    Combines results from both the Knowledge Graph (Neo4j) and Vector Store (Weaviate).
    """
    print(f"🔍 Performing merged retrieval for: {query}")

    # 1. Fetch from Knowledge Graph
    graph_docs = []
    try:
        graph_docs = search_knowledge_graph(query, top_k=top_k)
        print(f"📊 Graph search found {len(graph_docs)} results.")
    except Exception as e:
        print(f"⚠️ Graph search failed: {e}")

    # 2. Fetch from Vector Store
    vector_docs = []
    if collection is not None:
        try:
            vector_docs = semantic_search_retrieve(query, collection, top_k=top_k)
            print(f"🔗 Vector search found {len(vector_docs)} results.")
        except Exception as e:
            print(f"⚠️ Vector search failed: {e}")
    else:
        print("⚠️ Vector collection is None, skipping vector search.")

    # 3. Interleave and deduplicate
    # We interleave to ensure the LLM gets a balanced view of both structured facts and semantic text.
    if not graph_docs and not vector_docs:
        print("⚠️ No results found from either source.")
        return []

    combined = []
    max_len = max(len(graph_docs), len(vector_docs))

    for i in range(max_len):
        if i < len(graph_docs):
            combined.append(graph_docs[i])
        if i < len(vector_docs):
            combined.append(vector_docs[i])

    # Deduplicate by text content
    seen = set()
    unique_docs = []
    for doc in combined:
        clean_text = doc["text"].strip().lower()
        if clean_text not in seen:
            unique_docs.append(doc)
            seen.add(clean_text)

    # Return a generous context window (up to top_k * 2)
    return unique_docs[: top_k * 2]
