# config.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

# --- Main configuration class ---
class Config:
    """Base configuration class."""
    # SECRET_KEY is essential for security, taken from the environment.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_secret_key'
    
    # SQLALCHEMY_DATABASE_URI is taken from the environment.
    # The default value is for local development with PostgreSQL.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost/mydb?client_encoding=utf8'
    
    # Disabled to avoid warnings.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# --- Initialization of the application and extensions ---
# This is for local use if the file is run directly.
# In a real application with the factory pattern, this configuration
# would be done inside the create_app() function.
app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Model definition (Example) ---
# Your Affiliate model is kept, but the syntax is corrected.
class Affiliate(db.Model):
    """Model to represent an Affiliate."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Affiliate {self.name}>'

# --- Main execution ---
if __name__ == '__main__':
    # The application is run if the file is executed directly.
    # This is useful for local testing.
    app.run(debug=True)