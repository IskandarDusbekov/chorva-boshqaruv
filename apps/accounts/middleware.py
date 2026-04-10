from django.contrib.auth import login
from django.http import HttpResponseForbidden
from django.urls import Resolver404, resolve

from .selectors import get_valid_access_link
from .services import create_audit_log


class AccessLinkMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        try:
            match = resolve(request.path_info)
        except Resolver404:
            return self.get_response(request)
        token = match.kwargs.get("token") if match else None
        access_link = get_valid_access_link(token=token) if token and match.url_name == "access_with_token" else None

        if token and access_link and access_link.user.is_active:
            request.access_link = access_link
            login(request, access_link.user, backend="django.contrib.auth.backends.ModelBackend")
            if not access_link.ip_address and request.META.get("REMOTE_ADDR"):
                access_link.ip_address = request.META["REMOTE_ADDR"]
                access_link.save(update_fields=["ip_address"])
            create_audit_log(
                user=access_link.user,
                action="middleware_authenticated",
                object_type="AccessLink",
                object_id=str(access_link.pk),
            )

        response = self.get_response(request)
        if token and not getattr(request, "access_link", None) and match.url_name == "access_with_token":
            return HttpResponseForbidden("Access token required.")
        return response
