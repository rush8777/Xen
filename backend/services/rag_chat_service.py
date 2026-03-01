from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
MAX_COURSE_SLIDES = 30
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

    async def _resolve_cached_video_state_async(
        self,
        *,
        project: Project,
    ) -> tuple[bool, Optional[datetime]]:
        """
        Decide whether Gemini cached video should be used for this request.

        Returns:
            (use_cached_video, expires_at_utc)
        """
        cached_content_name = (project.gemini_cached_content_name or "").strip()
        if not cached_content_name:
            return False, None

        loop = asyncio.get_running_loop()
        try:
            cache_obj = await loop.run_in_executor(
                None,
                lambda: client.caches.get(name=cached_content_name),
            )
        except Exception as exc:
            logger.info(
                "[RAG] Cached video lookup failed for project %s (%s): %s",
                project.id,
                cached_content_name,
                exc,
            )
            return False, None

        expires_at = self._extract_cache_expiry(cache_obj)
        if expires_at is None:
            return True, None
        return expires_at > datetime.now(timezone.utc), expires_at

    def _extract_cache_expiry(self, cache_obj: Any) -> Optional[datetime]:
        if cache_obj is None:
            return None

        for key in ("expire_time", "expires_at", "expireTime", "expiry_time"):
            value = getattr(cache_obj, key, None)
            dt_value = self._coerce_to_utc_datetime(value)
            if dt_value is not None:
                return dt_value

        if hasattr(cache_obj, "to_dict"):
            try:
                payload = cache_obj.to_dict() or {}
                for key in ("expire_time", "expires_at", "expireTime", "expiry_time"):
                    dt_value = self._coerce_to_utc_datetime(payload.get(key))
                    if dt_value is not None:
                        return dt_value
            except Exception:
                pass

        return None

    def _coerce_to_utc_datetime(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)

        if isinstance(value, dict):
            try:
                seconds = int(value.get("seconds"))
                nanos = int(value.get("nanos", 0))
                return datetime.fromtimestamp(
                    seconds + (nanos / 1_000_000_000.0),
                    tz=timezone.utc,
                )
            except Exception:
                return None

        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            if cleaned.endswith("Z"):
                cleaned = cleaned[:-1] + "+00:00"
            try:
                parsed = datetime.fromisoformat(cleaned)
            except Exception:
                return None
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)

        iso_fn = getattr(value, "isoformat", None)
        if callable(iso_fn):
            try:
                return self._coerce_to_utc_datetime(iso_fn())
            except Exception:
                return None
        return None

    def _build_cached_video_system_prompt(
        self,
        *,
        project: Project,
        expires_at: Optional[datetime],
    ) -> str:
        expiry_line = (
            f"Cached video expiry (UTC): {expires_at.isoformat()}"
            if expires_at is not None
            else "Cached video expiry (UTC): unknown"
        )
        return "\n".join(
            [
                "ROLE",
                "You are a structured video performance analysis assistant embedded inside a SaaS video intelligence platform.",
                f"Project name: {project.name}",
                f"Project id: {project.id}",
                "",
                "CONTEXT RULES",
                "Answer using the attached Gemini cached video content as the primary source of truth.",
                "Ground conclusions in what is visible/audible in the video and explicitly acknowledge uncertainty when evidence is missing.",
                "Do not invent metrics or claim observations that are not supported by the video.",
                expiry_line,
                "",
                "OUTPUT RULES",
                "- Be analytical, precise, and structured.",
                "- If the user asks for optimization, provide practical, mechanical improvements.",
                "- If a requested fact cannot be verified from video evidence, clearly say so.",
            ]
        )

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
        use_cached_video, cached_expires_at = await self._resolve_cached_video_state_async(
            project=project
        )
        if use_cached_video:
            contents = self._build_contents(messages=messages, user_message=user_message)
            loop = asyncio.get_running_loop()
            try:
                resp = await loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            cached_content=project.gemini_cached_content_name,
                            temperature=0.7,
                            response_mime_type="text/plain",
                        ),
                    ),
                )
                text = (resp.text or "").strip()
                if not text:
                    raise ValueError("Empty response from Gemini cached video flow")
                expiry_note = (
                    f"Using Gemini cached video until {cached_expires_at.isoformat()} UTC."
                    if cached_expires_at is not None
                    else "Using Gemini cached video."
                )
                return text, True, 1, [expiry_note]
            except Exception as exc:
                logger.warning(
                    "[RAG] Cached video generation failed for project %s, falling back to RAG: %s",
                    project.id,
                    exc,
                )

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
            "Set is_course_request=true ONLY when the user explicitly asks for a course-like deliverable "
            "(course, lessons, slides, curriculum, training plan, learning path, tutorial plan).\n"
            "For normal Q&A, greetings, small talk, summarization, analysis questions, and generic advice, "
            "set is_course_request=false.\n"
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
        template = str((course_requirements or {}).get("course_template") or "sonos_typo").strip().lower()
        if template not in {"default", "sonos_typo", "pixel_brutalist", "brand_guides"}:
            template = "sonos_typo"
        content_profile = self._build_course_content_profile(
            user_message=user_message,
            goal=goal,
            course_requirements=course_requirements or {},
            recent_messages=messages[-8:],
        )

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
            "- Generate 6 to 30 slides.\n"
            "- Use content_profile.recommended_slide_count as the baseline, and expand depth when needed.\n"
            "- For comprehensive/professional requests, prefer 18 to 30 slides when the topic scope supports it.\n"
            "- Include at least 1 checklist slide with concrete action items.\n"
            "- Include at least 1 quiz slide for reinforcement.\n"
            "- Adapt slide depth and text density based on content_profile. Avoid uniform fixed-size slides.\n"
            "- Break large topics into multiple sequential slides/sections when needed (do not compress everything into one slide).\n"
            "- Recommendations should optimize retention, hook strength, views, likes, engagement when relevant.\n"
            "- Keep language practical and specific.\n"
            "- If project context is limited, still produce a useful course and mention data limitations in summary.\n"
        )
        sonos_prompt = (
            "You are designing a SonosTypoCourse native deck.\n"
            "Return strict JSON only with keys:\n"
            "{\n"
            '  "course_summary": "string",\n'
            '  "course_data": {\n'
            '    "courseTitle": "string",\n'
            '    "subtitle": "string",\n'
            '    "slides": [\n'
            "      {\n"
            '        "type": "cover|statement|contents|overview|columns|cards|divider|highlights|checklist|quiz",\n'
            '        "palette": "navy|maroon|powder|olive|peach|midnight|lilac|charcoal",\n'
            '        "title": "string?",\n'
            '        "subtitle": "string?",\n'
            '        "buttonLabel": "string?",\n'
            '        "bigWord": "string?",\n'
            '        "leftText": "string?",\n'
            '        "rightLabel": "string?",\n'
            '        "rightText": "string?",\n'
            '        "items": ["string"] | [{"text":"string","checked":boolean}]?,\n'
            '        "paragraphs": ["string"]?,\n'
            '        "body": "string?",\n'
            '        "columns": [{"heading":"string?","body":"string?","description":"string?","title":"string?","text":"string?"}]?,\n'
            '        "cards": [{"heading":"string?","description":"string?","title":"string?","body":"string?","text":"string?"}]?,\n'
            '        "lines": ["string"]?,\n'
            '        "quizQuestion": "string?",\n'
            '        "quizOptions": ["string"]?,\n'
            '        "correctAnswer": number?\n'
            "      }\n"
            "    ]\n"
            "  }\n"
            "}\n"
            "Constraints:\n"
            "- Generate 6 to 30 slides.\n"
            "- Use content_profile.recommended_slide_count as the baseline, and expand depth when needed.\n"
            "- For comprehensive/professional requests, prefer 18 to 30 slides when the topic scope supports it.\n"
            "- Include at least 1 checklist and 1 quiz slide.\n"
            "- Include at least 1 columns or cards slide with concrete tactics.\n"
            "- For each columns/cards slide, choose the number of blocks dynamically from content complexity (usually 2 to 4); do not force a fixed count.\n"
            "- Avoid sparse middle columns: if you include a middle block, give it substantive copy similar depth to neighboring blocks.\n"
            "- Do not use placeholder one-word bodies; each block should have a practical paragraph (typically 1 to 3 sentences).\n"
            "- Use Sonos-appropriate typography-first text blocks, but vary density per content_profile.\n"
            "- Avoid forcing fixed-length copy blocks across all slides.\n"
            "- Break large topics into multiple sequential slides/sections when needed (do not compress everything into one slide).\n"
            "- Keep recommendations practical and tied to retention/hook/views/engagement.\n"
        )
        brand_guides_prompt = (
            "You are designing a BrandGuidesCourse native deck.\n"
            "Return strict JSON only with keys:\n"
            "{\n"
            '  "course_summary": "string",\n'
            '  "course_data": {\n'
            '    "brand": {\n'
            '      "name": "string",\n'
            '      "accent": "hex color like #FF6B00",\n'
            '      "navLinks": ["string"],\n'
            '      "year": "string",\n'
            '      "version": "string"\n'
            "    },\n"
            '    "slides": [\n'
            "      {\n"
            '        "type": "cover|intro|toc|logo-grid|clear-space|logo-detail|typography|palette|logo-misuse|section",\n'
            '        "title": "string?",\n'
            '        "body": "string?",\n'
            '        "items": [{"number": number, "label": "string"}]?,\n'
            '        "rules": [{"type":"do|dont","text":"string"}]?,\n'
            '        "swatches": [{"name":"string","hex":"#RRGGBB","cmyk":"string?","rgb":"string?","width": number?}]?\n'
            "      }\n"
            "    ]\n"
            "  }\n"
            "}\n"
            "Constraints:\n"
            "- Generate 6 to 30 slides.\n"
            "- Use content_profile.recommended_slide_count as the baseline, and expand depth when needed.\n"
            "- For comprehensive/professional requests, prefer 18 to 30 slides when the topic scope supports it.\n"
            "- Include at least one 'toc' slide and one 'palette' slide.\n"
            "- Include at least one 'logo-misuse' or 'clear-space' governance slide.\n"
            "- Adapt detail level from content_profile (light/balanced/deep) instead of fixed-size sections.\n"
            "- Break large topics into multiple sequential slides/sections when needed (do not compress everything into one slide).\n"
            "- Keep copy concise, practical, and creator-focused.\n"
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
            "course_template": template,
            "content_profile": content_profile,
        }

        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=self.model,
                contents=[json.dumps(course_input, ensure_ascii=False)],
                config=types.GenerateContentConfig(
                    system_instruction=(
                        sonos_prompt
                        if template == "sonos_typo"
                        else brand_guides_prompt
                        if template == "brand_guides"
                        else course_prompt
                    ),
                    temperature=0.4,
                    response_mime_type="application/json",
                ),
            ),
        )
        payload = self._safe_parse_json_object((resp.text or "").strip())
        if not payload:
            raise ValueError("Failed to parse course JSON")

        course_summary = str(payload.get("course_summary") or "").strip()
        if template == "sonos_typo":
            course_data = self._sanitize_sonos_course_payload(payload.get("course_data"))
        elif template == "brand_guides":
            course_data = self._sanitize_brand_guides_payload(payload.get("course_data"))
        else:
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
            "- Ask 2 to 4 questions when clarification is needed.\n"
            "- Prefer compact multiple-choice questions (single_choice or multi_choice).\n"
            "- Keep options short and scannable (usually 3 to 6 options).\n"
            "- Use short_text only when options cannot cover the likely answers.\n"
            "- Ask only essential questions that materially improve course quality.\n"
            "- Questions can include scope, topics, audience level, desired depth, tone, constraints, examples.\n"
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
                for idx, q in enumerate(questions_raw[:4]):
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
            use_cached_video, cached_expires_at = loop.run_until_complete(
                self._resolve_cached_video_state_async(project=project)
            )
        finally:
            loop.close()

        if use_cached_video:
            contents = self._build_contents(messages=messages, user_message=user_message)
            expiry_note = (
                f"Using Gemini cached video until {cached_expires_at.isoformat()} UTC."
                if cached_expires_at is not None
                else "Using Gemini cached video."
            )

            def _cached_token_iter() -> Iterator[str]:
                stream = client.models.generate_content_stream(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        cached_content=project.gemini_cached_content_name,
                        temperature=0.7,
                        response_mime_type="text/plain",
                    ),
                )
                for chunk in stream:
                    text = getattr(chunk, "text", None)
                    if text is not None and text != "":
                        yield text

            return _cached_token_iter(), True, 1, [expiry_note]

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

    def _build_course_content_profile(
        self,
        *,
        user_message: str,
        goal: str,
        course_requirements: dict[str, Any],
        recent_messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        joined = " ".join(
            [
                str(user_message or ""),
                str(goal or ""),
                " ".join(str((m or {}).get("content") or "") for m in recent_messages[-6:]),
                " ".join(f"{k}:{v}" for k, v in (course_requirements or {}).items()),
            ]
        ).lower()

        if any(k in joined for k in ("brand", "logo", "palette", "guideline", "typography")):
            content_type = "brand_guidelines"
        elif any(k in joined for k in ("technical", "spec", "framework", "api", "documentation")):
            content_type = "technical"
        elif any(k in joined for k in ("pitch", "presentation", "deck", "stakeholder", "exec")):
            content_type = "presentation"
        else:
            content_type = "educational"

        deep_signals = (
            "advanced",
            "comprehensive",
            "deep",
            "detailed",
            "step-by-step",
            "full",
            "professional",
            "complete course",
            "in-depth",
            "indepth",
            "masterclass",
        )
        light_signals = ("quick", "brief", "short", "summary", "overview")
        if any(k in joined for k in deep_signals):
            density_target = "deep"
        elif any(k in joined for k in light_signals):
            density_target = "light"
        else:
            density_target = "balanced"

        requested_slide_count = self._extract_requested_slide_count(joined)
        if density_target == "deep":
            complexity = "complex"
            slide_count = 20
        elif density_target == "light":
            complexity = "simple"
            slide_count = 8
        else:
            complexity = "medium"
            slide_count = 12

        # Context-rich requests can sustain larger, more complete course structures.
        if len(joined) > 1800:
            slide_count += 4
        if any(token in joined for token in ("full curriculum", "complete", "all modules", "end-to-end")):
            slide_count += 4

        if requested_slide_count is not None:
            slide_count = requested_slide_count

        if content_type == "brand_guidelines":
            slide_mix = {"cover": 1, "intro": 1, "toc": 1, "typography": 1, "palette": 1, "logo-misuse": 1}
        elif content_type == "technical":
            slide_mix = {"cover": 1, "overview": 2, "columns": 2, "checklist": 1, "quiz": 1}
        elif content_type == "presentation":
            slide_mix = {"cover": 1, "statement": 1, "contents": 1, "highlights": 2, "checklist": 1, "quiz": 1}
        else:
            slide_mix = {"cover": 1, "overview": 2, "columns": 1, "cards": 1, "checklist": 1, "quiz": 1}

        return {
            "content_type": content_type,
            "complexity": complexity,
            "density_target": density_target,
            "recommended_slide_count": max(MIN_COURSE_SLIDES, min(MAX_COURSE_SLIDES, slide_count)),
            "recommended_mix": slide_mix,
        }

    def _extract_requested_slide_count(self, text: str) -> Optional[int]:
        if not text:
            return None

        patterns = (
            r"\b(\d{1,2})\s*(?:slides?|pages?)\b",
            r"\b(?:slides?|pages?)\s*(?:of|around|about)?\s*(\d{1,2})\b",
        )
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                continue
            try:
                value = int(match.group(1))
            except Exception:
                continue
            if value >= MIN_COURSE_SLIDES:
                return max(MIN_COURSE_SLIDES, min(MAX_COURSE_SLIDES, value))
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

    def _sanitize_sonos_course_payload(self, raw: Any) -> Optional[dict[str, Any]]:
        if not isinstance(raw, dict):
            return None

        course_title = self._normalize_text(raw.get("courseTitle"), 120) or "Video Improvement Course"
        subtitle = self._normalize_text(raw.get("subtitle"), 120)

        raw_slides = raw.get("slides")
        if not isinstance(raw_slides, list):
            return None

        allowed_types = {
            "cover", "statement", "contents", "overview", "columns",
            "cards", "divider", "highlights", "checklist", "quiz",
        }
        allowed_palettes = {"navy", "maroon", "powder", "olive", "peach", "midnight", "lilac", "charcoal"}

        slides: list[dict[str, Any]] = []
        has_checklist = False
        has_quiz = False
        has_structured_cards = False

        type_aliases = {
            "title": "cover",
            "text-only": "overview",
            "text-image": "overview",
        }

        for slide_raw in raw_slides[:MAX_COURSE_SLIDES]:
            if not isinstance(slide_raw, dict):
                continue
            raw_type = self._normalize_text(slide_raw.get("type"), 40).lower()
            slide_type = type_aliases.get(raw_type, raw_type)

            # Coerce generic/ambiguous slides into Sonos-native types so the UI never
            # gets a non-renderable slide.
            if slide_type not in allowed_types:
                if isinstance(slide_raw.get("quizOptions"), list):
                    slide_type = "quiz"
                elif isinstance(slide_raw.get("columns"), list):
                    slide_type = "columns"
                elif isinstance(slide_raw.get("cards"), list):
                    slide_type = "cards"
                elif isinstance(slide_raw.get("items"), list):
                    has_check = False
                    for item in slide_raw.get("items") or []:
                        if isinstance(item, dict) and "checked" in item:
                            has_check = True
                            break
                    slide_type = "checklist" if has_check else "contents"
                elif self._normalize_text(slide_raw.get("bigWord"), 20):
                    slide_type = "statement"
                elif isinstance(slide_raw.get("lines"), list):
                    slide_type = "highlights"
                elif self._normalize_text(slide_raw.get("body"), 20):
                    slide_type = "overview"
                else:
                    slide_type = "divider"

            if slide_type not in allowed_types:
                continue

            slide: dict[str, Any] = {"type": slide_type}
            palette = self._normalize_text(slide_raw.get("palette"), 30).lower()
            if palette in allowed_palettes:
                slide["palette"] = palette

            # Shared text fields
            for field, lim in (
                ("title", 140), ("subtitle", 320), ("buttonLabel", 40),
                ("bigWord", 120), ("leftText", 800), ("rightLabel", 80),
                ("rightText", 800), ("body", 1200), ("quizQuestion", 260),
            ):
                value = self._normalize_text(slide_raw.get(field), lim)
                if value:
                    slide[field] = value

            # paragraphs
            paragraphs_raw = slide_raw.get("paragraphs")
            if isinstance(paragraphs_raw, list):
                paragraphs = [self._normalize_text(p, 500) for p in paragraphs_raw]
                paragraphs = [p for p in paragraphs if p]
                if paragraphs:
                    slide["paragraphs"] = paragraphs[:6]

            # items
            items_raw = slide_raw.get("items")
            if isinstance(items_raw, list):
                if slide_type == "checklist":
                    checklist_items: list[dict[str, Any]] = []
                    for it in items_raw[:12]:
                        if isinstance(it, dict):
                            text = self._normalize_text(it.get("text"), 260)
                            checked = bool(it.get("checked", False))
                        else:
                            text = self._normalize_text(it, 260)
                            checked = False
                        if not text:
                            continue
                        checklist_items.append({"text": text, "checked": checked})
                    if checklist_items:
                        slide["items"] = checklist_items
                        has_checklist = True
                else:
                    strings = [self._normalize_text(it, 200) for it in items_raw]
                    strings = [s for s in strings if s]
                    if strings:
                        slide["items"] = strings[:12]

            # columns
            columns_raw = slide_raw.get("columns")
            if isinstance(columns_raw, list):
                columns: list[dict[str, Any]] = []
                for col in columns_raw[:6]:
                    if not isinstance(col, dict):
                        continue
                    heading = self._normalize_text(col.get("heading") or col.get("title"), 100)
                    body = self._normalize_text(
                        col.get("body") or col.get("description") or col.get("text"),
                        500,
                    )
                    if heading or body:
                        columns.append({"heading": heading or "Point", "body": body or "Details"})
                if columns:
                    slide["columns"] = columns
                    has_structured_cards = True

            # cards
            cards_raw = slide_raw.get("cards")
            if isinstance(cards_raw, list):
                cards: list[dict[str, Any]] = []
                for card in cards_raw[:8]:
                    if not isinstance(card, dict):
                        continue
                    heading = self._normalize_text(card.get("heading") or card.get("title"), 100)
                    description = self._normalize_text(
                        card.get("description") or card.get("body") or card.get("text"),
                        500,
                    )
                    if heading or description:
                        cards.append({
                            "heading": heading or "Point",
                            "description": description or "Details",
                        })
                if cards:
                    slide["cards"] = cards
                    has_structured_cards = True

            # highlights lines
            lines_raw = slide_raw.get("lines")
            if isinstance(lines_raw, list):
                lines = [self._normalize_text(line, 120) for line in lines_raw]
                lines = [line for line in lines if line]
                if lines:
                    slide["lines"] = lines[:10]

            # quiz
            if slide_type == "quiz":
                options_raw = slide_raw.get("quizOptions")
                if isinstance(options_raw, list):
                    options = [self._normalize_text(o, 180) for o in options_raw]
                    options = [o for o in options if o]
                    if len(options) >= 2:
                        slide["quizOptions"] = options[:6]
                        try:
                            ca = int(slide_raw.get("correctAnswer", 0))
                        except Exception:
                            ca = 0
                        if ca < 0 or ca >= len(slide["quizOptions"]):
                            ca = 0
                        slide["correctAnswer"] = ca
                        has_quiz = True

            # Minimal validity by type
            if slide_type in {"cover", "overview", "divider"} and not slide.get("title"):
                continue
            if slide_type == "statement" and not (slide.get("bigWord") or slide.get("title")):
                continue
            if slide_type == "contents" and not slide.get("items"):
                continue
            if slide_type in {"columns", "cards"} and not (slide.get("columns") or slide.get("cards")):
                continue
            if slide_type == "highlights" and not slide.get("lines"):
                continue
            if slide_type == "checklist" and not slide.get("items"):
                continue
            if slide_type == "quiz" and not (slide.get("quizQuestion") and slide.get("quizOptions")):
                continue

            slides.append(slide)

        if len(slides) < MIN_COURSE_SLIDES:
            return None
        if not has_checklist or not has_quiz:
            return None
        if not has_structured_cards:
            return None

        out: dict[str, Any] = {"courseTitle": course_title, "slides": slides}
        if subtitle:
            out["subtitle"] = subtitle
        return out

    def _sanitize_brand_guides_payload(self, raw: Any) -> Optional[dict[str, Any]]:
        if not isinstance(raw, dict):
            return None

        brand_raw = raw.get("brand")
        if isinstance(brand_raw, dict):
            brand_name = self._normalize_text(brand_raw.get("name"), 60) or "Creator Brand"
            brand_accent = self._normalize_text(brand_raw.get("accent"), 16) or "#FF6B00"
            nav_links_raw = brand_raw.get("navLinks")
            nav_links: list[str] = []
            if isinstance(nav_links_raw, list):
                for link in nav_links_raw[:5]:
                    txt = self._normalize_text(link, 40)
                    if txt:
                        nav_links.append(txt)
            year = self._normalize_text(brand_raw.get("year"), 12) or "2026"
            version = self._normalize_text(brand_raw.get("version"), 24) or "Version 1.0"
        else:
            brand_name = "Creator Brand"
            brand_accent = "#FF6B00"
            nav_links = ["Introduction", "Logo", "Elements"]
            year = "2026"
            version = "Version 1.0"

        slides_raw = raw.get("slides")
        if not isinstance(slides_raw, list):
            return None

        allowed_types = {
            "cover", "intro", "toc", "logo-grid", "clear-space",
            "logo-detail", "typography", "palette", "logo-misuse", "section",
        }
        type_aliases = {
            "title": "cover",
            "text-only": "intro",
            "text-image": "logo-detail",
            "cards": "logo-grid",
            "checklist": "logo-misuse",
            "quiz": "section",
        }

        slides: list[dict[str, Any]] = []
        has_toc = False
        has_palette = False
        has_governance = False

        for slide_raw in slides_raw[:MAX_COURSE_SLIDES]:
            if not isinstance(slide_raw, dict):
                continue
            raw_type = self._normalize_text(slide_raw.get("type"), 40).lower()
            slide_type = type_aliases.get(raw_type, raw_type)
            if slide_type not in allowed_types:
                if isinstance(slide_raw.get("swatches"), list):
                    slide_type = "palette"
                elif isinstance(slide_raw.get("rules"), list):
                    slide_type = "logo-misuse"
                elif isinstance(slide_raw.get("items"), list):
                    slide_type = "toc"
                elif self._normalize_text(slide_raw.get("clearBody"), 30):
                    slide_type = "clear-space"
                else:
                    slide_type = "intro"

            slide: dict[str, Any] = {"type": slide_type}
            for field, lim in (
                ("title", 140), ("body", 1200), ("eyebrow", 80),
                ("brandName", 140), ("tagline", 220), ("coverBg", 16),
                ("patternColor", 24), ("introBg", 16), ("tocTitle", 100),
                ("tocBg", 16), ("gridTitle", 100), ("gridSubtitle", 260),
                ("logoText", 80), ("clearTitle", 120), ("clearSubtitle", 180),
                ("clearBody", 1200), ("clearNote", 320), ("detailTitle", 120),
                ("detailBody", 900), ("typoTitle", 120), ("typefaceName", 100),
                ("typoBody", 900), ("displayChars", 20), ("displayColor", 16),
                ("paletteTitle", 100), ("paletteLead", 120), ("paletteBody", 600),
                ("misuseTitle", 120), ("misuseBody", 900), ("sectionBg", 16),
                ("sectionFg", 16),
            ):
                value = self._normalize_text(slide_raw.get(field), lim)
                if value:
                    slide[field] = value

            items_raw = slide_raw.get("items")
            if isinstance(items_raw, list):
                toc_items: list[dict[str, Any]] = []
                for idx, item in enumerate(items_raw[:10]):
                    if isinstance(item, dict):
                        number_raw = item.get("number", idx + 1)
                        label = self._normalize_text(item.get("label"), 80)
                    else:
                        number_raw = idx + 1
                        label = self._normalize_text(item, 80)
                    try:
                        number = int(number_raw)
                    except Exception:
                        number = idx + 1
                    if not label:
                        continue
                    toc_items.append({"number": max(1, number), "label": label})
                if toc_items:
                    slide["items"] = toc_items

            rules_raw = slide_raw.get("rules")
            if isinstance(rules_raw, list):
                rules: list[dict[str, Any]] = []
                for rule in rules_raw[:10]:
                    if isinstance(rule, dict):
                        r_type = self._normalize_text(rule.get("type"), 10).lower()
                        text = self._normalize_text(rule.get("text"), 260)
                    else:
                        r_type = "dont"
                        text = self._normalize_text(rule, 260)
                    if r_type not in {"do", "dont"}:
                        r_type = "dont"
                    if not text:
                        continue
                    rules.append({"type": r_type, "text": text})
                if rules:
                    slide["rules"] = rules

            swatches_raw = slide_raw.get("swatches")
            if isinstance(swatches_raw, list):
                swatches: list[dict[str, Any]] = []
                for sw in swatches_raw[:10]:
                    if not isinstance(sw, dict):
                        continue
                    name = self._normalize_text(sw.get("name"), 40)
                    hex_value = self._normalize_text(sw.get("hex"), 16)
                    if not name or not hex_value:
                        continue
                    sw_obj: dict[str, Any] = {"name": name, "hex": hex_value}
                    cmyk = self._normalize_text(sw.get("cmyk"), 40)
                    rgb = self._normalize_text(sw.get("rgb"), 40)
                    if cmyk:
                        sw_obj["cmyk"] = cmyk
                    if rgb:
                        sw_obj["rgb"] = rgb
                    try:
                        width = int(sw.get("width", 1))
                    except Exception:
                        width = 1
                    sw_obj["width"] = max(1, min(5, width))
                    swatches.append(sw_obj)
                if swatches:
                    slide["swatches"] = swatches

            if slide_type == "cover" and not (slide.get("brandName") or slide.get("title")):
                slide["brandName"] = "Brand Guidelines"
            if slide_type == "intro" and not slide.get("body"):
                slide["body"] = "This guide aligns visual identity for consistent creator content."
            if slide_type == "toc":
                if not slide.get("tocTitle"):
                    slide["tocTitle"] = "Table of Content"
                if not slide.get("items"):
                    slide["items"] = [
                        {"number": 1, "label": "Introduction"},
                        {"number": 2, "label": "Logo System"},
                        {"number": 3, "label": "Typography"},
                        {"number": 4, "label": "Color Palette"},
                    ]
                has_toc = True
            if slide_type == "palette":
                if not slide.get("swatches"):
                    slide["swatches"] = [
                        {"name": "Primary", "hex": brand_accent, "width": 3},
                        {"name": "Dark", "hex": "#111111", "width": 2},
                        {"name": "Light", "hex": "#F4F4F4", "width": 2},
                    ]
                has_palette = True
            if slide_type in {"logo-misuse", "clear-space"}:
                has_governance = True

            slides.append(slide)

        if len(slides) < MIN_COURSE_SLIDES:
            return None
        if not has_toc or not has_palette:
            return None
        if not has_governance:
            return None

        return {
            "brand": {
                "name": brand_name,
                "accent": brand_accent,
                "navLinks": nav_links or ["Introduction", "Logo", "Elements"],
                "year": year,
                "version": version,
            },
            "slides": slides,
        }

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



