from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Chat, Project


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


