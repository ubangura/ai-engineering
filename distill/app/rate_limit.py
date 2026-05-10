from datetime import datetime, timedelta, timezone

from models.domain import ErrorResponse
from sqlalchemy.orm import Session

from app.db.models import RateLimit

_LIMITS = {
    "video": 5,
    "qa": 30,
    "translate": 3,
}


class RateLimitExceeded(Exception):
    def __init__(self, error: ErrorResponse):
        self.error = error
        super().__init__(error.code)


def _window_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(minute=0, second=0, microsecond=0)


def check_and_increment(
    session: Session,
    bucket: str,
    scope: str,
) -> None:
    window = _window_start()
    limit = _LIMITS[bucket]

    row = (
        session.query(RateLimit)
        .filter_by(scope=scope, bucket=bucket, window_start=window)
        .with_for_update()
        .first()
    )

    if row is None:
        row = RateLimit(scope=scope, bucket=bucket, window_start=window, count=0)
        session.add(row)

    if row.count >= limit:
        raise RateLimitExceeded(
            ErrorResponse(
                code="rate_limited",
                detail=_rate_limit_message(bucket, limit),
            )
        )

    row.count += 1
    session.commit()


def _rate_limit_message(bucket: str, limit: int) -> str:
    messages = {
        "video": f"You can process up to {limit} new videos per hour. Please wait until {_time_of_reset()}.",
        "qa": f"This conversation has reached {limit} Q&A turns for this hour. Please wait until {_time_of_reset()}.",
        "translate": f"Up to {limit} language translations per video are supported.",
    }
    return messages.get(bucket, "Rate limit reached. Please try again later.")


def _time_of_reset() -> str:
    now = datetime.now(timezone.utc)
    next_hour = now.replace(minute=0, second=0, microsecond=0)

    next_hour += timedelta(hours=1)
    return next_hour.strftime("%H:%M:%S")
