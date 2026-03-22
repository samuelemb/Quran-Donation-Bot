from sqlalchemy.orm import Session

from quran_donation_bot.app.core.config import get_settings
from quran_donation_bot.app.db.repositories.admin_users import AdminUserRepository
from quran_donation_bot.app.utils.security import hash_password, verify_password


class AdminUserService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = AdminUserRepository(session)

    def ensure_default_admin(self):
        settings = get_settings()
        admin = self.repository.get_by_email(settings.admin_email)
        if admin is None:
            admin = self.repository.create(
                email=settings.admin_email,
                full_name=settings.admin_full_name,
                password_hash=hash_password(settings.admin_password),
                role="super_admin",
                is_active=True,
            )
            self.session.commit()
        return admin

    def authenticate(self, email: str, password: str):
        admin = self.repository.get_by_email(email)
        if admin is None or not admin.is_active:
            return None
        if not verify_password(password, admin.password_hash):
            return None
        return admin

    def list_admins(self):
        return self.repository.list_all()

    def change_password(self, admin_user_id: int, new_password: str):
        admin = self.repository.get_by_id(admin_user_id)
        if admin is None:
            return None
        self.repository.update(admin, password_hash=hash_password(new_password))
        self.session.commit()
        return admin
