from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from quran_donation_bot.app.core.constants import SubscriptionStatus
from quran_donation_bot.app.db.models import Subscription


class SubscriptionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, subscription_id: int) -> Subscription | None:
        stmt = (
            select(Subscription)
            .options(
                joinedload(Subscription.user),
                joinedload(Subscription.payment_method),
                joinedload(Subscription.last_donation),
            )
            .where(Subscription.id == subscription_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_user_id(self, user_id: int) -> Subscription | None:
        stmt = (
            select(Subscription)
            .options(
                joinedload(Subscription.user),
                joinedload(Subscription.payment_method),
                joinedload(Subscription.last_donation),
            )
            .where(Subscription.user_id == user_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(self, *, limit: int = 200, offset: int = 0) -> list[Subscription]:
        stmt = (
            select(Subscription)
            .options(
                joinedload(Subscription.user),
                joinedload(Subscription.payment_method),
                joinedload(Subscription.last_donation),
            )
            .order_by(Subscription.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_by_status(self, status: SubscriptionStatus, *, limit: int = 200, offset: int = 0) -> list[Subscription]:
        stmt = (
            select(Subscription)
            .options(
                joinedload(Subscription.user),
                joinedload(Subscription.payment_method),
                joinedload(Subscription.last_donation),
            )
            .where(Subscription.status == status)
            .order_by(Subscription.next_payment_due_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars().all())

    def count_by_status(self, status: SubscriptionStatus) -> int:
        stmt = select(func.count(Subscription.id)).where(Subscription.status == status)
        return int(self.session.execute(stmt).scalar_one() or 0)

    def create(self, **payload) -> Subscription:
        subscription = Subscription(**payload)
        self.session.add(subscription)
        self.session.flush()
        return subscription

    def update(self, subscription: Subscription, **payload) -> Subscription:
        for key, value in payload.items():
            setattr(subscription, key, value)
        self.session.add(subscription)
        self.session.flush()
        return subscription

    def refresh_overdue_statuses(self) -> int:
        now = datetime.now(timezone.utc)
        stmt = select(Subscription).where(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.next_payment_due_at < now,
        )
        subscriptions = list(self.session.execute(stmt).scalars().all())
        for subscription in subscriptions:
            subscription.status = SubscriptionStatus.OVERDUE
            self.session.add(subscription)
        self.session.flush()
        return len(subscriptions)

    def list_due_for_reminders(self) -> list[Subscription]:
        stmt = (
            select(Subscription)
            .options(
                joinedload(Subscription.user),
                joinedload(Subscription.payment_method),
                joinedload(Subscription.last_donation),
            )
            .where(Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.OVERDUE]))
            .order_by(Subscription.next_payment_due_at.asc())
        )
        return list(self.session.execute(stmt).scalars().all())
