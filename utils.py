import re
from unicodedata import normalize
from werkzeug.security import generate_password_hash
from models import User
from extensions import db

def slugify(text):
    """
    Convierte el texto en un slug compatible con URL.
    """
    if not isinstance(text, str):
        return ""
    # Normalizar caracteres Unicode para letras acentuadas, etc.
    text = normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    # Reemplazar los caracteres no alfanuméricos con guiones
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    # Reemplazar espacios y guiones múltiples con un solo guión
    text = re.sub(r'[-\s]+', '-', text)
    return text

def _create_initial_data(app):
    """
    Crea un usuario administrador inicial si no existe.
    """
    with app.app_context():
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✔ Usuario administrador creado.")
        else:
            print("ℹ️ Usuario administrador ya existe.")