import asyncio
import logging

import nest_asyncio
from pyrogram import idle

from app.bot_init.bot_init import client_bot
from app.fsm_context.fsm_context import fsm_context_init
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Launch the bot.

    Asynchronously initializes the FSM context, launches the bot client, and waits for completion.
    """
    loop = asyncio.get_event_loop()
    run = loop.run_until_complete
    run(fsm_context_init())
    run(client_bot.start())
    logger.info("Client started")
    run(idle())
    logger.info("Client stopped")
    run(client_bot.stop())


nest_asyncio.apply()
asyncio.run(main())
