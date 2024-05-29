from os import getenv

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = getenv('TELEGRAM_BOT_TOKEN')

DATABASE_CONNECTION_STRING = getenv('DATABASE_CONNECTION_STRING')

SECRET_KEY = getenv("SECRET_KEY")

API_HASH = getenv('API_HASH')

API_ID = int(getenv('API_ID'))

CLIENT_SESSION_PATH = getenv('CLIENT_SESSION_PATH', './app/bot_init')
