from sqlalchemy.orm import Session

from quran_donation_bot.app.services.admin_user_service import AdminUserService
from quran_donation_bot.app.services.broadcast_service import BroadcastService
from quran_donation_bot.app.services.donation_service import DonationService
from quran_donation_bot.app.services.feedback_service import FeedbackService
from quran_donation_bot.app.services.payment_method_service import PaymentMethodService
from quran_donation_bot.app.services.portal_settings_service import PortalSettingsService
from quran_donation_bot.app.services.user_service import UserService


class AdminService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.admin_users = AdminUserService(session)
        self.broadcasts = BroadcastService(session)
        self.donations = DonationService(session)
        self.payment_methods = PaymentMethodService(session)
        self.portal_settings = PortalSettingsService(session)
        self.users = UserService(session)
        self.feedback = FeedbackService(session)

    def create_broadcast(self, *, message: str) -> dict:
        broadcast = self.broadcasts.create_broadcast(admin_user_id=None, content=message, send_now=False)
        return {"message": broadcast.content, "status": broadcast.status}
