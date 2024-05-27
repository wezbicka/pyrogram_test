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


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="authorization:reset_password")
)
async def set_password(_: Client, message: types.Message) -> None:
    """Handler for setting a new password."""
    keyboard = [[types.KeyboardButton(text="В главное меню")]]
    reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard)
    if not validation_password(password=message.text.strip()):
        text_message = text_set_password_message(is_error=True)
    else:
        data = get_fsm_context().get_data(telegram_id=message.from_user.id)
        data["password"] = encrypt_password(password=message.text.strip())
        text_message = "Подтвердите ваш новый пароль, введя его еще раз"
        get_fsm_context().update_state(
            telegram_id=message.from_user.id,
            state="authorization:confirm_reset_password"
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
    get_filters().message_filter(state="authorization:confirm_reset_password")
)
async def confirm_set_password(client: Client, message: types.Message) -> None:
    """Confirmation handler for setting a new password."""
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    is_update_user: bool = False
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
            state="authorization:reset_password"
        )
    else:
        auth_controller.update_password(
            owner_telegram_id=message.from_user.id,
            password=data.get('password')
        )
        text_message = "Пароль успешно изменен"
        reply_markup = None
        is_update_user = True
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    if is_update_user:
        await authorization_user(message=message, _=client)


@client_bot.on_message(
    filters.text &
    get_filters().message_filter(state="registration_authorization") &
    filters.regex("Авторизация")
)
async def authorization_user(_: Client, message: types.Message) -> None:
    """User authorization request handler."""
    text_message = (
        "Введите ваш логин для авторизации в данном боте, "
        "или нажмите продолжить, чтобы использовать ваш логин телеграмма"
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
        state="authorization:login"
    )


@client_bot.on_message(
    filters.text &
    (get_filters().message_filter(state="authorization:login"))
)
async def authorization_user_login(_: Client, message: types.Message) -> None:
    """Login input handler for authorization."""
    login_name = message.from_user.username if message.text == "Продолжить" \
        else message.text.strip()
    user: Users | None = auth_controller.get_user(login_name=login_name)
    keyboard = list()
    if not user:
        text_message = "Данный логин не был обнаружен. \
            Повторите ввод логина еще раз"
        keyboard.append([
            types.KeyboardButton(text="Продолжить"),
            types.KeyboardButton(text="В главное меню")]
        )
        reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard)
    else:
        data = get_fsm_context().get_data(telegram_id=message.from_user.id)
        data["login_name"] = login_name
        get_fsm_context().update_data(
            telegram_id=message.from_user.id,
            data=data
        )
        text_message = "Введите ваш пароль от аккаунта"
        if auth_controller.check_user_is_owner(
            user_telegram_id=message.from_user.id,
            owner_telegram_id=user.owner_telegram_id
        ):
            keyboard.append([
                types.KeyboardButton(text="Восстановление пароля")
            ])
        keyboard.append([types.KeyboardButton(text="В главное меню")])
        reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard)
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    if user:
        get_fsm_context().update_state(
            telegram_id=message.from_user.id,
            state="authorization:password"
        )


@client_bot.on_message(filters.text & (get_filters().message_filter(
    state="authorization:password") & filters.regex("Восстановление пароля")))
async def reset_password(_: Client, message: types.Message) -> None:
    """ОPassword recovery request handler."""
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    user: Users | None = auth_controller.get_user(
        login_name=data.get('login_name')
    )
    reply_markup = None
    if not auth_controller.check_user_is_owner(
        user_telegram_id=message.from_user.id,
        owner_telegram_id=user.owner_telegram_id
    ):
        text_message = "Вы не имеете доступ к данному функционалу"
    else:
        text_message = text_set_password_message()
        keyboard = list()
        keyboard.append([types.KeyboardButton(text="В главное меню")])
        reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard)
        get_fsm_context().update_state(
            telegram_id=message.from_user.id,
            state="authorization:reset_password"
        )
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    if not reply_markup:
        await send_message_start(_=_, message=message)


@client_bot.on_message(
    filters.text &
    (get_filters().message_filter(state="authorization:password"))
)
async def registration_user(client: Client, message: types.Message) -> None:
    """User authorization handler."""
    is_authorize: bool = False
    reply_markup = None
    keyboard = list()
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    user: Users | None = auth_controller.get_user(
        login_name=data.get('login_name')
    )
    if not verify_password(
        password=message.text.strip(),
        encrypted_password=user.password
    ):
        text_message = "Вы ввели неверный пароль. \
            Повторите попытку еще раз, или сбросьте ваш пароль"
        if auth_controller.check_user_is_owner(
            user_telegram_id=message.from_user.id,
            owner_telegram_id=user.owner_telegram_id
        ):
            keyboard.append([
                types.KeyboardButton(text="Восстановление пароля")
            ])
        keyboard.append([types.KeyboardButton(text="В главное меню")])
        reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard)
    else:
        auth_controller.update_is_login(
            owner_telegram_id=user.owner_telegram_id,
            is_login=True
        )
        text_message = "Вы успешно авторизовались"
        is_authorize = True
    telegram_utils = TelegramUtils(
        text=text_message,
        reply_markup=reply_markup,
        message=message
    )
    await telegram_utils.send_messages()
    if is_authorize:
        return await send_message_start(
            message=message,
            _=client,
            owner_telegram_id=user.owner_telegram_id
        )


@client_bot.on_message(filters.text & filters.regex("Выйти с аккаунта"))
async def confirm_delete_account_user(
    client: Client,
    message: types.Message
) -> None:
    """Account logout confirmation handler."""
    data = get_fsm_context().get_data(telegram_id=message.from_user.id)
    if not data.get('owner_telegram_id'):
        text_message = "Вы не имеете доступ к данному функционалу"
    else:
        auth_controller.update_is_login(
            owner_telegram_id=data.get('owner_telegram_id'),
            is_login=False
        )
        text_message = "Вы успешно отключились от аккаунта"
    telegram_utils = TelegramUtils(text=text_message, message=message)
    await telegram_utils.send_messages()
    return await send_message_start(
        _=client,
        message=message,
        owner_telegram_id=message.from_user.id
    )
