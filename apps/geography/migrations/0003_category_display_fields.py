from django.db import migrations, models


def populate_category_labels(apps, schema_editor):
    Category = apps.get_model("geography", "Category")
    for category in Category.objects.all().iterator():
        category.label = category.name.replace("_", " ").title()
        category.save(update_fields=["label"])


class Migration(migrations.Migration):
    dependencies = [("geography", "0002_ward_ward_effective_window_valid")]

    operations = [
        migrations.AddField(
            model_name="category",
            name="label",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="category",
            name="icon",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="category",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(populate_category_labels, migrations.RunPython.noop),
    ]
