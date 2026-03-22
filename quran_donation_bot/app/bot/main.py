import asyncio
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CallbackContext

from quran_donation_bot.app.bot.handlers import about, donation, donations, feedback, help as help_handler, settings, start
from quran_donation_bot.app.bot.keyboards.reply import main_menu_keyboard
from quran_donation_bot.app.core.config import get_settings
from quran_donation_bot.app.core.logging import setup_logging
from quran_donation_bot.app.db.repositories.users import UserRepository
from quran_donation_bot.app.db.session import SessionLocal
from quran_donation_bot.app.jobs.scheduler import build_scheduler, send_subscription_reminders
from quran_donation_bot.app.services.payment_method_cache import PaymentMethodCache
from quran_donation_bot.app.utils.i18n import get_user_language


logger = logging.getLogger(__name__)


def _preload_user_language_cache(application: Application) -> None:
    session_factory = application.bot_data["session_factory"]
    with session_factory() as session:
        language_map = UserRepository(session).get_language_map()
    application.bot_data["user_language_cache"] = language_map
    logger.info("Preloaded %s user language entries", len(language_map))


async def post_init(application: Application) -> None:
    await asyncio.to_thread(_preload_user_language_cache, application)
    scheduler = build_scheduler()
    if scheduler is None:
        return
    scheduler.add_job(send_subscription_reminders, "interval", hours=6, id="subscription-reminders", replace_existing=True)
    scheduler.start()
    application.bot_data["scheduler"] = scheduler


async def post_shutdown(application: Application) -> None:
    scheduler = application.bot_data.get("scheduler")
    if scheduler is not None:
        scheduler.shutdown(wait=False)


async def bot_error_handler(update: object, context: CallbackContext) -> None:
    logger.exception("Unhandled bot exception", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message is not None:
        language = get_user_language(context, update.effective_user.id if update.effective_user else None)
        await update.effective_message.reply_text(
            "Something went wrong. Please try again in a moment."
            if language == "en"
            else "حدث خطأ ما. يرجى المحاولة مرة أخرى بعد قليل."
            if language == "ar"
            else "አንድ ችግር ተፈጥሯል። እባክዎ ትንሽ ቆይተው ደግመው ይሞክሩ።",
            reply_markup=main_menu_keyboard(language),
        )


def build_application() -> Application:
    settings_obj = get_settings()
    application = (
        Application.builder()
        .token(settings_obj.bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    application.bot_data["session_factory"] = SessionLocal
    application.bot_data["payment_method_cache"] = PaymentMethodCache()
    application.bot_data["user_language_cache"] = {}

    for handler in start.get_handler():
        application.add_handler(handler)
    application.add_handler(donation.get_handler())
    application.add_handler(donations.get_handler())
    application.add_handler(settings.get_handler())
    application.add_handler(about.get_handler())
    application.add_handler(help_handler.get_handler())
    application.add_handler(feedback.get_handler())
    application.add_error_handler(bot_error_handler)
    return application


def main() -> None:
    setup_logging()
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    application = build_application()
    logger.info("Starting Quran Donation Bot")
    application.run_polling(allowed_updates=["message", "callback_query"])
