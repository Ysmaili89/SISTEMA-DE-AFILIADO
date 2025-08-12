# Importaciones de bibliotecas estándar
import functools
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from werkzeug.security import check_password_hash

# Importaciones de bibliotecas de terceros
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, current_user

# Importaciones de aplicaciones locales
from models import User, Product, Category, Subcategory, Article, SyncInfo, SocialMediaLink, ContactMessage, Testimonio, Afiliado, AffiliateStatistic, db
from forms import LoginForm, ProductForm, CategoryForm, SubCategoryForm, ArticleForm, ApiSyncForm, SocialMediaForm, ContactMessageAdminForm, TestimonialForm
from utils import slugify
from services.api_sync import fetch_and_update_products_from_external_api

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Decorador personalizado para garantizar que el usuario sea un administrador
def admin_required(f):
    @functools.wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Acceso denegado: No tienes permisos de administrador.', 'danger')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.admin_dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        print(f"Intentando iniciar sesión para el nombre de usuario: {username}")
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"Usuario encontrado: {user.username}, Es admin: {user.is_admin}")
            password_check = check_password_hash(user.password_hash, password)
            print(f"Resultado de la comprobación de contraseña: {password_check}")
            if password_check:
                if user.is_admin:
                    login_user(user)
                    flash('Inicio de sesión exitoso como administrador.', 'success')
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('admin.admin_dashboard'))
                else:
                    flash('Acceso denegado: No tienes permisos de administrador.', 'danger')
            else:
                flash('Nombre de usuario o contraseña incorrectos.', 'danger')
        else:
            flash('Nombre de usuario o contraseña incorrectos.', 'danger')
    return render_template('admin/admin_login.html', form=form)

@bp.route('/logout')
@admin_required
def admin_logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('admin.admin_login'))

@bp.route('/dashboard')
@admin_required
def admin_dashboard():
    products_count = Product.query.count()
    categories_count = Category.query.count()
    articles_count = Article.query.count()
    unread_messages_count = ContactMessage.query.filter_by(is_read=False).count()
    pending_testimonials_count = Testimonio.query.filter_by(is_visible=False).count()
    afiliados_count = Afiliado.query.count()
    estadisticas_afiliados_count = AffiliateStatistic.query.count()

    return render_template('admin/admin_dashboard.html',
                           products_count=products_count,
                           categories_count=categories_count,
                           articles_count=articles_count,
                           unread_messages_count=unread_messages_count,
                           pending_testimonials_count=pending_testimonials_count,
                           afiliados_count=afiliados_count,
                           estadisticas_afiliados_count=estadisticas_afiliados_count)

# --- Admin Products Management ---
@bp.route('/productos')
@admin_required
def admin_products():
    products = Product.query.all()

    category_lookup = {
        subcat.id: f"{cat.name} > {subcat.name}"
        for cat in Category.query.options(joinedload(Category.subcategories)).all()
        for subcat in cat.subcategories
    }

    products_for_display = []
    for p in products:
        products_for_display.append({
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "description": p.description,
            "image": p.image,
            "link": p.link,
            "subcategory_id": p.subcategory_id,
            "external_id": p.external_id,
            "category_display_name": category_lookup.get(p.subcategory_id, 'Desconocida')
        })

    return render_template('admin/admin_products.html', products=products_for_display)

@bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    form = ProductForm()

    if form.validate_on_submit():
        selected_subcategory_id = form.subcategory.data.id if form.subcategory.data else None

        external_id_value = form.external_id.data.strip()
        if external_id_value == '':
            external_id_value = None

        new_product = Product(
            name=form.name.data,
            slug=slugify(form.name.data),
            price=form.price.data,
            description=form.description.data,
            image=form.image.data,
            link=form.link.data,
            subcategory_id=selected_subcategory_id,
            external_id=external_id_value
        )
        try:
            db.session.add(new_product)
            db.session.commit()
            flash('Producto añadido exitosamente!', 'success')
            return redirect(url_for('admin.admin_products'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un producto con el mismo nombre o ID externo.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir producto: {e}', 'danger')
    return render_template('admin/admin_add_edit_product.html', form=form)

@bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)

    if form.validate_on_submit():
        selected_subcategory = form.subcategory.data
        product.subcategory_id = selected_subcategory.id if selected_subcategory else None

        external_id_value = form.external_id.data.strip()
        if external_id_value == '':
            external_id_value = None

        form.populate_obj(product)
        product.slug = slugify(product.name)
        product.external_id = external_id_value
        product.last_updated = datetime.now(timezone.utc)

        try:
            db.session.commit()
            flash('Producto actualizado exitosamente!', 'success')
            return redirect(url_for('admin.admin_products'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un producto con el mismo nombre o ID externo.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar producto: {e}', 'danger')
    return render_template('admin/admin_add_edit_product.html', form=form, product=product)

@bp.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Producto eliminado exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar producto: {e}', 'danger')
    return redirect(url_for('admin.admin_products'))

# --- Admin Categories Management ---
@bp.route('/categories')
@admin_required
def admin_categories():
    categories = Category.query.options(joinedload(Category.subcategories)).all()
    return render_template('admin/admin_categories.html', categories=categories)

@bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
def admin_add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        existing_category = Category.query.filter_by(slug=slugify(form.name.data)).first()
        if existing_category:
            flash('Error: Ya existe una categoría con ese nombre (o un slug similar).', 'danger')
            return render_template('admin/admin_add_edit_category.html', category_form=form)

        new_category = Category(name=form.name.data, slug=slugify(form.name.data))
        try:
            db.session.add(new_category)
            db.session.commit()
            flash('Categoría añadida exitosamente!', 'success')
            return redirect(url_for('admin.admin_categories'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe una categoría con ese nombre o slug.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir categoría: {e}', 'danger')

    return render_template('admin/admin_add_edit_category.html', category_form=form)

@bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        form.populate_obj(category)
        category.slug = slugify(category.name)
        try:
            db.session.commit()
            flash('Categoría actualizada exitosamente!', 'success')
            return redirect(url_for('admin.admin_categories'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe una categoría con ese nombre.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar categoría: {e}', 'danger')
    return render_template('admin/admin_add_edit_category.html', form=form, category=category)

@bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def admin_delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    try:
        db.session.delete(category)
        db.session.commit()
        flash('Categoría eliminada exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar categoría: {e}', 'danger')
    return redirect(url_for('admin.admin_categories'))

@bp.route('/categories/<int:category_id>/add_subcategory', methods=['GET', 'POST'])
@admin_required
def admin_add_subcategory(category_id):
    category = Category.query.get_or_404(category_id)
    form = SubCategoryForm()
    if form.validate_on_submit():
        new_slug = slugify(form.name.data)
        existing_subcategory = Subcategory.query.filter_by(slug=new_slug, category_id=category.id).first()
        if existing_subcategory:
            flash(f'Error: Ya existe una subcategoría con el nombre "{form.name.data}" en esta categoría. Por favor, elige un nombre diferente.', 'danger')
            return render_template('admin/admin_add_edit_subcategory.html', form=form, category=category)

        new_subcategory = Subcategory(name=form.name.data, slug=new_slug, category_id=category.id)
        try:
            db.session.add(new_subcategory)
            db.session.commit()
            flash('Subcategoría añadida exitosamente!', 'success')
            return redirect(url_for('admin.admin_categories'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe una subcategoría con ese nombre.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir subcategoría: {e}', 'danger')
    return render_template('admin/admin_add_edit_subcategory.html', form=form, category=category)

@bp.route('/categories/<int:category_id>/edit_subcategory/<int:subcategory_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_subcategory(category_id, subcategory_id):
    category = Category.query.get_or_404(category_id)
    subcategory = Subcategory.query.filter_by(id=subcategory_id, category_id=category_id).first_or_404()
    form = SubCategoryForm(obj=subcategory)
    if form.validate_on_submit():
        form.populate_obj(subcategory)
        subcategory.slug = slugify(subcategory.name)
        try:
            db.session.commit()
            flash('Subcategoría actualizada exitosamente!', 'success')
            return redirect(url_for('admin.admin_categories'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe una subcategoría con ese nombre.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar subcategoría: {e}', 'danger')
    return render_template('admin/admin_add_edit_subcategory.html', form=form, category=category, subcategory=subcategory)

@bp.route('/categories/<int:category_id>/delete_subcategory/<int:subcategory_id>', methods=['POST'])
@admin_required
def admin_delete_subcategory(category_id, subcategory_id):
    subcategory = Subcategory.query.filter_by(id=subcategory_id, category_id=category_id).first_or_404()
    try:
        db.session.delete(subcategory)
        db.session.commit()
        flash('Subcategoría eliminada exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar subcategoría: {e}', 'danger')
    return redirect(url_for('admin.admin_categories'))

# --- Admin Articles (Guias) Management ---
@bp.route('/articles')
@admin_required
def admin_articles():
    articles = Article.query.order_by(Article.date_posted.desc()).all()
    return render_template('admin/admin_articles.html', articles=articles)

@bp.route('/articles/add', methods=['GET', 'POST'])
@admin_required
def admin_add_article():
    form = ArticleForm()
    if form.validate_on_submit():
        new_article = Article(
            title=form.title.data,
            slug=slugify(form.title.data),
            content=form.content.data,
            author=form.author.data,
            date_posted=datetime.now(timezone.utc),
            image=form.image.data
        )
        try:
            db.session.add(new_article)
            db.session.commit()
            flash('Artículo añadido exitosamente!', 'success')
            return redirect(url_for('admin.admin_articles'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un artículo con ese título.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir artículo: {e}', 'danger')
    return render_template('admin/admin_add_edit_article.html', form=form)

@bp.route('/articles/edit/<int:article_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    form = ArticleForm(obj=article)
    if form.validate_on_submit():
        form.populate_obj(article)
        article.slug = slugify(article.title)
        try:
            db.session.commit()
            flash('Artículo actualizado exitosamente!', 'success')
            return redirect(url_for('admin.admin_articles'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un artículo con ese título.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar artículo: {e}', 'danger')
    return render_template('admin/admin_add_edit_article.html', form=form, article=article)

@bp.route('/articles/delete/<int:article_id>', methods=['POST'])
@admin_required
def admin_delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    try:
        db.session.delete(article)
        db.session.commit()
        flash('Artículo eliminado exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar artículo: {e}', 'danger')
    return redirect(url_for('admin.admin_articles'))

# --- Admin API Products Sync ---
@bp.route('/api_products')
@admin_required
def admin_api_products():
    sync_info = SyncInfo.query.first()
    if not sync_info:
        sync_info = SyncInfo(last_sync_time="N/A", last_sync_count=0, last_synced_api_url="N/A")
        db.session.add(sync_info)
        db.session.commit()
    form = ApiSyncForm()
    return render_template('admin/admin_api_products.html',
                           last_sync_time=sync_info.last_sync_time,
                           last_sync_count=sync_info.last_sync_count,
                           last_synced_api_url=sync_info.last_synced_api_url,
                           form=form)

@bp.route('/api_products/sync', methods=['POST'])
@admin_required
def admin_sync_api_products():
    form = ApiSyncForm()
    if form.validate_on_submit():
        api_url = form.api_url.data
        sync_info = SyncInfo.query.first()
        if not sync_info:
            sync_info = SyncInfo(last_sync_time="N/A", last_sync_count=0, last_synced_api_url="N/A")
            db.session.add(sync_info)
            db.session.commit()

        try:
            updated_count = fetch_and_update_products_from_external_api(api_url)

            sync_info.last_sync_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            sync_info.last_sync_count = updated_count
            sync_info.last_synced_api_url = api_url
            db.session.commit()

            flash(f'Sincronización API completada. Se actualizaron/añadieron {updated_count} productos.', 'success')
        except Exception as e:
            flash(f'Error durante la sincronización API. Detalles: {str(e)}', 'danger')
            db.session.rollback()
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error en {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('admin.admin_api_products'))

PLATFORM_ICONS = {
    'Facebook': 'fab fa-facebook-f',
    'Twitter': 'fab fa-x-twitter',
    'Instagram': 'fab fa-instagram',
    'LinkedIn': 'fab fa-linkedin-in',
    'YouTube': 'fab fa-youtube',
    'TikTok': 'fab fa-tiktok',
    'WhatsApp': 'fab fa-whatsapp',
    'Telegram': 'fab fa-telegram-plane',
    'Pinterest': 'fab fa-pinterest-p',
    'Snapchat': 'fab fa-snapchat-ghost',
    'Discord': 'fab fa-discord',
    'Reddit': 'fab fa-reddit-alien',
}

# --- Admin Social Media Management ---
@bp.route('/social_media')
@admin_required
def admin_social_media():
    social_media_links = SocialMediaLink.query.order_by(SocialMediaLink.order_num).all()
    return render_template('admin/admin_social_media.html', social_media_links=social_media_links)

@bp.route('/social_media/add', methods=['GET', 'POST'])
@admin_required
def admin_add_social_media():
    form = SocialMediaForm()
    if form.validate_on_submit():
        platform_name = form.platform.data
        icon_class = PLATFORM_ICONS.get(platform_name, 'fas fa-link')

        new_link = SocialMediaLink(
            platform=platform_name,
            url=form.url.data,
            icon_class=icon_class,
            is_visible=form.is_visible.data,
            order_num=SocialMediaLink.query.count()
        )
        try:
            db.session.add(new_link)
            db.session.commit()
            flash('Social media link added successfully!', 'success')
            return redirect(url_for('admin.admin_social_media'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un enlace para esta plataforma.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir enlace: {e}', 'danger')
    return render_template('admin/admin_add_edit_social_media.html', form=form)

@bp.route('/social_media/edit/<int:link_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_social_media(link_id):
    link = SocialMediaLink.query.get_or_404(link_id)
    form = SocialMediaForm(obj=link)

    if form.validate_on_submit():
        platform_name = form.platform.data
        icon_class = PLATFORM_ICONS.get(platform_name, 'fas fa-link')

        form.populate_obj(link)
        link.icon_class = icon_class
        try:
            db.session.commit()
            flash('Social media link updated successfully!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un enlace para esta plataforma.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar enlace: {e}', 'danger')
    return render_template('admin/admin_add_edit_social_media.html', form=form, link=link)

@bp.route('/social_media/delete/<int:link_id>', methods=['POST'])
@admin_required
def admin_delete_social_media(link_id):
    link = SocialMediaLink.query.get_or_404(link_id)
    try:
        db.session.delete(link)
        db.session.commit()
        flash('Social media link deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar enlace: {e}', 'danger')
    return redirect(url_for('admin.admin_social_media'))

# --- Admin Contact Messages Management ---
@bp.route('/messages')
@admin_required
def admin_messages():
    messages = ContactMessage.query.order_by(ContactMessage.timestamp.desc()).all()
    return render_template('admin/admin_messages.html', messages=messages)

@bp.route('/messages/view/<int:message_id>', methods=['GET', 'POST'])
@admin_required
def admin_view_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    form = ContactMessageAdminForm(obj=message)

    if not message.is_read:
        message.is_read = True
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error al marcar mensaje como leído: {e}', 'danger')

    if form.validate_on_submit():
        message.is_read = form.is_read.data
        message.is_archived = form.is_archived.data

        if form.response_text.data:
            message.response_text = form.response_text.data
            message.response_timestamp = datetime.now(timezone.utc)
        else:
            message.response_text = None
            message.response_timestamp = None

        try:
            db.session.commit()
            flash('Mensaje actualizado exitosamente!', 'success')
            return redirect(url_for('admin.admin_messages'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar mensaje: {e}', 'danger')

    return render_template('admin/admin_view_message.html', message=message, form=form)

@bp.route('/messages/delete/<int:message_id>', methods=['POST'])
@admin_required
def admin_delete_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    try:
        db.session.delete(message)
        db.session.commit()
        flash('Mensaje eliminado permanentemente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar mensaje: {e}', 'danger')
    return redirect(url_for('admin.admin_messages'))

@bp.route('/messages/toggle_archive/<int:message_id>', methods=['POST'])
@admin_required
def admin_toggle_archive_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.is_archived = not message.is_archived
    try:
        db.session.commit()
        status = "archivado" if message.is_archived else "desarchivado"
        flash(f'Mensaje {status} exitosamente.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar estado de archivo: {e}', 'danger')
    return redirect(url_for('admin.admin_messages'))

@bp.route('/messages/toggle_read/<int:message_id>', methods=['POST'])
@admin_required
def admin_toggle_read_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.is_read = not message.is_read
    try:
        db.session.commit()
        status = "leído" if message.is_read else "no leído"
        flash(f'Mensaje marcado como {status} exitosamente.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar estado de lectura: {e}', 'danger')
    return redirect(url_for('admin.admin_messages'))

@bp.route('/messages/like/<int:message_id>', methods=['POST'])
@admin_required
def admin_like_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.likes += 1
    try:
        db.session.commit()
        flash('Me gusta añadido al mensaje.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al añadir me gusta: {e}', 'danger')
    return redirect(url_for('admin.admin_view_message', message_id=message_id))

@bp.route('/messages/dislike/<int:message_id>', methods=['POST'])
@admin_required
def admin_dislike_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.dislikes += 1
    try:
        db.session.commit()
        flash('No me gusta añadido al mensaje.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al añadir no me gusta: {e}', 'danger')
    return redirect(url_for('admin.admin_view_message', message_id=message_id))

# --- Admin Testimonials Management ---
@bp.route('/testimonials')
@admin_required
def admin_testimonials():
    testimonials = Testimonio.query.order_by(Testimonio.date_posted.desc()).all()
    return render_template('admin/admin_testimonials.html', testimonials=testimonials)

@bp.route('/testimonials/add', methods=['GET', 'POST'])
@admin_required
def admin_add_testimonial():
    form = TestimonialForm()
    if form.validate_on_submit():
        new_testimonial = Testimonio(
            author=form.author.data,
            content=form.content.data,
            is_visible=form.is_visible.data,
            date_posted=datetime.now(timezone.utc)
        )
        try:
            db.session.add(new_testimonial)
            db.session.commit()
            flash('Testimonio añadido exitosamente!', 'success')
            return redirect(url_for('admin.admin_testimonials'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir testimonio: {e}', 'danger')
    return render_template('admin/admin_add_edit_testimonial.html', form=form)

@bp.route('/testimonials/edit/<int:testimonial_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_testimonial(testimonial_id):
    testimonial = Testimonio.query.get_or_404(testimonial_id)
    form = TestimonialForm(obj=testimonial)

    if request.method == 'GET':
        form.likes.data = testimonial.likes
        form.dislikes.data = testimonial.dislikes

    if form.validate_on_submit():
        form.populate_obj(testimonial)
        try:
            db.session.commit()
            flash('Testimonio actualizado exitosamente!', 'success')
            return redirect(url_for('admin.admin_testimonials'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar testimonio: {e}', 'danger')
    return render_template('admin/admin_add_edit_testimonial.html', form=form, testimonial=testimonial)

@bp.route('/testimonials/delete/<int:testimonial_id>', methods=['POST'])
@admin_required
def admin_delete_testimonial(testimonial_id):
    testimonial = Testimonio.query.get_or_404(testimonial_id)
    try:
        db.session.delete(testimonial)
        db.session.commit()
        flash('Testimonio eliminado permanentemente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar testimonio: {e}', 'danger')
    return redirect(url_for('admin.admin_testimonials'))

@bp.route('/testimonials/toggle_visibility/<int:testimonial_id>', methods=['POST'])
@admin_required
def admin_toggle_visibility_testimonial(testimonial_id):
    testimonial = Testimonio.query.get_or_404(testimonial_id)
    testimonial.is_visible = not testimonial.is_visible
    try:
        db.session.commit()
        status = "visible" if testimonial.is_visible else "oculto"
        flash(f'Testimonio marcado como {status} exitosamente.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar estado de visibilidad: {e}', 'danger')
    return redirect(url_for('admin.admin_testimonials'))

# --- NUEVAS RUTAS PARA LOS "ME GUSTA" / "NO ME GUSTA" DE LOS TESTIMONIOS ---
@bp.route('/testimonials/like/<int:testimonial_id>', methods=['POST'])
@admin_required
def admin_like_testimonial(testimonial_id):
    testimonial = Testimonio.query.get_or_404(testimonial_id)
    testimonial.likes += 1
    try:
        db.session.commit()
        flash(f'Me gusta añadido al testimonio de "{testimonial.author}".', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al añadir me gusta al testimonio: {e}', 'danger')
    return redirect(url_for('admin.admin_testimonials'))

@bp.route('/testimonials/dislike/<int:testimonial_id>', methods=['POST'])
@admin_required
def admin_dislike_testimonial(testimonial_id):
    testimonial = Testimonio.query.get_or_404(testimonial_id)
    testimonial.dislikes += 1
    try:
        db.session.commit()
        flash(f'No me gusta añadido al testimonio de "{testimonial.author}".', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al añadir no me gusta al testimonio: {e}', 'danger')
    return redirect(url_for('admin.admin_testimonials'))