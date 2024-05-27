from pyrogram import filters, types, Client
from app.auth_manager import auth_controller
from app.auth_manager.password import text_set_password_message, \
    validation_password, encrypt_password, verify_password
from app.bot_init.bot_init import client_bot
from app.fsm_context.fsm_context import get_fsm_context
from app.root.controller import send_message_start
from app.root.filters import get_filters
from app.utils import TelegramUtils


@client_bot.on_callback_query(
    filters.regex("menu_settings:") &
    (get_filters().message_filter(state="main_menu") |
    (get_filters().message_filter(state="settings", is_regex=True)))
)
@client_bot.on_message(filters.text & filters.regex("Изменение настроек"))
async def settings_menu(
    _: Client,
    message: types.Message | types.CallbackQuery
) -> None:
    """Handler for opening the menu for changing user settings."""
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    reply_markup = None
    if not data.get('owner_telegram_id') or not auth_controller.check_user_is_owner(
        user_telegram_id=message.from_user.id,
        owner_telegram_id=data.get('owner_telegram_id')
    ):
        text_message = "Вы не имеете доступ к данному функционалу"
        state = "main_menu"
    else:
        text_message = (
            "Данное меню предназначено для изменения настроек профиля"
        )
        inline_keyboard = list()
        inline_keyboard.append([
            types.InlineKeyboardButton(
                text="Изменить название профиля",
                callback_data=f"settings:update_username:{data.get('owner_telegram_id')}"
            )
        ])
        inline_keyboard.append([
            types.InlineKeyboardButton(
                text="Изменить логин",
                callback_data=f"settings:update_login:{data.get('owner_telegram_id')}"
            )
        ])
        inline_keyboard.append([
            types.InlineKeyboardButton(
                text="Изменить пароль",
                callback_data=f"settings:update_password:{data.get('owner_telegram_id')}"
            )
        ])
        inline_keyboard.append([
            types.InlineKeyboardButton(
                text="Вернуться в главное меню",
                callback_data=f"main_menu:{data.get('owner_telegram_id')}"
            )
        ])
        reply_markup = types.InlineKeyboardMarkup(
            inline_keyboard=inline_keyboard
        )
        state = "settings"
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


@client_bot.on_callback_query(
    filters.regex("settings:update_username:") &
    get_filters().message_filter(state="settings")
)
async def update_username(_: Client, message: types.CallbackQuery) -> None:
    """Handler to start changing the username."""
    owner_telegram_id = int(message.data.split(":")[-1])
    text_message = (
        "Введите ваше новое имя"
    )
    reply_markup = get_back_buttons(owner_telegram_id=owner_telegram_id)
    get_fsm_context().update_state(
        telegram_id=message.from_user.id,
        state="settings:set_username"
    )
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="settings:set_username")
)
async def set_username(_: Client, message: types.Message) -> None:
    """Handler for setting a new username."""
    auth_controller.update_username(
        owner_telegram_id=message.from_user.id,
        username=message.text
    )
    text_message = (
        f"Имя успешно изменено. Новое имя: {message.text}"
    )
    telegram_utils = TelegramUtils(text=text_message, message=message)
    await telegram_utils.send_messages()
    return await settings_menu(_=_, message=message)


@client_bot.on_callback_query(
    filters.regex("settings:update_login:") &
    get_filters().message_filter(state="settings")
)
async def update_login(_: Client, message: types.CallbackQuery) -> None:
    """Handler to start changing the user login."""
    owner_telegram_id = int(message.data.split(":")[-1])
    text_message = (
        "Введите ваш новый логин"
    )
    reply_markup = get_back_buttons(owner_telegram_id=owner_telegram_id)
    get_fsm_context().update_state(
        telegram_id=message.from_user.id,
        state="settings:set_login_name"
    )
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="settings:set_login_name")
)
async def set_login(_: Client, message: types.Message) -> None:
    """Handler for setting a new user login."""
    is_update_login: bool = False
    reply_markup = None
    if auth_controller.get_user(login_name=message.text):
        text_message = (
            "Данный логин уже существует!!!\n"
            "Введите ваш новый логин"
        )
        reply_markup = get_back_buttons(owner_telegram_id=message.from_user.id)
    else:
        auth_controller.update_login_name(
            owner_telegram_id=message.from_user.id,
            login_name=message.text
        )
        text_message = (
            f"Логин успешно изменен. Новый логин: {message.text}"
        )
        is_update_login = True
    telegram_utils = TelegramUtils(
        text=text_message,
        message=message,
        reply_markup=reply_markup
    )
    await telegram_utils.send_messages()
    if is_update_login:
        return await settings_menu(_=_, message=message)


@client_bot.on_callback_query(
    filters.regex("settings:update_password:") &
    get_filters().message_filter(state="settings")
)
async def update_password(_: Client, message: types.CallbackQuery) -> None:
    """Handler to start changing the user's password."""
    owner_telegram_id = int(message.data.split(":")[-1])
    text_message = text_set_password_message()
    reply_markup = get_back_buttons(owner_telegram_id=owner_telegram_id)
    get_fsm_context().update_state(
        telegram_id=message.from_user.id,
        state="settings:set_password"
    )
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="settings:set_password")
)
async def set_password(_: Client, message: types.Message) -> None:
    """Handler for setting a new user password."""
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    if not validation_password(password=message.text.strip()):
        text_message = text_set_password_message(is_error=True)
    else:
        data["password"] = encrypt_password(password=message.text.strip())
        text_message = (
            "Подтвердите ваш новый пароль, введя его еще раз"
        )
        get_fsm_context().update_data(
            telegram_id=message.from_user.id,
            data=data
        )
        get_fsm_context().update_state(
            telegram_id=message.from_user.id,
            state="settings:confirm_set_password"
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
    get_filters().message_filter(state="settings:confirm_set_password")
)
async def confirm_set_password(_: Client, message: types.Message) -> None:
    """Handler for confirming a new user password."""
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    owner_telegram_id = data.get('owner_telegram_id')
    is_update_password: bool = False
    if not verify_password(
        password=message.text.strip(),
        encrypted_password=data.get("password")
    ):
        text_message = (
            "Пароли не совпадают!!!\n"
            f"{text_set_password_message()}"
        )
        reply_markup = get_back_buttons(owner_telegram_id=owner_telegram_id)
        get_fsm_context().update_state(
            telegram_id=owner_telegram_id,
            state="registration:set_password"
        )
    else:
        auth_controller.update_password(
            owner_telegram_id=owner_telegram_id,
            password=data.get('password')
        )
        text_message = "Пароль успешно изменен"
        reply_markup = None
        is_update_password = True
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    if is_update_password:
        return await settings_menu(_=_, message=message)


def get_back_buttons(owner_telegram_id: int) -> types.InlineKeyboardMarkup:
    """
    Function to get a keyboard with a "Back" and "Back to Main Menu" button.

    Options:
    - owner_telegram_id: User owner ID.

    Returns:
    - types.InlineKeyboardMarkup: Pyrogram keyboard object.
    """
    inline_keyboard = list()
    inline_keyboard.append([
        types.InlineKeyboardButton(
            text="Вернуться назад",
            callback_data=f"menu_settings:{owner_telegram_id}"
        )
    ])
    inline_keyboard.append([
        types.InlineKeyboardButton(
            text="Вернуться в главное меню",
            callback_data=f"main_menu:{owner_telegram_id}"
        )
    ])
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return reply_markup
