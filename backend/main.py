import os
import hmac
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import parse_qsl

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import init_database, get_connection


# =========================
# FastAPI App
# =========================

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
# Constants
# =========================

DAILY_BONUS = 100
AD_REWARD = 50

REFERRER_REWARD = 100
REFERRED_USER_REWARD = 50


# =========================
# Models
# =========================

class TelegramAuth(BaseModel):
    init_data: str


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    task_type: str
    link: str = ""
    reward: int


class TaskComplete(BaseModel):
    init_data: str


class AdReward(BaseModel):
    init_data: str


class WalletUpdate(BaseModel):
    init_data: str
    wallet_address: str


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
# Get Telegram User
# =========================

def get_telegram_user(init_data: str):

    data = verify_telegram_init_data(
        init_data
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

    return telegram_user


# =========================
# Home
# =========================

@app.get("/")
def home():

    return {
        "status": "online",
        "app": "Watch2Earn",
        "version": "3.0"
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
# Telegram Bot Webhook
# =========================

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):

    try:

        update = await request.json()

        from bot import process_update

        result = process_update(update)

        return {
            "ok": True,
            "result": result
        }

    except Exception as error:

        print(
            "Telegram webhook error:",
            error
        )

        return {
            "ok": False
        }


# =========================
# Authenticate User
# =========================

@app.post("/auth")
def authenticate_user(auth: TelegramAuth):

    telegram_user = get_telegram_user(
        auth.init_data
    )

    telegram_id = telegram_user["id"]

    username = telegram_user.get(
        "username"
    )

    first_name = telegram_user.get(
        "first_name"
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:

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
                """,
                (
                    telegram_id,
                    username,
                    first_name
                )
            )

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

        return {
            "status": "success",
            "user": dict(user)
        }

    except Exception as error:

        connection.rollback()

        print(
            "Authentication error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to authenticate user"
        )

    finally:

        cursor.close()
        connection.close()


# =========================
# Get User
# =========================

@app.get("/users/{telegram_id}")
def get_user(telegram_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                telegram_id,
                username,
                first_name,
                balance,
                referrals,
                ads_watched,
                wallet_address,
                referred_by,
                created_at
            FROM users
            WHERE telegram_id = %s
            """,
            (telegram_id,)
        )

        user = cursor.fetchone()

        if not user:

            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return {
            "user": dict(user)
        }

    finally:

        cursor.close()
        connection.close()


# =========================
# Daily Bonus
# =========================

@app.post("/daily-bonus")
def claim_daily_bonus(auth: TelegramAuth):

    telegram_user = get_telegram_user(
        auth.init_data
    )

    telegram_id = telegram_user["id"]

    connection = get_connection()
    cursor = connection.cursor()

    try:

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

            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

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

                return {
                    "success": False,
                    "message": "Daily bonus already claimed",
                    "remaining_hours": hours,
                    "remaining_minutes": minutes
                }

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

        cursor.execute(
            """
            SELECT balance
            FROM users
            WHERE telegram_id = %s
            """,
            (telegram_id,)
        )

        updated_user = cursor.fetchone()

        return {
            "success": True,
            "reward": DAILY_BONUS,
            "balance": updated_user["balance"]
        }

    except HTTPException:

        connection.rollback()
        raise

    except Exception as error:

        connection.rollback()

        print(
            "Daily bonus error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to claim daily bonus"
        )

    finally:

        cursor.close()
        connection.close()


# =========================
# Get Tasks
# =========================

@app.get("/tasks")
def get_tasks():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                title,
                description,
                task_type,
                link,
                reward
            FROM tasks
            WHERE status = TRUE
            ORDER BY id DESC
            """
        )

        tasks = cursor.fetchall()

        return {
            "success": True,
            "tasks": [
                dict(task)
                for task in tasks
            ]
        }

    finally:

        cursor.close()
        cursor.close() if False else None
        connection.close()


# =========================
# Admin - Add Task
# =========================

@app.post("/admin/tasks")
def create_task(task: TaskCreate):

    if task.reward <= 0:

        raise HTTPException(
            status_code=400,
            detail="Reward must be greater than 0"
        )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO tasks
            (
                title,
                description,
                task_type,
                link,
                reward,
                status
            )
            VALUES (%s, %s, %s, %s, %s, TRUE)
            RETURNING *
            """,
            (
                task.title,
                task.description,
                task.task_type,
                task.link,
                task.reward
            )
        )

        new_task = cursor.fetchone()

        connection.commit()

        return {
            "success": True,
            "task": dict(new_task)
        }

    except Exception as error:

        connection.rollback()

        print(
            "Create task error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to create task"
        )

    finally:

        cursor.close()
        connection.close()


# =========================
# Complete Task
# =========================

@app.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: int,
    auth: TaskComplete
):

    telegram_user = get_telegram_user(
        auth.init_data
    )

    telegram_id = telegram_user["id"]

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT *
            FROM tasks
            WHERE id = %s
            AND status = TRUE
            """,
            (task_id,)
        )

        task = cursor.fetchone()

        if not task:

            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

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

            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        cursor.execute(
            """
            SELECT id
            FROM task_completions
            WHERE telegram_id = %s
            AND task_id = %s
            """,
            (
                telegram_id,
                task_id
            )
        )

        completed = cursor.fetchone()

        if completed:

            return {
                "success": False,
                "message": "Task already completed"
            }

        cursor.execute(
            """
            UPDATE users
            SET balance = balance + %s
            WHERE telegram_id = %s
            """,
            (
                task["reward"],
                telegram_id
            )
        )

        cursor.execute(
            """
            INSERT INTO task_completions
            (
                telegram_id,
                task_id
            )
            VALUES (%s, %s)
            """,
            (
                telegram_id,
                task_id
            )
        )

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
                "task",
                task["reward"]
            )
        )

        connection.commit()

        cursor.execute(
            """
            SELECT balance
            FROM users
            WHERE telegram_id = %s
            """,
            (telegram_id,)
        )

        updated_user = cursor.fetchone()

        return {
            "success": True,
            "reward": task["reward"],
            "balance": updated_user["balance"]
        }

    except HTTPException:

        connection.rollback()
        raise

    except Exception as error:

        connection.rollback()

        print(
            "Task completion error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to complete task"
        )

    finally:

        cursor.close()
        connection.close()


# =========================
# Watch Ad Reward
# =========================

@app.post("/watch-ad")
def watch_ad(auth: AdReward):

    telegram_user = get_telegram_user(
        auth.init_data
    )

    telegram_id = telegram_user["id"]

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE users
            SET balance = balance + %s,
                ads_watched = ads_watched + 1
            WHERE telegram_id = %s
            RETURNING balance, ads_watched
            """,
            (
                AD_REWARD,
                telegram_id
            )
        )

        user = cursor.fetchone()

        if not user:

            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

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
                "watch_ad",
                AD_REWARD
            )
        )

        connection.commit()

        return {
            "success": True,
            "reward": AD_REWARD,
            "balance": user["balance"],
            "ads_watched": user["ads_watched"]
        }

    except HTTPException:

        connection.rollback()
        raise

    except Exception as error:

        connection.rollback()

        print(
            "Watch ad reward error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to give ad reward"
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# REFERRAL SYSTEM
# ============================================================

@app.get("/referrals/{telegram_id}")
def get_referrals(telegram_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                referrals
            FROM users
            WHERE telegram_id = %s
            """,
            (telegram_id,)
        )

        user = cursor.fetchone()

        if not user:

            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        cursor.execute(
            """
            SELECT
                u.telegram_id,
                u.username,
                u.first_name,
                r.reward,
                r.created_at
            FROM referral_rewards r
            JOIN users u
                ON u.telegram_id = r.referred_user_id
            WHERE r.referrer_id = %s
            ORDER BY r.id DESC
            """,
            (telegram_id,)
        )

        referrals_list = cursor.fetchall()

        return {
            "success": True,
            "referrals": user["referrals"] or 0,
            "users": [
                dict(item)
                for item in referrals_list
            ]
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# LEADERBOARD
# ============================================================

@app.get("/leaderboard")
def leaderboard(limit: int = 20):

    if limit < 1:
        limit = 1

    if limit > 100:
        limit = 100

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                telegram_id,
                username,
                first_name,
                balance,
                referrals,
                ads_watched
            FROM users
            ORDER BY balance DESC, id ASC
            LIMIT %s
            """,
            (limit,)
        )

        users = cursor.fetchall()

        result = []

        for index, user in enumerate(
            users,
            start=1
        ):

            result.append(
                {
                    "rank": index,
                    "telegram_id": user["telegram_id"],
                    "username": user["username"],
                    "first_name": user["first_name"],
                    "balance": user["balance"],
                    "referrals": user["referrals"],
                    "ads_watched": user["ads_watched"]
                }
            )

        return {
            "success": True,
            "leaderboard": result
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# WALLET
# ============================================================

@app.get("/wallet")
def get_wallet(auth: TelegramAuth):

    telegram_user = get_telegram_user(
        auth.init_data
    )

    telegram_id = telegram_user["id"]

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                wallet_address,
                balance
            FROM users
            WHERE telegram_id = %s
            """,
            (telegram_id,)
        )

        user = cursor.fetchone()

        if not user:

            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return {
            "success": True,
            "wallet_address": user["wallet_address"],
            "balance": user["balance"]
        }

    finally:

        cursor.close()
        connection.close()


@app.post("/wallet")
def save_wallet(wallet: WalletUpdate):

    telegram_user = get_telegram_user(
        wallet.init_data
    )

    telegram_id = telegram_user["id"]

    wallet_address = (
        wallet.wallet_address.strip()
    )

    if not wallet_address:

        raise HTTPException(
            status_code=400,
            detail="Wallet address is required"
        )

    # Basic TON address validation
    if not (
        wallet_address.startswith("EQ")
        or wallet_address.startswith("UQ")
        or wallet_address.startswith("kQ")
        or wallet_address.startswith("0:")
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid TON wallet address"
        )

    if len(wallet_address) < 20:

        raise HTTPException(
            status_code=400,
            detail="Invalid TON wallet address"
        )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE users
            SET wallet_address = %s
            WHERE telegram_id = %s
            RETURNING wallet_address, balance
            """,
            (
                wallet_address,
                telegram_id
            )
        )

        user = cursor.fetchone()

        if not user:

            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        connection.commit()

        return {
            "success": True,
            "message": "TON wallet saved successfully",
            "wallet_address": user["wallet_address"],
            "balance": user["balance"]
        }

    except HTTPException:

        connection.rollback()
        raise

    except Exception as error:

        connection.rollback()

        print(
            "Wallet save error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to save wallet"
        )

    finally:

        cursor.close()
        connection.close()


@app.delete("/wallet")
def remove_wallet(auth: TelegramAuth):

    telegram_user = get_telegram_user(
        auth.init_data
    )

    telegram_id = telegram_user["id"]

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE users
            SET wallet_address = NULL
            WHERE telegram_id = %s
            RETURNING telegram_id
            """,
            (telegram_id,)
        )

        user = cursor.fetchone()

        if not user:

            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        connection.commit()

        return {
            "success": True,
            "message": "Wallet removed"
        }

    except HTTPException:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()
