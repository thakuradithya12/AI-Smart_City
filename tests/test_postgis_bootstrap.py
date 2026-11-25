from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.db import DatabaseError, migrations


def test_initial_geography_migration_enables_postgis_before_spatial_tables():
    migration_module = import_module("apps.geography.migrations.0001_initial")
    migration = migration_module.Migration("0001_initial", "geography")

    assert migration.atomic is True
    assert isinstance(migration.operations[0], migrations.RunPython)
    schema_editor = SimpleNamespace(
        connection=SimpleNamespace(vendor="postgresql"), execute=Mock()
    )

    migration_module.ensure_postgis(None, schema_editor)

    schema_editor.execute.assert_called_once_with(
        "CREATE EXTENSION IF NOT EXISTS postgis"
    )


def test_postgis_permission_failure_has_an_actionable_message():
    migration_module = import_module("apps.geography.migrations.0001_initial")
    schema_editor = SimpleNamespace(
        connection=SimpleNamespace(vendor="postgresql"),
        execute=Mock(side_effect=DatabaseError("permission denied")),
    )

    with pytest.raises(RuntimeError, match="database role must be allowed.*CREATE EXTENSION postgis"):
        migration_module.ensure_postgis(None, schema_editor)


def test_non_postgresql_database_fails_before_spatial_schema_creation():
    migration_module = import_module("apps.geography.migrations.0001_initial")
    schema_editor = SimpleNamespace(connection=SimpleNamespace(vendor="sqlite"))

    with pytest.raises(RuntimeError, match="PostGIS is required"):
        migration_module.ensure_postgis(None, schema_editor)
