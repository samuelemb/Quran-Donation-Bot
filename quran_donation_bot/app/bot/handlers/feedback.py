from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

from quran_donation_bot.app.bot.background import run_db_task
from quran_donation_bot.app.bot.keyboards.reply import cancel_keyboard, main_menu_keyboard
from quran_donation_bot.app.core.constants import FEEDBACK_MESSAGE
from quran_donation_bot.app.services.donation_service import DonationService
from quran_donation_bot.app.services.feedback_service import FeedbackService
from quran_donation_bot.app.utils.i18n import get_user_language, is_menu_text, menu_pattern


async def feedback_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END
    language = get_user_language(context, update.effective_user.id if update.effective_user else None)
    await update.message.reply_text(
        "Please type your feedback below. Your message will be sent directly to the admin team."
        if language == "en"
        else "يرجى كتابة ملاحظاتك أدناه. سيتم إرسال رسالتك مباشرة إلى فريق الإدارة."
        if language == "ar"
        else "እባክዎ አስተያየትዎን ከታች ይጻፉ። መልዕክትዎ በቀጥታ ወደ አስተዳደር ቡድኑ ይላካል።",
        reply_markup=cancel_keyboard(language),
    )
    if update.effective_user is not None:
        session_factory = context.application.bot_data["session_factory"]
        telegram_id = update.effective_user.id

        def touch_user() -> None:
            with session_factory() as session:
                DonationService(session).touch_user(telegram_id)

        run_db_task(touch_user)
    return FEEDBACK_MESSAGE


async def feedback_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user is None or update.message is None or update.message.text is None:
        return FEEDBACK_MESSAGE
    language = get_user_language(context, update.effective_user.id)

    if is_menu_text(update.message.text, "cancel"):
        await update.message.reply_text(
            "Feedback cancelled."
            if language == "en"
            else "تم إلغاء الملاحظات."
            if language == "ar"
            else "አስተያየቱ ተሰርዟል።",
            reply_markup=main_menu_keyboard(language),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Thank you. Your feedback has been sent."
        if language == "en"
        else "شكرًا لك. تم إرسال ملاحظاتك."
        if language == "ar"
        else "እናመሰግናለን። አስተያየትዎ ተልኳል።",
        reply_markup=main_menu_keyboard(language),
    )

    session_factory = context.application.bot_data["session_factory"]
    telegram_id = update.effective_user.id
    feedback_text = update.message.text.strip()

    def submit_feedback() -> None:
        with session_factory() as session:
            FeedbackService(session).submit_feedback(telegram_id, feedback_text)

    run_db_task(submit_feedback)
    return ConversationHandler.END


def get_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(menu_pattern("feedback")), feedback_start)],
        states={
            FEEDBACK_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_submit)],
        },
        fallbacks=[MessageHandler(filters.Regex(menu_pattern("cancel")), feedback_submit)],
        allow_reentry=True,
    )
