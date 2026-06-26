
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.auth.database import get_db
from src.auth.models import User, ChatSession, ChatMessage, KnowledgeBase
from src.auth.schemas import (
    ChatSessionCreate, ChatSessionOut, ChatMessageOut, AskRequest, AskResponse,
)
from src.auth.security import get_current_user

router = APIRouter(prefix="/api/v1", tags=["Chat"])


def _build_session_out(session: ChatSession) -> dict:
    """Convert a ChatSession ORM object to the response format the frontend expects."""
    kb_ids = [session.knowledge_base_id] if session.knowledge_base_id else []
    return {
        "id": session.id,
        "title": session.title,
        "knowledge_base_id": session.knowledge_base_id,
        "knowledge_base_ids": kb_ids,
        "created_at": session.created_at,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "graph_data": m.graph_data,
                "created_at": m.created_at,
            }
            for m in (session.messages or [])
        ],
    }


# session

@router.post("/chat", status_code=201)
async def create_chat_session(
    body: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    kb_id = body.knowledge_base_ids[0] if body.knowledge_base_ids else None
    if kb_id:
        kb_res = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.doctor_id == current_user.id,
            )
        )
        if not kb_res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Knowledge base not found.")

    session = ChatSession(
        doctor_id=current_user.id,
        knowledge_base_id=kb_id,
        title=body.title or "New Chat",
    )
    db.add(session)
    await db.commit()
    
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session.id)
    )
    session = result.scalar_one()
    return _build_session_out(session)


@router.get("/chat", response_model=List[dict])
async def list_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.doctor_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return [_build_session_out(s) for s in sessions]


@router.get("/chat/sessions", response_model=List[dict])
async def list_chat_sessions_alias(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    
    return await list_chat_sessions(current_user=current_user, db=db)


@router.get("/chat/{session_id}")
async def get_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id, ChatSession.doctor_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return _build_session_out(session)


@router.delete("/chat/{session_id}", status_code=204)
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.doctor_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    await db.delete(session)
    await db.commit()


# message

@router.post("/chat/{session_id}/messages")
async def send_message(
    session_id: int,
    body: AskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message and get an AI response.
    """
    # 1. Load session and verify ownership
    session_result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id, ChatSession.doctor_id == current_user.id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    # 2. Extract the user's query from Vercel AI SDK format or direct format
    user_query = ""
    if body.message:
        user_query = body.message
    elif body.messages:
        
        for m in reversed(body.messages):
            if isinstance(m, dict) and m.get("role") == "user":
                user_query = m.get("content", "")
                break

    if not user_query.strip():
        raise HTTPException(status_code=422, detail="Message content is empty.")

    # 3. Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=user_query,
    )
    db.add(user_msg)
    await db.commit()

    # 4. Run the isolated RAG pipeline
    try:
        from main import run_agentic_workflow_isolated
        answer, graph_data, citations = run_agentic_workflow_isolated(
            query=user_query,
            doctor_id=str(current_user.id),
        )
    except Exception as e:
        answer = f"I encountered an error while processing your query: {str(e)}"
        graph_data = None
        citations = []

    # 5. Save assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=answer,
        graph_data=graph_data,
    )
    db.add(assistant_msg)

    # 6. Update session title from first user message if still default
    if session.title == "New Chat" and len(session.messages) == 0:
        session.title = user_query[:80]

    await db.commit()
    await db.refresh(assistant_msg)

    return {
        "id": str(assistant_msg.id),
        "role": "assistant",
        "content": answer,
        "graph_data": graph_data,
        "citations": citations,
    }
