# Importaciones de Flask y extensiones
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, current_user

# Importaciones para manejo de base de datos y ORM
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

# Importaciones para manejo de fechas
from datetime import datetime, timezone
import functools

# Importaciones de modelos
from models import (
    User,
    Product,
    Category,
    Subcategory,
    Article,
    SyncInfo,
    SocialMediaLink,
    ContactMessage,
    Testimonial,
    # Advertisement,  # <-- eliminado porque no se usa
    Affiliate,
    AffiliateStatistic,
    AdsenseConfig,
)

# Importaciones de extensiones
from extensions import db

# Importaciones de formularios
from forms import (
    LoginForm,
    ProductForm,
    CategoryForm,
    SubCategoryForm,
    ArticleForm,
    ApiSyncForm,
    SocialMediaForm,
    TestimonialForm,
    AffiliateForm,
    AdsenseConfigForm,
)

# Utilidades y servicios
from utils import slugify
from services.api_sync import fetch_and_update_products_from_external_api

# Creación del blueprint admin
bp = Blueprint('admin', __name__, url_prefix='/admin')

# --- Decorador para acceso solo para administradores ---
def admin_required(f):
    """Decorador personalizado para garantizar que el usuario sea un administrador."""
    @functools.wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Acceso denegado: No tiene permisos de administrador.', 'danger')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# --- Authentication Routes ---
@bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Handles admin login."""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.admin_dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_admin:
            login_user(user)
            flash('Login successful as an administrator.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.admin_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('admin/admin_login.html', form=form)

@bp.route('/logout')
@admin_required
def admin_logout():
    """Logs the admin user out."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.admin_login'))

# --- Main Dashboard ---
@bp.route('/dashboard')
@admin_required
def admin_dashboard():
    """Displays the admin dashboard with summary statistics."""
    # Using consistent, standard Python class names (e.g., from `models` module)
    product_count = Product.query.count()
    category_count = Category.query.count()
    article_count = Article.query.count()
    unread_messages_count = ContactMessage.query.filter_by(is_read=False).count()
    pending_testimonials_count = Testimonial.query.filter_by(is_visible=False).count()
    affiliate_count = Affiliate.query.count()
    affiliate_statistic_count = AffiliateStatistic.query.count()

    return render_template('admin/admin_dashboard.html',
                           product_count=product_count,
                           category_count=category_count,
                           article_count=article_count,
                           unread_messages_count=unread_messages_count,
                           pending_testimonials_count=pending_testimonials_count,
                           affiliate_count=affiliate_count,
                           affiliate_statistic_count=affiliate_statistic_count)
# --- Product Management ---
@bp.route('/products')
@admin_required
def admin_products():
    """Displays a list of all products."""
    products = Product.query.all()
    category_lookup = {
        subcat.id: f"{cat.name} > {subcat.name}"
        for cat in Category.query.options(joinedload(Category.subcategories)).all()
        for subcat in cat.subcategories
    }
    products_for_display = [
        {
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "price": p.price,
            "description": p.description,
            "image": p.image,
            "link": p.link,
            "subcategory_id": p.subcategory_id,
            "external_id": p.external_id,
            "category_display_name": category_lookup.get(p.subcategory_id, 'Uncategorized')
        } for p in products
    ]
    return render_template('admin/admin_products.html', products=products_for_display)

@bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    """Adds a new product."""
    form = ProductForm()
    
    if form.validate_on_submit():
        selected_subcategory_id = form.subcategory.data.id if form.subcategory.data else None

        external_id_value = form.external_id.data.strip()
        if not external_id_value:
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
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin.admin_products'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: A product with this name or external ID already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {e}', 'danger')
    return render_template('admin/admin_add_edit_product.html', form=form)

@bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    """Edits an existing product."""
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)

    if form.validate_on_submit():
        selected_subcategory = form.subcategory.data
        product.subcategory_id = selected_subcategory.id if selected_subcategory else None

        external_id_value = form.external_id.data.strip()
        if not external_id_value:
            external_id_value = None

        form.populate_obj(product)
        product.slug = slugify(product.name)
        product.external_id = external_id_value
        product.updated_at = datetime.now(timezone.utc)

        try:
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin.admin_products'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: A product with this name or external ID already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {e}', 'danger')
    return render_template('admin/admin_add_edit_product.html', form=form, product=product)

@bp.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    """Deletes a product."""
    product = Product.query.get_or_404(product_id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {e}', 'danger')
    return redirect(url_for('admin.admin_products'))

# --- Category Management ---
@bp.route('/categories')
@admin_required
def admin_categories():
    """Displays a list of all categories and subcategories."""
    categories = Category.query.options(joinedload(Category.subcategories)).all()
    return render_template('admin/admin_categories.html', categories=categories)

@bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
def admin_add_category():
    """Adds a new category."""
    form = CategoryForm()
    if form.validate_on_submit():
        existing_category = Category.query.filter_by(slug=slugify(form.name.data)).first()
        if existing_category:
            flash('Error: A category with this name (or a similar slug) already exists.', 'danger')
            return render_template('admin/admin_add_edit_category.html', form=form)

        new_category = Category(name=form.name.data, slug=slugify(form.name.data))
        try:
            db.session.add(new_category)
            db.session.commit()
            flash('Category added successfully!', 'success')
            return redirect(url_for('admin.admin_categories'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: A category with this name or slug already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding category: {e}', 'danger')
    return render_template('admin/admin_add_edit_category.html', form=form)

@bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_category(category_id):
    """Edits an existing category."""
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        form.populate_obj(category)
        category.slug = slugify(category.name)
        try:
            db.session.commit()
            flash('Category updated successfully!', 'success')
            return redirect(url_for('admin.admin_categories'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: A category with this name already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating category: {e}', 'danger')
    return render_template('admin/admin_add_edit_category.html', form=form, category=category)

@bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def admin_delete_category(category_id):
    """Deletes a category and its subcategories/products."""
    category = Category.query.get_or_404(category_id)
    try:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {e}', 'danger')
    return redirect(url_for('admin.admin_categories'))

# --- Subcategory Management ---
@bp.route('/categories/<int:category_id>/add_subcategory', methods=['GET', 'POST'])
@admin_required
def admin_add_subcategory(category_id):
    """Adds a new subcategory to a specific category."""
    category = Category.query.get_or_404(category_id)
    form = SubCategoryForm()
    if form.validate_on_submit():
        new_slug = slugify(form.name.data)
        existing_subcategory = Subcategory.query.filter_by(slug=new_slug, category_id=category.id).first()
        if existing_subcategory:
            flash(f'Error: A subcategory named "{form.name.data}" already exists in this category. Please choose a different name.', 'danger')
            return render_template('admin/admin_add_edit_subcategory.html', form=form, category=category)

        new_subcategory = Subcategory(name=form.name.data, slug=new_slug, category_id=category.id)
        try:
            db.session.add(new_subcategory)
            db.session.commit()
            flash('Subcategory added successfully!', 'success')
            return redirect(url_for('admin.admin_categories'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: A subcategory with this name already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding subcategory: {e}', 'danger')
    return render_template('admin/admin_add_edit_subcategory.html', form=form, category=category)

@bp.route('/categories/<int:category_id>/edit_subcategory/<int:subcategory_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_subcategory(category_id, subcategory_id):
    """Edits an existing subcategory."""
    category = Category.query.get_or_404(category_id)
    subcategory = Subcategory.query.filter_by(id=subcategory_id, category_id=category_id).first_or_404()
    form = SubCategoryForm(obj=subcategory)
    if form.validate_on_submit():
        form.populate_obj(subcategory)
        subcategory.slug = slugify(subcategory.name)
        try:
            db.session.commit()
            flash('Subcategory updated successfully!', 'success')
            return redirect(url_for('admin.admin_categories'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: A subcategory with this name already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating subcategory: {e}', 'danger')
    return render_template('admin/admin_add_edit_subcategory.html', form=form, category=category, subcategory=subcategory)

@bp.route('/categories/<int:category_id>/delete_subcategory/<int:subcategory_id>', methods=['POST'])
@admin_required
def admin_delete_subcategory(category_id, subcategory_id):
    """Deletes a subcategory."""
    subcategory = Subcategory.query.filter_by(id=subcategory_id, category_id=category_id).first_or_404()
    try:
        db.session.delete(subcategory)
        db.session.commit()
        flash('Subcategory deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting subcategory: {e}', 'danger')
    return redirect(url_for('admin.admin_categories'))

# --- Article Management ---
@bp.route('/articles')
@admin_required
def admin_articles():
    """Displays a list of all articles."""
    articles = Article.query.order_by(Article.date.desc()).all()
    return render_template('admin/admin_articles.html', articles=articles)

@bp.route('/articles/add', methods=['GET', 'POST'])
@admin_required
def admin_add_article():
    """Adds a new article."""
    form = ArticleForm()
    if form.validate_on_submit():
        new_article = Article(
            title=form.title.data,
            slug=slugify(form.title.data),
            content=form.content.data,
            author=form.author.data,
            date=datetime.now(timezone.utc),
            image=form.image.data
        )
        try:
            db.session.add(new_article)
            db.session.commit()
            flash('Article added successfully!', 'success')
            return redirect(url_for('admin.admin_articles'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: An article with this title already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding article: {e}', 'danger')
    return render_template('admin/admin_add_edit_article.html', form=form)

@bp.route('/articles/edit/<int:article_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_article(article_id):
    """Edits an existing article."""
    article = Article.query.get_or_404(article_id)
    form = ArticleForm(obj=article)
    if form.validate_on_submit():
        form.populate_obj(article)
        article.slug = slugify(article.title)
        try:
            db.session.commit()
            flash('Article updated successfully!', 'success')
            return redirect(url_for('admin.admin_articles'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: An article with this title already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating article: {e}', 'danger')
    return render_template('admin/admin_add_edit_article.html', form=form, article=article)

@bp.route('/articles/delete/<int:article_id>', methods=['POST'])
@admin_required
def admin_delete_article(article_id):
    """Deletes an article."""
    article = Article.query.get_or_404(article_id)
    try:
        db.session.delete(article)
        db.session.commit()
        flash('Article deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting article: {e}', 'danger')
    return redirect(url_for('admin.admin_articles'))

# --- API Synchronization ---
@bp.route('/api_products')
@admin_required
def admin_api_products():
    """Displays the API synchronization status."""
    sync_info = SyncInfo.query.first()
    if not sync_info:
        sync_info = SyncInfo(last_sync_time=datetime.now(timezone.utc), last_sync_count=0, last_synced_api_url="N/A")
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
    """Triggers the API product synchronization."""
    form = ApiSyncForm()
    if form.validate_on_submit():
        api_url = form.api_url.data
        try:
            updated_count = fetch_and_update_products_from_external_api(api_url)
            sync_info = SyncInfo.query.first()
            if not sync_info:
                sync_info = SyncInfo(last_sync_time=datetime.now(timezone.utc), last_sync_count=updated_count, last_synced_api_url=api_url)
                db.session.add(sync_info)
            else:
                sync_info.last_sync_time = datetime.now(timezone.utc)
                sync_info.last_sync_count = updated_count
                sync_info.last_synced_api_url = api_url
            db.session.commit()
            flash(f'API sync complete. {updated_count} products were updated/added.', 'success')
        except Exception as e:
            flash(f'Error during API sync: {str(e)}', 'danger')
            db.session.rollback()
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('admin.admin_api_products'))

# --- Social Media Links Management ---
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

@bp.route('/social_media')
@admin_required
def admin_social_media():
    """Displays all social media links."""
    social_media_links = SocialMediaLink.query.order_by(SocialMediaLink.order_num).all()
    return render_template('admin/admin_social_media.html', social_media_links=social_media_links)

@bp.route('/social_media/add', methods=['GET', 'POST'])
@admin_required
def admin_add_social_media():
    """Adds a new social media link."""
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
            flash('Error: A link for this platform already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding link: {e}', 'danger')
    return render_template('admin/admin_add_edit_social_media.html', form=form)

@bp.route('/social_media/edit/<int:link_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_social_media(link_id):
    """Edits an existing social media link."""
    link = SocialMediaLink.query.get_or_404(link_id)
    form = SocialMediaForm(obj=link)

    if form.validate_on_submit():
        platform_name = form.platform.data
        link.icon_class = PLATFORM_ICONS.get(platform_name, 'fas fa-link')
        form.populate_obj(link)
        try:
            db.session.commit()
            flash('Social media link updated successfully!', 'success')
            return redirect(url_for('admin.admin_social_media'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: A link for this platform already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating link: {e}', 'danger')
    return render_template('admin/admin_add_edit_social_media.html', form=form, link=link)

@bp.route('/social_media/delete/<int:link_id>', methods=['POST'])
@admin_required
def admin_delete_social_media(link_id):
    """Deletes a social media link."""
    link = SocialMediaLink.query.get_or_404(link_id)
    try:
        db.session.delete(link)
        db.session.commit()
        flash('Social media link deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting link: {e}', 'danger')
    return redirect(url_for('admin.admin_social_media'))

# --- Contact Messages Management ---
@bp.route('/messages')
@admin_required
def admin_messages():
    """Displays all contact messages."""
    messages = ContactMessage.query.order_by(ContactMessage.timestamp.desc()).all()
    return render_template('admin/admin_messages.html', messages=messages)

@bp.route('/messages/view/<int:message_id>', methods=['GET', 'POST'])
@admin_required
def admin_view_message(message_id):
    """Views and manages a single contact message."""
    message = ContactMessage.query.get_or_404(message_id)
    
    # La lógica para marcar el mensaje como leído se ha mantenido
    if not message.is_read:
        message.is_read = True
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error marking message as read: {e}', 'danger')
    
    return render_template('admin/admin_view_message.html', message=message)


@bp.route('/messages/delete/<int:message_id>', methods=['POST'])
@admin_required
def admin_delete_message(message_id):
    """Deletes a contact message permanently."""
    message = ContactMessage.query.get_or_404(message_id)
    try:
        db.session.delete(message)
        db.session.commit()
        flash('Message permanently deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting message: {e}', 'danger')
    return redirect(url_for('admin.admin_messages'))

@bp.route('/messages/toggle_archive/<int:message_id>', methods=['POST'])
@admin_required
def admin_toggle_archive_message(message_id):
    """Toggles the archived status of a message."""
    message = ContactMessage.query.get_or_404(message_id)
    message.is_archived = not message.is_archived
    try:
        db.session.commit()
        status = "archived" if message.is_archived else "unarchived"
        flash(f'Message successfully {status}.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating archive status: {e}', 'danger')
    return redirect(url_for('admin.admin_messages'))

# --- Testimonial Management ---
@bp.route('/testimonials')
@admin_required
def admin_testimonials():
    """Displays all testimonials."""
    testimonials = Testimonial.query.order_by(Testimonial.date_posted.desc()).all()
    return render_template('admin/admin_testimonials.html', testimonials=testimonials)

@bp.route('/testimonials/add', methods=['GET', 'POST'])
@admin_required
def admin_add_testimonial():
    """Adds a new testimonial."""
    form = TestimonialForm()
    if form.validate_on_submit():
        new_testimonial = Testimonial(
            author=form.author.data,
            content=form.content.data,
            is_visible=form.is_visible.data,
            date_posted=datetime.now(timezone.utc)
        )
        try:
            db.session.add(new_testimonial)
            db.session.commit()
            flash('Testimonial added successfully!', 'success')
            return redirect(url_for('admin.admin_testimonials'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding testimonial: {e}', 'danger')
    return render_template('admin/admin_add_edit_testimonial.html', form=form)

@bp.route('/testimonials/edit/<int:testimonial_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_testimonial(testimonial_id):
    """Edits an existing testimonial."""
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    form = TestimonialForm(obj=testimonial)

    if form.validate_on_submit():
        form.populate_obj(testimonial)
        try:
            db.session.commit()
            flash('Testimonial updated successfully!', 'success')
            return redirect(url_for('admin.admin_testimonials'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating testimonial: {e}', 'danger')
    return render_template('admin/admin_add_edit_testimonial.html', form=form, testimonial=testimonial)

@bp.route('/testimonials/delete/<int:testimonial_id>', methods=['POST'])
@admin_required
def admin_delete_testimonial(testimonial_id):
    """Deletes a testimonial."""
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    try:
        db.session.delete(testimonial)
        db.session.commit()
        flash('Testimonial deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting testimonial: {e}', 'danger')
    return redirect(url_for('admin.admin_testimonials'))

@bp.route('/testimonials/toggle_visibility/<int:testimonial_id>', methods=['POST'])
@admin_required
def admin_toggle_visibility_testimonial(testimonial_id):
    """Toggles the visibility of a testimonial."""
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    testimonial.is_visible = not testimonial.is_visible
    try:
        db.session.commit()
        status = "visible" if testimonial.is_visible else "hidden"
        flash(f'Testimonial marked as {status}.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating visibility status: {e}', 'danger')
    return redirect(url_for('admin.admin_testimonials'))

# --- Advertisement Management ---
# --- Affiliate Management ---
@bp.route('/affiliates')
@admin_required
def admin_affiliates():
    """Displays a list of all affiliates."""
    affiliates = Affiliate.query.all()
    return render_template('admin/admin_affiliates.html', affiliates=affiliates)

@bp.route('/affiliates/add', methods=['GET', 'POST'])
@admin_required
def admin_add_affiliate():
    """Adds a new affiliate."""
    form = AffiliateForm()
    if form.validate_on_submit():
        new_affiliate = Affiliate(
            name=form.name.data,
            referral_link=form.referral_link.data,
            email=form.email.data
        )
        try:
            db.session.add(new_affiliate)
            db.session.commit()
            flash('Affiliate added successfully!', 'success')
            return redirect(url_for('admin.admin_affiliates'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: An affiliate with this email or referral link already exists.', 'danger')
    return render_template('admin/admin_add_edit_affiliate.html', form=form)

@bp.route('/affiliates/edit/<int:affiliate_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_affiliate(affiliate_id):
    """Edits an existing affiliate."""
    affiliate = Affiliate.query.get_or_404(affiliate_id)
    form = AffiliateForm(obj=affiliate)
    if form.validate_on_submit():
        form.populate_obj(affiliate)
        try:
            db.session.commit()
            flash('Affiliate updated successfully!', 'success')
            return redirect(url_for('admin.admin_affiliates'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: An affiliate with this email or referral link already exists.', 'danger')
    return render_template('admin/admin_add_edit_affiliate.html', form=form, affiliate=affiliate)

@bp.route('/affiliates/delete/<int:affiliate_id>', methods=['POST'])
@admin_required
def admin_delete_affiliate(affiliate_id):
    """Deletes an affiliate."""
    affiliate = Affiliate.query.get_or_404(affiliate_id)
    try:
        db.session.delete(affiliate)
        db.session.commit()
        flash('Affiliate deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting affiliate: {e}', 'danger')
    return redirect(url_for('admin.admin_affiliates'))

# --- Affiliate Statistics Management ---
@bp.route('/affiliate_statistics')
@admin_required
def admin_affiliate_statistics():
    """Displays a list of all affiliate statistics."""
    statistics = AffiliateStatistic.query.options(joinedload(AffiliateStatistic.affiliate)).order_by(AffiliateStatistic.timestamp.desc()).all()
    return render_template('admin/admin_affiliate_statistics.html', statistics=statistics)


# --- Adsense Configuration Management ---
@bp.route('/adsense_config', methods=['GET', 'POST'])
@admin_required
def admin_adsense_config():
    """Handles the configuration for AdSense."""
    config = AdsenseConfig.query.first()
    if not config:
        config = AdsenseConfig()
        db.session.add(config)
        db.session.commit()
    form = AdsenseConfigForm(obj=config)
    if form.validate_on_submit():
        form.populate_obj(config)
        try:
            db.session.commit()
            flash('AdSense configuration updated successfully!', 'success')
            return redirect(url_for('admin.admin_adsense_config'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating AdSense configuration: {e}', 'danger')
    return render_template('admin/admin_adsense_config.html', form=form)