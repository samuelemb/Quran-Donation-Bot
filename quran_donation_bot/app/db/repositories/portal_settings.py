from sqlalchemy import select
from sqlalchemy.orm import Session

from quran_donation_bot.app.db.models import PortalSetting


class PortalSettingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self) -> PortalSetting | None:
        stmt = select(PortalSetting).limit(1)
        return self.session.execute(stmt).scalar_one_or_none()

    def create(self, **payload) -> PortalSetting:
        setting = PortalSetting(**payload)
        self.session.add(setting)
        self.session.flush()
        return setting

    def update(self, setting: PortalSetting, **payload) -> PortalSetting:
        for key, value in payload.items():
            setattr(setting, key, value)
        self.session.add(setting)
        self.session.flush()
        return setting
