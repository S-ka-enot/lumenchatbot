#!/usr/bin/env python3
"""Скрипт для сброса пароля админа"""
import asyncio
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.admin import Admin
from sqlalchemy import select


async def reset_admin_password(username: str = "admin", new_password: str = "admin12345"):
    """Сброс пароля админа"""
    async with AsyncSessionLocal() as session:
        stmt = select(Admin).where(Admin.username == username)
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()
        
        if not admin:
            print(f"Админ с username '{username}' не найден!")
            return False
        
        admin.password_hash = get_password_hash(new_password)
        admin.is_active = True
        session.add(admin)
        await session.commit()
        
        print(f"✅ Пароль для админа '{username}' успешно сброшен!")
        print(f"   Новый пароль: {new_password}")
        return True


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    password = sys.argv[2] if len(sys.argv) > 2 else "admin12345"
    
    print(f"Сброс пароля для админа '{username}'...")
    asyncio.run(reset_admin_password(username, password))

