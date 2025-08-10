from flask import Blueprint

# Crear un blueprint para las rutas
bp = Blueprint('rutas', __name__)

# Importar los módulos con las rutas para registrarlas en el blueprint
from . import afiliados_routes  # noqa: F401
from . import productos_routes  # noqa: F401
