"""Helpers for configuring Django's PostGIS backend from DATABASE_URL."""

from urllib.parse import parse_qsl, unquote, urlsplit


POSTGIS_ENGINE = "django.contrib.gis.db.backends.postgis"


def database_config_from_url(database_url):
    """Parse a PostgreSQL URL into Django settings without an extra package."""
    try:
        parsed = urlsplit(database_url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("DATABASE_URL has an invalid port or URL encoding.") from exc

    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("DATABASE_URL must use the postgres:// or postgresql:// scheme.")

    name = unquote(parsed.path.lstrip("/"))
    if not parsed.hostname or not name:
        raise ValueError("DATABASE_URL must include a database name and host.")

    options = dict(parse_qsl(parsed.query, keep_blank_values=True))
    config = {
        "ENGINE": POSTGIS_ENGINE,
        "NAME": name,
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname,
        "PORT": str(port or 5432),
    }
    if options:
        config["OPTIONS"] = options
    return config
