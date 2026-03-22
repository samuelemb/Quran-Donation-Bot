from quran_donation_bot.app.core.constants import PaymentProviderType
from quran_donation_bot.app.schemas.donation import DonationCreate
from quran_donation_bot.app.schemas.payment_method import PaymentMethodCreate
from quran_donation_bot.app.schemas.user import UserCreate
from quran_donation_bot.app.services.donation_service import DonationService
from quran_donation_bot.app.services.payment_method_service import PaymentMethodService


ADMIN_HEADERS = {"X-Admin-Api-Key": "change-me"}


def seed_data(session):
    payment_method = PaymentMethodService(session).create_payment_method(
        PaymentMethodCreate(
            name="CBE",
            provider_type=PaymentProviderType.BANK,
            account_name="Trust",
            account_number="111",
            instructions="Pay exact amount",
            display_order=1,
            is_active=True,
        )
    )
    user = DonationService(session).create_or_get_user(
        UserCreate(telegram_id=2002, username="apiuser", first_name="Fatima")
    )
    donation = DonationService(session).create_pending_donation(
        DonationCreate(
            user_id=user.id,
            payment_method_id=payment_method.id,
            quran_amount=2,
            total_amount=900,
            screenshot_file_id="api-file",
            payment_method_name_snapshot=payment_method.name,
            payment_provider_type_snapshot=payment_method.provider_type,
            account_name_snapshot=payment_method.account_name,
            account_number_snapshot=payment_method.account_number,
            payment_instructions_snapshot=payment_method.instructions,
        )
    )
    return user, payment_method, donation


def test_health_endpoint(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_pending_donations(api_client, session_factory):
    with session_factory() as session:
        seed_data(session)

    response = api_client.get("/api/v1/donations/pending", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_payment_method_crud(api_client):
    create_response = api_client.post(
        "/api/v1/payment-methods",
        headers=ADMIN_HEADERS,
        json={
            "name": "Awash",
            "provider_type": "bank",
            "account_name": "Trust",
            "account_number": "999",
            "instructions": "Send exact amount",
            "display_order": 2,
            "is_active": True,
        },
    )
    assert create_response.status_code == 201
    payment_method_id = create_response.json()["id"]

    update_response = api_client.patch(
        f"/api/v1/payment-methods/{payment_method_id}",
        headers=ADMIN_HEADERS,
        json={"account_number": "1000", "is_active": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["account_number"] == "1000"
    assert update_response.json()["is_active"] is False
