import telebot
from telebot.types import Message, CallbackQuery
from config import ADMIN_ID
from database import get_all_users


def register_broadcast_handlers(bot: telebot.TeleBot):
    """
    Broadcast handlers are fully integrated into admin.py.
    This module is kept for clean project structure and can be
    extended for scheduled broadcasts or templates in the future.
    """
    pass
