"""
Knowledge Base and Document management router.
All operations are strictly scoped to the authenticated doctor.
"""
import os
import shutil
import threading
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.auth.database import get_db
from src.auth.models import User, KnowledgeBase, Document, ProcessingTask
from src.auth.schemas import (
    KnowledgeBaseCreate, KnowledgeBaseOut, DocumentOut,
    UploadResult, PreviewRequest, ProcessRequest, TaskStatusOut,
)
from src.auth.security import get_current_user
from src.chunking.chunker import extract_and_chunk

router = APIRouter(prefix="/api/v1", tags=["Knowledge Base"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─── Knowledge Base CRUD ─────────────────────────────────────────────────────

@router.post("/knowledge-base", response_model=KnowledgeBaseOut, status_code=201)
async def create_knowledge_base(
    body: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    kb = KnowledgeBase(
        doctor_id=current_user.id,
        name=body.name,
        description=body.description,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    # Load relationships
    result = await db.execute(
        select(KnowledgeBase)
        .options(selectinload(KnowledgeBase.documents).selectinload(Document.processing_tasks))
        .where(KnowledgeBase.id == kb.id)
    )
    return result.scalar_one()


@router.get("/knowledge-base", response_model=List[KnowledgeBaseOut])
async def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KnowledgeBase)
        .options(selectinload(KnowledgeBase.documents).selectinload(Document.processing_tasks))
        .where(KnowledgeBase.doctor_id == current_user.id)
        .order_by(KnowledgeBase.created_at.desc())
    )
    return result.scalars().all()


@router.get("/knowledge-base/{kb_id}", response_model=KnowledgeBaseOut)
async def get_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KnowledgeBase)
        .options(selectinload(KnowledgeBase.documents).selectinload(Document.processing_tasks))
        .where(KnowledgeBase.id == kb_id, KnowledgeBase.doctor_id == current_user.id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")
    return kb


@router.delete("/knowledge-base/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id, KnowledgeBase.doctor_id == current_user.id
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")
    await db.delete(kb)
    await db.commit()


# ─── Document Upload ──────────────────────────────────────────────────────────

@router.post("/knowledge-base/{kb_id}/documents/upload", response_model=List[UploadResult])
async def upload_documents(
    kb_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload files and create Document records (does not process yet)."""
    # Verify KB ownership
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id, KnowledgeBase.doctor_id == current_user.id
        )
    )
    kb = kb_result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")

    results: List[UploadResult] = []
    doctor_upload_dir = os.path.join(UPLOAD_DIR, str(current_user.id), str(kb_id))
    os.makedirs(doctor_upload_dir, exist_ok=True)

    for file in files:
        # Check if already exists
        existing_result = await db.execute(
            select(Document).where(
                Document.knowledge_base_id == kb_id,
                Document.file_name == file.filename,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            results.append(UploadResult(
                document_id=existing.id,
                file_name=file.filename or "unknown",
                status="exists",
                message="Document already exists in this knowledge base.",
                skip_processing=True,
            ))
            continue

        # Save file to disk
        file_path = os.path.join(doctor_upload_dir, file.filename or f"file_{uuid.uuid4()}")
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        doc = Document(
            knowledge_base_id=kb_id,
            file_name=file.filename or "unknown",
            file_path=file_path,
            file_size=len(content),
            content_type=file.content_type or "application/octet-stream",
            status="uploaded",
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        results.append(UploadResult(
            upload_id=doc.id,
            file_name=file.filename or "unknown",
            status="pending",
            skip_processing=False,
            temp_path=file_path,
        ))

    return results


# ─── Document Preview ─────────────────────────────────────────────────────────

@router.post("/knowledge-base/{kb_id}/documents/preview")
async def preview_chunks(
    kb_id: int,
    body: PreviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview how a document will be chunked before processing."""
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id, KnowledgeBase.doctor_id == current_user.id
        )
    )
    if not kb_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Knowledge base not found.")

    preview_data = {}
    for doc_id in body.document_ids:
        doc_result = await db.execute(
            select(Document).where(Document.id == doc_id, Document.knowledge_base_id == kb_id)
        )
        doc = doc_result.scalar_one_or_none()
        if not doc or not doc.file_path or not os.path.exists(doc.file_path):
            continue
        try:
            chunks = extract_and_chunk(doc.file_path)
            preview_data[doc_id] = {
                "chunks": [
                    {"content": c.get("text", c) if isinstance(c, dict) else str(c), "metadata": {}}
                    for c in chunks[:10]  # max 10 for preview
                ],
                "total_chunks": len(chunks),
            }
        except Exception as e:
            preview_data[doc_id] = {"chunks": [], "total_chunks": 0, "error": str(e)}

    return preview_data


# ─── Document Processing ──────────────────────────────────────────────────────

# In-memory task status store (survives the request lifecycle)
_task_store: dict[int, dict] = {}
_task_store_lock = threading.Lock()


def _run_ingestion_in_background(
    task_id: int,
    doc_id: int,
    file_path: str,
    doctor_id: str,
    db_url: str,
):
    """Background thread that runs the full ingestion pipeline for one document."""
    import asyncio
    from src.auth.database import AsyncSessionLocal
    from src.auth.models import Document, ProcessingTask
    from src.vectordb.vector_store import ingest_to_weaviate
    from src.chunking.chunker import extract_and_chunk

    async def _async_run():
        async with AsyncSessionLocal() as session:
            # Mark as processing
            task_res = await session.execute(
                select(ProcessingTask).where(ProcessingTask.id == task_id)
            )
            task = task_res.scalar_one_or_none()
            if task:
                task.status = "processing"
                await session.commit()

            with _task_store_lock:
                _task_store[task_id] = {"document_id": doc_id, "status": "processing"}

            try:
                chunks = extract_and_chunk(file_path)
                ingest_to_weaviate(chunks, doctor_id=doctor_id)

                # Update DB
                if task:
                    task.status = "completed"
                    await session.commit()

                # Update document status
                doc_res = await session.execute(select(Document).where(Document.id == doc_id))
                doc = doc_res.scalar_one_or_none()
                if doc:
                    doc.status = "completed"
                    await session.commit()

                with _task_store_lock:
                    _task_store[task_id] = {"document_id": doc_id, "status": "completed"}

            except Exception as e:
                if task:
                    task.status = "failed"
                    task.error_message = str(e)
                    await session.commit()
                with _task_store_lock:
                    _task_store[task_id] = {
                        "document_id": doc_id,
                        "status": "failed",
                        "error_message": str(e),
                    }

    asyncio.run(_async_run())


@router.post("/knowledge-base/{kb_id}/documents/process")
async def process_documents(
    kb_id: int,
    items: List[ProcessRequest],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start background ingestion of uploaded documents into Weaviate."""
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id, KnowledgeBase.doctor_id == current_user.id
        )
    )
    if not kb_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Knowledge base not found.")

    from src.auth.database import DATABASE_URL

    task_list = []
    for item in items:
        if item.skip_processing:
            continue

        doc_result = await db.execute(
            select(Document).where(Document.id == item.upload_id, Document.knowledge_base_id == kb_id)
        )
        doc = doc_result.scalar_one_or_none()
        if not doc:
            continue

        task = ProcessingTask(document_id=doc.id, status="pending")
        db.add(task)
        await db.commit()
        await db.refresh(task)

        file_path = doc.file_path or item.temp_path or ""

        t = threading.Thread(
            target=_run_ingestion_in_background,
            args=(task.id, doc.id, file_path, str(current_user.id), DATABASE_URL),
            daemon=True,
        )
        t.start()

        with _task_store_lock:
            _task_store[task.id] = {"document_id": doc.id, "status": "pending"}

        task_list.append({"upload_id": item.upload_id, "task_id": task.id})

    return {"tasks": task_list}


@router.get("/knowledge-base/{kb_id}/documents/tasks")
async def get_task_status(
    kb_id: int,
    task_ids: str = "",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Poll background task statuses."""
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id, KnowledgeBase.doctor_id == current_user.id
        )
    )
    if not kb_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Knowledge base not found.")

    ids = [int(i) for i in task_ids.split(",") if i.strip().isdigit()]
    status_map = {}
    for tid in ids:
        with _task_store_lock:
            entry = _task_store.get(tid)
        if entry:
            status_map[str(tid)] = entry
        else:
            # Fall back to DB
            task_result = await db.execute(
                select(ProcessingTask).where(ProcessingTask.id == tid)
            )
            task = task_result.scalar_one_or_none()
            if task:
                status_map[str(tid)] = {
                    "document_id": task.document_id,
                    "status": task.status,
                    "error_message": task.error_message,
                }
    return status_map


@router.get("/documents", response_model=List[DocumentOut])
async def list_all_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents belonging to the current doctor."""
    result = await db.execute(
        select(Document)
        .join(KnowledgeBase)
        .options(selectinload(Document.processing_tasks))
        .where(KnowledgeBase.doctor_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    return result.scalars().all()
