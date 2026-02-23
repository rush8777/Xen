from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    ForeignKey,
    UniqueConstraint,
    Date,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    oauth_connections = relationship(
        "OAuthConnection",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(255), nullable=False, unique=True, index=True)
    provider = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class OAuthConnection(Base):
    __tablename__ = "oauth_connections"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    provider = Column(String(50), nullable=False, index=True)
    provider_account_id = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)

    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    scopes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="oauth_connections")


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    platform = Column(String(50), nullable=False, index=True)

    channel_title = Column(String(255), nullable=True)
    channel_id = Column(String(255), nullable=True)
    channel_url = Column(String(255), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    url = Column(String(500), nullable=True)

    duration_seconds = Column(Integer, nullable=True)
    view_count = Column(Integer, nullable=True)
    like_count = Column(Integer, nullable=True)
    comment_count = Column(Integer, nullable=True)

    categories = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)

    published_at = Column(DateTime, nullable=True, index=True)
    cached_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    platform_videos = relationship(
        "PlatformVideo",
        cascade="all, delete-orphan",
    )
    user = relationship("User")


class PlatformVideo(Base):
    __tablename__ = "platform_videos"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "platform",
            "platform_video_id",
            name="uq_user_platform_video",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    platform = Column(String(50), nullable=False, index=True)
    platform_video_id = Column(String(255), nullable=False)
    etag = Column(String(255), nullable=True)
    extra = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    video = relationship("Video", back_populates="platform_videos")
    user = relationship("User")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True, index=True)
    priority = Column(String(50), nullable=True)  # Video, Image, Post
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    status = Column(String(50), default="draft", nullable=False)  # draft, in_progress, completed, etc.
    job_id = Column(String(255), nullable=True, index=True)  # Analysis job ID
    analysis_file_path = Column(String(1000), nullable=True)  # Path to analysis results file
    gemini_file_uri = Column(String(500), nullable=True)  # Gemini file URI reference
    # Cached video metadata for cost-optimized analysis
    gemini_cached_content_name = Column(String(255), nullable=True)
    video_duration_seconds = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Vector data generation status tracking
    vector_generation_status = Column(
        String(20), nullable=False, default="not_started"
    )  # not_started, pending, completed, failed
    vector_generation_started_at = Column(DateTime, nullable=True)
    vector_generation_completed_at = Column(DateTime, nullable=True)
    vector_generation_error = Column(Text, nullable=True)

    # Premium analysis status tracking
    premium_analysis_status = Column(
        String(20), nullable=False, default="not_started"
    )  # not_started, pending, completed, failed
    premium_analysis_started_at = Column(DateTime, nullable=True)
    premium_analysis_completed_at = Column(DateTime, nullable=True)
    premium_analysis_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User")
    video = relationship("Video")
    chats = relationship(
        "Chat",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=True)  # Facebook, Instagram, YouTube, etc.

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project", back_populates="chats")
    messages = relationship(
        "ChatMessage",
        back_populates="chat",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False, index=True)

    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chat = relationship("Chat", back_populates="messages")


class ProjectStatistics(Base):
    __tablename__ = "project_statistics"
    __table_args__ = (UniqueConstraint("project_id", name="uq_project_statistics_project"),)

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        unique=True,
    )

    stats_json = Column(Text, nullable=False, default="{}")
    status = Column(String(20), nullable=False, default="pending")  # not_started, pending, completed, failed
    version = Column(Integer, nullable=False, default=1)
    error = Column(Text, nullable=True)

    generated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")


class ProjectContentFeatures(Base):
    __tablename__ = "project_content_features"
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_project_content_features_project"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        unique=True,
    )

    status = Column(String(20), nullable=False, default="not_started")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)

    clips_status = Column(String(20), nullable=False, default="not_started")
    clips_progress = Column(Integer, nullable=False, default=0)
    clips_json = Column(Text, nullable=False, default="{}")
    clips_error = Column(Text, nullable=True)

    subtitles_status = Column(String(20), nullable=False, default="not_started")
    subtitles_progress = Column(Integer, nullable=False, default=0)
    subtitles_json = Column(Text, nullable=False, default="{}")
    subtitles_error = Column(Text, nullable=True)

    chapters_status = Column(String(20), nullable=False, default="not_started")
    chapters_progress = Column(Integer, nullable=False, default=0)
    chapters_json = Column(Text, nullable=False, default="{}")
    chapters_error = Column(Text, nullable=True)

    moments_status = Column(String(20), nullable=False, default="not_started")
    moments_progress = Column(Integer, nullable=False, default=0)
    moments_json = Column(Text, nullable=False, default="{}")
    moments_error = Column(Text, nullable=True)

    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")


class GeminiCache(Base):
    __tablename__ = "gemini_caches"
    __table_args__ = (
        UniqueConstraint(
            "video_hash",
            "prompt_template_key",
            "model",
            name="uq_gemini_cache_video_prompt_model",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    video_hash = Column(String(64), nullable=False, index=True)
    prompt_template_key = Column(String(255), nullable=False, index=True)
    model = Column(String(255), nullable=False, index=True)

    gemini_file_name = Column(String(255), nullable=True)
    gemini_file_uri = Column(String(500), nullable=True)
    cached_content_name = Column(String(255), nullable=False)

    ttl_seconds = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime, nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class ProjectOverview(Base):
    __tablename__ = "project_overviews"
    __table_args__ = (UniqueConstraint("project_id", name="uq_project_overview_project"),)

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        unique=True,
    )

    blog_markdown = Column(Text, nullable=False, default="")
    summary = Column(Text, nullable=False, default="")
    insights_json = Column(Text, nullable=False, default="{}")

    status = Column(String(20), nullable=False, default="pending")  # not_started, pending, completed, failed
    version = Column(Integer, nullable=False, default=1)
    error = Column(Text, nullable=True)

    generated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")


class ProjectPremiumAnalysis(Base):
    __tablename__ = "project_premium_analyses"
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_project_premium_analysis_project"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        unique=True,
    )

    pass_1_output = Column(Text, nullable=True)
    pass_2_output = Column(Text, nullable=True)
    pass_3_output = Column(Text, nullable=True)
    pass_4_output = Column(Text, nullable=True)
    pass_5_output = Column(Text, nullable=True)

    status = Column(String(20), nullable=False, default="pending")  # not_started, pending, completed, failed
    version = Column(Integer, nullable=False, default=1)
    error = Column(Text, nullable=True)

    generated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")


class PremiumIntervalAnalysis(Base):
    __tablename__ = "premium_interval_analyses"
    __table_args__ = (
        UniqueConstraint("project_id", "interval_id", name="uq_premium_interval_project_interval"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    interval_id = Column(Integer, ForeignKey("video_intervals.id"), nullable=False, index=True)
    interval_index = Column(Integer, nullable=False)
    start_time_seconds = Column(Integer, nullable=False)
    end_time_seconds = Column(Integer, nullable=False)

    pass_1_json = Column(Text, nullable=True)
    pass_2_json = Column(Text, nullable=True)
    pass_3_json = Column(Text, nullable=True)
    pass_4_json = Column(Text, nullable=True)
    pass_5_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")
    video = relationship("Video")
    interval = relationship("VideoInterval")


class PremiumStructuralInterval(Base):
    __tablename__ = "premium_structural_intervals"
    __table_args__ = (
        UniqueConstraint("project_id", "interval_id", name="uq_premium_structural_project_interval"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    interval_id = Column(Integer, ForeignKey("video_intervals.id"), nullable=False, index=True)
    interval_index = Column(Integer, nullable=False)
    start_time_seconds = Column(Integer, nullable=False)
    end_time_seconds = Column(Integer, nullable=False)

    hook_strength_score = Column(Integer, nullable=True)
    hook_strength_justification = Column(Text, nullable=True)

    stimulation_cuts_per_20s = Column(Integer, nullable=True)
    stimulation_camera_variation = Column(String(20), nullable=True)
    stimulation_motion_intensity = Column(String(20), nullable=True)
    stimulation_justification = Column(Text, nullable=True)

    escalation_intensity_increase = Column(Integer, nullable=True)  # 1/0
    escalation_stakes_raised = Column(Integer, nullable=True)  # 1/0
    escalation_justification = Column(Text, nullable=True)

    cognitive_information_rate = Column(String(20), nullable=True)
    cognitive_over_explanation_risk = Column(Integer, nullable=True)  # 1/0
    cognitive_justification = Column(Text, nullable=True)

    drop_risk_score_percent = Column(Integer, nullable=True)
    drop_risk_justification = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")
    video = relationship("Video")
    interval = relationship("VideoInterval")
    embedding_record = relationship(
        "PremiumStructuralIntervalEmbedding",
        back_populates="structural_interval",
        uselist=False,
        cascade="all, delete-orphan",
    )


class PremiumPsychologicalInterval(Base):
    __tablename__ = "premium_psychological_intervals"
    __table_args__ = (
        UniqueConstraint("project_id", "interval_id", name="uq_premium_psych_project_interval"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    interval_id = Column(Integer, ForeignKey("video_intervals.id"), nullable=False, index=True)
    interval_index = Column(Integer, nullable=False)
    start_time_seconds = Column(Integer, nullable=False)
    end_time_seconds = Column(Integer, nullable=False)

    primary_trigger_type = Column(String(50), nullable=True)
    primary_trigger_justification = Column(Text, nullable=True)

    trigger_intensity_score = Column(Integer, nullable=True)
    trigger_intensity_justification = Column(Text, nullable=True)

    emotional_arc_pattern_type = Column(String(50), nullable=True)
    emotional_arc_justification = Column(Text, nullable=True)

    attention_sustainability_type = Column(String(50), nullable=True)
    attention_sustainability_justification = Column(Text, nullable=True)

    viewer_momentum_score = Column(Integer, nullable=True)
    viewer_momentum_justification = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")
    video = relationship("Video")
    interval = relationship("VideoInterval")
    embedding_record = relationship(
        "PremiumPsychologicalIntervalEmbedding",
        back_populates="psychological_interval",
        uselist=False,
        cascade="all, delete-orphan",
    )


class PremiumPerformanceInterval(Base):
    __tablename__ = "premium_performance_intervals"
    __table_args__ = (
        UniqueConstraint("project_id", "interval_id", name="uq_premium_perf_project_interval"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    interval_id = Column(Integer, ForeignKey("video_intervals.id"), nullable=False, index=True)
    interval_index = Column(Integer, nullable=False)
    start_time_seconds = Column(Integer, nullable=False)
    end_time_seconds = Column(Integer, nullable=False)

    retention_strength_score = Column(Integer, nullable=True)
    retention_strength_justification = Column(Text, nullable=True)

    competitive_density_score = Column(Integer, nullable=True)
    competitive_density_justification = Column(Text, nullable=True)

    platform_tiktok_score = Column(Integer, nullable=True)
    platform_tiktok_justification = Column(Text, nullable=True)
    platform_instagram_reels_score = Column(Integer, nullable=True)
    platform_instagram_reels_justification = Column(Text, nullable=True)
    platform_youtube_shorts_score = Column(Integer, nullable=True)
    platform_youtube_shorts_justification = Column(Text, nullable=True)

    conversion_leverage_score = Column(Integer, nullable=True)
    conversion_leverage_justification = Column(Text, nullable=True)

    total_performance_index_score = Column(Integer, nullable=True)
    total_performance_index_justification = Column(Text, nullable=True)

    structural_weakness_priority_json = Column(Text, nullable=True)
    highest_leverage_target = Column(Text, nullable=True)
    highest_leverage_justification = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")
    video = relationship("Video")
    interval = relationship("VideoInterval")
    embedding_record = relationship(
        "PremiumPerformanceIntervalEmbedding",
        back_populates="performance_interval",
        uselist=False,
        cascade="all, delete-orphan",
    )


class PremiumTranscriptInterval(Base):
    __tablename__ = "premium_transcript_intervals"
    __table_args__ = (
        UniqueConstraint("project_id", "interval_id", name="uq_premium_transcript_project_interval"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    interval_id = Column(Integer, ForeignKey("video_intervals.id"), nullable=False, index=True)
    interval_index = Column(Integer, nullable=False)
    start_time_seconds = Column(Integer, nullable=False)
    end_time_seconds = Column(Integer, nullable=False)

    transcript_text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")
    video = relationship("Video")
    interval = relationship("VideoInterval")
    embedding_record = relationship(
        "PremiumTranscriptIntervalEmbedding",
        back_populates="transcript_interval",
        uselist=False,
        cascade="all, delete-orphan",
    )


class PremiumVerificationInterval(Base):
    __tablename__ = "premium_verification_intervals"
    __table_args__ = (
        UniqueConstraint("project_id", "interval_id", name="uq_premium_verification_project_interval"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    interval_id = Column(Integer, ForeignKey("video_intervals.id"), nullable=False, index=True)
    interval_index = Column(Integer, nullable=False)
    start_time_seconds = Column(Integer, nullable=False)
    end_time_seconds = Column(Integer, nullable=False)

    question_type = Column(String(100), nullable=True)
    timestamp_reference = Column(String(50), nullable=True)
    visual_evidence_summary = Column(Text, nullable=True)
    verification_status = Column(String(50), nullable=True)
    answer = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")
    video = relationship("Video")
    interval = relationship("VideoInterval")
    embedding_record = relationship(
        "PremiumVerificationIntervalEmbedding",
        back_populates="verification_interval",
        uselist=False,
        cascade="all, delete-orphan",
    )


class PremiumStructuralIntervalEmbedding(Base):
    __tablename__ = "premium_structural_interval_embeddings"

    structural_interval_id = Column(
        Integer,
        ForeignKey("premium_structural_intervals.id"),
        primary_key=True,
    )
    combined_text = Column(Text, nullable=True)
    embedding = Column(Text, nullable=True)  # JSON list of floats for vector
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    structural_interval = relationship(
        "PremiumStructuralInterval",
        back_populates="embedding_record",
    )


class PremiumPsychologicalIntervalEmbedding(Base):
    __tablename__ = "premium_psychological_interval_embeddings"

    psychological_interval_id = Column(
        Integer,
        ForeignKey("premium_psychological_intervals.id"),
        primary_key=True,
    )
    combined_text = Column(Text, nullable=True)
    embedding = Column(Text, nullable=True)  # JSON list of floats for vector
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    psychological_interval = relationship(
        "PremiumPsychologicalInterval",
        back_populates="embedding_record",
    )


class PremiumPerformanceIntervalEmbedding(Base):
    __tablename__ = "premium_performance_interval_embeddings"

    performance_interval_id = Column(
        Integer,
        ForeignKey("premium_performance_intervals.id"),
        primary_key=True,
    )
    combined_text = Column(Text, nullable=True)
    embedding = Column(Text, nullable=True)  # JSON list of floats for vector
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    performance_interval = relationship(
        "PremiumPerformanceInterval",
        back_populates="embedding_record",
    )


class PremiumTranscriptIntervalEmbedding(Base):
    __tablename__ = "premium_transcript_interval_embeddings"

    transcript_interval_id = Column(
        Integer,
        ForeignKey("premium_transcript_intervals.id"),
        primary_key=True,
    )
    combined_text = Column(Text, nullable=True)
    embedding = Column(Text, nullable=True)  # JSON list of floats for vector
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    transcript_interval = relationship(
        "PremiumTranscriptInterval",
        back_populates="embedding_record",
    )


class PremiumVerificationIntervalEmbedding(Base):
    __tablename__ = "premium_verification_interval_embeddings"

    verification_interval_id = Column(
        Integer,
        ForeignKey("premium_verification_intervals.id"),
        primary_key=True,
    )
    combined_text = Column(Text, nullable=True)
    embedding = Column(Text, nullable=True)  # JSON list of floats for vector
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    verification_interval = relationship(
        "PremiumVerificationInterval",
        back_populates="embedding_record",
    )


class VideoInterval(Base):
    __tablename__ = "video_intervals"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    interval_index = Column(Integer, nullable=False)
    start_time_seconds = Column(Integer, nullable=False)
    end_time_seconds = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("video_id", "interval_index", name="uq_video_interval_index"),)

    video = relationship("Video")


class VideoSubInterval(Base):
    __tablename__ = "video_sub_intervals"

    id = Column(Integer, primary_key=True, index=True)
    interval_id = Column(Integer, ForeignKey("video_intervals.id"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)

    sub_index = Column(Integer, nullable=False)
    start_time_seconds = Column(Integer, nullable=False)
    end_time_seconds = Column(Integer, nullable=False)

    camera_frame = Column(Text, nullable=True)
    environment_background = Column(Text, nullable=True)
    people_figures = Column(Text, nullable=True)
    objects_props = Column(Text, nullable=True)
    text_symbols = Column(Text, nullable=True)
    motion_changes = Column(Text, nullable=True)
    lighting_color = Column(Text, nullable=True)
    audio_visible_indicators = Column(Text, nullable=True)
    occlusions_limits = Column(Text, nullable=True)

    raw_combined_text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("video_id", "start_time_seconds", name="uq_video_sub_interval_time"),)

    interval = relationship("VideoInterval")
    video = relationship("Video")
    embedding_record = relationship(
        "SubVideoIntervalEmbedding",
        back_populates="sub_interval",
        uselist=False,
        cascade="all, delete-orphan",
    )


class SubVideoIntervalEmbedding(Base):
    __tablename__ = "sub_video_interval_embeddings"

    sub_interval_id = Column(
        Integer,
        ForeignKey("video_sub_intervals.id"),
        primary_key=True,
    )
    embedding = Column(Text, nullable=True)  # JSON list of floats for vector
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    sub_interval = relationship("VideoSubInterval", back_populates="embedding_record")


class IntervalEmbedding(Base):
    __tablename__ = "interval_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    interval_id = Column(Integer, ForeignKey("video_intervals.id"), nullable=False, index=True)
    combined_interval_text = Column(Text, nullable=True)
    embedding = Column(Text, nullable=True)  # JSON list of floats for vector
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    video = relationship("Video")
    interval = relationship("VideoInterval")


class AnalysisInterval(Base):
    __tablename__ = "analysis_intervals"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "granularity",
            "interval_index",
            "sub_index",
            name="uq_analysis_interval_slot",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    parent_interval_id = Column(
        Integer,
        ForeignKey("analysis_intervals.id"),
        nullable=True,
        index=True,
    )
    granularity = Column(String(32), nullable=False, index=True)  # interval | sub_interval
    interval_index = Column(Integer, nullable=False, default=-1)
    sub_index = Column(Integer, nullable=False, default=-1)
    start_time_seconds = Column(Integer, nullable=False, index=True)
    end_time_seconds = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")
    video = relationship("Video")
    parent_interval = relationship(
        "AnalysisInterval",
        remote_side=[id],
        backref="child_intervals",
    )


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "interval_id",
            "analysis_type",
            name="uq_analysis_record_scope",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    interval_id = Column(
        Integer,
        ForeignKey("analysis_intervals.id"),
        nullable=False,
        index=True,
    )
    analysis_type = Column(String(64), nullable=False, index=True)
    source_pass = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="completed", index=True)
    summary_text = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    schema_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")
    video = relationship("Video")
    interval = relationship("AnalysisInterval")
    embedding_record = relationship(
        "AnalysisEmbedding",
        back_populates="analysis_record",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AnalysisEmbedding(Base):
    __tablename__ = "analysis_embeddings"

    analysis_record_id = Column(
        Integer,
        ForeignKey("analysis_records.id"),
        primary_key=True,
    )
    embedding = Column(Text, nullable=True)  # JSON list of floats for vector
    embedding_model = Column(String(64), nullable=False, default="gemini-embedding-001")
    embedding_dim = Column(Integer, nullable=False, default=3072)
    embedded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    analysis_record = relationship(
        "AnalysisRecord",
        back_populates="embedding_record",
    )


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    run_type = Column(String(32), nullable=False, index=True)  # vector | premium | full_refresh
    status = Column(String(20), nullable=False, index=True)  # pending | running | completed | failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")
