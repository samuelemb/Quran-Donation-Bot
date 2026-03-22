import uvicorn

from quran_donation_bot.app.api.app import build_api_app
from quran_donation_bot.app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "quran_donation_bot.app.api.app:build_api_app",
        host=settings.api_host,
        port=settings.api_port,
        factory=True,
        reload=not settings.is_production,
    )


if __name__ == "__main__":
    main()
