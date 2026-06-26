from src.graphdb.neo4j_client import graph_db
from src.llm.llm_client import get_groq_client, LLM_MODEL


def extract_entities_from_query(query: str) -> list[str]:
    """
    Use the LLM to extract key medical entities from the user's query.
    Handles potential language differences between query and graph.
    """
    prompt = f"""
    You are an expert medical entity extractor.
    The underlying medical knowledge base contains French terminology, but queries may be in English.
    
    1. Extract the key medical entities (diseases, symptoms, treatments, etc.) from the query.
    2. For every English entity found, provide its French equivalent.
    3. Return ONLY a single comma-separated list of all terms (both English and French).
    
    Query: {query}
    Entities:
    """
    client = get_groq_client()
    response = client.chat.completions.create(
        model=LLM_MODEL, messages=[{"role": "user", "content": prompt}], max_tokens=150
    )
    entities_text = response.choices[0].message.content
    entities = [e.strip() for e in entities_text.split(",") if e.strip()]
    return entities


def search_knowledge_graph(query: str, col=None, top_k: int = 5, doctor_id: str = "global") -> list[dict]:
    """
    Search the Knowledge Graph for the user query, filtered by doctor_id.
    1. Extract entities from the user's plain-text query.
    2. Query Neo4j for these entities constrained to the doctor's own nodes.
    3. Return a list of context dicts describing the relationships found.
    """
    entities = extract_entities_from_query(query)

    if not entities:
        return []

    graph_context = []

    for entity in entities:
        # Cypher query with doctor_id isolation constraint
        cypher_query = """
        MATCH (n)-[r]-(m)
        WHERE (toLower(n.id) CONTAINS toLower($entity)
           OR any(lbl IN labels(n) WHERE toLower(lbl) CONTAINS toLower($entity)))
          AND n.doctor_id = $doctor_id
        RETURN n.id AS source, type(r) AS relationship, m.id AS target
        LIMIT 10
        """

        results = graph_db.execute_query(
            cypher_query,
            parameters={"entity": entity, "doctor_id": str(doctor_id)},
        )

        for record in results:
            context_str = (
                f"{record['source']} -[{record['relationship']}]-> {record['target']}"
            )
            doc_dict = {"text": context_str, "page": "Graph Database"}
            if doc_dict not in graph_context:
                graph_context.append(doc_dict)

    return graph_context[:top_k]


def get_graph_visualization_data(query: str, doctor_id: str = "global") -> dict:
    """
    Return raw graph nodes and links for the knowledge graph visualization panel.
    Strictly filtered to the authenticated doctor's nodes.
    """
    entities = extract_entities_from_query(query)
    if not entities:
        return {"nodes": [], "links": []}

    nodes = {}
    links = []

    for entity in entities[:5]:  # limit to avoid huge graphs
        cypher_query = """
        MATCH (n)-[r]-(m)
        WHERE (toLower(n.id) CONTAINS toLower($entity))
          AND n.doctor_id = $doctor_id
        RETURN n.id AS source, labels(n) AS source_labels,
               type(r) AS relationship,
               m.id AS target, labels(m) AS target_labels
        LIMIT 15
        """
        try:
            results = graph_db.execute_query(
                cypher_query,
                parameters={"entity": entity, "doctor_id": str(doctor_id)},
            )
            for record in results:
                src = record.get("source", "Unknown")
                tgt = record.get("target", "Unknown")
                src_labels = record.get("source_labels", [])
                tgt_labels = record.get("target_labels", [])

                # Determine node group from labels
                def _group(labels):
                    lbl_str = " ".join(labels).lower() if labels else ""
                    if any(k in lbl_str for k in ["disease", "maladie", "pathology"]):
                        return "disease"
                    if any(k in lbl_str for k in ["drug", "medication", "traitement"]):
                        return "medication"
                    return "symptom"

                if src and src not in nodes:
                    nodes[src] = {"id": src, "label": src, "group": _group(src_labels)}
                if tgt and tgt not in nodes:
                    nodes[tgt] = {"id": tgt, "label": tgt, "group": _group(tgt_labels)}
                if src and tgt:
                    links.append({"source": src, "target": tgt, "label": record.get("relationship", "RELATED")})
        except Exception:
            pass

    return {"nodes": list(nodes.values()), "links": links}
