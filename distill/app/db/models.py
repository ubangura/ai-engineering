import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Video(Base):
    __tablename__ = "videos"
    __table_args__ = (CheckConstraint("duration_seconds > 0"),)

    video_id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    uploader: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Transcript(Base):
    __tablename__ = "transcripts"
    __table_args__ = (CheckConstraint("source IN ('youtube','deepgram')"),)

    video_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("videos.video_id", ondelete="CASCADE"),
        primary_key=True,
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    vtt_text: Mapped[str] = mapped_column(Text, nullable=False)
    segments: Mapped[list] = mapped_column(JSONB, nullable=False)
    mean_confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Outline(Base):
    __tablename__ = "outlines"
    __table_args__ = (
        CheckConstraint("category IN ('stem','humanities','social','other')"),
        CheckConstraint("recommended_temperature BETWEEN 0.0 AND 1.0"),
        CheckConstraint("is_lecture_confidence BETWEEN 0.0 AND 1.0"),
    )

    video_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("videos.video_id", ondelete="CASCADE"),
        primary_key=True,
    )
    outline: Mapped[dict] = mapped_column(JSONB, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_temperature: Mapped[float] = mapped_column(Float, nullable=False)
    is_lecture_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class StudyPack(Base):
    __tablename__ = "study_packs"

    video_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("videos.video_id", ondelete="CASCADE"),
        primary_key=True,
    )
    summaries: Mapped[list] = mapped_column(JSONB, nullable=False)
    flashcards: Mapped[list] = mapped_column(JSONB, nullable=False)
    generation_temperature: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Translation(Base):
    __tablename__ = "translations"

    video_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("videos.video_id", ondelete="CASCADE"),
        primary_key=True,
    )
    language: Mapped[str] = mapped_column(Text, primary_key=True)
    summaries: Mapped[list] = mapped_column(JSONB, nullable=False)
    flashcards: Mapped[list] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class QASession(Base):
    __tablename__ = "qa_sessions"

    video_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("videos.video_id", ondelete="CASCADE"),
        primary_key=True,
    )
    session_id: Mapped[str] = mapped_column(Text, primary_key=True)
    turns: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"), onupdate=_now
    )


class RateLimit(Base):
    __tablename__ = "rate_limits"
    __table_args__ = (
        CheckConstraint("bucket IN ('video','qa','translate')"),
        CheckConstraint("count >= 0"),
    )

    scope: Mapped[str] = mapped_column(Text, primary_key=True)
    bucket: Mapped[str] = mapped_column(Text, primary_key=True)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True
    )
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_video_id", "video_id"),
        CheckConstraint("status IN ('queued','running','done','error')"),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    video_id: Mapped[str] = mapped_column(
        Text, ForeignKey("videos.video_id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, default="queued")
    error_code: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"), onupdate=_now
    )
