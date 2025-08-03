# config.py
import os

class Config:
    """Clase de configuración para la aplicación."""
    
    # Secret key for session security, etc.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_por_defecto_solo_para_desarrollo_local'
    
    # Get database URL from environment variable
    # Prioritize local SQLite for development if DATABASE_URL is not set
    uri = os.getenv('DATABASE_URL')
    
    # If using PostgreSQL, adjust scheme for psycopg 3 and SQLAlchemy 2.x
    if uri and uri.startswith("postgresql://"):
        SQLALCHEMY_DATABASE_URI = uri.replace("postgresql://", "postgresql+psycopg://", 1)
    else:
        # Default to SQLite if DATABASE_URL is not set or is not PostgreSQL
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False