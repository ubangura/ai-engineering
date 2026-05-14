from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from models.domain import Flashcard, Summary
from models.requests.translate import TranslationRequest
from models.responses.translate import TranslationResponse
from sqlalchemy.orm import Session

from app.db import get_session
from app.db import models as orm
from app.rate_limit import RateLimitExceeded, check_and_increment
from app.sessions import get_session_id
from app.translate import translate_pack

router = APIRouter()


def _flatten_outline_titles(nodes: list[dict]) -> dict[str, str]:
    titles = {}
    for node in nodes:
        titles[node["id"]] = node["title"]
        if node.get("children"):
            titles.update(_flatten_outline_titles(node["children"]))
    return titles


@router.post("/api/translate")
async def translate(
    body: TranslationRequest,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> TranslationResponse:
    pack_row = session.get(orm.StudyPack, body.video_id)
    if pack_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    outline_titles = _flatten_outline_titles(pack_row.outline["nodes"])

    translation_row = session.get(
        orm.Translation, (body.video_id, body.target_language)
    )

    if translation_row:
        return TranslationResponse(
            video_id=body.video_id,
            target_language=body.target_language,
            summaries=[Summary(**summary) for summary in translation_row.summaries],
            flashcards=[
                Flashcard(**flashcard) for flashcard in translation_row.flashcards
            ],
            outline_titles=translation_row.outline_titles,
        )

    scope = f"cookie:{get_session_id(request)}"
    try:
        check_and_increment(session, "translate", scope)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                **exc.error.model_dump(),
                "retry_after_seconds": exc.retry_after_seconds,
            },
        )

    summaries = [Summary(**summary) for summary in pack_row.summaries]
    flashcards = [Flashcard(**flashcard) for flashcard in pack_row.flashcards]
    result = await translate_pack(
        summaries, flashcards, outline_titles, body.target_language, body.video_id
    )

    session.add(
        orm.Translation(
            video_id=body.video_id,
            language=body.target_language,
            outline_titles=result.outline_titles,
            summaries=[summary.model_dump() for summary in result.summaries],
            flashcards=[flashcard.model_dump() for flashcard in result.flashcards],
        )
    )
    session.commit()
    return result
