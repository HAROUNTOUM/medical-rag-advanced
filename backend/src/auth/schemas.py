"""
Pydantic v2 schemas for request/response validation.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, field_validator


# ─── Auth ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Knowledge Base ──────────────────────────────────────────────────────────

class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProcessingTaskOut(BaseModel):
    id: int
    status: str  # pending / processing / completed / failed
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class DocumentOut(BaseModel):
    id: int
    file_name: str
    file_path: Optional[str]
    file_size: Optional[int]
    content_type: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    processing_tasks: List[ProcessingTaskOut] = []
    model_config = {"from_attributes": True}

class KnowledgeBaseOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    documents: List[DocumentOut] = []
    model_config = {"from_attributes": True}


# ─── Documents ───────────────────────────────────────────────────────────────

class UploadResult(BaseModel):
    upload_id: Optional[int] = None
    document_id: Optional[int] = None
    file_name: str
    status: str  # "pending" | "exists"
    message: Optional[str] = None
    skip_processing: bool = False
    temp_path: Optional[str] = None

class PreviewRequest(BaseModel):
    document_ids: List[int]
    chunk_size: int = 1000
    chunk_overlap: int = 200

class ProcessRequest(BaseModel):
    upload_id: int
    file_name: str
    status: str
    skip_processing: bool
    temp_path: Optional[str] = None

class TaskStatusOut(BaseModel):
    document_id: int
    status: str
    error_message: Optional[str] = None


# ─── Chat ─────────────────────────────────────────────────────────────────────

class ChatSessionCreate(BaseModel):
    title: str
    knowledge_base_ids: List[int] = []

class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    graph_data: Optional[Any] = None
    created_at: datetime
    model_config = {"from_attributes": True}

class ChatSessionOut(BaseModel):
    id: int
    title: str
    knowledge_base_id: Optional[int]
    knowledge_base_ids: List[int] = []
    created_at: datetime
    messages: List[ChatMessageOut] = []
    model_config = {"from_attributes": True}

class AskRequest(BaseModel):
    messages: Optional[List[Any]] = None   # Vercel AI SDK compat
    message: Optional[str] = None          # direct call compat

class AskResponse(BaseModel):
    id: str
    role: str = "assistant"
    content: str
    graph_data: Optional[Any] = None
    citations: List[Any] = []


# ─── API Keys ────────────────────────────────────────────────────────────────

class APIKeyCreate(BaseModel):
    name: str
    is_active: bool = True

class APIKeyUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class APIKeyOut(BaseModel):
    id: int
    name: str
    key: str          # shows prefix + masked portion
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
