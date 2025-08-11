# Importaciones de bibliotecas estándar
import os
from datetime import datetime, date, timezone

# Importaciones de terceros
from openai import OpenAI
from dotenv import load_dotenv
from flask import Blueprint, render_template, flash, redirect, url_for, request
from sqlalchemy import func
from sqlalchemy.orm import joinedload

# Importaciones de aplicaciones locales
from models import (
    Product, Category, Subcategory, Article, ContactMessage,
    Testimonial, Advertisement, Affiliate, AffiliateStatistic, AdsenseConfig
)
from forms import PublicTestimonialForm
from extensions import db

# Cargar variables de entorno lo antes posible
load_dotenv()

# Definir el plan 'publico'
bp = Blueprint('public', __name__)
# Configurar el cliente OpenAI
# Este bloque inicializa el cliente de OpenAI si la clave está disponible.
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured in the environment.")
    
    openai_client = OpenAI(api_key=api_key)

except Exception as e:
    print(f"Error initializing OpenAI client in public.py: {e}")
    openai_client = None

# --- Funciones auxiliares para herramientas de chatbot ---
# Estas funciones interactúan con la base de datos y preparan los datos para el chatbot.

def get_all_products_for_chatbot():
    """
    Retrieves all products from the database and formats them for the chatbot.
    Returns a list of dictionaries containing product ID, name, price, description, and link.
    Handles possible database errors.
    """
    try:
        products = Product.query.all()
        products_data = []
        for p in products:
            products_data.append({
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "description": p.description,
                "link": p.link
            })
        return products_data
    except Exception as e:
        print(f"Error getting products for chatbot: {e}")
        return []

def get_product_by_name_for_chatbot(product_name):
    """
    Retrieves details of a specific product by its name, formatted for the chatbot.
    Performs a case-insensitive search.
    Returns a dictionary with product details or a message if not found or an error occurs.
    """
    try:
        product = Product.query.filter(func.lower(Product.name) == func.lower(product_name)).first()
        if product:
            return {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "description": product.description,
                "link": product.link
            }
        return {"message": f"Product '{product_name}' not found."}
    except Exception as e:
        print(f"Error getting product by name for chatbot: {e}")
        return {"error": f"Could not retrieve product by name: {str(e)}"}

def get_available_categories():
    """
    Retrieves all product categories and returns their names as a list.
    Handles possible database errors.
    """
    try:
        categories = [cat.name for cat in Category.query.all()]
        return {"categories": categories}
    except Exception as e:
        print(f"Error getting available categories: {e}")
        return {"error": f"Could not retrieve categories: {str(e)}"}

def get_shipping_info():
    """
    Provides general information about the store's shipping policies.
    """
    return {"shipping_info": "We offer nationwide shipping. Estimated delivery time is 3 to 5 business days. For specific tracking, please visit our contact section."}

def get_contact_info():
    """
    Provides contact information for customer support, including a dynamic URL to the contact page.
    """
    contact_url = url_for('public.contact', _external=True)
    return {"contact_info": f"You can contact our support team by visiting our contact section at {contact_url} or by sending an email to soporte@afiliadosonline.com."}

def get_general_help_info():
    """
    Provides general information on where to find help and guides, including a dynamic URL to the guides section.
    """
    guides_url = url_for('public.guides', _external=True)
    return {"help_info": f"You can find detailed guides and additional help in our Guides section: {guides_url}."}

### Context Processors
# Estos decoradores inyectan variables en el contexto de todas las plantillas.

@bp.context_processor
def inject_active_advertisements():
    """
    Injects a list of active advertisements into the template context.
    Advertisements are filtered by is_active=True and by start/end dates if defined.
    """
    now_utc = datetime.now(timezone.utc)
    active_ads = Advertisement.query.options(joinedload(Advertisement.product)).filter(
        Advertisement.is_active,
        (Advertisement.start_date.is_(None)) | (Advertisement.start_date <= now_utc),
        (Advertisement.end_date.is_(None)) | (Advertisement.end_date >= now_utc)
    ).all()
    return dict(active_advertisements=active_ads)

@bp.context_processor
def inject_adsense_config():
    """
    Inyecta la configuración global de AdSense en el contexto de la plantilla,
    obteniendo los datos de la base de datos.
    """
    adsense_config_db = AdsenseConfig.query.first()
    if adsense_config_db:
        return dict(
            adsense_client_id=adsense_config_db.adsense_client_id,
            adsense_slot_header=adsense_config_db.adsense_slot_header,
            adsense_slot_sidebar=adsense_config_db.adsense_slot_sidebar,
            adsense_slot_article_top=adsense_config_db.adsense_slot_article_top,
            adsense_slot_article_bottom=adsense_config_db.adsense_slot_article_bottom
        )
    else:
        return dict(
            adsense_client_id='',
            adsense_slot_header='',
            adsense_slot_sidebar='',
            adsense_slot_article_top='',
            adsense_slot_article_bottom=''
        )

# --- Public Routes ---

@bp.route('/')
def index():
    """Renders the main index page with paginated products."""
    page = request.args.get('page', 1, type=int)
    per_page = 9
    products_pagination = Product.query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    products = products_pagination.items
    total_pages = products_pagination.pages
    return render_template('index.html', products=products, page=page, total_pages=total_pages)

@bp.route('/product/<slug>')
def product_detail(slug):
    """Renders the detail page for a specific product based on its slug."""
    product = Product.query.filter_by(slug=slug).first()
    if product:
        return render_template('product_detail.html', product=product)
    flash('Producto no encontrado.', 'danger')
    return redirect(url_for('public.index'))

@bp.route('/categories')
def show_categories():
    """Renders the categories page, displaying all categories and product counts per subcategory."""
    categories = Category.query.all()
    product_counts_raw = db.session.query(
        Subcategory.id,
        func.count(Product.id)
    ).outerjoin(Product, Subcategory.id == Product.subcategory_id) \
        .group_by(Subcategory.id) \
        .all()
    product_counts_dict = {sub_id: count for sub_id, count in product_counts_raw}
    return render_template(
        'categorias.html',
        categories=categories,
        product_counts=product_counts_dict
    )

@bp.route('/products/<slug>')
def products_by_slug(slug):
    """Renders a page displaying products within a specific subcategory based on its slug."""
    subcat = Subcategory.query.filter_by(slug=slug).first()
    if subcat:
        page = request.args.get('page', 1, type=int)
        per_page = 9
        products_pagination = Product.query.filter_by(subcategory_id=subcat.id).paginate(page=page, per_page=per_page, error_out=False)
        products_in_subcat = products_pagination.items
        total_pages = products_pagination.pages
        return render_template('productos_por_subcategoria.html',
                               subcat_name=subcat.name,
                               products=products_in_subcat,
                               page=page,
                               total_pages=total_pages)
    flash('Subcategoría no encontrada.', 'danger')
    return redirect(url_for('public.show_categories'))

@bp.route('/guides')
def guides():
    """Renders the guides page with paginated articles."""
    page = request.args.get('page', 1, type=int)
    per_page = 6
    articles_pagination = Article.query.order_by(Article.date_posted.desc()).paginate(page=page, per_page=per_page, error_out=False)
    articles_db = articles_pagination.items
    total_pages = articles_pagination.pages
    articles = []
    for art in articles_db:
        # Normalizar la fecha a datetime con timezone
        date_dt = art.date_posted
        if isinstance(art.date_posted, date) and not isinstance(art.date_posted, datetime):
            date_dt = datetime.combine(art.date_posted, datetime.min.time()).replace(tzinfo=timezone.utc)
        elif isinstance(art.date_posted, datetime) and art.date_posted.tzinfo is None:
            date_dt = art.date_posted.replace(tzinfo=timezone.utc)

        articles.append({
            "title": art.title,
            "slug": art.slug,
            "content": art.content,
            "date_iso": date_dt.strftime("%Y-%m-%d") if date_dt else "",
            "formatted_date": date_dt.strftime("%d %b %Y") if date_dt else "",
        })
    return render_template('guias.html', articles=articles, page=page, total_pages=total_pages)

@bp.route('/guide/<slug>')
def guide_detail(slug):
    """Renders the detail page for a specific article based on its slug."""
    article = Article.query.filter_by(slug=slug).first()
    if article:
        # Normalizar la fecha a datetime con timezone antes de pasarla a la plantilla
        if isinstance(article.date_posted, date) and not isinstance(article.date_posted, datetime):
            article.date_posted = datetime.combine(article.date_posted, datetime.min.time()).replace(tzinfo=timezone.utc)
        elif isinstance(article.date_posted, datetime) and article.date_posted.tzinfo is None:
            article.date_posted = article.date_posted.replace(tzinfo=timezone.utc)
        return render_template('guia_detalle.html', article=article)
    flash('Artículo no encontrado.', 'danger')
    return redirect(url_for('public.guides'))

@bp.route('/about', methods=['GET', 'POST'])
def about():
    testimonial_form = PublicTestimonialForm()

    if testimonial_form.validate_on_submit():
        # Honeypot check for spam, redirect silently if filled
        if testimonial_form.fax_number.data:
            print("Spam detected: honeypot field filled for testimonial submission.")
            return redirect(url_for('public.about'))

        try:
            new_testimonial = Testimonial(
                author=testimonial_form.author.data,
                content=testimonial_form.content.data,
                is_visible=False, # Testimonios no son visibles por defecto, esperan aprobación
                date_posted=datetime.now(timezone.utc)
            )
            db.session.add(new_testimonial)
            db.session.commit()
            flash('¡Gracias por tu testimonio! Será revisado y, si es aprobado, aparecerá pronto en nuestra página.', 'success')
            return redirect(url_for('public.about'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al enviar tu testimonio. Por favor, inténtalo de nuevo. Detalles: {e}', 'danger')
            print(f"Error saving testimonial: {e}")

    # Obtener testimonios visibles para mostrar en la página
    testimonials = Testimonial.query.filter_by(is_visible=True).order_by(Testimonial.date_posted.desc()).all()
    return render_template('about.html', testimonials=testimonials, testimonial_form=testimonial_form)

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Renders the contact page and handles form submissions."""
    errors = {}
    success = False

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        fax_number = request.form.get('fax_number')

        if not name:
            errors['name'] = 'El nombre es obligatorio.'
        if not email or '@' not in email:
            errors['email'] = 'Introduce un correo electrónico válido.'
        if not message:
            errors['message'] = 'El mensaje es obligatorio.'

        if fax_number:
            print("Spam detected: honeypot field filled.")
            return redirect(url_for('public.contact'))

        if not errors:
            try:
                new_message = ContactMessage(
                    name=name,
                    email=email,
                    message=message,
                    timestamp=datetime.now(timezone.utc)
                )
                db.session.add(new_message)
                db.session.commit()
                flash('¡Gracias! Tu mensaje ha sido enviado correctamente. Nos pondremos en contacto contigo pronto.', 'success')
                success = True
                return render_template('contact.html', success=success, errors={})
            except Exception as e:
                db.session.rollback()
                flash(f'Ocurrió un error al enviar tu mensaje: {e}', 'danger')
                print(f"Error saving contact message: {e}")
                errors['general'] = 'Ocurrió un error al enviar tu mensaje. Inténtalo de nuevo.'

    return render_template('contact.html', success=success, errors=errors)

@bp.route('/privacy-policy')
def privacy_policy():
    """Renders the privacy policy page."""
    return render_template('privacy_policy.html')

@bp.route('/terms-conditions')
def terms_conditions():
    """Renders the terms and conditions page."""
    return render_template('terms_conditions.html')

@bp.route('/cookie-policy')
def cookie_policy():
    """Renders the cookie policy page."""
    return render_template('cookie_policy.html')

@bp.route('/sitemap.xml')
def sitemap():
    """Generates and serves the sitemap.xml for SEO."""
    base_url = request.url_root.rstrip('/')
    urls = [
        {"loc": base_url + url_for('public.index'), "changefreq": "daily", "priority": "1.0"},
        {"loc": base_url + url_for('public.show_categories'), "changefreq": "weekly", "priority": "0.8"},
        {"loc": base_url + url_for('public.about'), "changefreq": "monthly", "priority": "0.7"},
        {"loc": base_url + url_for('public.contact'), "changefreq": "monthly", "priority": "0.6"},
        {"loc": base_url + url_for('public.guides'), "changefreq": "weekly", "priority": "0.9"},
        {"loc": base_url + url_for('public.privacy_policy'), "changefreq": "monthly", "priority": "0.5"},
        {"loc": base_url + url_for('public.terms_conditions'), "changefreq": "monthly", "priority": "0.5"},
        {"loc": base_url + url_for('public.cookie_policy'), "changefreq": "monthly", "priority": "0.5"},
    ]
    for product in Product.query.all():
        urls.append({
            "loc": f"{base_url}{url_for('public.product_detail', slug=product.slug)}",
            "changefreq": "weekly",
            "priority": "0.8"
        })
    for article in Article.query.all():
        urls.append({
            "loc": f"{base_url}{url_for('public.guide_detail', slug=article.slug)}",
            "changefreq": "weekly",
            "priority": "0.8"
        })
    return render_template('sitemap.xml', urls=urls, today=datetime.now().strftime("%Y-%m-%d"))

@bp.route('/robots.txt')
def robots_txt():
    """Serves the robots.txt file for web crawlers."""
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Sitemap: " + request.url_root.rstrip('/') + url_for('public.sitemap') + "\n"
    )

@bp.route('/search')
def search_results():
    """
    Renders the search results page, searching both products and articles.
    """
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 9

    products_found = []
    articles_found = []
    
    # Se inicializan las variables de paginación fuera del bloque 'if'
    # para evitar errores de linter.
    total_products_pages = 0
    total_articles_pages = 0
    total_pages = 1

    if query:
        products_query = Product.query.filter(
            (Product.name.ilike(f'%{query}%')) |
            (Product.description.ilike(f'%{query}%'))
        )
        articles_query = Article.query.filter(
            (Article.title.ilike(f'%{query}%')) |
            (Article.content.ilike(f'%{query}%'))
        )

        products_pagination = products_query.paginate(page=page, per_page=per_page, error_out=False)
        products_found = products_pagination.items
        total_products_pages = products_pagination.pages

        articles_pagination = articles_query.paginate(page=page, per_page=per_page, error_out=False)
        articles_found = articles_pagination.items
        total_articles_pages = articles_pagination.pages

        total_pages = max(total_products_pages, total_articles_pages) if products_found or articles_found else 1

    return render_template('search_results.html',
                           query=query,
                           products=products_found,
                           articles=articles_found,
                           page=page,
                           total_pages=total_pages)

### Interfaz de usuario de afiliados y rutas API

@bp.route('/ref/<int:affiliate_id>')
def register_click(affiliate_id):
    """
    Registra un clic para un afiliado y lo redirige a su enlace.
    """
    affiliate = Affiliate.query.get_or_404(affiliate_id)

    # Busca si ya existe una estadística para este afiliado en el día de hoy
    statistic = AffiliateStatistic.query.filter_by(
        affiliate_id=affiliate.id,
        date=date.today()
    ).first()

    if statistic:
        # Si existe, incrementa el contador de clics
        statistic.clicks += 1
    else:
        # Si no existe, crea una nueva entrada
        statistic = AffiliateStatistic(
            affiliate_id=affiliate.id,
            clicks=1,
            date=date.today()
        )
        db.session.add(statistic)

    # Guarda los cambios en la base de datos
    db.session.commit()

    # Redirige al usuario al enlace del afiliado
    return redirect(affiliate.referral_link)