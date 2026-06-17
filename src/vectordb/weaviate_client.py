import os
import weaviate
from dotenv import load_dotenv, find_dotenv

# Ensure environment variables are loaded
load_dotenv(find_dotenv())


class WeaviateClient:
    """
    Singleton client to manage the connection to Weaviate Cloud.
    Patterned after Neo4jClient for consistency.
    """

    def __init__(self):
        self.url = os.getenv("WEAVIATE_URL", "").strip('"')
        self.api_key = os.getenv("WEAVIATE_API_KEY", "").strip('"')
        self.client = None

        if not self.url:
            print(
                "⚠️  WEAVIATE_URL is missing. Weaviate-based vector search will be disabled."
            )
            return

        print(f"📡 Attempting to connect to Weaviate at: {self.url.split('//')[-1]}...")

        try:
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=self.url,
                auth_credentials=weaviate.auth.AuthApiKey(self.api_key),
                skip_init_checks=False,
            )
            if self.client.is_ready():
                print("✅ Weaviate connection established successfully.")
            else:
                print("❌ Weaviate connection established but cluster is not ready.")
        except Exception as e:
            print(f"❌ Weaviate Connection failed: {e}")
            self.client = None

    def close(self):
        """Close the underlying connection."""
        if self.client:
            self.client.close()

    def is_ready(self) -> bool:
        """Check if the client is connected and the cluster is ready."""
        try:
            return self.client is not None and self.client.is_ready()
        except Exception:
            return False


# Initialize the singleton instance
vector_db = WeaviateClient()
