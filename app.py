# Importaciones de bibliotecas estándar
import os
from datetime import datetime, timezone

# Importaciones de terceros
from flask import Flask
from flask_babel import Babel
from flask_migrate import Migrate
from flask_moment import Moment
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
import markdown
from babel.numbers import format_currency as babel_format_currency

# Importaciones de aplicaciones locales
from extensions import db, login_manager
from models import (
    SocialMediaLink, User, Category, Subcategory,
    Product, Article, Testimonial, Affiliate, AdsenseConfig
)
from utils import slugify

# -------------------- CARGAR VARIABLES DE ENTORNO --------------------
load_dotenv()

# -------------------- CONFIGURACIÓN DE FLASK-BABEL --------------------
def get_application_locale():
    # Esta función determina el 'locale' para Flask-Babel
    return 'es'

# -------------------- FÁBRICA DE APLICACIONES PRINCIPALES --------------------
def create_app():
    app = Flask(__name__)

    # ----------- CONFIGURACIONES BÁSICAS -----------
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_very_secret_key_for_dev_only')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BABEL_DEFAULT_LOCALE'] = 'es'

    # ----------- EXTENSIONES -----------
    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)
    Babel(app, locale_selector=get_application_locale)
    Moment(app)
    CSRFProtect(app)

    login_manager.login_view = 'admin.admin_login'
    login_manager.login_message_category = 'info'

    with app.app_context():
        # ADVERTENCIA: db.create_all() está comentado para evitar conflictos con Flask-Migrate.
        # db.create_all()
        pass

    # ----------- BLUEPRINTS -----------
    # Importar los blueprints DENTRO de la función, después de inicializar la app
    # Esto es CRUCIAL para evitar errores de importación circular
    from routes.admin import bp as admin_bp
    from routes.public import bp as public_bp
    from routes.api import bp as api_bp
    
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # ----------- INYECCIÓN DE CONTEXTO GLOBAL -----------
    @app.context_processor
    def inject_social_media_links():
        links = SocialMediaLink.query.filter_by(is_visible=True).order_by(SocialMediaLink.order_num).all()
        return dict(social_media_links=links)

    @app.context_processor
    def inject_adsense_config():
        try:
            config = AdsenseConfig.query.first()
            if config and config.is_active:
                return dict(
                    adsense_client_id=config.adsense_client_id,
                    adsense_slot_header=config.ad_slot_header,
                    adsense_slot_sidebar=config.ad_slot_sidebar,
                    adsense_slot_article_top=config.ad_slot_article_top,
                    adsense_slot_article_bottom=config.ad_slot_article_bottom
                )
        except Exception:
            pass
        return dict(
            adsense_client_id='',
            adsense_slot_header='',
            adsense_slot_sidebar='',
            adsense_slot_article_top='',
            adsense_slot_article_bottom=''
        )

    @app.context_processor
    def inject_now():
        return {'now': datetime.now(timezone.utc)}

    # ----------- FILTROS JINJA2 PERSONALIZADOS -----------
    @app.template_filter('markdown')
    def markdown_filter(text):
        return markdown.markdown(text)

    @app.template_filter('format_currency')
    def format_currency_filter(value, currency='USD', locale='es_MX'):
        try:
            return babel_format_currency(value, currency, locale=locale)
        except Exception:
            return value

    @app.template_filter('datetime')
    def format_datetime_filter(value, format="%Y-%m-%d %H:%M:%S"):
        if isinstance(value, datetime):
            return value.strftime(format)
        return value

    # ----------- COMANDOS CLI PERSONALIZADOS -----------
    @app.cli.command('seed-db')
    def seed_initial_data():
        """Crea datos iniciales para la aplicación si no existen."""
        with app.app_context():
            print("⚙️ Creando datos iniciales...")
            
            if User.query.first():
                print("ℹ️ Los usuarios ya existen. Omitiendo la creación de datos iniciales.")
                return

            admin_user = User(username='admin', password_hash=generate_password_hash('adminpass'), is_admin=True)
            db.session.add(admin_user)

            if not Affiliate.query.filter_by(email='afiliado@example.com').first():
                db.session.add(Affiliate(
                    name='Test Affiliate',
                    email='afiliado@example.com',
                    referral_link='http://localhost:5000/ref/1',
                    is_active=True
                ))

            if not AdsenseConfig.query.first():
                db.session.add(AdsenseConfig(
                    adsense_client_id='ca-pub-1234567890123456',
                    ad_slot_header='1111111111',
                    ad_slot_sidebar='2222222222',
                    ad_slot_article_top='3333333333',
                    ad_slot_article_bottom='4444444444'
                ))

            categories_data = {
                'Tecnología': ['Smartphones', 'Laptops'],
                'Hogar': ['Cocina', 'Jardín'],
                'Deportes': ['Fitness']
            }
            subcategories_db = {}
            for cat_name, sub_names in categories_data.items():
                category = Category(name=cat_name, slug=slugify(cat_name))
                db.session.add(category)
                db.session.flush()
                for sub_name in sub_names:
                    subcategory = Subcategory(name=sub_name, slug=slugify(sub_name), category=category)
                    db.session.add(subcategory)
                    db.session.flush()
                    subcategories_db[sub_name] = subcategory

            subcategories_list = list(subcategories_db.values())
            for i in range(1, 51):
                name = f"Producto Ejemplo {i}"
                price = 10.0 + (i * 5)
                description = f"Descripción detallada del Producto {i}. Este es un producto fantástico con muchas características."
                
                subcat = subcategories_list[i % len(subcategories_list)]
                
                db.session.add(Product(
                    name=name,
                    slug=slugify(name),
                    price=price,
                    description=description,
                    image=f'https://placehold.co/400x300/e0e0e0/555555?text={slugify(name)}',
                    link=f'https://ejemplo.com/{slugify(name)}',
                    subcategory_id=subcat.id
                ))

            articles_data = [
                ('Guía para elegir tu primer smartphone', 'Contenido guía smartphone...', 'Equipo Afiliados Online', 'Smartphone'),
                ('Recetas con tu nueva batidora', 'Contenido recetas batidora...', 'Chef Invitado', 'Batidora'),
            ]
            for title, content, author, image_text in articles_data:
                db.session.add(Article(
                    title=title,
                    slug=slugify(title),
                    content=f'<p>{content}</p>',
                    author=author,
                    date=datetime.now(timezone.utc),
                    image=f'https://placehold.co/800x400/e0e0e0/555555?text={image_text}'
                ))

            social_links = [
                ('Facebook', 'https://facebook.com', 'fab fa-facebook-f', 1),
                ('X', 'https://x.com', 'fab fa-x-twitter', 2),
                ('Instagram', 'https://instagram.com', 'fab fa-instagram', 3),
                ('YouTube', 'https://youtube.com', 'fab fa-youtube', 4),
                ('LinkedIn', 'https://linkedin.com', 'fab fa-linkedin-in', 5),
            ]
            for name, url, icon, order in social_links:
                db.session.add(SocialMediaLink(platform=name, url=url, icon_class=icon, is_visible=True, order_num=order))

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

    # ----------- ADMINISTRADOR DE INICIO DE SESIÓN -----------
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    return app

# -------------------- EJECUCIÓN PRINCIPAL (SOLO PARA DESARROLLO LOCAL) --------------------
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)