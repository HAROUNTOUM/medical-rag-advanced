from src.ingestion.loader import ingest_pdf
from src.retrieval.retriever import semantic_search_retrieve
from src.llm.llm_client import llm_call
import sys
from src.vectordb.weaviate_client import get_weaviate_client

def main():
    print("Welcome to medical-rag-advanced!")
    
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        PDF_PATH = 'data/medical_book.pdf'
        print("Starting ingestion process...")
        ingest_pdf(PDF_PATH)
        return
        
    client = get_weaviate_client()
    try:
        # 2. Query
        query = 'What diseases affect the skin?'
        print(f"Querying: {query}")
        answer = llm_call(query, retrieve_function=semantic_search_retrieve, use_rag=True)
        print("\nAnswer:\n", answer)
    finally:
        client.close()

if __name__ == "__main__":
    main()
