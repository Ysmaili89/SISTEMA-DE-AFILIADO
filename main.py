from app import create_app, create_initial_data

app = create_app()

# Crear tablas y datos iniciales si no existen (solo en Render o producción)
create_initial_data(app)
