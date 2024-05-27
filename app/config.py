from os import getenv

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = getenv('TELEGRAM_BOT_TOKEN', '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11')

DATABASE_CONNECTION_STRING = getenv(
    'DATABASE_CONNECTION_STRING',
    'postgresql://postgres:postgres@db:5432/pyrogram_db'
)

SECRET_KEY = getenv("SECRET_KEY", "Nici5kgdDugUeddUQk4Vehclq1QYoZW4oO7uVguCnlU=")

API_HASH = getenv('API_HASH', '0123456789abcdef0123456789abcdef')

API_ID = int(getenv('API_ID', '12345678'))

CLIENT_SESSION_PATH = getenv('CLIENT_SESSION_PATH', './app/bot_init')
