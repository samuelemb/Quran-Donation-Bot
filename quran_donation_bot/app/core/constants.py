from enum import StrEnum


QURAN_PRICE_BIRR = 450


class MenuButtons(StrEnum):
    DONATE = "📖 Donate Quran"
    DONATIONS = "📊 My Donations"
    SETTINGS = "⚙️ Settings"
    ABOUT = "ℹ️ About Us"
    HELP = "❓ Help"
    FEEDBACK = "💬 Send Feedback"
    CANCEL = "Cancel"
    BACK = "Back"


class DonationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class NotificationDeliveryStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class PaymentProviderType(StrEnum):
    MOBILE_MONEY = "mobile_money"
    BANK = "bank"


class DonationPlanType(StrEnum):
    ONE_TIME = "one_time"
    MONTHLY = "monthly"
    THREE_MONTH = "three_month"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    OVERDUE = "overdue"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class SettingsOption(StrEnum):
    LANGUAGE = "Language"
    PAYMENT_METHOD = "Payment Method"
    QURAN_AMOUNT = "Quran Amount"


DONATION_PLAN, DONATION_QURAN_AMOUNT, DONATION_PAYMENT_METHOD, DONATION_SCREENSHOT = range(4)
SETTINGS_MENU, SETTINGS_QURAN_AMOUNT, SETTINGS_LANGUAGE = range(10, 13)
FEEDBACK_MESSAGE = 20
