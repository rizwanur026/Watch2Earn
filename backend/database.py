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

    try:

        # =========================
        # Users
        # =========================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                balance BIGINT NOT NULL DEFAULT 0,
                referrals INTEGER NOT NULL DEFAULT 0,
                ads_watched INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =========================
        # Reward Transactions
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
                description TEXT DEFAULT '',
                task_type TEXT NOT NULL,
                link TEXT DEFAULT '',
                reward BIGINT NOT NULL DEFAULT 0,
                status BOOLEAN NOT NULL DEFAULT TRUE,
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
        # Referrals
        # =========================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id SERIAL PRIMARY KEY,
                referrer_id BIGINT NOT NULL,
                referred_id BIGINT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =========================
        # Indexes
        # =========================

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_balance
            ON users(balance DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rewards_telegram_id
            ON reward_transactions(telegram_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status
            ON tasks(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_completions_user
            ON task_completions(telegram_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_referrals_referrer
            ON referrals(referrer_id)
        """)

        connection.commit()

        print("Database initialized successfully.")

    except Exception as error:

        connection.rollback()

        print(
            "Database initialization error:",
            error
        )

        raise

    finally:

        cursor.close()
        connection.close()
