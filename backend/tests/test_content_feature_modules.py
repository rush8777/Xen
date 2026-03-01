from __future__ import annotations

import asyncio

from backend.services.content_features.constants import FeatureGenerationContext
from backend.services.content_features.features.chapters_feature import generate_chapters_payload
from backend.services.content_features.features.clips_feature import generate_clips_payload
from backend.services.content_features.features.moments_feature import generate_moments_payload
from backend.services.content_features.features.subtitles_feature import generate_subtitles_payload
from backend.services.content_features.parsing import parse_json_object


class _FakeClient:
    def __init__(self, payload):
        self._payload = payload

    async def generate_json(self, *, cached_content_name: str, prompt: str, feature_id: str):
        return self._payload


def _context() -> FeatureGenerationContext:
    return FeatureGenerationContext(
        project_id=1,
        project_name="Demo",
        video_url="https://example.com/video",
        duration_seconds=120,
        cached_content_name="cachedContents/demo",
        overview_summary="Overview text",
    )


def test_parse_json_object_handles_code_fences():
    parsed = parse_json_object("```json\n{\"clips\": []}\n```")
    assert parsed == {"clips": []}


def test_clips_payload_normalizes_key_moment_schema_and_dedupes_overlap():
    payload = {
        "key_moments": [
            {
                "id": "moment_custom",
                "title": "Breakthrough",
                "category": "critical_insight",
                "start_time_seconds": -4,
                "end_time_seconds": 10,
                "duration_seconds": 12,
                "justification": "This moment reframes the problem with concrete evidence and changes what the audience should prioritize next.",
                "impact_level": "high",
                "context": "After setup",
                "key_quote": "We were solving the wrong problem.",
            },
            {
                "id": "moment_overlap",
                "title": "Overlap duplicate",
                "category": "decision_point",
                "start_time_seconds": 2,
                "end_time_seconds": 18,
                "duration_seconds": 16,
                "justification": "This line sounds strong but is overlapping a lot with the prior one and should be dropped by overlap filtering.",
                "impact_level": "medium",
                "context": "Same area",
                "key_quote": "Duplicate",
            },
            {
                "id": "moment_invalid",
                "title": "",
                "category": "random_category",
                "start_time_seconds": 75,
                "end_time_seconds": 80,
                "duration_seconds": 5,
                "justification": "important moment",
                "impact_level": "unknown",
            },
        ]
    }
    out = asyncio.run(generate_clips_payload(_context(), _FakeClient(payload)))
    assert len(out["key_moments"]) == 1
    m = out["key_moments"][0]
    assert m["id"] == "moment_custom"
    assert m["category"] == "critical_insight"
    assert m["impact_level"] == "high"
    assert m["start_time_seconds"] == 0
    assert 15 <= m["duration_seconds"] <= 90
    assert out["clips"][0]["id"] == "moment_custom"
    assert out["clips"][0]["justification"] == m["justification"]


def test_subtitles_payload_formats_lines_and_monotonic_timing():
    payload = {
        "segments": [
            {
                "start_time_seconds": 0,
                "end_time_seconds": 3,
                "text": "This is a test subtitle segment that should be wrapped.",
                "lines": [],
            },
            {
                "start_time_seconds": 1,
                "end_time_seconds": 4,
                "text": "Second segment",
            },
        ]
    }
    out = asyncio.run(generate_subtitles_payload(_context(), _FakeClient(payload)))
    assert out["segments"][0]["start_time_seconds"] == 0
    assert out["segments"][1]["start_time_seconds"] >= out["segments"][0]["end_time_seconds"]
    assert len(out["segments"][0]["lines"]) <= 2


def test_moments_payload_category_is_normalized():
    payload = {
        "moments": [
            {
                "id": "m1",
                "label": "Moment",
                "category": "random",
                "start_time_seconds": 10,
                "end_time_seconds": 20,
                "importance_score": 88,
                "rationale": "Reason",
            }
        ]
    }
    out = asyncio.run(generate_moments_payload(_context(), _FakeClient(payload)))
    assert out["moments"][0]["category"] == "informative"


def test_chapters_payload_normalizes_hierarchy_and_additive_fields():
    payload = {
        "totalChapters": 3,
        "chapters": [
            {
                "id": "c1",
                "title": "Opening Proof Arc",
                "start_time_seconds": -12,
                "end_time_seconds": 48,
                "summary": "The presenter frames the core promise, previews the outcome, and immediately anchors credibility through concrete setup details and practical constraints.",
                "psychological_intent": "deliver_proof",
                "chapter_type": "hook",
                "subchapters": [
                    {
                        "id": "s1",
                        "title": "Framing",
                        "start_time_seconds": 1,
                        "end_time_seconds": 18,
                        "summary": "The setup defines the claim boundaries and gives enough detail for the audience to understand what evidence should appear next in the sequence.",
                    },
                    {
                        "id": "s2",
                        "title": "Evidence cue",
                        "start_time_seconds": 18,
                        "end_time_seconds": 38,
                        "summary": "The speaker introduces proof signals and begins transitioning toward the first concrete demonstration while preserving narrative momentum.",
                    },
                ],
            },
            {
                "id": "c2",
                "title": "Compressed section",
                "start_time_seconds": 48,
                "end_time_seconds": 90,
                "summary": "A focused segment that moves quickly through supporting points while tightening the argument.",
                "psychological_intent": "unknown_intent",
                "chapter_type": "not_a_type",
                "subchapters": [],
            },
        ],
    }

    out = asyncio.run(generate_chapters_payload(_context(), _FakeClient(payload)))
    assert "totalChapters" in out
    assert "chapters" in out
    assert out["totalChapters"] > 0
    assert len(out["chapters"]) == 2

    first = out["chapters"][0]
    assert first["id"] == "c1"
    assert first["start_time_seconds"] == 0
    assert first["psychological_intent"] == "deliver_proof"
    assert first["chapter_type"] == "Hook"
    assert isinstance(first["subchapters"], list)
    assert len(first["subchapters"]) >= 2
    assert first["subchapters"][0]["start_time_seconds"] >= first["start_time_seconds"]
    assert first["subchapters"][0]["end_time_seconds"] <= first["end_time_seconds"]

    second = out["chapters"][1]
    assert second["psychological_intent"] == "other"
    assert second["chapter_type"] == "Education"
    assert len(second["subchapters"]) >= 2
