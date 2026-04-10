from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from .models import (
    AccountSourceChoices,
    CurrencyChoices,
    FinanceEntry,
    FinanceStatusChoices,
    FinanceTypeChoices,
    MilkPrice,
    MilkRecord,
    Worker,
    WorkerAdvance,
)


USD_RATE = Decimal("12800")


def _today():
    return timezone.now().date()


def _month_start(value):
    return value.replace(day=1)


def _next_month(value):
    if value.month == 12:
        return value.replace(year=value.year + 1, month=1, day=1)
    return value.replace(month=value.month + 1, day=1)


def to_uzs(amount, currency):
    amount = Decimal(amount or 0)
    if currency == CurrencyChoices.USD:
        return amount * USD_RATE
    return amount


def money_breakdown(entries, *, entry_type=None, source=None, status=None):
    totals = {"UZS": Decimal("0"), "USD": Decimal("0")}
    for item in entries:
        if entry_type and item.entry_type != entry_type:
            continue
        if source and item.source != source:
            continue
        if status and item.status != status:
            continue
        totals[item.currency] += Decimal(item.amount or 0)
    return totals


def get_active_milk_price(on_date=None):
    on_date = on_date or _today()
    return MilkPrice.objects.filter(effective_from__lte=on_date).order_by("-effective_from", "-created_at").first()


def get_milk_records(date_from=None, date_to=None):
    queryset = MilkRecord.objects.all()
    if date_from:
        queryset = queryset.filter(record_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(record_date__lte=date_to)
    return queryset


def get_finance_entries(date_from=None, date_to=None):
    queryset = FinanceEntry.objects.all()
    if date_from:
        queryset = queryset.filter(entry_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(entry_date__lte=date_to)
    return queryset.select_related("related_milk_record", "created_by")


def filter_finance_entries(*, date_from=None, date_to=None, year=None, entry_type=None):
    queryset = get_finance_entries(date_from, date_to)
    if year:
        queryset = queryset.filter(entry_date__year=year)
    if entry_type:
        queryset = queryset.filter(entry_type=entry_type)
    return queryset


def finance_totals_by_category(entries):
    grouped = {}
    for item in entries:
        key = (item.entry_type, item.category)
        bucket = grouped.setdefault(
            key,
            {"entry_type": item.entry_type, "category": item.category, "UZS": Decimal("0"), "USD": Decimal("0"), "count": 0},
        )
        bucket[item.currency] += Decimal(item.amount or 0)
        bucket["count"] += 1
    return sorted(grouped.values(), key=lambda row: (row["entry_type"], row["category"]))


def filter_worker_payments(*, date_from=None, date_to=None, year=None, worker_id=None):
    queryset = WorkerAdvance.objects.select_related("worker").order_by("-advance_date", "-created_at")
    if date_from:
        queryset = queryset.filter(advance_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(advance_date__lte=date_to)
    if year:
        queryset = queryset.filter(advance_date__year=year)
    if worker_id:
        queryset = queryset.filter(worker_id=worker_id)
    return queryset


def get_workers():
    return Worker.objects.prefetch_related("advances").all()


def _previous_salary_balance(worker, current_month_start):
    """Return previous months balance in worker salary currency.

    Positive value means the farm still owes the worker.
    Negative value means the worker was paid more than expected.
    """
    if not worker.started_at:
        return {
            "months": 0,
            "expected": Decimal("0"),
            "paid": Decimal("0"),
            "balance": Decimal("0"),
        }
    previous_months = 0
    cursor = _month_start(worker.started_at)
    while cursor < current_month_start:
        previous_months += 1
        cursor = _next_month(cursor)

    expected = worker.monthly_salary * previous_months
    paid = Decimal("0")
    for payment in worker.advances.all():
        month_ref = _month_start(payment.month_reference or payment.advance_date)
        if month_ref < current_month_start and payment.currency == worker.currency:
            paid += Decimal(payment.amount or 0)
    return {
        "months": previous_months,
        "expected": expected,
        "paid": paid,
        "balance": expected - paid,
    }


def get_worker_payroll_summary(reference_date=None):
    reference_date = reference_date or _today()
    current_month_start = _month_start(reference_date)
    next_month_start = _next_month(current_month_start)
    workers = get_workers()
    summary = []

    for worker in workers:
        current_payments = [
            payment
            for payment in worker.advances.all()
            if current_month_start <= _month_start(payment.month_reference or payment.advance_date) < next_month_start
        ]
        month_uzs = sum((Decimal(p.amount or 0) for p in current_payments if p.currency == CurrencyChoices.UZS), Decimal("0"))
        month_usd = sum((Decimal(p.amount or 0) for p in current_payments if p.currency == CurrencyChoices.USD), Decimal("0"))
        advance_uzs = sum(
            (Decimal(p.amount or 0) for p in current_payments if p.currency == CurrencyChoices.UZS and p.payment_type == WorkerAdvance.PaymentTypeChoices.ADVANCE),
            Decimal("0"),
        )
        advance_usd = sum(
            (Decimal(p.amount or 0) for p in current_payments if p.currency == CurrencyChoices.USD and p.payment_type == WorkerAdvance.PaymentTypeChoices.ADVANCE),
            Decimal("0"),
        )
        current_paid_salary_currency = sum(
            (Decimal(p.amount or 0) for p in current_payments if p.currency == worker.currency),
            Decimal("0"),
        )
        previous = _previous_salary_balance(worker, current_month_start)
        total_due = previous["balance"] + worker.monthly_salary
        remaining_salary = total_due - current_paid_salary_currency

        summary.append(
            {
                "id": worker.id,
                "name": worker.full_name,
                "role": worker.job_type.name if worker.job_type else worker.get_role_display(),
                "salary": worker.monthly_salary,
                "currency": worker.currency,
                "started_at": worker.started_at,
                "payday_day": worker.payday_day,
                "month_paid_uzs": month_uzs,
                "month_paid_usd": month_usd,
                "advance_uzs": advance_uzs,
                "advance_usd": advance_usd,
                "carry": previous["paid"] - previous["expected"],
                "previous_months": previous["months"],
                "previous_expected": previous["expected"],
                "previous_paid": previous["paid"],
                "previous_balance": previous["balance"],
                "current_paid_salary_currency": current_paid_salary_currency,
                "total_due": total_due,
                "remaining": remaining_salary,
            }
        )
    return summary


def get_finance_entry(entry_id):
    return FinanceEntry.objects.filter(id=entry_id).first()


def get_dashboard_overview(date_from=None, date_to=None):
    today = _today()
    last_week_start = today - timedelta(days=6)
    previous_day = today - timedelta(days=1)

    records = list(get_milk_records(date_from, date_to))
    last_week_records = list(get_milk_records(last_week_start, today))
    finances = list(get_finance_entries(date_from, date_to))
    all_pending_milk = list(
        FinanceEntry.objects.filter(
            status=FinanceStatusChoices.PENDING,
            related_milk_record__isnull=False,
        ).select_related("related_milk_record").order_by("-entry_date", "-created_at")
    )
    confirmed_finances = [item for item in finances if item.status == FinanceStatusChoices.CONFIRMED]
    pending_milk = all_pending_milk
    workers = list(get_workers())

    total_liters = sum((record.total_liters for record in records), Decimal("0"))
    weekly_values = [record.total_liters for record in last_week_records]
    max_daily = max(weekly_values, default=Decimal("0"))
    min_daily = min(weekly_values, default=Decimal("0"))
    today_record = next((record for record in last_week_records if record.record_date == today), None)
    prev_record = next((record for record in last_week_records if record.record_date == previous_day), None)
    today_liters = today_record.total_liters if today_record else Decimal("0")
    prev_liters = prev_record.total_liters if prev_record else Decimal("0")
    progress_percent = int((today_liters / max_daily) * 100) if max_daily > 0 else 0
    growth_percent = ((today_liters - prev_liters) / prev_liters) * 100 if prev_liters > 0 else Decimal("0")

    confirmed_income = money_breakdown(confirmed_finances, entry_type=FinanceTypeChoices.INCOME)
    confirmed_expense = money_breakdown(confirmed_finances, entry_type=FinanceTypeChoices.EXPENSE)
    pending_milk_totals = money_breakdown(pending_milk, entry_type=FinanceTypeChoices.INCOME)
    internal_income = money_breakdown(
        confirmed_finances,
        source=AccountSourceChoices.INTERNAL,
        entry_type=FinanceTypeChoices.INCOME,
    )
    internal_expense = money_breakdown(
        confirmed_finances,
        source=AccountSourceChoices.INTERNAL,
        entry_type=FinanceTypeChoices.EXPENSE,
    )
    external_income = money_breakdown(
        confirmed_finances,
        source=AccountSourceChoices.EXTERNAL,
        entry_type=FinanceTypeChoices.INCOME,
    )
    external_expense = money_breakdown(
        confirmed_finances,
        source=AccountSourceChoices.EXTERNAL,
        entry_type=FinanceTypeChoices.EXPENSE,
    )

    return {
        "total_liters": total_liters,
        "max_daily": max_daily,
        "min_daily": min_daily,
        "today_liters": today_liters,
        "progress_percent": progress_percent,
        "growth_percent": growth_percent,
        "income_totals": confirmed_income,
        "expense_totals": confirmed_expense,
        "pending_milk_totals": pending_milk_totals,
        "internal_balance": {
            "UZS": internal_income["UZS"] - internal_expense["UZS"],
            "USD": internal_income["USD"] - internal_expense["USD"],
        },
        "external_balance": {
            "UZS": external_income["UZS"] - external_expense["UZS"],
            "USD": external_income["USD"] - external_expense["USD"],
        },
        "farm_balance": {
            "UZS": internal_income["UZS"] - internal_expense["UZS"],
            "USD": internal_income["USD"] - internal_expense["USD"],
        },
        "recent_finances": finances[:10],
        "recent_milk_records": records[:10],
        "pending_milk_entries": pending_milk[:10],
        "workers": workers,
        "worker_count": len(workers),
        "weekly_chart": [
            {
                "date": record.record_date.strftime("%d-%m"),
                "liters": float(record.total_liters),
                "percent": int((record.total_liters / max_daily) * 100) if max_daily else 0,
            }
            for record in reversed(last_week_records)
        ],
        "active_milk_price": get_active_milk_price(today),
    }


def get_period_report(date_from, date_to):
    overview = get_dashboard_overview(date_from, date_to)
    finances = list(get_finance_entries(date_from, date_to))
    workers = list(get_workers())
    return {
        "date_from": date_from,
        "date_to": date_to,
        "overview": overview,
        "finances": finances,
        "workers": workers,
    }
