from datetime import datetime, timezone

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from quran_donation_bot.app.core.constants import DonationStatus
from quran_donation_bot.app.db.models import Donation


class DonationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_pending(self, **payload) -> Donation:
        donation = Donation(status=DonationStatus.PENDING, **payload)
        self.session.add(donation)
        self.session.flush()
        return donation

    def get_by_id(self, donation_id: int) -> Donation | None:
        stmt = (
            select(Donation)
            .options(joinedload(Donation.payment_method), joinedload(Donation.user))
            .where(Donation.id == donation_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_for_user(self, user_id: int) -> list[Donation]:
        stmt = (
            select(Donation)
            .options(joinedload(Donation.payment_method))
            .where(Donation.user_id == user_id)
            .order_by(Donation.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_all(self, *, limit: int = 200, offset: int = 0) -> list[Donation]:
        stmt = (
            select(Donation)
            .options(joinedload(Donation.payment_method), joinedload(Donation.user))
            .order_by(Donation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars().all())

    def count_pending(self) -> int:
        stmt = select(func.count(Donation.id)).where(Donation.status == DonationStatus.PENDING)
        return int(self.session.execute(stmt).scalar_one() or 0)

    def count_by_status(self, status: DonationStatus) -> int:
        stmt = select(func.count(Donation.id)).where(Donation.status == status)
        return int(self.session.execute(stmt).scalar_one() or 0)

    def get_approved_totals(self) -> tuple[int, float]:
        stmt = select(
            func.coalesce(func.sum(Donation.quran_amount), 0),
            func.coalesce(func.sum(Donation.total_amount), 0),
        ).where(Donation.status == DonationStatus.APPROVED)
        quran_total, amount_total = self.session.execute(stmt).one()
        return int(quran_total or 0), float(amount_total or 0)

    def get_approved_average_amount(self) -> float:
        stmt = select(func.coalesce(func.avg(Donation.total_amount), 0)).where(Donation.status == DonationStatus.APPROVED)
        value = self.session.execute(stmt).scalar_one()
        return float(value or 0)

    def get_approved_total_since(self, since: datetime) -> float:
        stmt = select(func.coalesce(func.sum(Donation.total_amount), 0)).where(
            Donation.status == DonationStatus.APPROVED,
            Donation.created_at >= since,
        )
        value = self.session.execute(stmt).scalar_one()
        return float(value or 0)

    def get_monthly_totals(self, *, months: int = 6) -> list[tuple[str, float]]:
        now = datetime.now(timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        starts = []
        current = month_start
        for _ in range(months):
            starts.append(current)
            current = (current - timedelta(days=1)).replace(day=1)
        starts.reverse()

        rows: list[tuple[str, float]] = []
        for start in starts:
            if start.month == 12:
                end = datetime(start.year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                end = datetime(start.year, start.month + 1, 1, tzinfo=timezone.utc)
            stmt = select(func.coalesce(func.sum(Donation.total_amount), 0)).where(
                Donation.status == DonationStatus.APPROVED,
                Donation.created_at >= start,
                Donation.created_at < end,
            )
            total = self.session.execute(stmt).scalar_one()
            rows.append((start.strftime("%b"), float(total or 0)))
        return rows

    def count_active_subscribers(self, *, days: int = 30) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        latest_approved = (
            select(Donation.user_id, func.max(Donation.created_at).label("latest_created_at"))
            .where(Donation.status == DonationStatus.APPROVED)
            .group_by(Donation.user_id)
            .subquery()
        )
        stmt = select(func.count()).select_from(latest_approved).where(latest_approved.c.latest_created_at >= cutoff)
        return int(self.session.execute(stmt).scalar_one() or 0)

    def count_late_subscribers(self, *, days: int = 30) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        latest_approved = (
            select(Donation.user_id, func.max(Donation.created_at).label("latest_created_at"))
            .where(Donation.status == DonationStatus.APPROVED)
            .group_by(Donation.user_id)
            .subquery()
        )
        stmt = select(func.count()).select_from(latest_approved).where(latest_approved.c.latest_created_at < cutoff)
        return int(self.session.execute(stmt).scalar_one() or 0)

    def list_recent(self, *, limit: int = 100, status: DonationStatus | None = None) -> list[Donation]:
        stmt = (
            select(Donation)
            .options(joinedload(Donation.payment_method), joinedload(Donation.user))
            .order_by(Donation.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(Donation.status == status)
        return list(self.session.execute(stmt).scalars().all())

    def get_user_totals(self, user_id: int) -> tuple[int, float]:
        stmt = select(
            func.coalesce(func.sum(Donation.quran_amount), 0),
            func.coalesce(func.sum(Donation.total_amount), 0),
        ).where(Donation.user_id == user_id, Donation.status == DonationStatus.APPROVED)
        quran_total, amount_total = self.session.execute(stmt).one()
        return int(quran_total or 0), float(amount_total or 0)

    def list_pending(self, *, limit: int = 100, offset: int = 0) -> list[Donation]:
        stmt = (
            select(Donation)
            .options(joinedload(Donation.user), joinedload(Donation.payment_method))
            .where(Donation.status == DonationStatus.PENDING)
            .order_by(Donation.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars().all())

    def update_status(
        self,
        donation: Donation,
        *,
        status: DonationStatus,
        reviewed_by: str,
        review_notes: str | None = None,
        rejection_reason: str | None = None,
    ) -> Donation:
        donation.status = status
        donation.reviewed_at = datetime.now(timezone.utc)
        donation.reviewed_by = reviewed_by
        donation.review_notes = review_notes
        donation.rejection_reason = rejection_reason
        self.session.add(donation)
        self.session.flush()
        return donation
