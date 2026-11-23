from django.contrib.gis.geos import MultiPolygon
from django.core.exceptions import ValidationError


def validated_multi_polygon(geometry):
    """Validate the supported WGS84 ward shapes and normalize polygons for storage."""
    if geometry is None or geometry.empty:
        raise ValidationError("Ward boundary must not be empty.")
    if geometry.srid != 4326:
        raise ValidationError("Ward boundary must use SRID 4326.")
    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValidationError("Ward boundary must be a Polygon or MultiPolygon.")
    xmin, ymin, xmax, ymax = geometry.extent
    if xmin < -180 or xmax > 180 or ymin < -90 or ymax > 90:
        raise ValidationError("Ward coordinates must be longitude/latitude values in SRID 4326.")
    if not geometry.valid:
        raise ValidationError("Ward boundary geometry is invalid or self-intersecting.")
    if geometry.geom_type == "Polygon":
        return MultiPolygon(geometry, srid=4326)
    return geometry


def has_area_overlap(first, second):
    """Return true when polygon interiors overlap; shared borders alone are allowed."""
    if not first.intersects(second):
        return False
    intersection = first.intersection(second)
    return not intersection.empty and intersection.area > 0
