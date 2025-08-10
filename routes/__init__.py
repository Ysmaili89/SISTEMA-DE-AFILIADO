# Código corregido
from flask import Blueprint

# Importaciones locales para registrar las rutas en el Blueprint
from . import afiliados_routes
from . import productos_routes

# Crear un blueprint para las rutas
bp = Blueprint('rutas', __name__)

# Aquí puedes añadir más módulos de rutas si los tienes