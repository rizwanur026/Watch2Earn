import os
import hmac
import hashlib
import json
import asyncio
from datetime import datetime, timezone
from urllib.parse import parse_qsl

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Query,
)

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telegram import Update

from database import (
    init_database,
    get_connection
)

from bot import create_application


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Watch2Earn API",
    version="5.1"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CONSTANTS
# ============================================================

DAILY_BONUS = 100
AD_REWARD = 50

REFERRER_REWARD = 100
REFERRED_USER_REWARD = 50

AD_COOLDOWN_SECONDS = 30


# ============================================================
# ENVIRONMENT
# ============================================================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

WEB_APP_URL = os.getenv(
    "WEB_APP_URL",
    "https://rizwanur026.github.io/Watch2Earn/"
)

RENDER_EXTERNAL_URL = os.getenv(
    "RENDER_EXTERNAL_URL"
)

ADMIN_TELEGRAM_ID = os.getenv(
    "ADMIN_TELEGRAM_ID"
)


# ============================================================
# TELEGRAM APPLICATION
# ============================================================

telegram_application = create_application()

telegram_ready = False
telegram_lock = asyncio.Lock()


# ============================================================
# DATABASE
# ============================================================

init_database()


# ============================================================
# MODELS
# ============================================================

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


# ============================================================
# TELEGRAM AUTHENTICATION
# ============================================================

def verify_telegram_init_data(init_data: str):

    if not BOT_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="TELEGRAM_BOT_TOKEN is not configured"
        )

    if not init_data:
        raise HTTPException(
            status_code=401,
            detail="Telegram init data missing"
        )

    try:
        data = dict(
            parse_qsl(
                init_data,
                keep_blank_values=True
            )
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram init data"
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
        BOT_TOKEN.encode(),
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

    # Optional auth-date freshness check.
    # Telegram init data should normally be recent.
    try:
        auth_date = int(data.get("auth_date", "0"))

        if auth_date:
            current_timestamp = int(
                datetime.now(timezone.utc).timestamp()
            )

            # Allow up to 24 hours.
            if current_timestamp - auth_date > 86400:
                raise HTTPException(
                    status_code=401,
                    detail="Telegram authentication data expired"
                )

    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram auth date"
        )

    return data


# ============================================================
# TELEGRAM USER
# ============================================================

def get_telegram_user(init_data: str):

    data = verify_telegram_init_data(init_data)

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


# ============================================================
# ADMIN CHECK
# ============================================================

def require_admin(init_data: str):

    telegram_user = get_telegram_user(
        init_data
    )

    telegram_id = str(
        telegram_user["id"]
    )

    if not ADMIN_TELEGRAM_ID:
        raise HTTPException(
            status_code=503,
            detail="ADMIN_TELEGRAM_ID is not configured"
        )

    if telegram_id != str(ADMIN_TELEGRAM_ID):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return telegram_user


# ============================================================
# TELEGRAM INITIALIZATION
# ============================================================

async def initialize_telegram():

    global telegram_ready

    async with telegram_lock:

        if telegram_ready:
            return True

        for attempt in range(1, 4):

            try:

                print(
                    f"Telegram initialization attempt "
                    f"{attempt}/3"
                )

                await telegram_application.initialize()

                await telegram_application.start()

                if RENDER_EXTERNAL_URL:

                    webhook_url = (
                        RENDER_EXTERNAL_URL.rstrip("/")
                        + "/telegram/webhook"
                    )

                    await telegram_application.bot.set_webhook(
                        url=webhook_url,
                        allowed_updates=[
                            "message",
                            "callback_query"
                        ]
                    )

                    print(
                        "Telegram webhook configured:",
                        webhook_url
                    )

                else:

                    print(
                        "RENDER_EXTERNAL_URL not configured. "
                        "Telegram webhook was not set."
                    )

                telegram_ready = True

                print(
                    "Telegram application ready."
                )

                return True

            except Exception as error:

                print(
                    f"Telegram initialization failed "
                    f"(attempt {attempt}/3):",
                    repr(error)
                )

                if attempt < 3:
                    await asyncio.sleep(3)

        print(
            "Telegram initialization failed. "
            "FastAPI will continue running."
        )

        telegram_ready = False

        return False


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup_event():

    print("Watch2Earn API starting...")

    try:
        init_database()

        print(
            "Database initialization completed."
        )

    except Exception as error:

        print(
            "Database initialization error:",
            repr(error)
        )

    # Telegram failure must NOT crash Render.
    await initialize_telegram()


# ============================================================
# SHUTDOWN
# ============================================================

@app.on_event("shutdown")
async def shutdown_event():

    global telegram_ready

    if not telegram_ready:
        return

    try:

        await telegram_application.stop()

        await telegram_application.shutdown()

        telegram_ready = False

        print(
            "Telegram application stopped."
        )

    except Exception as error:

        print(
            "Telegram shutdown error:",
            repr(error)
        )


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "status": "online",
        "app": "Watch2Earn",
        "version": "5.1",
        "telegram": (
            "connected"
            if telegram_ready
            else "starting/unavailable"
        )
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT 1")
        cursor.fetchone()

        return {
            "status": "healthy",
            "database": "connected",
            "telegram": telegram_ready
        }

    except Exception as error:

        return {
            "status": "unhealthy",
            "database": "error",
            "telegram": telegram_ready,
            "error": str(error)
        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# TELEGRAM WEBHOOK
# ============================================================

@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request
):

    global telegram_ready

    try:

        if not telegram_ready:

            ready = await initialize_telegram()

            if not ready:

                return {
                    "ok": False,
                    "message": "Telegram bot is not ready"
                }

        update_data = await request.json()

        update = Update.de_json(
            update_data,
            telegram_application.bot
        )

        await telegram_application.process_update(
            update
        )

        return {
            "ok": True
        }

    except Exception as error:

        print(
            "Telegram webhook error:",
            repr(error)
        )

        return {
            "ok": False
        }


# ============================================================
# AUTH
# ============================================================

@app.post("/auth")
def authenticate_user(
    auth: TelegramAuth
):

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
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to authenticate user"
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# GET USER
# ============================================================

@app.get("/users/{telegram_id}")
def get_user(
    telegram_id: int
):

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


# ============================================================
# DAILY BONUS
# ============================================================

@app.post("/daily-bonus")
def claim_daily_bonus(
    auth: TelegramAuth
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
            FROM users
            WHERE telegram_id = %s
            FOR UPDATE
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
            FOR UPDATE
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

                return {
                    "success": False,
                    "message":
                        "Daily bonus already claimed",
                    "remaining_hours":
                        int(remaining // 3600),
                    "remaining_minutes":
                        int(
                            (remaining % 3600) // 60
                        )
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
            "balance":
                updated_user["balance"]
        }

    except HTTPException:

        connection.rollback()
        raise

    except Exception as error:

        connection.rollback()

        print(
            "Daily bonus error:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to claim daily bonus"
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# GET TASKS
# ============================================================

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
        connection.close()


# ============================================================
# ADMIN ADD TASK
# ============================================================

@app.post("/admin/tasks")
def create_task(
    task: TaskCreate,
    init_data: str = Query(...)
):

    require_admin(init_data)

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
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to create task"
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# COMPLETE TASK
# ============================================================

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
            FOR UPDATE
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
            INSERT INTO task_completions
            (
                telegram_id,
                task_id
            )
            VALUES (%s, %s)
            ON CONFLICT (telegram_id, task_id)
            DO NOTHING
            RETURNING id
            """,
            (
                telegram_id,
                task_id
            )
        )

        completion = cursor.fetchone()

        if not completion:

            connection.rollback()

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
            "balance":
                updated_user["balance"]
        }

    except HTTPException:

        connection.rollback()
        raise

    except Exception as error:

        connection.rollback()

        print(
            "Task completion error:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to complete task"
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# WATCH AD
# ============================================================

@app.post("/watch-ad")
def watch_ad(
    auth: AdReward
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
            SELECT created_at
            FROM reward_transactions
            WHERE telegram_id = %s
            AND reward_type = 'watch_ad'
            ORDER BY id DESC
            LIMIT 1
            """,
            (telegram_id,)
        )

        last_ad = cursor.fetchone()

        now = datetime.now(timezone.utc)

        if last_ad:

            last_time = last_ad["created_at"]

            if last_time.tzinfo is None:

                last_time = last_time.replace(
                    tzinfo=timezone.utc
                )

            elapsed = (
                now - last_time
            ).total_seconds()

            if elapsed < AD_COOLDOWN_SECONDS:

                remaining = int(
                    AD_COOLDOWN_SECONDS - elapsed
                )

                return {
                    "success": False,
                    "message":
                        "Please wait before watching another ad.",
                    "remaining_seconds":
                        remaining
                }

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
            "balance":
                user["balance"],
            "ads_watched":
                user["ads_watched"]
        }

    except HTTPException:

        connection.rollback()
        raise

    except Exception as error:

        connection.rollback()

        print(
            "Watch ad reward error:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to give ad reward"
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# REFERRALS
# ============================================================

@app.get("/referrals/{telegram_id}")
def get_referrals(
    telegram_id: int
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT referrals
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
                ON u.telegram_id =
                   r.referred_user_id
            WHERE r.referrer_id = %s
            ORDER BY r.id DESC
            """,
            (telegram_id,)
        )

        referral_users = cursor.fetchall()

        return {
            "success": True,
            "referrals":
                user["referrals"] or 0,
            "referrer_reward":
                REFERRER_REWARD,
            "referred_user_reward":
                REFERRED_USER_REWARD,
            "users": [
                dict(item)
                for item in referral_users
            ]
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# LEADERBOARD
# ============================================================

@app.get("/leaderboard")
def leaderboard(
    limit: int = 20
):

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
                    "telegram_id":
                        user["telegram_id"],
                    "username":
                        user["username"],
                    "first_name":
                        user["first_name"],
                    "balance":
                        user["balance"],
                    "referrals":
                        user["referrals"],
                    "ads_watched":
                        user["ads_watched"]
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
# WALLET GET
# ============================================================

@app.get("/wallet")
def get_wallet(
    init_data: str = Query(...)
):

    telegram_user = get_telegram_user(
        init_data
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
            "wallet_address":
                user["wallet_address"],
            "balance":
                user["balance"]
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# WALLET SAVE
# ============================================================

@app.post("/wallet")
def save_wallet(
    wallet: WalletUpdate
):

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
            "message":
                "TON wallet saved successfully",
            "wallet_address":
                user["wallet_address"],
            "balance":
                user["balance"]
        }

    except HTTPException:

        connection.rollback()
        raise

    except Exception as error:

        connection.rollback()

        print(
            "Wallet save error:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to save wallet"
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# WALLET REMOVE
# ============================================================

@app.delete("/wallet")
def remove_wallet(
    auth: TelegramAuth
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

    except Exception as error:

        connection.rollback()

        print(
            "Wallet remove error:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to remove wallet"
        )

    finally:

        cursor.close()
        connection.close()
