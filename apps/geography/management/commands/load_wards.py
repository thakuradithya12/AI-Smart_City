import json
from datetime import date
from pathlib import Path

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.geography.geometry import has_area_overlap, validated_multi_polygon
from apps.geography.models import Ward


class Command(BaseCommand):
    help = "Load source-documented GeoJSON wards after validating geometry and active overlaps."

    def add_arguments(self, parser):
        parser.add_argument("geojson", type=Path)
        parser.add_argument("--source", required=True)
        parser.add_argument("--effective-from", required=True, type=date.fromisoformat)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        source = options["source"].strip()
        effective_from = options["effective_from"]
        if not source or len(source) > 240:
            raise CommandError("--source must contain 1 to 240 characters identifying the boundary source.")
        try:
            document = json.loads(options["geojson"].read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CommandError(f"Could not read GeoJSON: {exc}") from exc
        if (not isinstance(document, dict) or document.get("type") != "FeatureCollection"
                or not isinstance(document.get("features"), list)):
            raise CommandError("Input must be a GeoJSON FeatureCollection.")

        wards = []
        names = set()
        for index, feature in enumerate(document["features"], start=1):
            try:
                name = feature["properties"]["name"].strip()
                geometry = GEOSGeometry(json.dumps(feature["geometry"]), srid=4326)
                boundary = validated_multi_polygon(geometry)
            except (
                KeyError, TypeError, AttributeError, ValueError,
                GEOSException, SuspiciousOperation, ValidationError,
            ) as exc:
                raise CommandError(f"Feature {index} has no valid name or ward geometry: {exc}") from exc
            if not name or len(name) > 120:
                raise CommandError(f"Feature {index} must have a ward name of 1 to 120 characters.")
            if name in names:
                raise CommandError(f"GeoJSON contains duplicate ward name '{name}'.")
            names.add(name)
            wards.append(Ward(
                name=name,
                boundary=boundary,
                source=source,
                effective_from=effective_from,
                effective_to=None,
            ))
        if not wards:
            raise CommandError("GeoJSON contains no ward features.")

        for index, ward in enumerate(wards):
            for other in wards[index + 1:]:
                if has_area_overlap(ward.boundary, other.boundary):
                    raise CommandError(f"Ward boundaries '{ward.name}' and '{other.name}' overlap.")
        existing = Ward.objects.active_on(effective_from).exclude(name__in=names)
        for ward in wards:
            for other in existing.iterator():
                if has_area_overlap(ward.boundary, other.boundary):
                    raise CommandError(f"Ward boundary '{ward.name}' overlaps active ward '{other.name}'.")

        for index, ward in enumerate(wards):
            existing_ward = Ward.objects.filter(name=ward.name).first()
            if existing_ward:
                # Validate updates on the persisted instance so unique checks exclude itself.
                existing_ward.boundary = ward.boundary
                existing_ward.source = ward.source
                existing_ward.effective_from = ward.effective_from
                existing_ward.effective_to = None
                ward = existing_ward
                wards[index] = ward
            try:
                ward.full_clean()
            except ValidationError as exc:
                raise CommandError(f"Ward '{ward.name}' failed model validation: {exc}") from exc
        if options["dry_run"]:
            self.stdout.write(f"Validated {len(wards)} ward(s); dry run; no database changes.")
            return

        with transaction.atomic():
            for ward in wards:
                existing_ward = Ward.objects.filter(name=ward.name).first()
                if existing_ward:
                    existing_ward.boundary = ward.boundary
                    existing_ward.source = ward.source
                    existing_ward.effective_from = ward.effective_from
                    existing_ward.effective_to = None
                    existing_ward.full_clean()
                    existing_ward.save()
                else:
                    ward.save()
        self.stdout.write(f"Loaded {len(wards)} ward(s).")
