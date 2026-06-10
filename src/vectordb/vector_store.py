import weaviate.classes as wvc
from src.vectordb.weaviate_client import get_weaviate_client
from src.embeddings.embedder import embed

COLLECTION_NAME = 'MedicalBook'

def get_collection():
    client = get_weaviate_client()
    return client.collections.get(COLLECTION_NAME)

def ingest_to_weaviate(chunks: list[dict]):
    """Delete old collection, create new one and batch insert chunks."""
    client = get_weaviate_client()
    
    # Clean start
    if client.collections.exists(COLLECTION_NAME):
        client.collections.delete(COLLECTION_NAME)
        print(f'🗑️  Deleted: {COLLECTION_NAME}')

    # Create collection with BM25 tokenization enabled
    client.collections.create(
        name=COLLECTION_NAME,
        vectorizer_config=wvc.config.Configure.Vectorizer.none(),
        properties=[
            wvc.config.Property(
                name='text',
                data_type=wvc.config.DataType.TEXT,
                tokenization=wvc.config.Tokenization.WORD
            ),
            wvc.config.Property(name='page',     data_type=wvc.config.DataType.INT),
            wvc.config.Property(name='chunk_id', data_type=wvc.config.DataType.INT),
        ]
    )
    print(f'✅ Collection created: {COLLECTION_NAME}')

    # Batch insert
    collection = client.collections.get(COLLECTION_NAME)
    total      = len(chunks)
    with collection.batch.dynamic() as batch:
        for i, chunk in enumerate(chunks):
            batch.add_object(
                properties={'text': chunk['text'], 'page': chunk['page'], 'chunk_id': chunk['chunk_id']},
                vector=embed(chunk['text'])
            )
            if (i + 1) % 50 == 0 or (i + 1) == total:
                print(f'  📥 {i + 1}/{total} chunks...')

    print(f'🎉 Done — {total} chunks in Weaviate')
    client.close()
