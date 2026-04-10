from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "BotGate boshqaruv paneli"
admin.site.site_title = "BotGate Admin"
admin.site.index_title = "Tizim boshqaruvi"


urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("auth/", include("apps.accounts.urls")),
    path("panel/", include("apps.dashboard.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
