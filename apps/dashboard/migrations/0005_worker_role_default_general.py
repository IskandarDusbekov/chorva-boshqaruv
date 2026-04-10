from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0004_workerjobtype_remove_financecategory_entry_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="worker",
            name="role",
            field=models.CharField(
                choices=[
                    ("worker", "Ishchi"),
                    ("milker", "Sut sog'uvchi"),
                    ("shepherd", "Cho'pon"),
                    ("manager", "Ish boshqaruvchi"),
                ],
                default="worker",
                max_length=20,
                verbose_name="Ish turi",
            ),
        ),
    ]
