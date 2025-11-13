#!/usr/bin/env python3
"""Скрипт для сброса пароля админа."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.admin import Admin
from sqlalchemy import select

async def reset_admin_password(username: str = "admin", password: str = "admin12345"):
    """Сбрасывает пароль админа."""
    async with AsyncSessionLocal() as session:
        stmt = select(Admin).where(Admin.username == username)
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()

        if not admin:
            print(f"❌ Админ с username '{username}' не найден.")
            print("💡 Создаю нового админа...")
            admin = Admin(
                username=username,
                password_hash=get_password_hash(password),
                is_active=True,
            )
            session.add(admin)
        else:
            print(f"✅ Админ '{username}' найден. Обновляю пароль...")
            admin.password_hash = get_password_hash(password)
            admin.is_active = True
            session.add(admin)
        
        await session.commit()
        await session.refresh(admin)
        print(f"✅ Пароль успешно установлен!")
        print(f"   Логин: {username}")
        print(f"   Пароль: {password}")
        return True

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    password = sys.argv[2] if len(sys.argv) > 2 else "admin12345"
    asyncio.run(reset_admin_password(username, password))
