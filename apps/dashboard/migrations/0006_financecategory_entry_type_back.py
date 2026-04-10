from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0005_worker_role_default_general"),
    ]

    operations = [
        migrations.AddField(
            model_name="financecategory",
            name="entry_type",
            field=models.CharField(
                choices=[("income", "Kirim"), ("expense", "Chiqim")],
                default="expense",
                max_length=10,
                verbose_name="Turi",
            ),
        ),
        migrations.AlterModelOptions(
            name="financecategory",
            options={
                "ordering": ["entry_type", "name"],
                "verbose_name": "Moliya kategoriyasi",
                "verbose_name_plural": "Moliya kategoriyalari",
            },
        ),
    ]
