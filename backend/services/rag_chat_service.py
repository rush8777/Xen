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
MAX_COURSE_SLIDES = 12
MIN_COURSE_SLIDES = 6


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

            merged_by_window: dict[tuple[str, int, int], RetrievedInterval] = {}
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

                    key = (
                        interval.source,
                        interval.start_time_seconds,
                        interval.end_time_seconds,
                    )
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

    async def detect_course_intent_async(
        self,
        *,
        project: Project,
        messages: list[dict[str, Any]],
        user_message: str,
    ) -> dict[str, Any]:
        """
        Detect whether latest user request should trigger a course generation flow.
        Returns a conservative fallback on any parser/model failure.
        """
        latest = (user_message or "").strip()
        if not latest:
            return {"is_course_request": False, "confidence": 0.0, "goal": ""}

        recent_messages: list[dict[str, str]] = []
        for m in messages[-8:]:
            role = (m.get("role") or "").strip().lower()
            content = (m.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                recent_messages.append({"role": role, "content": content[:1000]})

        detector_prompt = (
            "You are an intent classifier for a video-analysis chat assistant.\n"
            "Decide if the user is asking for a generated learning course/slides/training path.\n"
            "Use broad detection: requests for coaching plan, improvement program, learning slides, "
            "or guided lesson should usually be true.\n"
            "Return strict JSON only with keys:\n"
            "{\n"
            '  "is_course_request": boolean,\n'
            '  "confidence": number,\n'
            '  "goal": "short string"\n'
            "}\n"
            "confidence must be between 0 and 1.\n"
            "goal should summarize the intended learning/improvement objective."
        )
        detector_input = {
            "project_name": project.name,
            "latest_user_message": latest,
            "recent_messages": recent_messages,
        }

        loop = asyncio.get_running_loop()
        try:
            resp = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=self.model,
                    contents=[json.dumps(detector_input, ensure_ascii=False)],
                    config=types.GenerateContentConfig(
                        system_instruction=detector_prompt,
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                ),
            )
            payload = self._safe_parse_json_object((resp.text or "").strip()) or {}
            is_course_request = bool(payload.get("is_course_request"))
            try:
                confidence = float(payload.get("confidence", 0.0))
            except Exception:
                confidence = 0.0
            confidence = max(0.0, min(1.0, confidence))
            goal = str(payload.get("goal") or "").strip()[:240]
            return {
                "is_course_request": is_course_request,
                "confidence": confidence,
                "goal": goal,
            }
        except Exception as exc:
            logger.warning("[RAG] Course intent detection failed: %s", exc)
            return {"is_course_request": False, "confidence": 0.0, "goal": ""}

    async def generate_course_async(
        self,
        *,
        project: Project,
        messages: list[dict[str, Any]],
        user_message: str,
        goal: str,
        course_requirements: Optional[dict[str, Any]] = None,
        db: Session,
    ) -> tuple[str, dict[str, Any], bool, int, list[str]]:
        """
        Generate structured course data compatible with TeachCanvasKit.

        Returns:
            (course_summary, course_data, rag_was_active, context_chunks_used, context_chunks)
        """
        context_chunks, rag_active = await self.retrieve_project_context_async(
            project_id=project.id,
            query=user_message,
            messages=messages,
            db=db,
        )

        context_blob = "\n\n".join(context_chunks) if context_chunks else ""
        course_prompt = (
            "You are an expert video growth educator.\n"
            "Generate an actionable mini-course to improve the user's video performance.\n"
            "Return strict JSON only with keys:\n"
            "{\n"
            '  "course_summary": "string",\n'
            '  "course_data": {\n'
            '    "courseTitle": "string",\n'
            '    "slides": [\n'
            "      {\n"
            '        "id": "string",\n'
            '        "type": "title|text-image|text-only|cards|checklist|quiz",\n'
            '        "title": "string",\n'
            '        "subtitle": "string?",\n'
            '        "body": "string?",\n'
            '        "buttonLabel": "string?",\n'
            '        "cards": [{"heading":"string","description":"string","icon":"string?"}]?,\n'
            '        "items": [{"text":"string","checked":boolean?}]?,\n'
            '        "quizQuestion": "string?",\n'
            '        "quizOptions": ["string"]?,\n'
            '        "correctAnswer": number?\n'
            "      }\n"
            "    ]\n"
            "  }\n"
            "}\n"
            "Constraints:\n"
            "- 6 to 12 slides.\n"
            "- Include at least 1 checklist slide with concrete action items.\n"
            "- Include at least 1 quiz slide for reinforcement.\n"
            "- Recommendations should optimize retention, hook strength, views, likes, engagement when relevant.\n"
            "- Keep language practical and specific.\n"
            "- If project context is limited, still produce a useful course and mention data limitations in summary.\n"
        )

        recent_messages: list[dict[str, str]] = []
        for m in messages[-8:]:
            role = (m.get("role") or "").strip().lower()
            content = (m.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                recent_messages.append({"role": role, "content": content[:900]})

        course_input = {
            "project_name": project.name,
            "user_goal": (goal or "").strip(),
            "latest_user_message": user_message,
            "recent_messages": recent_messages,
            "course_requirements": course_requirements or {},
            "retrieved_context": context_blob[:MAX_CONTEXT_CHARS],
        }

        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=self.model,
                contents=[json.dumps(course_input, ensure_ascii=False)],
                config=types.GenerateContentConfig(
                    system_instruction=course_prompt,
                    temperature=0.4,
                    response_mime_type="application/json",
                ),
            ),
        )
        payload = self._safe_parse_json_object((resp.text or "").strip())
        if not payload:
            raise ValueError("Failed to parse course JSON")

        course_summary = str(payload.get("course_summary") or "").strip()
        course_data = self._sanitize_course_payload(payload.get("course_data"))
        if not course_data:
            raise ValueError("Generated course payload failed validation")

        if not course_summary:
            course_summary = (
                f"I created a focused course for improving '{project.name}' with "
                "step-by-step slides and a quiz."
            )
        course_summary = course_summary[:700]
        return course_summary, course_data, rag_active, len(context_chunks), context_chunks

    async def plan_course_clarification_async(
        self,
        *,
        project: Project,
        messages: list[dict[str, Any]],
        user_message: str,
        goal: str,
    ) -> dict[str, Any]:
        """
        Ask the model whether course clarification is needed and generate
        follow-up questions dynamically (no hardcoded questions).
        """
        latest = (user_message or "").strip()
        recent_messages: list[dict[str, str]] = []
        for m in messages[-10:]:
            role = (m.get("role") or "").strip().lower()
            content = (m.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                recent_messages.append({"role": role, "content": content[:1200]})

        planner_prompt = (
            "You are a course-design intake planner for a video coaching assistant.\n"
            "Your job: decide if we need clarification before generating a high-quality course.\n"
            "Do not hardcode fixed questions; adapt questions to the user's request and context.\n"
            "Prefer asking only essential questions.\n"
            "Return strict JSON with keys:\n"
            "{\n"
            '  "needs_clarification": boolean,\n'
            '  "assistant_message": "string",\n'
            '  "questions": [\n'
            "    {\n"
            '      "id": "short_snake_case",\n'
            '      "label": "question text",\n'
            '      "input_type": "single_choice|multi_choice|short_text|number",\n'
            '      "options": ["option 1", "option 2", "..."],\n'
            '      "max_select": number,\n'
            '      "placeholder": "string",\n'
            '      "required": boolean\n'
            "    }\n"
            "  ],\n"
            '  "reasoning_brief": "short string"\n'
            "}\n"
            "Guidelines:\n"
            "- Ask 2 to 6 questions when clarification is needed.\n"
            "- Prefer compact multiple-choice questions (single_choice or multi_choice).\n"
            "- Keep options short and scannable (usually 3 to 6 options).\n"
            "- Use short_text only when options cannot cover the likely answers.\n"
            "- Questions can include scope, topics, audience level, desired slide count, tone, constraints, examples.\n"
            "- If info is already sufficient, set needs_clarification=false and return an empty questions array.\n"
            "- assistant_message should be concise and user-facing.\n"
            "- required should be true only when essential for quality.\n"
        )
        planner_input = {
            "project_name": project.name,
            "goal": (goal or "").strip(),
            "latest_user_message": latest,
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
                        temperature=0.2,
                        response_mime_type="application/json",
                    ),
                ),
            )
            payload = self._safe_parse_json_object((resp.text or "").strip()) or {}
            needs_clarification = bool(payload.get("needs_clarification"))
            assistant_message = str(payload.get("assistant_message") or "").strip()

            questions_raw = payload.get("questions")
            questions: list[dict[str, Any]] = []
            if isinstance(questions_raw, list):
                for idx, q in enumerate(questions_raw[:6]):
                    if not isinstance(q, dict):
                        continue
                    qid = self._normalize_text(q.get("id"), 40).lower().replace(" ", "_")
                    if not qid:
                        qid = f"q_{idx + 1}"
                    label = self._normalize_text(q.get("label"), 220)
                    if not label:
                        continue
                    input_type = self._normalize_text(q.get("input_type"), 20).lower()
                    if input_type not in {"single_choice", "multi_choice", "short_text", "number"}:
                        input_type = "short_text"
                    placeholder = self._normalize_text(q.get("placeholder"), 180)
                    required = bool(q.get("required", True))
                    options: list[str] = []
                    options_raw = q.get("options")
                    if isinstance(options_raw, list):
                        for option in options_raw[:8]:
                            opt = self._normalize_text(option, 80)
                            if opt and opt not in options:
                                options.append(opt)
                    if input_type in {"single_choice", "multi_choice"} and len(options) < 2:
                        input_type = "short_text"
                        options = []
                    try:
                        max_select = int(q.get("max_select", 2))
                    except Exception:
                        max_select = 2
                    if max_select < 1:
                        max_select = 1
                    if input_type != "multi_choice":
                        max_select = 1
                    questions.append(
                        {
                            "id": qid,
                            "label": label,
                            "input_type": input_type,
                            "options": options,
                            "max_select": max_select,
                            "placeholder": placeholder,
                            "required": required,
                        }
                    )

            if needs_clarification and not questions:
                needs_clarification = False

            if not assistant_message:
                if needs_clarification:
                    assistant_message = (
                        "Before I generate the course, I need a few details to tailor it well."
                    )
                else:
                    assistant_message = "I have enough information to generate the course."

            return {
                "needs_clarification": needs_clarification,
                "assistant_message": assistant_message[:500],
                "questions": questions,
            }
        except Exception as exc:
            logger.warning("[RAG] Course clarification planning failed: %s", exc)
            return {
                "needs_clarification": False,
                "assistant_message": "",
                "questions": [],
            }

    async def generate_chat_heading_async(
        self,
        *,
        project: Project,
        messages: list[dict[str, Any]],
    ) -> str:
        """
        Generate a short, user-friendly chat heading from recent conversation.
        """
        convo: list[dict[str, str]] = []
        for m in messages[-10:]:
            role = (m.get("role") or "").strip().lower()
            content = (m.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                convo.append({"role": role, "content": content[:450]})

        prompt = (
            "You generate concise chat titles.\n"
            "Return strict JSON only:\n"
            "{ \"heading\": \"string\" }\n"
            "Rules:\n"
            "- 3 to 8 words.\n"
            "- Specific to the conversation goal.\n"
            "- No quotes, emojis, or trailing punctuation.\n"
            "- Avoid generic titles like 'Chat', 'Conversation', 'Project discussion'.\n"
        )
        payload = {
            "project_name": project.name,
            "recent_messages": convo,
        }

        loop = asyncio.get_running_loop()
        try:
            resp = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=self.model,
                    contents=[json.dumps(payload, ensure_ascii=False)],
                    config=types.GenerateContentConfig(
                        system_instruction=prompt,
                        temperature=0.2,
                        response_mime_type="application/json",
                    ),
                ),
            )
            parsed = self._safe_parse_json_object((resp.text or "").strip()) or {}
            heading = self._normalize_text(parsed.get("heading"), 80)
            if heading:
                return heading
        except Exception as exc:
            logger.warning("[RAG] Chat heading generation failed: %s", exc)

        # Fallback deterministic heading from latest user message.
        latest_user = ""
        for m in reversed(messages):
            if (m.get("role") or "").strip().lower() == "user":
                latest_user = (m.get("content") or "").strip()
                break
        fallback = self._normalize_text(latest_user, 80) or f"{project.name} Analysis"
        return fallback

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

    def _sanitize_course_payload(self, raw: Any) -> Optional[dict[str, Any]]:
        if not isinstance(raw, dict):
            return None

        course_title = self._normalize_text(raw.get("courseTitle"), 120)
        if not course_title:
            course_title = "Video Improvement Course"

        raw_slides = raw.get("slides")
        if not isinstance(raw_slides, list):
            return None

        allowed_types = {"title", "text-image", "text-only", "cards", "checklist", "quiz"}
        slides: list[dict[str, Any]] = []
        has_checklist = False
        has_quiz = False

        for idx, slide_raw in enumerate(raw_slides[:MAX_COURSE_SLIDES]):
            if not isinstance(slide_raw, dict):
                continue
            slide_type = self._normalize_text(slide_raw.get("type"), 40).lower()
            if slide_type not in allowed_types:
                continue

            slide_title = self._normalize_text(slide_raw.get("title"), 140)
            if not slide_title:
                continue

            slide_id = self._normalize_text(slide_raw.get("id"), 64) or f"s{idx + 1}"
            slide: dict[str, Any] = {"id": slide_id, "type": slide_type, "title": slide_title}

            subtitle = self._normalize_text(slide_raw.get("subtitle"), 260)
            body = self._normalize_text(slide_raw.get("body"), 1800)
            button_label = self._normalize_text(slide_raw.get("buttonLabel"), 40)

            if subtitle:
                slide["subtitle"] = subtitle
            if body:
                slide["body"] = body
            if button_label:
                slide["buttonLabel"] = button_label

            if slide_type in {"text-image", "text-only"} and not body:
                continue

            if slide_type == "cards":
                cards_raw = slide_raw.get("cards")
                if not isinstance(cards_raw, list) or not cards_raw:
                    continue
                cards: list[dict[str, Any]] = []
                for card_raw in cards_raw[:8]:
                    if not isinstance(card_raw, dict):
                        continue
                    heading = self._normalize_text(card_raw.get("heading"), 80)
                    description = self._normalize_text(card_raw.get("description"), 300)
                    icon = self._normalize_text(card_raw.get("icon"), 20)
                    if not heading or not description:
                        continue
                    card_obj: dict[str, Any] = {"heading": heading, "description": description}
                    if icon:
                        card_obj["icon"] = icon
                    cards.append(card_obj)
                if not cards:
                    continue
                slide["cards"] = cards

            if slide_type == "checklist":
                items_raw = slide_raw.get("items")
                if not isinstance(items_raw, list) or not items_raw:
                    continue
                items: list[dict[str, Any]] = []
                for item_raw in items_raw[:12]:
                    if isinstance(item_raw, dict):
                        text = self._normalize_text(item_raw.get("text"), 240)
                        checked = bool(item_raw.get("checked", False))
                    else:
                        text = self._normalize_text(item_raw, 240)
                        checked = False
                    if not text:
                        continue
                    items.append({"text": text, "checked": checked})
                if len(items) < 2:
                    continue
                slide["items"] = items
                has_checklist = True

            if slide_type == "quiz":
                question = self._normalize_text(slide_raw.get("quizQuestion"), 240)
                options_raw = slide_raw.get("quizOptions")
                if not question or not isinstance(options_raw, list):
                    continue
                quiz_options = [
                    self._normalize_text(opt, 140)
                    for opt in options_raw[:6]
                    if self._normalize_text(opt, 140)
                ]
                if len(quiz_options) < 2:
                    continue
                try:
                    correct_answer = int(slide_raw.get("correctAnswer", 0))
                except Exception:
                    correct_answer = 0
                if correct_answer < 0 or correct_answer >= len(quiz_options):
                    correct_answer = 0
                slide["quizQuestion"] = question
                slide["quizOptions"] = quiz_options
                slide["correctAnswer"] = correct_answer
                has_quiz = True

            slides.append(slide)

        if len(slides) < MIN_COURSE_SLIDES:
            return None
        if not has_checklist or not has_quiz:
            return None

        return {"courseTitle": course_title, "slides": slides}

    def _normalize_text(self, value: Any, max_len: int) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        compact = re.sub(r"\s+", " ", text)
        return compact[:max_len].strip()

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



