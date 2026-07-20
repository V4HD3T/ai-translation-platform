"""Guards against migration drift (v0.0.9): the Alembic chain must build
exactly the schema the SQLModel metadata describes. Tests themselves
create their databases with create_all (fast, isolated), so without this
check a model change that forgot its migration would sail through the
whole suite and only fail on a real deployment."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlmodel import SQLModel

import app.models  # noqa: F401  -- side effect: populates SQLModel.metadata

BACKEND_DIR = Path(__file__).resolve().parent.parent


def test_alembic_head_matches_sqlmodel_metadata(tmp_path):
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    inspector = inspect(create_engine(url))
    migrated = {
        table: {column["name"] for column in inspector.get_columns(table)}
        for table in inspector.get_table_names()
        if table != "alembic_version"
    }
    expected = {
        name: set(table.columns.keys()) for name, table in SQLModel.metadata.tables.items()
    }
    assert migrated == expected
