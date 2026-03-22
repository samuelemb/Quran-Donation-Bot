from sqlalchemy.orm import Session

from quran_donation_bot.app.db.repositories.feedback import FeedbackRepository
from quran_donation_bot.app.db.repositories.users import UserRepository


class FeedbackService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.feedback = FeedbackRepository(session)
        self.users = UserRepository(session)

    def submit_feedback(self, telegram_id: int, message: str):
        user = self.users.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        feedback = self.feedback.create(user_id=user.id, message=message)
        self.session.commit()
        return feedback

    def list_feedback(self):
        return self.feedback.list_all()

    def count_feedback(self) -> int:
        return self.feedback.count_all()
