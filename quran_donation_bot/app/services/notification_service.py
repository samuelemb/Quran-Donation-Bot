import logging
from datetime import datetime, timezone

from telegram import Bot
from telegram.error import TelegramError

from quran_donation_bot.app.bot.keyboards.inline import donate_now_keyboard
from quran_donation_bot.app.core.config import get_settings
from quran_donation_bot.app.core.constants import DonationPlanType
from quran_donation_bot.app.core.constants import NotificationDeliveryStatus
from quran_donation_bot.app.db.models import Donation, Subscription
from quran_donation_bot.app.db.repositories.notification_logs import NotificationLogRepository
from quran_donation_bot.app.schemas.notification import NotificationResult
from quran_donation_bot.app.utils.i18n import normalize_language, rtl


logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, session) -> None:
        settings = get_settings()
        self.bot = Bot(token=settings.bot_token)
        self.logs = NotificationLogRepository(session)
        self.session = session

    async def send_donation_approved_message(self, user_telegram_id: int, donation: Donation) -> NotificationResult:
        language = self._user_language(donation.user.language if donation.user is not None else None)
        if language == "ar":
            message = rtl(
                "تمت مراجعة لقطة الشاشة الخاصة بك واعتمادها. شكرًا لك على تبرعك واشتراكك.\n\n"
                f"التبرع: {donation.quran_amount} مصحف\n"
                f"المبلغ: {float(donation.total_amount):.0f} بر"
            )
        elif language == "am":
            message = (
                "የላኩት ስክሪንሾት ተመርምሮ ጸድቋል። ከሰደቃዎ እና ምዝገባዎ እናመሰግናለን።\n\n"
                f"ስደቃ: {donation.quran_amount} ቁርአን\n"
                f"መጠን: {float(donation.total_amount):.0f} ብር"
            )
        else:
            message = (
                "The admin has confirmed your screenshot. Thank you for your donation and subscription.\n\n"
                f"Donation: {donation.quran_amount} Quran(s)\n"
                f"Amount: {float(donation.total_amount):.0f} Birr"
            )
        return await self._send_once(
            user_id=donation.user_id,
            donation_id=donation.id,
            user_telegram_id=user_telegram_id,
            notification_type="donation_approved",
            message=message,
        )

    async def send_donation_rejected_message(
        self,
        user_telegram_id: int,
        donation: Donation,
        reason: str | None = None,
    ) -> NotificationResult:
        language = self._user_language(donation.user.language if donation.user is not None else None)
        if language == "ar":
            message = "تعذّر اعتماد لقطة الشاشة التي أرسلتها. يرجى إعادة إرسال إيصال دفع واضح وصحيح."
            if donation is not None:
                message += f"\n\nالتبرع: {donation.quran_amount} مصحف"
            if reason:
                message += f"\nالسبب: {reason}"
            message = rtl(message)
        elif language == "am":
            message = "የላኩት ስክሪንሾት ማጽደቅ አልተቻለም። እባክዎ ግልጽ እና ትክክለኛ የክፍያ ደረሰኝ እንደገና ይላኩ።"
            if donation is not None:
                message += f"\n\nስደቃ: {donation.quran_amount} ቁርአን"
            if reason:
                message += f"\nምክንያት: {reason}"
        else:
            message = "Your screenshot was not approved. Please resend a valid payment receipt."
            if donation is not None:
                message += f"\n\nDonation: {donation.quran_amount} Quran(s)"
            if reason:
                message += f"\nReason: {reason}"
        return await self._send_once(
            user_id=donation.user_id,
            donation_id=donation.id,
            user_telegram_id=user_telegram_id,
            notification_type="donation_rejected",
            message=message,
        )

    async def send_subscription_reminder_message(
        self,
        subscription: Subscription,
        *,
        reminder_key: str,
        days_delta: int,
    ) -> NotificationResult:
        language = self._user_language(subscription.user.language if subscription.user is not None else None)
        plan_label = {
            DonationPlanType.MONTHLY: (
                "monthly subscription"
                if language == "en"
                else "الاشتراك الشهري"
                if language == "ar"
                else "ወርሃዊ ደንበኝነት"
            ),
            DonationPlanType.THREE_MONTH: (
                "3-month subscription"
                if language == "en"
                else "اشتراك 3 أشهر"
                if language == "ar"
                else "የ3 ወር ደንበኝነት"
            ),
        }.get(
            subscription.plan_type,
            "subscription" if language == "en" else "الاشتراك" if language == "ar" else "ደንበኝነት",
        )
        if days_delta > 0 and language == "en":
            lead_text = f"is due in {days_delta} day(s)"
        elif days_delta == 0 and language == "en":
            lead_text = "is due today"
        elif days_delta < 0 and language == "en":
            lead_text = f"is overdue by {abs(days_delta)} day(s)"
        elif days_delta > 0 and language == "am":
            lead_text = f"ከ{days_delta} ቀን በኋላ ይደርሳል"
        elif days_delta == 0 and language == "am":
            lead_text = "ዛሬ የሚከፈል ነው"
        elif days_delta < 0 and language == "am":
            lead_text = f"{abs(days_delta)} ቀን ዘግይቷል"
        elif days_delta > 0:
            lead_text = f"سيحين موعده بعد {days_delta} يوم"
        elif days_delta == 0:
            lead_text = "موعده اليوم"
        else:
            lead_text = f"متأخر منذ {abs(days_delta)} يوم"

        if language == "ar":
            message = rtl(
                f"تذكير: {plan_label} {lead_text}.\n\n"
                f"عدد المصاحف: {subscription.quran_amount}\n"
                f"المبلغ: {float(subscription.monthly_amount):.0f} بر\n"
                f"تاريخ الاستحقاق: {subscription.next_payment_due_at.strftime('%Y-%m-%d')}\n\n"
                "يرجى إكمال الدفع ثم إرسال لقطة شاشة للإيصال داخل البوت."
            )
        elif language == "am":
            message = (
                f"ማሳሰቢያ: {plan_label} {lead_text}።\n\n"
                f"የቁርአን ብዛት: {subscription.quran_amount}\n"
                f"መጠን: {float(subscription.monthly_amount):.0f} ብር\n"
                f"የክፍያ ቀን: {subscription.next_payment_due_at.strftime('%Y-%m-%d')}\n\n"
                "እባክዎ ክፍያውን ያጠናቁ እና የደረሰኙን ስክሪንሾት በቦቱ ውስጥ ይላኩ።"
            )
        else:
            message = (
                f"Reminder: your {plan_label} {lead_text}.\n\n"
                f"Qurans: {subscription.quran_amount}\n"
                f"Amount: {float(subscription.monthly_amount):.0f} Birr\n"
                f"Due date: {subscription.next_payment_due_at.strftime('%Y-%m-%d')}\n\n"
                "Please complete your payment and send your receipt screenshot in the bot."
            )
        return await self._send_once(
            user_id=subscription.user_id,
            donation_id=None,
            user_telegram_id=subscription.user.telegram_id,
            notification_type=f"subscription_reminder:{subscription.id}:{reminder_key}",
            message=message,
            reply_markup=donate_now_keyboard(subscription.id, language),
        )

    @staticmethod
    def _user_language(language: str | None) -> str:
        return normalize_language(language)

    async def _send_once(
        self,
        *,
        user_id: int,
        donation_id: int | None,
        user_telegram_id: int,
        notification_type: str,
        message: str,
        reply_markup=None,
    ) -> NotificationResult:
        existing = self.logs.get_by_user_donation_type(
            user_id=user_id,
            donation_id=donation_id,
            notification_type=notification_type,
        )
        if existing and existing.delivery_status == NotificationDeliveryStatus.SENT:
            return NotificationResult(
                delivered=True,
                status=NotificationDeliveryStatus.SENT,
                telegram_message_id=existing.telegram_message_id,
                sent_at=existing.sent_at,
            )

        log = existing or self.logs.create(
            user_id=user_id,
            donation_id=donation_id,
            notification_type=notification_type,
        )
        try:
            telegram_message = await self.bot.send_message(
                chat_id=user_telegram_id,
                text=message,
                reply_markup=reply_markup,
            )
            self.logs.mark_sent(log, message_id=telegram_message.message_id)
            self.session.commit()
            logger.info("Sent %s notification to telegram_id=%s donation_id=%s", notification_type, user_telegram_id, donation_id)
            return NotificationResult(
                delivered=True,
                status=NotificationDeliveryStatus.SENT,
                telegram_message_id=telegram_message.message_id,
                sent_at=datetime.now(timezone.utc),
            )
        except TelegramError as exc:
            self.logs.mark_failed(log, reason=str(exc))
            self.session.commit()
            logger.exception("Failed to send %s notification for donation_id=%s", notification_type, donation_id)
            return NotificationResult(
                delivered=False,
                status=NotificationDeliveryStatus.FAILED,
                failure_reason=str(exc),
            )
