from datetime import datetime

from pydantic import BaseModel, ConfigDict

from quran_donation_bot.app.core.constants import DonationPlanType, DonationStatus, PaymentProviderType


class DonationCreate(BaseModel):
    user_id: int
    payment_method_id: int
    quran_amount: int
    total_amount: float
    screenshot_file_id: str
    payment_method_name_snapshot: str
    payment_provider_type_snapshot: PaymentProviderType
    account_name_snapshot: str
    account_number_snapshot: str
    payment_instructions_snapshot: str | None = None
    plan_type: DonationPlanType = DonationPlanType.ONE_TIME


class DonationSummaryItem(BaseModel):
    id: int
    plan_type: DonationPlanType
    quran_amount: int
    total_amount: float
    payment_method: str
    status: DonationStatus
    created_at: datetime


class DonationSummary(BaseModel):
    total_qurans: int
    total_amount: float
    donations: list[DonationSummaryItem]


class DonationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    payment_method_id: int
    quran_amount: int
    total_amount: float
    screenshot_file_id: str
    plan_type: DonationPlanType
    payment_method_name_snapshot: str
    account_name_snapshot: str
    account_number_snapshot: str
    payment_instructions_snapshot: str | None
    status: DonationStatus
    created_at: datetime
    reviewed_at: datetime | None
    reviewed_by: str | None
    review_notes: str | None
    rejection_reason: str | None


class DonationReviewRequest(BaseModel):
    reviewed_by: str
    reason: str | None = None
    review_notes: str | None = None
