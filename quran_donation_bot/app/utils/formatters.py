from html import escape

from quran_donation_bot.app.core.config import get_settings
from quran_donation_bot.app.core.constants import DonationPlanType, DonationStatus, QURAN_PRICE_BIRR
from quran_donation_bot.app.schemas.donation import DonationSummary
from quran_donation_bot.app.utils.i18n import normalize_language, rtl, t


def welcome_message(
    name: str,
    *,
    channel_link: str | None = None,
    quran_price_birr: int | None = None,
    language: str = "en",
) -> str:
    settings = get_settings()
    safe_name = escape(name)
    effective_channel_link = settings.channel_link if channel_link is None else channel_link
    effective_channel_link = (effective_channel_link or "").strip()
    effective_quran_price = quran_price_birr or QURAN_PRICE_BIRR
    lang = normalize_language(language)
    updates_line = ""
    if effective_channel_link:
        safe_channel_link = escape(effective_channel_link, quote=True)
        if lang == "ar":
            updates_line = f'\n\nالتحديثات: <a href="{safe_channel_link}">قناتنا</a>'
        elif lang == "am":
            updates_line = f'\n\nለተጨማሪ: <a href="{safe_channel_link}">ቻናላችን</a>'
        else:
            updates_line = f'\n\nUpdates: <a href="{safe_channel_link}">Our Channel</a>'
    if lang == "ar":
        return rtl(
            f"<b>السلام عليكم {safe_name}.</b>\n\n"
            "<b>مرحبًا بك في بوت التبرع بالمصحف.</b>\n\n"
            "هذا البوت مخصّص لتسهيل التبرع بالمصاحف للأطفال المسلمين في المناطق الريفية في تيغراي.\n\n"
            f"<b>سعر المصحف الواحد: {effective_quran_price} بر</b>\n\n"
            "شكرًا لك على دعمك ومساهمتك.\n\n"
            "جزاك الله خيرًا."
            f"{updates_line}"
        )
    if lang == "am":
        return (
            f"<b>ሰላም {safe_name}።</b>\n\n"
            "<b>ወደ የቁርአን ስደቃ ቦት እንኳን ደህና መጡ።</b>\n\n"
            "ይህ ቦት በትግራይ የገጠር አካባቢዎች ለሚኖሩ ሙስሊም ህፃናት ቁርአን ለማድረስ ለሚደረገው ሰደቃ ያግዛል።\n\n"
            f"<b>የአንድ ቁርአን ዋጋ: {effective_quran_price} ብር</b>\n\n"
            "ለድጋፍዎ እና ለሰደቃዎ እናመሰግናለን።\n\n"
            "አላህ ይባርክዎ።"
            f"{updates_line}"
        )
    return (
        f"<b>Assalam Alaikum {safe_name}.</b>\n\n"
        "<b>Welcome to Quran Donation Bot.</b>\n\n"
        "This bot is intended to help people donate Qurans for rural Muslim children in Tigray.\n\n"
        f"<b>1 Quran = {effective_quran_price} Birr</b>\n\n"
        "Thank you for your donation and support.\n\n"
        "May Allah reward your support."
        f"{updates_line}"
    )


def donation_amount_message(quran_amount: int, total_amount: int, plan_type: DonationPlanType, language: str = "en") -> str:
    plan_label = {
        DonationPlanType.ONE_TIME: t("plan_one_time", language),
        DonationPlanType.MONTHLY: t("plan_monthly", language),
        DonationPlanType.THREE_MONTH: t("plan_three_month", language),
    }[plan_type]
    if normalize_language(language) == "ar":
        return rtl(
            f"<b>{plan_label}</b>\n"
            f"قيمة التبرع لـ {quran_amount} مصحف هي <b>{total_amount} بر</b>. يرجى اختيار طريقة الدفع."
        )
    if normalize_language(language) == "am":
        return (
            f"<b>{plan_label}</b>\n"
            f"ለ {quran_amount} ቁርአን የሚከፈለው መጠን <b>{total_amount} ብር</b> ነው። እባክዎ የክፍያ ዘዴ ይምረጡ።"
        )
    return (
        f"<b>{plan_label}</b>\n"
        f"The amount for {quran_amount} Quran(s) is <b>{total_amount} Birr</b>. Please choose a payment method."
    )


def payment_instruction_message(
    *,
    amount: int,
    payment_name: str,
    account_name: str,
    account_number: str,
    instructions: str | None,
    language: str = "en",
) -> str:
    extra = f"\n\nInstructions: {instructions}" if instructions else ""
    if normalize_language(language) == "ar":
        extra = f"\n\nالتعليمات: {instructions}" if instructions else ""
        return rtl(
            f"يرجى إيداع <b>{amount} بر</b> في هذا الحساب ثم إرسال لقطة شاشة لإيصال الدفع.\n\n"
            f"مزود الدفع: {payment_name}\n"
            f"اسم الحساب: {account_name}\n"
            f"رقم الحساب: {account_number}{extra}\n\n"
            "بعد إتمام الدفع، أرسل لقطة الشاشة هنا ليتم التحقق منها."
        )
    if normalize_language(language) == "am":
        extra = f"\n\nመመሪያ: {instructions}" if instructions else ""
        return (
            f"እባክዎ <b>{amount} ብር</b> ወደዚህ ሂሳብ ያስገቡ እና የክፍያውን ደረሰኝ ስክሪንሾት ይላኩ።\n\n"
            f"የክፍያ አቅራቢ: {payment_name}\n"
            f"የሂሳብ ስም: {account_name}\n"
            f"የሂሳብ ቁጥር: {account_number}{extra}\n\n"
            "ክፍያውን ከጨረሱ በኋላ ስክሪንሾቱን እዚህ ይላኩ እንዲመረመር።"
        )
    return (
        f"Please deposit <b>{amount} Birr</b> to this account and send a screenshot of the payment receipt.\n\n"
        f"Provider: {payment_name}\n"
        f"Account Name: {account_name}\n"
        f"Account Number: {account_number}{extra}\n\n"
        "After payment, send your screenshot here for review."
    )


def format_status(status: DonationStatus) -> str:
    return status.value.capitalize()


def donations_summary_message(summary: DonationSummary, language: str = "en") -> str:
    if normalize_language(language) == "ar":
        lines = [
            "ملخص تبرعاتك",
            "",
            f"إجمالي المصاحف المتبرع بها: {summary.total_qurans}",
            f"إجمالي المبلغ المتبرع به: {summary.total_amount:.0f} بر",
            "",
            "سجل التبرعات:",
        ]

        if not summary.donations:
            lines.append("لا توجد تبرعات حتى الآن.")
            return "\n".join(lines)

        status_labels = {
            DonationStatus.PENDING: "قيد المراجعة",
            DonationStatus.APPROVED: "مقبول",
            DonationStatus.REJECTED: "مرفوض",
        }
        for item in summary.donations:
            lines.extend(
                [
                    "",
                    f"- {item.quran_amount} مصحف | {item.total_amount:.0f} بر",
                    f"  طريقة الدفع: {item.payment_method}",
                    f"  التاريخ: {item.created_at.strftime('%Y-%m-%d %H:%M')}",
                    f"  الحالة: {status_labels.get(item.status, item.status.value)}",
                ]
            )
        return rtl("\n".join(lines))
    if normalize_language(language) == "am":
        lines = [
            "የሰደቃዎ ማጠቃለያ",
            "",
            f"ጠቅላላ የተለገሱ ቁርአኖች: {summary.total_qurans}",
            f"ጠቅላላ የተለገሰ ገንዘብ: {summary.total_amount:.0f} ብር",
            "",
            "የሰደቃ ታሪክ:",
        ]
        if not summary.donations:
            lines.append("እስካሁን ምንም ሰደቃ የለም።")
            return "\n".join(lines)
        status_labels = {
            DonationStatus.PENDING: "በመገምገም ላይ",
            DonationStatus.APPROVED: "ጸድቋል",
            DonationStatus.REJECTED: "ተቀባይነት አላገኘም",
        }
        for item in summary.donations:
            lines.extend(
                [
                    "",
                    f"- {item.quran_amount} ቁርአን | {item.total_amount:.0f} ብር",
                    f"  የክፍያ ዘዴ: {item.payment_method}",
                    f"  ቀን: {item.created_at.strftime('%Y-%m-%d %H:%M')}",
                    f"  ሁኔታ: {status_labels.get(item.status, item.status.value)}",
                ]
            )
        return "\n".join(lines)

    lines = [
        "Your donation summary",
        "",
        f"Total Qurans Donated: {summary.total_qurans}",
        f"Total Amount Donated: {summary.total_amount:.0f} Birr",
        "",
        "Donation History:",
    ]

    if not summary.donations:
        lines.append("No donations yet.")
        return "\n".join(lines)

    for item in summary.donations:
        lines.extend(
            [
                "",
                f"- {item.quran_amount} Quran(s) | {item.total_amount:.0f} Birr",
                f"  Method: {item.payment_method}",
                f"  Date: {item.created_at.strftime('%Y-%m-%d %H:%M')}",
                f"  Status: {format_status(item.status)}",
            ]
        )

    return "\n".join(lines)


def about_message(language: str = "en") -> str:
    message = t("about_title", language)
    return rtl(message) if normalize_language(language) == "ar" else message


def help_message(support_contact: str | None = None, language: str = "en") -> str:
    settings = get_settings()
    effective_support_contact = support_contact or settings.support_contact
    message = t("help_title", language, support_contact=effective_support_contact)
    return rtl(message) if normalize_language(language) == "ar" else message
