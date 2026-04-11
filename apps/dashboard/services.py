"""Dashboard yozuvlarini yaratish va sinxronlash servis qatlami."""

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


def _worker_payment_note(worker_name, payment_type_label):
    """Ishchi to'lovi uchun yagona note formatini yasaydi."""
    return f"{worker_name} - {payment_type_label}"


def _worker_payment_snapshot(*, worker_name, payment_type_label, currency, advance_date):
    """Edit paytida eski holatni tozalash uchun payment snapshot tayyorlaydi."""
    return {
        "note": _worker_payment_note(worker_name, payment_type_label),
        "currency": currency,
        "advance_date": advance_date,
    }


def _delete_worker_payment_orphans(*, snapshot):
    """Bog'lanmay qolgan eski ishchi to'lovi chiqimlarini o'chiradi."""
    if not snapshot:
        return
    FinanceEntry.objects.filter(
        related_worker_payment__isnull=True,
        related_milk_record__isnull=True,
        entry_type=FinanceTypeChoices.EXPENSE,
        category="Ishchi to'lovi",
        source=AccountSourceChoices.INTERNAL,
        currency=snapshot["currency"],
        entry_date=snapshot["advance_date"],
        note=snapshot["note"],
    ).delete()


def create_milk_price(**data):
    """Yangi sut narxini yaratadi."""
    return MilkPrice.objects.create(**data)


def create_milk_record(*, user, **data):
    """Bir kunlik sut yozuvini yaratadi yoki mavjudini navbat bo'yicha yangilaydi."""
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
    """Tasdiqlangan kirim yoki chiqim yozuvini yaratadi."""
    return FinanceEntry.objects.create(created_by=user, status=FinanceStatusChoices.CONFIRMED, **data)


def create_worker_advance(*, user, **data):
    """Ishchi uchun avans yoki ish haqi yozuvini saqlaydi."""
    return WorkerAdvance.objects.create(created_by=user, **data)


def sync_worker_payment_finance_entry(*, user, payment, previous_snapshot=None):
    """Ishchi to'lovi bilan bog'liq moliyaviy chiqimni bir xil holatda ushlab turadi."""
    note = _worker_payment_note(payment.worker.full_name, payment.get_payment_type_display())
    defaults = {
        "created_by": user,
        "entry_type": FinanceTypeChoices.EXPENSE,
        "category": "Ishchi to'lovi",
        "amount": payment.amount,
        "currency": payment.currency,
        "source": AccountSourceChoices.INTERNAL,
        "status": FinanceStatusChoices.CONFIRMED,
        "entry_date": payment.advance_date,
        "received_at": payment.advance_date,
        "note": note,
    }

    finance_entry = FinanceEntry.objects.filter(related_worker_payment=payment).order_by("-created_at").first()

    if finance_entry:
        for field, value in defaults.items():
            setattr(finance_entry, field, value)
        finance_entry.related_worker_payment = payment
        finance_entry.save()
    else:
        finance_entry = FinanceEntry.objects.create(related_worker_payment=payment, **defaults)

    # Bir payment uchun faqat bitta moliya chiqimi qolishi kerak.
    FinanceEntry.objects.filter(related_worker_payment=payment).exclude(pk=finance_entry.pk).delete()
    _delete_worker_payment_orphans(snapshot=previous_snapshot)
    return finance_entry


def delete_worker_payment_finance_entry(*, payment):
    """Ishchi to'lovi o'chirilganda bog'liq moliya yozuvini ham o'chiradi."""
    FinanceEntry.objects.filter(related_worker_payment=payment).delete()
    _delete_worker_payment_orphans(
        snapshot=_worker_payment_snapshot(
            worker_name=payment.worker.full_name,
            payment_type_label=payment.get_payment_type_display(),
            currency=payment.currency,
            advance_date=payment.advance_date,
        )
    )


def create_milk_income_from_record(*, user, milk_record):
    """Sut yozuvi uchun default hisobdagi kutilayotgan kirimni yaratadi."""
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
    """Default hisobdagi sut pulini haqiqiy hisobga o'tkazadi."""
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
