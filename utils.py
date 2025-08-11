# utils.py
import re
from unicodedata import normalize
from werkzeug.security import generate_password_hash
from models import User
from extensions import db

def slugify(text):
    """
    Convierte el texto en un slug compatible con URL.

    Args:
        text (str): La cadena de texto a convertir.

    Returns:
        str: El slug generado.
    """
    if not isinstance(text, str):
        return ""
    # Normalizar caracteres Unicode para letras acentuadas, etc.
    # Por ejemplo, 'á' se convierte en 'a'
    text = normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    # Reemplazar los caracteres no alfanuméricos (excepto guiones) con nada
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    # Reemplazar espacios y guiones múltiples con un solo guión
    text = re.sub(r'[-\s]+', '-', text)
    return text

def _create_initial_data(app):
    """
    Crea un usuario administrador inicial si no existe.

    Args:
        app (Flask.app): La instancia de la aplicación Flask.
    """
    with app.app_context():
        # Busca si ya existe un usuario con el nombre de usuario 'admin'
        if not User.query.filter_by(username='admin').first():
            # Si no existe, crea un nuevo usuario administrador
            admin_user = User(
                username='admin',
                # Genera un hash seguro para la contraseña
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                is_admin=True
            )
            # Agrega el usuario a la sesión de la base de datos
            db.session.add(admin_user)
            # Guarda los cambios en la base de datos
            db.session.commit()
            print("✔ Usuario administrador creado.")
        else:
            print("ℹ️ Usuario administrador ya existe.")