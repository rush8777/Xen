from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from google.genai import types
from sqlalchemy.orm import Session

from ..gemini_backend.gemini_client import client
from ..models import Project
from ..services.vector_retrieval_service import (
    CONTENT_SPECIFIC_THRESHOLD,
    DEFAULT_SIMILARITY_THRESHOLD,
    VectorRetrievalService,
)

logger = logging.getLogger(__name__)

# Maximum number of context chunks to inject into the prompt
MAX_CONTEXT_CHUNKS = 5

# Rough character budget for injected context (keeps us well within token limits)
MAX_CONTEXT_CHARS = 6000


class RagChatService:
    """
    RAG-enabled chat service.

    Retrieval flow:
      1. Generate a Gemini text embedding for the user query.
      2. Run cosine similarity search across VideoSubInterval +
         SubVideoIntervalEmbedding tables for the project's video.
      3. Rank and format the top-N matching intervals as context.
      4. Inject context into Gemini system prompt and generate reply.

    Falls back gracefully when:
      - Vector data has not been generated for the project yet.
      - Embedding API call fails.
      - No intervals are stored for the video.
    """

    model: str = "models/gemini-2.5-flash"

    def __init__(self) -> None:
        self._retrieval = VectorRetrievalService()

    # ------------------------------------------------------------------
    # Retrieval (now async, with sync fallback for backward compat)
    # ------------------------------------------------------------------

    async def retrieve_project_context_async(
        self,
        *,
        project_id: int,
        query: str,
        db: Session,
    ) -> tuple[list[str], bool]:
        """
        Retrieve relevant video interval context for `query`.

        Returns:
            (context_chunks, rag_active)
            - context_chunks: list of formatted context strings
            - rag_active: True if real vector data was found
        """
        try:
            # 1. Generate query embedding
            query_embedding = await self._retrieval.generate_query_embedding(query)

            # 2. Search vector DB
            content_filter = self._retrieval.detect_content_type(query)
            similarity_threshold = (
                CONTENT_SPECIFIC_THRESHOLD
                if content_filter
                else DEFAULT_SIMILARITY_THRESHOLD
            )
            intervals = self._retrieval.search_similar_intervals(
                db=db,
                project_id=project_id,
                query_embedding=query_embedding,
                query_text=query,
                limit=MAX_CONTEXT_CHUNKS,
                similarity_threshold=similarity_threshold,
                content_filter=content_filter,
            )

            if not intervals:
                return [], False

            # 3. Format context chunks
            chunks = self._retrieval.format_retrieved_context(
                intervals,
                content_filter=content_filter,
            )

            # 4. Enforce character budget
            truncated: list[str] = []
            total = 0
            for chunk in chunks:
                remaining = MAX_CONTEXT_CHARS - total
                if remaining <= 0:
                    break

                # If a single chunk is too large, include a truncated version rather
                # than dropping all context (which would disable RAG entirely).
                if len(chunk) > remaining:
                    if not truncated:
                        truncated.append(chunk[:remaining])
                        total += remaining
                    break

                truncated.append(chunk)
                total += len(chunk)

            return truncated, bool(truncated)

        except Exception as exc:
            logger.warning(
                "[RAG] Context retrieval failed for project %s: %s", project_id, exc
            )
            return [], False

    def retrieve_project_context(self, *, project_id: int, query: str) -> list[str]:
        """
        Synchronous compatibility shim (used when no DB session is available).
        Returns empty list — use retrieve_project_context_async for real RAG.
        """
        return []

    # ------------------------------------------------------------------
    # Reply generation
    # ------------------------------------------------------------------

    async def generate_reply_async(
        self,
        *,
        project: Project,
        messages: list[dict[str, Any]],
        user_message: str,
        db: Session,
    ) -> tuple[str, bool, int, list[str]]:
        """
        Generate an assistant reply with RAG context injection.

        Returns:
            (reply_text, rag_was_active, context_chunks_used, context_chunks)
        """
        context_chunks, rag_active = await self.retrieve_project_context_async(
            project_id=project.id,
            query=user_message,
            db=db,
        )

        system_preamble = self._build_system_prompt(
            project=project,
            context_chunks=context_chunks,
            rag_active=rag_active,
        )

        contents = self._build_contents(messages=messages, user_message=user_message)

        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_preamble,
                    temperature=0.7,
                    response_mime_type="text/plain",
                ),
            ),
        )

        text = (resp.text or "").strip()
        if not text:
            raise ValueError("Empty response from Gemini")

        return text, rag_active, len(context_chunks), context_chunks

    def generate_reply(
        self,
        *,
        project: Project,
        messages: list[dict[str, Any]],
        user_message: str,
        db: Optional[Session] = None,
    ) -> str:
        """
        Synchronous reply generation.

        When `db` is provided, runs the full async RAG pipeline via
        asyncio.run (safe in a new thread/executor context).
        When `db` is None, falls back to context-free generation.
        """
        if db is not None:
            try:
                loop = asyncio.new_event_loop()
                try:
                    text, _, _, _ = loop.run_until_complete(
                        self.generate_reply_async(
                            project=project,
                            messages=messages,
                            user_message=user_message,
                            db=db,
                        )
                    )
                finally:
                    loop.close()
                return text
            except Exception as exc:
                logger.warning(
                    "[RAG] Async pipeline failed, falling back to no-context: %s", exc
                )

        # Fallback: no-context generation (original behaviour)
        return self._generate_reply_no_context(
            project=project, messages=messages, user_message=user_message
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_system_prompt(
        self,
        *,
        project: Project,
        context_chunks: list[str],
        rag_active: bool,
    ) -> str:
        lines = [
            "You are an assistant that helps the user analyse and understand their video project.",
            f"Project name: {project.name}",
            f"Project id: {project.id}",
            "",
            "If the user asks something unrelated to the project, answer normally.",
            "If you don't know something, say so.",
            "",
        ]

        if rag_active and context_chunks:
            lines.append(
                "The following are the most relevant segments retrieved from the "
                "video's visual analysis database, ordered by relevance to the user's "
                "question. Use this context to give accurate, time-specific answers."
            )
            lines.append("")
            for i, chunk in enumerate(context_chunks, 1):
                lines.append(f"--- Context {i} ---")
                lines.append(chunk)
            lines.append("--- End of retrieved context ---")
            lines.append("")
            lines.append(
                "When referencing video content, cite the timestamp range shown above "
                "(e.g. 'At 01:20–01:40, ...')."
            )
        else:
            lines.append(
                "Relevant video context: No vector data is available for this project yet. "
                "Answer based on general knowledge and the project name."
            )

        return "\n".join(lines)

    def _build_contents(
        self,
        *,
        messages: list[dict[str, Any]],
        user_message: str,
    ) -> list[types.Content]:
        contents: list[types.Content] = []
        for m in messages:
            role = (m.get("role") or "").strip().lower()
            content = (m.get("content") or "").strip()
            if not content:
                continue
            gemini_role = "model" if role == "assistant" else "user"
            contents.append(
                types.Content(role=gemini_role, parts=[types.Part(text=content)])
            )

        # Ensure latest user message is present
        if (
            not contents
            or contents[-1].role != "user"
            or contents[-1].parts[0].text != user_message
        ):
            contents.append(
                types.Content(role="user", parts=[types.Part(text=user_message)])
            )

        return contents

    def _generate_reply_no_context(
        self,
        *,
        project: Project,
        messages: list[dict[str, Any]],
        user_message: str,
    ) -> str:
        """Original context-free generation path (fallback)."""
        system_preamble = (
            "You are an assistant that helps the user with their project.\n"
            f"Project name: {project.name}\n"
            f"Project id: {project.id}\n"
            "If the user asks something unrelated to the project, answer normally.\n"
            "If you don't know something, say so.\n"
            "\nRelevant project context: (none provided yet)\n"
        )

        contents = self._build_contents(messages=messages, user_message=user_message)

        resp = client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_preamble,
                temperature=0.7,
                response_mime_type="text/plain",
            ),
        )

        text = (resp.text or "").strip()
        if not text:
            raise ValueError("Empty response from Gemini")
        return text

