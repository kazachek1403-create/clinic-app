"""
Формы WTForms для платформы управления клиниками.
Включает валидацию для авторизации, продуктов, пользователей и т.д.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileSize
from wtforms import (
    StringField, PasswordField, SelectField, FloatField, 
    TextAreaField, FileField, IntegerField, DateTimeField, BooleanField
)
from wtforms.validators import (
    DataRequired, Optional, Length, Email, ValidationError, 
    NumberRange, Regexp
)
from models import User, Product
import re


class LoginForm(FlaskForm):
    """Форма входа."""
    username = StringField('Логин', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Пароль', validators=[DataRequired()])


class UserForm(FlaskForm):
    """Форма создания/редактирования пользователя (администратор)."""
    username = StringField('Логин', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Пароль', validators=[Optional(), Length(min=6)])
    role = SelectField('Роль', choices=[('admin', 'Администратор'), ('seller', 'Продавец')], validators=[DataRequired()])
    discount_percent = FloatField('Персональная скидка (%)', validators=[NumberRange(min=0, max=100)])
    
    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user and (not hasattr(self, 'user_id') or user.id != self.user_id):
            raise ValidationError('Логин уже существует.')


class ProductForm(FlaskForm):
    """Форма создания/редактирования продукта."""
    name = StringField('Название продукта', validators=[DataRequired(), Length(min=3, max=255)])
    base_price = FloatField('Базовая цена (руб.)', validators=[DataRequired(), NumberRange(min=0)])
    
    def validate_name(self, field):
        product = Product.query.filter_by(name=field.data).first()
        if product and (not hasattr(self, 'product_id') or product.id != self.product_id):
            raise ValidationError('Продукт с таким названием уже существует.')


class AuthorizationForm(FlaskForm):
    """Форма подачи заявки на авторизацию клиники."""
    product_id = SelectField('Продукт', coerce=int, validators=[DataRequired()])
    inn = StringField('ИНН', validators=[
        DataRequired(),
        Regexp(r'^\d{10}$|^\d{12}$', message='ИНН должен содержать 10 или 12 цифр')
    ])
    contact_name = StringField('ФИО', validators=[DataRequired(), Length(min=3, max=255)])
    contact_phone = StringField('Телефон', validators=[DataRequired(), Length(min=5, max=20)])


class MaterialUploadForm(FlaskForm):
    """Форма загрузки общего материала."""
    title = StringField('Название', validators=[DataRequired(), Length(min=3, max=255)])
    description = TextAreaField('Описание', validators=[Optional()])
    file = FileField('Файл', validators=[
        DataRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png', 'docx', 'xlsx', 'pptx'], 'Допустимые форматы: PDF, JPG, PNG, DOCX, XLSX, PPTX'),
        FileSize(max_size=16*1024*1024, message='Размер файла не должен превышать 16 МБ')
    ])


class DocumentUploadForm(FlaskForm):
    """Форма загрузки персонального документа."""
    seller_id = SelectField('Продавец', coerce=int, validators=[DataRequired()])
    title = StringField('Название', validators=[DataRequired(), Length(min=3, max=255)])
    description = TextAreaField('Описание', validators=[Optional()])
    file = FileField('Файл', validators=[
        DataRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png', 'docx', 'xlsx', 'pptx'], 'Допустимые форматы: PDF, JPG, PNG, DOCX, XLSX, PPTX'),
        FileSize(max_size=16*1024*1024, message='Размер файла не должен превышать 16 МБ')
    ])


class ExchangeRateForm(FlaskForm):
    """Форма редактирования курса валюты."""
    exchange_rate = FloatField('Курс валюты (руб./USD)', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='Курс должен быть положительным числом')
    ])


class EventForm(FlaskForm):
    """Форма создания события календаря продавцом."""
    title = StringField('Название', validators=[DataRequired(), Length(min=3, max=255)])
    event_type = SelectField('Тип события', choices=[
        ('deal_date', 'Сделка'),
        ('presentation_request', 'Презентация'),
        ('promo_support', 'Промо-поддержка'),
        ('event_participation', 'Участие в мероприятии'),
        ('meeting', 'Совещание'),
        ('other', 'Другое')
    ], validators=[DataRequired()])
    start_datetime = DateTimeField('Дата и время начала', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    end_datetime = DateTimeField('Дата и время окончания', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[Optional()])


class EmailSettingsForm(FlaskForm):
    """Форма настройки параметров отправки email."""
    mail_server = StringField('SMTP сервер', validators=[Optional()])
    mail_port = IntegerField('Порт', validators=[Optional(), NumberRange(min=1, max=65535)])
    mail_username = StringField('Логин', validators=[Optional()])
    mail_password = PasswordField('Пароль', validators=[Optional()])
    mail_use_tls = BooleanField('Использовать TLS')
