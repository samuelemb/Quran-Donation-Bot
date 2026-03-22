from dataclasses import dataclass
from threading import Lock
from time import monotonic

from quran_donation_bot.app.core.constants import PaymentProviderType
from quran_donation_bot.app.db.session import SessionLocal
from quran_donation_bot.app.services.payment_method_service import PaymentMethodService


@dataclass(slots=True)
class PaymentMethodSnapshot:
    id: int
    name: str
    provider_type: PaymentProviderType
    account_name: str
    account_number: str
    instructions: str | None
    display_order: int


class PaymentMethodCache:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self._lock = Lock()
        self._expires_at = 0.0
        self._items: list[PaymentMethodSnapshot] = []

    def get_active(self) -> list[PaymentMethodSnapshot]:
        now = monotonic()
        with self._lock:
            if self._items and now < self._expires_at:
                return list(self._items)

        with SessionLocal() as session:
            methods = PaymentMethodService(session).list_payment_methods()
            snapshots = [
                PaymentMethodSnapshot(
                    id=method.id,
                    name=method.name,
                    provider_type=method.provider_type,
                    account_name=method.account_name,
                    account_number=method.account_number,
                    instructions=method.instructions,
                    display_order=method.display_order,
                )
                for method in methods
                if method.is_active
            ]

        with self._lock:
            self._items = snapshots
            self._expires_at = monotonic() + self.ttl_seconds
            return list(self._items)

    def get_by_id(self, payment_method_id: int) -> PaymentMethodSnapshot | None:
        return next((item for item in self.get_active() if item.id == payment_method_id), None)

    def invalidate(self) -> None:
        with self._lock:
            self._items = []
            self._expires_at = 0.0
