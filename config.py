import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# Channel settings
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Database settings
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "menu_bot.db")
