from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.urls import Resolver404, resolve


class SecurityProbeBlockMiddleware:
    """Sezgir fayl va odatiy probe pathlarini 404 bilan yopadi."""

    blocked_fragments = (
        ".env",
        ".git",
        ".sqlite3",
        "db.sqlite3",
        "/logs/",
        ".log",
        ".sql",
        ".bak",
        "phpmyadmin",
        "wp-admin",
        "wp-login",
        "xmlrpc.php",
        "composer.json",
        "package-lock.json",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lowered_path = request.path_info.lower()
        if any(fragment in lowered_path for fragment in self.blocked_fragments):
            return HttpResponseNotFound("Not Found")
        return self.get_response(request)


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

        if match.url_name == "access_with_token" and not match.kwargs.get("token"):
            return HttpResponseForbidden("Access token required.")

        return self.get_response(request)
