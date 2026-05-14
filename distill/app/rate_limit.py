from datetime import datetime, timedelta, timezone
from typing import Literal

from models.domain import ErrorResponse
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.models import RateLimit

_LIMITS = {
    "video": 5,
    "qa": 30,
    "translate": 3,
}


class RateLimitExceeded(Exception):
    def __init__(self, error: ErrorResponse, retry_after_seconds: int):
        self.error = error
        self.retry_after_seconds = retry_after_seconds
        super().__init__(error.code)


def _window_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(minute=0, second=0, microsecond=0)


def check_and_increment(
    session: Session, bucket: Literal["video", "qa", "translate"], scope: str
) -> None:
    window = _window_start()
    limit = _LIMITS[bucket]

    stmt = (
        pg_insert(RateLimit)
        .values(scope=scope, bucket=bucket, window_start=window, count=1)
        .on_conflict_do_update(
            index_elements=["scope", "bucket", "window_start"],
            set_={"count": RateLimit.count + 1},
        )
        .returning(RateLimit.count)
    )
    new_count = session.execute(stmt).scalar_one()

    if new_count > limit:
        session.rollback()
        retry_after = _seconds_until_reset()
        raise RateLimitExceeded(
            ErrorResponse(
                code="rate_limited",
                detail=_rate_limit_message(bucket, limit),
            ),
            retry_after_seconds=retry_after,
        )

    session.commit()


def _rate_limit_message(bucket: str, limit: int) -> str:
    messages = {
        "video": f"You can process up to {limit} new videos per hour. Please wait until {_time_of_reset()}.",
        "qa": f"This conversation has reached {limit} Q&A turns for this hour. Please wait until {_time_of_reset()}.",
        "translate": f"You can do {limit} translations per hour. Please wait until {_time_of_reset()}.",
    }
    return messages.get(bucket, "Rate limit reached. Please try again later.")


def _seconds_until_reset() -> int:
    now = datetime.now(timezone.utc)
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return int((next_hour - now).total_seconds())


def _time_of_reset() -> str:
    now = datetime.now(timezone.utc)
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return next_hour.strftime("%H:%M:%S")
