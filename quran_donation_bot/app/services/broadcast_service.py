import logging
from asyncio import sleep
from datetime import datetime, timezone

from telegram import Bot
from telegram.error import TelegramError
from sqlalchemy.orm import Session

from quran_donation_bot.app.core.config import get_settings
from quran_donation_bot.app.db.repositories.broadcasts import BroadcastRepository
from quran_donation_bot.app.db.repositories.users import UserRepository


logger = logging.getLogger(__name__)


class BroadcastService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = BroadcastRepository(session)
        self.users = UserRepository(session)
        self.bot = Bot(token=get_settings().bot_token)

    def create_broadcast(self, *, admin_user_id: int | None, content: str, send_now: bool = False):
        broadcast = self.repository.create(
            admin_user_id=admin_user_id,
            content=content,
            status="sent" if send_now else "draft",
            sent_at=datetime.now(timezone.utc) if send_now else None,
        )
        self.session.commit()
        return broadcast

    def list_broadcasts(self):
        return self.repository.list_all()

    def list_broadcasts_page(self, *, page: int = 1, page_size: int = 10):
        page = max(1, page)
        page_size = max(1, min(page_size, 50))
        offset = (page - 1) * page_size
        return self.repository.list_page(limit=page_size, offset=offset)

    def count_broadcasts(self) -> int:
        return self.repository.count_all()

    async def send_broadcast(self, *, admin_user_id: int | None, content: str):
        broadcast = self.repository.create(
            admin_user_id=admin_user_id,
            content=content,
            status="sending",
        )
        self.session.commit()

        recipients = self.users.list_active_recipients()
        delivered_count = 0
        failed_count = 0
        failure_samples: list[str] = []

        if not recipients:
            self.repository.update(
                broadcast,
                status="failed",
                recipient_count=0,
                delivered_count=0,
                failed_count=0,
                failure_summary="No active users available for broadcast.",
            )
            self.session.commit()
            return broadcast

        for user in recipients:
            try:
                await self.bot.send_message(chat_id=user.telegram_id, text=content)
                delivered_count += 1
            except TelegramError as exc:
                failed_count += 1
                if len(failure_samples) < 5:
                    label = user.username or str(user.telegram_id)
                    failure_samples.append(f"{label}: {exc}")
                logger.warning("Broadcast failed for telegram_id=%s: %s", user.telegram_id, exc)
            await sleep(0.05)

        status = "sent"
        if delivered_count == 0:
            status = "failed"
        elif failed_count > 0:
            status = "partial"

        self.repository.update(
            broadcast,
            status=status,
            recipient_count=len(recipients),
            delivered_count=delivered_count,
            failed_count=failed_count,
            failure_summary=" | ".join(failure_samples) if failure_samples else None,
            sent_at=datetime.now(timezone.utc) if delivered_count > 0 else None,
        )
        self.session.commit()
        return broadcast
