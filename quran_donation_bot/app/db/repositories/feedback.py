from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from quran_donation_bot.app.db.models import Feedback


class FeedbackRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, user_id: int, message: str) -> Feedback:
        feedback = Feedback(user_id=user_id, message=message)
        self.session.add(feedback)
        self.session.flush()
        return feedback

    def list_for_user(self, user_id: int) -> list[Feedback]:
        stmt = (
            select(Feedback)
            .options(joinedload(Feedback.user))
            .where(Feedback.user_id == user_id)
            .order_by(Feedback.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_all(self) -> list[Feedback]:
        stmt = select(Feedback).options(joinedload(Feedback.user)).order_by(Feedback.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def count_all(self) -> int:
        stmt = select(func.count(Feedback.id))
        return int(self.session.execute(stmt).scalar_one() or 0)
