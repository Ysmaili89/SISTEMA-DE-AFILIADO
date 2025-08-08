# Importa las clases necesarias de las bibliotecas de Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Instancia las extensiones. No las inicializamos con una aplicación aquí.
# Las inicializamos en el patrón de "fábrica de aplicaciones"
# para que puedan ser compartidas y configuradas por la app.
db = SQLAlchemy()
login_manager = LoginManager()
