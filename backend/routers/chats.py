from __future__ import annotations

import asyncio
import base64
import json
import re
from datetime import datetime
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


class RecentChatDTO(BaseModel):
    id: int
    project_id: int
    project_name: str
    project_category: str | None = None
    name: str
    platform: str | None = None
    updated_at: str
    last_message_at: str | None = None


class ChatSendMessageRequest(BaseModel):
    chat_id: int | None = None
    project_id: int | None = None
    message: str
    user_id: int | None = None
    course_clarification_answers: dict[str, str] | None = None
    course_mode_enabled: bool = False


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
    course_generated: bool = False
    course_summary: str | None = None
    course_data: dict | None = None
    course_template: str | None = None
    course_clarification_needed: bool = False
    course_clarification_questions: list[dict] = []


_MENTION_RE = re.compile(r"@([^\n@]+)")
_COURSE_PAYLOAD_PREFIX = "[[COURSE_PAYLOAD_V1:"
_COURSE_PAYLOAD_SUFFIX = "]]"
_COURSE_TRIGGER_TERMS = (
    "course",
    "curriculum",
    "lesson",
    "lessons",
    "training plan",
    "learning path",
    "study plan",
    "slide deck",
    "slides",
    "module",
    "modules",
    "teach me",
    "tutorial",
    "coaching plan",
)
_SMALLTALK_RE = re.compile(
    r"^\s*(hi|hello|hey|yo|sup|hola|good morning|good afternoon|good evening|thanks|thank you)\b[!.? ]*$",
    re.IGNORECASE,
)


def _contains_course_trigger(user_message: str) -> bool:
    text = (user_message or "").strip().lower()
    if not text:
        return False
    return any(term in text for term in _COURSE_TRIGGER_TERMS)


def _should_generate_course(
    *,
    user_message: str,
    intent: dict,
    provided_clarification_answers: dict[str, str],
    course_mode_enabled: bool,
) -> bool:
    """
    Gate course generation to explicit learning/course requests.
    This prevents normal chat (greetings, quick questions) from
    being routed into the course pipeline.
    """
    # Hard gate: if the user did not enable course mode, always use text chat.
    if not course_mode_enabled:
        return False

    if provided_clarification_answers:
        return True

    text = (user_message or "").strip()
    if not text:
        return False

    if _SMALLTALK_RE.match(text):
        return False

    is_course_request = bool(intent.get("is_course_request"))
    try:
        confidence = float(intent.get("confidence", 0.0))
    except Exception:
        confidence = 0.0

    has_explicit_trigger = _contains_course_trigger(text)

    # Strong explicit request: allow with moderate confidence.
    if has_explicit_trigger and is_course_request and confidence >= 0.45:
        return True

    # Very high confidence model decision can trigger even without keywords.
    if is_course_request and confidence >= 0.85:
        return True

    return False


def _build_stored_assistant_content(
    *,
    summary: str,
    course_data: dict | None,
    course_template: str | None,
) -> str:
    if not course_data:
        return summary
    payload = {
        "course_data": course_data,
        "course_template": course_template or "default",
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    return f"{summary}\n\n{_COURSE_PAYLOAD_PREFIX}{encoded}{_COURSE_PAYLOAD_SUFFIX}"


def _extract_project_name_from_message(message: str) -> str | None:
    """
    Extract first '@Project Name' mention.
    We allow spaces; capture stops at newline or another '@'.
    For multi-word names, we need to find the actual project name in the database.
    """
    if not message:
        return None

    matches = list(_MENTION_RE.finditer(message))
    if not matches:
        return None
    # Use the latest mention in the message so users can override an earlier one.
    match = matches[-1]

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


def _resolve_default_project_for_new_chat(*, db: Session, user_id: int | None) -> Project | None:
    query = db.query(Project)
    if user_id is not None:
        query = query.filter(Project.user_id == user_id)
    return query.order_by(Project.updated_at.desc(), Project.created_at.desc()).first()


def _resolve_project_for_message(
    *,
    db: Session,
    chat: Chat | None,
    project_id: int | None,
    message: str,
    user_id: int | None,
) -> Project:
    """
    Resolve target project for the current message.
    Priority:
      1) Explicit project_id in request payload.
      2) Latest @mention in message.
      3) Existing chat.project_id (if chat provided).
      4) Most recently updated project.
    """
    if project_id is not None:
        project_query = db.query(Project).filter(Project.id == project_id)
        if user_id is not None:
            project_query = project_query.filter(Project.user_id == user_id)
        project = project_query.first()
        if project:
            return project
        raise HTTPException(status_code=404, detail="Project not found")

    project_name = _extract_project_name_from_message(message)
    if project_name:
        return _resolve_project_by_name(
            db=db,
            project_name=project_name,
            user_id=user_id,
        )

    if chat is not None:
        project = db.query(Project).filter(Project.id == chat.project_id).first()
        if project:
            return project
        raise HTTPException(status_code=404, detail="Project not found for chat")

    project = _resolve_default_project_for_new_chat(db=db, user_id=user_id)
    if project:
        return project
    raise HTTPException(
        status_code=400,
        detail='No project specified and no recent project found. Start your message with a project mention like "@My Project".',
    )


def _is_default_chat_name(chat_name: str, project_name: str) -> bool:
    name = (chat_name or "").strip().lower()
    project = (project_name or "").strip().lower()
    return name in {
        "",
        "new chat",
        "untitled chat",
        f"{project} chat",
    }


async def _maybe_update_chat_heading_async(
    *,
    rag: RagChatService,
    db: Session,
    chat: Chat,
    project: Project,
) -> None:
    if not _is_default_chat_name(chat.name, project.name):
        return
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    history = [{"role": r.role, "content": r.content} for r in rows]
    heading = await rag.generate_chat_heading_async(project=project, messages=history)
    heading = (heading or "").strip()
    if not heading:
        return
    if heading == chat.name:
        return
    chat.name = heading[:120]
    chat.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(chat)


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


@router.get("/recent-chats", response_model=list[RecentChatDTO])
def list_recent_chats(
    limit: int = 10,
    user_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[RecentChatDTO]:
    safe_limit = max(1, min(50, int(limit)))
    query = db.query(Chat, Project).join(Project, Project.id == Chat.project_id)
    if user_id is not None:
        query = query.filter(Project.user_id == user_id)
    rows = query.order_by(Chat.updated_at.desc()).limit(safe_limit).all()

    out: list[RecentChatDTO] = []
    for chat, project in rows:
        last_message = (
            db.query(ChatMessage)
            .filter(ChatMessage.chat_id == chat.id)
            .order_by(ChatMessage.created_at.desc())
            .first()
        )
        out.append(
            RecentChatDTO(
                id=chat.id,
                project_id=project.id,
                project_name=project.name,
                project_category=project.category,
                name=chat.name,
                platform=chat.platform,
                updated_at=chat.updated_at.isoformat(),
                last_message_at=last_message.created_at.isoformat() if last_message else None,
            )
        )
    return out


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
        project = _resolve_project_for_message(
            db=db,
            chat=chat,
            project_id=payload.project_id,
            message=message,
            user_id=payload.user_id,
        )
        if chat.project_id != project.id:
            chat.project_id = project.id
            db.commit()
            db.refresh(chat)
    else:
        project = _resolve_project_for_message(
            db=db,
            chat=None,
            project_id=payload.project_id,
            message=message,
            user_id=payload.user_id,
        )
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
    chat.updated_at = datetime.utcnow()
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

    # Generate assistant reply via RAG pipeline or course pipeline
    rag_active = False
    context_chunks_used = 0
    context_chunks: list[str] = []
    course_generated = False
    course_summary: str | None = None
    course_data: dict | None = None
    course_template: str | None = None
    course_clarification_needed = False
    course_clarification_questions: list[dict] = []
    try:
        provided_clarification_answers = payload.course_clarification_answers or {}
        course_template = str(provided_clarification_answers.get("course_template") or "default")
        intent = await rag.detect_course_intent_async(
            project=project,
            messages=history,
            user_message=message,
        )
        should_generate_course = _should_generate_course(
            user_message=message,
            intent=intent,
            provided_clarification_answers=provided_clarification_answers,
            course_mode_enabled=bool(payload.course_mode_enabled),
        )

        if should_generate_course:
            try:
                if not provided_clarification_answers:
                    clarification_plan = await rag.plan_course_clarification_async(
                        project=project,
                        messages=history,
                        user_message=message,
                        goal=str(intent.get("goal") or "").strip(),
                    )
                    if clarification_plan.get("needs_clarification"):
                        course_clarification_needed = True
                        course_clarification_questions = list(
                            clarification_plan.get("questions") or []
                        )
                        assistant_text = str(
                            clarification_plan.get("assistant_message")
                            or "Before generating the course, I need a few details."
                        )
                        rag_active = False
                        context_chunks_used = 0
                        context_chunks = []
                    else:
                        (
                            assistant_text,
                            course_data,
                            rag_active,
                            context_chunks_used,
                            context_chunks,
                        ) = await rag.generate_course_async(
                            project=project,
                            messages=history,
                            user_message=message,
                            goal=str(intent.get("goal") or "").strip(),
                            course_requirements=provided_clarification_answers,
                            db=db,
                        )
                        course_generated = True
                        course_summary = assistant_text
                else:
                    (
                        assistant_text,
                        course_data,
                        rag_active,
                        context_chunks_used,
                        context_chunks,
                    ) = await rag.generate_course_async(
                        project=project,
                        messages=history,
                        user_message=message,
                        goal=str(intent.get("goal") or "").strip(),
                        course_requirements=provided_clarification_answers,
                        db=db,
                    )
                    course_generated = True
                    course_summary = assistant_text
            except Exception:
                assistant_text, rag_active, context_chunks_used, context_chunks = await rag.generate_reply_async(
                    project=project, messages=history, user_message=message, db=db
                )
        else:
            assistant_text, rag_active, context_chunks_used, context_chunks = await rag.generate_reply_async(
                project=project, messages=history, user_message=message, db=db
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant generation failed: {str(e)}")

    stored_assistant_content = _build_stored_assistant_content(
        summary=assistant_text,
        course_data=course_data if course_generated else None,
        course_template=course_template,
    )
    assistant_row = ChatMessage(chat_id=chat.id, role="assistant", content=stored_assistant_content)
    db.add(assistant_row)
    chat.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assistant_row)
    try:
        await _maybe_update_chat_heading_async(
            rag=rag,
            db=db,
            chat=chat,
            project=project,
        )
    except Exception:
        pass

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
        course_generated=course_generated,
        course_summary=course_summary,
        course_data=course_data,
        course_template=course_template,
        course_clarification_needed=course_clarification_needed,
        course_clarification_questions=course_clarification_questions,
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
        project = _resolve_project_for_message(
            db=db,
            chat=chat,
            project_id=payload.project_id,
            message=message,
            user_id=payload.user_id,
        )
        if chat.project_id != project.id:
            chat.project_id = project.id
            db.commit()
            db.refresh(chat)
    else:
        project = _resolve_project_for_message(
            db=db,
            chat=None,
            project_id=payload.project_id,
            message=message,
            user_id=payload.user_id,
        )
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
    chat.updated_at = datetime.utcnow()
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

    token_iter = None
    rag_active = False
    context_chunks_used = 0
    context_chunks: list[str] = []
    course_generated = False
    course_summary: str | None = None
    course_data: dict | None = None
    course_template: str | None = None
    course_clarification_needed = False
    course_clarification_questions: list[dict] = []

    try:
        provided_clarification_answers = payload.course_clarification_answers or {}
        course_template = str(provided_clarification_answers.get("course_template") or "default")
        loop = asyncio.new_event_loop()
        try:
            intent = loop.run_until_complete(
                rag.detect_course_intent_async(
                    project=project,
                    messages=history,
                    user_message=message,
                )
            )
            should_generate_course = _should_generate_course(
                user_message=message,
                intent=intent,
                provided_clarification_answers=provided_clarification_answers,
                course_mode_enabled=bool(payload.course_mode_enabled),
            )

            if should_generate_course:
                try:
                    if not provided_clarification_answers:
                        clarification_plan = loop.run_until_complete(
                            rag.plan_course_clarification_async(
                                project=project,
                                messages=history,
                                user_message=message,
                                goal=str(intent.get("goal") or "").strip(),
                            )
                        )
                        if clarification_plan.get("needs_clarification"):
                            course_clarification_needed = True
                            course_clarification_questions = list(
                                clarification_plan.get("questions") or []
                            )
                            course_summary = str(
                                clarification_plan.get("assistant_message")
                                or "Before generating the course, I need a few details."
                            )
                        else:
                            (
                                course_summary,
                                course_data,
                                rag_active,
                                context_chunks_used,
                                context_chunks,
                            ) = loop.run_until_complete(
                                rag.generate_course_async(
                                    project=project,
                                    messages=history,
                                    user_message=message,
                                    goal=str(intent.get("goal") or "").strip(),
                                    course_requirements=provided_clarification_answers,
                                    db=db,
                                )
                            )
                            course_generated = True
                    else:
                        (
                            course_summary,
                            course_data,
                            rag_active,
                            context_chunks_used,
                            context_chunks,
                        ) = loop.run_until_complete(
                            rag.generate_course_async(
                                project=project,
                                messages=history,
                                user_message=message,
                                goal=str(intent.get("goal") or "").strip(),
                                course_requirements=provided_clarification_answers,
                                db=db,
                            )
                        )
                        course_generated = True
                except Exception:
                    token_iter, rag_active, context_chunks_used, context_chunks = rag.stream_reply(
                        project=project,
                        messages=history,
                        user_message=message,
                        db=db,
                    )
            else:
                token_iter, rag_active, context_chunks_used, context_chunks = rag.stream_reply(
                    project=project,
                    messages=history,
                    user_message=message,
                    db=db,
                )
        finally:
            loop.close()
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
                "course_generation_planned": course_generated,
                "course_clarification_needed": course_clarification_needed,
                "course_clarification_questions": course_clarification_questions,
                "course_template": course_template,
            },
        )

        if course_generated or course_clarification_needed:
            assistant_text = (course_summary or "").strip()
        else:
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

        if not assistant_text:
            assistant_text = "No response received."

        stored_assistant_content = _build_stored_assistant_content(
            summary=assistant_text,
            course_data=course_data if course_generated else None,
            course_template=course_template,
        )
        assistant_row = ChatMessage(chat_id=chat.id, role="assistant", content=stored_assistant_content)
        db.add(assistant_row)
        chat.updated_at = datetime.utcnow()
        db.commit()
        try:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(
                    _maybe_update_chat_heading_async(
                        rag=rag,
                        db=db,
                        chat=chat,
                        project=project,
                    )
                )
            finally:
                loop.close()
        except Exception:
            pass

        yield _sse_event(
            "done",
            {
                "chat_id": chat.id,
                "project": {"id": project.id, "name": project.name},
                "content": assistant_text,
                "rag_active": rag_active,
                "context_chunks_used": context_chunks_used,
                "context_chunks": context_chunks or [],
                "course_generated": course_generated,
                "course_summary": course_summary,
                "course_data": course_data,
                "course_template": course_template,
                "course_clarification_needed": course_clarification_needed,
                "course_clarification_questions": course_clarification_questions,
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
