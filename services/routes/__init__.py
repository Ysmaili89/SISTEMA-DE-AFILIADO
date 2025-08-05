from flask import Flask
from config import Config

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    @app.route("/")
    def home():
        return "Hola desde Flask en Render"

    return app
