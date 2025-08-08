
# Importa la función de fábrica de aplicaciones
from app import create_app

# Crea la instancia de la aplicación
app = create_app()

# Nota: Este archivo es el punto de entrada principal para servidores como Gunicorn.
# La variable 'app' debe ser expuesta a nivel global para que el servidor pueda encontrarla.
