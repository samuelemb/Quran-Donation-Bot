from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from quran_donation_bot.app.core.config import get_settings
from quran_donation_bot.app.services.portal_settings_service import PortalSettingsService


@dataclass(slots=True)
class PortalSettingsSnapshot:
    support_contact: str
    telegram_channel_link: str | None
    price_per_quran_birr: int


class PortalSettingsCache:
    _snapshot: PortalSettingsSnapshot | None = None
    _expires_at: datetime | None = None
    _ttl_seconds = 60

    @classmethod
    def get(cls, session: Session) -> PortalSettingsSnapshot:
        now = datetime.now(timezone.utc)
        if cls._snapshot is not None and cls._expires_at is not None and now < cls._expires_at:
            return cls._snapshot

        settings = PortalSettingsService(session).get_or_create()
        cls._snapshot = PortalSettingsSnapshot(
            support_contact=settings.support_contact,
            telegram_channel_link=settings.telegram_channel_link,
            price_per_quran_birr=settings.price_per_quran_birr,
        )
        cls._expires_at = now + timedelta(seconds=cls._ttl_seconds)
        return cls._snapshot

    @classmethod
    def get_cached_or_default(cls) -> PortalSettingsSnapshot:
        now = datetime.now(timezone.utc)
        if cls._snapshot is not None and cls._expires_at is not None and now < cls._expires_at:
            return cls._snapshot

        settings = get_settings()
        return PortalSettingsSnapshot(
            support_contact=settings.support_contact,
            telegram_channel_link=settings.channel_link,
            price_per_quran_birr=450,
        )

    @classmethod
    def refresh(cls, session: Session) -> PortalSettingsSnapshot:
        return cls.get(session)

    @classmethod
    def invalidate(cls) -> None:
        cls._snapshot = None
        cls._expires_at = None
