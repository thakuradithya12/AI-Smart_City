import pytest

from config.database import POSTGIS_ENGINE, database_config_from_url


def test_database_url_is_decoded_and_uses_postgis_engine():
    config = database_config_from_url(
        "postgresql://demo%40user:p%2Fss@ep-example.neon.tech/city%20demo"
        "?sslmode=require&channel_binding=require"
    )

    assert config == {
        "ENGINE": POSTGIS_ENGINE,
        "NAME": "city demo",
        "USER": "demo@user",
        "PASSWORD": "p/ss",
        "HOST": "ep-example.neon.tech",
        "PORT": "5432",
        "OPTIONS": {"sslmode": "require", "channel_binding": "require"},
    }


def test_database_url_uses_explicit_port():
    config = database_config_from_url("postgres://city:secret@localhost:5544/city")

    assert config["PORT"] == "5544"


@pytest.mark.parametrize(
    ("database_url", "message"),
    [
        ("mysql://user:pass@host/db", "postgres:// or postgresql://"),
        ("postgresql:///city", "database name and host"),
        ("postgresql://user:pass@host", "database name and host"),
        ("postgresql://user:pass@host:bad/db", "invalid port"),
    ],
)
def test_invalid_database_url_fails_with_a_safe_error(database_url, message):
    with pytest.raises(ValueError, match=message):
        database_config_from_url(database_url)
