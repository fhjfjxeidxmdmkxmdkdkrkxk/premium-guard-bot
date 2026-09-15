import os
import logging

from telegram import Update
from telegram.ext import Application, ChatJoinRequestHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# जिन Admin IDs को Premium होने पर भी कभी ban नहीं करना है
# Render में ऐसे डालेंगे:
# ADMIN_IDS=123456789,987654321
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}


async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request

    if not request:
        return

    chat_id = request.chat.id
    user = request.from_user
    user_id = user.id

    logging.info(
        "Join request: %s | ID: %s | Premium: %s",
        user.full_name,
        user_id,
        user.is_premium
    )

    # 1️⃣ Whitelisted Admin → हमेशा ACCEPT
    if user_id in ADMIN_IDS:
        await context.bot.approve_chat_join_request(
            chat_id=chat_id,
            user_id=user_id
        )

        logging.info("Admin approved: %s", user_id)
        return

    # 2️⃣ Premium लेकिन Admin नहीं → DECLINE + BAN
    if user.is_premium:
        try:
            # पहले join request decline
            await context.bot.decline_chat_join_request(
                chat_id=chat_id,
                user_id=user_id
            )

            # फिर channel से ban
            await context.bot.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id
            )

            logging.info("Premium user banned: %s", user_id)

        except Exception as e:
            logging.error(
                "Premium ban failed for %s: %s",
                user_id,
                e
            )

        return

    # 3️⃣ Normal user → ACCEPT
    try:
        await context.bot.approve_chat_join_request(
            chat_id=chat_id,
            user_id=user_id
        )

        logging.info("Normal user approved: %s", user_id)

    except Exception as e:
        logging.error(
            "Approval failed for %s: %s",
            user_id,
            e
        )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        ChatJoinRequestHandler(join_request)
    )

    logging.info("Premium Guard Bot started")

    app.run_polling(
        allowed_updates=["chat_join_request"]
    )


if __name__ == "__main__":
    main()
