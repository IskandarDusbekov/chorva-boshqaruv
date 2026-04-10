from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0003_financecategory"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="financecategory",
            name="entry_type",
        ),
        migrations.AlterModelOptions(
            name="financecategory",
            options={
                "ordering": ["name"],
                "verbose_name": "Moliya kategoriyasi",
                "verbose_name_plural": "Moliya kategoriyalari",
            },
        ),
        migrations.CreateModel(
            name="WorkerJobType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True, verbose_name="Ish turi nomi")),
                ("is_active", models.BooleanField(default=True, verbose_name="Faol")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["name"],
                "verbose_name": "Ish turi",
                "verbose_name_plural": "Ish turlari",
            },
        ),
        migrations.AddField(
            model_name="worker",
            name="job_type",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="workers", to="dashboard.workerjobtype", verbose_name="Maxsus ish turi"),
        ),
    ]
