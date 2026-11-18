from logging.config import fileConfig

from alembic import context
from flask import current_app

config = context.config
fileConfig(config.config_file_name)

database = current_app.extensions["migrate"].db
target_metadata = database.metadata


def get_engine():
    try:
        return database.engine
    except (AttributeError, TypeError):
        return database.get_engine()


def get_engine_url():
    return get_engine().url.render_as_string(hide_password=False).replace("%", "%%")


def run_migrations_offline():
    context.configure(
        url=get_engine_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with get_engine().connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
