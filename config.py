import os
from dotenv import load_dotenv

print("CONFIG PATH:", os.getcwd())

load_dotenv()

print("ENV KEY:", os.getenv("VELORA_API_KEY"))

BOT_TOKEN = os.getenv("VELORA_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

CHANNEL_USERNAME = "@Velora_news"
CHANNEL_LINK = "https://t.me/Velora_news"

API_URL = os.getenv("VELORA_API_URL", "https://getvelora.xyz").rstrip("/")
API_KEY = os.getenv("VELORA_API_KEY", "")






# import os
# from dotenv import load_dotenv

# load_dotenv()

# BOT_TOKEN = os.getenv("VELORA_BOT_TOKEN")
# ADMIN_ID = int(os.getenv("ADMIN_ID"))

# CHANNEL_USERNAME = "@Velora_news"
# CHANNEL_LINK = "https://t.me/Velora_news"

# # VELORA API (WireGuard)
# API_URL = os.getenv("VELORA_API_URL", "https://getvelora.xyz").rstrip("/")
# API_KEY = os.getenv("VELORA_API_KEY", "")
