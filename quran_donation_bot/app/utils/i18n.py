import re

from telegram.ext import ContextTypes

from quran_donation_bot.app.db.repositories.users import UserRepository


TRANSLATIONS = {
    "en": {
        "menu_donate": "📖 Donate Quran",
        "menu_donations": "📊 My Donations",
        "menu_settings": "⚙️ Settings",
        "menu_about": "ℹ️ About Us",
        "menu_help": "❓ Help",
        "menu_feedback": "💬 Send Feedback",
        "menu_cancel": "Cancel",
        "settings_title": "Settings",
        "settings_language": "Language",
        "settings_payment": "Payment Method",
        "settings_quran": "Quran Amount",
        "settings_choose_language": "Choose your preferred language.",
        "settings_language_updated_en": "Language updated to English.",
        "settings_language_updated_ar": "Language updated to Arabic.",
        "settings_language_updated_am": "Language updated to Amharic.",
        "donation_choose_type": "Choose your donation type.",
        "donation_enter_amount": "Please enter the amount of Qurans you want to donate.",
        "plan_one_time": "One-Time Donation",
        "plan_monthly": "Monthly Subscription",
        "plan_three_month": "3-Month Subscription",
        "donation_cancelled": "Donation flow cancelled.",
        "donation_choose_plan": "Please choose a donation type using the buttons above.",
        "donation_invalid_number": "Please enter a valid number.",
        "donation_session_expired": "Donation session expired. Please start again.",
        "donation_no_methods": "No payment methods are available right now. Please try again later.",
        "donation_choose_payment": "Please choose a payment method using the buttons above.",
        "donation_send_screenshot": "Please send your payment screenshot.",
        "donation_sent_for_review": "Your screenshot has been sent for review.",
        "help_title": "How to donate:\n1. Tap Donate Quran.\n2. Enter the number of Qurans.\n3. Choose a payment method.\n4. Pay and send your receipt screenshot.\n\nPayment review:\nYour screenshot is stored as pending until reviewed in the admin portal.\n\nIf approval is delayed:\nPlease wait for review or contact support.\n\nSupport: {support_contact}",
        "about_title": "Quran Donation Bot exists to help donors provide Qurans to rural Muslim children in Tigray.\n\nThe project focuses on clear donation tracking, respectful communication, and an easy giving experience.",
    },
    "ar": {
        "menu_donate": "📖 التبرع بالمصحف",
        "menu_donations": "📊 تبرعاتي",
        "menu_settings": "⚙️ الإعدادات",
        "menu_about": "ℹ️ من نحن",
        "menu_help": "❓ المساعدة",
        "menu_feedback": "💬 إرسال ملاحظات",
        "menu_cancel": "إلغاء",
        "settings_title": "الإعدادات",
        "settings_language": "اللغة",
        "settings_payment": "طريقة الدفع",
        "settings_quran": "عدد المصاحف",
        "settings_choose_language": "اختر اللغة التي تفضّلها.",
        "settings_language_updated_en": "تم تغيير اللغة إلى الإنجليزية.",
        "settings_language_updated_ar": "تم تغيير اللغة إلى العربية.",
        "donation_choose_type": "اختر نوع التبرع المناسب.",
        "donation_enter_amount": "أدخل عدد المصاحف التي ترغب في التبرع بها.",
        "plan_one_time": "تبرع لمرة واحدة",
        "plan_monthly": "اشتراك شهري",
        "plan_three_month": "اشتراك 3 أشهر",
        "donation_cancelled": "تم إلغاء عملية التبرع.",
        "donation_choose_plan": "يرجى اختيار نوع التبرع من الأزرار أعلاه.",
        "donation_invalid_number": "يرجى إدخال رقم صحيح.",
        "donation_session_expired": "انتهت جلسة التبرع. يرجى البدء من جديد.",
        "donation_no_methods": "لا تتوفر طرق دفع حاليًا. يرجى المحاولة مرة أخرى لاحقًا.",
        "donation_choose_payment": "يرجى اختيار طريقة الدفع من الأزرار أعلاه.",
        "donation_send_screenshot": "يرجى إرسال لقطة شاشة لإثبات الدفع.",
        "donation_sent_for_review": "تم إرسال لقطة الشاشة للمراجعة.",
        "help_title": "طريقة التبرع:\n1. اضغط على التبرع بالمصحف.\n2. أدخل عدد المصاحف.\n3. اختر طريقة الدفع.\n4. ادفع ثم أرسل لقطة شاشة الإيصال.\n\nمراجعة الدفع:\nيتم حفظ لقطة الشاشة كمعلّقة إلى أن يراجعها فريق الإدارة.\n\nإذا تأخرت الموافقة:\nيرجى الانتظار قليلًا أو التواصل مع الدعم.\n\nالدعم: {support_contact}",
        "about_title": "أُنشئ بوت التبرع بالمصحف ليسهّل على المتبرعين إيصال المصاحف إلى الأطفال المسلمين في المناطق الريفية في تيغراي.\n\nيركّز المشروع على الوضوح والاحترام وسهولة التبرع.",
    },
    "am": {
        "menu_donate": "📖 ቁርአን ይሰድቁ",
        "menu_donations": "📊 ሰደቃዎቼ",
        "menu_settings": "⚙️ ማስተካከያ",
        "menu_about": "ℹ️ ስለ እኛ",
        "menu_help": "❓ እገዛ",
        "menu_feedback": "💬 አስተያየት ላክ",
        "menu_cancel": "ሰርዝ",
        "settings_title": "ማስተካከያ",
        "settings_language": "ቋንቋ",
        "settings_payment": "የክፍያ ዘዴ",
        "settings_quran": "የቁርአን ብዛት",
        "settings_choose_language": "የሚመርጡትን ቋንቋ ይምረጡ።",
        "settings_language_updated_en": "ቋንቋው ወደ እንግሊዝኛ ተቀይሯል።",
        "settings_language_updated_ar": "ቋንቋው ወደ ዓረብኛ ተቀይሯል።",
        "settings_language_updated_am": "ቋንቋው ወደ አማርኛ ተቀይሯል።",
        "donation_choose_type": "የስደቃ አይነትዎን ይምረጡ።",
        "donation_enter_amount": "ለመሰደቅ የሚፈልጉትን የቁርአን ብዛት ያስገቡ።",
        "plan_one_time": "አንድ ጊዜ ሰደቃ",
        "plan_monthly": "ወርሃዊ ለመሰደቅ",
        "plan_three_month": "በየ 3 ወር ለመሰደቅ",
        "donation_cancelled": "የሰደቃ ሂደቱ ተሰርዟል።",
        "donation_choose_plan": "ከላይ ካሉት አዝራሮች የስደቃ አይነት ይምረጡ።",
        "donation_invalid_number": "እባክዎ ትክክለኛ ቁጥር ያስገቡ።",
        "donation_session_expired": "የሰደቃ ክፍለ ጊዜው አልፏል። እባክዎ እንደገና ይጀምሩ።",
        "donation_no_methods": "በአሁኑ ጊዜ የክፍያ ዘዴዎች አይገኙም። በኋላ ደግሞ ይሞክሩ።",
        "donation_choose_payment": "ከላይ ካሉት አዝራሮች የክፍያ ዘዴ ይምረጡ።",
        "donation_send_screenshot": "እባክዎ የክፍያውን ማረጋገጫ ስክሪንሾት ይላኩ።",
        "donation_sent_for_review": "ስክሪንሾቱ ለግምገማ ተልኳል።",
        "help_title": "የሰደቃ መንገድ:\n1. ቁርአን ይሰድቁን ይጫኑ።\n2. የቁርአን ብዛት ያስገቡ።\n3. የክፍያ ዘዴ ይምረጡ።\n4. ክፍያውን ያጠናቁ እና የደረሰኙን ስክሪንሾት ይላኩ።\n\nየክፍያ ግምገማ:\nስክሪንሾቱ በአስተዳደር ቡድኑ እስኪገመገም ድረስ በመጠባበቅ ላይ ይቆያል።\n\nማጽደቁ ከዘገየ:\nትንሽ ይጠብቁ ወይም ድጋፍን ያነጋግሩ።\n\nድጋፍ: {support_contact}",
        "about_title": "የቁርአን ሰደቃ ቦት ለተለጋሾች በትግራይ የገጠር አካባቢዎች ለሚኖሩ ሙስሊም ህፃናት ቁርአን እንዲደርስ ለማገዝ ተዘጋጅቷል።\n\nፕሮጀክቱ ግልጽነትን፣ አክብሮትን እና ቀላል የሰደቃ ልምድን ያስቀድማል።",
    },
}


def normalize_language(language: str | None) -> str:
    raw = (language or "").lower()
    if raw.startswith("ar"):
        return "ar"
    if raw.startswith("am"):
        return "am"
    return "en"


def t(key: str, language: str | None = None, **kwargs) -> str:
    lang = normalize_language(language)
    template = TRANSLATIONS[lang].get(key) or TRANSLATIONS["en"].get(key) or key
    return template.format(**kwargs)


def rtl(text: str) -> str:
    return f"\u202B{text}\u202C"


def menu_text(key: str, language: str | None = None) -> str:
    return t(f"menu_{key}", language)


def menu_pattern(key: str) -> str:
    variants = {menu_text(key, "en"), menu_text(key, "ar"), menu_text(key, "am")}
    return "^(" + "|".join(re.escape(item) for item in variants) + ")$"


def is_menu_text(text: str | None, key: str) -> bool:
    if text is None:
        return False
    return text in {menu_text(key, "en"), menu_text(key, "ar"), menu_text(key, "am")}


def get_user_language(context: ContextTypes.DEFAULT_TYPE, telegram_id: int | None) -> str:
    if telegram_id is None:
        return "en"

    cache = context.application.bot_data.setdefault("user_language_cache", {})
    cached = cache.get(telegram_id)
    if cached:
        return normalize_language(cached)

    session_factory = context.application.bot_data["session_factory"]
    with session_factory() as session:
        user = UserRepository(session).get_by_telegram_id(telegram_id)
        language = normalize_language(user.language if user is not None else None)

    cache[telegram_id] = language
    return language


def set_user_language(context: ContextTypes.DEFAULT_TYPE, telegram_id: int | None, language: str) -> None:
    if telegram_id is None:
        return
    context.application.bot_data.setdefault("user_language_cache", {})[telegram_id] = normalize_language(language)


def language_prompt() -> str:
    return "Please choose your language.\n\nاختر لغتك.\n\nእባክዎ ቋንቋዎን ይምረጡ።"
