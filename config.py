"""
Конфигурация приложения Flask для платформы клиник.
Включает параметры БД, почты, безопасности и загрузки файлов.
"""

import os
from datetime import timedelta

# Базовый путь приложения
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Основная конфигурация."""
    # Секретный ключ для сессий и CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clinic-secret-key-change-in-production'
    
    # Конфигурация SQLAlchemy
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'clinic.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    
    # Загрузка файлов
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MATERIALS_FOLDER = os.path.join(UPLOAD_FOLDER, 'materials')
    DOCUMENTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'documents')
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 МБ
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'docx', 'xlsx', 'pptx'}
    
    # Почта (по умолчанию отключена)
    MAIL_SERVER = None
    MAIL_PORT = None
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    
    # Пагинация
    ITEMS_PER_PAGE = 20


class DevelopmentConfig(Config):
    """Конфигурация для разработки."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Конфигурация для production."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Конфигурация для тестирования."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Выбор конфигурации по переменной окружения
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
