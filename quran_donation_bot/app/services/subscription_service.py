from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from quran_donation_bot.app.core.constants import DonationPlanType, SubscriptionStatus
from quran_donation_bot.app.db.models import Donation
from quran_donation_bot.app.db.repositories.subscriptions import SubscriptionRepository
from quran_donation_bot.app.services.portal_settings_cache import PortalSettingsCache


class SubscriptionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = SubscriptionRepository(session)

    def sync_after_approved_donation(self, donation: Donation):
        if donation.plan_type == DonationPlanType.ONE_TIME:
            return None

        billing_interval_days = 90 if donation.plan_type == DonationPlanType.THREE_MONTH else 30
        payment_date = donation.created_at
        payload = {
            "payment_method_id": donation.payment_method_id,
            "last_donation_id": donation.id,
            "plan_type": donation.plan_type,
            "billing_interval_days": billing_interval_days,
            "quran_amount": donation.quran_amount,
            "monthly_amount": donation.total_amount,
            "status": SubscriptionStatus.ACTIVE,
            "next_payment_due_at": payment_date + timedelta(days=billing_interval_days),
            "last_paid_at": payment_date,
        }
        subscription = self.repository.get_by_user_id(donation.user_id)
        if subscription is None:
            subscription = self.repository.create(
                user_id=donation.user_id,
                started_at=payment_date,
                **payload,
            )
        else:
            subscription = self.repository.update(subscription, **payload)
        self.session.flush()
        return subscription

    def sync_defaults_for_user(self, user_id: int, *, payment_method_id: int | None = None, quran_amount: int | None = None):
        subscription = self.repository.get_by_user_id(user_id)
        if subscription is None:
            return None
        updates = {}
        if payment_method_id is not None:
            updates["payment_method_id"] = payment_method_id
        if quran_amount is not None:
            price_per_quran = PortalSettingsCache.get(self.session).price_per_quran_birr
            updates["quran_amount"] = quran_amount
            updates["monthly_amount"] = quran_amount * price_per_quran
        if not updates:
            return subscription
        subscription = self.repository.update(subscription, **updates)
        self.session.flush()
        return subscription

    def list_active(self, *, limit: int = 200, offset: int = 0):
        refreshed = self.repository.refresh_overdue_statuses()
        if refreshed:
            self.session.commit()
        return self.repository.list_by_status(SubscriptionStatus.ACTIVE, limit=limit, offset=offset)

    def list_overdue(self, *, limit: int = 200, offset: int = 0):
        refreshed = self.repository.refresh_overdue_statuses()
        if refreshed:
            self.session.commit()
        return self.repository.list_by_status(SubscriptionStatus.OVERDUE, limit=limit, offset=offset)

    def count_active(self) -> int:
        refreshed = self.repository.refresh_overdue_statuses()
        if refreshed:
            self.session.commit()
        return self.repository.count_by_status(SubscriptionStatus.ACTIVE)

    def count_overdue(self) -> int:
        refreshed = self.repository.refresh_overdue_statuses()
        if refreshed:
            self.session.commit()
        return self.repository.count_by_status(SubscriptionStatus.OVERDUE)

    def list_due_for_reminders(self):
        refreshed = self.repository.refresh_overdue_statuses()
        if refreshed:
            self.session.commit()
        return self.repository.list_due_for_reminders()

    def mark_paid(self, subscription_id: int):
        subscription = self.repository.get_by_id(subscription_id)
        if subscription is None:
            return None
        now = datetime.now(timezone.utc)
        subscription = self.repository.update(
            subscription,
            status=SubscriptionStatus.ACTIVE,
            last_paid_at=now,
            next_payment_due_at=now + timedelta(days=subscription.billing_interval_days),
        )
        self.session.commit()
        return subscription
