from fastapi import APIRouter, HTTPException, status

from quran_donation_bot.app.api.dependencies import AdminAuth, DbSession
from quran_donation_bot.app.schemas.payment_method import PaymentMethodCreate, PaymentMethodRead, PaymentMethodUpdate
from quran_donation_bot.app.services.payment_method_service import PaymentMethodService


router = APIRouter(prefix="/api/v1/payment-methods", tags=["payment-methods"])


@router.get("", response_model=list[PaymentMethodRead], dependencies=[AdminAuth])
async def list_payment_methods(db: DbSession):
    return PaymentMethodService(db).list_payment_methods()


@router.post("", response_model=PaymentMethodRead, status_code=status.HTTP_201_CREATED, dependencies=[AdminAuth])
async def create_payment_method(payload: PaymentMethodCreate, db: DbSession):
    return PaymentMethodService(db).create_payment_method(payload)


@router.patch("/{payment_method_id}", response_model=PaymentMethodRead, dependencies=[AdminAuth])
async def update_payment_method(payment_method_id: int, payload: PaymentMethodUpdate, db: DbSession):
    method = PaymentMethodService(db).update_payment_method(payment_method_id, payload)
    if method is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    return method
