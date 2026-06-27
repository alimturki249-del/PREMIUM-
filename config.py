import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "7666572782:AAERYfPULn-ceQYzl6zr318Tf17lbyAqUDM")
ADMIN_ID = int(123456789os.getenv("ADMIN_ID", "8445317010"))
DB_PATH = os.getenv("DB_PATH", "subscription_bot.db")
