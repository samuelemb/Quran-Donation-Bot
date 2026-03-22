from sqlalchemy import func, select
from sqlalchemy.orm import Session

from quran_donation_bot.app.db.models import BroadcastMessage


class BroadcastRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, **payload) -> BroadcastMessage:
        broadcast = BroadcastMessage(**payload)
        self.session.add(broadcast)
        self.session.flush()
        return broadcast

    def list_all(self) -> list[BroadcastMessage]:
        stmt = select(BroadcastMessage).order_by(BroadcastMessage.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def list_page(self, *, limit: int = 10, offset: int = 0) -> list[BroadcastMessage]:
        stmt = select(BroadcastMessage).order_by(BroadcastMessage.created_at.desc()).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())

    def count_all(self) -> int:
        stmt = select(func.count(BroadcastMessage.id))
        return int(self.session.execute(stmt).scalar_one() or 0)

    def update(self, broadcast: BroadcastMessage, **payload) -> BroadcastMessage:
        for key, value in payload.items():
            setattr(broadcast, key, value)
        self.session.add(broadcast)
        self.session.flush()
        return broadcast
