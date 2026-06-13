import os
import weaviate
from dotenv import load_dotenv

load_dotenv()

def get_weaviate_client():
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=os.getenv('WEAVIATE_URL'),
        auth_credentials=weaviate.auth.AuthApiKey(os.getenv('WEAVIATE_API_KEY'))
    )
    return client
