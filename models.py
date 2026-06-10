"""
Модели данных для платформы управления клиниками.
Включает User, Product, Authorization, Event, Material, PersonalDocument и Setting.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Модель пользователя (администратор или продавец)."""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='seller')
    discount_percent = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    product_assignments = db.relationship('ProductAssignment', backref='user', cascade='all, delete-orphan')
    authorizations = db.relationship('Authorization', backref='seller', cascade='all, delete-orphan')
    personal_documents = db.relationship('PersonalDocument', backref='seller', cascade='all, delete-orphan')
    events_created = db.relationship('Event', backref='creator', foreign_keys='Event.creator_id', cascade='all, delete-orphan')
    events_as_seller = db.relationship('Event', backref='seller_obj', foreign_keys='Event.seller_id', cascade='all, delete-orphan')
    events_approved = db.relationship('Event', backref='approver', foreign_keys='Event.admin_id', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Product(db.Model):
    """Модель продукта (медицинского препарата/услуги)."""
    __tablename__ = 'product'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    base_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    assignments = db.relationship('ProductAssignment', backref='product', cascade='all, delete-orphan')
    authorizations = db.relationship('Authorization', backref='product', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.name} ({self.base_price} руб.)>'


class ProductAssignment(db.Model):
    """Промежуточная модель: назначение продукта продавцу."""
    __tablename__ = 'product_assignment'
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='uq_user_product'),)
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductAssignment user_id={self.user_id}, product_id={self.product_id}>'


class Authorization(db.Model):
    """Модель заявки на авторизацию клиники по продукту."""
    __tablename__ = 'authorization'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    inn = db.Column(db.String(12), nullable=False)
    contact_name = db.Column(db.String(255), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Authorization product_id={self.product_id}, inn={self.inn}, status={self.status}>'
    
    def days_remaining(self):
        if self.expires_at:
            delta = self.expires_at - datetime.utcnow()
            return max(0, delta.days)
        return None


class Material(db.Model):
    """Модель общего материала (брошюра, каталог)."""
    __tablename__ = 'material'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    description = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Material {self.title}>'


class PersonalDocument(db.Model):
    """Модель персонального документа (для конкретного продавца)."""
    __tablename__ = 'personal_document'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PersonalDocument {self.title} for seller_id={self.seller_id}>'


class Event(db.Model):
    """Модель события календаря (запрос продавца или слот администратора)."""
    __tablename__ = 'event'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False, index=True)
    end_datetime = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    admin_comment = db.Column(db.Text, nullable=True)
    is_anonymous_slot = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Event {self.title} ({self.event_type})>'


class Setting(db.Model):
    """Модель для хранения системных параметров (ключ-значение)."""
    __tablename__ = 'setting'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Setting {self.key}={self.value}>'
