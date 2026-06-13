import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from langchain_experimental.graph_transformers import LLMGraphTransformer
from dotenv import load_dotenv
from langchain_core.documents import Document
from src.chunking.chunker import extract_and_chunk
from langchain_community.graphs import Neo4jGraph

load_dotenv()


def build_knowledge_graph(file_path: str, transformer: LLMGraphTransformer):
    """
    Extracts chunks from a file, transforms them into graph documents,
    and saves them directly to Neo4j.
    """
    graph_store = Neo4jGraph()

    print(f"--- Step 1: Processing and chunking document: {file_path} ---")
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
            page_content = chunk.get("text", "")
            metadata = {k: v for k, v in chunk.items() if k != "text"}
            metadata["source"] = file_path
            documents.append(Document(page_content=page_content, metadata=metadata))
        else:
            documents.append(chunk)

    print(
        f"--- Step 2: Extracting Graph Entities using LLM (Total Chunks: {len(documents)}) ---"
    )

    # Process chunks in small batches to prevent a single Groq parse error from destroying the entire job
    for i, doc in enumerate(documents):
        try:
            print(f"Processing chunk {i + 1}/{len(documents)}...")
            # We process 1 by 1 because LLM tools can occasionally hallucinate bad JSON syntax
            graph_documents = transformer.convert_to_graph_documents([doc])

            if graph_documents:
                graph_store.add_graph_documents(
                    graph_documents,
                    baseEntityLabel=True,
                    include_source=True,
                )
        except Exception as e:
            print(
                f"Warning: Failed to extract graph for chunk {i + 1} due to {e}. Skipping..."
            )

    print("--- Knowledge Graph Construction Complete! ---")
