import os
import hmac
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import parse_qsl

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from telegram import Update

from database import init_database, get_connection
from bot import create_application

app = FastAPI(
title="Watch2Earn API",
version="5.1"
)

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=False,
allow_methods=["*"],
allow_headers=["*"],
)

DAILY_BONUS = 100
AD_REWARD = 50

REFERRER_REWARD = 100
REFERRED_USER_REWARD = 50

AD_COOLDOWN_SECONDS = 30

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

WEB_APP_URL = os.getenv(
"WEB_APP_URL",
"https://rizwanur026.github.io/Watch2Earn/"
)

RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")

telegram_application = create_application()

init_database()

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

def verify_telegram_init_data(init_data: str):

```
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
    BOT_TOKEN.encode("utf-8"),
    hashlib.sha256
).digest()

calculated_hash = hmac.new(
    secret_key,
    data_check_string.encode("utf-8"),
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
```

def get_telegram_user(init_data: str):

```
data = verify_telegram_init_data(init_data)

if "user" not in data:
    raise HTTPException(
        status_code=401,
        detail="Telegram user missing"
    )

try:
    telegram_user = json.loads(data["user"])
except (json.JSONDecodeError, TypeError):
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
```

def require_admin(init_data: str):

```
telegram_user = get_telegram_user(init_data)

if not ADMIN_TELEGRAM_ID:
    raise HTTPException(
        status_code=503,
        detail="ADMIN_TELEGRAM_ID is not configured"
    )

if str(telegram_user["id"]) != str(ADMIN_TELEGRAM_ID):
    raise HTTPException(
        status_code=403,
        detail="Admin access required"
    )

return telegram_user
```

@app.on_event("startup")
async def startup_event():

```
try:

    print("Watch2Earn API starting...")

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
            "RENDER_EXTERNAL_URL not configured."
        )

    print("Telegram application ready.")

except Exception as error:

    print(
        "Telegram startup error:",
        error
    )

    raise
```

@app.on_event("shutdown")
async def shutdown_event():

```
try:

    await telegram_application.stop()
    await telegram_application.shutdown()

    print("Telegram application stopped.")

except Exception as error:

    print(
        "Telegram shutdown error:",
        error
    )
```

@app.get("/")
def home():

```
return {
    "status": "online",
    "app": "Watch2Earn",
    "version": "5.1"
}
```

@app.head("/")
def home_head():

```
return
```

@app.get("/health")
def health():

```
connection = None
cursor = None

try:

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT 1")
    cursor.fetchone()

    return {
        "status": "healthy",
        "database": "connected"
    }

except Exception as error:

    return {
        "status": "unhealthy",
        "database": "error",
        "error": str(error)
    }

finally:

    if cursor:
        cursor.close()

    if connection:
        connection.close()
```

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):

```
try:

    update_data = await request.json()

    update = Update.de_json(
        update_data,
        telegram_application.bot
    )

    if update:

        await telegram_application.process_update(
            update
        )

    return {
        "ok": True
    }

except Exception as error:

    print(
        "Telegram webhook error:",
        error
    )

    return {
        "ok": False
    }
```

@app.post("/auth")
def authenticate_user(auth: TelegramAuth):

```
telegram_user = get_telegram_user(
    auth.init_data
)

telegram_id = telegram_user["id"]
username = telegram_user.get("username")
first_name = telegram_user.get("first_name")

connection = None
cursor = None

try:

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

    if not user:

        raise HTTPException(
            status_code=500,
            detail="User could not be loaded"
        )

    return {
        "status": "success",
        "user": dict(user)
    }

except HTTPException:

    if connection:
        connection.rollback()

    raise

except Exception as error:

    if connection:
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

    if cursor:
        cursor.close()

    if connection:
        connection.close()
```

@app.get("/users/{telegram_id}")
def get_user(telegram_id: int):

```
connection = None
cursor = None

try:

    connection = get_connection()
    cursor = connection.cursor()

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

    if cursor:
        cursor.close()

    if connection:
        connection.close()
```

@app.post("/daily-bonus")
def claim_daily_bonus(auth: TelegramAuth):

```
telegram_user = get_telegram_user(
    auth.init_data
)

telegram_id = telegram_user["id"]

connection = None
cursor = None

try:

    connection = get_connection()
    cursor = connection.cursor()

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

        elapsed = (
            now - last_claim
        ).total_seconds()

        if elapsed < 86400:

            remaining = 86400 - elapsed

            return {
                "success": False,
                "message": "Daily bonus already claimed",
                "remaining_hours": int(
                    remaining // 3600
                ),
                "remaining_minutes": int(
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
        "balance": updated_user["balance"]
    }

except HTTPException:

    if connection:
        connection.rollback()

    raise

except Exception as error:

    if connection:
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

    if cursor:
        cursor.close()

    if connection:
        connection.close()
```

@app.get("/tasks")
def get_tasks():

```
connection = None
cursor = None

try:

    connection = get_connection()
    cursor = connection.cursor()

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

    if cursor:
        cursor.close()

    if connection:
        connection.close()
```

@app.post("/admin/tasks")
def create_task(
task: TaskCreate,
init_data: str = Query(...)
):

```
require_admin(init_data)

if not task.title.strip():

    raise HTTPException(
        status_code=400,
        detail="Task title is required"
    )

if task.reward <= 0:

    raise HTTPException(
        status_code=400,
        detail="Reward must be greater than 0"
    )

connection = None
cursor = None

try:

    connection = get_connection()
    cursor = connection.cursor()

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
            task.title.strip(),
            task.description.strip(),
            task.task_type.strip(),
            task.link.strip(),
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

    if connection:
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

    if cursor:
        cursor.close()

    if connection:
        connection.close()
```

@app.post("/tasks/{task_id}/complete")
def complete_task(
task_id: int,
auth: TaskComplete
):

```
telegram_user = get_telegram_user(
    auth.init_data
)

telegram_id = telegram_user["id"]

connection = None
cursor = None

try:

    connection = get_connection()
    cursor = connection.cursor()

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
        "balance": updated_user["balance"]
    }

except HTTPException:

    if connection:
        connection.rollback()

    raise

except Exception as error:

    if connection:
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

    if cursor:
        cursor.close()

    if connection:
        connection.close()
```

@app.post("/watch-ad")
def watch_ad(auth: AdReward):

```
telegram_user = get_telegram_user(
    auth.init_data
)

telegram_id = telegram_user["id"]

connection = None
cursor = None

try:

    connection = get_connection()
    cursor = connection.cursor()

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

            remaining = max(
                1,
                int(
                    AD_COOLDOWN_SECONDS - elapsed
                )
            )

            return {
                "success": False,
                "message": "Please wait before watching another ad.",
                "remaining_seconds": remaining
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
        "balance": user["balance"],
        "ads_watched": user["ads_watched"]
    }

except HTTPException:

    if connection:
        connection.rollback()

    raise

except Exception as error:

    if connection:
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

    if cursor:
        cursor.close()

    if connection:
        connection.close()
```

@app.get("/referrals/{telegram_id}")
def get_referrals(telegram_id: int):

```
connection = None
cursor = None

try:

    connection = get_connection()
    cursor = connection.cursor()

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
            ON u.telegram_id = r.referred_user_id
        WHERE r.referrer_id = %s
        ORDER BY r.id DESC
        """,
        (telegram_id,)
    )

    referral_users = cursor.fetchall()

    return {
        "success": True,
        "referrals": user["referrals"] or 0,
        "referrer_reward": REFERRER_REWARD,
        "referred_user_reward": REFERRED_USER_REWARD,
        "users": [
            dict(item)
            for item in referral_users
        ]
    }

finally:

    if cursor:
        cursor.close()

    if connection:
        connection.close()
```

@app.get("/leaderboard")
def leaderboard(limit: int = 20):

```
limit = max(1, min(limit, 100))

connection = None
cursor = None

try:

    connection = get_connection()
    cursor = connection.cursor()

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

    if cursor:
        cursor.close()

    if connection:
        connection.close()
```

@app.get("/wallet")
def get_wallet(
init_data: str = Query(...)
):

```
telegram_user = get_telegram_user(
    init_data
)

telegram_id = telegram_user["id"]

connection = None
cursor = None

try:

    connection = get_connection()
    cursor = connection.cursor()

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

    if cursor:
        cursor.close()

    if connection:
        connection.close()
```

@app.post("/wallet")
def save_wallet(wallet: WalletUpdate):

```
telegram_user = get_telegram_user(
    wallet.init_data
)

telegram_id = telegram_user["id"]

wallet_address = wallet.wallet_address.strip()

if not wallet_address:

    raise HTTPException(
        status_code=400,
        detail="Wallet address is required"
    )

valid_prefix = (
    wallet_address.startswith("EQ")
    or wallet_address.startswith("UQ")
    or wallet_address.startswith("kQ")
    or wallet_address.startswith("0:")
)

if not valid_prefix or len(wallet_address) < 20:

    raise HTTPException(
        status_code=400,
        detail="Invalid TON wallet address"
    )

connection = None
cursor = None

try:

    connection = get_connection()
    cursor = connection.cursor()

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

    if connection:
        connection.rollback()

    raise

except Exception as error:

    if connection:
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

    if cursor:
        cursor.close()

    if connection:
        connection.close()
```

@app.delete("/wallet")
def remove_wallet(auth: TelegramAuth):

```
telegram_user = get_telegram_user(
    auth.init_data
)

telegram_id = telegram_user["id"]

connection = None
cursor = None

try:

    connection = get_connection()
    cursor = connection.cursor()

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

    if connection:
        connection.rollback()

    raise

except Exception as error:

    if connection:
        connection.rollback()

    print(
        "Wallet remove error:",
        error
    )

    raise HTTPException(
        status_code=500,
        detail="Unable to remove wallet"
    )

finally:

    if cursor:
        cursor.close()

    if connection:
        connection.close()
```
