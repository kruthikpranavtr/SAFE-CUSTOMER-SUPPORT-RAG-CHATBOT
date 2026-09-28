import os
import uuid
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from backend.app.utils.config import settings
from backend.app.models.schemas import DocumentInfo, DocumentChunk
from backend.app.database.db import execute_query, execute_insert, execute_commit
from backend.app.rag.document_processor import DocumentProcessor
from backend.app.rag.vector_store import vector_store

router = APIRouter(prefix="/documents", tags=["documents"])

def index_document_file(doc_id: str, file_path: str, filename: str) -> int:
    pages_data = DocumentProcessor.extract_text_from_file(file_path)
    chunks = DocumentProcessor.chunk_document(pages_data, doc_id, filename)
    chunk_count = vector_store.add_chunks(chunks)
    execute_commit(
        "UPDATE documents SET status = 'Ready', chunk_count = ? WHERE id = ?",
        (chunk_count, doc_id)
    )
    return chunk_count

@router.get("", response_model=List[DocumentInfo])
async def list_documents():
    rows = execute_query("SELECT id, filename, file_type, file_path, status, chunk_count, file_size, uploaded_at FROM documents ORDER BY uploaded_at DESC")
    return [DocumentInfo(**r) for r in rows]

@router.post("/upload", response_model=DocumentInfo)
async def upload_document(file: UploadFile = File(...)):
    # 1. Validation
    filename = os.path.basename(file.filename or "uploaded_file.txt")
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file extension '{ext}'. Supported: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    doc_id = str(uuid.uuid4())
    os.makedirs(settings.DOCUMENTS_DIR, exist_ok=True)
    target_path = os.path.join(settings.DOCUMENTS_DIR, f"{doc_id}_{filename}")

    # Read and validate size & content
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes). Cannot index empty documents.")

    if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024)}MB.")

    # Duplicate document check
    existing_doc = execute_query("SELECT id FROM documents WHERE filename = ?", (filename,))
    if existing_doc:
        raise HTTPException(status_code=400, detail=f"Duplicate document: '{filename}' is already indexed in the knowledge base.")

    with open(target_path, "wb") as f:
        f.write(contents)

    # Validate readability and non-corruption before database insertion
    try:
        pages_data = DocumentProcessor.extract_text_from_file(target_path)
        total_text_len = sum(len(p.get("text", "").strip()) for p in pages_data)
        if not pages_data or total_text_len == 0:
            if os.path.exists(target_path):
                os.remove(target_path)
            raise HTTPException(status_code=400, detail=f"Corrupted or unreadable file: '{filename}' contains no extractable text.")
    except Exception as e:
        if os.path.exists(target_path):
            os.remove(target_path)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to read file '{filename}': {str(e)}")

    now = datetime.utcnow().isoformat()
    execute_insert(
        """
        INSERT INTO documents (id, filename, file_type, file_path, status, chunk_count, file_size, uploaded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (doc_id, filename, ext.replace(".", "").upper(), target_path, "Processing", 0, len(contents), now)
    )

    # Index into vector database
    try:
        chunk_count = index_document_file(doc_id, target_path, filename)
        status = "Ready"
    except Exception as e:
        execute_commit("UPDATE documents SET status = 'Error' WHERE id = ?", (doc_id,))
        raise HTTPException(status_code=500, detail=f"Failed to process and index document: {str(e)}")

    return DocumentInfo(
        id=doc_id,
        filename=filename,
        file_type=ext.replace(".", "").upper(),
        file_path=target_path,
        status=status,
        chunk_count=chunk_count,
        file_size=len(contents),
        uploaded_at=now
    )

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    rows = execute_query("SELECT id, file_path FROM documents WHERE id = ?", (doc_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc = rows[0]
    # Remove from ChromaDB
    vector_store.delete_document_chunks(doc_id)
    
    # Remove physical file if exists
    if doc["file_path"] and os.path.exists(doc["file_path"]):
        try:
            os.remove(doc["file_path"])
        except Exception:
            pass

    # Remove from SQLite
    execute_commit("DELETE FROM documents WHERE id = ?", (doc_id,))
    return {"status": "success", "message": f"Document {doc_id} deleted"}

@router.post("/reindex")
async def reindex_all_documents():
    docs = execute_query("SELECT id, filename, file_path FROM documents")
    reindexed_count = 0
    total_chunks = 0
    for doc in docs:
        if doc["file_path"] and os.path.exists(doc["file_path"]):
            vector_store.delete_document_chunks(doc["id"])
            c_count = index_document_file(doc["id"], doc["file_path"], doc["filename"])
            total_chunks += c_count
            reindexed_count += 1

    return {
        "status": "success",
        "documents_reindexed": reindexed_count,
        "total_chunks": total_chunks
    }

@router.get("/{doc_id}/chunks")
async def get_document_chunks(doc_id: str):
    chunks = vector_store.get_document_chunks(doc_id)
    return {"document_id": doc_id, "chunk_count": len(chunks), "chunks": chunks}

def initialize_sample_documents_if_empty():
    """
    Scans data/documents/ for initial sample documents and indexes them if documents table is empty.
    """
    if not os.path.exists(settings.DOCUMENTS_DIR):
        return

    existing_rows = execute_query("SELECT file_path FROM documents")
    existing_paths = {os.path.abspath(row["file_path"]) for row in existing_rows} if existing_rows else set()

    sample_files = [f for f in os.listdir(settings.DOCUMENTS_DIR) if os.path.isfile(os.path.join(settings.DOCUMENTS_DIR, f))]
    for fname in sample_files:
        fpath = os.path.join(settings.DOCUMENTS_DIR, fname)
        if os.path.abspath(fpath) in existing_paths:
            continue
        ext = os.path.splitext(fname)[1].lower()
        if ext in settings.ALLOWED_EXTENSIONS:
            doc_id = str(uuid.uuid4())
            size = os.path.getsize(fpath)
            now = datetime.utcnow().isoformat()
            
            # Format clean display title
            clean_title = fname
            for s_ext in [".pdf", ".txt", ".md", ".docx"]:
                clean_title = clean_title.replace(s_ext, "").replace(s_ext.upper(), "")
            clean_title = clean_title.replace("_", " ").title() + (" (Policy Document)" if "policy" in fname.lower() else " (FAQ)")
            
            execute_insert(
                """
                INSERT INTO documents (id, filename, file_type, file_path, status, chunk_count, file_size, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (doc_id, clean_title, ext.replace(".", "").upper(), fpath, "Ready", 0, size, now)
            )
            try:
                index_document_file(doc_id, fpath, clean_title)
            except Exception as e:
                print(f"Error indexing sample document {fname}: {e}")
