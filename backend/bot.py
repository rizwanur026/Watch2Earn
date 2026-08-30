```python
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
    ContextTypes,
)

from database import get_connection


# ============================================================
# CONFIGURATION
# ============================================================

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


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# DATABASE - GET OR CREATE USER
# ============================================================

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

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()


# ============================================================
# REFERRAL URL
# ============================================================

def get_referral_url(telegram_id):

    username = BOT_USERNAME.lstrip("@")

    return (
        f"https://t.me/{username}"
        f"?start={telegram_id}"
    )


# ============================================================
# START COMMAND
# ============================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user:
        return

    user = update.effective_user

    telegram_id = user.id
    username = user.username
    first_name = user.first_name or "User"

    connection = get_connection()
    cursor = connection.cursor()

    referred_user_rewarded = False
    referrer_rewarded = False

    try:

        # ====================================================
        # CHECK USER
        # ====================================================

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = %s
            """,
            (telegram_id,)
        )

        existing_user = cursor.fetchone()


        # ====================================================
        # NEW USER
        # ====================================================

        if not existing_user:

            # ------------------------------------------------
            # CREATE USER
            # ------------------------------------------------

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

            existing_user = cursor.fetchone()


            # =================================================
            # REFERRAL
            # =================================================

            if context.args:

                referral_code = context.args[0]

                try:

                    referrer_id = int(
                        referral_code
                    )

                except ValueError:

                    referrer_id = None


                # ------------------------------------------------
                # SELF REFERRAL PROTECTION
                # ------------------------------------------------

                if (
                    referrer_id
                    and referrer_id != telegram_id
                ):

                    # --------------------------------------------
                    # CHECK REFERRER
                    # --------------------------------------------

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

                        # ----------------------------------------
                        # CHECK DUPLICATE REFERRAL
                        # ----------------------------------------

                        cursor.execute(
                            """
                            SELECT id
                            FROM referral_rewards
                            WHERE referred_user_id = %s
                            """,
                            (telegram_id,)
                        )

                        already_referred = cursor.fetchone()


                        if not already_referred:

                            # ------------------------------------
                            # SAVE referred_by
                            # ------------------------------------

                            cursor.execute(
                                """
                                UPDATE users
                                SET referred_by = %s
                                WHERE telegram_id = %s
                                """,
                                (
                                    referrer_id,
                                    telegram_id
                                )
                            )


                            # ------------------------------------
                            # REWARD REFERRER
                            # ------------------------------------

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


                            # ------------------------------------
                            # REWARD NEW USER
                            # ------------------------------------

                            cursor.execute(
                                """
                                UPDATE users
                                SET balance = balance + %s
                                WHERE telegram_id = %s
                                """,
                                (
                                    REFERRED_USER_REWARD,
                                    telegram_id
                                )
                            )


                            # ------------------------------------
                            # REFERRER TRANSACTION
                            # ------------------------------------

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


                            # ------------------------------------
                            # NEW USER TRANSACTION
                            # ------------------------------------

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


                            # ------------------------------------
                            # REFERRAL RECORD
                            # ------------------------------------

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
                                    telegram_id,
                                    REFERRER_REWARD
                                )
                            )


                            referred_user_rewarded = True
                            referrer_rewarded = True


        # ====================================================
        # EXISTING USER
        # ====================================================

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


    # ========================================================
    # MAIN BUTTONS
    # ========================================================

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
                "👥 My Referral",
                callback_data="referral"
            )
        ],

        [
            InlineKeyboardButton(
                "💰 My Balance",
                callback_data="balance"
            )
        ]

    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )


    # ========================================================
    # WELCOME MESSAGE
    # ========================================================

    message = (
        f"👋 Welcome to Watch2Earn, {first_name}!\n\n"
        f"💰 Watch ads\n"
        f"🎯 Complete tasks\n"
        f"🎁 Claim daily bonuses\n"
        f"👥 Invite friends\n\n"
        f"Start earning W2E today!"
    )


    if referred_user_rewarded:

        message += (
            f"\n\n🎉 Referral bonus received!\n"
            f"+{REFERRED_USER_REWARD} W2E"
        )


    await update.message.reply_text(
        message,
        reply_markup=reply_markup
    )


# ============================================================
# REFERRAL COMMAND
# ============================================================

async def referrals_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user:
        return

    telegram_id = update.effective_user.id

    referral_url = get_referral_url(
        telegram_id
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                referrals,
                balance
            FROM users
            WHERE telegram_id = %s
            """,
            (telegram_id,)
        )

        user = cursor.fetchone()

        if not user:

            await update.message.reply_text(
                "Please use /start first."
            )

            return

        referrals = user["referrals"] or 0

        await update.message.reply_text(

            "👥 YOUR REFERRAL\n\n"
            f"👤 Friends invited: {referrals}\n"
            f"💰 Reward per friend: {REFERRER_REWARD} W2E\n\n"
            "🔗 Your referral link:\n"
            f"{referral_url}\n\n"
            "Share this link with your friends.\n"
            f"You earn {REFERRER_REWARD} W2E "
            "when a new user joins through your link."

        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# REFERRAL CALLBACK
# ============================================================

async def referral_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    telegram_id = query.from_user.id

    referral_url = get_referral_url(
        telegram_id
    )

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

        referrals = 0

        if user:

            referrals = user["referrals"] or 0


        keyboard = [

            [
                InlineKeyboardButton(
                    "🔗 Open Referral Link",
                    url=referral_url
                )
            ],

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


        await query.message.reply_text(

            "👥 REFERRAL PROGRAM\n\n"
            f"👤 Friends invited: {referrals}\n"
            f"🎁 You earn: {REFERRER_REWARD} W2E\n"
            f"🎁 New user gets: {REFERRED_USER_REWARD} W2E\n\n"
            "🔗 Your personal referral link:\n"
            f"{referral_url}\n\n"
            "Share your link with friends to earn more W2E.",

            reply_markup=reply_markup
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# BALANCE CALLBACK
# ============================================================

async def balance_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    telegram_id = query.from_user.id

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                balance,
                referrals,
                ads_watched
            FROM users
            WHERE telegram_id = %s
            """,
            (telegram_id,)
        )

        user = cursor.fetchone()

        if not user:

            await query.message.reply_text(
                "Please use /start first."
            )

            return


        await query.message.reply_text(

            "💰 YOUR WATCH2EARN BALANCE\n\n"
            f"💵 Balance: {user['balance']} W2E\n"
            f"👥 Referrals: {user['referrals'] or 0}\n"
            f"📺 Ads watched: {user['ads_watched'] or 0}"

        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# HELP
# ============================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "📚 Watch2Earn Help\n\n"
        "/start - Open Watch2Earn\n"
        "/referrals - Get your referral link\n"
        "/help - Show help\n\n"
        "💰 Earn W2E by watching ads.\n"
        "🎯 Complete tasks.\n"
        "🎁 Claim daily bonuses.\n"
        "👥 Invite friends.\n"
        "💳 Connect your TON wallet from the Mini App."

    )


# ============================================================
# MAIN
# ============================================================

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


    # Start
    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )


    # Referral
    application.add_handler(
        CommandHandler(
            "referrals",
            referrals_command
        )
    )


    # Help
    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )


    # Callback buttons
    from telegram.ext import CallbackQueryHandler

    application.add_handler(
        CallbackQueryHandler(
            referral_callback,
            pattern="^referral$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            balance_callback,
            pattern="^balance$"
        )
    )


    logger.info(
        "Watch2Earn bot started"
    )


    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
```
