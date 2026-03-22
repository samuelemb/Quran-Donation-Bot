from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from quran_donation_bot.app.bot.background import run_db_task
from quran_donation_bot.app.bot.keyboards.inline import donation_plan_keyboard, payment_methods_keyboard
from quran_donation_bot.app.bot.keyboards.reply import cancel_keyboard, main_menu_keyboard
from quran_donation_bot.app.core.constants import (
    DONATION_PLAN,
    DONATION_PAYMENT_METHOD,
    DONATION_QURAN_AMOUNT,
    DONATION_SCREENSHOT,
    DonationPlanType,
    MenuButtons,
)
from quran_donation_bot.app.db.repositories.subscriptions import SubscriptionRepository
from quran_donation_bot.app.schemas.donation import DonationCreate
from quran_donation_bot.app.services.donation_service import DonationService
from quran_donation_bot.app.services.portal_settings_cache import PortalSettingsCache
from quran_donation_bot.app.utils.formatters import donation_amount_message, payment_instruction_message
from quran_donation_bot.app.utils.i18n import get_user_language, is_menu_text, menu_pattern, t
from quran_donation_bot.app.utils.validators import parse_positive_int


async def donation_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END
    language = get_user_language(context, update.effective_user.id if update.effective_user else None)

    await update.message.reply_text(
        t("donation_choose_type", language),
        reply_markup=donation_plan_keyboard(language),
    )

    if update.effective_user is not None:
        session_factory = context.application.bot_data["session_factory"]
        payment_method_cache = context.application.bot_data["payment_method_cache"]
        telegram_id = update.effective_user.id

        def warm_up_donation_flow() -> None:
            with session_factory() as session:
                PortalSettingsCache.refresh(session)
                DonationService(session).touch_user(telegram_id)
            payment_method_cache.get_active()

        run_db_task(warm_up_donation_flow)

    return DONATION_PLAN


async def donation_plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None:
        return DONATION_PLAN

    await query.answer()
    data = query.data or ""
    try:
        plan_type = DonationPlanType(data.split(":")[-1])
    except ValueError:
        language = get_user_language(context, update.effective_user.id if update.effective_user else None)
        await query.edit_message_text(
            "Invalid donation type selected."
            if language == "en"
            else "تم اختيار نوع تبرع غير صالح."
            if language == "ar"
            else "የተመረጠው የስደቃ አይነት ትክክል አይደለም።"
        )
        return ConversationHandler.END

    context.user_data["donation_plan_type"] = plan_type
    language = get_user_language(context, update.effective_user.id if update.effective_user else None)
    if update.effective_chat is not None:
        try:
            await query.message.delete()
        except Exception:
            await query.edit_message_text("Donation type selected.")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=t("donation_enter_amount", language),
            reply_markup=cancel_keyboard(language),
        )
    return DONATION_QURAN_AMOUNT


async def donation_waiting_for_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return DONATION_PLAN

    language = get_user_language(context, update.effective_user.id if update.effective_user else None)
    if is_menu_text(update.message.text, "cancel"):
        context.user_data.pop("donation_plan_type", None)
        await update.message.reply_text(t("donation_cancelled", language), reply_markup=main_menu_keyboard(language))
        return ConversationHandler.END

    await update.message.reply_text(t("donation_choose_plan", language))
    return DONATION_PLAN


async def donation_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return DONATION_QURAN_AMOUNT

    language = get_user_language(context, update.effective_user.id if update.effective_user else None)
    if is_menu_text(update.message.text, "cancel"):
        await update.message.reply_text(t("donation_cancelled", language), reply_markup=main_menu_keyboard(language))
        return ConversationHandler.END

    quran_amount = parse_positive_int(update.message.text)
    if quran_amount is None:
        await update.message.reply_text(t("donation_invalid_number", language))
        return DONATION_QURAN_AMOUNT

    plan_type = context.user_data.get("donation_plan_type")
    if not isinstance(plan_type, DonationPlanType):
        await update.message.reply_text(t("donation_session_expired", language), reply_markup=main_menu_keyboard(language))
        return ConversationHandler.END

    total_amount = PortalSettingsCache.get_cached_or_default().price_per_quran_birr * quran_amount
    methods = context.application.bot_data["payment_method_cache"].get_active()

    if not methods:
        await update.message.reply_text(
            t("donation_no_methods", language),
            reply_markup=main_menu_keyboard(language),
        )
        return ConversationHandler.END

    context.user_data["donation_quran_amount"] = quran_amount
    context.user_data["donation_total_amount"] = total_amount

    await update.message.reply_text(
        donation_amount_message(quran_amount, total_amount, plan_type, language),
        reply_markup=payment_methods_keyboard(methods),
        parse_mode=ParseMode.HTML,
    )
    return DONATION_PAYMENT_METHOD


async def payment_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None:
        return DONATION_PAYMENT_METHOD

    await query.answer()
    language = get_user_language(context, update.effective_user.id if update.effective_user else None)
    payment_method_id = int((query.data or "").split(":")[-1])

    payment_method = context.application.bot_data["payment_method_cache"].get_by_id(payment_method_id)

    if payment_method is None:
        await query.edit_message_text(
            "Selected payment method is unavailable."
            if language == "en"
            else "طريقة الدفع المحددة غير متاحة."
            if language == "ar"
            else "የተመረጠው የክፍያ ዘዴ አይገኝም።"
        )
        return ConversationHandler.END

    context.user_data["payment_method_id"] = payment_method.id
    context.user_data["payment_method_snapshot"] = {
        "name": payment_method.name,
        "provider_type": payment_method.provider_type,
        "account_name": payment_method.account_name,
        "account_number": payment_method.account_number,
        "instructions": payment_method.instructions,
    }
    total_amount = context.user_data["donation_total_amount"]
    plan_type = context.user_data.get("donation_plan_type", DonationPlanType.ONE_TIME)

    await query.edit_message_text(
        payment_instruction_message(
            amount=total_amount,
            payment_name=payment_method.name,
            account_name=payment_method.account_name,
            account_number=payment_method.account_number,
            instructions=payment_method.instructions,
            language=language,
        ),
        parse_mode=ParseMode.HTML,
    )

    if update.effective_chat is not None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=t("donation_send_screenshot", language),
            reply_markup=cancel_keyboard(language),
        )

    return DONATION_SCREENSHOT


async def donation_now_from_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None or update.effective_user is None:
        return ConversationHandler.END

    await query.answer()
    language = get_user_language(context, update.effective_user.id)
    subscription_id = int((query.data or "").split(":")[-1])

    with context.application.bot_data["session_factory"]() as session:
        subscription = SubscriptionRepository(session).get_by_id(subscription_id)

    if (
        subscription is None
        or subscription.user is None
        or subscription.user.telegram_id != update.effective_user.id
        or subscription.payment_method is None
        or not subscription.payment_method.is_active
    ):
        await query.edit_message_text(
            "Your saved subscription payment details are unavailable. Please start a normal donation."
            if language == "en"
            else "بيانات الدفع المحفوظة لاشتراكك غير متاحة. يرجى بدء تبرع عادي."
            if language == "ar"
            else "የተቀመጠው የደንበኝነት ክፍያ መረጃ አይገኝም። እባክዎ መደበኛ ልገሳ ይጀምሩ።"
        )
        return ConversationHandler.END

    payment_method = subscription.payment_method
    total_amount = int(subscription.monthly_amount)
    context.user_data["donation_plan_type"] = subscription.plan_type
    context.user_data["donation_quran_amount"] = subscription.quran_amount
    context.user_data["donation_total_amount"] = total_amount
    context.user_data["payment_method_id"] = payment_method.id
    context.user_data["payment_method_snapshot"] = {
        "name": payment_method.name,
        "provider_type": payment_method.provider_type,
        "account_name": payment_method.account_name,
        "account_number": payment_method.account_number,
        "instructions": payment_method.instructions,
    }

    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    if update.effective_chat is not None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=payment_instruction_message(
                amount=total_amount,
                payment_name=payment_method.name,
                account_name=payment_method.account_name,
                account_number=payment_method.account_number,
                instructions=payment_method.instructions,
                language=language,
            ),
            parse_mode=ParseMode.HTML,
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=t("donation_send_screenshot", language),
            reply_markup=cancel_keyboard(language),
        )

    return DONATION_SCREENSHOT


async def donation_waiting_for_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return DONATION_PAYMENT_METHOD

    language = get_user_language(context, update.effective_user.id if update.effective_user else None)
    if is_menu_text(update.message.text, "cancel"):
        context.user_data.pop("donation_plan_type", None)
        context.user_data.pop("donation_quran_amount", None)
        context.user_data.pop("donation_total_amount", None)
        await update.message.reply_text(t("donation_cancelled", language), reply_markup=main_menu_keyboard(language))
        return ConversationHandler.END

    await update.message.reply_text(t("donation_choose_payment", language))
    return DONATION_PAYMENT_METHOD


async def donation_screenshot_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user is None or update.message is None or not update.message.photo:
        return DONATION_SCREENSHOT
    language = get_user_language(context, update.effective_user.id)

    payment_method_id = context.user_data.get("payment_method_id")
    payment_method_snapshot = context.user_data.get("payment_method_snapshot")
    quran_amount = context.user_data.get("donation_quran_amount")
    total_amount = context.user_data.get("donation_total_amount")
    plan_type = context.user_data.get("donation_plan_type", DonationPlanType.ONE_TIME)

    if not all([payment_method_id, payment_method_snapshot, quran_amount, total_amount]):
        await update.message.reply_text(t("donation_session_expired", language), reply_markup=main_menu_keyboard(language))
        return ConversationHandler.END

    photo = update.message.photo[-1]

    with context.application.bot_data["session_factory"]() as session:
        service = DonationService(session)
        user = service.touch_user(update.effective_user.id)
        if user is None:
            await update.message.reply_text(
                "Please start the bot first with /start."
                if language == "en"
                else "الرجاء بدء البوت أولًا باستخدام /start."
                if language == "ar"
                else "እባክዎ መጀመሪያ /start በመጠቀም ቦቱን ያስጀምሩ።"
            )
            return ConversationHandler.END
        service.create_pending_donation(
            DonationCreate(
                user_id=user.id,
                payment_method_id=payment_method_id,
                quran_amount=quran_amount,
                total_amount=total_amount,
                screenshot_file_id=photo.file_id,
                payment_method_name_snapshot=payment_method_snapshot["name"],
                payment_provider_type_snapshot=payment_method_snapshot["provider_type"],
                account_name_snapshot=payment_method_snapshot["account_name"],
                account_number_snapshot=payment_method_snapshot["account_number"],
                payment_instructions_snapshot=payment_method_snapshot["instructions"],
                plan_type=plan_type,
            )
        )

    context.user_data.pop("payment_method_id", None)
    context.user_data.pop("payment_method_snapshot", None)
    context.user_data.pop("donation_plan_type", None)
    context.user_data.pop("donation_quran_amount", None)
    context.user_data.pop("donation_total_amount", None)

    await update.message.reply_text(
        t("donation_sent_for_review", language),
        reply_markup=main_menu_keyboard(language),
    )
    return ConversationHandler.END


async def donation_waiting_for_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return DONATION_SCREENSHOT

    language = get_user_language(context, update.effective_user.id if update.effective_user else None)
    if is_menu_text(update.message.text, "cancel"):
        await update.message.reply_text(t("donation_cancelled", language), reply_markup=main_menu_keyboard(language))
        context.user_data.pop("donation_plan_type", None)
        context.user_data.pop("payment_method_id", None)
        context.user_data.pop("payment_method_snapshot", None)
        context.user_data.pop("donation_quran_amount", None)
        context.user_data.pop("donation_total_amount", None)
        return ConversationHandler.END

    await update.message.reply_text(t("donation_send_screenshot", language))
    return DONATION_SCREENSHOT


def get_handler():
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(menu_pattern("donate")), donation_start),
            CallbackQueryHandler(donation_now_from_subscription, pattern=r"^subscription:donate:\d+$"),
        ],
        states={
            DONATION_PLAN: [
                CallbackQueryHandler(donation_plan_selected, pattern=r"^plan:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, donation_waiting_for_plan),
            ],
            DONATION_QURAN_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, donation_amount_received)],
            DONATION_PAYMENT_METHOD: [
                CallbackQueryHandler(payment_method_selected, pattern=r"^pay:\d+$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, donation_waiting_for_payment_method),
            ],
            DONATION_SCREENSHOT: [
                MessageHandler(filters.PHOTO, donation_screenshot_received),
                MessageHandler(filters.TEXT & ~filters.COMMAND, donation_waiting_for_screenshot),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex(menu_pattern("cancel")), donation_waiting_for_screenshot)],
        allow_reentry=True,
    )
