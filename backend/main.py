import os
import hmac
import hashlib
from urllib.parse import parse_qsl

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from database import init_database, get_connection


app = FastAPI(title="Watch2Earn API")


# Initialize database
init_database()


class TelegramAuth(BaseModel):
    init_data: str


def verify_telegram_init_data(init_data: str):
    """
    Verify Telegram Mini App initData.

    The bot token must be stored as an environment variable:
    TELEGRAM_BOT_TOKEN
    """

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    data = dict(parse_qsl(init_data, keep_blank_values=True))

    received_hash = data.pop("hash", None)

    if not received_hash:
        raise HTTPException(
            status_code=401,
            detail="Missing Telegram hash"
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
            detail="Invalid Telegram initData"
        )

    return data


@app.get("/")
def home():

    return {
        "status": "online",
        "app": "Watch2Earn",
        "version": "1.0"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.post("/auth")
def authenticate_user(auth: TelegramAuth):

    data = verify_telegram_init_data(
        auth.init_data
    )

    if "user" not in data:

        raise HTTPException(
            status_code=401,
            detail="Telegram user data missing"
        )

    import json

    telegram_user = json.loads(data["user"])

    telegram_id = telegram_user["id"]

    username = telegram_user.get(
        "username"
    )

    first_name = telegram_user.get(
        "first_name"
    )


    connection = get_connection()


    existing_user = connection.execute(
        """
        SELECT * FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,)
    ).fetchone()


    if existing_user:

        connection.close()

        return {
            "status": "existing",
            "user": dict(existing_user)
        }


    connection.execute(
        """
        INSERT INTO users
        (
            telegram_id,
            username,
            first_name
        )
        VALUES (?, ?, ?)
        """,
        (
            telegram_id,
            username,
            first_name
        )
    )


    connection.commit()


    new_user = connection.execute(
        """
        SELECT * FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,)
    ).fetchone()


    connection.close()


    return {
        "status": "created",
        "user": dict(new_user)
    }
