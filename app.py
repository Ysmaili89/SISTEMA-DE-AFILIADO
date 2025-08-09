# app.py
# Importaciones de bibliotecas estándar
import os
import click
from datetime import datetime, timezone, date

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
    SocialMediaLink, User, Categoria, Subcategoria,
    Producto, Articulo, Testimonial, Afiliado, AdsenseConfig,
    EstadisticaAfiliado
)
from utils import slugify

# Para formato de moneda
from babel.numbers import format_currency as babel_format_currency

# -------------------- CARGAR VARIABLES DE ENTORNO --------------------
# Esto es para desarrollo local. En Render, las variables de entorno se establecen directamente.
load_dotenv()

# -------------------- CONFIGURACIÓN DE FLASK-BABEL --------------------
def get_application_locale():
    # Esta función determina el 'locale' para Flask-Babel
    return 'es'

# -------------------- INYECTAR DATOS GLOBALES --------------------
def inject_social_media_links():
    # Inyecta enlaces de redes sociales en el contexto de Jinja2
    links = SocialMediaLink.query.filter_by(is_visible=True).order_by(SocialMediaLink.order_num).all()
    return dict(social_media_links=links)

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
    csrf = CSRFProtect(app) 

    login_manager.login_view = 'admin.admin_login'
    login_manager.login_message_category = 'info'

    # --------------------------------------------------------------------------
    # CORRECCIÓN: Se ha eliminado el bloque de código que borraba y recreaba
    # la base de datos en cada inicio. Ahora se debe usar Flask-Migrate para
    # gestionar los cambios en la base de datos.
    # --------------------------------------------------------------------------
    with app.app_context():
        db.create_all() # ADVERTENCIA: Esta línea crea tablas, pero es mejor usar migraciones.
    
    # Después de corregir esto, se debe usar Flask-Migrate para las actualizaciones del esquema.
    # Comandos:
    # 1. flask db init (solo la primera vez)
    # 2. flask db migrate -m "Mensaje de la migración"
    # 3. flask db upgrade

    # ----------- BLUEPRINTS -----------
    from routes.admin import bp as admin_bp
    from routes.public import bp as public_bp
    from routes.api import bp as api_bp
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp)

    # ----------- INYECCIÓN DE CONTEXTO GLOBAL -----------
    app.context_processor(inject_social_media_links)

    @app.context_processor
    def inject_adsense_config():
        try:
            config = AdsenseConfig.query.first()
            if config:
                return dict(
                    adsense_client_id=config.adsense_client_id,
                    adsense_slot_1=config.adsense_slot_1,
                    adsense_slot_2=config.adsense_slot_2,
                    adsense_slot_3=config.adsense_slot_3,
                )
        except Exception:
            pass
        return dict(
            adsense_client_id='',
            adsense_slot_1='',
            adsense_slot_2='',
            adsense_slot_3=''
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

            if not Afiliado.query.filter_by(email='afiliado@example.com').first():
                db.session.add(Afiliado(
                    nombre='Afiliado de Prueba',
                    email='afiliado@example.com',
                    enlace_referido='http://localhost:5000/ref/1',
                    activo=True
                ))

            if not AdsenseConfig.query.first():
                db.session.add(AdsenseConfig(
                    adsense_client_id='ca-pub-1234567890123456',
                    adsense_slot_1='1111111111',
                    adsense_slot_2='2222222222',
                    adsense_slot_3='3333333333'
                ))

            categorias = {
                'Tecnología': ['Smartphones', 'Laptops'],
                'Hogar': ['Cocina', 'Jardín'],
                'Deportes': ['Fitness']
            }
            subcategorias_db = {}
            for cat_nombre, sub_nombres in categorias.items():
                categoria = Categoria(nombre=cat_nombre, slug=slugify(cat_nombre))
                db.session.add(categoria)
                db.session.flush()
                for sub_nombre in sub_nombres:
                    subcategoria = Subcategoria(nombre=sub_nombre, slug=slugify(sub_nombre), categoria=categoria)
                    db.session.add(subcategoria)
                    subcategorias_db[sub_nombre] = subcategoria

            # Genera 50 productos de ejemplo
            subcategorias_list = list(subcategorias_db.values())
            for i in range(1, 51):
                nombre = f"Producto Ejemplo {i}"
                precio = 10.0 + (i * 5)
                desc = f"Descripción detallada del Producto {i}. Este es un producto fantástico con muchas características."
                
                # Asigna productos a las subcategorías de manera cíclica
                subcat = subcategorias_list[i % len(subcategorias_list)]
                
                db.session.add(Producto(
                    nombre=nombre,
                    slug=slugify(nombre),
                    precio=precio,
                    descripcion=desc,
                    imagen=f'https://placehold.co/400x300/e0e0e0/555555?text={slugify(nombre)}',
                    link=f'https://ejemplo.com/{slugify(nombre)}',
                    subcategoria_id=subcat.id
                ))

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

            redes = [
                ('Facebook', 'https://facebook.com', 'fab fa-facebook-f'),
                ('X', 'https://x.com', 'fab fa-x-twitter'),
                ('Instagram', 'https://instagram.com', 'fab fa-instagram'),
                ('YouTube', 'https://youtube.com', 'fab fa-youtube'),
                ('LinkedIn', 'https://linkedin.com', 'fab fa-linkedin-in'),
            ]
            for nombre, url, icono in redes:
                db.session.add(SocialMediaLink(platform=nombre, url=url, icon_class=icono, is_visible=True))

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

    app.cli.add_command(seed_initial_data)

    # ----------- ADMINISTRADOR DE INICIO DE SESIÓN -----------
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # -------------------- RUTA DE INICIO PÚBLICA --------------------
    # CORRECCIÓN: Se actualiza la ruta de inicio para limitar a 12 productos
    @public_bp.route('/')
    @public_bp.route('/index')
    def index():
        productos = Producto.query.order_by(Producto.id.desc()).limit(12).all()
        testimonios = Testimonial.query.filter_by(is_visible=True).order_by(Testimonial.id.desc()).all()
        return render_template('public/index.html', productos=productos, testimonios=testimonios)
    # ----------- FIN DE LA FÁBRICA DE APLICACIONES -----------
    return app

# -------------------- ESTABLECER CONTRASEÑA DE ADMINISTRADOR --------------------
def set_admin_password(app, new_password):
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            admin_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            print("Contraseña actualizada para 'admin'.")
        else:
            print("Usuario 'admin' no encontrado.")

# -------------------- EJECUCIÓN PRINCIPAL (SOLO PARA DESARROLLO LOCAL) --------------------
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        pass
    app.run(debug=True)