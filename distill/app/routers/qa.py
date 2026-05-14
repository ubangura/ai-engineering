import json
from typing import Annotated

from agents.qa import run_qa
from anthropic.types import MessageParam
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from models.requests.qa import QARequest
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_session
from app.db import models as orm
from app.rate_limit import RateLimitExceeded, check_and_increment
from app.sessions import get_session_id
from app.sse import keepalive_stream

router = APIRouter()


@router.post("/api/qa")
async def ask_question(
    body: QARequest,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
):
    transcript_row = session.get(orm.Transcript, body.video_id)
    if transcript_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    session_id = get_session_id(request)
    scope = f"cookie:{session_id}"
    try:
        check_and_increment(session, "qa", scope)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                **exc.error.model_dump(),
                "retry_after_seconds": exc.retry_after_seconds,
            },
        )

    qa_row = session.get(orm.QASession, (body.video_id, session_id))
    history = _turns_to_history(qa_row.turns if qa_row else [])
    transcript_vtt = transcript_row.vtt_text

    return StreamingResponse(
        keepalive_stream(_qa_stream(body, session_id, transcript_vtt, history)),
        media_type="text/event-stream",
    )


def _turns_to_history(turns: list[dict]) -> list[MessageParam]:
    history: list[MessageParam] = []
    for turn in turns:
        history.append({"role": "user", "content": turn["question"]})
        history.append({"role": "assistant", "content": turn["answer"]})
    return history


async def _qa_stream(
    body: QARequest,
    session_id: str,
    transcript_vtt: str,
    history: list[MessageParam],
):
    answer_text = ""
    async for chunk in run_qa(
        transcript_vtt,
        history,
        body.question,
        body.video_id,
        session_id,
    ):
        yield chunk
        if chunk.startswith("event: done\n"):
            try:
                data = json.loads(chunk.split("\ndata: ", 1)[1].rstrip())
                answer_text = data.get("answer", "")
            except (IndexError, json.JSONDecodeError):
                pass

    _persist_turn(body.video_id, session_id, body.question, answer_text)


def _persist_turn(video_id: str, session_id: str, question: str, answer: str) -> None:
    new_turn = {"question": question, "answer": answer}
    with SessionLocal() as session:
        row = session.get(orm.QASession, (video_id, session_id))
        if row is None:
            session.add(
                orm.QASession(
                    video_id=video_id,
                    session_id=session_id,
                    turns=[new_turn],
                )
            )
        else:
            row.turns = row.turns + [new_turn]
        session.commit()
