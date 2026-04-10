from django.http import HttpResponseForbidden
from django.urls import Resolver404, resolve


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
