from models.domain import Flashcard, Summary
from pydantic import BaseModel, Field


class TranslationResponse(BaseModel):
    """Translated study pack content in the requested language."""

    video_id: str = Field(
        description="YouTube video ID whose study pack was translated"
    )
    target_language: str = Field(
        description="BCP-47 language code of the translation (e.g. 'fr', 'zh-CN')"
    )
    summaries: list[Summary] = Field(
        description="Summaries translated into target_language; depth must match the source exactly"
    )
    flashcards: list[Flashcard] = Field(
        description="Flashcards translated into target_language; section_id, start_time, and end_time must match the source exactly"
    )
    outline_titles: dict[str, str] = Field(
        description="Flat mapping of outline node ID to translated title; all node IDs from the source outline must be present"
    )
