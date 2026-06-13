from src.ingestion.loader import ingest_pdf
from src.llm.llm_client import llm_call
import sys
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_groq import ChatGroq
from src.graphdb.neo4j_client import Neo4jClient
from src.ingestion.graph_extractor import build_knowledge_graph
from src.retrieval.graph_retriever import search_knowledge_graph


def answer_user(query: str):
    # This will return a list of relationship triads you can append to context
    graph_context = search_knowledge_graph(query)
    context_string = "\n".join(graph_context)
    return context_string


def main():
    print("Welcome to medical-rag-advanced!")

    if len(sys.argv) > 1 and sys.argv[1] == "ingest_pdf":
        PDF_PATH = "data/medical_book.pdf"
        print("Starting PDF vector ingestion process...")
        ingest_pdf(PDF_PATH)
        return

    if True:
        print("Starting Knowledge Graph extraction process...")
        allowed_nodes = [
            "Person",
            "Hospital",
            "MedicalCondition",
            "Symptom",
            "Treatment",
        ]
        allowed_relationships = [
            "WORKS_AT",
            "DIAGNOSES",
            "TREATS",
            "EXPERIENCES",
            "LOCATED_IN",
        ]
        llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.0)
        transformer = LLMGraphTransformer(
            llm=llm,
            allowed_nodes=allowed_nodes,
            allowed_relationships=allowed_relationships,
        )
        DATA_PATH = "src/data/livre iECN orthopédie traumatologie v2.pdf"
        build_knowledge_graph(DATA_PATH, transformer)
        return

    client = Neo4jClient()
    try:
        # Standard query loop using the knowledge graph retriever
        query = "What diseases affect the skin?"
        print(f"Querying Knowledge Graph for: {query}")
        answer = llm_call(query, retrieve_function=search_knowledge_graph, use_rag=True)
        print("\nAnswer:\n", answer)
    finally:
        client.close()


if __name__ == "__main__":
    main()
