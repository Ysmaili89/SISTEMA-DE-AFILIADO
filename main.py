# main.py
from app import create_app

# Gunicorn busca un objeto llamado 'app' en este módulo.
# Por eso, creamos la instancia aquí.
app = create_app()