import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# 1. Import logic and routes
from main import run_health_checks
from src.graphdb.neo4j_client import graph_db
from src.vectordb.weaviate_client import vector_db
from src.api.routes import router


# 2. Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Perform a health check on startup
    print("🚀 API Starting up...")
    run_health_checks()
    yield
    print("🛑 Shutting down... Closing Database drivers.")
    graph_db.close()
    vector_db.close()


app = FastAPI(
    title="Medical-RAG Advanced API",
    description="API for querying the merged Knowledge Graph and Vector Store agent.",
    lifespan=lifespan,
)

# 3. Include the router
app.include_router(router)


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Medical RAG Agent API is running. See /docs for usage.",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
