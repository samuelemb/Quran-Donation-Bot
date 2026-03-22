from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from quran_donation_bot.app.bot.background import run_db_task
from quran_donation_bot.app.core.constants import MenuButtons
from quran_donation_bot.app.services.donation_service import DonationService
from quran_donation_bot.app.services.portal_settings_cache import PortalSettingsCache
from quran_donation_bot.app.utils.formatters import help_message
from quran_donation_bot.app.utils.i18n import get_user_language, menu_pattern


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    language = get_user_language(context, update.effective_user.id if update.effective_user else None)
    session_factory = context.application.bot_data["session_factory"]
    support_contact = None
    with session_factory() as session:
        support_contact = PortalSettingsCache.get(session).support_contact
    await update.message.reply_text(help_message(support_contact=support_contact, language=language))
    if update.effective_user is not None:
        telegram_id = update.effective_user.id

        def touch_user() -> None:
            with session_factory() as session:
                DonationService(session).touch_user(telegram_id)

        run_db_task(touch_user)


def get_handler():
    return MessageHandler(filters.Regex(menu_pattern("help")), help_handler)
