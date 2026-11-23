from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("complaints", "0004_complaint_list_indexes")]

    operations = [
        migrations.AddField(
            model_name="complaint",
            name="landmark",
            field=models.CharField(blank=True, max_length=160),
        ),
    ]
