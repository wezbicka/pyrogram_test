"""
Setting up and initializing the bot client.

This module contains code to configure and initialize a bot client that uses the Pyrogram library.

Options:
    api_id (int): API identifier provided by Telegram.
    api_hash (str): Secret hash provided by Telegram.
    bot_token (str): Telegram bot token.
    client_bot (Client): Pyrogram bot client object.
"""

from pyrogram import Client
from app import config

api_id = config.API_ID
api_hash = config.API_HASH
bot_token = config.TELEGRAM_BOT_TOKEN
client_bot = Client(
    name=f"{config.CLIENT_SESSION_PATH}/pyrogram_bot",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token
)
