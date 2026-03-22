from sqlalchemy.orm import Session

from quran_donation_bot.app.core.config import get_settings
from quran_donation_bot.app.db.repositories.portal_settings import PortalSettingRepository


class PortalSettingsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = PortalSettingRepository(session)

    def get_or_create(self):
        setting = self.repository.get()
        if setting is not None:
            return setting
        config = get_settings()
        setting = self.repository.create(
            organization_name="Quran Donation",
            support_contact=config.support_contact,
            telegram_channel_link=config.channel_link,
        )
        self.session.commit()
        return setting

    def update(self, **payload):
        setting = self.get_or_create()
        setting = self.repository.update(setting, **payload)
        self.session.commit()
        return setting
