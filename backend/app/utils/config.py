import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Safe Customer Support RAG Chatbot"
    API_V1_STR: str = "/api"
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./data/app.db")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/vectorstore")
    DOCUMENTS_DIR: str = os.getenv("DOCUMENTS_DIR", "./data/documents")
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "local")  # "local", "gemini", "openai"
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    # Retrieval & Thresholds
    TOP_K_CHUNKS: int = 4
    SIMILARITY_THRESHOLD_HIGH: float = 0.65
    SIMILARITY_THRESHOLD_MODERATE: float = 0.40
    SIMILARITY_THRESHOLD_LOW: float = 0.20
    
    # Upload limits
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".txt", ".docx", ".md"}

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
