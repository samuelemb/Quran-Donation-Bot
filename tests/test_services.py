from quran_donation_bot.app.core.constants import PaymentProviderType
from quran_donation_bot.app.schemas.donation import DonationCreate
from quran_donation_bot.app.schemas.payment_method import PaymentMethodCreate
from quran_donation_bot.app.schemas.user import UserCreate
from quran_donation_bot.app.services.donation_service import DonationService
from quran_donation_bot.app.services.feedback_service import FeedbackService
from quran_donation_bot.app.services.payment_method_service import PaymentMethodService
from quran_donation_bot.app.services.settings_service import SettingsService


def create_user_and_method(db_session):
    donation_service = DonationService(db_session)
    payment_method = PaymentMethodService(db_session).create_payment_method(
        PaymentMethodCreate(
            name="Telebirr",
            provider_type=PaymentProviderType.MOBILE_MONEY,
            account_name="Trust",
            account_number="123",
            instructions="Use your name",
            display_order=1,
            is_active=True,
        )
    )
    user = donation_service.create_or_get_user(
        UserCreate(telegram_id=1001, username="user1", first_name="Ahmed")
    )
    return user, payment_method


def test_calculate_total_amount(db_session):
    service = DonationService(db_session)
    assert service.calculate_total_amount(3) == 1350


def test_create_pending_donation_and_summary(db_session):
    user, payment_method = create_user_and_method(db_session)
    service = DonationService(db_session)
    donation = service.create_pending_donation(
        DonationCreate(
            user_id=user.id,
            payment_method_id=payment_method.id,
            quran_amount=2,
            total_amount=900,
            screenshot_file_id="file-1",
            payment_method_name_snapshot=payment_method.name,
            payment_provider_type_snapshot=payment_method.provider_type,
            account_name_snapshot=payment_method.account_name,
            account_number_snapshot=payment_method.account_number,
            payment_instructions_snapshot=payment_method.instructions,
        )
    )
    assert donation.status.value == "pending"
    assert donation.payment_method_name_snapshot == "Telebirr"

    summary = service.get_user_donation_summary(1001)
    assert summary is not None
    assert len(summary.donations) == 1
    assert summary.total_amount == 0


def test_update_settings_and_feedback(db_session):
    user, payment_method = create_user_and_method(db_session)
    SettingsService(db_session).update_default_payment_method(user.telegram_id, payment_method.id)
    SettingsService(db_session).update_default_quran_amount(user.telegram_id, 5)
    updated_user = DonationService(db_session).users.get_by_telegram_id(user.telegram_id)
    assert updated_user is not None
    assert updated_user.default_payment_method_id == payment_method.id
    assert updated_user.default_quran_amount == 5

    feedback = FeedbackService(db_session).submit_feedback(user.telegram_id, "Great project")
    assert feedback is not None


def test_approve_and_reject_donation(db_session):
    user, payment_method = create_user_and_method(db_session)
    service = DonationService(db_session)
    donation = service.create_pending_donation(
        DonationCreate(
            user_id=user.id,
            payment_method_id=payment_method.id,
            quran_amount=1,
            total_amount=450,
            screenshot_file_id="file-2",
            payment_method_name_snapshot=payment_method.name,
            payment_provider_type_snapshot=payment_method.provider_type,
            account_name_snapshot=payment_method.account_name,
            account_number_snapshot=payment_method.account_number,
            payment_instructions_snapshot=payment_method.instructions,
        )
    )
    approved = service.approve_donation(donation.id, reviewed_by="portal-admin", review_notes="ok")
    assert approved is not None
    assert approved.status.value == "approved"
    assert approved.reviewed_by == "portal-admin"

    second = service.create_pending_donation(
        DonationCreate(
            user_id=user.id,
            payment_method_id=payment_method.id,
            quran_amount=1,
            total_amount=450,
            screenshot_file_id="file-3",
            payment_method_name_snapshot=payment_method.name,
            payment_provider_type_snapshot=payment_method.provider_type,
            account_name_snapshot=payment_method.account_name,
            account_number_snapshot=payment_method.account_number,
            payment_instructions_snapshot=payment_method.instructions,
        )
    )
    rejected = service.reject_donation(second.id, reviewed_by="portal-admin", reason="invalid receipt")
    assert rejected is not None
    assert rejected.status.value == "rejected"
    assert rejected.rejection_reason == "invalid receipt"
