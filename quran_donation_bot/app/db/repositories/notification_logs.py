from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from quran_donation_bot.app.core.constants import NotificationDeliveryStatus
from quran_donation_bot.app.db.models import NotificationLog


class NotificationLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_user_donation_type(self, *, user_id: int, donation_id: int | None, notification_type: str) -> NotificationLog | None:
        stmt = select(NotificationLog).where(
            NotificationLog.user_id == user_id,
            NotificationLog.donation_id == donation_id,
            NotificationLog.notification_type == notification_type,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create(self, **payload) -> NotificationLog:
        log = NotificationLog(**payload)
        self.session.add(log)
        self.session.flush()
        return log

    def mark_sent(self, log: NotificationLog, *, message_id: int | None) -> NotificationLog:
        log.delivery_status = NotificationDeliveryStatus.SENT
        log.attempt_count = (log.attempt_count or 0) + 1
        log.telegram_message_id = message_id
        log.failure_reason = None
        log.sent_at = datetime.now(timezone.utc)
        self.session.add(log)
        self.session.flush()
        return log

    def mark_failed(self, log: NotificationLog, *, reason: str) -> NotificationLog:
        log.delivery_status = NotificationDeliveryStatus.FAILED
        log.attempt_count = (log.attempt_count or 0) + 1
        log.failure_reason = reason
        self.session.add(log)
        self.session.flush()
        return log
