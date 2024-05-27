from pyrogram import types, filters, Client

from app.auth_manager import auth_controller
from app.bot_init.bot_init import client_bot
from app.db.models import UserTasks
from app.fsm_context.fsm_context import get_fsm_context
from app.root.filters import get_filters
from app.tasks_manager import tasks_controller
from app.tasks_manager.handlers import get_back_edit_buttons, \
    get_back_buttons, tasks_menu
from app.utils import TelegramUtils


@client_bot.on_callback_query(filters.regex("tasks:edit_tasks:") & get_filters().message_filter(state="tasks"))
async def edit_tasks(_: Client, message: types.CallbackQuery | types.Message) -> None:
    """Handler for the /edit_tasks command or the task edit button in the menu."""
    data: dict = get_fsm_context().get_data(telegram_id=message.from_user.id)
    owner_telegram_id = (int(message.data.split(":")[-1])
                         if isinstance(message, types.CallbackQuery) and message.data.split(":")[-1].isdigit()
                         else data.get('owner_telegram_id'))
    list_user_tasks: list[UserTasks] = tasks_controller.get_all_tasks(
        owner_telegram_id=owner_telegram_id
    )
    reply_markup = None
    if not list_user_tasks:
        text_message = (
            "У вас отсутствуют созданные задачи"
        )
    else:
        list_ids_tasks: list[int] = [x.id_task for x in list_user_tasks]
        if not data.get('editor_task_pagination'):
            data['editor_task_pagination'] = 0
        data['editor_task_list_ids'] = list_ids_tasks
        get_fsm_context().update_data(telegram_id=message.from_user.id, data=data)
        pagination = data.get("editor_task_pagination")
        button_previous = types.InlineKeyboardButton(
            text="Предыдущие SKU",
            callback_data=f"tasks:edit_task:button:previous"
        )
        button_next = types.InlineKeyboardButton(
            text="Следующие SKU",
            callback_data=f"tasks:edit_task:button:next"
        )
        button_start = types.InlineKeyboardButton(
            text="Перейти в начало",
            callback_data=f"tasks:edit_task:button:start"
        )
        button_end = types.InlineKeyboardButton(
            text="Перейти в конец",
            callback_data=f"tasks:edit_task:button:end"
        )
        button_ids = [list_ids_tasks[x:x + 2] for x in range(pagination, pagination + 10, 2)]
        inline_keyboard = [
            [types.InlineKeyboardButton(
                text=str(x),
                callback_data=f"tasks:edit_task:id_task:{list_ids_tasks[pagination+count*2+num]}"
                    f":{owner_telegram_id}") for num, x in enumerate(y)
            ] for count, y in enumerate(button_ids)
        ]
        inline_keyboard.append([button_previous, button_next] if pagination and pagination + 10 < len(
            list_ids_tasks) else [button_previous] if pagination else [button_next]
            if pagination + 10 < len(list_ids_tasks) else [])
        inline_keyboard.append([button_start, button_end])
        inline_keyboard += get_back_buttons(owner_telegram_id=owner_telegram_id).inline_keyboard
        text_message = (
            "Введите номер вашей задачи, или выберите ее из списка доступных вам"
        )
        reply_markup = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
        get_fsm_context().update_state(telegram_id=message.from_user.id, state="tasks:edit")
    telegram_utils = TelegramUtils(text=text_message, reply_markup=reply_markup, message=message)
    await telegram_utils.send_messages()
    if not list_user_tasks:
        await tasks_menu(_=_, message=message)


@client_bot.on_callback_query(
    filters.regex("tasks:edit_task:button:") & get_filters().message_filter(state="tasks:edit"))
async def pagination_button(_: Client, message: types.CallbackQuery) -> None:
    """Handler for pagination buttons when selecting a task for editing."""
    data: dict = get_fsm_context().get_data(telegram_id=message.from_user.id)
    data["editor_task_pagination"] = (
        data.get("editor_task_pagination") - 10 if message.data == "tasks:edit_task:button:previous"
        else data.get("editor_task_pagination") + 10 if message.data == "tasks:edit_task:button:next"
        else 0 if message.data == "tasks:edit_task:button:start" else
        len(data.get("editor_task_list_ids")) - len(data.get("editor_task_list_ids")) % 10)
    get_fsm_context().update_data(telegram_id=message.from_user.id, data=data)
    await edit_tasks(_=_, message=message)


@client_bot.on_message(filters.text & get_filters().message_filter(state="tasks:edit"))
@client_bot.on_callback_query(
    filters.regex("tasks:edit_task:id_task:") & get_filters().message_filter(state="tasks:edit"))
async def choice_task(_: Client, message: types.Message | types.CallbackQuery) -> None:
    """Handler for selecting a task for editing."""
    data: dict = get_fsm_context().get_data(telegram_id=message.from_user.id)
    if isinstance(message, types.Message):
        owner_telegram_id = int(data.get('owner_telegram_id'))
        id_task = message.text.strip()
    else:
        owner_telegram_id = int(message.data.split(":")[-1])
        id_task = message.data.split(":")[-2]
    reply_markup = None
    if not id_task.isdigit():
        text_message = (
            "Неверный формат ввода данных. Попробуйте отправить номер задачи заново"
        )
    else:
        id_task = int(id_task)
        task = tasks_controller.get_task_by_id(
            id_task=id_task,
            owner_telegram_id=owner_telegram_id
        )
        if not task:
            text_message = (
                "Данная задача не была найдена в базе данных. Попробуйте отправить номер задачи заново"
            )
        else:
            data['editor_task_id'] = id_task
            get_fsm_context().update_data(
                telegram_id=message.from_user.id,
                data=data
            )
            is_owner: bool = auth_controller.check_user_is_owner(
                user_telegram_id=message.from_user.id, owner_telegram_id=owner_telegram_id)
            text_message, inline_keyboard = create_text_and_buttons_edit(
                owner_telegram_id=owner_telegram_id, is_owner=is_owner)
            reply_markup = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
            get_fsm_context().update_state(
                telegram_id=message.from_user.id,
                state="tasks:edit:edit_task"
            )
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    if get_fsm_context().get_state(telegram_id=message.from_user.id) != "tasks:edit:edit_task":
        await edit_tasks(_=_, message=message)


@client_bot.on_callback_query(
    filters.regex("tasks:menu_edit") &
    get_filters().message_filter(state="tasks:edit", is_regex=True)
)
async def call_menu_editor(_: Client, message: types.Message | types.CallbackQuery) -> None:
    """Handler for calling the task editing menu."""
    data: dict = get_fsm_context().get_data(telegram_id=message.from_user.id)
    if isinstance(message, types.Message):
        owner_telegram_id = int(data.get('owner_telegram_id'))
    else:
        owner_telegram_id = int(message.data.split(":")[-1])
    is_owner: bool = auth_controller.check_user_is_owner(
        user_telegram_id=message.from_user.id,
        owner_telegram_id=owner_telegram_id
    )
    text_message, inline_keyboard = create_text_and_buttons_edit(
        owner_telegram_id=owner_telegram_id, is_owner=is_owner)
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    get_fsm_context().update_state(
        telegram_id=message.from_user.id,
        state="tasks:edit:edit_task"
    )


@client_bot.on_callback_query(
    filters.regex("tasks:edit_task:view_task:") &
    get_filters().message_filter(state="tasks:edit:edit_task")
)
async def update_status_task(_: Client, message: types.CallbackQuery) -> None:
    """Handler for updating the task status when editing."""
    data: dict = get_fsm_context().get_data(telegram_id=message.from_user.id)
    owner_telegram_id = int(message.data.split(":")[-1])
    id_task = data.get('editor_task_id')
    task = tasks_controller.get_task_by_id(
        owner_telegram_id=owner_telegram_id,
        id_task=id_task
    )
    await tasks_controller.send_messages_get_all_tasks(
        list_tasks=[task],
        message=message
    )
    await call_menu_editor(_=_, message=message)


@client_bot.on_callback_query(
    filters.regex("tasks:edit_task:edit_status:") &
    get_filters().message_filter(state="tasks:edit:edit_task")
)
async def update_status_task(_: Client, message: types.CallbackQuery) -> None:
    """Handler for updating the task status (completed/not completed) when editing."""
    data: dict = get_fsm_context().get_data(telegram_id=message.from_user.id)
    owner_telegram_id = int(message.data.split(":")[-1])
    id_task = data.get('editor_task_id')
    status = tasks_controller.update_task_completion(
        owner_telegram_id=owner_telegram_id,
        id_task=id_task
    )
    text_message = (
        f"Статут задания с номером {id_task} успешно изменен на "
        f"{'\'Завершена\'' if status else '\'Не завершена\''}"
    )
    telegram_utils = TelegramUtils(text=text_message, message=message)
    await telegram_utils.send_messages()
    await call_menu_editor(_=_, message=message)


@client_bot.on_callback_query(
    filters.regex("tasks:edit_task:edit_name:") &
    get_filters().message_filter(state="tasks:edit:edit_task")
)
async def update_name_task(_: Client, message: types.CallbackQuery) -> None:
    """Handler for changing the task name when editing."""
    text_message = "Введите новое название вашего задания"
    await call_send_state(
        message=message,
        state="tasks:edit:edit_task:set_name",
        text_message=text_message
    )


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="tasks:edit:edit_task:set_name")
)
async def set_task_name(_: Client, message: types.Message) -> None:
    """Handler for setting a new task name when editing."""
    data: dict = get_fsm_context().get_data(telegram_id=message.from_user.id)
    tasks_controller.update_task_name(
        id_task=data.get('editor_task_id'),
        owner_telegram_id=data.get('owner_telegram_id'),
        task_name=message.text
    )
    text_message = (
        f"Название задачи под номером {data.get('editor_task_id')} "
        f"было успешно изменено на {message.text}"
    )
    telegram_utils = TelegramUtils(text=text_message, message=message)
    await telegram_utils.send_messages()
    await call_menu_editor(_=_, message=message)


@client_bot.on_callback_query(
    filters.regex("tasks:edit_task:edit_desc:") &
    get_filters().message_filter(state="tasks:edit:edit_task")
)
async def update_description_task(_: Client, message: types.CallbackQuery) -> None:
    """Handler for changing the task description when editing."""
    text_message = "Введите новое описание вашего задания"
    await call_send_state(
        message=message,
        state="tasks:edit:edit_task:set_description",
        text_message=text_message
    )


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="tasks:edit:edit_task:set_description")
)
async def set_description_task(_: Client, message: types.Message) -> None:
    """Handler for setting a new task description when editing."""
    data: dict = get_fsm_context().get_data(telegram_id=message.from_user.id)
    tasks_controller.update_task_description(
        id_task=data.get('editor_task_id'),
        owner_telegram_id=data.get('owner_telegram_id'),
        description=message.text
    )
    text_message = (
        f"Описание задачи под номером {data.get('editor_task_id')} "
        f"было успешно изменено на:\n{message.text}"
    )
    telegram_utils = TelegramUtils(text=text_message, message=message)
    await telegram_utils.send_messages()
    await call_menu_editor(_=_, message=message)


@client_bot.on_callback_query(
    filters.regex("tasks:edit_task:edit_start:") &
    get_filters().message_filter(state="tasks:edit:edit_task")
)
async def update_start_date_task(_: Client, message: types.CallbackQuery) -> None:
    """Handler for changing the start date of a task when editing."""
    text_message = tasks_controller.get_text_set_time()
    await call_send_state(
        message=message,
        state="tasks:edit:edit_task:set_start_date",
        text_message=text_message
    )


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="tasks:edit:edit_task:set_start_date")
)
async def set_start_date_task(_: Client, message: types.Message) -> None:
    """Handler for setting a new start date and time for a task when editing."""
    data: dict = get_fsm_context().get_data(telegram_id=message.from_user.id)
    if not tasks_controller.check_valid_date(start_time=message.text.strip()):
        text_message = tasks_controller.get_text_set_time(is_error=True)
        return await call_send_state(
            message=message,
            state="tasks:edit:edit_task:set_start_date",
            text_message=text_message
        )
    tasks_controller.update_task_start_time(
        id_task=data.get('editor_task_id'),
        owner_telegram_id=data.get('owner_telegram_id'),
        start_time=message.text.strip()
    )
    text_message = (
        f"Дата старта задачи по Гринвичу была успешно обновлена на {message.text}"
    )
    telegram_utils = TelegramUtils(text=text_message, message=message)
    await telegram_utils.send_messages()
    await call_menu_editor(_=_, message=message)


@client_bot.on_callback_query(
    filters.regex("tasks:edit_task:edit_end:") &
    get_filters().message_filter(state="tasks:edit:edit_task")
)
async def update_end_date_task(_: Client, message: types.CallbackQuery) -> None:
    """Handler for changing the end date and time of a task when editing."""
    data: dict = get_fsm_context().get_data(telegram_id=message.from_user.id)
    task: UserTasks = tasks_controller.get_task_by_id(
        id_task=data.get('editor_task_id'),
        owner_telegram_id=data.get('owner_telegram_id')
    )
    text_message = tasks_controller.get_text_set_time(start_time=task.start_time)
    await call_send_state(
        message=message,
        state="tasks:edit:edit_task:set_end_date",
        text_message=text_message
    )


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="tasks:edit:edit_task:set_end_date")
)
async def set_end_date_task(_: Client, message: types.Message) -> None:
    """Handler for setting a new end date and time for a task when editing."""
    data: dict = get_fsm_context().get_data(telegram_id=message.from_user.id)
    task: UserTasks = tasks_controller.get_task_by_id(
        id_task=data.get('editor_task_id'),
        owner_telegram_id=data.get('owner_telegram_id')
    )
    start_time = task.start_time.strftime(format='%d.%m.%Y %H:%M')
    if not tasks_controller.check_valid_date(
        start_time=start_time,
        end_time=message.text.strip()
    ):
        text_message = tasks_controller.get_text_set_time(is_error=True)
        return await call_send_state(
            message=message,
            state="tasks:edit:edit_task:set_end_date",
            text_message=text_message
        )
    tasks_controller.update_task_end_time(
        id_task=data.get('editor_task_id'),
        owner_telegram_id=data.get('owner_telegram_id'),
        end_time=message.text.strip()
    )
    text_message = (
        f"Дата завершения задачи по Гринвичу была успешно обновлена на {message.text}"
    )
    telegram_utils = TelegramUtils(text=text_message, message=message)
    await telegram_utils.send_messages()
    await call_menu_editor(_=_, message=message)


@client_bot.on_callback_query(
    filters.regex("tasks:edit_task:delete:") &
    get_filters().message_filter(state="tasks:edit:edit_task")
)
async def delete_task(_: Client, message: types.CallbackQuery) -> None:
    """Handler for deleting a task when editing."""
    data: dict = get_fsm_context().get_data(telegram_id=message.from_user.id)
    text_message = (
        f"Вы точно хотите удалить задачу под номером {data.get('editor_task_id')}"
    )
    inline_keyboard = list()
    inline_keyboard.append([
        types.InlineKeyboardButton(
            text="Да",
            callback_data=f"tasks:edit_task:confirm_delete:{data.get('owner_telegram_id')}"
        ),
        types.InlineKeyboardButton(
            text="Нет",
            callback_data=f"tasks:menu_edit:{data.get('owner_telegram_id')}"
        )
    ])
    inline_keyboard.append([types.InlineKeyboardButton(
        text="Вернуться в главное меню",
        callback_data=f"main_menu:{data.get('owner_telegram_id')}"
    )])
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    telegram_utils = TelegramUtils(
        text=text_message,
        message=message,
        reply_markup=reply_markup
    )
    await telegram_utils.send_messages()
    get_fsm_context().update_state(
        telegram_id=message.from_user.id,
        state="tasks:edit:edit_task:delete"
    )


@client_bot.on_callback_query(
    filters.regex("tasks:edit_task:confirm_delete:") &
    get_filters().message_filter(state="tasks:edit:edit_task:delete")
)
async def confirm_delete_task(_: Client, message: types.Message) -> None:
    """Handler for confirming the deletion of a task when editing."""
    data: dict = get_fsm_context().get_data(telegram_id=message.from_user.id)
    tasks_controller.delete_task(
        owner_telegram_id=data.get('owner_telegram_id'),
        id_task=data.get('editor_task_id')
    )
    text_message = (
        f'Задача номер {data.get('editor_task_id')} была успешно удалена'
    )
    telegram_utils = TelegramUtils(text=text_message, message=message)
    await telegram_utils.send_messages()
    await edit_tasks(_=_, message=message)


def create_text_and_buttons_edit(
    owner_telegram_id: int,
    is_owner: bool = False
) -> tuple[str, list[list[types.InlineKeyboardButton]]]:
    """
        Function for creating text and buttons in the task editing menu.

        Options:
        - owner_telegram_id: ID of the task owner
        - is_owner: Flag indicating whether the user is the owner of the task

        Returns: A tuple with text and a list of buttons
    """
    text_message = (
        "В данном меню у вас есть возможность\n\n"
        "1) Просмотреть данныую задачу\n"
        "2) Изменить статус задачи\n"
        "3) Изменить название задачи\n"
        "4) Изменить описание задачи\n"
        "5) Изменить дату и время старта задачи\n"
        "6) Изменить дату и время окончания задачи\n"
        "7) Удалить задачу\n"
    )
    inline_keyboard = list()
    inline_keyboard.append([types.InlineKeyboardButton(
        text="Просмотреть данную задачу",
        callback_data=f"tasks:edit_task:view_task:{owner_telegram_id}"
    )])
    inline_keyboard.append([types.InlineKeyboardButton(
        text="Изменить статус задачи",
        callback_data=f"tasks:edit_task:edit_status:{owner_telegram_id}"
    )])
    if is_owner:
        inline_keyboard.append([types.InlineKeyboardButton(
            text="Изменить название задачи",
            callback_data=f"tasks:edit_task:edit_name:{owner_telegram_id}"
        )])
        inline_keyboard.append([types.InlineKeyboardButton(
            text="Изменить описание задачи",
            callback_data=f"tasks:edit_task:edit_desc:{owner_telegram_id}"
        )])
        inline_keyboard.append([types.InlineKeyboardButton(
            text="Изменить дату и время старта задачи",
            callback_data=f"tasks:edit_task:edit_start:{owner_telegram_id}"
        )])
        inline_keyboard.append([types.InlineKeyboardButton(
            text="Изменить дату и время окончания задачи",
            callback_data=f"tasks:edit_task:edit_end:{owner_telegram_id}"
        )])
        inline_keyboard.append([types.InlineKeyboardButton(
            text="Удалить задачу",
            callback_data=f"tasks:edit_task:delete:{owner_telegram_id}"
        )])
    inline_keyboard += get_back_buttons(
        owner_telegram_id=owner_telegram_id
    ).inline_keyboard
    return text_message, inline_keyboard


async def call_send_state(
    message: types.CallbackQuery | types.Message,
    state: str,
    text_message: str
) -> None:
    """
       Function to call state change and send message with keyboard.

       Options:
       - message: CallbackQuery or Message object
       - state: New state
       - text_message: Message text
    """
    data: dict = get_fsm_context().get_data(
        telegram_id=message.from_user.id
    )
    owner_telegram_id = (
        int(message.data.split(":")[-1] if isinstance(message, types.CallbackQuery) \
            else data.get('owner_telegram_id')))
    reply_markup = get_back_edit_buttons(owner_telegram_id=owner_telegram_id)
    telegram_utils = TelegramUtils(
        text=text_message,
        message=message,
        reply_markup=reply_markup
    )
    await telegram_utils.send_messages()
    get_fsm_context().update_state(
        telegram_id=message.from_user.id,
        state=state
    )
