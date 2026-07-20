#!/usr/bin/env python3
"""
SentinelAI Database Seeder

Seeds the database with:
- Admin user account
- Default model configurations
- Sample data for development/testing

Usage:
    python scripts/seed-db.py
    python scripts/seed-db.py --env production  # Only creates admin user

Environment Variables:
    DATABASE_URL: PostgreSQL connection string
    ADMIN_EMAIL: Admin email (default: admin@sentinelai.local)
    ADMIN_PASSWORD: Admin password (default: auto-generated)
"""

import argparse
import asyncio
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import asyncpg


# ==============================================================================
# Configuration
# ==============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sentinelai:sentinelai@localhost:5432/sentinelai",
)

# Convert asyncpg URL if needed
DB_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@sentinelai.local")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

DEFAULT_MODELS = [
    {
        "name": "GPT-4",
        "provider": "openai",
        "model_id": "gpt-4",
        "description": "OpenAI GPT-4 - Most capable model for complex tasks",
        "is_active": True,
        "max_tokens": 8192,
        "temperature": 0.7,
    },
    {
        "name": "GPT-4 Turbo",
        "provider": "openai",
        "model_id": "gpt-4-turbo-preview",
        "description": "OpenAI GPT-4 Turbo - Faster and cheaper than GPT-4",
        "is_active": True,
        "max_tokens": 128000,
        "temperature": 0.7,
    },
    {
        "name": "Claude 3 Sonnet",
        "provider": "anthropic",
        "model_id": "claude-3-sonnet-20240229",
        "description": "Anthropic Claude 3 Sonnet - Balanced performance and speed",
        "is_active": True,
        "max_tokens": 4096,
        "temperature": 0.7,
    },
    {
        "name": "Claude 3 Opus",
        "provider": "anthropic",
        "model_id": "claude-3-opus-20240229",
        "description": "Anthropic Claude 3 Opus - Most capable Anthropic model",
        "is_active": True,
        "max_tokens": 4096,
        "temperature": 0.7,
    },
    {
        "name": "Gemini Pro",
        "provider": "google",
        "model_id": "gemini-pro",
        "description": "Google Gemini Pro - General purpose model",
        "is_active": True,
        "max_tokens": 8192,
        "temperature": 0.7,
    },
    {
        "name": "Llama 2 (Local)",
        "provider": "ollama",
        "model_id": "llama2",
        "description": "Meta Llama 2 - Local inference via Ollama",
        "is_active": True,
        "max_tokens": 4096,
        "temperature": 0.7,
    },
    {
        "name": "Mistral (Local)",
        "provider": "ollama",
        "model_id": "mistral",
        "description": "Mistral 7B - Fast local inference via Ollama",
        "is_active": True,
        "max_tokens": 4096,
        "temperature": 0.7,
    },
]


# ==============================================================================
# Password Hashing (standalone, no dependency on app)
# ==============================================================================


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    try:
        import bcrypt

        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    except ImportError:
        # Fallback: use passlib if bcrypt not directly available
        from passlib.context import CryptContext

        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return ctx.hash(password)


# ==============================================================================
# Seed Functions
# ==============================================================================


async def create_admin_user(conn: asyncpg.Connection) -> dict:
    """Create the admin user account."""
    password = ADMIN_PASSWORD or secrets.token_urlsafe(16)
    hashed = hash_password(password)
    user_id = str(uuid4())
    now = datetime.now(timezone.utc)

    # Check if admin already exists
    existing = await conn.fetchrow(
        "SELECT id FROM users WHERE email = $1", ADMIN_EMAIL
    )
    if existing:
        print(f"  ⚠️  Admin user already exists: {ADMIN_EMAIL}")
        return {"email": ADMIN_EMAIL, "password": "(unchanged)", "id": str(existing["id"])}

    await conn.execute(
        """
        INSERT INTO users (id, email, username, hashed_password, full_name, role, is_active, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        user_id,
        ADMIN_EMAIL,
        "admin",
        hashed,
        "System Administrator",
        "admin",
        True,
        now,
        now,
    )

    return {"email": ADMIN_EMAIL, "password": password, "id": user_id}


async def create_model_configs(conn: asyncpg.Connection) -> int:
    """Create default model configurations."""
    count = 0
    now = datetime.now(timezone.utc)

    for model in DEFAULT_MODELS:
        # Check if model already exists
        existing = await conn.fetchrow(
            "SELECT id FROM model_configs WHERE model_id = $1", model["model_id"]
        )
        if existing:
            continue

        model_config_id = str(uuid4())
        await conn.execute(
            """
            INSERT INTO model_configs (id, name, provider, model_id, description, is_active, max_tokens, temperature, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            model_config_id,
            model["name"],
            model["provider"],
            model["model_id"],
            model["description"],
            model["is_active"],
            model["max_tokens"],
            model["temperature"],
            now,
            now,
        )
        count += 1

    return count


async def create_sample_data(conn: asyncpg.Connection) -> dict:
    """Create sample data for development (users, chats)."""
    now = datetime.now(timezone.utc)
    created = {"users": 0, "chats": 0}

    # Sample users
    sample_users = [
        {
            "email": "developer@sentinelai.local",
            "username": "developer",
            "full_name": "Dev User",
            "role": "user",
        },
        {
            "email": "analyst@sentinelai.local",
            "username": "analyst",
            "full_name": "Security Analyst",
            "role": "user",
        },
        {
            "email": "viewer@sentinelai.local",
            "username": "viewer",
            "full_name": "Read-Only Viewer",
            "role": "viewer",
        },
    ]

    for user in sample_users:
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", user["email"]
        )
        if existing:
            continue

        user_id = str(uuid4())
        password = hash_password("DemoP@ss123!")
        await conn.execute(
            """
            INSERT INTO users (id, email, username, hashed_password, full_name, role, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            user_id,
            user["email"],
            user["username"],
            password,
            user["full_name"],
            user["role"],
            True,
            now,
            now,
        )
        created["users"] += 1

    return created


# ==============================================================================
# Main
# ==============================================================================


async def main(environment: str = "development"):
    """Run database seeding."""
    print("=" * 60)
    print(" SentinelAI Database Seeder")
    print(f" Environment: {environment}")
    print(f" Database: {DB_URL.split('@')[-1] if '@' in DB_URL else DB_URL}")
    print("=" * 60)
    print()

    try:
        conn = await asyncpg.connect(DB_URL)
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print("   Make sure the database is running and DATABASE_URL is correct.")
        sys.exit(1)

    try:
        # Always create admin user
        print("📌 Creating admin user...")
        admin_info = await create_admin_user(conn)
        print(f"  ✅ Admin: {admin_info['email']}")
        if admin_info["password"] != "(unchanged)":
            print(f"  🔑 Password: {admin_info['password']}")
            print("  ⚠️  Save this password! It won't be shown again.")
        print()

        # Create model configs
        print("📌 Creating model configurations...")
        model_count = await create_model_configs(conn)
        print(f"  ✅ Created {model_count} model configurations")
        print()

        # Create sample data (dev/staging only)
        if environment != "production":
            print("📌 Creating sample data...")
            sample_data = await create_sample_data(conn)
            print(f"  ✅ Created {sample_data['users']} sample users")
            print()
            print("  Sample accounts (password: DemoP@ss123!):")
            print("    - developer@sentinelai.local")
            print("    - analyst@sentinelai.local")
            print("    - viewer@sentinelai.local")
            print()

        print("=" * 60)
        print(" ✅ Database seeding complete!")
        print("=" * 60)

    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelAI Database Seeder")
    parser.add_argument(
        "--env",
        choices=["development", "staging", "production"],
        default="development",
        help="Target environment (default: development)",
    )
    args = parser.parse_args()

    asyncio.run(main(args.env))
