from sqlalchemy.orm import Session

from quran_donation_bot.app.db.repositories.payment_methods import PaymentMethodRepository
from quran_donation_bot.app.db.repositories.users import UserRepository
from quran_donation_bot.app.services.subscription_service import SubscriptionService


class SettingsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.payment_methods = PaymentMethodRepository(session)

    def update_default_payment_method(self, telegram_id: int, payment_method_id: int):
        user = self.users.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        payment_method = self.payment_methods.get_by_id(payment_method_id)
        if payment_method is None or not payment_method.is_active:
            return None
        self.users.update_settings(user, default_payment_method_id=payment_method_id)
        SubscriptionService(self.session).sync_defaults_for_user(user.id, payment_method_id=payment_method_id)
        self.session.commit()
        return payment_method

    def update_default_quran_amount(self, telegram_id: int, quran_amount: int):
        user = self.users.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        self.users.update_settings(user, default_quran_amount=quran_amount)
        SubscriptionService(self.session).sync_defaults_for_user(user.id, quran_amount=quran_amount)
        self.session.commit()
        return user

    def update_language(self, telegram_id: int, language: str):
        user = self.users.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        normalized_language = language.lower()
        if normalized_language not in {"en", "ar", "am"}:
            return None
        self.users.update_settings(user, language=normalized_language)
        self.session.commit()
        return user
