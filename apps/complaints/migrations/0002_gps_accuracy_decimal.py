from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("complaints", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="complaint",
            name="gps_accuracy_m",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
    ]
