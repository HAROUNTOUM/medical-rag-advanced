from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from src.graphdb.neo4j_client import graph
from src.chunking.chunker import extract_and_chunk


llm = ChatOpenAI(temperature=0, model_name="gpt-4-0125-preview")

llm_transformer = LLMGraphTransformer(llm=llm)
# graph_documents = llm_transformer.convert_to_graph_documents(documents)
