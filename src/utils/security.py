def check_query_validity(text: str):
    banned_words = [
        "ignore previous",
        "jailbreak",
        "ignore previous instructions",
        "ignore all previous instructions",
    ]
    for word in banned_words:
        if word in text:
            raise ValueError("invalid query")
