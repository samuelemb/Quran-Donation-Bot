from __future__ import annotations

from time import monotonic
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from telegram import Bot
from telegram.error import TelegramError

from quran_donation_bot.app.core.config import get_settings
from quran_donation_bot.app.core.constants import PaymentProviderType
from quran_donation_bot.app.db.session import SessionLocal
from quran_donation_bot.app.services.admin_user_service import AdminUserService
from quran_donation_bot.app.services.broadcast_service import BroadcastService
from quran_donation_bot.app.services.donation_service import DonationService
from quran_donation_bot.app.services.feedback_service import FeedbackService
from quran_donation_bot.app.services.notification_service import NotificationService
from quran_donation_bot.app.services.payment_method_service import PaymentMethodService
from quran_donation_bot.app.services.portal_settings_service import PortalSettingsService
from quran_donation_bot.app.services.subscription_service import SubscriptionService
from quran_donation_bot.app.services.user_service import UserService
from quran_donation_bot.app.schemas.payment_method import PaymentMethodCreate, PaymentMethodUpdate


TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
router = APIRouter(tags=["admin-portal"])
_CACHE: dict[str, tuple[float, object]] = {}
LANGUAGE_OPTIONS = ["English", "Amharic", "Tigrinya", "Arabic"]
TIMEZONE_OPTIONS = [
    "(GMT+03:00) East Africa Time - Addis Ababa",
    "(GMT+03:00) East Africa Time - Nairobi",
    "(GMT+00:00) UTC",
]


def _cache_get(key: str, ttl_seconds: int, loader):
    cached = _CACHE.get(key)
    now = monotonic()
    if cached and now - cached[0] < ttl_seconds:
        return cached[1]
    value = loader()
    _CACHE[key] = (now, value)
    return value


def _invalidate_cache(*keys: str) -> None:
    for key in keys:
        _CACHE.pop(key, None)


def _current_admin(request: Request, session=None):
    admin_id = request.session.get("admin_user_id")
    if not admin_id:
        return None
    if session is not None:
        return AdminUserService(session).repository.get_by_id(admin_id)
    with SessionLocal() as local_session:
        return AdminUserService(local_session).repository.get_by_id(admin_id)


def _require_admin(request: Request):
    admin = _current_admin(request)
    if admin is None:
        return RedirectResponse(url="/admin/login", status_code=303)
    return admin


def _base_context(request: Request, title: str, active_nav: str, **extra):
    if "portal_settings" in extra:
        settings = extra.pop("portal_settings")
    else:
        with SessionLocal() as session:
            settings = _cache_get("portal_settings", 60, lambda: PortalSettingsService(session).get_or_create())
    if "current_admin" in extra:
        admin = extra.pop("current_admin")
    else:
        admin = _current_admin(request)
    return {
        "request": request,
        "title": title,
        "active_nav": active_nav,
        "portal_settings": settings,
        "current_admin": admin,
        **extra,
    }


@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    if request.session.get("admin_user_id"):
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse("admin/login.html", _base_context(request, "Admin Login", "login"))


@router.post("/admin/login")
async def admin_login_submit(request: Request):
    form = await request.form()
    email = str(form.get("email", "")).strip()
    password = str(form.get("password", "")).strip()
    with SessionLocal() as session:
        service = AdminUserService(session)
        service.ensure_default_admin()
        admin = service.authenticate(email, password)
    if admin is None:
        return templates.TemplateResponse(
            "admin/login.html",
            _base_context(request, "Admin Login", "login", error="Invalid email or password."),
            status_code=400,
        )
    request.session["admin_user_id"] = admin.id
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/admin/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin

    with SessionLocal() as session:
        donation_service = DonationService(session)
        user_service = UserService(session)
        feedback_service = FeedbackService(session)
        subscription_service = SubscriptionService(session)
        portal_settings = _cache_get("portal_settings", 60, lambda: PortalSettingsService(session).get_or_create())
        dashboard_data = _cache_get(
            "admin_dashboard",
            20,
            lambda: {
                "total_donors": user_service.count_users(),
                "active_subscribers": subscription_service.count_active(),
                "total_qurans": donation_service.donations.get_approved_totals()[0],
                "total_money": donation_service.donations.get_approved_totals()[1],
                "pending_count": donation_service.donations.count_pending(),
                "late_count": subscription_service.count_overdue(),
                "feedback_count": feedback_service.count_feedback(),
                "monthly_series": _monthly_totals(donation_service.donations.get_monthly_totals(months=6)),
            },
        )
        context = _base_context(
            request,
            "Dashboard",
            "dashboard",
            portal_settings=portal_settings,
            current_admin=_current_admin(request, session),
            dashboard=dashboard_data,
        )
    return templates.TemplateResponse("admin/dashboard.html", context)


@router.get("/admin/pending-approvals", response_class=HTMLResponse)
async def admin_pending_approvals(request: Request):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    with SessionLocal() as session:
        pending = DonationService(session).list_pending_donations(limit=50, offset=0)
        context = _base_context(
            request,
            "Pending Approvals",
            "pending",
            portal_settings=_cache_get("portal_settings", 60, lambda: PortalSettingsService(session).get_or_create()),
            current_admin=_current_admin(request, session),
            pending_donations=pending,
        )
    return templates.TemplateResponse("admin/pending_approvals.html", context)


@router.get("/admin/pending-approvals/{donation_id}/screenshot")
async def admin_pending_approval_screenshot(request: Request, donation_id: int):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    with SessionLocal() as session:
        donation = DonationService(session).get_donation(donation_id)
        if donation is None:
            return RedirectResponse(url="/admin/pending-approvals", status_code=303)
        try:
            bot = Bot(token=get_settings().bot_token)
            file = await bot.get_file(donation.screenshot_file_id)
            return RedirectResponse(url=file.file_path, status_code=303)
        except TelegramError:
            return RedirectResponse(url="/admin/pending-approvals", status_code=303)


@router.post("/admin/pending-approvals/{donation_id}/approve")
async def admin_approve_donation(request: Request, donation_id: int):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    with SessionLocal() as session:
        donation_service = DonationService(session)
        donation = donation_service.approve_donation(donation_id, reviewed_by=admin.email, review_notes="Approved in admin portal")
        if donation is not None:
            await NotificationService(session).send_donation_approved_message(donation.user.telegram_id, donation)
    _invalidate_cache("admin_dashboard")
    return RedirectResponse(url="/admin/pending-approvals", status_code=303)


@router.post("/admin/pending-approvals/{donation_id}/reject")
async def admin_reject_donation(request: Request, donation_id: int):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    form = await request.form()
    reason = str(form.get("reason", "Receipt rejected")).strip() or "Receipt rejected"
    with SessionLocal() as session:
        donation_service = DonationService(session)
        donation = donation_service.reject_donation(donation_id, reviewed_by=admin.email, reason=reason, review_notes=reason)
        if donation is not None:
            await NotificationService(session).send_donation_rejected_message(donation.user.telegram_id, donation, reason)
    _invalidate_cache("admin_dashboard")
    return RedirectResponse(url="/admin/pending-approvals", status_code=303)


@router.get("/admin/subscribers", response_class=HTMLResponse)
async def admin_subscribers(request: Request):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    with SessionLocal() as session:
        subscription_service = SubscriptionService(session)
        active_subscriptions = subscription_service.list_active(limit=200, offset=0)
        overdue_subscriptions = subscription_service.list_overdue(limit=200, offset=0)
        context = _base_context(
            request,
            "Subscribers",
            "subscribers",
            portal_settings=_cache_get("portal_settings", 60, lambda: PortalSettingsService(session).get_or_create()),
            current_admin=_current_admin(request, session),
            subscriber_rows=_subscription_rows(active_subscriptions),
            late_rows=_late_subscription_rows(overdue_subscriptions),
        )
    return templates.TemplateResponse("admin/subscribers.html", context)


@router.get("/admin/donations", response_class=HTMLResponse)
async def admin_donations(request: Request):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    with SessionLocal() as session:
        donation_service = DonationService(session)
        donations = donation_service.donations.list_recent(limit=150)
        total_month = donation_service.donations.get_approved_total_since(datetime.now(timezone.utc) - timedelta(days=30))
        average = donation_service.donations.get_approved_average_amount()
        context = _base_context(
            request,
            "Donations",
            "donations",
            portal_settings=_cache_get("portal_settings", 60, lambda: PortalSettingsService(session).get_or_create()),
            current_admin=_current_admin(request, session),
            donation_rows=donations,
            donation_total_month=total_month,
            donation_average=average,
        )
    return templates.TemplateResponse("admin/donations.html", context)


@router.get("/admin/broadcast", response_class=HTMLResponse)
async def admin_broadcast(request: Request):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    try:
        page = max(1, int(request.query_params.get("page", "1")))
    except ValueError:
        page = 1
    page_size = 10
    with SessionLocal() as session:
        payment_methods = PaymentMethodService(session).list_payment_methods()
        broadcast_service = BroadcastService(session)
        broadcasts = broadcast_service.list_broadcasts_page(page=page, page_size=page_size)
        total_broadcasts = broadcast_service.count_broadcasts()
        total_pages = max(1, (total_broadcasts + page_size - 1) // page_size)
        context = _base_context(
            request,
            "Broadcast & Payments",
            "broadcast",
            portal_settings=_cache_get("portal_settings", 60, lambda: PortalSettingsService(session).get_or_create()),
            current_admin=_current_admin(request, session),
            payment_methods=payment_methods,
            broadcasts=broadcasts,
            total_broadcasts=total_broadcasts,
            broadcast_page=page,
            broadcast_total_pages=total_pages,
        )
    return templates.TemplateResponse("admin/broadcast.html", context)


@router.post("/admin/broadcast")
async def admin_broadcast_submit(request: Request):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    form = await request.form()
    content = str(form.get("content", "")).strip()
    if content:
        with SessionLocal() as session:
            await BroadcastService(session).send_broadcast(admin_user_id=admin.id, content=content)
    _invalidate_cache("broadcast_list", "admin_dashboard")
    return RedirectResponse(url="/admin/broadcast", status_code=303)


@router.post("/admin/payment-methods")
async def admin_create_payment_method(request: Request):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    form = await request.form()
    name = str(form.get("name", "")).strip()
    account_name = str(form.get("account_name", "")).strip()
    account_number = str(form.get("account_number", "")).strip()
    instructions = str(form.get("instructions", "")).strip() or None
    provider_type_raw = str(form.get("provider_type", PaymentProviderType.BANK.value)).strip()
    try:
        provider_type = PaymentProviderType(provider_type_raw)
    except ValueError:
        provider_type = PaymentProviderType.BANK
    display_order_raw = str(form.get("display_order", "100")).strip()
    try:
        display_order = int(display_order_raw)
    except ValueError:
        display_order = 100
    is_active = form.get("is_active") == "on"

    if name and account_name and account_number:
        payload = PaymentMethodCreate(
            name=name,
            provider_type=provider_type,
            account_name=account_name,
            account_number=account_number,
            instructions=instructions,
            display_order=display_order,
            is_active=is_active,
        )
        with SessionLocal() as session:
            PaymentMethodService(session).create_payment_method(payload)
    _invalidate_cache("portal_settings")
    return RedirectResponse(url="/admin/broadcast", status_code=303)


@router.post("/admin/payment-methods/{payment_method_id}")
async def admin_update_payment_method(request: Request, payment_method_id: int):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    form = await request.form()
    provider_type_raw = str(form.get("provider_type", PaymentProviderType.BANK.value)).strip()
    try:
        provider_type = PaymentProviderType(provider_type_raw)
    except ValueError:
        provider_type = PaymentProviderType.BANK
    display_order_raw = str(form.get("display_order", "100")).strip()
    try:
        display_order = int(display_order_raw)
    except ValueError:
        display_order = 100

    payload = PaymentMethodUpdate(
        name=str(form.get("name", "")).strip() or None,
        provider_type=provider_type,
        account_name=str(form.get("account_name", "")).strip() or None,
        account_number=str(form.get("account_number", "")).strip() or None,
        instructions=str(form.get("instructions", "")).strip() or None,
        display_order=display_order,
        is_active=form.get("is_active") == "on",
    )
    with SessionLocal() as session:
        PaymentMethodService(session).update_payment_method(payment_method_id, payload)
    _invalidate_cache("portal_settings")
    return RedirectResponse(url="/admin/broadcast", status_code=303)


@router.get("/admin/feedback", response_class=HTMLResponse)
async def admin_feedback(request: Request):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    with SessionLocal() as session:
        feedback_items = FeedbackService(session).list_feedback()[:100]
        context = _base_context(
            request,
            "Feedback",
            "feedback",
            portal_settings=_cache_get("portal_settings", 60, lambda: PortalSettingsService(session).get_or_create()),
            current_admin=_current_admin(request, session),
            feedback_items=feedback_items,
        )
    return templates.TemplateResponse("admin/feedback.html", context)


@router.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(request: Request):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    with SessionLocal() as session:
        settings = _cache_get("portal_settings", 60, lambda: PortalSettingsService(session).get_or_create())
        admins = _cache_get("portal_admins", 60, lambda: AdminUserService(session).list_admins())
        context = _base_context(
            request,
            "Settings",
            "settings",
            portal_settings=settings,
            current_admin=_current_admin(request, session),
            settings_model=settings,
            admin_rows=admins,
            language_options=LANGUAGE_OPTIONS,
            timezone_options=TIMEZONE_OPTIONS,
        )
    return templates.TemplateResponse("admin/settings.html", context)


@router.post("/admin/settings/general")
async def admin_settings_general(request: Request):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    form = await request.form()
    default_language = str(form.get("default_language", "English")).strip() or "English"
    if default_language not in LANGUAGE_OPTIONS:
        default_language = "English"
    system_timezone = str(form.get("system_timezone", "")).strip() or "(GMT+03:00) East Africa Time - Addis Ababa"
    if system_timezone not in TIMEZONE_OPTIONS:
        system_timezone = "(GMT+03:00) East Africa Time - Addis Ababa"
    payload = {
        "support_contact": str(form.get("support_contact", "")).strip(),
        "telegram_channel_link": str(form.get("telegram_channel_link", "")).strip(),
        "default_language": default_language,
        "system_timezone": system_timezone,
        "price_per_quran_birr": int(form.get("price_per_quran_birr", 450)),
        "notify_new_donations": form.get("notify_new_donations") == "on",
        "notify_late_payments": form.get("notify_late_payments") == "on",
        "notify_pending_approvals": form.get("notify_pending_approvals") == "on",
    }
    with SessionLocal() as session:
        PortalSettingsService(session).update(**payload)
    _invalidate_cache("portal_settings")
    return RedirectResponse(url="/admin/settings", status_code=303)


@router.post("/admin/settings/password")
async def admin_change_password(request: Request):
    admin = _require_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    form = await request.form()
    new_password = str(form.get("new_password", "")).strip()
    if new_password:
        with SessionLocal() as session:
            AdminUserService(session).change_password(admin.id, new_password)
    _invalidate_cache("portal_admins")
    return RedirectResponse(url="/admin/settings", status_code=303)


def _subscription_rows(subscriptions):
    rows = []
    for subscription in subscriptions:
        rows.append(
            {
                "user": subscription.user,
                "qurans_subscribed": subscription.quran_amount,
                "monthly_amount": float(subscription.monthly_amount),
                "payment_method": subscription.payment_method.name if subscription.payment_method else "Not set",
                "next_payment_date": subscription.next_payment_due_at,
                "status": subscription.status.value.title(),
            }
        )
    return rows


def _late_subscription_rows(subscriptions):
    rows = []
    now = datetime.now(timezone.utc)
    for subscription in subscriptions:
        days_overdue = (now.date() - subscription.next_payment_due_at.date()).days
        rows.append(
            {
                "user": subscription.user,
                "qurans_subscribed": subscription.quran_amount,
                "monthly_amount": float(subscription.monthly_amount),
                "payment_method": subscription.payment_method.name if subscription.payment_method else "Not set",
                "next_payment_date": subscription.next_payment_due_at,
                "status": subscription.status.value.title(),
                "days_overdue": days_overdue,
            }
        )
    return rows


def _monthly_totals(monthly_rows: list[tuple[str, float]]):
    peak = max((total for _, total in monthly_rows), default=0)
    rows = []
    for month, value in monthly_rows:
        height = 24 if peak == 0 or value == 0 else max(24, round((value / peak) * 220))
        rows.append({"label": month, "value": value, "height": height})
    return rows
