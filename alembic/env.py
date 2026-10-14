import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.app.core.config import settings
from src.app.core.database import Base, normalize_database_url

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set SQLAlchemy URL dynamically from application settings
target_url = normalize_database_url(settings.DATABASE_URL)
config.set_main_option("sqlalchemy.url", target_url)

# Ensure all models are imported so Base.metadata contains the full schema
import src.app.models  # noqa: F401

target_metadata = Base.metadata

# Schemas managed internally by Supabase that Alembic MUST ignore
SUPABASE_INTERNAL_SCHEMAS = {
    "auth",
    "storage",
    "realtime",
    "vault",
    "graphql",
    "graphql_public",
    "pgsodium",
    "pgsodium_masks",
    "supabase_functions",
    "supabase_migrations",
}


def include_object(object, name, type_, reflected, compare_to):
    """Filter callback to ensure Alembic only manages the 'public' schema and

    ignores Supabase internal system tables and schemas.
    """
    # If the object belongs to an internal Supabase schema, ignore it
    if hasattr(object, "schema") and object.schema in SUPABASE_INTERNAL_SCHEMAS:
        return False

    # Ignore Supabase default tables that might appear without explicit schema
    if type_ == "table" and name in {"schema_migrations", "spatial_ref_sys"}:
        return False

    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        include_schemas=False,
        version_table_schema="public",
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        include_schemas=False,
        version_table_schema="public",
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
