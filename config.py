import os

class Config:
    # La SECRET_KEY es crucial para la seguridad de Flask y Flask-Login.
    # DEBE ser una variable de entorno en producción.
    # En desarrollo, puedes establecerla en tu archivo .env
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_por_defecto_solo_para_desarrollo_local'
    
    # MODIFICACIÓN CLAVE AQUÍ:
    # Prioriza la variable de entorno SQLALCHEMY_DATABASE_URI del .env.
    # Si no está definida en .env, usa 'sqlite:///app.db' por defecto.
    # Esto asegura que siempre se use SQLite a menos que explícitamente configures otra cosa.
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI') or \
                              'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Otras configuraciones que podrías necesitar:
    # MAIL_SERVER = 'smtp.googlemail.com'
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USERNAME = os.environ.get('EMAIL_USER')
    # MAIL_PASSWORD = os.environ.get('EMAIL_PASS')