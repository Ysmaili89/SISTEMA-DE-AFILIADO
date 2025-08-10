# C:\Users\joran\OneDrive\data\Documentos\LMSGI\afiliados_app\routes\api.py

from flask import Blueprint, jsonify
from models import Product, Category, Subcategory, Article, Testimonial
from sqlalchemy.orm import joinedload

# Defines the Blueprint for the API with the /api prefix
bp = Blueprint('api', __name__, url_prefix='/api')

# ----------- PRODUCT ROUTES -----------

# Get all products
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

# Get a product by ID
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
    return jsonify({"message": "Product not found"}), 404

# ----------- CATEGORY ROUTES -----------

# Get all categories
@bp.route('/categories', methods=['GET'])
def api_categories():
    categories = Category.query.all()
    categories_data = [{
        "id": c.id,
        "name": c.name,
        "slug": c.slug
    } for c in categories]
    return jsonify(categories_data)

# Get a category by ID with its subcategories
@bp.route('/categories/<int:category_id>', methods=['GET'])
def api_category_by_id(category_id):
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
    return jsonify({"message": "Category not found"}), 404

# ----------- SUBCATEGORY ROUTES -----------

# Get all subcategories
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

# Get a subcategory by ID with its products
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
    return jsonify({"message": "Subcategory not found"}), 404

# ----------- ARTICLE ROUTES -----------

# Get all articles
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

# Get an article by ID
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
    return jsonify({"message": "Article not found"}), 404
    
# Get an article by its slug
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
    return jsonify({"message": "Article not found"}), 404

# ----------- TESTIMONIAL ROUTES -----------

# Get all testimonials
@bp.route('/testimonials', methods=['GET'])
def api_testimonials():
    # Get only visible testimonials, ordered by date
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

# Get a testimonial by ID
@bp.route('/testimonials/<int:testimonial_id>', methods=['GET'])
def api_testimonial_by_id(testimonial_id):
    testimonial = Testimonial.query.get(testimonial_id)
    if testimonial and testimonial.is_visible:
        return jsonify({
            "id": testimonial.id,
            "author": testimonial.author,
            "content": testimonial.content,
            "date_posted": testimonial.date_posted.isoformat() if testimonial.date_posted else None,
            "likes": testimonial.likes,
            "dislikes": testimonial.dislikes
        })
    return jsonify({"message": "Testimonial not found or not visible"}), 404