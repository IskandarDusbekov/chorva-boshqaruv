from datetime import date

from .models import (
    AccountSourceChoices,
    FinanceEntry,
    FinanceStatusChoices,
    FinanceTypeChoices,
    MilkPrice,
    MilkRecord,
    WorkerAdvance,
)
from .selectors import get_active_milk_price, get_finance_entry


def create_milk_price(**data):
    return MilkPrice.objects.create(**data)


def create_milk_record(*, user, **data):
    active_price = get_active_milk_price(data["record_date"])
    price_per_liter = active_price.price_per_liter if active_price else 0
    currency = active_price.currency if active_price else "UZS"
    milk_record = MilkRecord.objects.filter(record_date=data["record_date"]).first()
    if not milk_record:
        milk_record = MilkRecord(record_date=data["record_date"], created_by=user)

    shift = data.get("shift")
    liters = data.get("liters")
    if shift == "morning" and liters not in (None, ""):
        milk_record.morning_liters = liters
    if shift == "evening" and liters not in (None, ""):
        milk_record.evening_liters = liters
    if data.get("note"):
        milk_record.note = data["note"]

    milk_record.price_per_liter = price_per_liter
    milk_record.currency = currency
    milk_record.created_by = user
    milk_record.save()
    return milk_record


def create_finance_entry(*, user, **data):
    return FinanceEntry.objects.create(created_by=user, status=FinanceStatusChoices.CONFIRMED, **data)


def create_worker_advance(*, user, **data):
    return WorkerAdvance.objects.create(created_by=user, **data)


def sync_worker_payment_finance_entry(*, user, payment):
    finance_entry, _created = FinanceEntry.objects.update_or_create(
        related_worker_payment=payment,
        defaults={
            "created_by": user,
            "entry_type": FinanceTypeChoices.EXPENSE,
            "category": "Ishchi to'lovi",
            "amount": payment.amount,
            "currency": payment.currency,
            "source": AccountSourceChoices.INTERNAL,
            "status": FinanceStatusChoices.CONFIRMED,
            "entry_date": payment.advance_date,
            "received_at": payment.advance_date,
            "note": f"{payment.worker.full_name} - {payment.get_payment_type_display()}",
        },
    )
    return finance_entry


def delete_worker_payment_finance_entry(*, payment):
    FinanceEntry.objects.filter(related_worker_payment=payment).delete()


def create_milk_income_from_record(*, user, milk_record):
    finance_entry, _created = FinanceEntry.objects.update_or_create(
        related_milk_record=milk_record,
        entry_type=FinanceTypeChoices.INCOME,
        defaults={
            "created_by": user,
            "category": "Sut sotuvi",
            "amount": milk_record.milk_income_amount,
            "currency": milk_record.currency,
            "source": AccountSourceChoices.DEFAULT,
            "status": FinanceStatusChoices.PENDING,
            "entry_date": milk_record.record_date,
            "received_at": None,
            "note": "Sut yozuvi bo'yicha kutilayotgan to'lov",
        },
    )
    return finance_entry


def mark_milk_payment_received(*, entry_id, account_source, received_at=None):
    finance_entry = get_finance_entry(entry_id)
    if not finance_entry:
        return None
    actual_date = received_at or date.today()
    finance_entry.status = FinanceStatusChoices.CONFIRMED
    finance_entry.source = account_source
    finance_entry.received_at = actual_date
    # Ferma hisobiga tushgan sana bo'yicha ko'rsatilsin
    finance_entry.entry_date = actual_date
    finance_entry.save(update_fields=["status", "source", "received_at", "entry_date"])
    return finance_entry
