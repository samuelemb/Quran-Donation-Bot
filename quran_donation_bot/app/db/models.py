from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quran_donation_bot.app.core.constants import (
    DonationPlanType,
    DonationStatus,
    NotificationDeliveryStatus,
    PaymentProviderType,
    SubscriptionStatus,
)
from quran_donation_bot.app.db.base import Base


def enum_values(enum_cls) -> list[str]:
    return [member.value for member in enum_cls]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_interaction_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    default_payment_method_id: Mapped[int | None] = mapped_column(ForeignKey("payment_methods.id", ondelete="SET NULL"))
    default_quran_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)

    default_payment_method: Mapped["PaymentMethod | None"] = relationship(foreign_keys=[default_payment_method_id])
    donations: Mapped[list["Donation"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    subscription: Mapped["Subscription | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    feedback_entries: Mapped[list["Feedback"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notification_logs: Mapped[list["NotificationLog"]] = relationship(back_populates="user")


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    provider_type: Mapped[PaymentProviderType] = mapped_column(
        Enum(PaymentProviderType, name="payment_provider_type", values_callable=enum_values),
        nullable=False,
        default=PaymentProviderType.BANK,
        server_default=PaymentProviderType.BANK.value,
    )
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_number: Mapped[str] = mapped_column(String(100), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    donations: Mapped[list["Donation"]] = relationship(back_populates="payment_method")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="payment_method")


class Donation(Base):
    __tablename__ = "donations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_method_id: Mapped[int] = mapped_column(ForeignKey("payment_methods.id", ondelete="RESTRICT"), nullable=False)
    quran_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    screenshot_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    payment_method_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    payment_provider_type_snapshot: Mapped[PaymentProviderType] = mapped_column(
        Enum(PaymentProviderType, name="payment_provider_type", values_callable=enum_values), nullable=False
    )
    account_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    account_number_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    payment_instructions_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_type: Mapped[DonationPlanType] = mapped_column(
        Enum(DonationPlanType, name="donation_plan_type", values_callable=enum_values),
        nullable=False,
        default=DonationPlanType.ONE_TIME,
        server_default=DonationPlanType.ONE_TIME.value,
    )
    status: Mapped[DonationStatus] = mapped_column(
        Enum(DonationStatus, name="donation_status", values_callable=enum_values),
        nullable=False,
        default=DonationStatus.PENDING,
        server_default=DonationStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="donations")
    payment_method: Mapped["PaymentMethod"] = relationship(back_populates="donations")
    notification_logs: Mapped[list["NotificationLog"]] = relationship(back_populates="donation")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="feedback_entries")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    payment_method_id: Mapped[int | None] = mapped_column(ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True)
    last_donation_id: Mapped[int | None] = mapped_column(ForeignKey("donations.id", ondelete="SET NULL"), nullable=True)
    plan_type: Mapped[DonationPlanType] = mapped_column(
        Enum(DonationPlanType, name="donation_plan_type", values_callable=enum_values),
        nullable=False,
    )
    billing_interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    quran_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status", values_callable=enum_values),
        nullable=False,
        default=SubscriptionStatus.ACTIVE,
        server_default=SubscriptionStatus.ACTIVE.value,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_payment_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="subscription")
    payment_method: Mapped["PaymentMethod | None"] = relationship(back_populates="subscriptions")
    last_donation: Mapped["Donation | None"] = relationship(foreign_keys=[last_donation_id])


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    donation_id: Mapped[int | None] = mapped_column(ForeignKey("donations.id", ondelete="SET NULL"))
    notification_type: Mapped[str] = mapped_column(String(100), nullable=False)
    delivery_status: Mapped[NotificationDeliveryStatus] = mapped_column(
        Enum(NotificationDeliveryStatus, name="notification_delivery_status", values_callable=enum_values),
        nullable=False,
        default=NotificationDeliveryStatus.PENDING,
        server_default=NotificationDeliveryStatus.PENDING.value,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    telegram_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="notification_logs")
    donation: Mapped["Donation | None"] = relationship(back_populates="notification_logs")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="super_admin", server_default="super_admin")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class BroadcastMessage(Base):
    __tablename__ = "broadcast_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_user_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id", ondelete="SET NULL"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", server_default="draft")
    recipient_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    delivered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failure_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PortalSetting(Base):
    __tablename__ = "portal_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_name: Mapped[str] = mapped_column(
        String(255), nullable=False, default="Quran Donation", server_default="Quran Donation"
    )
    support_contact: Mapped[str] = mapped_column(
        String(255), nullable=False, default="support@qurandonation.org", server_default="support@qurandonation.org"
    )
    telegram_channel_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_language: Mapped[str] = mapped_column(String(50), nullable=False, default="English", server_default="English")
    system_timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="(GMT+03:00) East Africa Time - Addis Ababa",
        server_default="(GMT+03:00) East Africa Time - Addis Ababa",
    )
    price_per_quran_birr: Mapped[int] = mapped_column(Integer, nullable=False, default=450, server_default="450")
    minimum_donation_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    notify_new_donations: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    notify_late_payments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    notify_pending_approvals: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
