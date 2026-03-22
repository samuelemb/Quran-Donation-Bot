from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from quran_donation_bot.app.db.models import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).options(joinedload(User.default_payment_method)).where(User.telegram_id == telegram_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).options(joinedload(User.default_payment_method)).where(User.id == user_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_users(self, *, limit: int = 100, offset: int = 0) -> list[User]:
        stmt = select(User).order_by(User.joined_at.desc()).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())

    def count_all(self) -> int:
        stmt = select(func.count(User.id))
        return int(self.session.execute(stmt).scalar_one() or 0)

    def list_active_recipients(self) -> list[User]:
        stmt = select(User).where(User.is_active.is_(True)).order_by(User.joined_at.asc())
        return list(self.session.execute(stmt).scalars().all())

    def get_language_map(self) -> dict[int, str]:
        stmt = select(User.telegram_id, User.language).where(User.language.is_not(None))
        return {
            int(telegram_id): str(language)
            for telegram_id, language in self.session.execute(stmt).all()
            if language
        }

    def create(self, telegram_id: int, username: str | None, first_name: str, language: str | None = None) -> User:
        now = datetime.now(timezone.utc)
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language=language,
            last_interaction_at=now,
        )
        self.session.add(user)
        self.session.flush()
        return user

    def touch_interaction(self, user: User) -> User:
        user.last_interaction_at = datetime.now(timezone.utc)
        self.session.add(user)
        self.session.flush()
        return user

    def update_profile(self, user: User, *, username: str | None, first_name: str, language: str | None = None) -> User:
        user.username = username
        user.first_name = first_name
        if language is not None:
            user.language = language
        user.last_interaction_at = datetime.now(timezone.utc)
        self.session.add(user)
        self.session.flush()
        return user

    def update_settings(
        self,
        user: User,
        *,
        default_payment_method_id: int | None = None,
        default_quran_amount: int | None = None,
        language: str | None = None,
    ) -> User:
        if default_payment_method_id is not None:
            user.default_payment_method_id = default_payment_method_id
        if default_quran_amount is not None:
            user.default_quran_amount = default_quran_amount
        if language is not None:
            user.language = language
        user.last_interaction_at = datetime.now(timezone.utc)
        self.session.add(user)
        self.session.flush()
        return user
