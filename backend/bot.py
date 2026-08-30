import os
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from database import get_connection


# =========================
# Configuration
# =========================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

WEB_APP_URL = os.getenv(
    "WEB_APP_URL",
    "https://rizwanur026.github.io/Watch2Earn/"
)

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "Watch2EarnBot"
)

REFERRER_REWARD = 100
REFERRED_USER_REWARD = 50


# =========================
# Logging
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# =========================
# Referral Link
# =========================

def get_referral_link(telegram_id):
    return (
        f"https://t.me/{BOT_USERNAME}"
        f"?start={telegram_id}"
    )


# =========================
# Start Command
# =========================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user or not update.message:
        return

    user = update.effective_user

    telegram_id = user.id
    username = user.username
    first_name = user.first_name

    connection = get_connection()
    cursor = connection.cursor()

    referral_success = False

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
        # NEW USER
        # =========================

        if not existing_user:

            referrer_id = None

            # Get referral parameter
            if context.args:

                try:

                    possible_referrer = int(
                        context.args[0]
                    )

                    # Self referral protection
                    if possible_referrer != telegram_id:

                        referrer_id = possible_referrer

                except ValueError:

                    referrer_id = None


            # =========================
            # Check Referrer
            # =========================

            if referrer_id:

                cursor.execute(
                    """
                    SELECT telegram_id
                    FROM users
                    WHERE telegram_id = %s
                    """,
                    (referrer_id,)
                )

                referrer = cursor.fetchone()

                if not referrer:

                    referrer_id = None


            # =========================
            # Create User
            # =========================

            initial_balance = (
                REFERRED_USER_REWARD
                if referrer_id
                else 0
            )

            cursor.execute(
                """
                INSERT INTO users
                (
                    telegram_id,
                    username,
                    first_name,
                    balance,
                    referrals,
                    ads_watched,
                    referred_by
                )
                VALUES (%s, %s, %s, %s, 0, 0, %s)
                RETURNING *
                """,
                (
                    telegram_id,
                    username,
                    first_name,
                    initial_balance,
                    referrer_id
                )
            )

            cursor.fetchone()


            # =========================
            # Referral Rewards
            # =========================

            if referrer_id:

                # Reward new user
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
                        "referral_bonus",
                        REFERRED_USER_REWARD
                    )
                )


                # Reward referrer
                cursor.execute(
                    """
                    UPDATE users
                    SET balance = balance + %s,
                        referrals = referrals + 1
                    WHERE telegram_id = %s
                    """,
                    (
                        REFERRER_REWARD,
                        referrer_id
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
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        referrer_id,
                        telegram_id,
                        REFERRER_REWARD
                    )
                )

                referral_success = True


            connection.commit()


        # =========================
        # EXISTING USER
        # =========================

        else:

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
    # Main Buttons
    # =========================

    keyboard = [

        [
            InlineKeyboardButton(
                "🚀 Open Watch2Earn",
                web_app=WebAppInfo(
                    url=WEB_APP_URL
                )
            )
        ],

        [
            InlineKeyboardButton(
                "👥 Invite & Earn",
                callback_data="referral"
            )
        ]

    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )


    message = (
        f"👋 Welcome to Watch2Earn, "
        f"{first_name}!\n\n"
        f"💰 Watch ads\n"
        f"🎯 Complete tasks\n"
        f"🎁 Claim daily bonuses\n"
        f"👥 Invite friends\n\n"
        f"Start earning W2E today!"
    )


    if referral_success:

        message += (
            "\n\n🎉 Referral bonus received!"
            f"\n💰 You received +{REFERRED_USER_REWARD} W2E"
        )


    await update.message.reply_text(
        message,
        reply_markup=reply_markup
    )


# =========================
# Referral Command
# =========================

async def referral_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user or not update.message:
        return

    telegram_id = update.effective_user.id

    referral_link = get_referral_link(
        telegram_id
    )

    await update.message.reply_text(

        "👥 Invite & Earn\n\n"
        f"🎁 Friend gets +{REFERRED_USER_REWARD} W2E\n"
        f"💰 You get +{REFERRER_REWARD} W2E\n\n"
        "🔗 Your referral link:\n"
        f"{referral_link}\n\n"
        "Share this link with your friends!"

    )


# =========================
# Referral Button
# =========================

async def referral_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    telegram_id = query.from_user.id

    referral_link = get_referral_link(
        telegram_id
    )

    await query.message.reply_text(

        "👥 Invite & Earn\n\n"
        f"🎁 Friend gets +{REFERRED_USER_REWARD} W2E\n"
        f"💰 You get +{REFERRER_REWARD} W2E\n\n"
        "🔗 Your referral link:\n"
        f"{referral_link}\n\n"
        "Share this link with your friends!"

    )


# =========================
# Help
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    await update.message.reply_text(

        "Watch2Earn Help\n\n"
        "/start - Open Watch2Earn\n"
        "/referral - Get referral link\n"
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


    # Commands
    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    application.add_handler(
        CommandHandler(
            "referral",
            referral_command
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )


    # Referral button
    application.add_handler(
        CallbackQueryHandler(
            referral_button,
            pattern="^referral$"
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
