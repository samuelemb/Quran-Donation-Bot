from fastapi import APIRouter, HTTPException, status

from quran_donation_bot.app.api.dependencies import AdminAuth, DbSession
from quran_donation_bot.app.schemas.user import UserRead
from quran_donation_bot.app.services.user_service import UserService


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("", response_model=list[UserRead], dependencies=[AdminAuth])
async def list_users(db: DbSession, limit: int = 100, offset: int = 0):
    return UserService(db).list_users(limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserRead, dependencies=[AdminAuth])
async def get_user(user_id: int, db: DbSession):
    user = UserService(db).get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
