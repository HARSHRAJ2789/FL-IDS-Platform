"""
seed_admin.py
─────────────
Run once after deploying to Railway/Render to create the admin account.

Usage:
    python seed_admin.py

Or set env vars to override defaults:
    ADMIN_EMAIL=you@company.com ADMIN_PASSWORD=yourpassword python seed_admin.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from core.database import SessionLocal, create_tables
from core.security import hash_password, generate_api_key
from models import Organization
from datetime import datetime

ADMIN_NAME     = os.getenv("ADMIN_NAME",     "Admin")
ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL",    "admin@fl-ids.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "FLAdmin@2026")

def seed():
    create_tables()
    db = SessionLocal()
    try:
        existing = db.query(Organization).filter(Organization.email == ADMIN_EMAIL).first()
        if existing:
            print(f"✅ Admin already exists: {ADMIN_EMAIL}")
            print(f"   API Key: {existing.api_key}")
            return

        admin = Organization(
            name          = ADMIN_NAME,
            email         = ADMIN_EMAIL,
            password_hash = hash_password(ADMIN_PASSWORD),
            api_key       = generate_api_key(),
            plan          = "enterprise",
            is_active     = True,
            created_at    = datetime.utcnow(),
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("=" * 55)
        print("  FL-IDS Admin Account Created")
        print("=" * 55)
        print(f"  Email    : {ADMIN_EMAIL}")
        print(f"  Password : {ADMIN_PASSWORD}")
        print(f"  API Key  : {admin.api_key}")
        print(f"  Plan     : enterprise")
        print("=" * 55)
        print("  ⚠️  Save these credentials — password is hashed")
        print("      and cannot be recovered after this point.")
        print("=" * 55)
    finally:
        db.close()

if __name__ == "__main__":
    seed()
