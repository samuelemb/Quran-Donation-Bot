from sqlalchemy import select
from sqlalchemy.orm import Session

from quran_donation_bot.app.db.models import PaymentMethod


class PaymentMethodRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_active(self) -> list[PaymentMethod]:
        stmt = (
            select(PaymentMethod)
            .where(PaymentMethod.is_active.is_(True))
            .order_by(PaymentMethod.display_order.asc(), PaymentMethod.name.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_all(self) -> list[PaymentMethod]:
        stmt = select(PaymentMethod).order_by(PaymentMethod.display_order.asc(), PaymentMethod.name.asc())
        return list(self.session.execute(stmt).scalars().all())

    def get_by_id(self, payment_method_id: int) -> PaymentMethod | None:
        stmt = select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_name(self, name: str) -> PaymentMethod | None:
        stmt = select(PaymentMethod).where(PaymentMethod.name == name)
        return self.session.execute(stmt).scalar_one_or_none()

    def create(self, **payload) -> PaymentMethod:
        method = PaymentMethod(**payload)
        self.session.add(method)
        self.session.flush()
        return method

    def update(self, method: PaymentMethod, **payload) -> PaymentMethod:
        for key, value in payload.items():
            setattr(method, key, value)
        self.session.add(method)
        self.session.flush()
        return method
