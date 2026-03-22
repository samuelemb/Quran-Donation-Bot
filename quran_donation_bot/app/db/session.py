from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from quran_donation_bot.app.core.config import get_settings


settings = get_settings()
is_neon_pooler = "neon.tech" in settings.database_url or "-pooler." in settings.database_url
engine = create_engine(
    settings.database_url,
    pool_pre_ping=not is_neon_pooler,
    poolclass=NullPool if is_neon_pooler else None,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
