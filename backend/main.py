from src.ingestion.loader import ingest_pdf
from src.llm.llm_client import llm_call
import sys
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_ollama import ChatOllama
from src.ingestion.graph_extractor import build_knowledge_graph
from src.retrieval.merged_retriever import merged_graph_vector_retrieve
from src.graphdb.neo4j_client import graph_db
from src.vectordb.weaviate_client import vector_db
from src.query.query_normalizer import normalize_query
from src.query.query_rewriter import rewrite_query


def run_health_checks():
    """Verify that all backend services are reachable."""
    print("\n[HEALTH] [Step 1/3] Running System Health Checks...")

    status = {"neo4j": "🔴 Offline", "weaviate": "🔴 Offline"}

    # Check Neo4j
    try:
        graph_db.driver.verify_connectivity()
        status["neo4j"] = "🟢 Healthy"
    except Exception as e:
        print(f"   [ERR] Neo4j Error: {e}")

    print(f"   - Neo4j Knowledge Graph: {status['neo4j']}")

    # Check Weaviate
    if vector_db.is_ready():
        status["weaviate"] = "🟢 Healthy"
    else:
        status["weaviate"] = "🔴 Offline/Not Configured"
    print(f"   - Weaviate Vector Store: {status['weaviate']}")

    return status


def run_agentic_workflow(query: str):
    """
    Orchestrates the agentic RAG process:
    1. Health Checks
    2. Intent & Entity Extraction (Internal to retriever)
    3. Merged Graph + Vector Retrieval
    4. Synthesis & Response
    """
    # 1. Health Checks
    run_health_checks()

    # 2. Start Agentic Workflow
    print(f"\n[BIO] [Step 2/3] Initiating Agentic Workflow for: '{query}'")

    # Pre-processing: Normalize and/or Rewrite
    processed_query = normalize_query(query)
    print(f"   - Normalized query: {processed_query}")

    try:
        # Step A: Query Rewriting (Agentic Step)
        print("   - Rewriting query for better RAG recall...")
        search_query = rewrite_query(processed_query)
        print(f"   - Search query: {search_query}")

        # Step B: Retrieval and Synthesis
        answer = llm_call(
            query=search_query,
            retrieve_function=merged_graph_vector_retrieve,
            use_rag=True,
        )

        print("\n[OK] [Step 3/3] Agent Synthesis Complete.")
        return answer

    except Exception as e:
        print(f"\n[ERR] [Error] Workflow failed: {e}")
        return f"Agent Error: {str(e)}"
    finally:
        pass


def run_agentic_workflow_isolated(
    query: str,
    doctor_id: str = "global",
) -> tuple[str, dict | None, list]:
    """
    Tenant-isolated version of the RAG workflow.
    Used by the chat API endpoint. Returns (answer, graph_data, citations).
    - All Weaviate queries are filtered by doctor_id.
    - All Neo4j Cypher queries enforce AND n.doctor_id = $doctor_id.
    - graph_data is returned for the live knowledge graph visualization.
    """
    from src.retrieval.graph_retriever import get_graph_visualization_data
    from src.vectordb.vector_store import get_collection

    print(f"\n[SEC] Isolated RAG for doctor_id={doctor_id}, query='{query}'")

    processed_query = normalize_query(query)
    try:
        search_query = rewrite_query(processed_query)
    except Exception:
        search_query = processed_query

    collection = get_collection()

    # Build a partial retrieve function that injects doctor_id
    def _retrieve(q, col, top_k=5):
        return merged_graph_vector_retrieve(q, col, top_k=top_k, doctor_id=doctor_id)

    try:
        answer = llm_call(
            query=search_query,
            retrieve_function=_retrieve,
            use_rag=True,
        )
    except Exception as e:
        answer = f"I encountered an error while processing your request: {str(e)}"

    # Build graph visualization data from Neo4j (doctor-scoped)
    graph_data = None
    try:
        graph_data = get_graph_visualization_data(query=search_query, doctor_id=doctor_id)
    except Exception as e:
        print(f"[WARN] Could not build graph data: {e}")

    return answer, graph_data, []



def main():
    """Main CLI entry point."""
    print("Welcome to Medical-RAG Advanced Orchestrator!")

    # Ingestion or Building commands
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "ingest_pdf":
            ingest_pdf("data/medical_book.pdf")
            return
        elif command == "build_graph":
            llm = ChatOllama(model="llama3.2:latest", temperature=0.0)
            transformer = LLMGraphTransformer(llm=llm)
            build_knowledge_graph(
                "src/data/livre iECN orthopédie traumatologie v2.pdf", transformer
            )
            return

    # Default: Run a sample query through the agentic workflow
    query = "What diseases affect the skin?"
    result = run_agentic_workflow(query)

    print("\n" + "=" * 30)
    print("🤖 AGENT RESPONSE:")
    print("-" * 30)
    print(result)
    print("=" * 30 + "\n")

    # Clean up for CLI
    graph_db.close()
    vector_db.close()


if __name__ == "__main__":
    main()
