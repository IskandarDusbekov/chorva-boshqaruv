"""Dashboard sahifalari, modallar va boshqaruv actionlari."""

from calendar import monthrange
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import AuditLog
from apps.accounts.models import UserRole
from apps.accounts.services import create_audit_log

from .forms import FinanceEntryForm, MilkPriceForm, MilkRecordForm, WorkerAdvanceForm, WorkerForm
from .models import AccountSourceChoices, FinanceEntry, FinanceStatusChoices, MilkRecord, Worker, WorkerAdvance
from .selectors import (
    filter_finance_entries,
    filter_worker_payments,
    finance_totals_by_category,
    get_dashboard_overview,
    get_period_report,
    get_worker_payroll_summary,
)
from .services import (
    create_finance_entry,
    create_milk_income_from_record,
    create_milk_price,
    create_milk_record,
    create_worker_advance,
    delete_worker_payment_finance_entry,
    mark_milk_payment_received,
    sync_worker_payment_finance_entry,
    _worker_payment_snapshot,
)


MONTH_CHOICES = [
    (1, "Yanvar"),
    (2, "Fevral"),
    (3, "Mart"),
    (4, "Aprel"),
    (5, "May"),
    (6, "Iyun"),
    (7, "Iyul"),
    (8, "Avgust"),
    (9, "Sentabr"),
    (10, "Oktabr"),
    (11, "Noyabr"),
    (12, "Dekabr"),
]


def _today():
    """Joriy sanani qaytaradi."""
    return timezone.now().date()


def _parse_date(value, fallback):
    """GET yoki POST dan kelgan sanani xavfsiz parse qiladi."""
    if not value:
        return fallback
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return fallback


def _redirect_back(request, fallback_name):
    """Forma yuborilgandan keyin foydalanuvchini avvalgi sahifaga qaytaradi."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(fallback_name)


def _parse_year(value):
    """Yil qiymatini butun songa aylantiradi."""
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def _parse_int(value):
    """Butun son kerak bo'lgan filtrlarda xatoni yutib yuboradi."""
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def _apply_year_month_period(date_from, date_to, year=None, month=None):
    """Yil va oy filteridan aniq sana oralig'ini yasaydi."""
    if year and month and 1 <= month <= 12:
        last_day = monthrange(year, month)[1]
        return datetime(year, month, 1).date(), datetime(year, month, last_day).date()
    if year:
        return datetime(year, 1, 1).date(), datetime(year, 12, 31).date()
    return date_from, date_to


def _date_range_query(date_from, date_to):
    """Pagination va linklar uchun sana query satrini qaytaradi."""
    return f"&date_from={date_from:%Y-%m-%d}&date_to={date_to:%Y-%m-%d}"


def _finance_query(date_from, date_to, year=None, month=None):
    """Moliya sahifasidagi filterlarni pagination bilan saqlab qoladi."""
    return (
        f"&date_from={date_from:%Y-%m-%d}&date_to={date_to:%Y-%m-%d}"
        f"&year={year or ''}&month={month or ''}"
    )


def _payment_query(date_from, date_to, year=None, month=None, worker_id=None):
    """Ishchi to'lovlari filtrlari uchun query satrini tayyorlaydi."""
    return (
        f"&worker_id={worker_id or ''}"
        f"&payment_date_from={date_from:%Y-%m-%d}&payment_date_to={date_to:%Y-%m-%d}"
        f"&payment_year={year or ''}&payment_month={month or ''}"
    )


def _audit_action(user, action, object_type, object_id="", meta=None):
    """Web paneldagi muhim o'zgarishlarni audit logga yozadi."""
    create_audit_log(
        user=user,
        action=action,
        object_type=object_type,
        object_id=str(object_id or ""),
        meta=meta or {},
    )


def _recent_logs():
    """Dashboard uchun audit log querysetini qaytaradi."""
    return AuditLog.objects.select_related("user").order_by("-created_at")


@login_required
def home(request):
    """Asosiy dashboard: kartalar, grafiklar va loglarni chiqaradi."""
    today = _today()
    date_from = _parse_date(request.GET.get("date_from"), today - timedelta(days=6))
    date_to = _parse_date(request.GET.get("date_to"), today)
    overview = get_dashboard_overview(date_from, date_to)
    logs_page_obj = Paginator(_recent_logs(), 10).get_page(request.GET.get("logs_page"))

    context = {
        "stats": overview,
        "worker_payroll": get_worker_payroll_summary(),
        "date_from": date_from,
        "date_to": date_to,
        "date_query_suffix": _date_range_query(date_from, date_to),
        "milk_price_form": MilkPriceForm(initial={"effective_from": today}),
        "milk_form": MilkRecordForm(initial={"record_date": today}),
        "finance_form": FinanceEntryForm(initial={"entry_date": today}),
        "worker_form": WorkerForm(),
        "advance_form": WorkerAdvanceForm(initial={"advance_date": today, "month_reference": today.replace(day=1)}),
        "logs_page_obj": logs_page_obj,
        "role": request.user.role,
        "nav_active": "home",
    }
    return render(request, "dashboard/home.html", context)


@login_required
def milk_page(request):
    """Sut boshqaruvi sahifasi va unga tegishli modal ma'lumotlar."""
    today = _today()
    date_from = _parse_date(request.GET.get("date_from"), today - timedelta(days=30))
    date_to = _parse_date(request.GET.get("date_to"), today)
    stats = get_dashboard_overview(date_from, date_to)
    milk_records = MilkRecord.objects.order_by("-record_date")
    context = {
        "stats": stats,
        "date_from": date_from,
        "date_to": date_to,
        "date_query_suffix": _date_range_query(date_from, date_to),
        "milk_form": MilkRecordForm(initial={"record_date": today}),
        "milk_price_form": MilkPriceForm(initial={"effective_from": today}),
        "milk_page_obj": Paginator(milk_records, 10).get_page(request.GET.get("page")),
        "pending_page_obj": Paginator(stats["pending_milk_entries"], 8).get_page(request.GET.get("pending_page")),
        "current_month_total": sum(
            item.total_liters for item in MilkRecord.objects.filter(record_date__year=today.year, record_date__month=today.month)
        ),
        "edit_item": None,
        "nav_active": "milk",
    }
    return render(request, "dashboard/milk_page.html", context)


@login_required
def entry_list(request):
    today = _today()
    context = get_period_report(today - timedelta(days=30), today)
    return render(request, "dashboard/entry_list.html", context)


@login_required
def entry_create(request):
    if request.method == "POST":
        form = MilkRecordForm(request.POST)
        if form.is_valid():
            milk_record = create_milk_record(user=request.user, **form.cleaned_data)
            pending_entry = create_milk_income_from_record(user=request.user, milk_record=milk_record)
            _audit_action(
                request.user,
                "milk_record_created",
                "MilkRecord",
                milk_record.pk,
                {"date": str(milk_record.record_date), "liters": str(milk_record.total_liters)},
            )
            if pending_entry.amount > 0:
                messages.success(request, "Sut yozuvi saqlandi va default hisobga kutilayotgan to'lov sifatida qo'shildi.")
            else:
                messages.warning(request, "Sut yozuvi saqlandi, lekin aktiv sut narxi topilmadi. Narx belgilang, shunda summa hisoblanadi.")
        else:
            messages.error(request, f"Sut yozuvini saqlab bo'lmadi: {form.errors.as_text()}")
    return _redirect_back(request, "dashboard:milk_page")


@login_required
def milk_edit(request, pk):
    item = get_object_or_404(MilkRecord, pk=pk)
    if request.method == "POST":
        form = MilkRecordForm(request.POST, instance=item)
        if form.is_valid():
            create_milk_record(user=request.user, **form.cleaned_data)
            create_milk_income_from_record(user=request.user, milk_record=item)
            _audit_action(
                request.user,
                "milk_record_updated",
                "MilkRecord",
                item.pk,
                {"date": str(item.record_date), "liters": str(item.total_liters)},
            )
            return redirect("dashboard:milk_page")
    else:
        form = MilkRecordForm(instance=item)
    today = _today()
    stats = get_dashboard_overview(today - timedelta(days=30), today)
    milk_records = MilkRecord.objects.order_by("-record_date")
    context = {
        "stats": stats,
        "date_from": today - timedelta(days=30),
        "date_to": today,
        "date_query_suffix": _date_range_query(today - timedelta(days=30), today),
        "milk_form": form,
        "milk_price_form": MilkPriceForm(initial={"effective_from": today}),
        "milk_page_obj": Paginator(milk_records, 10).get_page(request.GET.get("page")),
        "pending_page_obj": Paginator(stats["pending_milk_entries"], 8).get_page(request.GET.get("pending_page")),
        "current_month_total": sum(
            item.total_liters for item in MilkRecord.objects.filter(record_date__year=today.year, record_date__month=today.month)
        ),
        "edit_item": item,
        "nav_active": "milk",
    }
    return render(request, "dashboard/milk_page.html", context)


@login_required
def milk_delete(request, pk):
    item = get_object_or_404(MilkRecord, pk=pk)
    if request.method == "POST":
        _audit_action(
            request.user,
            "milk_record_deleted",
            "MilkRecord",
            item.pk,
            {"date": str(item.record_date), "liters": str(item.total_liters)},
        )
        FinanceEntry.objects.filter(related_milk_record=item).delete()
        item.delete()
    return redirect("dashboard:milk_page")


@login_required
def milk_price_create(request):
    if request.method == "POST":
        form = MilkPriceForm(request.POST)
        if form.is_valid():
            price = create_milk_price(**form.cleaned_data)
            _audit_action(
                request.user,
                "milk_price_created",
                "MilkPrice",
                price.pk,
                {"price": str(price.price_per_liter), "currency": price.currency, "effective_from": str(price.effective_from)},
            )
            messages.success(request, "Sut narxi saqlandi.")
        else:
            messages.error(request, f"Sut narxini saqlab bo'lmadi: {form.errors.as_text()}")
    return _redirect_back(request, "dashboard:milk_page")


@login_required
def finance_create(request):
    if request.method == "POST":
        form = FinanceEntryForm(request.POST)
        if form.is_valid():
            entry = create_finance_entry(user=request.user, **form.cleaned_data)
            _audit_action(
                request.user,
                "finance_entry_created",
                "FinanceEntry",
                entry.pk,
                {"type": entry.entry_type, "category": entry.category, "amount": str(entry.amount), "currency": entry.currency},
            )
            messages.success(request, "Moliyaviy yozuv saqlandi.")
        else:
            messages.error(request, f"Moliyaviy yozuvni saqlab bo'lmadi: {form.errors.as_text()}")
    return _redirect_back(request, "dashboard:finance_page")


@login_required
def finance_page(request):
    today = _today()
    date_from = _parse_date(request.GET.get("date_from"), today - timedelta(days=30))
    date_to = _parse_date(request.GET.get("date_to"), today)
    year = _parse_year(request.GET.get("year"))
    month = _parse_int(request.GET.get("month"))
    if month and not year:
        year = today.year
    date_from, date_to = _apply_year_month_period(date_from, date_to, year, month)
    context = get_period_report(date_from, date_to)
    finance_qs = filter_finance_entries(date_from=date_from, date_to=date_to).order_by("-entry_date", "-created_at")
    context["finance_page_obj"] = Paginator(finance_qs, 12).get_page(request.GET.get("page"))
    context["finance_form"] = FinanceEntryForm(initial={"entry_date": today})
    context["edit_item"] = None
    context["nav_active"] = "finance"
    context["report_period"] = request.GET.get("report_period", "monthly")
    context["selected_year"] = year
    context["selected_month"] = month
    context["month_choices"] = MONTH_CHOICES
    context["finance_query_suffix"] = _finance_query(date_from, date_to, year, month)
    confirmed_finance_qs = finance_qs.filter(status=FinanceStatusChoices.CONFIRMED)
    context["finance_category_rows"] = finance_totals_by_category(confirmed_finance_qs)
    return render(request, "dashboard/finance_page.html", context)


@login_required
def finance_edit(request, pk):
    item = get_object_or_404(FinanceEntry, pk=pk)
    if request.method == "POST":
        form = FinanceEntryForm(request.POST, instance=item)
        if form.is_valid():
            entry = form.save()
            _audit_action(
                request.user,
                "finance_entry_updated",
                "FinanceEntry",
                entry.pk,
                {"type": entry.entry_type, "category": entry.category, "amount": str(entry.amount), "currency": entry.currency},
            )
            return redirect("dashboard:finance_page")
    else:
        form = FinanceEntryForm(instance=item)
    today = _today()
    year = _parse_year(request.GET.get("year"))
    month = _parse_int(request.GET.get("month"))
    if month and not year:
        year = today.year
    date_from, date_to = _apply_year_month_period(today - timedelta(days=30), today, year, month)
    context = get_period_report(date_from, date_to)
    finance_qs = filter_finance_entries(date_from=date_from, date_to=date_to).order_by("-entry_date", "-created_at")
    context["finance_page_obj"] = Paginator(finance_qs, 12).get_page(request.GET.get("page"))
    context["finance_form"] = form
    context["edit_item"] = item
    context["nav_active"] = "finance"
    context["report_period"] = request.GET.get("report_period", "monthly")
    context["selected_year"] = year
    context["selected_month"] = month
    context["month_choices"] = MONTH_CHOICES
    context["finance_query_suffix"] = _finance_query(date_from, date_to, year, month)
    confirmed_finance_qs = finance_qs.filter(status=FinanceStatusChoices.CONFIRMED)
    context["finance_category_rows"] = finance_totals_by_category(confirmed_finance_qs)
    return render(request, "dashboard/finance_page.html", context)


@login_required
def finance_delete(request, pk):
    item = get_object_or_404(FinanceEntry, pk=pk)
    if request.method == "POST":
        _audit_action(
            request.user,
            "finance_entry_deleted",
            "FinanceEntry",
            item.pk,
            {"type": item.entry_type, "category": item.category, "amount": str(item.amount), "currency": item.currency},
        )
        item.delete()
    return redirect("dashboard:finance_page")


@login_required
def worker_create(request):
    if request.method == "POST":
        form = WorkerForm(request.POST)
        if form.is_valid():
            worker = form.save()
            _audit_action(
                request.user,
                "worker_created",
                "Worker",
                worker.pk,
                {"name": worker.full_name, "salary": str(worker.monthly_salary), "currency": worker.currency},
            )
            messages.success(request, "Ishchi saqlandi.")
        else:
            messages.error(request, f"Ishchini saqlab bo'lmadi: {form.errors.as_text()}")
    return _redirect_back(request, "dashboard:workers_page")


@login_required
def workers_page(request):
    today = _today()
    date_from = _parse_date(request.GET.get("payment_date_from"), today - timedelta(days=30))
    date_to = _parse_date(request.GET.get("payment_date_to"), today)
    year = _parse_year(request.GET.get("payment_year"))
    month = _parse_int(request.GET.get("payment_month"))
    if month and not year:
        year = today.year
    worker_id = _parse_int(request.GET.get("worker_id"))
    date_from, date_to = _apply_year_month_period(date_from, date_to, year, month)
    payments = filter_worker_payments(date_from=date_from, date_to=date_to, worker_id=worker_id)
    payroll = get_worker_payroll_summary()
    context = {
        "stats": get_dashboard_overview(today - timedelta(days=30), today),
        "worker_page_obj": Paginator(payroll, 8).get_page(request.GET.get("workers_page")),
        "worker_form": WorkerForm(),
        "advance_form": WorkerAdvanceForm(initial={"advance_date": today, "month_reference": today.replace(day=1)}),
        "payments_page_obj": Paginator(payments, 10).get_page(request.GET.get("page")),
        "edit_item": None,
        "payment_edit_item": None,
        "payment_date_from": date_from,
        "payment_date_to": date_to,
        "payment_year": year,
        "payment_month": month,
        "month_choices": MONTH_CHOICES,
        "payment_query_suffix": _payment_query(date_from, date_to, year, month, worker_id),
        "selected_worker_id": worker_id,
        "workers": Worker.objects.filter(is_active=True).order_by("full_name"),
        "nav_active": "workers_manage",
    }
    return render(request, "dashboard/workers_page.html", context)


@login_required
def worker_edit(request, pk):
    item = get_object_or_404(Worker, pk=pk)
    if request.method == "POST":
        form = WorkerForm(request.POST, instance=item)
        if form.is_valid():
            worker = form.save()
            _audit_action(
                request.user,
                "worker_updated",
                "Worker",
                worker.pk,
                {"name": worker.full_name, "salary": str(worker.monthly_salary), "currency": worker.currency},
            )
            return redirect("dashboard:workers_page")
    else:
        form = WorkerForm(instance=item)
    today = _today()
    date_from = _parse_date(request.GET.get("payment_date_from"), today - timedelta(days=30))
    date_to = _parse_date(request.GET.get("payment_date_to"), today)
    year = _parse_year(request.GET.get("payment_year"))
    month = _parse_int(request.GET.get("payment_month"))
    if month and not year:
        year = today.year
    worker_id = _parse_int(request.GET.get("worker_id"))
    date_from, date_to = _apply_year_month_period(date_from, date_to, year, month)
    payments = filter_worker_payments(date_from=date_from, date_to=date_to, worker_id=worker_id)
    payroll = get_worker_payroll_summary()
    context = {
        "stats": get_dashboard_overview(today - timedelta(days=30), today),
        "worker_page_obj": Paginator(payroll, 8).get_page(request.GET.get("workers_page")),
        "worker_form": form,
        "advance_form": WorkerAdvanceForm(initial={"advance_date": today, "month_reference": today.replace(day=1)}),
        "payments_page_obj": Paginator(payments, 10).get_page(request.GET.get("page")),
        "edit_item": item,
        "payment_edit_item": None,
        "payment_date_from": date_from,
        "payment_date_to": date_to,
        "payment_year": year,
        "payment_month": month,
        "month_choices": MONTH_CHOICES,
        "payment_query_suffix": _payment_query(date_from, date_to, year, month, worker_id),
        "selected_worker_id": worker_id,
        "workers": Worker.objects.filter(is_active=True).order_by("full_name"),
        "nav_active": "workers_manage",
    }
    return render(request, "dashboard/workers_page.html", context)


@login_required
def worker_delete(request, pk):
    item = get_object_or_404(Worker, pk=pk)
    if request.method == "POST":
        _audit_action(
            request.user,
            "worker_deleted",
            "Worker",
            item.pk,
            {"name": item.full_name, "salary": str(item.monthly_salary), "currency": item.currency},
        )
        item.delete()
    return redirect("dashboard:workers_page")


@login_required
def worker_advance_create(request):
    if request.method == "POST":
        form = WorkerAdvanceForm(request.POST)
        if form.is_valid():
            payment = create_worker_advance(user=request.user, **form.cleaned_data)
            sync_worker_payment_finance_entry(user=request.user, payment=payment)
            _audit_action(
                request.user,
                "worker_payment_created",
                "WorkerAdvance",
                payment.pk,
                {"worker": payment.worker.full_name, "amount": str(payment.amount), "currency": payment.currency, "type": payment.payment_type},
            )
            messages.success(request, "Ishchi to'lovi saqlandi va chiqimga qo'shildi.")
        else:
            messages.error(request, f"Ishchi to'lovini saqlab bo'lmadi: {form.errors.as_text()}")
    return _redirect_back(request, "dashboard:workers_page")


@login_required
def worker_payment_edit(request, pk):
    payment = get_object_or_404(WorkerAdvance, pk=pk)
    if request.method == "POST":
        previous_snapshot = _worker_payment_snapshot(
            worker_name=payment.worker.full_name,
            payment_type_label=payment.get_payment_type_display(),
            currency=payment.currency,
            advance_date=payment.advance_date,
        )
        form = WorkerAdvanceForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save()
            sync_worker_payment_finance_entry(
                user=request.user,
                payment=payment,
                previous_snapshot=previous_snapshot,
            )
            _audit_action(
                request.user,
                "worker_payment_updated",
                "WorkerAdvance",
                payment.pk,
                {"worker": payment.worker.full_name, "amount": str(payment.amount), "currency": payment.currency, "type": payment.payment_type},
            )
            messages.success(request, "To'lov yangilandi.")
            return redirect("dashboard:workers_page")
        messages.error(request, f"To'lovni yangilab bo'lmadi: {form.errors.as_text()}")
    else:
        form = WorkerAdvanceForm(instance=payment)

    today = _today()
    date_from = _parse_date(request.GET.get("payment_date_from"), today - timedelta(days=30))
    date_to = _parse_date(request.GET.get("payment_date_to"), today)
    year = _parse_year(request.GET.get("payment_year"))
    month = _parse_int(request.GET.get("payment_month"))
    if month and not year:
        year = today.year
    worker_id = _parse_int(request.GET.get("worker_id"))
    date_from, date_to = _apply_year_month_period(date_from, date_to, year, month)
    payments = filter_worker_payments(date_from=date_from, date_to=date_to, worker_id=worker_id)
    payroll = get_worker_payroll_summary()
    context = {
        "stats": get_dashboard_overview(today - timedelta(days=30), today),
        "worker_page_obj": Paginator(payroll, 8).get_page(request.GET.get("workers_page")),
        "worker_form": WorkerForm(),
        "advance_form": form,
        "payments_page_obj": Paginator(payments, 10).get_page(request.GET.get("page")),
        "edit_item": None,
        "payment_edit_item": payment,
        "payment_date_from": date_from,
        "payment_date_to": date_to,
        "payment_year": year,
        "payment_month": month,
        "month_choices": MONTH_CHOICES,
        "payment_query_suffix": _payment_query(date_from, date_to, year, month, worker_id),
        "selected_worker_id": worker_id,
        "workers": Worker.objects.filter(is_active=True).order_by("full_name"),
        "nav_active": "workers_manage",
    }
    return render(request, "dashboard/workers_page.html", context)


@login_required
def worker_payment_delete(request, pk):
    item = get_object_or_404(WorkerAdvance, pk=pk)
    if request.method == "POST":
        delete_worker_payment_finance_entry(payment=item)
        _audit_action(
            request.user,
            "worker_payment_deleted",
            "WorkerAdvance",
            item.pk,
            {"worker": item.worker.full_name, "amount": str(item.amount), "currency": item.currency, "type": item.payment_type},
        )
        item.delete()
    return redirect("dashboard:workers_page")


@login_required
def workers_report_page(request):
    today = _today()
    date_from = _parse_date(request.GET.get("payment_date_from"), today - timedelta(days=30))
    date_to = _parse_date(request.GET.get("payment_date_to"), today)
    year = _parse_year(request.GET.get("payment_year"))
    month = _parse_int(request.GET.get("payment_month"))
    if month and not year:
        year = today.year
    worker_id = _parse_int(request.GET.get("worker_id"))
    date_from, date_to = _apply_year_month_period(date_from, date_to, year, month)
    payroll = get_worker_payroll_summary()
    if worker_id:
        payroll = [item for item in payroll if item["id"] == worker_id]
    payments = filter_worker_payments(date_from=date_from, date_to=date_to, worker_id=worker_id)
    page_obj = Paginator(payroll, 12).get_page(request.GET.get("page"))
    context = {
        "worker_page_obj": page_obj,
        "payment_page_obj": Paginator(payments, 12).get_page(request.GET.get("payment_page")),
        "nav_active": "workers_report",
        "stats": get_dashboard_overview(today - timedelta(days=30), today),
        "payment_date_from": date_from,
        "payment_date_to": date_to,
        "payment_year": year,
        "payment_month": month,
        "month_choices": MONTH_CHOICES,
        "payment_query_suffix": _payment_query(date_from, date_to, year, month, worker_id),
        "selected_worker_id": worker_id,
        "workers": Worker.objects.filter(is_active=True).order_by("full_name"),
    }
    return render(request, "dashboard/workers_report_page.html", context)


@login_required
def general_report_export(request):
    today = _today()
    date_from = _parse_date(request.GET.get("date_from"), today - timedelta(days=30))
    date_to = _parse_date(request.GET.get("date_to"), today)
    year = _parse_year(request.GET.get("year"))
    month = _parse_int(request.GET.get("month"))
    if month and not year:
        year = today.year
    date_from, date_to = _apply_year_month_period(date_from, date_to, year, month)

    try:
        from .excel import build_general_report_workbook
    except Exception:
        return HttpResponse("Excel export uchun openpyxl kerak: pip install openpyxl", status=500)

    workbook = build_general_report_workbook(date_from=date_from, date_to=date_to)
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="ferma-hisobot-{date_from}-{date_to}.xlsx"'
    workbook.save(response)
    return response


@login_required
def milk_payment_receive(request, entry_id):
    if request.method == "POST":
        account_source = request.POST.get("account_source", AccountSourceChoices.INTERNAL)
        received_date = _parse_date(request.POST.get("received_at"), _today())
        entry = mark_milk_payment_received(entry_id=entry_id, account_source=account_source, received_at=received_date)
        if entry:
            _audit_action(
                request.user,
                "milk_payment_received",
                "FinanceEntry",
                entry.pk,
                {"amount": str(entry.amount), "currency": entry.currency, "source": entry.source, "received_at": str(entry.received_at)},
            )
        messages.success(request, "Sut to'lovi hisobga o'tkazildi.")
    return redirect("dashboard:milk_page")


@login_required
def report_list(request):
    today = _today()
    period = request.GET.get("period", "weekly")
    if period == "monthly":
        date_from = today - timedelta(days=30)
    elif period == "yearly":
        date_from = today.replace(month=1, day=1)
    elif period == "yesterday":
        date_from = today - timedelta(days=1)
    else:
        date_from = today - timedelta(days=6)
    context = get_period_report(date_from, today)
    context["worker_payroll"] = get_worker_payroll_summary()
    context["period"] = period
    context["nav_active"] = "finance"
    return render(request, "dashboard/report_list.html", context)


@login_required
def admin_dashboard(request):
    if request.user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        return redirect("dashboard:home")
    today = _today()
    date_from = _parse_date(request.GET.get("date_from"), today - timedelta(days=30))
    date_to = _parse_date(request.GET.get("date_to"), today)
    stats = get_dashboard_overview(date_from, date_to)
    logs_page_obj = Paginator(_recent_logs(), 10).get_page(request.GET.get("logs_page"))
    context = {
        "stats": stats,
        "worker_payroll": get_worker_payroll_summary(),
        "date_from": date_from,
        "date_to": date_to,
        "milk_price_form": MilkPriceForm(initial={"effective_from": today}),
        "milk_form": MilkRecordForm(initial={"record_date": today}),
        "finance_form": FinanceEntryForm(initial={"entry_date": today}),
        "worker_form": WorkerForm(),
        "advance_form": WorkerAdvanceForm(initial={"advance_date": today, "month_reference": today.replace(day=1)}),
        "logs_page_obj": logs_page_obj,
        "role": request.user.role,
        "is_admin_dashboard": True,
        "nav_active": "home",
    }
    return render(request, "dashboard/home.html", context)
