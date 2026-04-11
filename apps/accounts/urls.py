from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("access/", views.access_with_token, name="access_with_token_query"),
    path("access/<str:token>/", views.access_with_token, name="access_with_token"),
    path("telegram-mini-app/", views.telegram_mini_app, name="telegram_mini_app"),
    path("telegram-mini-app/verify/", views.telegram_mini_app_verify, name="telegram_mini_app_verify"),
    path("logout/", views.custom_logout, name="logout"),
    path("forbidden/", views.forbidden, name="forbidden"),
]
