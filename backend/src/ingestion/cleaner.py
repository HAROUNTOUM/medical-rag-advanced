import re


def clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text)  # extra whitespace
    text = re.sub(r"Page \d+", "", text)  # page numbers
    text = re.sub(r"[^\w\s\.,\!\?]", "", text)
    return text.strip()
