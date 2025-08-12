# app.py
# Importaciones de bibliotecas estándar
import os
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

# Importaciones de terceros
from flask import Flask, render_template
from flask_babel import Babel
from flask_migrate import Migrate
from flask_moment import Moment
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

# -------------------- LOAD ENVIRONMENT VARIABLES --------------------
# This is for local development. On Render, environment variables are set directly.
load_dotenv()

# -------------------- FLASK-BABEL CONFIGURATION --------------------
def get_application_locale():
    # This function determines the 'locale' for Flask-Babel
    return 'es'

# -------------------- INJECT GLOBAL DATA --------------------
def inject_social_media_links():
    # Injects social media links into the Jinja2 context
    links = SocialMediaLink.query.filter_by(is_visible=True).order_by(SocialMediaLink.order_num).all()
    return dict(social_media_links=links)

# -------------------- MAIN APPLICATION FACTORY --------------------
def create_app():
    app = Flask(__name__)

    # ----------- BASIC CONFIGURATIONS -----------
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_very_secret_key_for_dev_only')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BABEL_DEFAULT_LOCALE'] = 'es'

    # ----------- EXTENSIONS -----------
    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)
    Babel(app, locale_selector=get_application_locale)
    Moment(app)
    CSRFProtect(app)

    login_manager.login_view = 'admin.admin_login'
    login_manager.login_message_category = 'info'
    
    # -------------------- STARTUP LOGIC --------------------
    # NEW: Automatically creates the 'admin' user if it doesn't exist.
    with app.app_context():
        print("--- DIAGNÓSTICO DE INICIO ---")
        print(f"URL de la base de datos: {app.config['SQLALCHEMY_DATABASE_URI']}")
        try:
            # Check if the 'admin' user exists in the database
            admin_user_exists = User.query.filter_by(username='admin').first()
            if not admin_user_exists:
                print("❌ El usuario 'admin' no se encontró. Creando...")
                # If not, create the user with a secure password hash.
                admin_user = User(
                    username='admin',
                    password_hash=generate_password_hash('admin123'),
                    is_admin=True
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Usuario administrador 'admin' creado con la contraseña 'admin123'.")
            else:
                print("✅ El usuario administrador 'admin' ya existe.")
        except Exception as e:
            print(f"⚠️ Error durante el diagnóstico de la base de datos: {e}")
            print("Asegúrate de que tu base de datos esté accesible y que las migraciones se hayan aplicado.")
        print("--- FIN DEL DIAGNÓSTICO ---")
    
    # ----------- BLUEPRINTS -----------
    from routes.admin import bp as admin_bp
    from routes.public import bp as public_bp
    from routes.api import bp as api_bp
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp)

    # ----------- GLOBAL CONTEXT INJECTION -----------
    app.context_processor(inject_social_media_links)

    @app.context_processor
    def inject_adsense_config():
        try:
            config = AdsenseConfig.query.first()
            if config:
                return dict(
                    adsense_client_id=config.adsense_client_id,
                    adsense_slot_header=config.adsense_slot_header,
                    adsense_slot_sidebar=config.adsense_slot_sidebar,
                    adsense_slot_article_top=config.adsense_slot_article_top,
                    adsense_slot_article_bottom=config.adsense_slot_article_bottom
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

    # ----------- CUSTOM JINJA2 FILTERS -----------
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

    # ----------- CUSTOM CLI COMMANDS (unchanged) -----------
    @app.cli.command('seed-db')
    @app.cli.with_appcontext
    def seed_initial_data():
        """Crea datos iniciales para la aplicación si no existe."""
        print(" ⚙️ Creación de datos iniciales...")

        if User.query.first():
            print(" ✅ Los usuarios ya existen. Omitir la creación inicial de datos.")
            return
        admin_user = User(username='admin', password_hash=generate_password_hash('adminpass'), is_admin=True)
        db.session.add(admin_user)

        if not Affiliate.query.filter_by(email='affiliate@example.com').first():
            db.session.add(Affiliate(
                name='Test Affiliate',
                email='affiliate@example.com',
                referral_link='http://localhost:5000/ref/1',
                is_active=True
            ))

        if not AdsenseConfig.query.first():
            db.session.add(AdsenseConfig(
                adsense_client_id='ca-pub-1234567890123456',
                adsense_slot_header='1111111111',
                adsense_slot_sidebar='2222222222',
                adsense_slot_article_top='3333333333',
                adsense_slot_article_bottom='4444444444'
            ))

        categories = {
            'Technology': ['Smartphones', 'Laptops'],
            'Home': ['Kitchen', 'Garden'],
            'Sports': ['Fitness']
        }
        subcategories_db = {}
        for cat_name, sub_names in categories.items():
            category = Category(name=cat_name, slug=slugify(cat_name))
            db.session.add(category)
            db.session.flush()
            for sub_name in sub_names:
                subcategory = Subcategory(name=sub_name, slug=slugify(sub_name), category=category)
                db.session.add(subcategory)
                subcategories_db[sub_name] = subcategory

        # Generate 50 sample products
        subcategories_list = list(subcategories_db.values())
        for i in range(1, 51):
            name = f"Sample Product {i}"
            price = 10.0 + (i * 5)
            desc = f"Detailed description for Product {i}. This is a fantastic product with many features."
            
            # Assign products to subcategories cyclically
            subcat = subcategories_list[i % len(subcategories_list)]
            
            db.session.add(Product(
                name=name,
                slug=slugify(name),
                price=price,
                description=desc,
                image=f'https://placehold.co/400x300/e0e0e0/555555?text={slugify(name)}',
                link=f'https://example.com/{slugify(name)}',
                subcategory_id=subcat.id
            ))

        articles = [
            ('Guide to choosing your first smartphone', 'Content for smartphone guide...', 'Affiliates Team', 'Smartphone'),
            ('Recipes with your new blender', 'Content for blender recipes...', 'Guest Chef', 'Blender'),
        ]
        for title, content, author, image_text in articles:
            db.session.add(Article(
                title=title,
                slug=slugify(title),
                content=f'<p>{content}</p>',
                author=author,
                date=datetime.now(timezone.utc),
                image=f'https://placehold.co/800x400/e0e0e0/555555?text={image_text}'
            ))

        social_links = [
            ('Facebook', 'https://facebook.com', 'fab fa-facebook-f'),
            ('X', 'https://x.com', 'fab fa-x-twitter'),
            ('Instagram', 'https://instagram.com', 'fab fa-instagram'),
            ('YouTube', 'https://youtube.com', 'fab fa-youtube'),
            ('LinkedIn', 'https://linkedin.com', 'fab fa-linkedin-in'),
        ]
        for name, url, icon in social_links:
            db.session.add(SocialMediaLink(platform=name, url=url, icon_class=icon, is_visible=True))

        db.session.add(Testimonial(
            author="John Doe",
            content="Excellent site! I found the perfect product.",
            date_posted=datetime.now(timezone.utc),
            is_visible=True,
            likes=5,
            dislikes=0
        ))

        db.session.commit()
        print("✅ Initial data created.")

    app.cli.add_command(seed_initial_data)

    # ----------- LOGIN MANAGER -----------
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # -------------------- PUBLIC HOME ROUTE --------------------
    # CORRECTION: The home route is updated to limit to 12 products
    @public_bp.route('/')
    @public_bp.route('/index')
    def index():
        products = Product.query.order_by(Product.id.desc()).limit(12).all()
        testimonials = Testimonial.query.filter_by(is_visible=True).order_by(Testimonial.id.desc()).all()
        return render_template('public/index.html', products=products, testimonials=testimonials)

    # ----------- END OF APPLICATION FACTORY -----------
    return app

# -------------------- SET ADMIN PASSWORD --------------------
def set_admin_password(app, new_password):
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            admin_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            print("Password updated for 'admin'.")
        else:
            print("User 'admin' not found.")

# -------------------- MAIN EXECUTION (FOR LOCAL DEVELOPMENT ONLY) --------------------
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        pass
    app.run(debug=True)