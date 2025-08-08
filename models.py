from extensions import db
from flask_login import UserMixin
from datetime import datetime, timezone, date
from werkzeug.security import generate_password_hash, check_password_hash


# --- Modelos de la aplicación ---
class User(UserMixin, db.Model):
    """Modelo para representar a los usuarios."""
    __tablename__ = 'users'  # nombre en plural para evitar palabra reservada
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """Genera un hash seguro para la contraseña."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica si la contraseña es correcta."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Categoria(db.Model):
    """Modelo para las categorías de productos."""
    __tablename__ = 'categoria'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    subcategorias = db.relationship('Subcategoria', backref='categoria', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Categoria {self.nombre}>'


class Subcategoria(db.Model):
    """Modelo para las subcategorías de productos."""
    __tablename__ = 'subcategoria'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    productos = db.relationship('Producto', backref='subcategoria', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Subcategoria {self.nombre}>'


class Producto(db.Model):
    """Modelo para los productos afiliados."""
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    imagen = db.Column(db.String(255), nullable=True)
    link = db.Column(db.String(255), nullable=False)
    subcategoria_id = db.Column(db.Integer, db.ForeignKey('subcategoria.id'), nullable=True)
    external_id = db.Column(db.String(100), unique=True, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Producto {self.nombre}>'


class Articulo(db.Model):
    """Modelo para los artículos del blog."""
    __tablename__ = 'articulo'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    imagen = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Articulo {self.titulo}>'


class SyncInfo(db.Model):
    """Modelo para guardar la información de la última sincronización."""
    __tablename__ = 'sync_info'
    id = db.Column(db.Integer, primary_key=True)
    last_sync_time = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    last_sync_count = db.Column(db.Integer, nullable=False)
    last_synced_api_url = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<SyncInfo {self.last_sync_time}>'


class SocialMediaLink(db.Model):
    """Modelo para los enlaces a redes sociales."""
    __tablename__ = 'social_media_link'
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), unique=True, nullable=False)
    url = db.Column(db.String(255), nullable=False)
    icon_class = db.Column(db.String(100), nullable=True)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    order_num = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<SocialMediaLink {self.platform}>'


class ContactMessage(db.Model):
    """Modelo para los mensajes de contacto recibidos."""
    __tablename__ = 'contact_message'
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


class Testimonial(db.Model):
    """Modelo para los testimonios de usuarios."""
    __tablename__ = 'testimonial'
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    is_visible = db.Column(db.Boolean, default=False)
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Testimonial {self.author}>'


class Advertisement(db.Model):
    """Modelo para los anuncios gestionados por el administrador."""
    __tablename__ = 'advertisement'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    text_content = db.Column(db.Text, nullable=True)
    button_text = db.Column(db.String(100), nullable=True)
    button_url = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=True)
    product = db.relationship('Producto')
    adsense_client_id = db.Column(db.String(100), nullable=True)
    adsense_slot_id = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Advertisement {self.title} ({self.type})>'


class Afiliado(db.Model):
    """Modelo para los afiliados del sitio."""
    __tablename__ = 'afiliados'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    enlace_referido = db.Column(db.String(255), unique=True, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Afiliado {self.nombre}>'


class EstadisticaAfiliado(db.Model):
    """Modelo para las estadísticas de los afiliados."""
    __tablename__ = 'estadisticas_afiliados'
    id = db.Column(db.Integer, primary_key=True)
    afiliado_id = db.Column(db.Integer, db.ForeignKey('afiliados.id'), nullable=False)
    fecha = db.Column(db.Date, default=date.today)
    clics = db.Column(db.Integer, default=0)
    registros = db.Column(db.Integer, default=0)
    ventas = db.Column(db.Integer, default=0)
    comision_generada = db.Column(db.Float, default=0.0)
    pagado = db.Column(db.Boolean, default=False)

    afiliado = db.relationship('Afiliado', backref='estadisticas', lazy=True)

    def __repr__(self):
        return f'<EstadisticaAfiliado Afiliado: {self.afiliado_id}, Fecha: {self.fecha}>'


class AdsenseConfig(db.Model):
    """Modelo para la configuración de AdSense."""
    __tablename__ = 'adsense_config'
    id = db.Column(db.Integer, primary_key=True)
    adsense_client_id = db.Column(db.String(100), nullable=False)
    adsense_slot_1 = db.Column(db.String(50), nullable=True)
    adsense_slot_2 = db.Column(db.String(50), nullable=True)
    adsense_slot_3 = db.Column(db.String(50), nullable=True)
    estado = db.Column(db.String(20), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def __repr__(self):
        return f"<AdsenseConfig {self.adsense_client_id}>"
