from sqlalchemy.orm import Session

from quran_donation_bot.app.db.repositories.users import UserRepository


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = UserRepository(session)

    def list_users(self, *, limit: int = 100, offset: int = 0):
        return self.repository.list_users(limit=limit, offset=offset)

    def get_user(self, user_id: int):
        return self.repository.get_by_id(user_id)

    def count_users(self) -> int:
        return self.repository.count_all()

    def list_active_recipients(self):
        return self.repository.list_active_recipients()
