import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class Neo4jClient:
    """
    Neo4j driver wrapper.  Connection failures at init time are logged but
    never re-raised — the API must be able to start even when Neo4j is offline.
    Callers must check `is_ready()` before using `driver`.
    """

    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "").strip('"')
        self.user = os.getenv("NEO4J_USERNAME", "").strip('"')
        self.password = os.getenv("NEO4J_PASSWORD", "").strip('"')
        self.driver = None

        if not self.uri:
            print("[WARN] NEO4J_URI is missing. Graph features will be disabled.")
            return

        print(f"[INFO] Attempting to connect to Neo4j at: {self.uri.split('://')[0]}://***")
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            print("[OK] Neo4j connection established successfully.")
        except Exception as e:
            print(f"[ERR] Neo4j Connection failed (graph features disabled): {e}")
            if self.driver:
                try:
                    self.driver.close()
                except Exception:
                    pass
            self.driver = None  # <-- NEVER raise — just degrade gracefully

    def is_ready(self) -> bool:
        return self.driver is not None

    def close(self):
        if self.driver:
            try:
                self.driver.close()
            except Exception:
                pass

    def execute_query(self, query: str, parameters: dict | None = None):
        """Execute a Cypher query with retry logic. Returns [] if offline."""
        if not self.driver:
            return []
        for attempt in range(3):
            try:
                with self.driver.session() as session:
                    result = session.run(query, parameters or {})
                    return [record.data() for record in result]
            except Exception as e:
                if attempt == 2:
                    print(f"[ERR] Neo4j query failed after 3 attempts: {e}")
                    return []
                print(f"[WARN] Neo4j Query attempt {attempt + 1} failed. Retrying...")


# Singleton — NEVER raises, degrades gracefully when offline
graph_db = Neo4jClient()
