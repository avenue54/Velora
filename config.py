import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("VELORA_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Канал, на который нужно подписаться при /start
CHANNEL_USERNAME = "@Velora_news"
CHANNEL_LINK = "https://t.me/Velora_news"
