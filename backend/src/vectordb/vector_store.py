import weaviate.classes as wvc
from src.vectordb.weaviate_client import vector_db
from src.embeddings.embedder import embed

COLLECTION_NAME = "MedicalBook"


def get_collection():
    """Retrieve the collection using the global vector_db singleton."""
    if not vector_db.is_ready():
        return None
    return vector_db.client.collections.get(COLLECTION_NAME)


def _ensure_collection_exists(client) -> None:
    """Create the shared MedicalBook collection if it doesn't exist yet."""
    if client.collections.exists(COLLECTION_NAME):
        return
    client.collections.create(
        name=COLLECTION_NAME,
        vectorizer_config=wvc.config.Configure.Vectorizer.none(),
        properties=[
            wvc.config.Property(
                name="text",
                data_type=wvc.config.DataType.TEXT,
                tokenization=wvc.config.Tokenization.WORD,
            ),
            wvc.config.Property(name="page", data_type=wvc.config.DataType.INT),
            wvc.config.Property(name="chunk_id", data_type=wvc.config.DataType.INT),
            # ── Tenant isolation property ─────────────────────────────────────
            wvc.config.Property(
                name="doctor_id",
                data_type=wvc.config.DataType.TEXT,
                tokenization=wvc.config.Tokenization.FIELD,
            ),
        ],
    )
    print(f"[OK] Collection created: {COLLECTION_NAME}")


def ingest_to_weaviate(chunks: list[dict], doctor_id: str = "global"):
    """Batch-insert chunks into the shared Weaviate collection, stamped with doctor_id."""
    if not vector_db.is_ready():
        print("[ERR] Cannot ingest: Weaviate client is not ready.")
        return

    client = vector_db.client
    _ensure_collection_exists(client)

    collection = client.collections.get(COLLECTION_NAME)
    total = len(chunks)
    with collection.batch.dynamic() as batch:
        for i, chunk in enumerate(chunks):
            batch.add_object(
                properties={
                    "text": chunk["text"],
                    "page": chunk.get("page", 0),
                    "chunk_id": chunk.get("chunk_id", i),
                    "doctor_id": str(doctor_id),   # ← tenant isolation stamp
                },
                vector=embed(chunk["text"]),
            )
            if (i + 1) % 50 == 0 or (i + 1) == total:
                print(f"  [RECV] {i + 1}/{total} chunks (doctor_id={doctor_id})...")

    print(f"[DONE] Done — {total} chunks ingested for doctor_id={doctor_id}")
    # Note: We do NOT close the client here because it's a singleton managed elsewhere
