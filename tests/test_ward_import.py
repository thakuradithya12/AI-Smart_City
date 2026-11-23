import json

import pytest
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.geography.models import Ward


def polygon_feature(name, coordinates):
    return {"type": "Feature", "properties": {"name": name},
            "geometry": {"type": "Polygon", "coordinates": coordinates}}


def write_geojson(tmp_path, *features):
    path = tmp_path / "wards.geojson"
    path.write_text(json.dumps({"type": "FeatureCollection", "features": list(features)}), encoding="utf-8")
    return path


def square(name, left, bottom, right, top):
    return polygon_feature(name, [[
        [left, bottom], [right, bottom], [right, top], [left, top], [left, bottom],
    ]])


@pytest.mark.django_db
def test_load_wards_coerces_polygon_to_multipolygon_and_is_idempotent(tmp_path):
    path = write_geojson(tmp_path, square("North Ward", 0, 0, 1, 1))
    call_command("load_wards", str(path), source="municipal source supplied by fixture", effective_from="2026-01-01")
    ward = Ward.objects.get(name="North Ward")
    assert isinstance(ward.boundary, MultiPolygon)
    assert ward.source == "municipal source supplied by fixture"
    call_command("load_wards", str(path), source="municipal source supplied by fixture", effective_from="2026-01-01")
    assert Ward.objects.filter(name="North Ward").count() == 1


@pytest.mark.django_db
def test_load_wards_dry_run_does_not_write(tmp_path):
    path = write_geojson(tmp_path, square("Dry Ward", 0, 0, 1, 1))
    call_command("load_wards", str(path), source="fixture source", effective_from="2026-01-01", dry_run=True)
    assert not Ward.objects.exists()


@pytest.mark.django_db
def test_load_wards_accepts_valid_multipolygon(tmp_path):
    geometry = {"type": "MultiPolygon", "coordinates": [
        [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]],
    ]}
    feature = {"type": "Feature", "properties": {"name": "Split Ward"}, "geometry": geometry}
    path = write_geojson(tmp_path, feature)
    call_command("load_wards", str(path), source="fixture source", effective_from="2026-01-01")
    assert Ward.objects.get(name="Split Ward").boundary.num_geom == 2


@pytest.mark.django_db
def test_load_wards_rejects_non_polygon_geometry(tmp_path):
    feature = {"type": "Feature", "properties": {"name": "Point Ward"},
               "geometry": {"type": "Point", "coordinates": [0, 0]}}
    path = write_geojson(tmp_path, feature)
    with pytest.raises(CommandError):
        call_command("load_wards", str(path), source="fixture source", effective_from="2026-01-01")


@pytest.mark.django_db
@pytest.mark.parametrize("geometry", [
    {"type": "Polygon", "coordinates": []},
    {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [0, 1], [1, 0], [0, 0]]]},
])
def test_load_wards_rejects_empty_and_self_intersecting_geometry(tmp_path, geometry):
    feature = {"type": "Feature", "properties": {"name": "Invalid Ward"}, "geometry": geometry}
    path = write_geojson(tmp_path, feature)
    with pytest.raises(CommandError):
        call_command("load_wards", str(path), source="fixture source", effective_from="2026-01-01")
    assert not Ward.objects.exists()


@pytest.mark.django_db
def test_load_wards_refuses_overlapping_active_wards(tmp_path):
    path = write_geojson(tmp_path, square("Ward A", 0, 0, 2, 2), square("Ward B", 1, 1, 3, 3))
    with pytest.raises(CommandError, match="overlap"):
        call_command("load_wards", str(path), source="fixture source", effective_from="2026-01-01")
    assert not Ward.objects.exists()


@pytest.mark.django_db
def test_load_wards_refuses_overlap_with_existing_active_ward(tmp_path):
    existing = Polygon(((0, 0), (2, 0), (2, 2), (0, 2), (0, 0)))
    Ward.objects.create(name="Existing", boundary=MultiPolygon(existing, srid=4326),
                        source="fixture source", effective_from="2026-01-01")
    path = write_geojson(tmp_path, square("New Ward", 1, 1, 3, 3))
    with pytest.raises(CommandError, match="overlap"):
        call_command("load_wards", str(path), source="fixture source", effective_from="2026-02-01")


@pytest.mark.django_db
def test_ward_model_validation_rejects_active_spatial_overlap():
    first = Polygon(((0, 0), (2, 0), (2, 2), (0, 2), (0, 0)))
    Ward.objects.create(name="Model A", boundary=MultiPolygon(first, srid=4326),
                        source="fixture source", effective_from="2026-01-01")
    second = Polygon(((1, 1), (3, 1), (3, 3), (1, 3), (1, 1)))
    ward = Ward(name="Model B", boundary=MultiPolygon(second, srid=4326),
                source="fixture source", effective_from="2026-02-01")
    with pytest.raises(ValidationError, match="overlap"):
        ward.full_clean()
