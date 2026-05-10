from pydantic import BaseModel, Field, HttpUrl


class VideoIngestRequest(BaseModel):
    """Request to ingest a YouTube video and generate a study pack."""

    url: HttpUrl = Field(description="Public YouTube video URL to process")
