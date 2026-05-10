from models.domain import StudyPack
from pydantic import BaseModel, Field


class VideoIngestResponse(BaseModel):
    """Returned on 202 when a video has been queued for background processing."""

    job_id: str = Field(
        description="Unique identifier for this background processing job"
    )
    video_id: str = Field(description="YouTube video ID derived from the submitted URL")


class VideoStudyPackResponse(BaseModel):
    """Returned on 200 when the study pack for a video is already available."""

    video_id: str = Field(description="YouTube video ID")
    study_pack: StudyPack = Field(
        description="Fully generated study pack including outline, summaries, and flashcards"
    )
