from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class VideoMetadata(BaseModel):
    """Raw metadata extracted from yt-dlp."""

    video_id: str = Field(description="YouTube video ID")
    title: str = Field(description="Video title")
    duration_seconds: int = Field(gt=0, description="Total duration in seconds")
    uploader: str = Field(description="Channel or uploader name")
    is_live: bool = Field(description="True if the video is currently a live stream")
    was_live: bool = Field(
        description="True if the video was a live stream that has ended"
    )
    availability: Literal["public", "unlisted"] = Field(
        description="Platform-reported availability status"
    )
    age_limit: int = Field(
        ge=0, description="Minimum age required to view; 0 means unrestricted"
    )
    categories: list[str] = Field(
        description="Platform-assigned categories (e.g. 'Music', 'Education')"
    )


class TranscriptSegment(BaseModel):
    """A timestamped chunk of text."""

    start_time: float = Field(ge=0.0, description="Start time in seconds")
    end_time: float = Field(gt=0.0, description="End time in seconds")
    text: str = Field(description="Spoken text in this segment")


class OutlineNode(BaseModel):
    """A single node in the hierarchical outline tree."""

    id: str = Field(
        description="Stable identifier used to anchor flashcards and citations"
    )
    title: str = Field(description="Human-readable section title")
    start_time: float = Field(ge=0.0, description="Start timestamp in seconds")
    end_time: float = Field(gt=0.0, description="End timestamp in seconds")
    level: Literal["chapter", "section", "topic"] = Field(
        description="Depth of this node in the outline hierarchy"
    )
    children: list["OutlineNode"] = Field(
        default_factory=list, description="Nested child nodes"
    )


OutlineNode.model_rebuild()


class Outline(BaseModel):
    """Structural analysis of a video produced by the Outline Agent."""

    video_id: str = Field(description="YouTube video ID this outline belongs to")
    nodes: list[OutlineNode] = Field(description="Top-level outline nodes")


class VideoAnalysis(BaseModel):
    """Structural outline for a videp plus content signals used to configure downstream agents."""

    outline: Outline
    inferred_category: Literal["stem", "humanities", "social", "other"] = Field(
        description="Content category inferred from the associated transcript"
    )
    is_lecture_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence that the video is an educational lecture (0 = definitely not, 1 = definitely yes)",
    )
    language_detected: str = Field(
        description="BCP-47 language code detected in the transcript (e.g. 'en', 'fr')"
    )
    recommended_temperature: float = Field(
        ge=0.0,
        le=1.0,
        description="Suggested sampling temperature for downstream agents based on content category",
    )


class Citation(BaseModel):
    """A verbatim excerpt from a transcript anchored to a timestamp range."""

    section_id: str = Field(
        description="ID of the OutlineNode this citation falls within"
    )
    start_time: float = Field(ge=0.0, description="Start timestamp in seconds")
    end_time: float = Field(gt=0.0, description="End timestamp in seconds")
    quote: str = Field(max_length=500, description="Verbatim transcript excerpt")


class Flashcard(BaseModel):
    """A single question-answer pair anchored to a section of a video."""

    question: str = Field(description="The question side of the flashcard")
    answer: str = Field(description="The answer side of the flashcard")
    section_id: str = Field(description="ID of the OutlineNode this flashcard covers")
    citations: list[Citation] = Field(
        description="Transcript citations supporting the answer"
    )


class Summary(BaseModel):
    """A prose summary of a video at a specific depth."""

    depth: Literal["ninety_seconds", "five_minutes", "full"] = Field(
        description="Summary length tier"
    )
    text: str = Field(description="Summary prose in English")


class StudyPack(BaseModel):
    """Complete study material (summaries and flashcards) for a video."""

    video_id: str = Field(description="YouTube video ID this study pack belongs to")
    outline: Outline = Field(
        description="Structural outline the study pack was generated from"
    )
    summaries: list[Summary] = Field(
        min_length=3,
        max_length=3,
        description="One summary per depth tier: ninety_seconds, five_minutes, full",
    )
    flashcards: list[Flashcard] = Field(
        min_length=8,
        max_length=20,
        description="8–20 flashcards scaled by video duration",
    )


class WebSource(BaseModel):
    """An external web result returned by the Q&A agent's web search tool."""

    url: HttpUrl = Field(description="Source URL")
    title: str = Field(description="Page title")
    snippet: str = Field(description="Relevant excerpt from the page")


class QAResponse(BaseModel):
    """The complete answer to a user question, including transcript and web citations."""

    answer: str = Field(
        description="Full answer text with inline [mm:ss] citation markers"
    )
    citations: list[Citation] = Field(
        description="Resolved transcript citations referenced in the answer"
    )
    web_sources: list[WebSource] = Field(
        default_factory=list, description="Web sources used, if any"
    )


class ErrorResponse(BaseModel):
    """Structured error returned by any endpoint on a non-2xx response."""

    code: Literal[
        "livestream",
        "private",
        "age_restricted",
        "audio_too_poor",
        "not_a_lecture",
        "rate_limited",
        "not_found",
        "internal_error",
    ] = Field(description="Error code")
    detail: str = Field(description="User-facing explanation of the error")
