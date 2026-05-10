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
        description="Summaries translated into target_language; section_anchors and depth must match the source exactly"
    )
    flashcards: list[Flashcard] = Field(
        description="Flashcards translated into target_language; section_id, start_ts, and end_ts must match the source exactly"
    )
