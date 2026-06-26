import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_ollama import ChatOllama                          # <-- local LLM
from dotenv import load_dotenv
from langchain_core.documents import Document
from src.chunking.chunker import extract_and_chunk
from langchain_community.graphs import Neo4jGraph

load_dotenv()

LLM_MODEL = 'llama3.1:8b'

def get_transformer():
    llm = ChatOllama(model=LLM_MODEL, temperature=0)
    return LLMGraphTransformer(llm=llm)

def build_knowledge_graph(
    file_path: str,
    transformer: LLMGraphTransformer = None,
    doctor_id: str = "global",
):
    """
    Extracts chunks from a file, transforms them into graph documents,
    saves them to Neo4j, then stamps every __Entity__ node with doctor_id.
    """
    if transformer is None:
        transformer = get_transformer()          # use local Ollama by default

    graph_store = Neo4jGraph()

    print(f"--- Step 1: Processing and chunking document: {file_path} ---")
    raw_chunks = extract_and_chunk(file_path)

    documents = []
    for i, chunk in enumerate(raw_chunks):
        if isinstance(chunk, str):
            documents.append(
                Document(page_content=chunk, metadata={"source": file_path, "chunk_id": i})
            )
        elif isinstance(chunk, dict):
            page_content = chunk.get("text", "")
            metadata = {k: v for k, v in chunk.items() if k != "text"}
            metadata["source"] = file_path
            documents.append(Document(page_content=page_content, metadata=metadata))
        else:
            documents.append(chunk)

    print(f"--- Step 2: Extracting Graph Entities using LLM (Total Chunks: {len(documents)}) ---")

    for i, doc in enumerate(documents):
        try:
            print(f"Processing chunk {i + 1}/{len(documents)}...")
            graph_documents = transformer.convert_to_graph_documents([doc])
            if graph_documents:
                graph_store.add_graph_documents(
                    graph_documents,
                    baseEntityLabel=True,
                    include_source=True,
                )
        except Exception as e:
            print(f"Warning: Failed to extract graph for chunk {i + 1} due to {e}. Skipping...")

    # ── Stamp all newly created __Entity__ nodes with doctor_id ──────────────
    print(f"--- Step 3: Stamping nodes with doctor_id={doctor_id} ---")
    try:
        graph_store.query(
            "MATCH (n:__Entity__) WHERE n.doctor_id IS NULL SET n.doctor_id = $doctor_id",
            params={"doctor_id": str(doctor_id)},
        )
    except Exception as e:
        print(f"Warning: Could not stamp doctor_id on nodes: {e}")

    print("--- Knowledge Graph Construction Complete! ---")
    graph_store._driver.close()