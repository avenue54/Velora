import os
from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv("VELORA_BOT_TOKEN")

ADMIN_ID = int(
    os.getenv("ADMIN_ID")
)