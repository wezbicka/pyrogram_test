from pyrogram import filters, Client, types
from app.auth_manager import auth_controller
from app.auth_manager.password import validation_password, encrypt_password, \
    verify_password, text_set_password_message
from app.bot_init.bot_init import client_bot
from app.db.models import Users
from app.fsm_context.fsm_context import get_fsm_context
from app.root.controller import send_message_start
from app.root.filters import get_filters
from app.utils import TelegramUtils


@client_bot.on_message(filters.text & get_filters().message_filter(
    state="registration_authorization") & filters.regex("Регистрация"))
async def registration_user(_: Client, message: types.Message) -> None:
    """Handler for starting the user registration process in the bot."""
    text_message = (
        "Введите ваше имя в системе или нажмите продолжить, \
            чтобы использовать ваше имя в телеграмме"
    )
    keyboard = [[
        types.KeyboardButton(text="Продолжить"),
        types.KeyboardButton(text="В главное меню")
    ]]
    reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard)
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    get_fsm_context().update_state(
        telegram_id=message.from_user.id,
        state="registration:username"
    )


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="registration:username")
)
async def set_username(_: Client, message: types.Message) -> None:
    """Handler for setting the username during the registration process."""
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    data["username"] = message.from_user.first_name \
        if message.text == "Продолжить" else message.text.strip()
    text_message = (
        f"Ваше имя: {data.get('username')}. "
        "Введите ваш логин, "
        "который будет использоваться для доступа к боту, "
        f"или нажмите продолжить, чтобы использовать ваш логин телеграмма"
    )
    keyboard = [[
        types.KeyboardButton(text="Продолжить"),
        types.KeyboardButton(text="В главное меню")
    ]]
    reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard)
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    get_fsm_context().update_data(telegram_id=message.from_user.id, data=data)
    get_fsm_context().update_state(
        telegram_id=message.from_user.id,
        state="registration:nickname"
    )


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="registration:nickname")
)
async def set_username(_: Client, message: types.Message) -> None:
    """Handler for setting the user login during the registration process."""
    login_name = message.from_user.username if message.text == "Продолжить" \
        else message.text.strip()
    user: Users | None = auth_controller.get_user(
        owner_telegram_id=message.from_user.id
    )
    if user:
        text_message = (
            "Данный логин уже присутствует в боте. "
            "Введите ваш логин"
            ", который будет использоваться для доступа к боту, "
            "или нажмите продолжить, чтобы использовать ваш логин телеграмма"
        )
        keyboard = [[
            types.KeyboardButton(text="Продолжить"),
            types.KeyboardButton(text="В главное меню")
        ]]
        reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard)
    else:
        data = get_fsm_context().get_data(telegram_id=message.from_user.id)
        data["login_name"] = login_name
        text_message = text_set_password_message()
        keyboard = [[types.KeyboardButton(text="В главное меню")]]
        reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard)
        get_fsm_context().update_data(
            telegram_id=message.from_user.id,
            data=data
        )
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    get_fsm_context().update_state(
        telegram_id=message.from_user.id,
        state="registration:set_password"
    )


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="registration:set_password")
)
async def set_password(_: Client, message: types.Message) -> None:
    """Handler for setting the user's password during the registration process."""
    keyboard = [[types.KeyboardButton(text="В главное меню")]]
    reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard)
    if not validation_password(password=message.text.strip()):
        text_message = text_set_password_message(is_error=True)
    else:
        data = get_fsm_context().get_data(telegram_id=message.from_user.id)
        data["password"] = encrypt_password(password=message.text.strip())
        text_message = (
            "Подтвердите ваш новый пароль, введя его еще раз"
        )
        get_fsm_context().update_state(
            telegram_id=message.from_user.id,
            state="registration:confirm_set_password"
        )
        get_fsm_context().update_data(
            telegram_id=message.from_user.id,
            data=data
        )
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="registration:confirm_set_password")
)
async def confirm_set_password(client: Client, message: types.Message) -> None:
    """Handler for confirming the user's password during the registration process."""
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    is_save_user: bool = False
    if not verify_password(
        password=message.text.strip(),
        encrypted_password=data.get("password")
    ):
        text_message = (
            "Пароли не совпадают!!!\n"
            f"{text_set_password_message()}"
        )
        keyboard = [[types.KeyboardButton(text="В главное меню")]]
        reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard)
        get_fsm_context().update_state(
            telegram_id=message.from_user.id,
            state="registration:set_password"
        )
    else:
        auth_controller.set_user(
            owner_telegram_id=message.from_user.id,
            password=data.get('password'),
            login_name=data.get("login_name"),
            username=data.get("username")
        )
        text_message = "Регистрация в боте прошла успешно"
        reply_markup = None
        is_save_user = True
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    if is_save_user:
        await send_message_start(message=message, _=client)
