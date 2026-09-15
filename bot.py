import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    ChatJoinRequestHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# जिन Premium users को कभी ban नहीं करना है
# उदाहरण: ADMIN_IDS=123456789,987654321
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}


async def handle_join_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    request = update.chat_join_request

    if not request:
        return

    user = request.from_user
    chat = request.chat

    user_id = user.id
    name = user.full_name
    username = f"@{user.username}" if user.username else "No username"

    is_premium = bool(user.is_premium)

    logging.info(
        "Join request: %s | %s | Premium=%s",
        name,
        user_id,
        is_premium,
    )

    # 1. Whitelisted admin को हमेशा allow
    if user_id in ADMIN_IDS:
        await context.bot.approve_chat_join_request(
            chat_id=chat.id,
            user_id=user_id
        )

        logging.info(
            "WHITELIST APPROVED: %s (%s)",
            name,
            user_id
        )
        return

    # 2. Premium user -> approve फिर तुरंत ban
    if is_premium:
        try:
            await context.bot.approve_chat_join_request(
                chat_id=chat.id,
                user_id=user_id
            )

            await context.bot.ban_chat_member(
                chat_id=chat.id,
                user_id=user_id
            )

            logging.info(
                "PREMIUM BANNED: %s %s",
                name,
                username
            )

        except Exception:
            logging.exception(
                "Premium user action failed for %s",
                user_id
            )

        return

    # 3. Normal/non-Premium user -> approve
    try:
        await context.bot.approve_chat_join_request(
            chat_id=chat.id,
            user_id=user_id
        )

        logging.info(
            "NORMAL USER APPROVED: %s %s",
            name,
            username
        )

    except Exception:
        logging.exception(
            "Could not approve user %s",
            user_id
        )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        ChatJoinRequestHandler(handle_join_request)
    )

    logging.info("Premium Guard Bot started...")

    app.run_polling(
        allowed_updates=["chat_join_request"]
    )


if __name__ == "__main__":
    main()
