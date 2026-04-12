from decimal import Decimal

from django.core.cache import cache
from django.db.models import Case, DecimalField, Sum, Value, When

from .models import AccountSourceChoices, CurrencyChoices, FinanceEntry, FinanceStatusChoices, FinanceTypeChoices


def header_farm_balance(request):
    """Header uchun ferma asosiy balansini yengil cache bilan uzatadi."""
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {}

    cache_key = "header-farm-balance-v1"
    cached_balance = cache.get(cache_key)
    if cached_balance is not None:
        return {"header_farm_balance": cached_balance}

    totals = FinanceEntry.objects.filter(
        status=FinanceStatusChoices.CONFIRMED,
        source=AccountSourceChoices.INTERNAL,
    ).aggregate(
        income_uzs=Sum(
            Case(
                When(entry_type=FinanceTypeChoices.INCOME, currency=CurrencyChoices.UZS, then="amount"),
                default=Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        ),
        expense_uzs=Sum(
            Case(
                When(entry_type=FinanceTypeChoices.EXPENSE, currency=CurrencyChoices.UZS, then="amount"),
                default=Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        ),
        income_usd=Sum(
            Case(
                When(entry_type=FinanceTypeChoices.INCOME, currency=CurrencyChoices.USD, then="amount"),
                default=Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        ),
        expense_usd=Sum(
            Case(
                When(entry_type=FinanceTypeChoices.EXPENSE, currency=CurrencyChoices.USD, then="amount"),
                default=Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        ),
    )

    balance = {
        "UZS": (totals["income_uzs"] or Decimal("0")) - (totals["expense_uzs"] or Decimal("0")),
        "USD": (totals["income_usd"] or Decimal("0")) - (totals["expense_usd"] or Decimal("0")),
    }
    cache.set(cache_key, balance, timeout=15)
    return {"header_farm_balance": balance}
