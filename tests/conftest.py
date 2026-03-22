import os
from collections.abc import Generator

os.environ.setdefault("BOT_TOKEN", "123456:TESTTOKEN")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("CHANNEL_LINK", "https://t.me/test")
os.environ.setdefault("SUPPORT_CONTACT", "@support")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("ADMIN_API_KEY", "change-me")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from quran_donation_bot.app.api.app import build_api_app
from quran_donation_bot.app.api.dependencies import get_db
from quran_donation_bot.app.db.base import Base


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    try:
        yield TestingSessionLocal
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def api_client(session_factory) -> Generator[TestClient, None, None]:
    app = build_api_app()

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
