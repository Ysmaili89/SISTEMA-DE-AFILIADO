# config.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

# --- Clase de configuración principal ---
class Config:
    """Clase base de configuración."""
    # SECRET_KEY es fundamental para la seguridad, se toma del entorno.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_por_defecto'
    
    # SQLALCHEMY_DATABASE_URI se toma del entorno.
    # El valor por defecto es para desarrollo local con PostgreSQL.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost/mydb?client_encoding=utf8'
    
    # Se deshabilita para evitar advertencias.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# --- Inicialización de la aplicación y extensiones ---
# Esto es para uso local si el archivo se ejecuta directamente.
# En una aplicación real con el patrón de fábrica, esta configuración
# se haría dentro de la función create_app().
app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Definición de modelos (Ejemplo) ---
# Se mantiene tu modelo de Afiliado, pero se corrige la sintaxis.
class Afiliado(db.Model):
    """Modelo para representar a un Afiliado."""
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Afiliado {self.nombre}>'

# --- Ejecución principal ---
if __name__ == '__main__':
    # Se ejecuta la aplicación si el archivo se ejecuta directamente.
    # Esto es útil para pruebas locales.
    app.run(debug=True)
