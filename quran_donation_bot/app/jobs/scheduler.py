import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from quran_donation_bot.app.core.config import get_settings
from quran_donation_bot.app.db.session import SessionLocal
from quran_donation_bot.app.services.notification_service import NotificationService
from quran_donation_bot.app.services.subscription_service import SubscriptionService


logger = logging.getLogger(__name__)


def build_scheduler() -> AsyncIOScheduler | None:
    settings = get_settings()
    if not settings.enable_scheduler:
        logger.info("Scheduler disabled")
        return None
    scheduler = AsyncIOScheduler(timezone="Africa/Nairobi")
    logger.info("Scheduler enabled")
    return scheduler


async def send_subscription_reminders() -> None:
    now = datetime.now(timezone.utc)
    with SessionLocal() as session:
        service = SubscriptionService(session)
        notification_service = NotificationService(session)
        subscriptions = service.list_due_for_reminders()
        for subscription in subscriptions:
            days_delta = (subscription.next_payment_due_at.date() - now.date()).days
            if days_delta not in {7, 3, 1, 0} and days_delta > 0:
                continue
            reminder_key = now.date().isoformat()
            await notification_service.send_subscription_reminder_message(
                subscription,
                reminder_key=reminder_key,
                days_delta=days_delta,
            )
