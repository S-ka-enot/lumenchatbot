#!/usr/bin/env python3
"""Простой скрипт для сброса пароля админа через SQL."""
import sqlite3
import sys
from pathlib import Path

# Используем тот же метод хеширования, что и в приложении
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
    
    def get_password_hash(password: str) -> str:
        # Обрезаем пароль до 72 байт для bcrypt
        password_bytes = password.encode('utf-8')[:72]
        password_str = password_bytes.decode('utf-8', errors='ignore')
        return pwd_context.hash(password_str)
except ImportError:
    print("❌ Не установлен passlib. Установите: pip install passlib[bcrypt]")
    sys.exit(1)

def reset_admin_password(db_path: str, username: str = "admin", password: str = "admin12345"):
    """Сбрасывает пароль админа через SQL."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли админ
        cursor.execute("SELECT id, username, is_active FROM admins WHERE username = ?", (username,))
        admin = cursor.fetchone()
        
        password_hash = get_password_hash(password)
        
        if admin:
            # Обновляем существующего админа
            cursor.execute(
                "UPDATE admins SET password_hash = ?, is_active = 1 WHERE username = ?",
                (password_hash, username)
            )
            print(f"✅ Пароль админа '{username}' обновлен")
        else:
            # Создаем нового админа
            cursor.execute(
                "INSERT INTO admins (username, password_hash, is_active, created_at, updated_at) VALUES (?, ?, 1, datetime('now'), datetime('now'))",
                (username, password_hash)
            )
            print(f"✅ Создан новый админ '{username}'")
        
        conn.commit()
        print(f"   Логин: {username}")
        print(f"   Пароль: {password}")
        print(f"   Hash: {password_hash[:30]}...")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "backend/lumenpay.db"
    username = sys.argv[2] if len(sys.argv) > 2 else "admin"
    password = sys.argv[3] if len(sys.argv) > 3 else "admin12345"
    
    if not Path(db_path).exists():
        print(f"❌ База данных не найдена: {db_path}")
        sys.exit(1)
    
    reset_admin_password(db_path, username, password)
