from django.core.management.base import BaseCommand

from apps.complaints.models import Evidence
from apps.complaints.services import private_storage


def stored_media_paths(prefix=""):
    """Walk private storage without changing any files."""
    try:
        directories, files = private_storage.listdir(prefix)
    except FileNotFoundError:
        return
    for filename in files:
        yield f"{prefix}/{filename}" if prefix else filename
    for directory in directories:
        child = f"{prefix}/{directory}" if prefix else directory
        yield from stored_media_paths(child)


class Command(BaseCommand):
    help = "Report orphaned or missing private evidence files without modifying storage."

    def handle(self, *args, **options):
        referenced = set()
        for original, display, thumbnail in Evidence.objects.values_list(
            "original_path", "display_path", "thumbnail_path"
        ).iterator():
            referenced.update(path for path in (original, display, thumbnail) if path)
        actual = set(stored_media_paths())
        orphaned = sorted(actual - referenced)
        missing = sorted(referenced - actual)
        if not orphaned and not missing:
            self.stdout.write("No orphaned or missing private media files found.")
            return
        for path in orphaned:
            self.stdout.write(f"Orphaned private file: {path}")
        for path in missing:
            self.stdout.write(self.style.WARNING(f"Missing referenced private file: {path}"))
        self.stdout.write(f"Report only: {len(orphaned)} orphaned, {len(missing)} missing; no files changed.")
