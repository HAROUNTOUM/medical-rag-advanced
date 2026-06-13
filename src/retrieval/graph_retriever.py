from src.graphdb.neo4j_client import graph_db
from src.llm.llm_client import get_groq_client, LLM_MODEL


def extract_entities_from_query(query: str) -> list[str]:
    """
    Use the LLM to extract key medical entities from the user's query.
    """
    prompt = f"""
    You are an expert medical entity extractor.
    Extract the key medical entities (e.g., diseases, symptoms, treatments, medications) from the query below.
    Return ONLY a comma-separated list of entities. Do not add any extra text.
    
    Query: {query}
    Entities:
    """
    client = get_groq_client()
    response = client.chat.completions.create(
        model=LLM_MODEL, messages=[{"role": "user", "content": prompt}], max_tokens=100
    )
    # Process output into a clean list of entities
    entities_text = response.choices[0].message.content
    entities = [e.strip() for e in entities_text.split(",") if e.strip()]
    return entities


def search_knowledge_graph(query: str, col=None, top_k: int = 5) -> list[dict]:
    """
    Search the Knowledge Graph for the user query.
    1. Extract entities from the user's plain-text query.
    2. Query Neo4j for these entities and their immediate relationships.
    3. Return a list of context dicts describing the relationships found.
    """
    entities = extract_entities_from_query(query)

    if not entities:
        return []

    graph_context = []

    for entity in entities:
        # A simple Cypher query that finds nodes vaguely matching the entity name
        # and retrieves their direct neighbors.
        cypher_query = """
        MATCH (n)-[r]-(m)
        WHERE toLower(n.id) CONTAINS toLower($entity) 
           OR toLower(n.label) CONTAINS toLower($entity)
        RETURN n.id AS source, type(r) AS relationship, m.id AS target
        LIMIT 10
        """

        results = graph_db.execute_query(cypher_query, parameters={"entity": entity})

        for record in results:
            # We format the graph triad into a readable sentence or semantic string
            # e.g., "Paracetamol -[TREATS]-> Headache"
            context_str = (
                f"{record['source']} -[{record['relationship']}]-> {record['target']}"
            )
            # Create the dictionary structure expected by `format_docs`
            doc_dict = {"text": context_str, "page": "Graph Database"}
            if doc_dict not in graph_context:
                graph_context.append(doc_dict)

    return graph_context[:top_k]
