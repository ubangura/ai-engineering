from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    """Request to translate a study pack into a target language."""

    video_id: str = Field(
        description="YouTube video ID whose study pack should be translated"
    )
    target_language: str = Field(
        min_length=2,
        max_length=10,
        description="BCP-47 language code for the target language (e.g. 'fr', 'zh-CN')",
    )
