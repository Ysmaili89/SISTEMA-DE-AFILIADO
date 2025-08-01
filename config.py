import os

class Config:
    # Clave secreta de seguridad para sesiones, tokens, etc.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_por_defecto_solo_para_desarrollo_local'
    
    # URL de la base de datos: primero intenta con DATABASE_URL (Render), si no usa SQLite local.
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Otras posibles configuraciones
    # MAIL_SERVER = 'smtp.googlemail.com'
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USERNAME = os.environ.get('EMAIL_USER')
    # MAIL_PASSWORD = os.environ.get('EMAIL_PASS')
