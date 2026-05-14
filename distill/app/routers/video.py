import logging
import uuid
from typing import Annotated

from agents.outline import run_outline
from agents.study_pack import run_study_pack
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from models.domain import Flashcard, Outline, StudyPack, Summary
from models.requests.video import VideoIngestRequest
from models.responses.video import VideoIngestResponse, VideoStudyPackResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_session
from app.db import models as orm
from app.rate_limit import RateLimitExceeded, check_and_increment
from app.sessions import get_session_id
from app.sse import keepalive_stream, sse_event
from app.transcript.fetch import fetch_transcript
from app.transcript.gate import GateRejection, run_gate

router = APIRouter()
sse_router = APIRouter()
logger = logging.getLogger(__name__)


def _youtube_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def _study_pack_from_db(pack_row: orm.StudyPack) -> StudyPack:
    return StudyPack(
        video_id=pack_row.video_id,
        outline=Outline.model_validate(pack_row.outline),
        summaries=[Summary(**summary) for summary in pack_row.summaries],
        flashcards=[Flashcard(**flashcard) for flashcard in pack_row.flashcards],
    )


def _update_job_status(job_id: str, status: str, error_code: str | None = None) -> None:
    with SessionLocal() as session:
        job = session.get(orm.Job, uuid.UUID(job_id))
        if job:
            job.status = status
            if error_code is not None:
                job.error_code = error_code
            session.commit()


@router.get("/api/health")
async def health():
    return {"status": "ok"}


@router.post("/api/video")
async def submit_video(
    body: VideoIngestRequest,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
) -> VideoIngestResponse | VideoStudyPackResponse:
    try:
        metadata = await run_gate(str(body.url))
    except GateRejection as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.error.model_dump(),
        )

    video_id = metadata.video_id

    pack_row = session.get(orm.StudyPack, video_id)
    if pack_row:
        study_pack = _study_pack_from_db(pack_row)
        return VideoStudyPackResponse(video_id=video_id, study_pack=study_pack)

    scope = f"cookie:{get_session_id(request)}"
    try:
        check_and_increment(session, "video", scope)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                **exc.error.model_dump(),
                "retry_after_seconds": exc.retry_after_seconds,
            },
        )

    video = session.get(orm.Video, video_id)
    if video is None:
        video = orm.Video(
            video_id=video_id,
            title=metadata.title,
            duration_seconds=metadata.duration_seconds,
            uploader=metadata.uploader,
            metadata_=metadata.model_dump(),
        )
        session.add(video)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            video = session.get(orm.Video, video_id)
            if not video:
                raise

    job_id = str(uuid.uuid4())
    session.add(orm.Job(job_id=uuid.UUID(job_id), video_id=video_id))
    session.commit()

    response.status_code = status.HTTP_202_ACCEPTED
    return VideoIngestResponse(job_id=job_id, video_id=video_id)


@router.get("/api/video/{video_id}")
async def get_video(
    video_id: str,
    session: Annotated[Session, Depends(get_session)],
):
    pack_row = session.get(orm.StudyPack, video_id)
    if pack_row:
        study_pack = _study_pack_from_db(pack_row)
        return VideoStudyPackResponse(video_id=video_id, study_pack=study_pack)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")


@sse_router.get("/sse/video/{job_id}")
async def sse_video(job_id: str):
    return StreamingResponse(
        keepalive_stream(_pipeline_stream(job_id)),
        media_type="text/event-stream",
    )


async def _pipeline_stream(job_id: str):
    with SessionLocal() as session:
        job = session.get(orm.Job, uuid.UUID(job_id))
        if job is None:
            yield sse_event("error", {"code": "not_found", "detail": "Job not found"})
            return
        video_id = job.video_id
        status = job.status

    if status == "done":
        with SessionLocal() as session:
            pack_row = session.get(orm.StudyPack, video_id)
        if pack_row:
            study_pack = _study_pack_from_db(pack_row)
            yield sse_event("study-pack-done", {"study_pack": study_pack.model_dump()})
        yield sse_event("done", {"video_id": video_id})
        return

    if status == "error":
        with SessionLocal() as session:
            job = session.get(orm.Job, uuid.UUID(job_id))
            code = (job.error_code or "internal_error") if job else "internal_error"
        yield sse_event("error", {"code": code, "detail": "Processing failed"})
        return

    _update_job_status(job_id, "running")

    try:
        with SessionLocal() as session:
            video_row = session.get(orm.Video, video_id)
            title = video_row.title if video_row else ""
            duration = video_row.duration_seconds if video_row else 0
            categories = video_row.metadata_.get("categories", []) if video_row else []

        yield sse_event(
            "metadata-gate-pass",
            {
                "title": title,
                "duration": duration,
                "category": categories[0] if categories else None,
            },
        )

        with SessionLocal() as session:
            transcript_row = session.get(orm.Transcript, video_id)

        if transcript_row:
            vtt_text = transcript_row.vtt_text
        else:
            result = await fetch_transcript(video_id, _youtube_url(video_id))
            with SessionLocal() as session:
                session.add(
                    orm.Transcript(
                        video_id=video_id,
                        source=result.source,
                        vtt_text=result.vtt_text,
                        segments=[segment.model_dump() for segment in result.segments],
                        mean_confidence=result.mean_confidence,
                    )
                )
                session.commit()
            yield sse_event("transcript-source", {"source": result.source})
            yield sse_event(
                "transcript-fetched",
                {
                    "segment_count": len(result.segments),
                    "mean_confidence": result.mean_confidence,
                },
            )
            vtt_text = result.vtt_text

        with SessionLocal() as session:
            pack_row = session.get(orm.StudyPack, video_id)

        if pack_row:
            study_pack = _study_pack_from_db(pack_row)
            yield sse_event("outline-done", {"outline": pack_row.outline})
        else:
            analysis = await run_outline(vtt_text, video_id, job_id)
            yield sse_event("outline-done", {"outline": analysis.outline.model_dump()})
            study_pack = await run_study_pack(vtt_text, analysis, video_id, job_id)

            with SessionLocal() as session:
                session.add(
                    orm.StudyPack(
                        video_id=video_id,
                        category=analysis.inferred_category,
                        outline=analysis.outline.model_dump(),
                        summaries=[
                            summary.model_dump() for summary in study_pack.summaries
                        ],
                        flashcards=[
                            flashcard.model_dump()
                            for flashcard in study_pack.flashcards
                        ],
                    )
                )
                session.commit()

        yield sse_event("study-pack-done", {"study_pack": study_pack.model_dump()})

        _update_job_status(job_id, "done")
        yield sse_event("done", {"video_id": video_id})

    except GateRejection as exc:
        yield sse_event("error", exc.error.model_dump())
        _update_job_status(job_id, "error", exc.error.code)

    except Exception:
        logger.exception(
            "pipeline_error", extra={"job_id": job_id, "video_id": video_id}
        )
        yield sse_event(
            "error",
            {"code": "internal_error", "detail": "An unexpected error occurred"},
        )
        _update_job_status(job_id, "error", "internal_error")
