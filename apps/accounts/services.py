from datetime import timedelta
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from .models import AccessLink, AuditLog, TelegramSession, User, UserRole
from .selectors import get_active_allowed_contact, get_user_by_telegram_id, get_valid_access_link
from .utils import phone_number_candidates


def check_whitelist(phone_number):
    return get_active_allowed_contact(phone_number=phone_number)


def _login_attempt_key(telegram_id):
    return f"first-login-attempt:{telegram_id}"


def _login_lock_key(telegram_id):
    return f"first-login-lock:{telegram_id}"


def get_login_lock_remaining(telegram_id):
    expires_at = cache.get(_login_lock_key(telegram_id))
    if not expires_at:
        return 0
    remaining = int((expires_at - timezone.now()).total_seconds())
    return max(0, remaining)


def register_failed_login_attempt(telegram_id):
    lock_key = _login_lock_key(telegram_id)
    attempt_key = _login_attempt_key(telegram_id)
    max_attempts = settings.FIRST_LOGIN_MAX_ATTEMPTS
    lock_minutes = settings.FIRST_LOGIN_LOCK_MINUTES

    attempts = cache.get(attempt_key, 0) + 1
    cache.set(attempt_key, attempts, timeout=lock_minutes * 60)

    if attempts >= max_attempts:
        expires_at = timezone.now() + timedelta(minutes=lock_minutes)
        cache.set(lock_key, expires_at, timeout=lock_minutes * 60)
        cache.delete(attempt_key)
        return attempts, lock_minutes * 60
    return attempts, 0


def reset_failed_login_attempts(telegram_id):
    cache.delete(_login_attempt_key(telegram_id))
    cache.delete(_login_lock_key(telegram_id))


@transaction.atomic
def authenticate_first_login(*, username, password, telegram_id, chat_id, phone_number="", device_note=""):
    user = authenticate(username=username, password=password)
    if not user or not user.is_active:
        raise PermissionDenied("Username yoki parol noto'g'ri.")
    if phone_number and user.phone_number not in phone_number_candidates(phone_number):
        raise PermissionDenied("Username bu telefon raqamga tegishli emas.")
    if user.telegram_id and user.telegram_id != telegram_id:
        raise PermissionDenied("Bu foydalanuvchi boshqa Telegram akkauntga bog'langan.")

    user.telegram_id = telegram_id
    user.is_telegram_verified = True
    user.is_phone_verified = True
    user.save(update_fields=["telegram_id", "is_telegram_verified", "is_phone_verified", "updated_at"])

    session, created = TelegramSession.objects.get_or_create(
        user=user,
        telegram_id=telegram_id,
        chat_id=chat_id,
        defaults={
            "is_verified": True,
            "first_verified_at": timezone.now(),
            "device_note": device_note,
        },
    )
    if not created:
        session.is_verified = True
        session.device_note = device_note or session.device_note
        if not session.first_verified_at:
            session.first_verified_at = timezone.now()
        session.save(update_fields=["is_verified", "first_verified_at", "device_note", "last_seen_at"])

    create_audit_log(
        user=user,
        action="first_login_verified",
        object_type="TelegramSession",
        object_id=str(session.pk),
        meta={"telegram_id": telegram_id, "chat_id": chat_id},
    )
    return user, session


def bind_telegram_session(*, user, telegram_id, chat_id, device_note=""):
    session, _ = TelegramSession.objects.update_or_create(
        user=user,
        telegram_id=telegram_id,
        chat_id=chat_id,
        defaults={
            "is_verified": True,
            "device_note": device_note,
            "first_verified_at": timezone.now(),
        },
    )
    return session


def generate_access_link(*, user, target_path="/panel/", created_by_bot=True):
    access_link = AccessLink.objects.create(
        user=user,
        token=AccessLink.build_token(),
        target_path=target_path,
        expires_at=AccessLink.default_expiry(),
        created_by_bot=created_by_bot,
    )
    create_audit_log(
        user=user,
        action="access_link_created",
        object_type="AccessLink",
        object_id=str(access_link.pk),
        meta={"target_path": target_path, "expires_at": access_link.expires_at.isoformat()},
    )
    return access_link


def get_panel_target_path(user):
    if user.role in {UserRole.ADMIN, UserRole.MANAGER}:
        return "/panel/admin-dashboard/"
    return "/panel/"


@transaction.atomic
def validate_access_link(*, token, mark_used=True, source_meta=None):
    access_link = get_valid_access_link(token=token)
    if not access_link:
        raise PermissionDenied("Havola yaroqsiz yoki muddati tugagan.")
    if mark_used:
        access_link.is_used = True
        access_link.save(update_fields=["is_used"])
    create_audit_log(
        user=access_link.user,
        action="access_link_used",
        object_type="AccessLink",
        object_id=str(access_link.pk),
        meta={"target_path": access_link.target_path, **(source_meta or {})},
    )
    return access_link


def create_audit_log(*, action, user=None, object_type="", object_id="", meta=None):
    return AuditLog.objects.create(
        user=user,
        action=action,
        object_type=object_type,
        object_id=object_id,
        meta=meta or {},
    )


def login_with_access_link(request, user):
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    create_audit_log(user=user, action="web_login_via_access_link", object_type="User", object_id=str(user.pk))


def custom_logout_service(request):
    user = request.user if isinstance(request.user, User) and request.user.is_authenticated else None
    if user:
        create_audit_log(user=user, action="web_logout", object_type="User", object_id=str(user.pk))
    logout(request)


def _telegram_webapp_secret():
    token = getattr(settings, "BOT_TOKEN", "") or ""
    if not token:
        raise PermissionDenied("BOT_TOKEN sozlanmagan.")
    return hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()


def verify_telegram_webapp_init_data(init_data):
    if not init_data:
        raise PermissionDenied("Mini App ma'lumoti topilmadi.")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    provided_hash = pairs.pop("hash", "")
    if not provided_hash:
        raise PermissionDenied("Hash topilmadi.")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(pairs.items()))
    calculated_hash = hmac.new(
        _telegram_webapp_secret(),
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(calculated_hash, provided_hash):
        raise PermissionDenied("Mini App imzosi noto'g'ri.")

    auth_date_raw = pairs.get("auth_date")
    if not auth_date_raw:
        raise PermissionDenied("auth_date topilmadi.")
    max_age_seconds = 300
    if time.time() - int(auth_date_raw) > max_age_seconds:
        raise PermissionDenied("Mini App sessiyasi eskirgan.")

    user_payload = pairs.get("user")
    if not user_payload:
        raise PermissionDenied("Telegram user ma'lumoti topilmadi.")
    telegram_user = json.loads(user_payload)
    telegram_id = telegram_user.get("id")
    if not telegram_id:
        raise PermissionDenied("Telegram ID topilmadi.")

    user = get_user_by_telegram_id(telegram_id)
    if not user or not user.is_active or not user.is_telegram_verified:
        raise PermissionDenied("Bu Telegram foydalanuvchi tizimda tasdiqlanmagan.")
    if user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        raise PermissionDenied("Mini App faqat admin va manager uchun.")

    session, _ = TelegramSession.objects.get_or_create(
        user=user,
        telegram_id=telegram_id,
        chat_id=telegram_id,
        defaults={"is_verified": True, "first_verified_at": timezone.now(), "device_note": "telegram_webapp"},
    )
    if not session.is_verified:
        session.is_verified = True
    session.device_note = "telegram_webapp"
    session.save(update_fields=["is_verified", "device_note", "last_seen_at"])

    create_audit_log(
        user=user,
        action="mini_app_verified",
        object_type="TelegramSession",
        object_id=str(session.pk),
        meta={"telegram_id": telegram_id},
    )
    return user
