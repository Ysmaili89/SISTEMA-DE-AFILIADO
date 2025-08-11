# C:\Users\joran\OneDrive\data\Documentos\LMSGI\afiliados_app\routes\api.py

from flask import Blueprint, jsonify
from models import Product, Category, Subcategory, Article, Testimonial # Asegúrate de importar el modelo Testimonial
from sqlalchemy.orm import joinedload

# Se define el Blueprint para la API con el prefijo /api
bp = Blueprint('api', __name__, url_prefix='/api')

# ----------- RUTAS DE PRODUCTOS -----------

# Obtener todos los productos
@bp.route('/products', methods=['GET'])
def api_products():
    products = Product.query.all()
    products_data = [{
        "id": p.id,
        "name": p.name,
        "slug": p.slug,
        "price": p.price,
        "description": p.description,
        "image": p.image,
        "link": p.link,
        "subcategory_id": p.subcategory_id,
        "external_id": p.external_id,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None
    } for p in products]
    return jsonify(products_data)

# Obtener un producto por ID
@bp.route('/products/<int:product_id>', methods=['GET'])
def api_product_by_id(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "price": product.price,
            "description": product.description,
            "image": product.image,
            "link": product.link,
            "subcategory_id": product.subcategory_id,
            "external_id": product.external_id,
            "created_at": product.created_at.isoformat() if product.created_at else None,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None
        })
    return jsonify({"mensaje": "Producto no encontrado"}), 404

# ----------- RUTAS DE CATEGORÍAS -----------

# Obtener todas las categorías
@bp.route('/categories', methods=['GET'])
def api_categories():
    categories = Category.query.all()
    categories_data = [{
        "id": c.id,
        "name": c.name,
        "slug": c.slug
    } for c in categories]
    return jsonify(categories_data)

# Obtener una categoría por ID con sus subcategorías
@bp.route('/categories/<int:category_id>', methods=['GET'])
def api_category_by_id(category_id):
    # Usamos joinedload para prevenir el problema de N+1 consultas para las subcategorías
    category = Category.query.options(joinedload(Category.subcategories)).get(category_id)
    if category:
        subcategories_data = [{
            "id": sc.id,
            "name": sc.name,
            "slug": sc.slug,
            "category_id": sc.category_id
        } for sc in category.subcategories]
        return jsonify({
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "subcategories": subcategories_data
        })
    return jsonify({"mensaje": "Categoría no encontrada"}), 404

# ----------- RUTAS DE SUBCATEGORÍAS -----------

# Obtener todas las subcategorías
@bp.route('/subcategories', methods=['GET'])
def api_subcategories():
    subcategories = Subcategory.query.all()
    subcategories_data = [{
        "id": sc.id,
        "name": sc.name,
        "slug": sc.slug,
        "category_id": sc.category_id
    } for sc in subcategories]
    return jsonify(subcategories_data)

# Obtener una subcategoría por ID con sus productos
@bp.route('/subcategories/<int:subcategory_id>', methods=['GET'])
def api_subcategory_by_id(subcategory_id):
    subcategory = Subcategory.query.options(joinedload(Subcategory.products)).get(subcategory_id)
    if subcategory:
        products_data = [{
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "price": p.price,
            "image": p.image,
            "link": p.link
        } for p in subcategory.products]
        return jsonify({
            "id": subcategory.id,
            "name": subcategory.name,
            "slug": subcategory.slug,
            "category_id": subcategory.category_id,
            "products": products_data
        })
    return jsonify({"mensaje": "Subcategoría no encontrada"}), 404

# ----------- RUTAS DE ARTÍCULOS -----------

# Obtener todos los artículos
@bp.route('/articles', methods=['GET'])
def api_articles():
    articles = Article.query.all()
    articles_data = [{
        "id": a.id,
        "title": a.title,
        "slug": a.slug,
        "content": a.content,
        "author": a.author,
        "date_posted": a.date_posted.isoformat() if a.date_posted else None,
        "image": a.image
    } for a in articles]
    return jsonify(articles_data)

# Obtener un artículo por ID
@bp.route('/articles/<int:article_id>', methods=['GET'])
def api_article_by_id(article_id):
    article = Article.query.get(article_id)
    if article:
        return jsonify({
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "content": article.content,
            "author": article.author,
            "date_posted": article.date_posted.isoformat() if article.date_posted else None,
            "image": article.image
        })
    return jsonify({"mensaje": "Artículo no encontrado"}), 404
    
# Nuevo: Obtener un artículo por su slug
@bp.route('/articles/slug/<string:article_slug>', methods=['GET'])
def api_article_by_slug(article_slug):
    article = Article.query.filter_by(slug=article_slug).first()
    if article:
        return jsonify({
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "content": article.content,
            "author": article.author,
            "date_posted": article.date_posted.isoformat() if article.date_posted else None,
            "image": article.image
        })
    return jsonify({"mensaje": "Artículo no encontrado"}), 404

# ----------- RUTAS DE TESTIMONIOS -----------

# Nuevo: Obtener todos los testimonios
@bp.route('/testimonials', methods=['GET'])
def api_testimonials():
    # Obtener solo los testimonios visibles, ordenados por fecha
    testimonials = Testimonial.query.filter_by(is_visible=True).order_by(Testimonial.date_posted.desc()).all()
    testimonials_data = [{
        "id": t.id,
        "author": t.author,
        "content": t.content,
        "date_posted": t.date_posted.isoformat() if t.date_posted else None,
        "likes": t.likes,
        "dislikes": t.dislikes
    } for t in testimonials]
    return jsonify(testimonials_data)

# Nuevo: Obtener un testimonio por ID
@bp.route('/testimonials/<int:testimonial_id>', methods=['GET'])
def api_testimonial_by_id(testimonial_id):
    testimonial = Testimonial.query.get(testimonial_id)
    # Corrección: Uso de 'if' y 'and' en lugar de 'si' y 'y'
    if testimonial and testimonial.is_visible:
        # Corrección: Nombres de variables del modelo en inglés
        return jsonify({
            "id": testimonial.id,
            "author": testimonial.author,
            "content": testimonial.content,
            "date_posted": testimonial.date_posted.isoformat() if testimonial.date_posted else None,
            "likes": testimonial.likes,
            "dislikes": testimonial.dislikes
        })
    return jsonify({"mensaje": "Testimonio no encontrado o no visible"}), 404