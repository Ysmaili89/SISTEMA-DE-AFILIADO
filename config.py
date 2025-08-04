import os

class Config:
    """Clase de configuración para la aplicación."""
    
    # Clave secreta para la seguridad de la sesión, etc.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_por_defecto_solo_para_desarrollo_local'
    
    # Obtener la URL de la base de datos de la variable de entorno
    # Priorizar SQLite local para el desarrollo si no se establece DATABASE_URL
    uri = os.getenv('DATABASE_URL')
    
    # Si usa PostgreSQL, ajuste el esquema para psycopg 3 y SQLAlchemy 2.x
    if uri and uri.startswith("postgresql://"):
        SQLALCHEMY_DATABASE_URI = uri.replace("postgresql://", "postgresql+psycopg://", 1)
    else:
        # Predeterminado a SQLite si DATABASE_URL no está configurado o no es PostgreSQL
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False