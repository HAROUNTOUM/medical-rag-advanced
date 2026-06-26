from src.llm.llm_client import get_groq_client, LLM_MODEL


def rewrite_query(query):
    prompt = f"""Rewrite the following user query so it is optimized for medical document retrieval.
Preserve the meaning but improve clarity and specificity.
Return ONLY the rewritten query as a single sentence. Do not add any explanation or commentary.

Original query: {query}
Rewritten query:"""

    response = get_groq_client().chat.completions.create(
        model=LLM_MODEL, messages=[{"role": "user", "content": prompt}], max_tokens=100
    )

    return response.choices[0].message.content.strip().split("\n")[0]
