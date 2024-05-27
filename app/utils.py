import asyncio

from pyrogram import types

from app.bot_init.bot_init import client_bot
from app.fsm_context.fsm_context import get_fsm_context


class TelegramUtils:
    """
        A utility for interacting with the Telegram API, sending messages and deleting messages.

        Options:
        - message: types.Message | types.CallbackQuery: Telegram message or callback request object.
        - text: str: Message text.
        - chat_ids: list[int] | None: List of chat IDs to which you want to send a message (None by default).
        - reply_markup: types.ReplyKeyboardMarkup | types.InlineKeyboardMarkup | None: Keyboard layout object
          (default None).
        - resize_keyboard: bool: Flag for resizing the keyboard (True by default).

        Methods:
        - send_messages(): Asynchronously sends a message to the specified chats, taking into account the keyboard layout.
        - delete_message(delete_last_messages: bool = False, message_delete_ids: list[int] = None): Asynchronously deletes
          messages from specified chats. Can be used to delete the current message or previous ones.
    """
    def __init__(
            self, message: types.Message | types.CallbackQuery, text: str,
            chat_ids: list[int] | None = None,
            reply_markup: types.ReplyKeyboardMarkup | types.InlineKeyboardMarkup | None = None,
            resize_keyboard: bool = True):

        self.message = message
        self.text = text
        self.chat_ids = chat_ids if chat_ids else [message.from_user.id]
        self.reply_markup = reply_markup
        if isinstance(reply_markup, types.ReplyKeyboardMarkup):
            reply_markup.resize_keyboard = resize_keyboard
        asyncio.run(self.delete_message())

    async def send_messages(self) -> None:
        """Asynchronously sends message(s) to specified chats based on keyboard layout."""
        data = get_fsm_context().get_data(telegram_id=self.message.from_user.id)
        for count, chat_id in enumerate(self.chat_ids):
            message = await client_bot.send_message(
                reply_markup=self.reply_markup,
                chat_id=chat_id,
                text=self.text
            )
            if isinstance(self.reply_markup, types.InlineKeyboardMarkup):
                if not data.get('list_messages_delete_ids'):
                    data["list_messages_delete_ids"] = list()
                data["list_messages_delete_ids"].append(message.id)
        get_fsm_context().update_data(telegram_id=self.message.from_user.id, data=data)

    async def delete_message(
        self,
        delete_last_messages: bool = False,
        message_delete_ids: list[int] = None
    ) -> None:
        """
            Asynchronously deletes messages from specified chats. Can be used to delete the current message
            or previous ones.

            Options:
            - delete_last_messages: bool: Flag for deleting previous messages (default False).
            - message_delete_ids: list[int] | None: List of message IDs to delete (None by default).
        """
        data = get_fsm_context().get_data(telegram_id=self.message.from_user.id)
        if not self.chat_ids:
            return
        if not message_delete_ids and not delete_last_messages:
            message_delete_ids = [self.message.id] \
                if isinstance(self.message, types.Message) else list()
        if data.get('list_messages_delete_ids'):
            message_delete_ids += data.get('list_messages_delete_ids')
            del data["list_messages_delete_ids"]
            get_fsm_context().update_data(
                telegram_id=self.message.from_user.id,
                data=data
            )
        for count, chat_id in enumerate(self.chat_ids):
            await client_bot.delete_messages(
                chat_id=chat_id,
                message_ids=message_delete_ids
            )
