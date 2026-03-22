from quran_donation_bot.app.core.constants import PaymentProviderType
from quran_donation_bot.app.db.session import SessionLocal
from quran_donation_bot.app.services.payment_method_service import PaymentMethodService
from quran_donation_bot.app.schemas.payment_method import PaymentMethodCreate


DEFAULT_PAYMENT_METHODS = [
    ("Telebirr", PaymentProviderType.MOBILE_MONEY, "Tigray Quran Trust", "09XX XXX XXX", "Use your name as reference.", 1),
    ("Awash", PaymentProviderType.BANK, "Tigray Quran Trust", "1000 2000 3000", "Send the exact amount.", 2),
    ("CBE", PaymentProviderType.BANK, "Tigray Quran Trust", "1000 2000 3001", "Keep the receipt screenshot.", 3),
    ("Abyssinia", PaymentProviderType.BANK, "Tigray Quran Trust", "1000 2000 3002", "Keep the receipt screenshot.", 4),
    ("Zemzem", PaymentProviderType.BANK, "Tigray Quran Trust", "1000 2000 3003", "Keep the receipt screenshot.", 5),
    ("Hijra", PaymentProviderType.BANK, "Tigray Quran Trust", "1000 2000 3004", "Keep the receipt screenshot.", 6),
    ("Gadda", PaymentProviderType.BANK, "Tigray Quran Trust", "1000 2000 3005", "Keep the receipt screenshot.", 7),
]


def main() -> None:
    with SessionLocal() as session:
        service = PaymentMethodService(session)
        existing = {method.name for method in service.list_payment_methods()}
        for name, provider_type, account_name, account_number, instructions, display_order in DEFAULT_PAYMENT_METHODS:
            if name in existing:
                continue
            service.create_payment_method(
                PaymentMethodCreate(
                    name=name,
                    provider_type=provider_type,
                    account_name=account_name,
                    account_number=account_number,
                    instructions=instructions,
                    display_order=display_order,
                    is_active=True,
                )
            )


if __name__ == "__main__":
    main()
