# migrations/env.py

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Esto es importante: importa tu aplicación Flask y la base de datos
import sys
sys.path.append(os.getcwd()) # Asegúrate de que el directorio raíz del proyecto esté en el path
from app import create_app # Importa tu función create_app
# from models import Base # Si tienes una Base declarativa para tus modelos

# Esto es para que Alembic pueda acceder a la configuración de tu app Flask
# Crea una instancia de tu aplicación
app = create_app()
app.app_context().push() # Empuja el contexto de la aplicación

# Obtén la configuración de Alembic del archivo alembic.ini
config = context.config

# Configura los loggers
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Aquí es donde Alembic obtiene los metadatos de tus modelos
# Si usas db.Model de Flask-SQLAlchemy, esto es lo que necesitas:
from extensions import db # Importa tu instancia de db
target_metadata = db.metadata

# Si tienes una base declarativa personalizada, usarías:
# from myapp.mymodel import Base
# target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By omitting the Engine object, the context
    is able to emit SQL operations without connecting to a database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # **ESTA ES LA PARTE CLAVE:** Obtener la URL de la base de datos de la configuración de tu aplicación Flask
    # Esto asegura que Alembic use la misma URL que tu aplicación
    connectable = engine_from_config(
        app.config.get("SQLALCHEMY_DATABASE_URI"), # <-- ¡Aquí está la clave!
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True, # Importante para ALTER TABLE en SQLite/PostgreSQL
            # ... otras configuraciones
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()