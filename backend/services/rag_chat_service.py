from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

from google.genai import types
from sqlalchemy.orm import Session

from ..gemini_backend.gemini_client import client
from ..models import Project
from ..services.vector_retrieval_service import (
    CONTENT_KEYWORDS,
    CONTENT_SPECIFIC_THRESHOLD,
    DEFAULT_SIMILARITY_THRESHOLD,
    RetrievedInterval,
    VectorRetrievalService,
)

logger = logging.getLogger(__name__)

# Maximum number of context chunks to inject into the prompt
MAX_CONTEXT_CHUNKS = 10

# Rough character budget for injected context (keeps us well within token limits)
MAX_CONTEXT_CHARS = 100000


@dataclass
class QueryTransformPlan:
    strategy: str = "original"  # original | rewrite | multi_query | hyde | multi_hyde
    rewritten_query: str = ""
    search_queries: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    hyde_passage: str = ""
    content_focus: str = ""


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
        messages: Optional[list[dict[str, Any]]] = None,
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
            transform_plan = await self._plan_query_transformation_async(
                query=query,
                messages=messages or [],
            )

            retrieval_queries = self._build_retrieval_queries(
                original_query=query,
                plan=transform_plan,
            )
            content_filter = self._infer_content_filter(
                primary_query=transform_plan.rewritten_query or query,
                keywords=transform_plan.keywords,
                content_focus=transform_plan.content_focus,
            )
            similarity_threshold = (
                CONTENT_SPECIFIC_THRESHOLD
                if content_filter
                else DEFAULT_SIMILARITY_THRESHOLD
            )

            merged_by_window: dict[tuple[int, int], RetrievedInterval] = {}
            per_query_limit = max(6, MAX_CONTEXT_CHUNKS)

            for query_text, score_multiplier in retrieval_queries:
                query_embedding = await self._retrieval.generate_query_embedding(query_text)
                candidate_intervals = self._retrieval.search_similar_intervals(
                    db=db,
                    project_id=project_id,
                    query_embedding=query_embedding,
                    query_text=query_text,
                    limit=per_query_limit,
                    similarity_threshold=similarity_threshold,
                    content_filter=content_filter,
                )

                for interval in candidate_intervals:
                    adjusted_score = interval.similarity * score_multiplier
                    if adjusted_score <= 0:
                        continue

                    key = (interval.start_time_seconds, interval.end_time_seconds)
                    existing = merged_by_window.get(key)
                    if existing is None or adjusted_score > existing.similarity:
                        interval.similarity = adjusted_score
                        merged_by_window[key] = interval

            intervals = sorted(
                merged_by_window.values(),
                key=lambda r: r.similarity,
                reverse=True,
            )[:MAX_CONTEXT_CHUNKS]

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
            messages=messages,
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

    def stream_reply(
        self,
        *,
        project: Project,
        messages: list[dict[str, Any]],
        user_message: str,
        db: Session,
    ) -> tuple[Iterator[str], bool, int, list[str]]:
        """
        Stream assistant response chunks for real-time UI updates.

        Returns:
            (token_iterator, rag_was_active, context_chunks_used, context_chunks)
        """
        loop = asyncio.new_event_loop()
        try:
            context_chunks, rag_active = loop.run_until_complete(
                self.retrieve_project_context_async(
                    project_id=project.id,
                    query=user_message,
                    messages=messages,
                    db=db,
                )
            )
        finally:
            loop.close()

        system_preamble = self._build_system_prompt(
            project=project,
            context_chunks=context_chunks,
            rag_active=rag_active,
        )
        contents = self._build_contents(messages=messages, user_message=user_message)

        def _token_iter() -> Iterator[str]:
            stream = client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_preamble,
                    temperature=0.7,
                    response_mime_type="text/plain",
                ),
            )
            for chunk in stream:
                text = getattr(chunk, "text", None)
                if text is not None and text != "":
                    yield text

        return _token_iter(), rag_active, len(context_chunks), context_chunks

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

    async def _plan_query_transformation_async(
        self,
        *,
        query: str,
        messages: list[dict[str, Any]],
    ) -> QueryTransformPlan:
        """
        Ask the LLM how to transform the query for retrieval.
        Returns a conservative fallback plan on parse or API failures.
        """
        clean_query = (query or "").strip()
        fallback = QueryTransformPlan(
            strategy="original",
            rewritten_query=clean_query,
            search_queries=[clean_query] if clean_query else [],
        )
        if not clean_query:
            return fallback

        recent_messages: list[dict[str, str]] = []
        for m in messages[-6:]:
            role = (m.get("role") or "").strip().lower()
            content = (m.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                recent_messages.append({"role": role, "content": content[:800]})

        planner_prompt = (
            "You are a retrieval query planner for a video analysis RAG system.\n"
            "Input: a user's latest query and recent chat context.\n"
            "Task: decide how to transform the query for vector retrieval.\n"
            "Return strict JSON only with keys:\n"
            "{\n"
            '  "strategy": "original|rewrite|multi_query|hyde|multi_hyde",\n'
            '  "rewritten_query": "string",\n'
            '  "search_queries": ["string", ... up to 4],\n'
            '  "keywords": ["string", ... up to 8],\n'
            '  "hyde_passage": "string",\n'
            '  "content_focus": "motion|camera|environment|people|objects|lighting|audio|"\n'
            "}\n"
            "Guidelines:\n"
            "- Keep rewritten_query concise and retrieval-oriented.\n"
            "- multi_query: produce diverse phrasings for the same intent.\n"
            "- hyde/multi_hyde: include a technical hypothetical description in hyde_passage.\n"
            "- keywords should be concrete domain terms, not stopwords.\n"
            "- If unsure, choose strategy 'rewrite'.\n"
        )
        planner_input = {
            "latest_query": clean_query,
            "recent_messages": recent_messages,
        }

        loop = asyncio.get_running_loop()
        try:
            resp = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=self.model,
                    contents=[json.dumps(planner_input, ensure_ascii=False)],
                    config=types.GenerateContentConfig(
                        system_instruction=planner_prompt,
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                ),
            )
            raw = (resp.text or "").strip()
            payload = self._safe_parse_json_object(raw)
            if not payload:
                return fallback

            strategy = str(payload.get("strategy") or "rewrite").strip().lower()
            if strategy not in {"original", "rewrite", "multi_query", "hyde", "multi_hyde"}:
                strategy = "rewrite"

            rewritten_query = str(payload.get("rewritten_query") or clean_query).strip()
            if not rewritten_query:
                rewritten_query = clean_query

            search_queries = self._normalize_query_list(payload.get("search_queries"), limit=4)
            keywords = self._normalize_keyword_list(payload.get("keywords"), limit=8)
            hyde_passage = str(payload.get("hyde_passage") or "").strip()
            content_focus = str(payload.get("content_focus") or "").strip().lower()
            if content_focus not in {"motion", "camera", "environment", "people", "objects", "lighting", "audio"}:
                content_focus = ""

            if rewritten_query and rewritten_query not in search_queries:
                search_queries.insert(0, rewritten_query)
            if clean_query and clean_query not in search_queries:
                search_queries.append(clean_query)

            return QueryTransformPlan(
                strategy=strategy,
                rewritten_query=rewritten_query,
                search_queries=search_queries[:4],
                keywords=keywords,
                hyde_passage=hyde_passage,
                content_focus=content_focus,
            )
        except Exception as exc:
            logger.warning("[RAG] Query transformation failed, using fallback: %s", exc)
            return fallback

    def _build_retrieval_queries(
        self,
        *,
        original_query: str,
        plan: QueryTransformPlan,
    ) -> list[tuple[str, float]]:
        """
        Build ordered query list with score multipliers for fusion.
        """
        candidates: list[tuple[str, float]] = []
        primary = (plan.rewritten_query or original_query or "").strip()
        if primary:
            candidates.append((primary, 1.0))

        if plan.strategy in {"multi_query", "multi_hyde"}:
            for q in plan.search_queries:
                clean = q.strip()
                if clean:
                    candidates.append((clean, 0.93))

        if plan.keywords:
            keyword_query = " ".join(plan.keywords[:6]).strip()
            if keyword_query:
                candidates.append((keyword_query, 0.89))

        if plan.strategy in {"hyde", "multi_hyde"} and plan.hyde_passage.strip():
            candidates.append((plan.hyde_passage.strip(), 0.86))

        # Deduplicate while preserving first occurrence (highest weight).
        deduped: list[tuple[str, float]] = []
        seen: set[str] = set()
        for text, weight in candidates:
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append((text, weight))

        if not deduped and original_query.strip():
            deduped.append((original_query.strip(), 1.0))

        return deduped[:6]

    def _infer_content_filter(
        self,
        *,
        primary_query: str,
        keywords: list[str],
        content_focus: str,
    ) -> Optional[str]:
        if content_focus in CONTENT_KEYWORDS:
            return content_focus

        # Prefer explicit keyword signal before plain query heuristics.
        keyword_blob = " ".join(keywords).lower()
        for content_type, terms in CONTENT_KEYWORDS.items():
            if any(term in keyword_blob for term in terms):
                return content_type

        return self._retrieval.detect_content_type(primary_query)

    def _normalize_query_list(self, raw: Any, *, limit: int) -> list[str]:
        if not isinstance(raw, list):
            return []
        out: list[str] = []
        for item in raw:
            value = str(item or "").strip()
            if value and value not in out:
                out.append(value)
            if len(out) >= limit:
                break
        return out

    def _normalize_keyword_list(self, raw: Any, *, limit: int) -> list[str]:
        if not isinstance(raw, list):
            return []
        out: list[str] = []
        for item in raw:
            value = str(item or "").strip().lower()
            if not value:
                continue
            if len(value) > 40:
                value = value[:40].rstrip()
            if value and value not in out:
                out.append(value)
            if len(out) >= limit:
                break
        return out

    def _safe_parse_json_object(self, raw: str) -> Optional[dict[str, Any]]:
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # Fallback: extract first {...} object from model output.
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None
        return None

    def _build_system_prompt(
        self,
        *,
        project: Project,
        context_chunks: list[str],
        rag_active: bool,
    ) -> str:
        lines = [
            "ROLE",
            "You are a structured video performance analysis assistant embedded inside a SaaS video intelligence platform.",
            "Your job is to help the user analyze, interpret, and optimize their video project using available structured analysis data.",
            "",
            f"Project name: {project.name}",
            f"Project id: {project.id}",
            "",
            "CONTEXT RULES",
            "You have access to structured interval analysis, performance metrics, psychological classifications, and modeling outputs related to this project.",
            "You must prioritize project-specific data when answering.",
            "If analysis data exists, use it.",
            "If data is missing, explicitly state what is unavailable.",
            "",
            "BEHAVIOR RULES",
            "- Be analytical, precise, and structured.",
            "- Base conclusions only on available data.",
            "- Do not hallucinate unseen video content.",
            "- Do not invent metrics.",
            "- If something cannot be determined from the stored analysis, say: 'Not enough analyzed data available.'",
            "",
            "SCOPE HANDLING",
            "If the user asks something unrelated to this video project, answer normally as a general assistant.",
            "If the question is partially related, separate your answer into:",
            "1) Project-specific analysis",
            "2) General guidance (if necessary)",
            "",
            "OPTIMIZATION MODE",
            "When the user asks for improvements, provide mechanical, structural recommendations rather than motivational advice.",
            "Focus on retention, hook strength, engagement triggers, pacing, authority signals, and platform compatibility.",
            "",
            "UNCERTAINTY POLICY",
            "If you do not know something, say so clearly.",
            "Do not guess.",
        ]

        if rag_active and context_chunks:
            lines.append(
                "The following are the most relevant segments retrieved from the "
                "video's visual analysis database, ordered by relevance to the user's "
                "question. Use this context to give accurate, time-specific answers."
                "if the retrived context contain scores of the video, use them to give accurate answers without mentioning the scores."
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

