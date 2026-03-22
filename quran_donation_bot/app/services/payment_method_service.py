from sqlalchemy.orm import Session

from quran_donation_bot.app.db.repositories.payment_methods import PaymentMethodRepository
from quran_donation_bot.app.schemas.payment_method import PaymentMethodCreate, PaymentMethodUpdate


class PaymentMethodService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = PaymentMethodRepository(session)

    def list_payment_methods(self):
        return self.repository.list_all()

    def create_payment_method(self, payload: PaymentMethodCreate):
        method = self.repository.create(**payload.model_dump())
        self.session.commit()
        return method

    def update_payment_method(self, payment_method_id: int, payload: PaymentMethodUpdate):
        method = self.repository.get_by_id(payment_method_id)
        if method is None:
            return None
        updates = payload.model_dump(exclude_unset=True)
        method = self.repository.update(method, **updates)
        self.session.commit()
        return method
