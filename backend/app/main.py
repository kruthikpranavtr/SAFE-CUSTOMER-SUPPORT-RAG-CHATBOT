import os
from contextlib import asynccontextmanager
# pyrefly: ignore [missing-import]
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.utils.config import settings
from backend.app.database.db import init_db
from backend.app.api.documents import initialize_sample_documents_if_empty
from backend.app.api.chat import router as chat_router
from backend.app.api.documents import router as documents_router
from backend.app.api.sources import router as sources_router
from backend.app.api.feedback import router as feedback_router
from backend.app.api.study import router as study_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.escalations import router as escalations_router
from backend.app.api.risk_register import router as risk_register_router
from backend.app.api.guardrails import router as guardrails_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite DB schema
    init_db()
    # Startup: Auto-index sample policies if knowledgebase is empty
    initialize_sample_documents_if_empty()
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Safe Customer Support RAG Chatbot with uncertainty communication, source attribution, and user-study testing module.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(sources_router, prefix=settings.API_V1_STR)
app.include_router(feedback_router, prefix=settings.API_V1_STR)
app.include_router(study_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(escalations_router, prefix=settings.API_V1_STR)
app.include_router(risk_register_router, prefix=settings.API_V1_STR)
app.include_router(guardrails_router, prefix=settings.API_V1_STR)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "llm_provider": settings.LLM_PROVIDER,
        "vector_db": "ChromaDB"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
