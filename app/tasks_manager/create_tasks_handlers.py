from pyrogram import filters, Client, types
from app.auth_manager import auth_controller
from app.bot_init.bot_init import client_bot
from app.fsm_context.fsm_context import get_fsm_context
from app.root.filters import get_filters
from app.tasks_manager import tasks_controller
from app.tasks_manager.handlers import get_back_buttons, tasks_menu
from app.utils import TelegramUtils


@client_bot.on_callback_query(
    filters.regex("tasks:create_task:") &
    get_filters().message_filter(state="tasks")
)
async def create_task(_: Client, message: types.CallbackQuery) -> None:
    """Handler for creating a new task."""
    owner_telegram_id = int(message.data.split(":")[-1])
    reply_markup = None
    is_owner = auth_controller.check_user_is_owner(
        user_telegram_id=message.from_user.id,
        owner_telegram_id=owner_telegram_id
    )
    if is_owner:
        text_message = (
            "Введите название вашей новой задачи"
        )
        reply_markup = get_back_buttons(owner_telegram_id=owner_telegram_id)
        get_fsm_context().update_state(
            telegram_id=message.from_user.id,
            state="tasks:create:set_name"
        )
    else:
        text_message = (
            "Вы не имеете доступ к данному функционалу"
        )
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    if not is_owner:
        return await tasks_menu(_=_, message=message)


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="tasks:create:set_name")
)
async def create_task_set_name(_: Client, message: types.Message) -> None:
    """Handler for setting the name of the new task."""
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    data['task_name'] = message.text
    get_fsm_context().update_data(telegram_id=message.from_user.id, data=data)
    text_message = (
        "Введите описание вашей новой задачи"
    )
    reply_markup = get_back_buttons(
        owner_telegram_id=data.get('owner_telegram_id')
    )
    get_fsm_context().update_state(
        telegram_id=message.from_user.id,
        state="tasks:create:set_description"
    )
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="tasks:create:set_description")
)
async def create_task_set_description(
    _: Client,
    message: types.Message
) -> None:
    """Handler for setting the description of a new task."""
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    data['task_description'] = message.text
    get_fsm_context().update_data(telegram_id=message.from_user.id, data=data)
    text_message = tasks_controller.get_text_set_time()
    reply_markup = get_back_buttons(
        owner_telegram_id=data.get('owner_telegram_id')
    )
    get_fsm_context().update_state(
        telegram_id=message.from_user.id,
        state="tasks:create:set_start_time"
    )
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="tasks:create:set_start_time")
)
async def create_task_set_start_time(
    _: Client,
    message: types.Message
) -> None:
    """Handler for setting the start time of a new task."""
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    if not tasks_controller.check_valid_date(start_time=message.text):
        text_message = tasks_controller.get_text_set_time(is_error=True)
    else:
        data['task_start_time'] = message.text
        get_fsm_context().update_data(
            telegram_id=message.from_user.id,
            data=data
        )
        text_message = tasks_controller.get_text_set_time(
            start_time=data.get('task_start_time')
        )
        get_fsm_context().update_state(
            telegram_id=message.from_user.id,
            state="tasks:create:set_end_time"
        )
    reply_markup = get_back_buttons(
        owner_telegram_id=data.get('owner_telegram_id')
    )
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="tasks:create:set_end_time")
)
async def create_task_set_end_time(_: Client, message: types.Message) -> None:
    """Handler for setting the completion time of a new task."""
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    is_task_create: bool = False
    reply_markup = None
    if not tasks_controller.check_valid_date(
        start_time=data.get('task_start_time'),
        end_time=message.text.strip()
    ):
        text_message = tasks_controller.get_text_set_time(
            start_time=data.get('task_start_time'),
            is_error=True
        )
        reply_markup = get_back_buttons(
            owner_telegram_id=data.get('owner_telegram_id')
        )
    else:
        start_time = tasks_controller.transform_utc_time(
            time=data.get('task_start_time')
        )
        end_time = tasks_controller.transform_utc_time(
            time=message.text.strip()
        )
        tasks_controller.set_task(
            owner_telegram_id=data.get('owner_telegram_id'),
            start_time=start_time,
            end_time=end_time,
            task_name=data.get('task_name'),
            description=data.get('task_description')
        )
        text_message = "Новая задача упешно создана"
        is_task_create = True
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    if is_task_create:
        await tasks_menu(_=_, message=message)
