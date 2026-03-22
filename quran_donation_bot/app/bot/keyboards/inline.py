from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from quran_donation_bot.app.core.constants import DonationPlanType

from quran_donation_bot.app.db.models import PaymentMethod
from quran_donation_bot.app.utils.i18n import t


def payment_methods_keyboard(payment_methods: list[PaymentMethod]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(method.name, callback_data=f"pay:{method.id}")]
        for method in payment_methods
    ]
    return InlineKeyboardMarkup(buttons)


def donation_plan_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(t("plan_one_time", language), callback_data=f"plan:{DonationPlanType.ONE_TIME.value}")],
        [InlineKeyboardButton(t("plan_monthly", language), callback_data=f"plan:{DonationPlanType.MONTHLY.value}")],
        [InlineKeyboardButton(t("plan_three_month", language), callback_data=f"plan:{DonationPlanType.THREE_MONTH.value}")],
    ]
    return InlineKeyboardMarkup(buttons)


def settings_menu_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(t("settings_language", language), callback_data="settings:language")],
        [InlineKeyboardButton(t("settings_payment", language), callback_data="settings:payment")],
        [InlineKeyboardButton(t("settings_quran", language), callback_data="settings:quran")],
    ]
    return InlineKeyboardMarkup(buttons)


def settings_language_keyboard(current_language: str | None = None) -> InlineKeyboardMarkup:
    effective_language = (current_language or "en").lower()
    buttons = [
        [
            InlineKeyboardButton(
                f"{'• ' if effective_language == 'en' else ''}🇬🇧 English",
                callback_data="settings:language:set:en",
            )
        ],
        [
            InlineKeyboardButton(
                f"{'• ' if effective_language == 'ar' else ''}🇸🇦 العربية",
                callback_data="settings:language:set:ar",
            )
        ],
        [
            InlineKeyboardButton(
                f"{'• ' if effective_language == 'am' else ''}🇪🇹 አማርኛ",
                callback_data="settings:language:set:am",
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def start_language_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="start:language:set:en")],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data="start:language:set:ar")],
        [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="start:language:set:am")],
    ]
    return InlineKeyboardMarkup(buttons)


def settings_payment_methods_keyboard(payment_methods: list[PaymentMethod]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(method.name, callback_data=f"settings:payment:set:{method.id}")]
        for method in payment_methods
    ]
    return InlineKeyboardMarkup(buttons)
