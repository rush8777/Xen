from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from ..models import AnalysisEmbedding, AnalysisInterval, AnalysisRecord


def _serialize_json(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return None


def _serialize_embedding(embedding: list[float] | None) -> str | None:
    if embedding is None:
        return None
    try:
        return json.dumps(embedding)
    except (TypeError, ValueError):
        return None


def upsert_analysis_interval(
    db: Session,
    *,
    project_id: int,
    video_id: int,
    granularity: str,
    interval_index: int = -1,
    sub_index: int = -1,
    start_time_seconds: int,
    end_time_seconds: int,
    parent_interval_id: int | None = None,
) -> AnalysisInterval:
    row = (
        db.query(AnalysisInterval)
        .filter(
            AnalysisInterval.project_id == project_id,
            AnalysisInterval.granularity == granularity,
            AnalysisInterval.interval_index == interval_index,
            AnalysisInterval.sub_index == sub_index,
        )
        .first()
    )
    if not row:
        row = AnalysisInterval(
            project_id=project_id,
            video_id=video_id,
            granularity=granularity,
            interval_index=interval_index,
            sub_index=sub_index,
            start_time_seconds=start_time_seconds,
            end_time_seconds=end_time_seconds,
            parent_interval_id=parent_interval_id,
        )
        db.add(row)
        db.flush()
        return row

    row.video_id = video_id
    row.start_time_seconds = start_time_seconds
    row.end_time_seconds = end_time_seconds
    row.parent_interval_id = parent_interval_id
    row.updated_at = datetime.utcnow()
    db.flush()
    return row


def upsert_analysis_record(
    db: Session,
    *,
    project_id: int,
    video_id: int,
    interval_id: int,
    analysis_type: str,
    source_pass: int | None = None,
    status: str = "completed",
    summary_text: str | None = None,
    payload: Any = None,
    confidence: float | None = None,
    schema_version: int = 1,
) -> AnalysisRecord:
    row = (
        db.query(AnalysisRecord)
        .filter(
            AnalysisRecord.project_id == project_id,
            AnalysisRecord.interval_id == interval_id,
            AnalysisRecord.analysis_type == analysis_type,
        )
        .first()
    )
    payload_json = _serialize_json(payload)
    if not row:
        row = AnalysisRecord(
            project_id=project_id,
            video_id=video_id,
            interval_id=interval_id,
            analysis_type=analysis_type,
            source_pass=source_pass,
            status=status,
            summary_text=summary_text,
            payload_json=payload_json,
            confidence=confidence,
            schema_version=schema_version,
        )
        db.add(row)
        db.flush()
        return row

    row.video_id = video_id
    row.source_pass = source_pass
    row.status = status
    row.summary_text = summary_text
    row.payload_json = payload_json
    row.confidence = confidence
    row.schema_version = schema_version
    row.updated_at = datetime.utcnow()
    db.flush()
    return row


def upsert_analysis_embedding(
    db: Session,
    *,
    analysis_record_id: int,
    embedding: Optional[list[float]],
    embedding_model: str = "gemini-embedding-001",
    embedding_dim: int = 3072,
) -> AnalysisEmbedding:
    row = (
        db.query(AnalysisEmbedding)
        .filter(AnalysisEmbedding.analysis_record_id == analysis_record_id)
        .first()
    )
    serialized_embedding = _serialize_embedding(embedding)
    now = datetime.utcnow()
    if not row:
        row = AnalysisEmbedding(
            analysis_record_id=analysis_record_id,
            embedding=serialized_embedding,
            embedding_model=embedding_model,
            embedding_dim=embedding_dim,
            embedded_at=now if serialized_embedding else None,
        )
        db.add(row)
        db.flush()
        return row

    row.embedding = serialized_embedding
    row.embedding_model = embedding_model
    row.embedding_dim = embedding_dim
    row.embedded_at = now if serialized_embedding else None
    row.updated_at = now
    db.flush()
    return row
