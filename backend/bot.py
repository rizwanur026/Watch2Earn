import os
import logging
import psycopg2

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from database import get_connection


# =========================
# Configuration
# =========================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

WEB_APP_URL = os.getenv(
    "WEB_APP_URL",
    "https://rizwanur026.github.io/IBOY1/"
)

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "Watch2EarnBot"
)


# =========================
# Logging
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# =========================
# Database
# =========================

def get_or_create_user(
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
            return user

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

        return user

    finally:

        cursor.close()
        connection.close()


# =========================
# Start Command
# =========================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user:
        return

    user = update.effective_user

    telegram_id = user.id
    username = user.username
    first_name = user.first_name


    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Check existing user
        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = %s
            """,
            (telegram_id,)
        )

        existing_user = cursor.fetchone()


        # =========================
        # New User
        # =========================

        if not existing_user:

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


            # =========================
            # Referral
            # =========================

            if context.args:

                referral_code = context.args[0]

                try:

                    referrer_id = int(
                        referral_code
                    )

                except ValueError:

                    referrer_id = None


                if (
                    referrer_id
                    and referrer_id != telegram_id
                ):

                    # Check referrer
                    cursor.execute(
                        """
                        SELECT telegram_id
                        FROM users
                        WHERE telegram_id = %s
                        """,
                        (referrer_id,)
                    )

                    referrer = cursor.fetchone()


                    if referrer:

                        referral_reward = 100


                        # Reward referrer
                        cursor.execute(
                            """
                            UPDATE users
                            SET balance = balance + %s,
                                referrals = referrals + 1
                            WHERE telegram_id = %s
                            """,
                            (
                                referral_reward,
                                referrer_id
                            )
                        )


                        # Record reward
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
                                referral_reward
                            )
                        )


                        connection.commit()


        else:

            # Update Telegram profile
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


    except Exception as error:

        connection.rollback()

        logger.error(
            "Start command error: %s",
            error
        )


    finally:

        cursor.close()
        connection.close()


    # =========================
    # Open Mini App
    # =========================

    keyboard = [

        [
            InlineKeyboardButton(
                "🚀 Open Watch2Earn",
                web_app=WebAppInfo(
                    url=WEB_APP_URL
                )
            )
        ]

    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )


    await update.message.reply_text(

        f"👋 Welcome to Watch2Earn, "
        f"{first_name}!\n\n"
        f"💰 Watch ads\n"
        f"🎯 Complete tasks\n"
        f"🎁 Claim daily bonuses\n"
        f"👥 Invite friends\n\n"
        f"Start earning W2E today!",

        reply_markup=reply_markup
    )


# =========================
# Help
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "Watch2Earn Help\n\n"
        "/start - Open Watch2Earn\n"
        "/help - Show help\n\n"
        "Open the Mini App to access "
        "tasks, rewards, referrals and wallet."
    )


# =========================
# Main
# =========================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured"
        )


    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )


    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )


    logger.info(
        "Watch2Earn bot started"
    )


    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
