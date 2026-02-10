from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
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
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

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


