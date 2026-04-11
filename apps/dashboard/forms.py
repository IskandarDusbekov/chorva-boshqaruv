from django import forms
from django.utils import timezone

from .models import (
    FinanceCategory,
    FinanceEntry,
    MilkPrice,
    MilkRecord,
    Worker,
    WorkerAdvance,
    WorkerJobType,
)


class DateInput(forms.DateInput):
    input_type = "date"


UZBEK_MONTHS = {
    1: "Yanvar",
    2: "Fevral",
    3: "Mart",
    4: "Aprel",
    5: "May",
    6: "Iyun",
    7: "Iyul",
    8: "Avgust",
    9: "Sentabr",
    10: "Oktabr",
    11: "Noyabr",
    12: "Dekabr",
}


def apply_form_control_styles(form):
    base_class = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-700 shadow-sm focus:border-indigo-500 focus:outline-none"
    checkbox_class = "h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs["class"] = checkbox_class
            continue
        current = widget.attrs.get("class", "")
        widget.attrs["class"] = f"{current} {base_class}".strip()


class MilkRecordForm(forms.Form):
    SHIFT_MORNING = "morning"
    SHIFT_EVENING = "evening"
    SHIFT_CHOICES = (
        (SHIFT_MORNING, "Ertalabki sut"),
        (SHIFT_EVENING, "Kunduzgi / kechki sut"),
    )

    record_date = forms.DateField(widget=DateInput(), label="Sana")
    shift = forms.ChoiceField(choices=SHIFT_CHOICES, label="Qaysi payt")
    liters = forms.DecimalField(min_value=0, decimal_places=2, max_digits=10, label="Litr")
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Izoh")

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)
        apply_form_control_styles(self)
        if not instance and not self.initial.get("record_date"):
            self.initial["record_date"] = timezone.now().date()
        if instance:
            shift = self.SHIFT_MORNING
            liters = instance.morning_liters
            if instance.evening_liters and not instance.morning_liters:
                shift = self.SHIFT_EVENING
                liters = instance.evening_liters
            self.initial.setdefault("record_date", instance.record_date)
            self.initial.setdefault("shift", shift)
            self.initial.setdefault("liters", liters)
            self.initial.setdefault("note", instance.note)


class MilkPriceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_control_styles(self)

    class Meta:
        model = MilkPrice
        fields = ["effective_from", "price_per_liter", "currency", "note"]
        widgets = {"effective_from": DateInput()}


class FinanceEntryForm(forms.ModelForm):
    category = forms.ChoiceField(choices=(), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_control_styles(self)
        income_categories = FinanceCategory.objects.filter(is_active=True, entry_type="income").order_by("name")
        expense_categories = FinanceCategory.objects.filter(is_active=True, entry_type="expense").order_by("name")
        grouped_choices = []
        if income_categories.exists():
            grouped_choices.append(("Kirim kategoriyalari", [(item.name, item.name) for item in income_categories]))
        if expense_categories.exists():
            grouped_choices.append(("Chiqim kategoriyalari", [(item.name, item.name) for item in expense_categories]))
        self.fields["category"].choices = grouped_choices
        self.fields["category"].help_text = "Kategoriyalar admin panel orqali boshqariladi."
        if self.instance and self.instance.pk and self.instance.category:
            existing = self.instance.category
            values = [choice[0] for choice in self.fields["category"].choices]
            if existing not in values:
                self.fields["category"].choices = [(existing, existing)] + list(self.fields["category"].choices)

    class Meta:
        model = FinanceEntry
        fields = ["entry_type", "category", "amount", "currency", "source", "entry_date", "note"]
        widgets = {"entry_date": DateInput()}


class WorkerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_control_styles(self)
        self.fields["job_type"].queryset = WorkerJobType.objects.filter(is_active=True).order_by("name")

    class Meta:
        model = Worker
        fields = ["full_name", "job_type", "monthly_salary", "currency", "started_at", "payday_day", "note", "is_active"]
        widgets = {"started_at": DateInput()}


class WorkerAdvanceForm(forms.ModelForm):
    month_reference = forms.ChoiceField(label="Qaysi oy uchun")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_control_styles(self)
        today = timezone.now().date()
        month_choices = []
        for year in [today.year - 1, today.year, today.year + 1]:
            for month in range(1, 13):
                value = f"{year}-{month:02d}-01"
                label = f"{UZBEK_MONTHS[month]} {year}"
                month_choices.append((value, label))
        self.fields["month_reference"].choices = month_choices
        default_value = f"{today.year}-{today.month:02d}-01"
        if self.instance and self.instance.pk and self.instance.month_reference:
            default_value = self.instance.month_reference.strftime("%Y-%m-01")
        self.fields["month_reference"].initial = default_value
        if not self.initial.get("advance_date"):
            self.initial["advance_date"] = today
        if not self.initial.get("month_reference"):
            self.initial["month_reference"] = default_value

    def clean_month_reference(self):
        value = self.cleaned_data["month_reference"]
        return timezone.datetime.strptime(value, "%Y-%m-%d").date()

    class Meta:
        model = WorkerAdvance
        fields = ["worker", "payment_type", "amount", "currency", "month_reference", "advance_date", "note"]
        widgets = {"advance_date": DateInput(), "month_reference": DateInput()}
