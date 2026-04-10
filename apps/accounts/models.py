import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from .utils import normalize_phone_number


class UserRole(models.TextChoices):
    USER = "user", "Foydalanuvchi"
    MANAGER = "manager", "Menejer"
    ADMIN = "admin", "Administrator"


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        user = self.model(username=username, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault("role", UserRole.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(username=username, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=255, verbose_name="To'liq ism")
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Telefon raqam",
        help_text="Masalan: +998901234567",
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Username",
        help_text="Botdagi birinchi kirish uchun foydalanuvchiga beriladigan login.",
    )
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.USER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    is_telegram_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["phone_number", "full_name"]

    class Meta:
        ordering = ["full_name", "username"]
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.full_name} ({self.username})"

    def save(self, *args, **kwargs):
        self.phone_number = normalize_phone_number(self.phone_number)
        super().save(*args, **kwargs)


class AllowedContact(models.Model):
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Telefon raqam",
        help_text="Masalan: +998901234567",
    )
    full_name = models.CharField(max_length=255, verbose_name="To'liq ism")
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.USER)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_allowed_contacts",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Ruxsat berilgan kontakt"
        verbose_name_plural = "Ruxsat berilgan kontaktlar"

    def __str__(self):
        return f"{self.full_name} - {self.phone_number}"

    def save(self, *args, **kwargs):
        self.phone_number = normalize_phone_number(self.phone_number)
        super().save(*args, **kwargs)


class TelegramSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="telegram_sessions")
    telegram_id = models.BigIntegerField()
    chat_id = models.BigIntegerField()
    is_verified = models.BooleanField(default=False)
    first_verified_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    device_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-last_seen_at"]
        unique_together = ("user", "telegram_id", "chat_id")
        verbose_name = "Telegram sessiya"
        verbose_name_plural = "Telegram sessiyalar"

    def __str__(self):
        return f"{self.user.username} @{self.telegram_id}"


class AccessLink(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="access_links")
    token = models.CharField(max_length=128, unique=True, db_index=True)
    target_path = models.CharField(max_length=255, default="/panel/")
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_bot = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Vaqtinchalik havola"
        verbose_name_plural = "Vaqtinchalik havolalar"

    def __str__(self):
        return f"{self.user.username}:{self.target_path}"

    @classmethod
    def build_token(cls):
        return secrets.token_urlsafe(32)

    @classmethod
    def default_expiry(cls):
        return timezone.now() + timedelta(seconds=settings.ACCESS_LINK_TTL_SECONDS)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit log"
        verbose_name_plural = "Audit loglar"

    def __str__(self):
        return f"{self.action} ({self.created_at:%Y-%m-%d %H:%M})"
