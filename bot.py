import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ChatJoinRequestHandler, ContextTypes


# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

VIP_LINK = "https://t.me/+7FcNLyJjaP82NzM1"

# APK का Telegram file_id बाद में यहाँ डालेंगे
APK_FILE_ID = os.getenv("APK_FILE_ID", "").strip()


WELCOME_MESSAGE = """
🎉 WELCOME TO OUR CHANNEL

✅ आपका Join Request Successfully Approved हो गया है।

🔥 VIP Channel में Join करने के लिए नीचे दिए गए Button पर Click करें।

📝 Registration के लिए नीचे दिए गए Button का इस्तेमाल करें।

📱 आपका APK नीचे भेजा गया है।

⚠️ किसी भी अनजान व्यक्ति को अपना OTP, Password या Payment Details शेयर न करें।

❤️ Thank You & Welcome!
"""


# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# =========================
# JOIN REQUEST
# =========================

async def handle_join_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    request = update.chat_join_request

    if not request:
        return

    chat_id = request.chat.id
    user = request.from_user
    user_id = user.id

    logging.info(
        "Join Request | %s | ID=%s | Premium=%s",
        user.full_name,
        user_id,
        user.is_premium
    )

    # =========================
    # PREMIUM USER
    # =========================

    if user.is_premium:

        try:
            # Request reject
            await context.bot.decline_chat_join_request(
                chat_id=chat_id,
                user_id=user_id
            )

            # User ban
            await context.bot.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id
            )

            logging.info(
                "Premium user rejected and banned: %s",
                user_id
            )

        except Exception as error:

            logging.error(
                "Premium ban error %s: %s",
                user_id,
                error
            )

        return

    # =========================
    # NORMAL USER
    # =========================

    try:

        await context.bot.approve_chat_join_request(
            chat_id=chat_id,
            user_id=user_id
        )

        # Buttons
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔥 VIP CHANNEL",
                    url=VIP_LINK
                ),
                InlineKeyboardButton(
                    "📝 REGISTER NOW",
                    url=VIP_LINK
                )
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Personal Welcome DM
        # user_chat_id is supplied with join request
        try:

            await context.bot.send_message(
                chat_id=request.user_chat_id,
                text=WELCOME_MESSAGE,
                reply_markup=reply_markup
            )

            logging.info(
                "Welcome message sent: %s",
                user_id
            )

        except Exception as error:

            logging.warning(
                "Welcome DM failed %s: %s",
                user_id,
                error
            )

        # =========================
        # SEND APK
        # =========================

        if APK_FILE_ID:

            try:

                await context.bot.send_document(
                    chat_id=request.user_chat_id,
                    document=APK_FILE_ID,
                    caption="📱 आपका APK"
                )

                logging.info(
                    "APK sent: %s",
                    user_id
                )

            except Exception as error:

                logging.warning(
                    "APK sending failed %s: %s",
                    user_id,
                    error
                )

        else:

            logging.info(
                "APK_FILE_ID not configured yet."
            )

    except Exception as error:

        logging.error(
            "Normal user approval error %s: %s",
            user_id,
            error
        )


# =========================
# START BOT
# =========================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing"
        )

    app = Application.builder().token(
        BOT_TOKEN
    ).build()

    app.add_handler(
        ChatJoinRequestHandler(
            handle_join_request
        )
    )

    logging.info(
        "Premium Guard Bot started..."
    )

    app.run_polling(
        allowed_updates=["chat_join_request"]
    )


if __name__ == "__main__":
    main()
