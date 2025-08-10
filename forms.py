# forms.py - Formularios de la aplicación de afiliados

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, FloatField, SelectField,
    SubmitField, PasswordField, BooleanField, DateTimeLocalField
)
from wtforms.validators import (
    DataRequired, URL, NumberRange, Optional, Length, ValidationError, Email
)
from wtforms_sqlalchemy.fields import QuerySelectField

# Importa los modelos necesarios para los QuerySelectField
from models import Product, Subcategory, Category, Affiliate

# Validador personalizado para rutas relativas o URL completas
def validate_image_path(form, field):
    """
    Valida que la URL de la imagen sea una ruta web o una ruta local válida.
    """
    if field.data and not (
        field.data.startswith(('http://', 'https://', '/', 'static/'))
    ):
        raise ValidationError('La URL de la imagen debe comenzar con http://, https://, /, o ser una ruta válida (ej. /static/img/ o static/uploads/...).')

# --- Formularios de solicitud ---

class LoginForm(FlaskForm):
    """Formulario para el inicio de sesión del usuario."""
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class ProductForm(FlaskForm):
    """Formulario para crear y editar productos."""
    name = StringField('Nombre del Producto', validators=[DataRequired(), Length(min=2, max=200)])
    price = FloatField('Precio', validators=[DataRequired(), NumberRange(min=0.01, message='El precio debe ser un número positivo.')])
    description = TextAreaField('Descripción', validators=[Optional()])
    image = StringField('URL de la Imagen', validators=[Optional(), validate_image_path])
    link = StringField('Enlace de Afiliado', validators=[DataRequired(), URL(message='Por favor, introduce una URL válida.')])
    
    # Se usa 'Subcategory' y 'name' en lugar de 'Subcategoría' y 'nombre' para consistencia
    subcategory = QuerySelectField(
        'Subcategoría',
        query_factory=lambda: Subcategory.query.order_by(Subcategory.name).all(),
        get_pk=lambda a: a.id,
        get_label=lambda a: a.name,
        allow_blank=True,
        blank_text='-- Selecciona una Subcategoría --',
        validators=[Optional()]
    )
    external_id = StringField('ID Externo (Opcional)', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Guardar Producto')

class CategoryForm(FlaskForm):
    """Formulario para crear y editar categorías."""
    name = StringField('Nombre de la Categoría', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Guardar Categoría')

class SubCategoryForm(FlaskForm):
    """Formulario para crear y editar subcategorías."""
    name = StringField('Nombre de la Subcategoría', validators=[DataRequired(), Length(min=2, max=100)])
    
    # Se usa 'Category' y 'name' para consistencia
    category = QuerySelectField(
        'Categoría',
        query_factory=lambda: Category.query.order_by(Category.name).all(),
        get_pk=lambda a: a.id,
        get_label=lambda a: a.name,
        validators=[DataRequired(message='Por favor, selecciona una categoría.')]
    )
    submit = SubmitField('Guardar Subcategoría')

class ArticleForm(FlaskForm):
    """Formulario para crear y editar artículos."""
    title = StringField('Título del Artículo', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('Contenido del Artículo', validators=[DataRequired()])
    author = StringField('Autor', validators=[Optional(), Length(max=100)])
    image = StringField('URL de la Imagen (Opcional)', validators=[Optional(), validate_image_path])
    submit = SubmitField('Guardar Artículo')

class ApiSyncForm(FlaskForm):
    """Formulario para sincronizar productos externos."""
    api_url = StringField('URL de la API Externa', validators=[DataRequired(), URL(message='Por favor, introduce una URL válida para la API.')])
    submit = SubmitField('Sincronizar Productos')

class SocialMediaForm(FlaskForm):
    """Formulario para gestionar enlaces a redes sociales."""
    platform = SelectField('Plataforma', choices=[
        ('Facebook', 'Facebook'), ('Twitter', 'X (Twitter)'), ('Instagram', 'Instagram'),
        ('LinkedIn', 'LinkedIn'), ('YouTube', 'YouTube'), ('TikTok', 'TikTok'),
        ('WhatsApp', 'WhatsApp'), ('Telegram', 'Telegram'), ('Pinterest', 'Pinterest'),
        ('Snapchat', 'Snapchat'), ('Discord', 'Discord'), ('Reddit', 'Reddit'), ('Otro', 'Otro')
    ], validators=[DataRequired()])
    url = StringField('URL del Perfil', validators=[DataRequired(), URL()])
    is_visible = BooleanField('Visible en el Sitio Público', default=True)
    submit = SubmitField('Guardar Enlace')

class ContactMessageAdminForm(FlaskForm):
    """Formulario para responder y gestionar mensajes de contacto."""
    response_text = TextAreaField('Responder Mensaje', validators=[Optional()])
    is_read = BooleanField('Marcar como leído', default=False)
    is_archived = BooleanField('Archivar Mensaje', default=False)
    submit_response = SubmitField('Enviar Respuesta y Actualizar')

class TestimonialForm(FlaskForm):
    """Formulario para gestionar testimonios por el administrador."""
    author = StringField('Autor del Testimonio', validators=[DataRequired(), Length(min=2, max=100)])
    content = TextAreaField('Contenido del Testimonio', validators=[DataRequired()])
    is_visible = BooleanField('Visible en el Sitio Público', default=False)
    likes = StringField('Me gusta (solo lectura)', render_kw={'readonly': True})
    dislikes = StringField('Dislikes (solo lectura)', render_kw={'readonly': True})
    submit = SubmitField('Guardar Testimonio')

class PublicTestimonialForm(FlaskForm):
    """Formulario para que los usuarios envíen un testimonio."""
    author = StringField('Tu Nombre', validators=[DataRequired(), Length(min=2, max=100)])
    content = TextAreaField('Tu Testimonio', validators=[DataRequired(), Length(min=10, max=500)], render_kw={"rows": 5})
    # Este es un campo "honeypot" para evitar spam de bots. No debe ser visible.
    fax_number = StringField('Número de Fax (no rellenar)', validators=[Optional()])
    submit = SubmitField('Enviar Testimonio')

class AdvertisementForm(FlaskForm):
    """Formulario para crear y editar anuncios."""
    AD_TYPE_CHOICES = [
        ('destacado', 'Destacado (Texto/Botón)'),
        ('recomendado', 'Producto Recomendado'),
        ('mas_vendido', 'Lo más vendido (Texto/Botón)'),
        ('patrocinado', 'Patrocinado (AdSense)'),
        ('relevante', 'Relevante (AdSense)')
    ]

    type = SelectField('Tipo de Anuncio', choices=AD_TYPE_CHOICES, validators=[DataRequired()])
    title = StringField('Título del Anuncio', validators=[DataRequired(), Length(max=200)])
    is_active = BooleanField('Activo', default=True)

    text_content = TextAreaField('Contenido de Texto', validators=[Optional()])
    button_text = StringField('Texto del Botón', validators=[Optional(), Length(max=100)])
    button_url = StringField('URL del Botón', validators=[Optional(), URL()])

    # Se usa 'Product' y 'name' para consistencia
    product = QuerySelectField(
        'Producto Recomendado',
        query_factory=lambda: Product.query.order_by(Product.name).all(),
        get_pk=lambda a: a.id,
        get_label=lambda a: a.name,
        allow_blank=True,
        blank_text='-- Selecciona un Producto --',
        validators=[Optional()]
    )
    image_url = StringField('URL de la Imagen (Producto Recomendado)', validators=[Optional(), validate_image_path])

    adsense_client_id = StringField('ID de Cliente AdSense (ca-pub-XXXXXXXXXXXXXX)', validators=[Optional(), Length(max=50)])
    adsense_slot_id = StringField('ID de Slot AdSense (9999999999)', validators=[Optional(), Length(max=50)])

    start_date = DateTimeLocalField('Fecha de Inicio (Opcional)', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    end_date = DateTimeLocalField('Fecha de Fin (Opcional)', format='%Y-%m-%dT%H:%M', validators=[Optional()])

    submit = SubmitField('Guardar Anuncio')

    def validate(self):
        if not super().validate():
            return False

        if self.type.data == 'recomendado':
            if not self.product.data and not self.image_url.data:
                msg = 'Debes seleccionar un producto o proporcionar una URL de imagen.'
                self.product.errors.append(msg)
                self.image_url.errors.append(msg)
                return False
        elif self.type.data in ['destacado', 'mas_vendido']:
            if not (self.text_content.data or self.button_text.data or self.button_url.data):
                self.text_content.errors.append('Para este tipo de anuncio, se requiere contenido de texto, texto del botón o URL del botón.')
                return False
        elif self.type.data in ['patrocinado', 'relevante']:
            if not self.adsense_client_id.data or not self.adsense_slot_id.data:
                msg = 'Se requieren el ID de Cliente y el ID de Slot de AdSense para este tipo de anuncio.'
                self.adsense_client_id.errors.append(msg)
                self.adsense_slot_id.errors.append(msg)
                return False

        if self.start_date.data and self.end_date.data and self.start_date.data >= self.end_date.data:
            self.end_date.errors.append('La fecha de fin debe ser posterior a la fecha de inicio.')
            return False

        return True

# --- Formularios de afiliados (movidos de admin.py) ---

class AffiliateForm(FlaskForm):
    """Formulario para crear y editar afiliados."""
    name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Length(max=120), Email()])
    referral_link = StringField('Enlace de Referido', validators=[DataRequired(), URL()])
    is_active = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar Afiliado')

class AffiliateStatisticForm(FlaskForm):
    """Formulario para generar informes de estadísticas de afiliados."""
    start_date = DateTimeLocalField('Fecha de Inicio', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    end_date = DateTimeLocalField('Fecha de Fin', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    
    # Se usa 'affiliate' y 'Affiliate' para consistencia
    affiliate = QuerySelectField(
        'Afiliado',
        query_factory=lambda: Affiliate.query.order_by(Affiliate.name).all(),
        get_pk=lambda a: a.id,
        get_label=lambda a: a.name,
        allow_blank=True,
        blank_text='-- Todos los Afiliados --',
        validators=[Optional()]
    )
    submit = SubmitField('Generar Reporte')

class AdsenseConfigForm(FlaskForm):
    """Formulario para la configuración de AdSense."""
    client_id = StringField('ID de Cliente AdSense (data-ad-client)', validators=[DataRequired(), Length(max=50)])
    ad_slot_header = StringField('ID de Slot para Encabezado', validators=[Optional(), Length(max=50)])
    ad_slot_sidebar = StringField('ID de Slot para Barra Lateral', validators=[Optional(), Length(max=50)])
    ad_slot_article_top = StringField('ID de Slot para Parte Superior del Artículo', validators=[Optional(), Length(max=50)])
    ad_slot_article_bottom = StringField('ID de Slot para Parte Inferior del Artículo', validators=[Optional(), Length(max=50)])
    is_active = BooleanField('Activar AdSense', default=False)
    submit = SubmitField('Guardar Configuración AdSense')