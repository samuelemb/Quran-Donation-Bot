from datetime import datetime

from pydantic import BaseModel

from quran_donation_bot.app.core.constants import NotificationDeliveryStatus


class NotificationResult(BaseModel):
    delivered: bool
    status: NotificationDeliveryStatus
    telegram_message_id: int | None = None
    failure_reason: str | None = None
    sent_at: datetime | None = None
