from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from quran_donation_bot.app.core.constants import DonationStatus
from quran_donation_bot.app.db.repositories.donations import DonationRepository
from quran_donation_bot.app.db.repositories.payment_methods import PaymentMethodRepository
from quran_donation_bot.app.db.repositories.users import UserRepository
from quran_donation_bot.app.schemas.donation import DonationCreate, DonationSummary, DonationSummaryItem
from quran_donation_bot.app.schemas.user import UserCreate
from quran_donation_bot.app.services.portal_settings_cache import PortalSettingsCache
from quran_donation_bot.app.services.subscription_service import SubscriptionService


class DonationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.payment_methods = PaymentMethodRepository(session)
        self.donations = DonationRepository(session)

    def create_or_get_user(self, payload: UserCreate):
        user = self.users.get_by_telegram_id(payload.telegram_id)
        if user is None:
            user = self.users.create(
                telegram_id=payload.telegram_id,
                username=payload.username,
                first_name=payload.first_name,
                language=payload.language,
            )
            self.session.commit()
            return user

        now = datetime.now(timezone.utc)
        username_changed = user.username != payload.username
        first_name_changed = user.first_name != payload.first_name
        language_changed = payload.language is not None and user.language != payload.language
        interaction_stale = (
            user.last_interaction_at is None
            or (now - user.last_interaction_at) >= timedelta(hours=12)
        )
        if not username_changed and not first_name_changed and not language_changed and not interaction_stale:
            return user

        self.users.update_profile(
            user,
            username=payload.username,
            first_name=payload.first_name,
            language=payload.language,
        )
        self.session.commit()
        return user

    def touch_user(self, telegram_id: int):
        user = self.users.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        self.users.touch_interaction(user)
        self.session.commit()
        return user

    def calculate_total_amount(self, quran_amount: int) -> int:
        price_per_quran = PortalSettingsCache.get(self.session).price_per_quran_birr
        return quran_amount * price_per_quran

    def get_active_payment_methods(self):
        return self.payment_methods.list_active()

    def get_payment_method(self, payment_method_id: int):
        return self.payment_methods.get_by_id(payment_method_id)

    def create_pending_donation(self, payload: DonationCreate):
        donation = self.donations.create_pending(**payload.model_dump())
        self.session.commit()
        return donation

    def get_user_donation_summary(self, telegram_id: int) -> DonationSummary | None:
        user = self.users.get_by_telegram_id(telegram_id)
        if user is None:
            return None

        total_qurans, total_amount = self.donations.get_user_totals(user.id)
        donations = self.donations.list_for_user(user.id)
        return DonationSummary(
            total_qurans=total_qurans,
            total_amount=total_amount,
            donations=[
                DonationSummaryItem(
                    id=donation.id,
                    plan_type=donation.plan_type,
                    quran_amount=donation.quran_amount,
                    total_amount=float(donation.total_amount),
                    payment_method=donation.payment_method_name_snapshot,
                    status=donation.status,
                    created_at=donation.created_at,
                )
                for donation in donations
            ],
        )

    def get_donation(self, donation_id: int):
        return self.donations.get_by_id(donation_id)

    def list_pending_donations(self, *, limit: int = 100, offset: int = 0):
        return self.donations.list_pending(limit=limit, offset=offset)

    def approve_donation(self, donation_id: int, reviewed_by: str, reason: str | None = None, review_notes: str | None = None):
        donation = self.donations.get_by_id(donation_id)
        if donation is None:
            return None
        self.donations.update_status(
            donation,
            status=DonationStatus.APPROVED,
            reviewed_by=reviewed_by,
            review_notes=review_notes,
            rejection_reason=reason,
        )
        SubscriptionService(self.session).sync_after_approved_donation(donation)
        self.session.commit()
        return donation

    def reject_donation(self, donation_id: int, reviewed_by: str, reason: str, review_notes: str | None = None):
        donation = self.donations.get_by_id(donation_id)
        if donation is None:
            return None
        self.donations.update_status(
            donation,
            status=DonationStatus.REJECTED,
            reviewed_by=reviewed_by,
            review_notes=review_notes,
            rejection_reason=reason,
        )
        self.session.commit()
        return donation
