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
