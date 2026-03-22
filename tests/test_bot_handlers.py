from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from quran_donation_bot.app.bot.handlers.donation import (
    donation_amount_received,
    donation_screenshot_received,
    donation_waiting_for_screenshot,
)
from quran_donation_bot.app.bot.handlers.feedback import feedback_submit
from quran_donation_bot.app.core.constants import DONATION_PAYMENT_METHOD, DONATION_QURAN_AMOUNT, DONATION_SCREENSHOT
from quran_donation_bot.app.core.constants import PaymentProviderType
from quran_donation_bot.app.schemas.payment_method import PaymentMethodCreate
from quran_donation_bot.app.schemas.user import UserCreate
from quran_donation_bot.app.services.donation_service import DonationService
from quran_donation_bot.app.services.payment_method_service import PaymentMethodService


def make_context(session_factory):
    return SimpleNamespace(
        application=SimpleNamespace(bot_data={"session_factory": session_factory}),
        user_data={},
        bot=SimpleNamespace(send_message=AsyncMock()),
    )


def make_update(*, text=None, photo=None, telegram_id=3003):
    message = SimpleNamespace(
        text=text,
        photo=photo,
        reply_text=AsyncMock(),
    )
    return SimpleNamespace(
        message=message,
        effective_user=SimpleNamespace(id=telegram_id, username="botuser", first_name="Ali"),
        effective_chat=SimpleNamespace(id=telegram_id),
    )


@pytest.mark.asyncio
async def test_invalid_quran_amount_recovery(session_factory):
    context = make_context(session_factory)
    update = make_update(text="abc")
    state = await donation_amount_received(update, context)
    assert state == DONATION_QURAN_AMOUNT
    update.message.reply_text.assert_awaited()


@pytest.mark.asyncio
async def test_donation_amount_to_payment_method(session_factory):
    with session_factory() as session:
        PaymentMethodService(session).create_payment_method(
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

    context = make_context(session_factory)
    update = make_update(text="2")
    state = await donation_amount_received(update, context)
    assert state == DONATION_PAYMENT_METHOD
    assert context.user_data["donation_quran_amount"] == 2


@pytest.mark.asyncio
async def test_unsupported_message_while_waiting_for_screenshot(session_factory):
    context = make_context(session_factory)
    update = make_update(text="hello")
    state = await donation_waiting_for_screenshot(update, context)
    assert state == DONATION_SCREENSHOT
    update.message.reply_text.assert_awaited()


@pytest.mark.asyncio
async def test_feedback_flow(session_factory):
    with session_factory() as session:
        DonationService(session).create_or_get_user(UserCreate(telegram_id=3003, username="botuser", first_name="Ali"))

    context = make_context(session_factory)
    update = make_update(text="This is useful")
    state = await feedback_submit(update, context)
    assert state == -1


@pytest.mark.asyncio
async def test_screenshot_creates_pending_donation(session_factory):
    with session_factory() as session:
        payment_method = PaymentMethodService(session).create_payment_method(
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
        DonationService(session).create_or_get_user(UserCreate(telegram_id=3003, username="botuser", first_name="Ali"))

    photo = [SimpleNamespace(file_id="small"), SimpleNamespace(file_id="largest")]
    context = make_context(session_factory)
    context.user_data["payment_method_id"] = payment_method.id
    context.user_data["donation_quran_amount"] = 2
    context.user_data["donation_total_amount"] = 900
    update = make_update(photo=photo)
    state = await donation_screenshot_received(update, context)
    assert state == -1
