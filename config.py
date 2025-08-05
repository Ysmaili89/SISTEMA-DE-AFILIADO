import os

class Config:
    # La clave secreta para seguridad (Flask, Flask-Login).
    # Debe ser una variable de entorno en producciÃ³n.
    # En desarrollo puede estar en un archivo .env
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_por_defecto_solo_para_desarrollo_local'
    
    # ConfiguraciÃ³n de la base de datos
    # En producciÃ³n usa PostgreSQL, MySQL, etc.
    # En desarrollo usa SQLite local
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Para evitar advertencias innecesarias

    # Configuraciones opcionales para correo (SMTP)
    # MAIL_SERVER = 'smtp.googlemail.com'
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USERNAME = os.environ.get('EMAIL_USER')
    # MAIL_PASSWORD = os.environ.get('EMAIL_PASS')
