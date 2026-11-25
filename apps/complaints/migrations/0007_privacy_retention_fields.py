from django.contrib.gis.db import models as gis_models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("complaints", "0006_complaint_sla_fields")]

    operations = [
        migrations.AlterField(
            model_name="complaint",
            name="location",
            field=gis_models.PointField(blank=True, null=True, srid=4326),
        ),
        migrations.AddField(
            model_name="complaint",
            name="consent_version",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AddField(
            model_name="complaint",
            name="retention_purged_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
