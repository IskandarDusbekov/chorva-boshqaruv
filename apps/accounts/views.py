import json
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import (
    custom_logout_service,
    login_with_access_link,
    validate_access_link,
    verify_telegram_webapp_init_data,
)

logger = logging.getLogger(__name__)


def access_with_token(request, token=None):
    token = token or request.GET.get("token", "").strip()
    if not token:
        return HttpResponseForbidden("Havola yaroqsiz yoki eskirgan.")

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
        return HttpResponseForbidden("Havola yaroqsiz yoki eskirgan.")

    request.access_link = access_link
    login_with_access_link(request, access_link.user)
    return redirect(access_link.target_path)


@login_required
def custom_logout(request):
    custom_logout_service(request)
    return redirect("accounts:forbidden")


def forbidden(request):
    return render(request, "accounts/forbidden.html", status=403)


def telegram_mini_app(request):
    return render(request, "accounts/telegram_mini_app.html")


@csrf_exempt
@require_POST
def telegram_mini_app_verify(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        init_data = payload.get("initData", "")
        user = verify_telegram_webapp_init_data(init_data)
        login_with_access_link(request, user)
    except PermissionDenied as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=403)
    except Exception:
        logger.exception("Mini App verify jarayonida kutilmagan xatolik yuz berdi.")
        return JsonResponse(
            {"ok": False, "error": "Mini App tekshiruvida server xatoligi yuz berdi. Qayta urinib ko'ring."},
            status=500,
        )

    return JsonResponse({"ok": True, "redirect_url": "/panel/admin-dashboard/"})
