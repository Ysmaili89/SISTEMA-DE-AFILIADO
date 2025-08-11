# forms.py

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, FloatField, SelectField,
    SubmitField, PasswordField, BooleanField, DateTimeLocalField
)
from wtforms.validators import (
    DataRequired, URL, NumberRange, Optional, Length, ValidationError, Email
)
from wtforms_sqlalchemy.fields import QuerySelectField
from models import Product, Affiliate, Category, Subcategory


def validate_image_path(form, field):
    """
    Validates that the image URL is a web path or a valid local path.
    """
    if field.data and not (
        field.data.startswith(('http://', 'https://', '/', 'static/'))
    ):
        raise ValidationError('Image URL must start with http://, https://, / or be a valid path (e.g., /static/img/ or static/uploads/...).')


# --- Application Forms ---
class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class ProductForm(FlaskForm):
    """Form for creating and editing products."""
    name = StringField('Product Name', validators=[DataRequired(), Length(min=2, max=200)])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0.01, message='Price must be a positive number.')])
    description = TextAreaField('Description', validators=[Optional()])
    image = StringField('Image URL', validators=[Optional(), validate_image_path])
    link = StringField('Affiliate Link', validators=[DataRequired(), URL(message='Please enter a valid URL.')])
    subcategory = QuerySelectField(
        'Subcategory',
        query_factory=lambda: Subcategory.query.order_by(Subcategory.name).all(),
        get_pk=lambda a: a.id,
        get_label=lambda a: a.name,
        allow_blank=True,
        blank_text='-- Select a Subcategory --',
        validators=[Optional()]
    )
    external_id = StringField('External ID (Optional)', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Save Product')


class CategoryForm(FlaskForm):
    """Form for creating and editing categories."""
    name = StringField('Category Name', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Save Category')


class SubCategoryForm(FlaskForm):
    """Form for creating and editing subcategories."""
    name = StringField('Subcategory Name', validators=[DataRequired(), Length(min=2, max=100)])
    category = QuerySelectField(
        'Category',
        query_factory=lambda: Category.query.order_by(Category.name).all(),
        get_pk=lambda a: a.id,
        get_label=lambda a: a.name,
        validators=[DataRequired(message='Please select a category.')]
    )
    submit = SubmitField('Save Subcategory')


class ArticleForm(FlaskForm):
    """Form for creating and editing articles."""
    title = StringField('Article Title', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('Article Content', validators=[DataRequired()])
    author = StringField('Author', validators=[Optional(), Length(max=100)])
    image = StringField('Image URL (Optional)', validators=[Optional(), validate_image_path])
    submit = SubmitField('Save Article')


class ApiSyncForm(FlaskForm):
    """Form for syncing external products."""
    api_url = StringField('External API URL', validators=[DataRequired(), URL(message='Please enter a valid API URL.')])
    submit = SubmitField('Sync Products')


class SocialMediaForm(FlaskForm):
    """Form for managing social media links."""
    platform = SelectField('Platform', choices=[
        ('Facebook', 'Facebook'), ('Twitter', 'X (Twitter)'), ('Instagram', 'Instagram'),
        ('LinkedIn', 'LinkedIn'), ('YouTube', 'YouTube'), ('TikTok', 'TikTok'),
        ('WhatsApp', 'WhatsApp'), ('Telegram', 'Telegram'), ('Pinterest', 'Pinterest'),
        ('Snapchat', 'Snapchat'), ('Discord', 'Discord'), ('Reddit', 'Reddit'), ('Other', 'Other')
    ], validators=[DataRequired()])
    url = StringField('Profile URL', validators=[DataRequired(), URL()])
    is_visible = BooleanField('Visible on Public Site', default=True)
    submit = SubmitField('Save Link')


class ContactMessageAdminForm(FlaskForm):
    """Form for responding to and managing contact messages."""
    response_text = TextAreaField('Respond to Message', validators=[Optional()])
    is_read = BooleanField('Mark as Read', default=False)
    is_archived = BooleanField('Archive Message', default=False)
    submit_response = SubmitField('Send Response and Update')


class TestimonialForm(FlaskForm):
    """Form for managing testimonials by the administrator."""
    author = StringField('Testimonial Author', validators=[DataRequired(), Length(min=2, max=100)])
    content = TextAreaField('Testimonial Content', validators=[DataRequired()])
    is_visible = BooleanField('Visible on Public Site', default=False)
    likes = StringField('Likes (Read-only)', render_kw={'readonly': True})
    dislikes = StringField('Dislikes (Read-only)', render_kw={'readonly': True})
    submit = SubmitField('Save Testimonial')


class PublicTestimonialForm(FlaskForm):
    """Form for users to submit a testimonial."""
    author = StringField('Your Name', validators=[DataRequired(), Length(min=2, max=100)])
    content = TextAreaField('Your Testimonial', validators=[DataRequired(), Length(min=10, max=500)], render_kw={"rows": 5})
    fax_number = StringField('Fax Number (do not fill in)', validators=[Optional()])
    submit = SubmitField('Send Testimonial')


class AdvertisementForm(FlaskForm):
    """Form for creating and editing advertisements."""
    AD_TYPE_CHOICES = [
        ('featured', 'Featured (Text/Button)'),
        ('recommended', 'Recommended Product'),
        ('best_seller', 'Best Seller (Text/Button)'),
        ('sponsored', 'Sponsored (AdSense)'),
        ('relevant', 'Relevant (AdSense)')
    ]

    type = SelectField('Ad Type', choices=AD_TYPE_CHOICES, validators=[DataRequired()])
    title = StringField('Ad Title', validators=[DataRequired(), Length(max=200)])
    is_active = BooleanField('Active', default=True)

    text_content = TextAreaField('Text Content', validators=[Optional()])
    button_text = StringField('Button Text', validators=[Optional(), Length(max=100)])
    button_url = StringField('Button URL', validators=[Optional(), URL()])

    product = QuerySelectField(
        'Recommended Product',
        query_factory=lambda: Product.query.order_by(Product.name).all(),
        get_pk=lambda a: a.id,
        get_label=lambda a: a.name,
        allow_blank=True,
        blank_text='-- Select a Product --',
        validators=[Optional()]
    )
    image_url = StringField('Image URL (Recommended Product)', validators=[Optional(), validate_image_path])

    adsense_client_id = StringField('AdSense Client ID (ca-pub-XXXXXXXXXXXXXX)', validators=[Optional(), Length(max=50)])
    adsense_slot_id = StringField('AdSense Slot ID (9999999999)', validators=[Optional(), Length(max=50)])

    start_date = DateTimeLocalField('Start Date (Optional)', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    end_date = DateTimeLocalField('End Date (Optional)', format='%Y-%m-%dT%H:%M', validators=[Optional()])

    submit = SubmitField('Save Advertisement')

    def validate(self):
        if not super().validate():
            return False

        if self.type.data == 'recommended':
            if not self.product.data and not self.image_url.data:
                msg = 'You must select a product or provide an image URL.'
                self.product.errors.append(msg)
                self.image_url.errors.append(msg)
                return False
        elif self.type.data in ['featured', 'best_seller']:
            if not (self.text_content.data or self.button_text.data or self.button_url.data):
                self.text_content.errors.append('For this ad type, text content, button text, or button URL is required.')
                return False
        elif self.type.data in ['sponsored', 'relevant']:
            if not self.adsense_client_id.data or not self.adsense_slot_id.data:
                msg = 'AdSense Client ID and Slot ID are required for this ad type.'
                self.adsense_client_id.errors.append(msg)
                self.adsense_slot_id.errors.append(msg)
                return False

        if self.start_date.data and self.end_date.data and self.start_date.data >= self.end_date.data:
            self.end_date.errors.append('End date must be after the start date.')
            return False

        return True


# --- Affiliate Forms (Moved from admin.py) ---
class AffiliateForm(FlaskForm):
    """Form for creating and editing affiliates."""
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Length(max=120), Email()])
    referral_link = StringField('Referral Link', validators=[DataRequired(), URL()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Affiliate')


class AffiliateStatisticForm(FlaskForm):
    """Form for generating affiliate statistics reports."""
    start_date = DateTimeLocalField('Start Date', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    end_date = DateTimeLocalField('End Date', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    affiliate = QuerySelectField(
        'Affiliate',
        query_factory=lambda: Affiliate.query.order_by(Affiliate.name).all(),
        get_pk=lambda a: a.id,
        get_label=lambda a: a.name,
        allow_blank=True,
        blank_text='-- All Affiliates --',
        validators=[Optional()]
    )
    submit = SubmitField('Generate Report')


class AdsenseConfigForm(FlaskForm):
    """Form for AdSense configuration."""
    client_id = StringField('AdSense Client ID (data-ad-client)', validators=[DataRequired(), Length(max=50)])
    ad_slot_header = StringField('Header Ad Slot ID', validators=[Optional(), Length(max=50)])
    ad_slot_sidebar = StringField('Sidebar Ad Slot ID', validators=[Optional(), Length(max=50)])
    ad_slot_article_top = StringField('Article Top Ad Slot ID', validators=[Optional(), Length(max=50)])
    ad_slot_article_bottom = StringField('Article Bottom Ad Slot ID', validators=[Optional(), Length(max=50)])
    is_active = BooleanField('Activate AdSense', default=False)
    submit = SubmitField('Save AdSense Configuration')