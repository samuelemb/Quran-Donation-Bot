import logging
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from quran_donation_bot.app.api.routes import admin_portal, donations, feedback, health, payment_methods, users
from quran_donation_bot.app.core.config import get_settings
from quran_donation_bot.app.core.logging import setup_logging
from quran_donation_bot.app.db.session import SessionLocal
from quran_donation_bot.app.services.admin_user_service import AdminUserService
from quran_donation_bot.app.services.portal_settings_service import PortalSettingsService


logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    last_error = None
    for attempt in range(1, 4):
        try:
            with SessionLocal() as session:
                AdminUserService(session).ensure_default_admin()
                PortalSettingsService(session).get_or_create()
            last_error = None
            break
        except Exception as exc:
            last_error = exc
            logger.warning("Startup DB init attempt %s failed: %s", attempt, exc)
            if attempt < 3:
                await asyncio.sleep(1.5)
    if last_error is not None:
        raise last_error
    logger.info("API startup complete env=%s", settings.app_env)
    yield


def build_api_app() -> FastAPI:
    setup_logging()
    settings = get_settings()
    app = FastAPI(title="Quran Donation Bot API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.admin_session_secret,
        same_site="lax",
        https_only=settings.is_production,
    )
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(health.router)
    app.include_router(donations.router)
    app.include_router(payment_methods.router)
    app.include_router(users.router)
    app.include_router(feedback.router)
    app.include_router(admin_portal.router)

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", "generated-request-id")
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled API exception path=%s", request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app
