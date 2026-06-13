import pymupdf as fitz
from nltk.tokenize import sent_tokenize
import nltk

# Ensure nltk packages are available inside chunking
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

def extract_and_chunk(pdf_path: str, sentences_per_chunk: int = 4, overlap: int = 1) -> list[dict]:
    """Extract PDF and split into sentence-level chunks."""
    doc = fitz.open(pdf_path)
    chunks = []
    chunk_id = 0
    for page_num, page in enumerate(doc):
        text = page.get_text().strip()
        if not text:
            continue
        sentences = sent_tokenize(text)
        i = 0
        while i < len(sentences):
            chunk_text = ' '.join(sentences[i:i + sentences_per_chunk]).strip()
            if chunk_text:
                chunks.append({'chunk_id': chunk_id, 'text': chunk_text, 'page': page_num + 1})
                chunk_id += 1
            i += sentences_per_chunk - overlap
    doc.close()
    return chunks
