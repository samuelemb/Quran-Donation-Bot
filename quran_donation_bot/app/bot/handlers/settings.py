from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from quran_donation_bot.app.bot.background import run_db_task
from quran_donation_bot.app.bot.keyboards.inline import (
    settings_language_keyboard,
    settings_menu_keyboard,
    settings_payment_methods_keyboard,
)
from quran_donation_bot.app.bot.keyboards.reply import cancel_keyboard, main_menu_keyboard
from quran_donation_bot.app.core.constants import MenuButtons, SETTINGS_LANGUAGE, SETTINGS_MENU, SETTINGS_QURAN_AMOUNT
from quran_donation_bot.app.services.donation_service import DonationService
from quran_donation_bot.app.services.settings_service import SettingsService
from quran_donation_bot.app.utils.i18n import get_user_language, is_menu_text, menu_pattern, set_user_language, t
from quran_donation_bot.app.utils.validators import parse_positive_int


async def settings_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END
    language = get_user_language(context, update.effective_user.id if update.effective_user else None)
    await update.message.reply_text(t("settings_title", language), reply_markup=settings_menu_keyboard(language))
    if update.effective_user is not None:
        session_factory = context.application.bot_data["session_factory"]
        telegram_id = update.effective_user.id

        def touch_user() -> None:
            with session_factory() as session:
                DonationService(session).touch_user(telegram_id)

        run_db_task(touch_user)
    return SETTINGS_MENU


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None or update.effective_user is None:
        return ConversationHandler.END

    await query.answer()
    data = query.data or ""
    language = get_user_language(context, update.effective_user.id)

    if data == "settings:language":
        session_factory = context.application.bot_data["session_factory"]
        current_language = "en"
        with session_factory() as session:
            user = DonationService(session).users.get_by_telegram_id(update.effective_user.id)
            if user is not None and user.language:
                current_language = user.language
        await query.edit_message_text(
            t("settings_choose_language", language),
            reply_markup=settings_language_keyboard(current_language),
        )
        return SETTINGS_LANGUAGE

    if data.startswith("settings:language:set:"):
        language = data.split(":")[-1].lower()
        set_user_language(context, update.effective_user.id, language)
        language_key = {
            "ar": "settings_language_updated_ar",
            "am": "settings_language_updated_am",
        }.get(language, "settings_language_updated_en")
        await query.edit_message_text(t(language_key, language))
        if update.effective_chat is not None:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=t("settings_title", language),
                reply_markup=main_menu_keyboard(language),
            )

        session_factory = context.application.bot_data["session_factory"]
        telegram_id = update.effective_user.id

        def save_language() -> None:
            with session_factory() as session:
                SettingsService(session).update_language(telegram_id, language)

        run_db_task(save_language)
        return ConversationHandler.END

    if data == "settings:payment":
        methods = context.application.bot_data["payment_method_cache"].get_active()
        if not methods:
            await query.edit_message_text(
                "No active payment methods are available right now."
                if language == "en"
                else "لا توجد طرق دفع نشطة متاحة الآن."
                if language == "ar"
                else "በአሁኑ ጊዜ ንቁ የክፍያ ዘዴዎች የሉም።"
            )
            return SETTINGS_MENU
        await query.edit_message_text(
            "Choose your preferred default payment method."
            if language == "en"
            else "اختر طريقة الدفع الافتراضية المفضلة لديك."
            if language == "ar"
            else "የሚመርጡትን ቋሚ የክፍያ ዘዴ ይምረጡ።",
            reply_markup=settings_payment_methods_keyboard(methods),
        )
        return SETTINGS_MENU

    if data.startswith("settings:payment:set:"):
        payment_method_id = int(data.split(":")[-1])
        payment_method = context.application.bot_data["payment_method_cache"].get_by_id(payment_method_id)
        if payment_method is None:
            await query.edit_message_text(
                "Unable to update the payment method."
                if language == "en"
                else "تعذر تحديث طريقة الدفع."
                if language == "ar"
                else "የክፍያ ዘዴውን ማዘመን አልተቻለም።"
            )
            return ConversationHandler.END

        await query.edit_message_text(
            f"Default payment method updated to {payment_method.name}."
            if language == "en"
            else f"تم تحديث طريقة الدفع الافتراضية إلى {payment_method.name}."
            if language == "ar"
            else f"ቋሚ የክፍያ ዘዴዎ ወደ {payment_method.name} ተዘምኗል።",
            reply_markup=None,
        )

        session_factory = context.application.bot_data["session_factory"]
        telegram_id = update.effective_user.id

        def save_payment_method() -> None:
            with session_factory() as session:
                SettingsService(session).update_default_payment_method(telegram_id, payment_method_id)

        run_db_task(save_payment_method)
        return ConversationHandler.END

    if data == "settings:quran":
        await query.edit_message_text(
            "Enter your default Quran amount."
            if language == "en"
            else "أدخل العدد الافتراضي للمصاحف."
            if language == "ar"
            else "ቋሚ የቁርአን ብዛትዎን ያስገቡ።"
        )
        if update.effective_chat is not None:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Send the number of Qurans you want to use as your default amount."
                if language == "en"
                else "أرسل عدد المصاحف الذي تريد استخدامه كعدد افتراضي."
                if language == "ar"
                else "እንደ ቋሚ ለመጠቀም የሚፈልጉትን የቁርአን ብዛት ይላኩ።",
                reply_markup=cancel_keyboard(language),
            )
        return SETTINGS_QURAN_AMOUNT

    return SETTINGS_MENU


async def update_default_quran_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user is None or update.message is None or update.message.text is None:
        return SETTINGS_QURAN_AMOUNT
    language = get_user_language(context, update.effective_user.id)

    if is_menu_text(update.message.text, "cancel"):
        await update.message.reply_text(
            "Settings update cancelled."
            if language == "en"
            else "تم إلغاء تحديث الإعدادات."
            if language == "ar"
            else "የማስተካከያ ለውጡ ተሰርዟል።",
            reply_markup=main_menu_keyboard(language),
        )
        return ConversationHandler.END

    quran_amount = parse_positive_int(update.message.text)
    if quran_amount is None:
        await update.message.reply_text(
            "Please enter a valid number."
            if language == "en"
            else "الرجاء إدخال رقم صحيح."
            if language == "ar"
            else "እባክዎ ትክክለኛ ቁጥር ያስገቡ።"
        )
        return SETTINGS_QURAN_AMOUNT

    await update.message.reply_text(
        f"Default Quran amount updated to {quran_amount}."
        if language == "en"
        else f"تم تحديث العدد الافتراضي للمصاحف إلى {quran_amount}."
        if language == "ar"
        else f"ቋሚ የቁርአን ብዛትዎ ወደ {quran_amount} ተዘምኗል።",
        reply_markup=main_menu_keyboard(language),
    )

    session_factory = context.application.bot_data["session_factory"]
    telegram_id = update.effective_user.id

    def save_quran_amount() -> None:
        with session_factory() as session:
            SettingsService(session).update_default_quran_amount(telegram_id, quran_amount)

    run_db_task(save_quran_amount)
    return ConversationHandler.END


def get_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(menu_pattern("settings")), settings_start)],
        states={
            SETTINGS_MENU: [CallbackQueryHandler(settings_callback, pattern=r"^settings:")],
            SETTINGS_LANGUAGE: [CallbackQueryHandler(settings_callback, pattern=r"^settings:language")],
            SETTINGS_QURAN_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_default_quran_amount)],
        },
        fallbacks=[MessageHandler(filters.Regex(menu_pattern("cancel")), update_default_quran_amount)],
        allow_reentry=True,
    )
