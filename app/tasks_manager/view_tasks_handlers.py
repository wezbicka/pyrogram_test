from pyrogram import filters, Client, types

from app.bot_init.bot_init import client_bot
from app.db.models import UserTasks
from app.fsm_context.fsm_context import get_fsm_context
from app.root.filters import get_filters
from app.tasks_manager import tasks_controller
from app.tasks_manager.handlers import get_back_buttons
from app.utils import TelegramUtils


@client_bot.on_callback_query(
    filters.regex("tasks:view_tasks:") &
    get_filters().message_filter(state="tasks")
)
async def view_tasks(_: Client, message: types.CallbackQuery) -> None:
    """
        Processes the user's request to view tasks depending on the selected option.

        Actions:
        - Retrieve user ID from callback_data.
        - Generate a text message with available options for viewing tasks.
        - Create an inline keyboard with task view options and "Back" button.
        - Send a keyboard message to the user.
        - Update the state of the state machine on "tasks:view".
    """
    owner_telegram_id = int(message.data.split(":")[-1])
    text_message = (
        "В данном меню вы можете:\n\n"
        "1) Просмотреть все действующие задачи\n"
        "2) Просмотреть все выполненные задачи\n"
        "3) Просмотреть все просроченные задачи\n"
        "4) Просмотреть все задачи\n"
    )
    inline_keyboard = list()
    inline_keyboard.append([types.InlineKeyboardButton(
        text="Просмотреть все действующие задачи",
        callback_data=f"tasks:view_current_tasks:{owner_telegram_id}")])
    inline_keyboard.append([types.InlineKeyboardButton(
        text="Просмотреть все выполненные задачи",
        callback_data=f"tasks:view_completed_tasks:{owner_telegram_id}")])
    inline_keyboard.append([types.InlineKeyboardButton(
        text="Просмотреть все просроченные задачи",
        callback_data=f"tasks:view_overdue_tasks:{owner_telegram_id}")])
    inline_keyboard.append([types.InlineKeyboardButton(
        text="Просмотреть все задачи",
        callback_data=f"tasks:view_all_tasks:{owner_telegram_id}")])
    inline_keyboard += (get_back_buttons(
        owner_telegram_id=owner_telegram_id
    )).inline_keyboard
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    get_fsm_context().update_state(
        telegram_id=message.from_user.id,
        state="tasks:view"
    )


@client_bot.on_callback_query(
    filters.regex("tasks:view_current_tasks:") &
    get_filters().message_filter(state="tasks:view")
)
async def get_all_current_tasks(
    _: Client,
    message: types.CallbackQuery
) -> None:
    """
        Processes the user's request to view all current tasks.

        Actions:
        - Retrieves a list of the user's current tasks.
        - Sends a message with information about current tasks.
        - Calls the view_tasks function to return to the task view menu.
    """
    list_user_tasks: list[UserTasks] = tasks_controller.get_all_tasks(
        owner_telegram_id=int(message.data.split(":")[-1]), current_tasks=True)
    await tasks_controller.send_messages_get_all_tasks(
        list_tasks=list_user_tasks,
        message=message
    )
    await view_tasks(_=_, message=message)


@client_bot.on_callback_query(
    filters.regex("tasks:view_completed_tasks:") &
    get_filters().message_filter(state="tasks:view")
)
async def get_all_completed_tasks(
    _: Client,
    message: types.CallbackQuery
) -> None:
    """
        Handle the user's request to view all completed tasks.

        Actions:
        - Retrieves a list of completed user tasks.
        - Sends a message with information about completed tasks.
        - Calls the view_tasks function to return to the task view menu.
    """
    list_user_tasks: list[UserTasks] = tasks_controller.get_all_tasks(
        owner_telegram_id=int(message.data.split(":")[-1]),
        completed_tasks=True
    )
    await tasks_controller.send_messages_get_all_tasks(
        list_tasks=list_user_tasks,
        message=message
    )
    await view_tasks(_=_, message=message)


@client_bot.on_callback_query(
    filters.regex("tasks:view_overdue_tasks:") &
    get_filters().message_filter(state="tasks:view")
)
async def get_all_overdue_tasks(
    _: Client,
    message: types.CallbackQuery
) -> None:
    """
        Handle the user's request to view all overdue tasks.

        Actions:
        - Retrieves a list of user's overdue tasks.
        - Sends a message with information about overdue tasks.
        - Calls the view_tasks function to return to the task view menu.
    """
    list_user_tasks: list[UserTasks] = tasks_controller.get_all_tasks(
        owner_telegram_id=int(message.data.split(":")[-1]), overdue_tasks=True)
    await tasks_controller.send_messages_get_all_tasks(
        list_tasks=list_user_tasks,
        message=message
    )
    await view_tasks(_=_, message=message)


@client_bot.on_callback_query(
    filters.regex("tasks:view_all_tasks:") &
    get_filters().message_filter(state="tasks:view")
)
async def get_all_tasks(_: Client, message: types.CallbackQuery) -> None:
    """
        Processes the user's request to view all tasks.

        Actions:
        - Retrieves a list of all user tasks.
        - Sends a message with information about all tasks.
        - Calls the view_tasks function to return to the task view menu.
    """
    list_user_tasks: list[UserTasks] = tasks_controller.get_all_tasks(
        owner_telegram_id=int(message.data.split(":")[-1]))
    await tasks_controller.send_messages_get_all_tasks(
        list_tasks=list_user_tasks,
        message=message
    )
    await view_tasks(_=_, message=message)
