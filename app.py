# app.py

# Importaciones de bibliotecas estÃ¡ndar
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

# -------------------- CONFIGURACIÃN DE FLASK-BABEL --------------------
def get_application_locale():
    # Esta funciÃ³n determina el 'locale' para Flask-Babel
    return 'es'

# -------------------- INYECTAR DATOS GLOBALES --------------------
def inject_social_media_links():
    # Inyecta enlaces de redes sociales en el contexto de Jinja2
    links = SocialMediaLink.query.filter_by(is_visible=True).order_by(SocialMediaLink.order_num).all()
    return dict(social_media_links=links)

# -------------------- FÃBRICA DE APLICACIONES PRINCIPALES --------------------
def create_app():
    app = Flask(__name__)

    # ----------- CONFIGURACIONES BÃSICAS -----------
    # SECRET_KEY es esencial para la seguridad de la sesiÃ³n. Usa una variable de entorno en producciÃ³n.
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_very_secret_key_for_dev_only')
    # DATABASE_URL debe establecerse como una variable de entorno en Render.
    # 'sqlite:///site.db' es un respaldo para el desarrollo local si DATABASE_URL no estÃ¡ configurada.
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BABEL_DEFAULT_LOCALE'] = 'es'

    # ----------- EXTENSIONES -----------
    # Inicializa las extensiones de Flask con la aplicaciÃ³n
    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)
    Babel(app, locale_selector=get_application_locale)
    Moment(app)
    csrf = CSRFProtect(app) # noqa: F841 # Inicializa la protecciÃ³n CSRF

    # Configura Flask-Login
    login_manager.login_view = 'admin.admin_login'
    login_manager.login_message_category = 'info'

    # ----------- INICIALIZACIÃN DE LA BASE DE DATOS Y DATOS INICIALES -----------
    # Este bloque asegura que los datos iniciales se creen si no existen.
    # Se ejecuta en el contexto de la aplicaciÃ³n, lo que es crucial para el despliegue con Gunicorn.
    with app.app_context():
        # IMPORTANTE: No uses db.create_all() si usas migraciones.
        # En su lugar, usa `flask db upgrade` en la consola.
        # Este bloque solo crearÃ¡ los datos si la tabla de usuarios estÃ¡ vacÃ­a.
        if not User.query.first():
            print("âï¸ Creando datos iniciales...")

            # Usuario admin
            admin_user = User(username='admin', password_hash=generate_password_hash('adminpass'), is_admin=True)
            db.session.add(admin_user)

            # Afiliado de demostraciÃ³n
            if not Afiliado.query.filter_by(email='afiliado@example.com').first():
                db.session.add(Afiliado(
                    nombre='Afiliado de Prueba',
                    email='afiliado@example.com',
                    enlace_referido='http://localhost:5000/ref/1', # Este enlace podrÃ­a necesitar ser dinÃ¡mico para producciÃ³n
                    activo=True
                ))

            # ConfiguraciÃ³n inicial de Adsense
            if not AdsenseConfig.query.first():
                db.session.add(AdsenseConfig(
                    adsense_client_id='ca-pub-1234567890123456', # ID de marcador de posiciÃ³n
                    adsense_slot_1='1111111111',
                    adsense_slot_2='2222222222',
                    adsense_slot_3='3333333333'
                ))

            # CategorÃ­as y subcategorÃ­as
            categorias = {
                'TecnologÃ­a': ['Smartphones', 'Laptops'],
                'Hogar': ['Cocina', 'JardÃ­n'],
                'Deportes': ['Fitness']
            }
            for cat, subs in categorias.items():
                categoria = Categoria(nombre=cat, slug=slugify(cat))
                db.session.add(categoria)
                db.session.flush() # Flush para obtener el ID de las subcategorÃ­as antes de agregarlas
                for sub in subs:
                    db.session.add(Subcategoria(nombre=sub, slug=slugify(sub), categoria=categoria))

            # Productos
            productos = [
                ('Smartphone Pro X', 899.99, 'Smartphone con cÃ¡mara de alta resoluciÃ³n y baterÃ­a duradera.', 'Smartphones'),
                ('Laptop UltraBook', 1200.00, 'Laptop ligera y potente.', 'Laptops'),
                ('Batidora Multifuncional', 75.50, 'Batidora de cocina versÃ¡til.', 'Cocina'),
                ('Mancuernas Ajustables', 150.00, 'Set de mancuernas para entrenar en casa.', 'Fitness'),
            ]
            for nombre, precio, desc, subcat_nombre in productos:
                subcat = Subcategoria.query.filter_by(nombre=subcat_nombre).first()
                if subcat: # Asegurarse de que la subcategorÃ­a exista antes de agregar el producto
                    db.session.add(Producto(
                        nombre=nombre,
                        slug=slugify(nombre),
                        precio=precio,
                        descripcion=desc,
                        imagen=f'https://placehold.co/400x300/e0e0e0/555555?text={slugify(nombre)}',
                        link=f'https://ejemplo.com/{slugify(nombre)}',
                        subcategoria_id=subcat.id
                    ))

            # ArtÃ­culos
            articulos = [
                ('GuÃ­a para elegir tu primer smartphone', 'Contenido guÃ­a smartphone...', 'Equipo Afiliados Online', 'Smartphone'),
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
                author="Juan PÃ©rez",
                content="Â¡Excelente sitio! EncontrÃ© el producto perfecto.",
                date_posted=datetime.now(timezone.utc),
                is_visible=True,
                likes=5,
                dislikes=0
            ))

            db.session.commit()
            print("â Datos iniciales creados.")
        else:
            print("â¹ï¸ Los usuarios ya existen. Saltando datos iniciales.")
    # ----------- FIN DE LA INICIALIZACIÃN DE LA BASE DE DATOS -----------

    # ----------- ADMINISTRADOR DE INICIO DE SESIÃN -----------
    @login_manager.user_loader
    def load_user(user_id):
        # Callback para recargar el objeto de usuario desde el ID de usuario almacenado en la sesiÃ³n
        return db.session.get(User, int(user_id))

    # ----------- BLUEPRINTS -----------
    # Importa y registra los blueprints para diferentes partes de la aplicaciÃ³n
    from routes.admin import bp as admin_bp
    from routes.public import bp as public_bp
    from routes.api import bp as api_bp
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp)

    # ----------- INYECCIÃN DE CONTEXTO GLOBAL -----------
    # Estas funciones inyectan variables en el contexto de la plantilla Jinja2 para todas las solicitudes
    app.context_processor(inject_social_media_links)

    @app.context_processor
    def inject_adsense_config():
        # Inyecta la configuraciÃ³n de Adsense en el contexto de Jinja2
        config = AdsenseConfig.query.first()
        if config:
            return dict(
                adsense_client_id=config.adsense_client_id,
                adsense_slot_1=config.adsense_slot_1,
                adsense_slot_2=config.adsense_slot_2,
                adsense_slot_3=config.adsense_slot_3,
            )
        return dict( # Devuelve cadenas vacÃ­as si no se encuentra la configuraciÃ³n
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
        # Formatea un valor numÃ©rico como moneda
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

    return app # Devuelve la instancia de la aplicaciÃ³n Flask

# -------------------- ESTABLECER CONTRASEÃA DE ADMINISTRADOR --------------------
# Esta funciÃ³n se usa normalmente para CLI o tareas administrativas Ãºnicas, no como parte del inicio normal de la aplicaciÃ³n
def set_admin_password(app, new_password):
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            admin_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            print("ð ContraseÃ±a actualizada para 'admin'.")
        else:
            print("â ï¸ Usuario 'admin' no encontrado.")

# -------------------- EJECUCIÃN PRINCIPAL (SOLO PARA DESARROLLO LOCAL) --------------------
# Este bloque solo se ejecuta cuando se ejecuta app.py directamente (por ejemplo, 'python app.py')
# Gunicorn NO ejecuta este bloque.
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Â¡IMPORTANTE! No llames a db.create_all() si usas Flask-Migrate.
        # En su lugar, usa `flask db upgrade` en la consola.
        pass
    app.run(debug=True)