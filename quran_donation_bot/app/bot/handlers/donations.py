from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from quran_donation_bot.app.bot.background import run_db_task
from quran_donation_bot.app.services.donation_service import DonationService
from quran_donation_bot.app.utils.formatters import donations_summary_message
from quran_donation_bot.app.utils.i18n import get_user_language, menu_pattern


async def donations_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return
    language = get_user_language(context, update.effective_user.id)

    with context.application.bot_data["session_factory"]() as session:
        service = DonationService(session)
        summary = service.get_user_donation_summary(update.effective_user.id)

    if summary is None:
        await update.message.reply_text(
            "Please start the bot first by using /start."
            if language == "en"
            else "الرجاء بدء البوت أولًا باستخدام /start."
        )
        return

    await update.message.reply_text(donations_summary_message(summary, language))

    session_factory = context.application.bot_data["session_factory"]
    telegram_id = update.effective_user.id

    def touch_user() -> None:
        with session_factory() as session:
            DonationService(session).touch_user(telegram_id)

    run_db_task(touch_user)


def get_handler():
    return MessageHandler(filters.Regex(menu_pattern("donations")), donations_handler)
