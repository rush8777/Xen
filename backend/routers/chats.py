from __future__ import annotations

import json
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Chat, ChatMessage, Project
from ..services.rag_chat_service import RagChatService


router = APIRouter(prefix="/api", tags=["chats"])


# Pydantic schemas
class ChatCreate(BaseModel):
    name: str
    platform: Optional[str] = None


class ChatUpdate(BaseModel):
    name: Optional[str] = None
    platform: Optional[str] = None


class ChatResponse(BaseModel):
    id: int
    project_id: int
    name: str
    platform: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ChatMessageDTO(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    created_at: str


class ChatSendMessageRequest(BaseModel):
    chat_id: int | None = None
    message: str
    user_id: int | None = None


class ProjectRef(BaseModel):
    id: int
    name: str


class ChatSessionResponse(BaseModel):
    chat_id: int
    project: ProjectRef
    messages: list[ChatMessageDTO]
    rag_active: bool = False
    context_chunks_used: int = 0
    context_chunks: list[str] = []


_MENTION_RE = re.compile(r"@([^\n@]+)")


def _extract_project_name_from_message(message: str) -> str | None:
    """
    Extract first '@Project Name' mention.
    We allow spaces; capture stops at newline or another '@'.
    For multi-word names, we need to find the actual project name in the database.
    """
    if not message:
        return None

    match = _MENTION_RE.search(message)
    if not match:
        return None

    raw = (match.group(1) or "").strip()
    # Trim trailing punctuation (common when users type '@Project!' etc.)
    raw = raw.rstrip(" \t\r\n.,;:!?)]}\"'")
    
    # If there are multiple words, try to find the longest matching project name
    words = raw.split()
    if len(words) == 1:
        return raw or None
    
    # For multi-word potential names, we need to find the actual project name
    # by checking against existing projects in the database
    # This will be handled in _resolve_project_by_name with smart matching
    return raw or None


def _resolve_project_by_name(*, db: Session, project_name: str, user_id: int | None) -> Project:
    # Get all projects to check against
    q = db.query(Project)
    if user_id is not None:
        q = q.filter(Project.user_id == user_id)
    all_projects = q.all()
    
    # First try exact match
    for project in all_projects:
        if project.name.lower() == project_name.lower():
            return project
    
    # If no exact match, try to find the project name within the extracted text
    # This handles cases like "@Mock recording Summarize this project"
    # where "Mock recording" is the actual project name
    for project in all_projects:
        project_lower = project.name.lower()
        extracted_lower = project_name.lower()
        
        # Check if project name is at the start of extracted text
        if extracted_lower.startswith(project_lower):
            return project
        
        # Check if project name is contained within extracted text
        if project_lower in extracted_lower:
            # Make sure it's a word boundary match
            start_idx = extracted_lower.find(project_lower)
            # Check if it's at word boundaries
            before_ok = (start_idx == 0 or extracted_lower[start_idx-1].isspace())
            after_end = start_idx + len(project_lower)
            after_ok = (after_end >= len(extracted_lower) or extracted_lower[after_end].isspace() or 
                       extracted_lower[after_end] in '.,;:!?)]}\'"')
            
            if before_ok and after_ok:
                return project
    
    # Try progressively shorter versions of the extracted name
    words = project_name.split()
    for i in range(len(words), 0, -1):
        partial_name = " ".join(words[:i])
        for project in all_projects:
            if project.name.lower() == partial_name.lower():
                return project
    
    raise HTTPException(
        status_code=404,
        detail=f'Project not found for "@{project_name}". Available projects: {", ".join([f"{p.name}" for p in all_projects])}',
    )


@router.post("/projects/{project_id}/chats", response_model=ChatResponse, status_code=201)
def create_chat(
    project_id: int,
    chat: ChatCreate,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Create a chat for a project"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_chat = Chat(
        project_id=project_id,
        name=chat.name,
        platform=chat.platform,
    )
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)

    return ChatResponse(
        id=db_chat.id,
        project_id=db_chat.project_id,
        name=db_chat.name,
        platform=db_chat.platform,
        created_at=db_chat.created_at.isoformat(),
        updated_at=db_chat.updated_at.isoformat(),
    )


@router.get("/projects/{project_id}/chats", response_model=list[ChatResponse])
def list_project_chats(
    project_id: int,
    db: Session = Depends(get_db),
) -> list[ChatResponse]:
    """List chats for a project"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chats = db.query(Chat).filter(Chat.project_id == project_id).all()

    return [
        ChatResponse(
            id=chat.id,
            project_id=chat.project_id,
            name=chat.name,
            platform=chat.platform,
            created_at=chat.created_at.isoformat(),
            updated_at=chat.updated_at.isoformat(),
        )
        for chat in chats
    ]


@router.get("/chats/{chat_id}", response_model=ChatResponse)
def get_chat(chat_id: int, db: Session = Depends(get_db)) -> ChatResponse:
    """Get chat details"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return ChatResponse(
        id=chat.id,
        project_id=chat.project_id,
        name=chat.name,
        platform=chat.platform,
        created_at=chat.created_at.isoformat(),
        updated_at=chat.updated_at.isoformat(),
    )


@router.get("/chats/{chat_id}/messages", response_model=list[ChatMessageDTO])
def list_chat_messages(chat_id: int, db: Session = Depends(get_db)) -> list[ChatMessageDTO]:
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return [
        ChatMessageDTO(
            id=m.id,
            chat_id=m.chat_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat(),
        )
        for m in rows
    ]


@router.post("/chats/send-message", response_model=ChatSessionResponse)
async def send_message(payload: ChatSendMessageRequest, db: Session = Depends(get_db)) -> ChatSessionResponse:
    message = (payload.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    rag = RagChatService()

    # Load or create chat + resolve project
    chat: Chat | None = None
    project: Project | None = None

    if payload.chat_id is not None:
        chat = db.query(Chat).filter(Chat.id == payload.chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        project = db.query(Project).filter(Project.id == chat.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found for chat")
    else:
        project_name = _extract_project_name_from_message(message)
        if not project_name:
            raise HTTPException(
                status_code=400,
                detail='No project specified. Start your message with a project mention like "@My Project".',
            )
        project = _resolve_project_by_name(db=db, project_name=project_name, user_id=payload.user_id)
        chat = Chat(
            project_id=project.id,
            name=f"{project.name} Chat",
            platform=None,
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)

    # Persist user message
    user_row = ChatMessage(chat_id=chat.id, role="user", content=message)
    db.add(user_row)
    db.commit()
    db.refresh(user_row)

    # Build conversation history for model
    history_rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    history = [{"role": r.role, "content": r.content} for r in history_rows]

    # Generate assistant reply via RAG pipeline
    rag_active = False
    context_chunks_used = 0
    context_chunks: list[str] = []
    try:
        assistant_text, rag_active, context_chunks_used, context_chunks = await rag.generate_reply_async(
            project=project, messages=history, user_message=message, db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant generation failed: {str(e)}")

    assistant_row = ChatMessage(chat_id=chat.id, role="assistant", content=assistant_text)
    db.add(assistant_row)
    db.commit()
    db.refresh(assistant_row)

    # Return full message list (UI can render immediately)
    final_rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    messages = [
        ChatMessageDTO(
            id=m.id,
            chat_id=m.chat_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat(),
        )
        for m in final_rows
    ]

    return ChatSessionResponse(
        chat_id=chat.id,
        project=ProjectRef(id=project.id, name=project.name),
        messages=messages,
        rag_active=rag_active,
        context_chunks_used=context_chunks_used,
        context_chunks=context_chunks or [],
    )


@router.post("/chats/send-message-stream")
def send_message_stream(payload: ChatSendMessageRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    message = (payload.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    rag = RagChatService()

    # Load or create chat + resolve project
    chat: Chat | None = None
    project: Project | None = None

    if payload.chat_id is not None:
        chat = db.query(Chat).filter(Chat.id == payload.chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        project = db.query(Project).filter(Project.id == chat.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found for chat")
    else:
        project_name = _extract_project_name_from_message(message)
        if not project_name:
            raise HTTPException(
                status_code=400,
                detail='No project specified. Start your message with a project mention like "@My Project".',
            )
        project = _resolve_project_by_name(db=db, project_name=project_name, user_id=payload.user_id)
        chat = Chat(
            project_id=project.id,
            name=f"{project.name} Chat",
            platform=None,
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)

    # Persist user message first
    user_row = ChatMessage(chat_id=chat.id, role="user", content=message)
    db.add(user_row)
    db.commit()
    db.refresh(user_row)

    # Build conversation history for model
    history_rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    history = [{"role": r.role, "content": r.content} for r in history_rows]

    try:
        token_iter, rag_active, context_chunks_used, context_chunks = rag.stream_reply(
            project=project,
            messages=history,
            user_message=message,
            db=db,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant generation failed: {str(e)}")

    def _sse_event(event: str, payload_obj: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(payload_obj, ensure_ascii=False)}\n\n"

    def event_generator():
        assistant_parts: list[str] = []

        # Initial metadata event
        yield _sse_event(
            "meta",
            {
                "chat_id": chat.id,
                "project": {"id": project.id, "name": project.name},
                "rag_active": rag_active,
                "context_chunks_used": context_chunks_used,
                "context_chunks": context_chunks or [],
            },
        )

        try:
            for delta in token_iter:
                assistant_parts.append(delta)
                yield _sse_event("token", {"delta": delta})
        except Exception as e:
            db.rollback()
            yield _sse_event("error", {"error": f"Streaming generation failed: {str(e)}"})
            return

        assistant_text = "".join(assistant_parts).strip()
        if not assistant_text:
            assistant_text = "No response received."

        assistant_row = ChatMessage(chat_id=chat.id, role="assistant", content=assistant_text)
        db.add(assistant_row)
        db.commit()

        yield _sse_event(
            "done",
            {
                "chat_id": chat.id,
                "project": {"id": project.id, "name": project.name},
                "content": assistant_text,
                "rag_active": rag_active,
                "context_chunks_used": context_chunks_used,
                "context_chunks": context_chunks or [],
            },
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.patch("/chats/{chat_id}", response_model=ChatResponse)
def update_chat(
    chat_id: int,
    chat_update: ChatUpdate,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Update chat (rename, etc.)"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Update only provided fields
    update_data = chat_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chat, field, value)

    db.commit()
    db.refresh(chat)

    return ChatResponse(
        id=chat.id,
        project_id=chat.project_id,
        name=chat.name,
        platform=chat.platform,
        created_at=chat.created_at.isoformat(),
        updated_at=chat.updated_at.isoformat(),
    )


@router.delete("/chats/{chat_id}", status_code=200)
def delete_chat(chat_id: int, db: Session = Depends(get_db)) -> dict:
    """Delete chat"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    db.delete(chat)
    db.commit()

    return {"status": "ok"}
