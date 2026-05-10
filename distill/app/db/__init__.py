import os
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def initialize_database() -> None:
    from app.db import models as _  # noqa: F401 — registers all ORM models

    Base.metadata.create_all(bind=engine)
    _run_init_sql()


def _run_init_sql() -> None:
    sql_path = os.path.join(os.path.dirname(__file__), "init.sql")
    if not os.path.exists(sql_path):
        return
    with open(sql_path) as f:
        sql = f.read().strip()
    if not sql:
        return
    with engine.begin() as conn:
        conn.execute(text(sql))
