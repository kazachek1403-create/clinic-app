"""
Основное приложение Flask для платформы управления клиниками.
Содержит инициализацию, маршруты и вспомогательные функции.
"""

import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from config import config
from models import (
    db, User, Product, ProductAssignment, Authorization,
    Material, PersonalDocument, Event, Setting
)
from forms import (
    LoginForm, UserForm, ProductForm, AuthorizationForm,
    MaterialUploadForm, DocumentUploadForm, ExchangeRateForm,
    EventForm, EmailSettingsForm
)
from email_sender import mail, send_email, configure_mail_from_db


app = Flask(__name__)
app.config.from_object(config[os.environ.get('FLASK_ENV', 'development')])

db.init_app(app)
mail.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

os.makedirs(app.config['MATERIALS_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOCUMENTS_FOLDER'], exist_ok=True)


def get_setting(key, default=None):
    setting = Setting.query.filter_by(key=key).first()
    return setting.value if setting else default


def set_setting(key, value):
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.session.add(setting)
    db.session.commit()


def update_authorization_statuses():
    expired = Authorization.query.filter(
        Authorization.status == 'approved',
        Authorization.expires_at < datetime.utcnow()
    ).all()
    for auth in expired:
        auth.status = 'expired'
    db.session.commit()


def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('Доступ запрещён.', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard' if current_user.role == 'admin' else 'seller_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('admin_dashboard' if user.role == 'admin' else 'seller_dashboard'))
        flash('Неверный логин или пароль.', 'danger')
    
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('login'))


@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    stats = {
        'total_users': User.query.count(),
        'total_products': Product.query.count(),
        'total_authorizations': Authorization.query.count(),
        'pending_authorizations': Authorization.query.filter_by(status='pending').count()
    }
    return render_template('admin/dashboard.html', stats=stats)


@app.route('/admin/products')
@login_required
@role_required('admin')
def admin_products():
    page = request.args.get('page', 1, type=int)
    products = Product.query.paginate(page=page, per_page=20)
    return render_template('admin/products.html', products=products)


@app.route('/admin/products/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_product_new():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(name=form.name.data, base_price=form.base_price.data)
        db.session.add(product)
        db.session.commit()
        flash(f'Продукт создан.', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', form=form, is_new=True)


@app.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_user_new():
    form = UserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, role=form.role.data, discount_percent=form.discount_percent.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Пользователь создан.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('admin/user_form.html', form=form, is_new=True)


@app.route('/admin/authorizations')
@login_required
@role_required('admin')
def admin_authorizations():
    update_authorization_statuses()
    status = request.args.get('status', 'pending')
    page = request.args.get('page', 1, type=int)
    query = Authorization.query if status == 'all' else Authorization.query.filter_by(status=status)
    auths = query.paginate(page=page, per_page=20)
    return render_template('admin/authorizations.html', authorizations=auths, status_filter=status)


@app.route('/admin/authorizations/<int:auth_id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def admin_auth_approve(auth_id):
    auth = Authorization.query.get_or_404(auth_id)
    auth.status = 'approved'
    auth.approved_at = datetime.utcnow()
    auth.expires_at = datetime.utcnow() + timedelta(days=90)
    db.session.commit()
    flash('Заявка одобрена.', 'success')
    return redirect(url_for('admin_authorizations'))


@app.route('/admin/authorizations/<int:auth_id>/reject', methods=['POST'])
@login_required
@role_required('admin')
def admin_auth_reject(auth_id):
    auth = Authorization.query.get_or_404(auth_id)
    auth.status = 'rejected'
    db.session.commit()
    flash('Заявка отклонена.', 'info')
    return redirect(url_for('admin_authorizations'))


@app.route('/admin/exchange-rate', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_exchange_rate():
    form = ExchangeRateForm()
    if form.validate_on_submit():
        set_setting('exchange_rate', str(form.exchange_rate.data))
        flash('Курс обновлён.', 'success')
        return redirect(url_for('admin_exchange_rate'))
    elif request.method == 'GET':
        form.exchange_rate.data = float(get_setting('exchange_rate', '1.0'))
    return render_template('admin/exchange_rate.html', form=form)


@app.route('/seller/dashboard')
@login_required
@role_required('seller')
def seller_dashboard():
    update_authorization_statuses()
    products = get_seller_products(current_user)
    rate = float(get_setting('exchange_rate', '1.0'))
    
    products_with_prices = []
    for p in products:
        price = p.base_price * (1 - current_user.discount_percent / 100)
        products_with_prices.append({
            'product': p,
            'base_price': p.base_price,
            'discount_percent': current_user.discount_percent,
            'price_with_discount': price
        })
    
    form = AuthorizationForm()
    form.product_id.choices = [(p['product'].id, f"{p['product'].name}") for p in products_with_prices]
    
    if form.validate_on_submit():
        auth = Authorization(
            product_id=form.product_id.data,
            inn=form.inn.data,
            contact_name=form.contact_name.data,
            contact_phone=form.contact_phone.data,
            seller_id=current_user.id,
            status='pending'
        )
        db.session.add(auth)
        db.session.commit()
        flash('Заявка подана.', 'success')
        return redirect(url_for('seller_dashboard'))
    
    auths = Authorization.query.filter_by(seller_id=current_user.id).all()
    return render_template('seller/dashboard.html', form=form, products_with_prices=products_with_prices, authorizations=auths, exchange_rate=rate)


def get_seller_products(seller):
    assignments = ProductAssignment.query.filter_by(user_id=seller.id).all()
    return [a.product for a in assignments]


def create_app():
    with app.app_context():
        db.create_all()
        configure_mail_from_db(app)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
