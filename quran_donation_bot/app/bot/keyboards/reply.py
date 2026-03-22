from telegram import KeyboardButton, ReplyKeyboardMarkup

from quran_donation_bot.app.utils.i18n import menu_text


def main_menu_keyboard(language: str = "en") -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(menu_text("donate", language))],
        [KeyboardButton(menu_text("donations", language)), KeyboardButton(menu_text("settings", language))],
        [KeyboardButton(menu_text("about", language)), KeyboardButton(menu_text("help", language))],
        [KeyboardButton(menu_text("feedback", language))],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def cancel_keyboard(language: str = "en") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[KeyboardButton(menu_text("cancel", language))]], resize_keyboard=True, one_time_keyboard=True)
