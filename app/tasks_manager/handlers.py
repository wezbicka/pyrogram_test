from pyrogram import filters, types, Client

from app.auth_manager import auth_controller
from app.bot_init.bot_init import client_bot
from app.fsm_context.fsm_context import get_fsm_context
from app.root.controller import send_message_start
from app.root.filters import get_filters
from app.utils import TelegramUtils


@client_bot.on_callback_query(filters.regex("menu_tasks:") & (
        get_filters().message_filter(state="main_menu") |
        (get_filters().message_filter(state="tasks", is_regex=True))))
@client_bot.on_message(filters.text & filters.regex("Меню просмотра задач"))
async def tasks_menu(
    _: Client,
    message: types.Message | types.CallbackQuery
) -> None:
    """Callback Query функция для отображения меню задач."""
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    reply_markup = None
    if not data.get('owner_telegram_id'):
        text_message = (
            "вы не имеете доступ к данному функционалу"
        )
    else:
        is_owner = auth_controller.check_user_is_owner(
            user_telegram_id=message.from_user.id,
            owner_telegram_id=data.get('owner_telegram_id')
        )
        text_message = (
            "ВНИМАНИЕ!!! ТОЛЬКО ВЛАДЕЛЕЦ АККАУНТА "
            "ИМЕЕТ ВОЗМОЖНОСТЬ СОЗДАВАТЬ НОВЫЕ ЗАДАЧИ;\n"
            "Данное меню позволяет выполнить следующие действия:\n\n"
            "1) Создать новую задачу;\n"
            "2) Посмотреть созданные задачи;\n"
            "3) Редактировать созданные задачи;\n"
        )
        inline_keyboard = list()
        if is_owner:
            inline_keyboard.append([types.InlineKeyboardButton(
                text="Создать новую задачу",
                callback_data=f"tasks:create_task:{data.get('owner_telegram_id')}"
            )])
        inline_keyboard.append([types.InlineKeyboardButton(
            text="Просмотреть созданные задачи",
            callback_data=f"tasks:view_tasks:{data.get('owner_telegram_id')}"
        )])
        inline_keyboard.append([types.InlineKeyboardButton(
            text="Редактировать созданные задачи",
            callback_data=f"tasks:edit_tasks:{data.get('owner_telegram_id')}"
        )])
        inline_keyboard.append([types.InlineKeyboardButton(
            text="Вернуться в главное меню",
            callback_data=f"main_menu:{data.get('owner_telegram_id')}"
        )])
        reply_markup = types.InlineKeyboardMarkup(
            inline_keyboard=inline_keyboard
        )
        state = "tasks"
        get_fsm_context().update_state(
            telegram_id=message.from_user.id,
            state=state
        )
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    if not reply_markup:
        await send_message_start(_=_, message=message)


def get_back_buttons(owner_telegram_id: int) -> types.InlineKeyboardMarkup:
    """
        Returns a keyboard with a "Back" and "Back to Main Menu" button.

        Options:
        - `owner_telegram_id`: ID of the task owner.

        Returns:
        - types.InlineKeyboardMarkup: Keyboard with "Back" and "Back to main menu" buttons.
    """
    inline_keyboard = list()
    inline_keyboard.append([types.InlineKeyboardButton(
        text="Вернуться назад",
        callback_data=f"menu_tasks:{owner_telegram_id}"
    )])
    inline_keyboard.append([types.InlineKeyboardButton(
        text="Вернуться в главное меню",
        callback_data=f"main_menu:{owner_telegram_id}"
    )])
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return reply_markup


def get_back_edit_buttons(owner_telegram_id: int) -> types.InlineKeyboardMarkup:
    """
        Brings back a keyboard with a "Back" and "Back to Main Menu" button for editing tasks.

        Options:
        - `owner_telegram_id`: ID of the task owner.

        Returns:
        - types.InlineKeyboardMarkup: Keyboard with "Back" and "Back to main menu" buttons.
    """
    inline_keyboard = list()
    inline_keyboard.append([types.InlineKeyboardButton(
        text="Вернуться назад",
        callback_data=f"tasks:menu_edit:{owner_telegram_id}"
    )])
    inline_keyboard.append([types.InlineKeyboardButton(
        text="Вернуться в главное меню",
        callback_data=f"main_menu:{owner_telegram_id}"
    )])
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return reply_markup
