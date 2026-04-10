from datetime import date

from django.test import TestCase

from apps.accounts.models import User, UserRole

from .models import FinanceTypeChoices
from .selectors import get_dashboard_overview
from .services import create_finance_entry, create_milk_income_from_record, create_milk_record


class FarmDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="worker",
            password="StrongPass123",
            phone_number="+998900000001",
            full_name="Worker One",
            role=UserRole.USER,
        )

    def test_milk_record_creates_income(self):
        record = create_milk_record(
            user=self.user,
            record_date=date(2026, 4, 9),
            morning_liters=120,
            evening_liters=130,
            price_per_liter=10000,
            currency="UZS",
            note="Kunlik sut",
        )
        finance = create_milk_income_from_record(user=self.user, milk_record=record)
        self.assertEqual(finance.entry_type, FinanceTypeChoices.INCOME)
        self.assertEqual(str(record.total_liters), "250")

    def test_overview_returns_totals(self):
        create_finance_entry(
            user=self.user,
            entry_type="expense",
            category="Yem",
            amount=500000,
            currency="UZS",
            source="internal",
            entry_date=date(2026, 4, 9),
            note="",
        )
        overview = get_dashboard_overview(date(2026, 4, 1), date(2026, 4, 9))
        self.assertIn("expense_totals", overview)
