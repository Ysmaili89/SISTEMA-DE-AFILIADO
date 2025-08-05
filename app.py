# C:\Users\joran\OneDrive\data\Documentos\LMSGI\afiliados_app\app.py

# Standard library imports
import os
from datetime import datetime, timezone

# Third-party imports
from flask import Flask
from flask_babel import Babel
from flask_migrate import Migrate
from flask_moment import Moment
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
import markdown # Import markdown for the template filter

# Importaciones de aplicaciones locales
from extensions import db, login_manager
from models import (
    SocialMediaLink, User, Categoria, Subcategoria,
    Producto, Articulo, Testimonial, Afiliado, AdsenseConfig
)
from utils import slugify # Assuming utils.py exists and contains slugify

# For currency formatting
from babel.numbers import format_currency as babel_format_currency

# -------------------- CARGAR VARIABLES DE ENTORNO --------------------
# This is usually for local development. On Render, you set environment variables directly.
load_dotenv()

# -------------------- CONFIGURACIÓN DE FLASK-BABEL --------------------
def get_application_locale():
    # This function determines the locale for Flask-Babel
    return 'es'

# -------------------- INYECTAR DATOS GLOBALES --------------------
def inject_social_media_links():
    # Injects social media links into the Jinja2 context
    links = SocialMediaLink.query.filter_by(is_visible=True).order_by(SocialMediaLink.order_num).all()
    return dict(social_media_links=links)

# -------------------- FÁBRICA DE APLICACIONES PRINCIPALES --------------------
def create_app():
    app = Flask(__name__)

    # ----------- CONFIGURACIONES BÁSICAS -----------
    # SECRET_KEY is essential for session security. Use an environment variable in production.
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_very_secret_key_for_dev_only')
    # DATABASE_URL must be set as an environment variable on Render.
    # 'sqlite:///site.db' is a fallback for local development if DATABASE_URL is not set.
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BABEL_DEFAULT_LOCALE'] = 'es'

    # ----------- EXTENSIONES -----------
    # Initialize Flask extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)
    Babel(app, locale_selector=get_application_locale)
    Moment(app)
    csrf = CSRFProtect(app) # noqa: F841 # Initialize CSRF protection

    # Configure Flask-Login
    login_manager.login_view = 'admin.admin_login'
    login_manager.login_message_category = 'info'

    # ----------- DATABASE INITIALIZATION AND INITIAL DATA (MOVED HERE) -----------
    # This block ensures the database tables are created and initial data is populated
    # when the app starts, which is crucial for deployment with Gunicorn.
    # It runs within the application context.
    with app.app_context():
        # Create all database tables if they don't exist
        db.create_all()

        # Check if the User table is empty to avoid re-creating data on every restart
        if not User.query.first():
            print("🔧 Creando datos iniciales...")

            # Admin user
            admin_user = User(username='admin', password_hash=generate_password_hash('adminpass'), is_admin=True)
            db.session.add(admin_user)

            # Demo affiliate
            if not Afiliado.query.filter_by(email='afiliado@example.com').first():
                db.session.add(Afiliado(
                    nombre='Afiliado de Prueba',
                    email='afiliado@example.com',
                    enlace_referido='http://localhost:5000/ref/1', # This link might need to be dynamic for production
                    activo=True
                ))

            # Initial AdsenseConfig
            if not AdsenseConfig.query.first():
                db.session.add(AdsenseConfig(
                    adsense_client_id='ca-pub-1234567890123456', # Placeholder ID
                    adsense_slot_1='1111111111',
                    adsense_slot_2='2222222222',
                    adsense_slot_3='3333333333'
                ))

            # Categories and Subcategories
            categorias = {
                'Tecnología': ['Smartphones', 'Laptops'],
                'Hogar': ['Cocina', 'Jardín'],
                'Deportes': ['Fitness']
            }
            for cat, subs in categorias.items():
                categoria = Categoria(nombre=cat, slug=slugify(cat))
                db.session.add(categoria)
                db.session.flush() # Flush to get ID for subcategories before adding subcategories
                for sub in subs:
                    db.session.add(Subcategoria(nombre=sub, slug=slugify(sub), categoria=categoria))

            # Products
            productos = [
                ('Smartphone Pro X', 899.99, 'Smartphone con cámara de alta resolución y batería duradera.', 'Smartphones'),
                ('Laptop UltraBook', 1200.00, 'Laptop ligera y potente.', 'Laptops'),
                ('Batidora Multifuncional', 75.50, 'Batidora de cocina versátil.', 'Cocina'),
                ('Mancuernas Ajustables', 150.00, 'Set de mancuernas para entrenar en casa.', 'Fitness'),
            ]
            for nombre, precio, desc, subcat_nombre in productos:
                subcat = Subcategoria.query.filter_by(nombre=subcat_nombre).first()
                if subcat: # Ensure subcategory exists before adding product
                    db.session.add(Producto(
                        nombre=nombre,
                        slug=slugify(nombre),
                        precio=precio,
                        descripcion=desc,
                        imagen=f'https://placehold.co/400x300/e0e0e0/555555?text={slugify(nombre)}',
                        link=f'https://ejemplo.com/{slugify(nombre)}',
                        subcategoria_id=subcat.id
                    ))

            # Articles
            articulos = [
                ('Guía para elegir tu primer smartphone', 'Contenido guía smartphone...', 'Equipo Afiliados Online', 'Smartphone'),
                ('Recetas con tu nueva batidora', 'Contenido recetas batidora...', 'Chef Invitado', 'Batidora'),
            ]
            for titulo, contenido, autor, imagen_texto in articulos:
                db.session.add(Articulo(
                    titulo=titulo,
                    slug=slugify(titulo),
                    contenido=f'<p>{contenido}</p>',
                    autor=autor,
                    fecha=datetime.now(timezone.utc),
                    imagen=f'https://placehold.co/800x400/e0e0e0/555555?text={imagen_texto}'
                ))

            # Social media links
            redes = [
                ('Facebook', 'https://facebook.com', 'fab fa-facebook-f'),
                ('X', 'https://x.com', 'fab fa-x-twitter'),
                ('Instagram', 'https://instagram.com', 'fab fa-instagram'),
                ('YouTube', 'https://youtube.com', 'fab fa-youtube'),
                ('LinkedIn', 'https://linkedin.com', 'fab fa-linkedin-in'),
            ]
            for nombre, url, icono in redes:
                db.session.add(SocialMediaLink(platform=nombre, url=url, icon_class=icono, is_visible=True))

            # Testimonial
            db.session.add(Testimonial(
                author="Juan Pérez",
                content="¡Excelente sitio! Encontré el producto perfecto.",
                date_posted=datetime.now(timezone.utc),
                is_visible=True,
                likes=5,
                dislikes=0
            ))

            db.session.commit()
            print("✅ Datos iniciales creados.")
        else:
            print("ℹ️ Los usuarios ya existen. Saltando datos iniciales.")
    # ----------- END DATABASE INITIALIZATION -----------

    # ----------- ADMINISTRADOR DE INICIO DE SESIÓN -----------
    @login_manager.user_loader
    def load_user(user_id):
        # Callback to reload the user object from the user ID stored in the session
        return db.session.get(User, int(user_id))

    # ----------- BLUEPRINTS -----------
    # Import and register blueprints for different parts of the application
    from routes.admin import bp as admin_bp
    from routes.public import bp as public_bp
    from routes.api import bp as api_bp
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp)

    # ----------- GLOBAL CONTEXT INJECTION -----------
    # These functions inject variables into the Jinja2 template context for all requests
    app.context_processor(inject_social_media_links)

    @app.context_processor
    def inject_adsense_config():
        # Injects Adsense configuration into the Jinja2 context
        config = AdsenseConfig.query.first()
        if config:
            return dict(
                adsense_client_id=config.adsense_client_id,
                adsense_slot_1=config.adsense_slot_1,
                adsense_slot_2=config.adsense_slot_2,
                adsense_slot_3=config.adsense_slot_3,
            )
        return dict( # Return empty strings if no config found
            adsense_client_id='',
            adsense_slot_1='',
            adsense_slot_2='',
            adsense_slot_3=''
        )

    @app.context_processor
    def inject_now():
        # Injects the current UTC datetime into the Jinja2 context
        return {'now': datetime.now(timezone.utc)}

    # ----------- CUSTOM JINJA2 FILTERS -----------
    # Custom filters for use in Jinja2 templates
    @app.template_filter('markdown')
    def markdown_filter(text):
        # Renders Markdown text to HTML
        return markdown.markdown(text)

    @app.template_filter('format_currency')
    def format_currency_filter(value, currency='USD', locale='es_MX'):
        # Formats a numeric value as currency
        try:
            return babel_format_currency(value, currency, locale=locale)
        except Exception:
            return value

    @app.template_filter('datetime')
    def format_datetime_filter(value, format="%Y-%m-%d %H:%M:%S"):
        # Formats a datetime object to a string
        if isinstance(value, datetime):
            return value.strftime(format)
        return value

    return app # Return the Flask application instance

# -------------------- ESTABLECER CONTRASEÑA DE ADMINISTRADOR --------------------
# This function is typically used for CLI or one-off admin tasks, not part of regular app startup
def set_admin_password(app, new_password):
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            admin_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            print("🔐 Contraseña actualizada para 'admin'.")
        else:
            print("⚠️ Usuario 'admin' no encontrado.")

# -------------------- EJECUCIÓN PRINCIPAL (FOR LOCAL DEVELOPMENT ONLY) --------------------
# This block only runs when you execute app.py directly (e.g., `python app.py`)
# Gunicorn does NOT execute this block.
if __name__ == "__main__":
    app = create_app()
    # create_initial_data(app) # This call is now redundant here as it's inside create_app()
    app.run(debug=True)