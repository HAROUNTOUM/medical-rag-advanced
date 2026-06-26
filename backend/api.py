import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Core infrastructure
from main import run_health_checks
from src.graphdb.neo4j_client import graph_db
from src.vectordb.weaviate_client import vector_db

# Auth + multi-tenant routers
from src.auth.router import router as auth_router
from src.api.documents_router import router as documents_router
from src.api.chat_router import router as chat_router
from src.api.routes import router as legacy_router
from src.auth.database import create_tables


# ─── Lifecycle ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] API Starting up...")
    # Create SQLite tables for auth/tenant data
    await create_tables()
    print("[OK] Database tables ready.")
    # Health checks are best-effort — Neo4j/Weaviate being offline must NOT block startup
    try:
        run_health_checks()
    except Exception as e:
        print(f"[WARN] Health checks failed (non-fatal): {e}")
    yield
    print("[STOP] Shutting down...")
    try:
        graph_db.close()
    except Exception:
        pass
    try:
        vector_db.close()
    except Exception:
        pass


# ─── Application ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="RADoct — Multi-Tenant Medical RAG API",
    description=(
        "Production-grade, per-doctor isolated RAG platform. "
        "Hybrid Graph (Neo4j) + Vector (Weaviate) retrieval with full JWT auth."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────

# Auth (register / login / me)
app.include_router(auth_router)

# Knowledge bases + document upload/process
app.include_router(documents_router)

# Chat sessions + isolated RAG messages
app.include_router(chat_router)

# Legacy /health and /ask routes (kept for backward compat)
app.include_router(legacy_router)


# ─── Root ─────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "version": "2.0.0",
        "message": "RADoct Medical RAG API — multi-tenant, per-doctor isolation active.",
        "docs": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
