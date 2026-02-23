"""
Backfill unified analysis tables from legacy vector/premium tables.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional

repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, repo_root)

from backend.database import SessionLocal
from backend.models import (
    IntervalEmbedding,
    PremiumPerformanceInterval,
    PremiumPerformanceIntervalEmbedding,
    PremiumPsychologicalInterval,
    PremiumPsychologicalIntervalEmbedding,
    PremiumStructuralInterval,
    PremiumStructuralIntervalEmbedding,
    PremiumTranscriptInterval,
    PremiumTranscriptIntervalEmbedding,
    PremiumVerificationInterval,
    PremiumVerificationIntervalEmbedding,
    Project,
    SubVideoIntervalEmbedding,
    VideoInterval,
    VideoSubInterval,
)
from backend.services.unified_analysis_storage import (
    upsert_analysis_embedding,
    upsert_analysis_interval,
    upsert_analysis_record,
)


def _parse_embedding(raw: Optional[str]) -> list[float] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [float(v) for v in parsed]
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return None


def _row_payload(row: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for col in row.__table__.columns:
        value = getattr(row, col.name)
        payload[col.name] = value
    return payload


def run() -> None:
    db = SessionLocal()
    try:
        projects = db.query(Project).filter(Project.video_id.isnot(None)).all()
        total_records = 0

        for project in projects:
            interval_by_legacy_id: dict[int, int] = {}
            intervals = (
                db.query(VideoInterval)
                .filter(VideoInterval.video_id == project.video_id)
                .all()
            )
            for vi in intervals:
                unified = upsert_analysis_interval(
                    db,
                    project_id=project.id,
                    video_id=project.video_id,
                    granularity="interval",
                    interval_index=vi.interval_index,
                    sub_index=-1,
                    start_time_seconds=vi.start_time_seconds,
                    end_time_seconds=vi.end_time_seconds,
                )
                interval_by_legacy_id[vi.id] = unified.id

                ie = (
                    db.query(IntervalEmbedding)
                    .filter(IntervalEmbedding.interval_id == vi.id)
                    .first()
                )
                if ie and (ie.combined_interval_text or ie.embedding):
                    rec = upsert_analysis_record(
                        db,
                        project_id=project.id,
                        video_id=project.video_id,
                        interval_id=unified.id,
                        analysis_type="vector_interval_summary",
                        source_pass=None,
                        status="completed",
                        summary_text=ie.combined_interval_text,
                        payload={
                            "legacy_interval_embedding_id": ie.id,
                            "combined_interval_text": ie.combined_interval_text,
                        },
                    )
                    upsert_analysis_embedding(
                        db,
                        analysis_record_id=rec.id,
                        embedding=_parse_embedding(ie.embedding),
                    )
                    total_records += 1

            sub_rows = (
                db.query(VideoSubInterval, SubVideoIntervalEmbedding)
                .outerjoin(
                    SubVideoIntervalEmbedding,
                    SubVideoIntervalEmbedding.sub_interval_id == VideoSubInterval.id,
                )
                .filter(VideoSubInterval.video_id == project.video_id)
                .all()
            )
            for sub, emb in sub_rows:
                parent_unified_id = interval_by_legacy_id.get(sub.interval_id)
                unified_sub = upsert_analysis_interval(
                    db,
                    project_id=project.id,
                    video_id=project.video_id,
                    granularity="sub_interval",
                    interval_index=sub.interval.interval_index if sub.interval else -1,
                    sub_index=sub.sub_index,
                    start_time_seconds=sub.start_time_seconds,
                    end_time_seconds=sub.end_time_seconds,
                    parent_interval_id=parent_unified_id,
                )
                sub_payload = {
                    "legacy_sub_interval_id": sub.id,
                    "camera_frame": sub.camera_frame,
                    "environment_background": sub.environment_background,
                    "people_figures": sub.people_figures,
                    "objects_props": sub.objects_props,
                    "text_symbols": sub.text_symbols,
                    "motion_changes": sub.motion_changes,
                    "lighting_color": sub.lighting_color,
                    "audio_visible_indicators": sub.audio_visible_indicators,
                    "occlusions_limits": sub.occlusions_limits,
                    "raw_combined_text": sub.raw_combined_text,
                }
                rec = upsert_analysis_record(
                    db,
                    project_id=project.id,
                    video_id=project.video_id,
                    interval_id=unified_sub.id,
                    analysis_type="vision_raw",
                    source_pass=None,
                    status="completed",
                    summary_text=sub.raw_combined_text,
                    payload=sub_payload,
                )
                upsert_analysis_embedding(
                    db,
                    analysis_record_id=rec.id,
                    embedding=_parse_embedding(emb.embedding if emb else None),
                )
                total_records += 1

            premium_sources = [
                (
                    "premium_structural",
                    1,
                    PremiumStructuralInterval,
                    PremiumStructuralIntervalEmbedding,
                    PremiumStructuralIntervalEmbedding.structural_interval_id,
                ),
                (
                    "premium_psychological",
                    2,
                    PremiumPsychologicalInterval,
                    PremiumPsychologicalIntervalEmbedding,
                    PremiumPsychologicalIntervalEmbedding.psychological_interval_id,
                ),
                (
                    "premium_performance",
                    3,
                    PremiumPerformanceInterval,
                    PremiumPerformanceIntervalEmbedding,
                    PremiumPerformanceIntervalEmbedding.performance_interval_id,
                ),
                (
                    "premium_transcript",
                    4,
                    PremiumTranscriptInterval,
                    PremiumTranscriptIntervalEmbedding,
                    PremiumTranscriptIntervalEmbedding.transcript_interval_id,
                ),
                (
                    "premium_verification",
                    5,
                    PremiumVerificationInterval,
                    PremiumVerificationIntervalEmbedding,
                    PremiumVerificationIntervalEmbedding.verification_interval_id,
                ),
            ]

            for analysis_type, source_pass, interval_model, embedding_model, fk_column in premium_sources:
                rows = (
                    db.query(interval_model, embedding_model)
                    .outerjoin(embedding_model, fk_column == interval_model.id)
                    .filter(interval_model.project_id == project.id)
                    .all()
                )
                for interval_row, emb_row in rows:
                    unified_interval = upsert_analysis_interval(
                        db,
                        project_id=project.id,
                        video_id=project.video_id,
                        granularity="interval",
                        interval_index=interval_row.interval_index,
                        sub_index=-1,
                        start_time_seconds=interval_row.start_time_seconds,
                        end_time_seconds=interval_row.end_time_seconds,
                    )
                    rec = upsert_analysis_record(
                        db,
                        project_id=project.id,
                        video_id=project.video_id,
                        interval_id=unified_interval.id,
                        analysis_type=analysis_type,
                        source_pass=source_pass,
                        status="completed",
                        summary_text=(emb_row.combined_text if emb_row else None),
                        payload=_row_payload(interval_row),
                    )
                    upsert_analysis_embedding(
                        db,
                        analysis_record_id=rec.id,
                        embedding=_parse_embedding(emb_row.embedding if emb_row else None),
                    )
                    total_records += 1

            db.commit()

        print(f"Backfill completed. Upserted/updated records: {total_records}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
