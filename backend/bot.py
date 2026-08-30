import os
import json
import urllib.request
import urllib.parse

from database import get_connection


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

REFERRER_REWARD = 100
REFERRED_USER_REWARD = 50


def telegram_api(method, data):

    if not BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured"
        )

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/{method}"
    )

    encoded = urllib.parse.urlencode(
        data
    ).encode()

    request = urllib.request.Request(
        url,
        data=encoded,
        method="POST"
    )

    with urllib.request.urlopen(
        request,
        timeout=15
    ) as response:

        return json.loads(
            response.read().decode()
        )


def send_message(
    chat_id,
    text,
    reply_markup=None
):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup:

        data["reply_markup"] = json.dumps(
            reply_markup
        )

    return telegram_api(
        "sendMessage",
        data
    )


def create_user(
    telegram_id,
    username=None,
    first_name=None
):

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

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()


def process_referral(
    new_user_id,
    referrer_id
):

    if not referrer_id:
        return False

    if new_user_id == referrer_id:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # New user
        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = %s
            """,
            (new_user_id,)
        )

        new_user = cursor.fetchone()

        if not new_user:
            return False

        # Referrer
        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = %s
            """,
            (referrer_id,)
        )

        referrer = cursor.fetchone()

        if not referrer:
            return False

        # Already referred
        if new_user["referred_by"]:

            return False

        # Check existing referral reward
        cursor.execute(
            """
            SELECT id
            FROM referral_rewards
            WHERE referred_user_id = %s
            """,
            (new_user_id,)
        )

        existing = cursor.fetchone()

        if existing:
            return False

        # Save referrer
        cursor.execute(
            """
            UPDATE users
            SET referred_by = %s,
                balance = balance + %s
            WHERE telegram_id = %s
            """,
            (
                referrer_id,
                REFERRED_USER_REWARD,
                new_user_id
            )
        )

        # Reward referrer
        cursor.execute(
            """
            UPDATE users
            SET referrals = referrals + 1,
                balance = balance + %s
            WHERE telegram_id = %s
            """,
            (
                REFERRER_REWARD,
                referrer_id
            )
        )

        # New user transaction
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
                new_user_id,
                "referral_join",
                REFERRED_USER_REWARD
            )
        )

        # Referrer transaction
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
                referrer_id,
                "referral",
                REFERRER_REWARD
            )
        )

        # Referral record
        cursor.execute(
            """
            INSERT INTO referral_rewards
            (
                referrer_id,
                referred_user_id,
                reward
            )
            VALUES (%s, %s, %s)
            """,
            (
                referrer_id,
                new_user_id,
                REFERRER_REWARD
            )
        )

        connection.commit()

        return True

    except Exception as error:

        connection.rollback()

        print(
            "Referral error:",
            error
        )

        return False

    finally:

        cursor.close()
        connection.close()


def open_app_keyboard():

    if not WEBAPP_URL:
        return None

    return {
        "inline_keyboard": [
            [
                {
                    "text": "🚀 Open Watch2Earn",
                    "web_app": {
                        "url": WEBAPP_URL
                    }
                }
            ]
        ]
    }


def process_start(message):

    chat = message.get("chat", {})
    user = message.get("from", {})

    chat_id = chat.get("id")
    telegram_id = user.get("id")

    if not chat_id or not telegram_id:
        return

    username = user.get("username")
    first_name = user.get("first_name", "User")

    create_user(
        telegram_id,
        username,
        first_name
    )

    text = message.get("text", "")

    parts = text.split(maxsplit=1)

    referral_id = None

    if len(parts) == 2:

        payload = parts[1].strip()

        if payload.isdigit():

            referral_id = int(payload)

    if referral_id:

        rewarded = process_referral(
            telegram_id,
            referral_id
        )

        if rewarded:

            send_message(
                chat_id,
                (
                    "🎉 Welcome to Watch2Earn!\n\n"
                    f"You received +{REFERRED_USER_REWARD} W2E "
                    "from your referral bonus.\n\n"
                    "Invite more friends and earn together!"
                ),
                open_app_keyboard()
            )

            try:

                send_message(
                    referral_id,
                    (
                        "🎉 New referral joined!\n\n"
                        f"You earned +{REFERRER_REWARD} W2E."
                    )
                )

            except Exception as error:

                print(
                    "Referrer notification error:",
                    error
                )

            return

    send_message(
        chat_id,
        (
            f"👋 Hello {first_name}!\n\n"
            "Welcome to Watch2Earn.\n\n"
            "💰 Watch ads\n"
            "🎯 Complete tasks\n"
            "🎁 Claim daily bonus\n"
            "👥 Invite friends\n"
            "🏆 Climb the leaderboard\n\n"
            "Start earning now!"
        ),
        open_app_keyboard()
    )


def process_help(message):

    chat_id = message.get(
        "chat",
        {}
    ).get("id")

    if not chat_id:
        return

    send_message(
        chat_id,
        (
            "ℹ️ Watch2Earn Help\n\n"
            "Use /start to open the app.\n"
            "Invite friends using your referral link.\n"
            "Complete available tasks to earn W2E."
        ),
        open_app_keyboard()
    )


def process_update(update):

    message = update.get("message")

    if not message:
        return {
            "processed": False
        }

    text = message.get(
        "text",
        ""
    )

    if text.startswith("/start"):

        process_start(message)

        return {
            "processed": True,
            "type": "start"
        }

    if text.startswith("/help"):

        process_help(message)

        return {
            "processed": True,
            "type": "help"
        }

    return {
        "processed": False
    }


def set_webhook():

    if not BOT_TOKEN:
        print(
            "TELEGRAM_BOT_TOKEN is missing"
        )
        return

    if not WEBAPP_URL:
        print(
            "WEBAPP_URL is missing"
        )
        return

    webhook_url = (
        WEBAPP_URL.rstrip("/")
        + "/telegram/webhook"
    )

    try:

        result = telegram_api(
            "setWebhook",
            {
                "url": webhook_url
            }
        )

        print(
            "Telegram webhook:",
            result
        )

    except Exception as error:

        print(
            "Webhook setup error:",
            error
        )


if __name__ == "__main__":

    set_webhook()
