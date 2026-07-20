"""Alembic environment.

The migration target is the SQLModel metadata (app.models), and the
database URL comes from the app's own settings so there is exactly one
source of truth -- unless a caller injected a URL programmatically via
config.set_main_option (init_db at startup, and the migration-drift test
both do this).

render_as_batch=True matters on SQLite: most ALTER TABLE operations
aren't supported natively there, so Alembic rebuilds tables through a
temp copy ("batch mode") instead.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make `import app...` work no matter where alembic is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import SQLModel  # noqa: E402

from app.config import settings  # noqa: E402
import app.models  # noqa: E402,F401  -- side effect: populates SQLModel.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, render_as_batch=True
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
