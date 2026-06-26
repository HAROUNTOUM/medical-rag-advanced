import ollama

def embed(text: str) -> list[float]:
    """
    Embed text using Ollama nomic-embed-text (local).
    Returns a list of floats.
    """
    response = ollama.embeddings(model='nomic-embed-text', prompt=text)
    return response['embedding']
