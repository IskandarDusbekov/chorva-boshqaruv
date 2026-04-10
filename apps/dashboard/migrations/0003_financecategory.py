from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0002_finance_worker_milk_updates"),
    ]

    operations = [
        migrations.CreateModel(
            name="FinanceCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True, verbose_name="Kategoriya nomi")),
                ("entry_type", models.CharField(choices=[("income", "Kirim"), ("expense", "Chiqim")], max_length=10, verbose_name="Turi")),
                ("is_active", models.BooleanField(default=True, verbose_name="Faol")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["entry_type", "name"],
                "verbose_name": "Moliya kategoriyasi",
                "verbose_name_plural": "Moliya kategoriyalari",
            },
        ),
    ]
