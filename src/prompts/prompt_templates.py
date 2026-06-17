from src.retrieval.retriever import semantic_search_with_reranking
from src.vectordb.vector_store import get_collection

DEFAULT_PROMPT = (
    "You are a helpful medical assistant. "
    "Use ONLY the following documents to answer the question accurately. "
    "If the documents do not contain the answer, explicitly state that you do not have enough information from the provided documents. "
    "Do not use your own knowledge to answer if the context is missing.\n\n"
    "Documents:\n{documents}\n\n"
    "Question: {query}\n"
    "Answer:"
)


def format_docs(docs: list[dict]) -> str:
    """Format retrieved chunks into a structured string for the prompt."""
    return "\n\n".join(
        [
            f"Document {i} (Page {d['page']}):\n{d['text']}"
            for i, d in enumerate(docs, 1)
        ]
    )


def generate_final_prompt(
    query: str,
    top_k: int,
    retrieve_function: callable,
    rerank_query: str = None,
    rerank_property: str = None,
    use_rerank: bool = False,
    use_rag: bool = True,
) -> str:
    if not use_rag:
        return query

    col = None
    if use_rag:
        try:
            col = get_collection()
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize Weaviate client: {e}")
            print("Fallback: proceeding without vector context.")

    if use_rerank and rerank_property and col:
        docs = semantic_search_with_reranking(
            query=query,
            rerank_property=rerank_property,
            collection=col,
            rerank_query=rerank_query,
            top_k=top_k,
        )
    else:
        docs = retrieve_function(query, col, top_k)

    return DEFAULT_PROMPT.format(query=query, documents=format_docs(docs))
