import os
from groq import Groq
from dotenv import load_dotenv
from src.prompts.prompt_templates import generate_final_prompt

load_dotenv()

LLM_MODEL = 'llama-3.1-8b-instant'

def get_groq_client():
    return Groq(api_key=os.getenv('GROQ_API_KEY'))

def llm_call(query: str,
             retrieve_function: callable = None,
             top_k: int = 5,
             use_rag: bool = True,
             use_rerank: bool = False,
             rerank_property: str = None,
             rerank_query: str = None) -> str:
    
    prompt = generate_final_prompt(
        query=query,
        top_k=top_k,
        retrieve_function=retrieve_function,
        rerank_query=rerank_query,
        rerank_property=rerank_property,
        use_rerank=use_rerank,
        use_rag=use_rag
    )
    
    client = get_groq_client()
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content
