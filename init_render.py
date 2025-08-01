# init_render.py
from app import create_app, create_initial_data

app = create_app()

print("🚀 Iniciando el proceso de inicialización de la base de datos en Render.")
create_initial_data(app)
print("✅ Proceso de inicialización completado.")