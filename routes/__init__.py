# routes/__init__.py

from flask import Blueprint

# Crear un blueprint para las rutas
bp = Blueprint('routes', __name__)

# Importar los módulos con las rutas para registrarlas en el blueprint
from . import afiliados_routes
from . import productos_routes

# Aquí podrías también importar más módulos de rutas si tienes
