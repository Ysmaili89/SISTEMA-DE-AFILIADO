import os

class Config:
    # La clave secreta para seguridad (Flask, Flask-Login).
    # Debe ser una variable de entorno en producción.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_por_defecto'
    
    # Configuración de la base de datos
    # En producción se usará la variable de entorno
    # Para desarrollo local, usaremos esta URI por defecto
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost/mydb?client_encoding=utf8'
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False