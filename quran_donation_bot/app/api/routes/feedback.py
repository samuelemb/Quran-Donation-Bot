from fastapi import APIRouter

from quran_donation_bot.app.api.dependencies import AdminAuth, DbSession


router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


@router.get("", dependencies=[AdminAuth])
async def list_feedback(db: DbSession):
    from quran_donation_bot.app.services.feedback_service import FeedbackService

    return [
        {
            "id": feedback.id,
            "user_id": feedback.user_id,
            "message": feedback.message,
            "created_at": feedback.created_at,
        }
        for feedback in FeedbackService(db).list_feedback()
    ]
