"""
Premium Telegram Subscription Bot
Entry point — run this file to start the bot.
"""

import telebot
import logging

from config import BOT_TOKEN
from database import init_db
from handlers.admin import register_admin_handlers
from handlers.user import register_user_handlers
from handlers.payments import register_payment_handlers
from handlers.broadcast import register_broadcast_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Initialising database...")
    init_db()

    logger.info("Starting bot...")
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

    # Register all handlers (order matters — most specific first)
    register_payment_handlers(bot)   # payment flow (UTR, screenshot)
    register_admin_handlers(bot)     # admin commands & callbacks
    register_user_handlers(bot)      # /start, plan selection, QR
    register_broadcast_handlers(bot) # (placeholder for future extensions)

    # Fallback for unhandled messages
    @bot.message_handler(func=lambda m: True)
    def fallback(msg):
        bot.send_chat_action(msg.chat.id, "typing")
        bot.send_message(
            msg.chat.id,
            "👋 Use /start to begin or tap the menu below.",
            parse_mode="HTML"
        )

    logger.info("Bot is polling...")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=20)


if __name__ == "__main__":
    main()
