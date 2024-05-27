"""
Module for sending the bot's start message.

This module contains code to send the bot's start message depending on the user's state.

Options:
    menu_owner_keyboard (list): Keyboard for the account owner.
    menu_not_owner_keyboard (list): Keyboard for non-account owner.
"""

from pyrogram import Client, types

from app.auth_manager import auth_controller
from app.db.models import Users
from app.fsm_context.fsm_context import get_fsm_context
from app.utils import TelegramUtils

menu_owner_keyboard = [
    [types.KeyboardButton(text="Меню просмотра задач")],
    [types.KeyboardButton(text="Изменение настроек")],
    [
        types.KeyboardButton(text="Выйти с аккаунта"),
        types.KeyboardButton(text="Удалить аккаунт")
    ]
]
menu_not_owner_keyboard = [
    [types.KeyboardButton(text="Меню просмотра задач")],
    [types.KeyboardButton(text="Выйти с аккаунта")]
]


async def send_message_start(
    _: Client,
    message: types.Message | types.CallbackQuery,
    owner_telegram_id: int = None
) -> None:
    """Send a bot start message depending on the user's state."""
    keyboard = list()
    if isinstance(message, types.CallbackQuery):
        owner_telegram_id = int(message.data.split(":")[-1])
    else:
        state_telegram_id = get_fsm_context().get_data(
            telegram_id=message.from_user.id
        ).get('telegram_id')
        owner_telegram_id = (
            owner_telegram_id if owner_telegram_id else state_telegram_id if
            state_telegram_id else message.from_user.id)
    data = dict()
    data["list_messages_delete_ids"] = get_fsm_context().get_data(
        telegram_id=message.from_user.id).get('list_messages_delete_ids')
    get_fsm_context().clear(telegram_id=message.from_user.id)
    user: Users | None = auth_controller.get_user(owner_telegram_id=owner_telegram_id)
    if not user or not user.is_login:
        text_message = (
            f"Привет {message.from_user.first_name}.\n\n"
            "Для продолжения работы с данным ботом,\n"
            f"{('пройдите регистрацию, нажав на кнопку \'Регистрация\', или\n' if not user else '')}"
            "пройдите авторизацию, нажав на кнопку 'Авторизация'"
        )
        keyboard.append([types.KeyboardButton(text="Авторизация")])
        if not user:
            keyboard.append([types.KeyboardButton(text="Регистрация")])
        else:
            keyboard.append([types.KeyboardButton(text="Удалить аккаунт")])
        reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard)
        state = "registration_authorization"
    else:
        is_owner = auth_controller.check_user_is_owner(
            user_telegram_id=message.from_user.id,
            owner_telegram_id=owner_telegram_id
        )
        text_message = (
            f"Был выполнен вход {('не ' if not is_owner else '')}из кабинета владельца!!!\n"
            f"Привет, {user.username}.\n\n"
            "Ты находишься в главном меню приложения;\n"
            "Для продолжения работы с ботом, нажмите на нижние кнопки")
        keyboard = menu_owner_keyboard if is_owner else menu_not_owner_keyboard
        reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard)
        state = "main_menu"
        data["owner_telegram_id"] = int(owner_telegram_id)
    get_fsm_context().update_data(telegram_id=message.from_user.id, data=data)
    get_fsm_context().update_state(telegram_id=message.from_user.id, state=state)
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
