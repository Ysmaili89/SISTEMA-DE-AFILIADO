# init_db.py

from main import app  # Asegúrate que 'app' esté definido en main.py
from models import db  # Tu instancia de SQLAlchemy

# Crear todas las tablas
with app.app_context():
    db.create_all()
    print("✅ Base de datos inicializada correctamente (tablas creadas).")
