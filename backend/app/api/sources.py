from fastapi import APIRouter, HTTPException
from backend.app.rag.vector_store import vector_store

router = APIRouter(prefix="/sources", tags=["sources"])

@router.get("/{chunk_id}")
async def get_source_chunk(chunk_id: str):
    chunk = vector_store.get_chunk(chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Source chunk not found in vector store.")
    return chunk
