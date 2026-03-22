from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str
    language: str | None = None


class UserSettingsUpdate(BaseModel):
    default_payment_method_id: int | None = None
    default_quran_amount: int | None = None
    language: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    username: str | None
    first_name: str
    joined_at: datetime
    last_interaction_at: datetime
    is_active: bool
    default_payment_method_id: int | None
    default_quran_amount: int
    language: str | None
