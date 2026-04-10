from django.utils import timezone

from .models import AccessLink, TelegramSession, User
from .utils import normalize_phone_number, phone_number_candidates


def get_active_allowed_contact(phone_number):
    candidates = phone_number_candidates(phone_number)
    users = User.objects.filter(is_active=True)

    for user in users:
        stored_normalized = normalize_phone_number(user.phone_number)
        if stored_normalized in candidates:
            return user
    return None


def get_user_by_telegram_id(telegram_id):
    return User.objects.filter(telegram_id=telegram_id, is_active=True).first()


def get_active_session(user, telegram_id=None):
    queryset = TelegramSession.objects.filter(user=user, is_verified=True)
    if telegram_id is not None:
        queryset = queryset.filter(telegram_id=telegram_id)
    return queryset.order_by("-last_seen_at").first()


def get_valid_access_link(token):
    return (
        AccessLink.objects.filter(token=token, is_used=False, expires_at__gt=timezone.now())
        .select_related("user")
        .first()
    )
