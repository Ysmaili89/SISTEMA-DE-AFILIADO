from extensions import db
from flask_login import UserMixin
from datetime import datetime, timezone, date
from werkzeug.security import generate_password_hash, check_password_hash


# --- Application Models ---
class User(UserMixin, db.Model):
    """Model to represent users."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """Generates a secure hash for the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies if the password is correct."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# ---
class Category(db.Model):
    """Model for product categories."""
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    subcategories = db.relationship('Subcategory', backref='category', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Category {self.name}>'

# ---
class Subcategory(db.Model):
    """Model for product subcategories."""
    __tablename__ = 'subcategories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    products = db.relationship('Product', backref='subcategory', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Subcategory {self.name}>'

# ---
class Product(db.Model):
    """Model for affiliate products."""
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    link = db.Column(db.String(255), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategories.id'), nullable=True)
    external_id = db.Column(db.String(100), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Product {self.name}>'

# ---
class Article(db.Model):
    """Model for blog articles."""
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    image = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Article {self.title}>'

# ---
class SyncInfo(db.Model):
    """Model to store the last sync information."""
    __tablename__ = 'sync_info'
    id = db.Column(db.Integer, primary_key=True)
    last_sync_time = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    last_sync_count = db.Column(db.Integer, nullable=False)
    last_synced_api_url = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<SyncInfo {self.last_sync_time}>'

# ---
class SocialMediaLink(db.Model):
    """Model for social media links."""
    __tablename__ = 'social_media_links'
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), unique=True, nullable=False)
    url = db.Column(db.String(255), nullable=False)
    icon_class = db.Column(db.String(100), nullable=True)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    order_num = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<SocialMediaLink {self.platform}>'

# ---
class ContactMessage(db.Model):
    """Model for received contact messages."""
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    is_read = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    response_text = db.Column(db.Text, nullable=True)
    response_timestamp = db.Column(db.DateTime, nullable=True)
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<ContactMessage {self.email} - {self.subject}>'

# ---
class Testimonial(db.Model):
    """Model for user testimonials."""
    __tablename__ = 'testimonials'
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    is_visible = db.Column(db.Boolean, default=False)
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Testimonial {self.author}>'

# ---
class Advertisement(db.Model):
    """Model for advertisements managed by the administrator."""
    __tablename__ = 'advertisements'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    text_content = db.Column(db.Text, nullable=True)
    button_text = db.Column(db.String(100), nullable=True)
    button_url = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    product = db.relationship('Product')
    adsense_client_id = db.Column(db.String(100), nullable=True)
    adsense_slot_id = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Advertisement {self.title} ({self.type})>'

# ---
class Affiliate(db.Model):
    """Model for site affiliates."""
    __tablename__ = 'affiliates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    referral_link = db.Column(db.String(255), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Affiliate {self.name}>'

# ---
class AffiliateStatistic(db.Model):
    """Model for affiliate statistics."""
    __tablename__ = 'affiliate_statistics'
    id = db.Column(db.Integer, primary_key=True)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliates.id'), nullable=False)
    date = db.Column(db.Date, default=date.today)
    clicks = db.Column(db.Integer, default=0)
    registrations = db.Column(db.Integer, default=0)
    sales = db.Column(db.Integer, default=0)
    commission_generated = db.Column(db.Float, default=0.0)
    is_paid = db.Column(db.Boolean, default=False)

    affiliate = db.relationship('Affiliate', backref='statistics', lazy=True)

    def __repr__(self):
        return f'<AffiliateStatistic Affiliate: {self.affiliate_id}, Date: {self.date}>'

# ---
class AdsenseConfig(db.Model):
    """Modelo para la configuración de AdSense."""
    __tablename__ = 'adsense_configs'
    id = db.Column(db.Integer, primary_key=True)
    adsense_client_id = db.Column(db.String(100), nullable=False)
    adsense_slot_header = db.Column(db.String(50), nullable=True)
    adsense_slot_sidebar = db.Column(db.String(50), nullable=True)
    adsense_slot_article_top = db.Column(db.String(50), nullable=True)
    adsense_slot_article_bottom = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def __repr__(self):
        return f"<AdsenseConfig {self.adsense_client_id}>"