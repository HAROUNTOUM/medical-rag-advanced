from src.retrieval.graph_retriever import search_knowledge_graph
from src.retrieval.retriever import semantic_search_retrieve


def merged_graph_vector_retrieve(
    query: str, collection, top_k: int = 5, doctor_id: str = "global"
) -> list[dict]:
    """
    Combines results from both the Knowledge Graph (Neo4j) and Vector Store (Weaviate).
    Both searches are strictly filtered to the authenticated doctor's data.
    Enhanced with Multi-Query Expansion and Contextual Compression.
    """
    print(
        f"[SEARCH] Performing merged retrieval for: {query} (doctor_id={doctor_id})"
    )

    # 1. Fetch from Knowledge Graph (doctor-filtered Cypher)
    graph_docs = []
    try:
        graph_docs = search_knowledge_graph(
            query, top_k=top_k, doctor_id=doctor_id
        )
        print(f"[GRAPH] Graph search found {len(graph_docs)} results.")
    except Exception as e:
        print(f"[WARN] Graph search failed: {e}")

    # 2. Fetch from Vector Store using Multi-Query Expansion & Doctor Filtering
    vector_docs = []
    if collection is not None:
        try:
            from src.query.expansion import expand_query

            variations = expand_query(query)
            variations.append(query)  # ensure original query is also used
            print(
                f"✨ Expanded into {len(variations)} queries for vector search."
            )

            for var_query in variations:
                # مدمج: يتم تمرير الـ doctor_id لضمان تصفية نتائج البحث المتفرعة
                var_docs = semantic_search_retrieve(
                    var_query, collection, top_k=top_k, doctor_id=doctor_id
                )
                vector_docs.extend(var_docs)

            print(
                f"🔗 Vector search generated {len(vector_docs)} multi-query results (filtered by doctor)."
            )
        except Exception as e:
            print(f"[WARN] Vector search failed: {e}")
    else:
        print("[WARN] Vector collection is None, skipping vector search.")

    # 3. Interleave and deduplicate
    if not graph_docs and not vector_docs:
        print("[WARN] No results found from either source.")
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

    # 4. Contextual Compression
    # Apply compression to the deduplicated results to cut off any remaining irrelevant fluff
    try:
        from src.retrieval.post_processing import compress_context

        final_docs = unique_docs[: top_k * 2]
        compressed_docs = compress_context(query, final_docs, threshold=0.76)

        # Fallback to returning top documents if compression is too aggressive
        if not compressed_docs and final_docs:
            print(
                "⚠️ Compression removed all docs. Falling back to uncompressed unique docs."
            )
            return final_docs

        return compressed_docs
    except Exception as e:
        print(
            f"[WARN] Compression failed, falling back to unique docs: {e}"
        )
        return unique_docs[: top_k * 2]