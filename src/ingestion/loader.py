from src.chunking.chunker import extract_and_chunk
from src.vectordb.vector_store import ingest_to_weaviate

def ingest_pdf(pdf_path: str):
    print(f"Reading PDF from {pdf_path}...")
    chunks = extract_and_chunk(pdf_path)
    print(f'✅ {len(chunks)} chunks created')
    ingest_to_weaviate(chunks)
