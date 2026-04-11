from django.db import migrations, models


def backfill_worker_payment_finance_links(apps, schema_editor):
    FinanceEntry = apps.get_model("dashboard", "FinanceEntry")
    WorkerAdvance = apps.get_model("dashboard", "WorkerAdvance")

    for payment in WorkerAdvance.objects.all().order_by("id"):
        finance_entry = (
            FinanceEntry.objects.filter(
                related_worker_payment__isnull=True,
                entry_type="expense",
                category="Ishchi to'lovi",
                amount=payment.amount,
                currency=payment.currency,
                entry_date=payment.advance_date,
                note__contains=payment.worker.full_name,
            )
            .order_by("-id")
            .first()
        )
        if finance_entry:
            finance_entry.related_worker_payment_id = payment.id
            finance_entry.save(update_fields=["related_worker_payment"])


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0006_financecategory_entry_type_back"),
    ]

    operations = [
        migrations.AddField(
            model_name="financeentry",
            name="related_worker_payment",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="finance_entries",
                to="dashboard.workeradvance",
                verbose_name="Bog'liq ishchi to'lovi",
            ),
        ),
        migrations.RunPython(backfill_worker_payment_finance_links, migrations.RunPython.noop),
    ]
