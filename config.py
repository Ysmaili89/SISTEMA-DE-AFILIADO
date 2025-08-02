import os

class Config:
    # Clave secreta de seguridad para sesiones, tokens, etc.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_por_defecto_solo_para_desarrollo_local'
    
    # Obtener la URL original
    uri = os.getenv('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')

    # Reemplazar el esquema si es PostgreSQL
    if uri.startswith("postgresql://"):
        uri = uri.replace("postgresql://", "postgresql+psycopg://", 1)

    SQLALCHEMY_DATABASE_URI = uri

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Otras posibles configuraciones
    # MAIL_SERVER = 'smtp.googlemail.com'
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USERNAME = os.environ.get('EMAIL_USER')
    # MAIL_PASSWORD = os.environ.get('EMAIL_PASS')
