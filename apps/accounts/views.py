import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.utils.cache import patch_cache_control
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import (
    check_rate_limit,
    custom_logout_service,
    get_panel_target_path,
    login_with_access_link,
    validate_access_link,
    verify_telegram_webapp_init_data,
)

logger = logging.getLogger(__name__)


def _auth_client_identifier(request):
    ip_address = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR", "")
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    return f"{ip_address}|{user_agent[:120]}"


def _apply_auth_headers(response, *, clear_site_data=False):
    patch_cache_control(
        response,
        no_cache=True,
        no_store=True,
        must_revalidate=True,
        private=True,
        max_age=0,
    )
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    response["Referrer-Policy"] = "no-referrer"
    if clear_site_data:
        response["Clear-Site-Data"] = "\"cache\", \"cookies\", \"storage\""
    return response


def _too_many_requests_response(*, remaining_seconds, as_json=False):
    message = f"Juda ko'p urinish bo'ldi. {remaining_seconds} soniyadan keyin qayta urinib ko'ring."
    if as_json:
        response = JsonResponse({"ok": False, "error": message}, status=429)
    else:
        response = HttpResponseForbidden(message)
        response.status_code = 429
    response["Retry-After"] = str(remaining_seconds)
    return _apply_auth_headers(response)


@never_cache
def access_link_entry(request):
    response = render(request, "accounts/access_link_entry.html")
    return _apply_auth_headers(response)


@never_cache
def access_with_token(request, token=None):
    remaining = check_rate_limit(
        scope="access-link-direct",
        identifier=_auth_client_identifier(request),
        limit=settings.TOKEN_ACCESS_RATE_LIMIT,
        window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
    )
    if remaining:
        return _too_many_requests_response(remaining_seconds=remaining)

    token = token or request.GET.get("token", "").strip()
    if not token:
        response = HttpResponseForbidden("Havola yaroqsiz yoki eskirgan.")
        return _apply_auth_headers(response)

    try:
        access_link = validate_access_link(
            token=token,
            mark_used=True,
            source_meta={
                "ip_address": request.META.get("REMOTE_ADDR", ""),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "referer": request.META.get("HTTP_REFERER", ""),
            },
        )
    except Exception:
        response = HttpResponseForbidden("Havola yaroqsiz yoki eskirgan.")
        return _apply_auth_headers(response)

    request.access_link = access_link
    login_with_access_link(request, access_link.user)
    response = redirect(access_link.target_path)
    return _apply_auth_headers(response)


@csrf_exempt
@require_POST
@never_cache
def access_link_exchange(request):
    remaining = check_rate_limit(
        scope="access-link-exchange",
        identifier=_auth_client_identifier(request),
        limit=settings.TOKEN_EXCHANGE_RATE_LIMIT,
        window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
    )
    if remaining:
        return _too_many_requests_response(remaining_seconds=remaining, as_json=True)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        response = JsonResponse({"ok": False, "error": "So'rov formati noto'g'ri."}, status=400)
        return _apply_auth_headers(response)

    token = (payload.get("token") or "").strip()
    if not token:
        response = JsonResponse({"ok": False, "error": "Token topilmadi."}, status=400)
        return _apply_auth_headers(response)

    try:
        access_link = validate_access_link(
            token=token,
            mark_used=True,
            source_meta={
                "ip_address": request.META.get("REMOTE_ADDR", ""),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "referer": request.META.get("HTTP_REFERER", ""),
            },
        )
        login_with_access_link(request, access_link.user)
    except PermissionDenied as exc:
        response = JsonResponse({"ok": False, "error": str(exc)}, status=403)
        return _apply_auth_headers(response)
    except Exception:
        logger.exception("Access token exchange jarayonida kutilmagan xatolik yuz berdi.")
        response = JsonResponse({"ok": False, "error": "Havola tekshiruvida xatolik yuz berdi."}, status=500)
        return _apply_auth_headers(response)

    response = JsonResponse({"ok": True, "redirect_url": access_link.target_path})
    return _apply_auth_headers(response)


@login_required
def custom_logout(request):
    custom_logout_service(request)
    response = redirect("accounts:forbidden")
    return _apply_auth_headers(response, clear_site_data=True)


def forbidden(request):
    response = render(request, "accounts/forbidden.html", status=403)
    return _apply_auth_headers(response)


@never_cache
def telegram_mini_app(request):
    response = render(request, "accounts/telegram_mini_app.html")
    return _apply_auth_headers(response)


@csrf_exempt
@require_POST
def telegram_mini_app_verify(request):
    remaining = check_rate_limit(
        scope="mini-app-verify",
        identifier=_auth_client_identifier(request),
        limit=settings.MINI_APP_VERIFY_RATE_LIMIT,
        window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
    )
    if remaining:
        return _too_many_requests_response(remaining_seconds=remaining, as_json=True)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        init_data = payload.get("initData", "")
        user = verify_telegram_webapp_init_data(init_data)
        login_with_access_link(request, user)
    except PermissionDenied as exc:
        response = JsonResponse({"ok": False, "error": str(exc)}, status=403)
        return _apply_auth_headers(response)
    except Exception:
        logger.exception("Mini App verify jarayonida kutilmagan xatolik yuz berdi.")
        response = JsonResponse(
            {"ok": False, "error": "Mini App tekshiruvida server xatoligi yuz berdi. Qayta urinib ko'ring."},
            status=500,
        )
        return _apply_auth_headers(response)

    response = JsonResponse({"ok": True, "redirect_url": get_panel_target_path(user)})
    return _apply_auth_headers(response)
