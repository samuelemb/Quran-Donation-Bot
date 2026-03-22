from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.constants import ParseMode

from quran_donation_bot.app.bot.background import run_db_task
from quran_donation_bot.app.bot.keyboards.inline import start_language_keyboard
from quran_donation_bot.app.bot.keyboards.reply import main_menu_keyboard
from quran_donation_bot.app.schemas.user import UserCreate
from quran_donation_bot.app.services.donation_service import DonationService
from quran_donation_bot.app.services.portal_settings_cache import PortalSettingsCache
from quran_donation_bot.app.utils.formatters import welcome_message
from quran_donation_bot.app.utils.i18n import language_prompt, normalize_language, set_user_language


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return

    session_factory = context.application.bot_data["session_factory"]
    cached_language = context.application.bot_data.setdefault("user_language_cache", {}).get(update.effective_user.id)
    if not cached_language:
        await update.message.reply_text(language_prompt(), reply_markup=start_language_keyboard())
        return

    portal_settings = PortalSettingsCache.get_cached_or_default()
    language = normalize_language(cached_language)

    await update.message.reply_text(
        welcome_message(
            update.effective_user.first_name or "Friend",
            channel_link=portal_settings.telegram_channel_link,
            quran_price_birr=portal_settings.price_per_quran_birr,
            language=language,
        ),
        reply_markup=main_menu_keyboard(language),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

    payload = UserCreate(
        telegram_id=update.effective_user.id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name or "Friend",
        language=language,
    )

    def persist_user() -> None:
        with session_factory() as session:
            PortalSettingsCache.refresh(session)
            DonationService(session).create_or_get_user(payload)

    run_db_task(persist_user)

async def start_language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or update.effective_user is None:
        return

    await query.answer()
    data = query.data or ""
    language = data.split(":")[-1].lower()
    if language not in {"en", "ar", "am"}:
        await query.edit_message_text("Invalid language selection.")
        return

    session_factory = context.application.bot_data["session_factory"]
    payload = UserCreate(
        telegram_id=update.effective_user.id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name or "Friend",
        language=language,
    )
    with session_factory() as session:
        PortalSettingsCache.refresh(session)
        DonationService(session).create_or_get_user(payload)

    set_user_language(context, update.effective_user.id, language)
    portal_settings = PortalSettingsCache.get_cached_or_default()

    try:
        await query.message.delete()
    except Exception:
        await query.edit_message_text("Language selected.")
    if update.effective_chat is not None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome_message(
                update.effective_user.first_name or "Friend",
                channel_link=portal_settings.telegram_channel_link,
                quran_price_birr=portal_settings.price_per_quran_birr,
                language=language,
            ),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=main_menu_keyboard(language),
        )


def get_handler():
    return [
        CommandHandler("start", start_command),
        CallbackQueryHandler(start_language_selected, pattern=r"^start:language:set:(en|ar|am)$"),
    ]
