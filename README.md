# 🩺 Medical-RAG Advanced: Agentic Graph-Vector Pipeline

[![Docker](https://img.shields.io/badge/Docker-Enabled-blue?logo=docker)](./Dockerfile)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Neo4j](https://img.shields.io/badge/Database-Neo4j-008CC1?logo=neo4j)](https://neo4j.com/)
[![Weaviate](https://img.shields.io/badge/VectorStore-Weaviate-green?logo=weaviate)](https://weaviate.io/)

**Medical-RAG Advanced** is a state-of-the-art medical question-answering system that combines the power of **Knowledge Graphs (Neo4j)** and **Vector Search (Weaviate)** through an agentic workflow. It uses advanced query preprocessing and a hybrid retrieval strategy to provide accurate, context-aware answers to complex medical queries.

---

## 🚀 Key Features

-   **Agentic RAG Workflow**: Orchestrates query normalization, intent-aware rewriting, and multi-source retrieval.
-   **Hybrid Retrieval Architecture**:
    *   **Graph DB (Neo4j)**: Captures complex relationships between medical entities (diseases, symptoms, treatments).
    *   **Vector Store (Weaviate)**: Semantic search over deep document embeddings.
-   **Intelligent Query Processing**: Uses LLMs to normalize and rewrite queries for optimal recall.
-   **Production Ready**: Fully containerized with Docker, featuring robust health checks and lifecycle management.
-   **Medical Extraction**: Automated pipeline to build Knowledge Graphs from medical PDFs using `PyMuPDF` and `LLMGraphTransformer`.

---

## 🏗️ Architecture

1.  **Ingestion**: PDFs are chunked and processed. Entities/Relationships are extracted via LLM and stored in Neo4j; Text embeddings are stored in Weaviate.
2.  **Preprocessing**: Incoming queries are normalized (cleaning) and rewritten (expanding) by the agent.
3.  **Merged Retrieval**: The system performs a parallel search across both Graph and Vector databases, merging results for a comprehensive context.
4.  **Synthesis**: A final answer is synthesized by Groq's high-speed inference engine using the merged context.

---

## 🛠️ Tech Stack

-   **Language**: Python 3.11+
-   **API Framework**: FastAPI & Uvicorn
-   **Orchestration**: LangChain & LangChain-Experimental
-   **Inference**: Groq (Llama-3.1-8b)
-   **Local Processing**: Ollama (for KG construction/embeddings)
-   **Databases**: Neo4j (Aura DB) & Weaviate Cloud
-   **PDF Engine**: PyMuPDF

---

## ⚙️ Setup & Configuration

### 1. Environment Variables
Create a `.env` file in the root directory:

```env
# Neo4j Configuration
NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="your-password"

# Weaviate Configuration
WEAVIATE_URL="https://your-instance.weaviate.cloud"
WEAVIATE_API_KEY="your-api-key"

# LLM Configuration
GROQ_API_KEY="your-groq-api-key"
```

### 2. Local Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -m nltk.downloader punkt punkt_tab
```

---

## 🐳 Running with Docker (Recommended)

The easiest way to run the full API is via Docker:

```bash
# 1. Build the image
docker build -t medical-rag-api .

# 2. Run the container
docker run -p 8000:8000 --env-file .env medical-rag-api
```

---

## 📖 Usage

### 🛠️ Data Ingestion & KG Construction
To build the knowledge graph from a medical PDF:
```bash
python main.py build_graph
```

### 🌐 API Endpoints

Once the server is running (locally or via Docker), access the docs at `http://localhost:8000/docs`.

-   **POST `/ask`**: Query the agent.
    ```json
    {
      "query": "What are the primary treatments for orthopaedic trauma?"
    }
    ```
-   **GET `/health`**: Check connectivity to Neo4j and Weaviate.

---

## 📁 Project Structure

```text
├── src/
│   ├── api/          # FastAPI routes and schemas
│   ├── chunking/     # PDF splitting logic
│   ├── graphdb/      # Neo4j client and connectivity
│   ├── ingestion/    # Data loading and KG extraction
│   ├── llm/          # Groq and LLM interface
│   ├── query/        # Query normalization and rewriting
│   ├── retrieval/    # Merged Graph+Vector retrieval logic
│   └── vectordb/     # Weaviate client
├── main.py           # Orchestrator and CLI entry point
├── api.py            # API entry point
└── Dockerfile        # Container definition
```

---

*This project was developed for advanced medical NLP research and agentic RAG exploration.*
