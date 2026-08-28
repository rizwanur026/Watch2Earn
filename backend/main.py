import os
import hmac
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import parse_qsl

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import init_database, get_connection


app = FastAPI(title="Watch2Earn API")


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Database
# =========================

init_database()


# =========================
# Models
# =========================

class TelegramAuth(BaseModel):
    init_data: str


# =========================
# Telegram Verification
# =========================

def verify_telegram_init_data(init_data: str):

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured"
        )

    data = dict(
        parse_qsl(
            init_data,
            keep_blank_values=True
        )
    )

    received_hash = data.pop("hash", None)

    if not received_hash:
        raise HTTPException(
            status_code=401,
            detail="Telegram hash missing"
        )

    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(data.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
        calculated_hash,
        received_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram authentication"
        )

    return data


# =========================
# Home
# =========================

@app.get("/")
def home():

    return {
        "status": "online",
        "app": "Watch2Earn",
        "version": "2.0"
    }


# =========================
# Health
# =========================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# =========================
# Authenticate User
# =========================

@app.post("/auth")
def authenticate_user(auth: TelegramAuth):

    data = verify_telegram_init_data(
        auth.init_data
    )

    if "user" not in data:

        raise HTTPException(
            status_code=401,
            detail="Telegram user missing"
        )

    try:

        telegram_user = json.loads(
            data["user"]
        )

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram user data"
        )


    telegram_id = telegram_user.get("id")

    if not telegram_id:

        raise HTTPException(
            status_code=401,
            detail="Telegram ID missing"
        )


    username = telegram_user.get(
        "username"
    )

    first_name = telegram_user.get(
        "first_name"
    )


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = %s
        """,
        (telegram_id,)
    )

    user = cursor.fetchone()


    if user:

        cursor.execute(
            """
            UPDATE users
            SET username = %s,
                first_name = %s
            WHERE telegram_id = %s
            """,
            (
                username,
                first_name,
                telegram_id
            )
        )

        connection.commit()

    else:

        cursor.execute(
            """
            INSERT INTO users
            (
                telegram_id,
                username,
                first_name,
                balance,
                referrals,
                ads_watched
            )
            VALUES (%s, %s, %s, 0, 0, 0)
            RETURNING *
            """,
            (
                telegram_id,
                username,
                first_name
            )
        )

        user = cursor.fetchone()

        connection.commit()


    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = %s
        """,
        (telegram_id,)
    )

    user = cursor.fetchone()


    cursor.close()
    connection.close()


    return {
        "status": "success",
        "user": dict(user)
    }


# =========================
# Get User
# =========================

@app.get("/users/{telegram_id}")
def get_user(telegram_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = %s
        """,
        (telegram_id,)
    )

    user = cursor.fetchone()

    cursor.close()
    connection.close()


    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    return {
        "user": dict(user)
    }

from datetime import datetime, timezone


DAILY_BONUS = 100


@app.post("/daily-bonus")
def claim_daily_bonus(auth: TelegramAuth):

    # Verify Telegram Mini App data
    data = verify_telegram_init_data(
        auth.init_data
    )

    if "user" not in data:
        raise HTTPException(
            status_code=401,
            detail="Telegram user missing"
        )

    try:
        telegram_user = json.loads(
            data["user"]
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram user data"
        )

    telegram_id = telegram_user.get("id")

    if not telegram_id:
        raise HTTPException(
            status_code=401,
            detail="Telegram ID missing"
        )

    connection = get_connection()
    cursor = connection.cursor()

    # Check user
    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = %s
        """,
        (telegram_id,)
    )

    user = cursor.fetchone()

    if not user:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Check previous daily claim
    cursor.execute(
        """
        SELECT *
        FROM daily_claims
        WHERE telegram_id = %s
        """,
        (telegram_id,)
    )

    claim = cursor.fetchone()

    now = datetime.now(timezone.utc)

    if claim and claim["last_claim"]:

        last_claim = claim["last_claim"]

        if last_claim.tzinfo is None:
            last_claim = last_claim.replace(
                tzinfo=timezone.utc
            )

        elapsed = now - last_claim

        if elapsed.total_seconds() < 86400:

            remaining = (
                86400 -
                elapsed.total_seconds()
            )

            hours = int(
                remaining // 3600
            )

            minutes = int(
                (remaining % 3600) // 60
            )

            cursor.close()
            connection.close()

            return {
                "success": False,
                "message": "Daily bonus already claimed",
                "remaining_hours": hours,
                "remaining_minutes": minutes
            }

    # Add reward
    cursor.execute(
        """
        UPDATE users
        SET balance = balance + %s
        WHERE telegram_id = %s
        """,
        (
            DAILY_BONUS,
            telegram_id
        )
    )

    # Save transaction
    cursor.execute(
        """
        INSERT INTO reward_transactions
        (
            telegram_id,
            reward_type,
            amount
        )
        VALUES (%s, %s, %s)
        """,
        (
            telegram_id,
            "daily_bonus",
            DAILY_BONUS
        )
    )

    # Save daily claim
    cursor.execute(
        """
        INSERT INTO daily_claims
        (
            telegram_id,
            last_claim
        )
        VALUES (%s, %s)

        ON CONFLICT (telegram_id)
        DO UPDATE SET
            last_claim = EXCLUDED.last_claim
        """,
        (
            telegram_id,
            now
        )
    )

    connection.commit()

    # Get updated balance
    cursor.execute(
        """
        SELECT balance
        FROM users
        WHERE telegram_id = %s
        """,
        (telegram_id,)
    )

    updated_user = cursor.fetchone()

    cursor.close()
    connection.close()

    return {
        "success": True,
        "reward": DAILY_BONUS,
        "balance": updated_user["balance"]
    }
