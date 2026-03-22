from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from quran_donation_bot.app.bot.background import run_db_task
from quran_donation_bot.app.services.donation_service import DonationService
from quran_donation_bot.app.utils.formatters import about_message
from quran_donation_bot.app.utils.i18n import get_user_language, menu_pattern


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    language = get_user_language(context, update.effective_user.id if update.effective_user else None)
    await update.message.reply_text(about_message(language))
    if update.effective_user is not None:
        session_factory = context.application.bot_data["session_factory"]
        telegram_id = update.effective_user.id

        def touch_user() -> None:
            with session_factory() as session:
                DonationService(session).touch_user(telegram_id)

        run_db_task(touch_user)


def get_handler():
    return MessageHandler(filters.Regex(menu_pattern("about")), about_handler)
