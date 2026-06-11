import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.graphs import Neo4jGraph
from src.chunking.chunker import extract_and_chunk

load_dotenv()

# 1. Initialize your Neo4j Graph connection
# LangChain's Neo4jGraph automatically looks for NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD env vars
graph_store = Neo4jGraph()


def build_knowledge_graph(file_path: str, transformer: LLMGraphTransformer):
    """
    Extracts chunks from a file, transforms them into graph documents,
    and saves them directly to Neo4j.
    """
    print(f"--- Step 1: Processing and chunking document: {file_path} ---")
    # Assuming extract_and_chunk returns a list of text strings or LangChain Document objects
    # If it returns raw text strings, wrap them in Document objects:
    raw_chunks = extract_and_chunk(file_path)

    documents = []
    for i, chunk in enumerate(raw_chunks):
        if isinstance(chunk, str):
            documents.append(
                Document(
                    page_content=chunk, metadata={"source": file_path, "chunk_id": i}
                )
            )
        elif isinstance(chunk, dict):
            # Handle dictionary chunks from extract_and_chunk
            page_content = chunk.get("text", "")
            metadata = {k: v for k, v in chunk.items() if k != "text"}
            metadata["source"] = file_path
            documents.append(Document(page_content=page_content, metadata=metadata))
        else:
            # If it's already a Document object, just pass it through
            documents.append(chunk)

    print(
        f"--- Step 2: Extracting Graph Entities using LLM (Total Chunks: {len(documents)}) ---"
    )
    documents = documents[:10]
    # This calls the LLM to extract nodes and relationships
    graph_documents = transformer.convert_to_graph_documents(documents)
    print(f"Extracted {len(graph_documents)} graph documents.")

    print("--- Step 3: Loading Graph into Neo4j ---")
    # add_graph_documents handles creating nodes, relationships, and linking them to source chunks if configured
    graph_store.add_graph_documents(
        graph_documents,
        baseEntityLabel=True,  # Tags extracted nodes with a generic 'Base' label alongside specific ones
        include_source=True,  # Creates a relationship back to the source Document/Chunk node
    )

    print("--- Knowledge Graph Construction Complete! ---")


allowed_nodes = ["Person", "Hospital", "MedicalCondition", "Symptom", "Treatment"]
allowed_relationships = ["WORKS_AT", "DIAGNOSES", "TREATS", "EXPERIENCES", "LOCATED_IN"]
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.0)
transformer = LLMGraphTransformer(
    llm=llm, allowed_nodes=allowed_nodes, allowed_relationships=allowed_relationships
)

if __name__ == "__main__":
    # Path to your medical textbook or data source
    DATA_PATH = "src/data/livre iECN orthopédie traumatologie v2.pdf"

    if os.path.exists(DATA_PATH):
        build_knowledge_graph(DATA_PATH, transformer)
    else:
        print(f"Please place your data source at {DATA_PATH}")
