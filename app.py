# app.py
# Importaciones de bibliotecas estándar
import os
from datetime import datetime, timezone

# Importaciones de terceros
from flask import Flask, render_template
from flask_babel import Babel
from flask_migrate import Migrate
from flask_moment import Moment
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
import markdown

# Importaciones de aplicaciones locales
from extensions import db, login_manager
from models import (
    SocialMediaLink, User, Category, Subcategory,
    Product, Article, Testimonial, Affiliate, AdsenseConfig
)
from utils import slugify

# Para formato de moneda
from babel.numbers import format_currency as babel_format_currency

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
    # CORRECCIÓN F841: La variable 'csrf' ya no es necesaria. La extensión se inicializa al pasar 'app'.
    CSRFProtect(app)

    login_manager.login_view = 'admin.admin_login'
    login_manager.login_message_category = 'info'

    with app.app_context():
        # ADVERTENCIA: Se comenta db.create_all() para evitar conflictos con Flask-Migrate.
        # db.create_all()
        pass

    # ----------- BLUEPRINTS -----------
    from routes.admin import bp as admin_bp
    from routes.public import bp as public_bp
    from routes.api import bp as api_bp
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp)

    # ----------- INYECCIÓN DE CONTEXTO GLOBAL -----------
    # CORRECCIÓN F821: Las funciones se inyectan en el contexto, no se llaman directamente.
    @app.context_processor
    def inject_social_media_links():
        # Inyecta enlaces de redes sociales en el contexto de Jinja2
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

    # ----------- COMANDOS DE CLI PERSONALIZADOS -----------
    @app.cli.command('seed-db')
    def seed_initial_data():
        """Crea datos iniciales para la aplicación si no existen."""
        with app.app_context():
            print("⚙️ Creando datos iniciales...")
            
            if User.query.first():
                print("ℹ️ Los usuarios ya existen. Saltando la creación de datos iniciales.")
                return

            admin_user = User(username='admin', password_hash=generate_password_hash('adminpass'), is_admin=True)
            db.session.add(admin_user)

            if not Affiliate.query.filter_by(email='afiliado@example.com').first():
                db.session.add(Affiliate(
                    name='Afiliado de Prueba',
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

            categorias = {
                'Tecnología': ['Smartphones', 'Laptops'],
                'Hogar': ['Cocina', 'Jardín'],
                'Deportes': ['Fitness']
            }
            subcategorias_db = {}
            for cat_nombre, sub_nombres in categorias.items():
                categoria = Category(name=cat_nombre, slug=slugify(cat_nombre))
                db.session.add(categoria)
                db.session.flush()
                for sub_nombre in sub_nombres:
                    subcategoria = Subcategory(name=sub_nombre, slug=slugify(sub_nombre), category=categoria)
                    db.session.add(subcategoria)
                    subcategorias_db[sub_nombre] = subcategoria

            subcategorias_list = list(subcategorias_db.values())
            for i in range(1, 51):
                nombre = f"Producto Ejemplo {i}"
                precio = 10.0 + (i * 5)
                desc = f"Descripción detallada del Producto {i}. Este es un producto fantástico con muchas características."
                
                subcat = subcategorias_list[i % len(subcategorias_list)]
                
                db.session.add(Product(
                    name=nombre,
                    slug=slugify(nombre),
                    price=precio,
                    description=desc,
                    image=f'https://placehold.co/400x300/e0e0e0/555555?text={slugify(nombre)}',
                    link=f'https://ejemplo.com/{slugify(nombre)}',
                    subcategory_id=subcat.id
                ))

            articulos = [
                ('Guía para elegir tu primer smartphone', 'Contenido guía smartphone...', 'Equipo Afiliados Online', 'Smartphone'),
                ('Recetas con tu nueva batidora', 'Contenido recetas batidora...', 'Chef Invitado', 'Batidora'),
            ]
            for title, content, author, image_text in articulos:
                db.session.add(Article(
                    title=title,
                    slug=slugify(title),
                    content=f'<p>{content}</p>',
                    author=author,
                    date=datetime.now(timezone.utc),
                    image=f'https://placehold.co/800x400/e0e0e0/555555?text={image_text}'
                ))

            redes = [
                ('Facebook', 'https://facebook.com', 'fab fa-facebook-f', 1),
                ('X', 'https://x.com', 'fab fa-x-twitter', 2),
                ('Instagram', 'https://instagram.com', 'fab fa-instagram', 3),
                ('YouTube', 'https://youtube.com', 'fab fa-youtube', 4),
                ('LinkedIn', 'https://linkedin.com', 'fab fa-linkedin-in', 5),
            ]
            for name, url, icon, order in redes:
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
    
    # -------------------- RUTA DE INICIO PÚBLICA --------------------
    # CORRECCIÓN: Se actualiza la ruta de inicio para limitar a 12 productos
    @public_bp.route('/')
    @public_bp.route('/index')
    def index():
        productos = Product.query.order_by(Product.id.desc()).limit(12).all()
        testimonios = Testimonial.query.filter_by(is_visible=True).order_by(Testimonial.id.desc()).all()
        return render_template('public/index.html', productos=productos, testimonios=testimonios)

    # ----------- FIN DE LA FÁBRICA DE APLICACIONES -----------
    return app

# -------------------- EJECUCIÓN PRINCIPAL (SOLO PARA DESARROLLO LOCAL) --------------------
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)