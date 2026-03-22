from datetime import datetime

from pydantic import BaseModel, ConfigDict

from quran_donation_bot.app.core.constants import PaymentProviderType


class PaymentMethodCreate(BaseModel):
    name: str
    provider_type: PaymentProviderType = PaymentProviderType.BANK
    account_name: str
    account_number: str
    instructions: str | None = None
    display_order: int = 100
    is_active: bool = True


class PaymentMethodUpdate(BaseModel):
    name: str | None = None
    provider_type: PaymentProviderType | None = None
    account_name: str | None = None
    account_number: str | None = None
    instructions: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


class PaymentMethodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    provider_type: PaymentProviderType
    account_name: str
    account_number: str
    instructions: str | None
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
