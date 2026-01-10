"""Database seeding utilities.

Creates default admin user and singleton rows needed by Mission Control UI.
"""

from __future__ import annotations

import os
from sqlalchemy.orm import Session

from src.db.models import AdminUser, SystemState, AppSettings
from src.security.jwt_auth import hash_password

# Default settings for Mission Control
DEFAULT_SETTINGS = {
    "provider": "openai",
    "openai": {"api_key": "", "model": "gpt-4o"},
    "claude": {"api_key": "", "model": "claude-3-5-sonnet-20241022"},
    "watsonx": {
        "api_key": "",
        "project_id": "",
        "model_id": "meta-llama/llama-3-70b-instruct"
    },
    "ollama": {"base_url": "http://localhost:11434", "model": "llama3"},
    "adminWallet": os.getenv("ADMIN_WALLET", "0x71C7c83b96a438B59CFDA3e5859A23"),
    "organizationId": os.getenv("ORGANIZATION_ID", "ORG-8821"),
}


def seed_if_needed(db: Session) -> None:
    """Seed database with default data if tables are empty.

    Creates:
    - Default admin user (username/password from env vars)
    - SystemState singleton (autopilot=True, panic_mode=False)
    - AppSettings singleton (default LLM settings)

    Args:
        db: Database session
    """
    # Create default admin user
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin123")

    if not db.query(AdminUser).filter(AdminUser.username == username).first():
        admin = AdminUser(
            username=username,
            password_hash=hash_password(password),
            role="admin",
            is_active=True
        )
        db.add(admin)
        print(f"✅ Created default admin user: {username}")

    # Create system state singleton if none exists
    if db.query(SystemState).count() == 0:
        state = SystemState(autopilot_enabled=True, panic_mode=False)
        db.add(state)
        print("✅ Created system state singleton")

    # Create app settings singleton if none exists
    if db.query(AppSettings).count() == 0:
        settings = AppSettings(data=DEFAULT_SETTINGS)
        db.add(settings)
        print("✅ Created app settings singleton")

    db.commit()
    print("✅ Database seeding completed")
