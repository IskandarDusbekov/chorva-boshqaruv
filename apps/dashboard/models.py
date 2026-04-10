from decimal import Decimal

from django.conf import settings
from django.db import models


class CurrencyChoices(models.TextChoices):
    UZS = "UZS", "UZS"
    USD = "USD", "USD"


class FinanceTypeChoices(models.TextChoices):
    INCOME = "income", "Kirim"
    EXPENSE = "expense", "Chiqim"


class AccountSourceChoices(models.TextChoices):
    DEFAULT = "default", "Default hisob"
    INTERNAL = "internal", "Ichki hisob"
    EXTERNAL = "external", "Tashqi hisob"


class FinanceStatusChoices(models.TextChoices):
    PENDING = "pending", "Kutilmoqda"
    CONFIRMED = "confirmed", "Qabul qilingan"
    CANCELLED = "cancelled", "Bekor qilingan"


class WorkerRoleChoices(models.TextChoices):
    GENERAL = "worker", "Ishchi"
    MILKER = "milker", "Sut sog'uvchi"
    SHEPHERD = "shepherd", "Cho'pon"
    MANAGER = "manager", "Ish boshqaruvchi"


class DailyEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_entries")
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Kunlik yozuv"
        verbose_name_plural = "Kunlik yozuvlar"

    def __str__(self):
        return self.title


class MilkRecord(models.Model):
    record_date = models.DateField(unique=True, verbose_name="Sana")
    morning_liters = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ertalabki sut")
    evening_liters = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Kechki sut")
    price_per_liter = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="1 litr narxi",
        help_text="Sut sotuv narxi. Kirim hisoblashda ishlatiladi.",
    )
    currency = models.CharField(max_length=3, choices=CurrencyChoices.choices, default=CurrencyChoices.UZS)
    note = models.TextField(blank=True, verbose_name="Izoh")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="milk_records",
        verbose_name="Kiritgan foydalanuvchi",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-record_date"]
        verbose_name = "Sut yozuvi"
        verbose_name_plural = "Sut yozuvlari"

    def __str__(self):
        return f"{self.record_date} - {self.total_liters} litr"

    @property
    def total_liters(self):
        return (self.morning_liters or Decimal("0")) + (self.evening_liters or Decimal("0"))

    @property
    def milk_income_amount(self):
        return self.total_liters * (self.price_per_liter or Decimal("0"))


class MilkPrice(models.Model):
    effective_from = models.DateField(verbose_name="Amal qilish sanasi")
    price_per_liter = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="1 litr narxi")
    currency = models.CharField(max_length=3, choices=CurrencyChoices.choices, default=CurrencyChoices.UZS)
    note = models.CharField(max_length=255, blank=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-effective_from", "-created_at"]
        verbose_name = "Sut narxi"
        verbose_name_plural = "Sut narxlari"

    def __str__(self):
        return f"{self.effective_from} - {self.price_per_liter} {self.currency}"


class FinanceCategory(models.Model):
    name = models.CharField(max_length=120, unique=True, verbose_name="Kategoriya nomi")
    entry_type = models.CharField(
        max_length=10,
        choices=FinanceTypeChoices.choices,
        default=FinanceTypeChoices.EXPENSE,
        verbose_name="Turi",
    )
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["entry_type", "name"]
        verbose_name = "Moliya kategoriyasi"
        verbose_name_plural = "Moliya kategoriyalari"

    def __str__(self):
        return f"{self.get_entry_type_display()} - {self.name}"


class WorkerJobType(models.Model):
    name = models.CharField(max_length=120, unique=True, verbose_name="Ish turi nomi")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Ish turi"
        verbose_name_plural = "Ish turlari"

    def __str__(self):
        return self.name


class FinanceEntry(models.Model):
    entry_type = models.CharField(max_length=10, choices=FinanceTypeChoices.choices, verbose_name="Turi")
    category = models.CharField(max_length=120, verbose_name="Kategoriya")
    amount = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Miqdor")
    currency = models.CharField(max_length=3, choices=CurrencyChoices.choices, default=CurrencyChoices.UZS)
    source = models.CharField(
        max_length=10,
        choices=AccountSourceChoices.choices,
        default=AccountSourceChoices.INTERNAL,
        verbose_name="Hisob manbasi",
    )
    status = models.CharField(
        max_length=10,
        choices=FinanceStatusChoices.choices,
        default=FinanceStatusChoices.CONFIRMED,
        verbose_name="Holat",
    )
    entry_date = models.DateField(verbose_name="Sana")
    received_at = models.DateField(null=True, blank=True, verbose_name="Qabul qilingan sana")
    note = models.TextField(blank=True, verbose_name="Izoh")
    related_milk_record = models.ForeignKey(
        MilkRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="finance_entries",
        verbose_name="Bog'liq sut yozuvi",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="finance_entries",
        verbose_name="Kiritgan foydalanuvchi",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-entry_date", "-created_at"]
        verbose_name = "Moliyaviy yozuv"
        verbose_name_plural = "Moliyaviy yozuvlar"

    def __str__(self):
        return f"{self.get_entry_type_display()} - {self.category}"


class Worker(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="Ism familya")
    role = models.CharField(max_length=20, choices=WorkerRoleChoices.choices, default=WorkerRoleChoices.GENERAL, verbose_name="Ish turi")
    job_type = models.ForeignKey(
        WorkerJobType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workers",
        verbose_name="Maxsus ish turi",
    )
    monthly_salary = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Oylik")
    currency = models.CharField(max_length=3, choices=CurrencyChoices.choices, default=CurrencyChoices.UZS)
    started_at = models.DateField(null=True, blank=True, verbose_name="Ish boshlagan sana")
    payday_day = models.PositiveSmallIntegerField(default=30, verbose_name="Oylik beriladigan kun")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    note = models.TextField(blank=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Ishchi"
        verbose_name_plural = "Ishchilar"

    def __str__(self):
        return self.full_name

    @property
    def total_advance(self):
        total = self.advances.aggregate(total=models.Sum("amount"))["total"]
        return total or Decimal("0")

    @property
    def remaining_salary(self):
        return (self.monthly_salary or Decimal("0")) - self.total_advance


class WorkerAdvance(models.Model):
    class PaymentTypeChoices(models.TextChoices):
        ADVANCE = "advance", "Avans"
        SALARY = "salary", "Ish haqi"

    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name="advances", verbose_name="Ishchi")
    amount = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Avans miqdori")
    currency = models.CharField(max_length=3, choices=CurrencyChoices.choices, default=CurrencyChoices.UZS)
    payment_type = models.CharField(
        max_length=10,
        choices=PaymentTypeChoices.choices,
        default=PaymentTypeChoices.ADVANCE,
        verbose_name="To'lov turi",
    )
    month_reference = models.DateField(null=True, blank=True, verbose_name="Qaysi oy uchun")
    advance_date = models.DateField(verbose_name="Sana")
    note = models.TextField(blank=True, verbose_name="Izoh")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="worker_advances",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-advance_date", "-created_at"]
        verbose_name = "Ishchi avansi"
        verbose_name_plural = "Ishchi avanslari"

    def __str__(self):
        return f"{self.worker.full_name} - {self.amount} {self.currency}"


class Report(models.Model):
    STATUS_CHOICES = [
        ("draft", "Qoralama"),
        ("ready", "Tayyor"),
        ("archived", "Arxiv"),
    ]

    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=100)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports")
    date_from = models.DateField()
    date_to = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Hisobot"
        verbose_name_plural = "Hisobotlar"

    def __str__(self):
        return self.title


class ReportItem(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="items")
    entry = models.ForeignKey(DailyEntry, on_delete=models.CASCADE, related_name="report_items")
    summary_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ("report", "entry")
        verbose_name = "Hisobot qatori"
        verbose_name_plural = "Hisobot qatorlari"

    def __str__(self):
        return f"{self.report.title} / {self.entry.title}"
