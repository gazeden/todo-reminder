"""
Initialize the database with test data.
"""

import asyncio
from pathlib import Path
import sys
from sqlmodel import Session

# Append app package to python path
app_package_path = (Path(__file__).parent.parent).resolve()
sys.path.append(str(app_package_path))

from app.db.session import engine, init_db
from app.models.user import User
from app.core.security import get_password_hash


def create_initial_data():
    """Create initial test data."""
    with Session(engine) as session:
        # Create admin user
        admin = User(
            email="admin@example.com",
            username="admin",
            full_name="Admin User",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True,
        )
        session.add(admin)

        # Create regular user
        user = User(
            email="user@example.com",
            username="user",
            full_name="Regular User",
            hashed_password=get_password_hash("user123"),
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        session.commit()


if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("✅ Database tables created")

    print("Creating initial data...")
    create_initial_data()
    print("✅ Setup complete!")
