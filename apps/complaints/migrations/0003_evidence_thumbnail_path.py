from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("complaints", "0002_gps_accuracy_decimal")]

    operations = [
        migrations.AddField(
            model_name="evidence",
            name="thumbnail_path",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
    ]
