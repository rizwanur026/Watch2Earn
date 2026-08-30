import os
import psycopg2
from psycopg2.extras import RealDictCursor


DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured"
        )

    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


def init_database():

    connection = get_connection()
    cursor = connection.cursor()

    # =========================
    # Users
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            balance BIGINT DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            ads_watched INTEGER DEFAULT 0,
            referred_by BIGINT,
            wallet_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Existing database compatibility
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS referred_by BIGINT
    """)

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS wallet_address TEXT
    """)

    # =========================
    # Reward History
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reward_transactions (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            reward_type TEXT NOT NULL,
            amount BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # Daily Claims
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_claims (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            last_claim TIMESTAMP
        )
    """)

    # =========================
    # Tasks
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            task_type TEXT NOT NULL,
            link TEXT,
            reward BIGINT NOT NULL DEFAULT 0,
            status BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # Task Completions
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_completions (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            task_id INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (telegram_id, task_id)
        )
    """)

    # =========================
    # Referral Completions
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referral_rewards (
            id SERIAL PRIMARY KEY,
            referrer_id BIGINT UNIQUE NOT NULL,
            referred_user_id BIGINT UNIQUE NOT NULL,
            reward BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    cursor.close()
    connection.close()
