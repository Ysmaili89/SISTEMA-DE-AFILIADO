# routes/__init__.py
from flask import Blueprint

# Crear el Blueprint.
bp = Blueprint('rutas', __name__)

# Importar los módulos de rutas DESPUÉS de crear el Blueprint.
# El comentario '# noqa: F401' suprime advertencias de linters sobre importaciones no utilizadas.
from . import public_routes  # noqa: F401
from . import admin_routes   # noqa: F401
from . import api_routes     # noqa: F401
# Asegúrate de que los nombres de los archivos coincidan con lo que estás importando.
# Por ejemplo, si tienes un archivo "afiliados_routes.py", entonces la importación es correcta.