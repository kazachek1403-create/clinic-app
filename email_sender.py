"""
Система отправки email-уведомлений.
Использует Flask-Mail с поддержкой фонового потока для неблокирующей отправки.
"""

import threading
from flask import current_app, render_template_string
from flask_mail import Mail, Message
from models import Setting
import os


mail = Mail()


def get_mail_config():
    """Получить настройки почты из БД."""
    try:
        mail_server = Setting.query.filter_by(key='mail_server').first()
        mail_port = Setting.query.filter_by(key='mail_port').first()
        mail_username = Setting.query.filter_by(key='mail_username').first()
        mail_password = Setting.query.filter_by(key='mail_password').first()
        mail_use_tls = Setting.query.filter_by(key='mail_use_tls').first()
        
        if not all([mail_server, mail_port, mail_username, mail_password]):
            return None
        
        return {
            'server': mail_server.value,
            'port': int(mail_port.value),
            'username': mail_username.value,
            'password': mail_password.value,
            'use_tls': mail_use_tls.value.lower() == 'true' if mail_use_tls else False
        }
    except Exception as e:
        print(f"Ошибка при получении настроек почты: {e}")
        return None


def configure_mail_from_db(app):
    """Настроить Flask-Mail на основе параметров из БД."""
    with app.app_context():
        config = get_mail_config()
        if config:
            app.config['MAIL_SERVER'] = config['server']
            app.config['MAIL_PORT'] = config['port']
            app.config['MAIL_USERNAME'] = config['username']
            app.config['MAIL_PASSWORD'] = config['password']
            app.config['MAIL_USE_TLS'] = config['use_tls']
            app.config['MAIL_DEFAULT_SENDER'] = config['username']
            return True
        return False


def send_email(to, subject, template_name, **kwargs):
    """Отправить email в отдельном потоке."""
    def send_async(app, msg):
        with app.app_context():
            try:
                mail.send(msg)
            except Exception as e:
                print(f"Ошибка при отправке email: {e}")
    
    config = get_mail_config()
    if not config:
        print(f"Email не отправлен (почта не настроена): {to}")
        return
    
    try:
        template_path = os.path.join('email', f'{template_name}.txt')
        with current_app.open_resource(f'templates/{template_path}', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        body = render_template_string(template_content, **kwargs)
        
        msg = Message(
            subject=subject,
            recipients=to if isinstance(to, list) else [to],
            body=body
        )
        
        thread = threading.Thread(
            target=send_async,
            args=(current_app._get_current_object(), msg)
        )
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        print(f"Ошибка при подготовке email: {e}")


def send_test_email(to_email):
    """Отправить тестовое письмо."""
    send_email(
        to_email,
        subject='Тестовое письмо от платформы клиник',
        template_name='test_email',
        app_name='Платформа управления клиниками'
    )
