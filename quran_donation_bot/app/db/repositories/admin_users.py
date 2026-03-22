from sqlalchemy import select
from sqlalchemy.orm import Session

from quran_donation_bot.app.db.models import AdminUser


class AdminUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> AdminUser | None:
        stmt = select(AdminUser).where(AdminUser.email == email)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_id(self, admin_user_id: int) -> AdminUser | None:
        stmt = select(AdminUser).where(AdminUser.id == admin_user_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[AdminUser]:
        stmt = select(AdminUser).order_by(AdminUser.created_at.asc())
        return list(self.session.execute(stmt).scalars().all())

    def create(self, **payload) -> AdminUser:
        admin = AdminUser(**payload)
        self.session.add(admin)
        self.session.flush()
        return admin

    def update(self, admin: AdminUser, **payload) -> AdminUser:
        for key, value in payload.items():
            setattr(admin, key, value)
        self.session.add(admin)
        self.session.flush()
        return admin
