from src.llm.llm_client import get_groq_client


def expand_query(query: str) -> list[str]:
    prompt = f"""You are a helpful medical assistant. Expand the following query into exactly 3 different variations.
    The variations should use synonyms and capture different angles of the same medical intent.
    Return ONLY the 3 variations separated by a newline character. No numbering, no bullets, no introduction.
    
    Original Query: {query}
    """
    client = get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
    )
    result_text = response.choices[0].message.content.strip()
    variations = [line.strip() for line in result_text.split("\n") if line.strip()]
    return variations
if __name__ == "__main__":
    test_query = "what is the treatment of diabetes?"
    print(f"Original: {test_query}")
    print("Variations:", expand_query(test_query))
