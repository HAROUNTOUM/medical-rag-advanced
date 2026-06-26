def normalize_query(user_query: str) -> str:
    query = user_query.strip().lower()
    query = query.replace("\n", " ")
    return query
