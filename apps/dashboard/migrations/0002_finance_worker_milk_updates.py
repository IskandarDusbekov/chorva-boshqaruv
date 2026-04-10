from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MilkPrice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("effective_from", models.DateField(verbose_name="Amal qilish sanasi")),
                ("price_per_liter", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="1 litr narxi")),
                ("currency", models.CharField(choices=[("UZS", "UZS"), ("USD", "USD")], default="UZS", max_length=3)),
                ("note", models.CharField(blank=True, max_length=255, verbose_name="Izoh")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-effective_from", "-created_at"],
                "verbose_name": "Sut narxi",
                "verbose_name_plural": "Sut narxlari",
            },
        ),
        migrations.AddField(
            model_name="financeentry",
            name="received_at",
            field=models.DateField(blank=True, null=True, verbose_name="Qabul qilingan sana"),
        ),
        migrations.AddField(
            model_name="financeentry",
            name="status",
            field=models.CharField(
                choices=[("pending", "Kutilmoqda"), ("confirmed", "Qabul qilingan"), ("cancelled", "Bekor qilingan")],
                default="confirmed",
                max_length=10,
                verbose_name="Holat",
            ),
        ),
        migrations.AlterField(
            model_name="financeentry",
            name="source",
            field=models.CharField(
                choices=[("default", "Default hisob"), ("internal", "Ichki hisob"), ("external", "Tashqi hisob")],
                default="internal",
                max_length=10,
                verbose_name="Hisob manbasi",
            ),
        ),
        migrations.AddField(
            model_name="worker",
            name="payday_day",
            field=models.PositiveSmallIntegerField(default=30, verbose_name="Oylik beriladigan kun"),
        ),
        migrations.AddField(
            model_name="worker",
            name="started_at",
            field=models.DateField(blank=True, null=True, verbose_name="Ish boshlagan sana"),
        ),
        migrations.AddField(
            model_name="workeradvance",
            name="month_reference",
            field=models.DateField(blank=True, null=True, verbose_name="Qaysi oy uchun"),
        ),
        migrations.AddField(
            model_name="workeradvance",
            name="payment_type",
            field=models.CharField(
                choices=[("advance", "Avans"), ("salary", "Ish haqi")],
                default="advance",
                max_length=10,
                verbose_name="To'lov turi",
            ),
        ),
    ]
