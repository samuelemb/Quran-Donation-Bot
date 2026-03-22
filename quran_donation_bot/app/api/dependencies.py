from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from quran_donation_bot.app.core.config import get_settings
from quran_donation_bot.app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def require_admin_api_key(x_admin_api_key: Annotated[str | None, Header()] = None) -> str:
    settings = get_settings()
    if x_admin_api_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")
    return x_admin_api_key


AdminAuth = Depends(require_admin_api_key)
DbSession = Annotated[Session, Depends(get_db)]
