from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AccessLink, AllowedContact, AuditLog, TelegramSession, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "full_name", "phone_number", "role_badge", "is_active", "is_telegram_verified")
    list_filter = ("role", "is_active", "is_staff", "is_telegram_verified")
    search_fields = ("username", "full_name", "phone_number", "telegram_id")
    search_help_text = "Username, ism, telefon yoki Telegram ID bo'yicha qidiring."
    ordering = ("username",)
    list_per_page = 25
    fieldsets = (
        ("Kirish ma'lumotlari", {"fields": ("username", "password")}),
        (
            "Asosiy ma'lumotlar",
            {
                "fields": ("full_name", "phone_number", "telegram_id", "role"),
                "description": "Telefon raqam shu foydalanuvchi uchun ruxsat berilgan raqam hisoblanadi.",
            },
        ),
        (
            "Ruxsatlar va holat",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_phone_verified",
                    "is_telegram_verified",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Muhim sanalar", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            "Yangi foydalanuvchi",
            {
                "classes": ("wide",),
                "fields": ("username", "full_name", "phone_number", "role", "password1", "password2"),
                "description": "Foydalanuvchi shu yerning o'zida yaratiladi. Alohida ruxsat berilgan kontakt kiritish shart emas.",
            },
        ),
    )
    readonly_fields = ("last_login",)

    @admin.display(description="Rol")
    def role_badge(self, obj):
        return obj.get_role_display()


@admin.register(AllowedContact)
class AllowedContactAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone_number", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("full_name", "phone_number")
    search_help_text = "Ism yoki telefon raqam bo'yicha qidiring."
    list_per_page = 25
    readonly_fields = ("created_at", "created_by")


@admin.register(TelegramSession)
class TelegramSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "telegram_id", "chat_id", "is_verified", "last_seen_at")
    search_fields = ("user__username", "telegram_id", "chat_id")
    list_filter = ("is_verified",)
    search_help_text = "Username, Telegram ID yoki chat ID orqali qidiring."
    list_per_page = 25
    readonly_fields = ("first_verified_at", "last_seen_at")
    list_select_related = ("user",)

    def has_add_permission(self, request):
        return False


@admin.register(AccessLink)
class AccessLinkAdmin(admin.ModelAdmin):
    list_display = ("user", "target_path", "expires_at", "is_used", "created_by_bot")
    list_filter = ("is_used", "created_by_bot")
    search_fields = ("user__username", "token", "target_path")
    search_help_text = "Foydalanuvchi, token yoki manzil bo'yicha qidiring."
    list_per_page = 25
    readonly_fields = ("user", "token", "target_path", "expires_at", "is_used", "created_by_bot", "created_at", "ip_address")
    list_select_related = ("user",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "object_type", "object_id", "created_at")
    search_fields = ("action", "object_type", "object_id", "user__username")
    list_filter = ("action", "object_type")
    search_help_text = "Action, obyekt turi yoki foydalanuvchi bo'yicha qidiring."
    list_per_page = 50
    readonly_fields = ("user", "action", "object_type", "object_id", "meta", "created_at")
    list_select_related = ("user",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
