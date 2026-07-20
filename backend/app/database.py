from pathlib import Path

from sqlmodel import Session, create_engine

from app.config import settings

BACKEND_DIR = Path(__file__).resolve().parent.parent

connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)
engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)


def init_db() -> None:
    """Brings the database schema to the current Alembic head (v0.0.9;
    previously SQLModel.metadata.create_all).

    create_all can only ever add missing *tables* -- it cannot express
    "add a column to an existing table", which is exactly what this
    version needs (user.is_admin). Migrations are the real mechanism for
    schema evolution, so startup now applies them instead.

    The Config is built programmatically (no alembic.ini read) for two
    reasons: to inject the URL from the app's own settings, and to skip
    alembic.ini's [loggers] section, which would otherwise reconfigure
    the app's logging on every startup.

    Note for pre-0.0.9 databases: they have all the tables but no
    alembic_version stamp, so the initial migration would collide with
    existing tables. Dev data is throwaway -- delete app.db -- or run
    `alembic stamp 0001` once and upgrade normally from there.
    """
    from alembic import command
    from alembic.config import Config

    cfg = Config()
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, "head")


def get_session():
    """FastAPI dependency: yields a database session for each request."""
    with Session(engine) as session:
        yield session
