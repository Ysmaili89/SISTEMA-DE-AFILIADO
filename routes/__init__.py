# routes/__init__.py
from flask import Blueprint

# Crear el Blueprint.
bp = Blueprint('rutas', __name__)

# Importar los módulos de rutas después de crear el Blueprint.
# El comentario '# noqa: F401' es para que los linters (como Ruff)
# no muestren un error de importación no utilizada.
from . import afiliados_routes # noqa: F401
from . import productos_routes # noqa: F401
from . import public # noqa: F401
from . import api # noqa: F401
from . import admin # noqa: F401