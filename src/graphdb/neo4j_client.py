from neo4j import GraphDatabase

# Use find_dotenv to make sure we find the .env file regardless of where we run from
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())


class Neo4jClient:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "").strip('"')
        self.user = os.getenv("NEO4J_USERNAME", "").strip('"')
        self.password = os.getenv("NEO4J_PASSWORD", "").strip('"')

        if not self.uri:
            raise ValueError(
                "NEO4J_URI is missing! Please check your .env file or environment variables."
            )

        print(f"📡 Attempting to connect to Neo4j at: {self.uri.split('://')[0]}://***")

        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            self.driver.verify_connectivity()
            print("✅ Neo4j connection established successfully.")
        except Exception as e:
            print(f"❌ Neo4j Connection failed: {e}")
            if hasattr(self, "driver"):
                self.driver.close()
            raise e

    def close(self):
        if hasattr(self, "driver"):
            self.driver.close()

    def execute_query(self, query: str, parameters=None):
        """Execute a Cypher query with automatic retry logic."""
        for attempt in range(3):
            try:
                with self.driver.session() as session:
                    result = session.run(query, parameters)
                    return [record.data() for record in result]
            except Exception as e:
                if attempt == 2:
                    raise e
                print(f"⚠️ Neo4j Query attempt {attempt + 1} failed. Retrying...")


# Initialize a global client to use in other modules
graph_db = Neo4jClient()
