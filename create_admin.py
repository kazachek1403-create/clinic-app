"""
Скрипт для создания первого администратора.
Использование: python create_admin.py
"""

import os
import sys
from getpass import getpass

sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from models import User


def create_admin():
    """Интерактивное создание администратора."""
    with app.app_context():
        admin_count = User.query.filter_by(role='admin').count()
        if admin_count > 0:
            print("❌ Администраторы уже существуют. Этот скрипт можно запустить только один раз.")
            return
        
        print("\n" + "="*50)
        print("Создание первого администратора")
        print("="*50 + "\n")
        
        username = input("Введите логин администратора: ").strip()
        if not username or len(username) < 3:
            print("❌ Логин должен быть не менее 3 символов.")
            return
        
        if User.query.filter_by(username=username).first():
            print("❌ Этот логин уже занят.")
            return
        
        while True:
            password = getpass("Введите пароль: ")
            if len(password) < 6:
                print("❌ Пароль должен быть не менее 6 символов.")
                continue
            
            password_confirm = getpass("Повторите пароль: ")
            if password == password_confirm:
                break
            print("❌ Пароли не совпадают. Попробуйте снова.")
        
        admin = User(
            username=username,
            role='admin',
            discount_percent=0.0
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n" + "="*50)
        print(f"✅ Администратор '{username}' успешно создан!")
        print("="*50 + "\n")


if __name__ == '__main__':
    create_admin()
