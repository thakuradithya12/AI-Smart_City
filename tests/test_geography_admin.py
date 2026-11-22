from django.contrib.gis.admin import GISModelAdmin

from apps.geography.admin import WardAdmin


def test_ward_admin_uses_geospatial_editor():
    assert issubclass(WardAdmin, GISModelAdmin)
