from fastapi import APIRouter, HTTPException, status

from quran_donation_bot.app.api.dependencies import AdminAuth, DbSession
from quran_donation_bot.app.schemas.donation import DonationRead, DonationReviewRequest
from quran_donation_bot.app.services.donation_service import DonationService
from quran_donation_bot.app.services.notification_service import NotificationService


router = APIRouter(prefix="/api/v1/donations", tags=["donations"], dependencies=[])


@router.get("/pending", response_model=list[DonationRead], dependencies=[AdminAuth])
async def list_pending_donations(db: DbSession, limit: int = 100, offset: int = 0):
    return DonationService(db).list_pending_donations(limit=limit, offset=offset)


@router.get("/{donation_id}", response_model=DonationRead, dependencies=[AdminAuth])
async def get_donation(donation_id: int, db: DbSession):
    donation = DonationService(db).get_donation(donation_id)
    if donation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
    return donation


@router.patch("/{donation_id}/approve", response_model=DonationRead, dependencies=[AdminAuth])
async def approve_donation(donation_id: int, payload: DonationReviewRequest, db: DbSession):
    service = DonationService(db)
    donation = service.approve_donation(
        donation_id,
        reviewed_by=payload.reviewed_by,
        reason=payload.reason,
        review_notes=payload.review_notes,
    )
    if donation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
    await NotificationService(db).send_donation_approved_message(donation.user.telegram_id, donation)
    return donation


@router.patch("/{donation_id}/reject", response_model=DonationRead, dependencies=[AdminAuth])
async def reject_donation(donation_id: int, payload: DonationReviewRequest, db: DbSession):
    if not payload.reason:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rejection reason is required")
    service = DonationService(db)
    donation = service.reject_donation(
        donation_id,
        reviewed_by=payload.reviewed_by,
        reason=payload.reason,
        review_notes=payload.review_notes,
    )
    if donation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
    await NotificationService(db).send_donation_rejected_message(donation.user.telegram_id, donation, payload.reason)
    return donation
