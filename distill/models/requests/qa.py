from pydantic import BaseModel, Field


class QARequest(BaseModel):
    """Request to ask a question about a previously ingested video."""

    video_id: str = Field(description="YouTube video ID of the ingested video")
    question: str = Field(
        min_length=1, description="Natural language question about the video content"
    )
    session_id: str | None = Field(
        default=None,
        description="Session cookie value for conversation history continuity; omit to start a new session",
    )
