from django.contrib import admin

from .models import (
    DailyEntry,
    FinanceCategory,
    FinanceEntry,
    MilkPrice,
    MilkRecord,
    Report,
    ReportItem,
    Worker,
    WorkerAdvance,
    WorkerJobType,
)


@admin.register(MilkRecord)
class MilkRecordAdmin(admin.ModelAdmin):
    list_display = ("record_date", "morning_liters", "evening_liters", "total_liters", "price_per_liter", "currency")
    list_filter = ("currency",)
    search_fields = ("record_date", "note")
    list_per_page = 25
    date_hierarchy = "record_date"
    ordering = ("-record_date",)


@admin.register(MilkPrice)
class MilkPriceAdmin(admin.ModelAdmin):
    list_display = ("effective_from", "price_per_liter", "currency", "note")
    list_filter = ("currency",)
    ordering = ("-effective_from",)
    list_per_page = 25


@admin.register(FinanceEntry)
class FinanceEntryAdmin(admin.ModelAdmin):
    list_display = ("entry_date", "entry_type", "category", "amount", "currency", "source", "status")
    list_filter = ("entry_type", "currency", "source", "status")
    search_fields = ("category", "note")
    list_per_page = 25
    date_hierarchy = "entry_date"
    readonly_fields = ("created_at", "created_by", "related_milk_record", "related_worker_payment")
    list_select_related = ("created_by", "related_milk_record", "related_worker_payment")


@admin.register(FinanceCategory)
class FinanceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "entry_type", "is_active")
    list_filter = ("entry_type", "is_active")
    search_fields = ("name",)


@admin.register(WorkerJobType)
class WorkerJobTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_per_page = 25


class WorkerAdvanceInline(admin.TabularInline):
    model = WorkerAdvance
    extra = 0
    readonly_fields = ("created_at", "created_by")


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "role", "monthly_salary", "currency", "started_at", "payday_day", "is_active")
    list_filter = ("role", "currency", "is_active")
    search_fields = ("full_name",)
    inlines = [WorkerAdvanceInline]
    list_per_page = 25
    ordering = ("full_name",)


@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "category", "quantity", "created_at")
    search_fields = ("title", "category", "user__username")
    list_filter = ("category",)
    search_help_text = "Sarlavha, kategoriya yoki foydalanuvchi bo'yicha qidiring."
    list_per_page = 25


class ReportItemInline(admin.TabularInline):
    model = ReportItem
    extra = 0
    verbose_name = "Hisobot qatori"
    verbose_name_plural = "Hisobot qatorlari"
    readonly_fields = ("entry", "summary_value")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "report_type", "created_by", "status", "date_from", "date_to")
    list_filter = ("status", "report_type")
    search_fields = ("title", "created_by__username")
    inlines = [ReportItemInline]
    search_help_text = "Hisobot nomi yoki tuzuvchi bo'yicha qidiring."
    list_per_page = 25
