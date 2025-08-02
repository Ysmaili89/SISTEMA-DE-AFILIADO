import os

class Config:
    # Clave secreta para seguridad de sesiones, etc.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_por_defecto_solo_para_desarrollo_local'
    
    # Obtener la URL de la base de datos desde variable de entorno
    uri = os.getenv('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')

    # Si usas PostgreSQL, ajustar esquema para psycopg 3 y SQLAlchemy 2.x
    if uri.startswith("postgresql://"):
        uri = uri.replace("postgresql://", "postgresql+psycopg://", 1)

    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
