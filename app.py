# app.py

# Importaciones de bibliotecas estándar
import os
from datetime import datetime, timezone, date

# Importaciones de terceros
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
    Producto, Articulo, Testimonial, Afiliado, AdsenseConfig,
    EstadisticaAfiliado
)
# Asumiendo que utils.py existe y contiene slugify
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
    # SECRET_KEY es esencial para la seguridad de la sesión. Usa una variable de entorno en producción.
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_very_secret_key_for_dev_only')
    # DATABASE_URL debe establecerse como una variable de entorno en Render.
    # 'sqlite:///site.db' es un respaldo para el desarrollo local si DATABASE_URL no está configurada.
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BABEL_DEFAULT_LOCALE'] = 'es'

    # ----------- EXTENSIONES -----------
    # Inicializa las extensiones de Flask con la aplicación
    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)
    Babel(app, locale_selector=get_application_locale)
    Moment(app)
    csrf = CSRFProtect(app) # noqa: F841 # Inicializa la protección CSRF

    # Configura Flask-Login
    login_manager.login_view = 'admin.admin_login'
    login_manager.login_message_category = 'info'

    # ----------- INICIALIZACIÓN DE LA BASE DE DATOS Y DATOS INICIALES -----------
    # Este bloque asegura que los datos iniciales se creen si no existen.
    # Se ejecuta en el contexto de la aplicación, lo que es crucial para el despliegue con Gunicorn.
    with app.app_context():
        # IMPORTANTE: No uses db.create_all() si usas migraciones.
        # En su lugar, usa `flask db upgrade` en la consola.
        # Este bloque solo creará los datos si la tabla de usuarios está vacía.
        if not User.query.first():
            print("⚙️ Creando datos iniciales...")

            # Usuario admin
            admin_user = User(username='admin', password_hash=generate_password_hash('adminpass'), is_admin=True)
            db.session.add(admin_user)

            # Afiliado de demostración
            if not Afiliado.query.filter_by(email='afiliado@example.com').first():
                db.session.add(Afiliado(
                    nombre='Afiliado de Prueba',
                    email='afiliado@example.com',
                    enlace_referido='http://localhost:5000/ref/1', # Este enlace podría necesitar ser dinámico para producción
                    activo=True
                ))

            # Configuración inicial de Adsense
            if not AdsenseConfig.query.first():
                db.session.add(AdsenseConfig(
                    adsense_client_id='ca-pub-1234567890123456', # ID de marcador de posición
                    adsense_slot_1='1111111111',
                    adsense_slot_2='2222222222',
                    adsense_slot_3='3333333333'
                ))

            # Categorías y subcategorías
            categorias = {
                'Tecnología': ['Smartphones', 'Laptops'],
                'Hogar': ['Cocina', 'Jardín'],
                'Deportes': ['Fitness']
            }
            for cat, subs in categorias.items():
                categoria = Categoria(nombre=cat, slug=slugify(cat))
                db.session.add(categoria)
                db.session.flush() # Flush para obtener el ID de las subcategorías antes de agregarlas
                for sub in subs:
                    db.session.add(Subcategoria(nombre=sub, slug=slugify(sub), categoria=categoria))

            # Productos
            productos = [
                ('Smartphone Pro X', 899.99, 'Smartphone con cámara de alta resolución y batería duradera.', 'Smartphones'),
                ('Laptop UltraBook', 1200.00, 'Laptop ligera y potente.', 'Laptops'),
                ('Batidora Multifuncional', 75.50, 'Batidora de cocina versátil.', 'Cocina'),
                ('Mancuernas Ajustables', 150.00, 'Set de mancuernas para entrenar en casa.', 'Fitness'),
            ]
            for nombre, precio, desc, subcat_nombre in productos:
                subcat = Subcategoria.query.filter_by(nombre=subcat_nombre).first()
                if subcat: # Asegurarse de que la subcategoría exista antes de agregar el producto
                    db.session.add(Producto(
                        nombre=nombre,
                        slug=slugify(nombre),
                        precio=precio,
                        descripcion=desc,
                        imagen=f'https://placehold.co/400x300/e0e0e0/555555?text={slugify(nombre)}',
                        link=f'https://ejemplo.com/{slugify(nombre)}',
                        subcategoria_id=subcat.id
                    ))

            # Artículos
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

            # Enlaces a redes sociales
            redes = [
                ('Facebook', 'https://facebook.com', 'fab fa-facebook-f'),
                ('X', 'https://x.com', 'fab fa-x-twitter'),
                ('Instagram', 'https://instagram.com', 'fab fa-instagram'),
                ('YouTube', 'https://youtube.com', 'fab fa-youtube'),
                ('LinkedIn', 'https://linkedin.com', 'fab fa-linkedin-in'),
            ]
            for nombre, url, icono in redes:
                db.session.add(SocialMediaLink(platform=nombre, url=url, icon_class=icono, is_visible=True))

            # Testimonio
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
    # ----------- FIN DE LA INICIALIZACIÓN DE LA BASE DE DATOS -----------

    # ----------- ADMINISTRADOR DE INICIO DE SESIÓN -----------
    @login_manager.user_loader
    def load_user(user_id):
        # Callback para recargar el objeto de usuario desde el ID de usuario almacenado en la sesión
        return db.session.get(User, int(user_id))

    # ----------- BLUEPRINTS -----------
    # Importa y registra los blueprints para diferentes partes de la aplicación
    from routes.admin import bp as admin_bp
    from routes.public import bp as public_bp
    from routes.api import bp as api_bp
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp)

    # ----------- INYECCIÓN DE CONTEXTO GLOBAL -----------
    # Estas funciones inyectan variables en el contexto de la plantilla Jinja2 para todas las solicitudes
    app.context_processor(inject_social_media_links)

    @app.context_processor
    def inject_adsense_config():
        # Inyecta la configuración de Adsense en el contexto de Jinja2
        config = AdsenseConfig.query.first()
        if config:
            return dict(
                adsense_client_id=config.adsense_client_id,
                adsense_slot_1=config.adsense_slot_1,
                adsense_slot_2=config.adsense_slot_2,
                adsense_slot_3=config.adsense_slot_3,
            )
        return dict( # Devuelve cadenas vacías si no se encuentra la configuración
            adsense_client_id='',
            adsense_slot_1='',
            adsense_slot_2='',
            adsense_slot_3=''
        )

    @app.context_processor
    def inject_now():
        # Inyecta la fecha y hora UTC actual en el contexto de Jinja2
        return {'now': datetime.now(timezone.utc)}

    # ----------- FILTROS JINJA2 PERSONALIZADOS -----------
    # Filtros personalizados para usar en las plantillas de Jinja2
    @app.template_filter('markdown')
    def markdown_filter(text):
        # Convierte el texto de Markdown a HTML
        return markdown.markdown(text)

    @app.template_filter('format_currency')
    def format_currency_filter(value, currency='USD', locale='es_MX'):
        # Formatea un valor numérico como moneda
        try:
            return babel_format_currency(value, currency, locale=locale)
        except Exception:
            return value

    @app.template_filter('datetime')
    def format_datetime_filter(value, format="%Y-%m-%d %H:%M:%S"):
        # Formatea un objeto datetime a una cadena de texto
        if isinstance(value, datetime):
            return value.strftime(format)
        return value

    return app # Devuelve la instancia de la aplicación Flask

# -------------------- ESTABLECER CONTRASEÑA DE ADMINISTRADOR --------------------
# Esta función se usa normalmente para CLI o tareas administrativas únicas, no como parte del inicio normal de la aplicación
def set_admin_password(app, new_password):
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            admin_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            print("🔐 Contraseña actualizada para 'admin'.")
        else:
            print("⚠️ Usuario 'admin' no encontrado.")

# -------------------- EJECUCIÓN PRINCIPAL (SOLO PARA DESARROLLO LOCAL) --------------------
# Este bloque solo se ejecuta cuando se ejecuta app.py directamente (por ejemplo, 'python app.py')
# Gunicorn NO ejecuta este bloque.
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # ¡IMPORTANTE! No llames a db.create_all() si usas Flask-Migrate.
        # En su lugar, usa `flask db upgrade` en la consola.
        pass
    app.run(debug=True)