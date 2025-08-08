# C:\Users\joran\OneDrive\data\Documentos\LMSGI\afiliados_app\routes\api.py

from flask import Blueprint, jsonify
from models import Producto, Categoria, Subcategoria, Articulo, Testimonial # Asegúrate de importar el modelo Testimonial
from sqlalchemy.orm import joinedload

# Se define el Blueprint para la API con el prefijo /api
bp = Blueprint('api', __name__, url_prefix='/api')

# ----------- RUTAS DE PRODUCTOS -----------

# Obtener todos los productos
@bp.route('/productos', methods=['GET'])
def api_productos():
    productos = Producto.query.all()
    productos_data = [{
        "id": p.id,
        "nombre": p.nombre,
        "slug": p.slug,
        "precio": p.precio,
        "descripcion": p.descripcion,
        "imagen": p.imagen,
        "link": p.link,
        "subcategoria_id": p.subcategoria_id,
        "external_id": p.external_id,
        "fecha_creacion": p.fecha_creacion.isoformat() if p.fecha_creacion else None,
        "fecha_actualizacion": p.fecha_actualizacion.isoformat() if p.fecha_actualizacion else None
    } for p in productos]
    return jsonify(productos_data)

# Obtener un producto por ID
@bp.route('/productos/<int:producto_id>', methods=['GET'])
def api_producto_por_id(producto_id):
    producto = Producto.query.get(producto_id)
    if producto:
        return jsonify({
            "id": producto.id,
            "nombre": producto.nombre,
            "slug": producto.slug,
            "precio": producto.precio,
            "descripcion": producto.descripcion,
            "imagen": producto.imagen,
            "link": producto.link,
            "subcategoria_id": producto.subcategoria_id,
            "external_id": producto.external_id,
            "fecha_creacion": producto.fecha_creacion.isoformat() if producto.fecha_creacion else None,
            "fecha_actualizacion": producto.fecha_actualizacion.isoformat() if producto.fecha_actualizacion else None
        })
    return jsonify({"mensaje": "Producto no encontrado"}), 404

# ----------- RUTAS DE CATEGORÍAS -----------

# Obtener todas las categorías
@bp.route('/categorias', methods=['GET'])
def api_categorias():
    categorias = Categoria.query.all()
    categorias_data = [{
        "id": c.id,
        "nombre": c.nombre,
        "slug": c.slug
    } for c in categorias]
    return jsonify(categorias_data)

# Obtener una categoría por ID con sus subcategorías
@bp.route('/categorias/<int:categoria_id>', methods=['GET'])
def api_categoria_por_id(categoria_id):
    # Usamos joinedload para prevenir el problema de N+1 consultas para las subcategorías
    categoria = Categoria.query.options(joinedload(Categoria.subcategorias)).get(categoria_id)
    if categoria:
        subcategorias_data = [{
            "id": sc.id,
            "nombre": sc.nombre,
            "slug": sc.slug,
            "categoria_id": sc.categoria_id
        } for sc in categoria.subcategorias]
        return jsonify({
            "id": categoria.id,
            "nombre": categoria.nombre,
            "slug": categoria.slug,
            "subcategorias": subcategorias_data
        })
    return jsonify({"mensaje": "Categoría no encontrada"}), 404

# ----------- RUTAS DE SUBCATEGORÍAS -----------

# Obtener todas las subcategorías
@bp.route('/subcategorias', methods=['GET'])
def api_subcategorias():
    subcategorias = Subcategoria.query.all()
    subcategorias_data = [{
        "id": sc.id,
        "nombre": sc.nombre,
        "slug": sc.slug,
        "categoria_id": sc.categoria_id
    } for sc in subcategorias]
    return jsonify(subcategorias_data)

# Obtener una subcategoría por ID con sus productos
@bp.route('/subcategorias/<int:subcategoria_id>', methods=['GET'])
def api_subcategoria_por_id(subcategoria_id):
    subcategoria = Subcategoria.query.options(joinedload(Subcategoria.productos)).get(subcategoria_id)
    if subcategoria:
        productos_data = [{
            "id": p.id,
            "nombre": p.nombre,
            "slug": p.slug,
            "precio": p.precio,
            "imagen": p.imagen,
            "link": p.link
        } for p in subcategoria.productos]
        return jsonify({
            "id": subcategoria.id,
            "nombre": subcategoria.nombre,
            "slug": subcategoria.slug,
            "categoria_id": subcategoria.categoria_id,
            "productos": productos_data
        })
    return jsonify({"mensaje": "Subcategoría no encontrada"}), 404

# ----------- RUTAS DE ARTÍCULOS -----------

# Obtener todos los artículos
@bp.route('/articulos', methods=['GET'])
def api_articulos():
    articulos = Articulo.query.all()
    articulos_data = [{
        "id": a.id,
        "titulo": a.titulo,
        "slug": a.slug,
        "contenido": a.contenido,
        "autor": a.autor,
        "fecha": a.fecha.isoformat() if a.fecha else None,
        "imagen": a.imagen
    } for a in articulos]
    return jsonify(articulos_data)

# Obtener un artículo por ID
@bp.route('/articulos/<int:articulo_id>', methods=['GET'])
def api_articulo_por_id(articulo_id):
    articulo = Articulo.query.get(articulo_id)
    if articulo:
        return jsonify({
            "id": articulo.id,
            "titulo": articulo.titulo,
            "slug": articulo.slug,
            "contenido": articulo.contenido,
            "autor": articulo.autor,
            "fecha": articulo.fecha.isoformat() if articulo.fecha else None,
            "imagen": articulo.imagen
        })
    return jsonify({"mensaje": "Artículo no encontrado"}), 404
    
# Nuevo: Obtener un artículo por su slug
@bp.route('/articulos/slug/<string:articulo_slug>', methods=['GET'])
def api_articulo_por_slug(articulo_slug):
    articulo = Articulo.query.filter_by(slug=articulo_slug).first()
    if articulo:
        return jsonify({
            "id": articulo.id,
            "titulo": articulo.titulo,
            "slug": articulo.slug,
            "contenido": articulo.contenido,
            "autor": articulo.autor,
            "fecha": articulo.fecha.isoformat() if articulo.fecha else None,
            "imagen": articulo.imagen
        })
    return jsonify({"mensaje": "Artículo no encontrado"}), 404

# ----------- RUTAS DE TESTIMONIOS -----------

# Nuevo: Obtener todos los testimonios
@bp.route('/testimonios', methods=['GET'])
def api_testimonios():
    # Obtener solo los testimonios visibles, ordenados por fecha
    testimonios = Testimonial.query.filter_by(is_visible=True).order_by(Testimonial.date_posted.desc()).all()
    testimonios_data = [{
        "id": t.id,
        "author": t.author,
        "content": t.content,
        "date_posted": t.date_posted.isoformat() if t.date_posted else None,
        "likes": t.likes,
        "dislikes": t.dislikes
    } for t in testimonios]
    return jsonify(testimonios_data)

# Nuevo: Obtener un testimonio por ID
@bp.route('/testimonios/<int:testimonio_id>', methods=['GET'])
def api_testimonio_por_id(testimonio_id):
    testimonio = Testimonial.query.get(testimonio_id)
    if testimonio and testimonio.is_visible:
        return jsonify({
            "id": testimonio.id,
            "author": testimonio.author,
            "content": testimonio.content,
            "date_posted": testimonio.date_posted.isoformat() if testimonio.date_posted else None,
            "likes": testimonio.likes,
            "dislikes": testimonio.dislikes
        })
    return jsonify({"mensaje": "Testimonio no encontrado o no visible"}), 404