import re
from datetime import datetime, UTC

import pytz
from pyrogram import types
from sqlalchemy import text

from app.db.db_config import Session
from app.db.models import UserTasks
from app.utils import TelegramUtils


def get_all_tasks(
    owner_telegram_id: int,
    current_tasks: bool = False,
    overdue_tasks: bool = False,
    completed_tasks: bool = False
) -> list[UserTasks]:
    """
        Get a list of user tasks depending on the specified parameters.

        Options:
        - owner_telegram_id (int): Telegram user ID.
        - current_tasks (bool): Flag for getting current tasks (neither started nor completed).
        - overdue_tasks (bool): Flag for receiving overdue tasks.
        - completed_tasks (bool): Flag for receiving completed tasks.

        Returns:
        - list[UserTasks]: List of user task objects.
    """
    condition_text = "WHERE owner_telegram_id =:owner_telegram_id"
    with Session() as session:
        if current_tasks:
            condition_text += (
                " AND start_time AT TIME ZONE 'UTC' < current_timestamp AT TIME ZONE "
                "'UTC' AND end_time AT TIME ZONE 'UTC' > current_timestamp AT TIME ZONE 'UTC'"
                " AND status = false;"
            )
        elif overdue_tasks:
            condition_text += (
                " AND end_time AT TIME ZONE 'UTC' < current_timestamp AT TIME ZONE 'UTC'"
                " AND status = false;"
            )
        elif completed_tasks:
            condition_text += " AND status = true;"
        query = text(
            "SELECT id_task, owner_telegram_id, task_name, start_time, "
            "end_time, completion_time, status, description "
            "FROM user_tasks "
            f"{condition_text}"
        )
        user_tasks_list: list[UserTasks] = session.execute(
            query,
            {"owner_telegram_id": owner_telegram_id}
        ).all()
    return user_tasks_list


def get_task_by_id(id_task: int, owner_telegram_id: int) -> UserTasks | None:
    """
       Get a specific user task by its ID.

        Options:
        - id_task (int): Task ID.
        - owner_telegram_id (int): Telegram user ID.

        Returns:
        - Union[UserTasks, None]: The user's task object, or None if the task is not found.
    """
    with Session() as session:
        query = text(
            "SELECT id_task, owner_telegram_id, task_name, start_time, end_time, completion_time, status, "
            "end_time, completion_time, status, description "
            "FROM user_tasks "
            "WHERE id_task =:id_task AND owner_telegram_id = :owner_telegram_id"
        )
        user_task: UserTasks = session.execute(
            query,
            {
                "id_task": id_task,
                "owner_telegram_id": owner_telegram_id
            }
        ).first()
    return user_task


def set_task(
    owner_telegram_id: int,
    task_name: str,
    start_time: datetime,
    end_time: datetime,
    description: str,
    completion_time: datetime = None,
    status: bool = False
) -> None:
    """
        Add a new task to the database.

        Options:
        - owner_telegram_id (int): Telegram user ID.
        - task_name (str): Name of the task.
        - start_time (datetime): Start time of the task.
        - end_time (datetime): Time when the task ended.
        - description (str): Description of the task.
        - completion_time (datetime): Task completion time (None by default).
        - status (bool): Task completion status (default False).
    """
    with Session() as session:
        query = text(
            "INSERT INTO user_tasks (owner_telegram_id, task_name, "
            "start_time, end_time, completion_time, status, description) "
            "VALUES (:owner_telegram_id, :task_name, :start_time, "
            ":end_time, :completion_time, :status, :description);"
        )
        session.execute(
            query,
            {
                "owner_telegram_id": owner_telegram_id,
                "task_name": task_name,
                "start_time": start_time,
                "end_time": end_time,
                "completion_time": completion_time,
                "status": status,
                "description": description
            }
        )
        session.commit()


def update_task_name(id_task: int, owner_telegram_id: int, task_name: str) -> None:
    """
        Update the task name.

        Options:
        - id_task (int): Task ID.
        - owner_telegram_id (int): Telegram user ID.
        - task_name (str): New task name.
    """
    with Session() as session:
        query = text(
            "UPDATE user_tasks SET task_name =:task_name "
            "WHERE owner_telegram_id =:owner_telegram_id;"
        )
        session.execute(
            query,
            {
                "id_task": id_task,
                "owner_telegram_id": owner_telegram_id,
                "task_name": task_name
            }
        )
        session.commit()


def update_task_description(
    id_task: int,
    owner_telegram_id: int,
    description: str
) -> None:
    """
        Update the task description.

        Options:
        - id_task (int): Task ID.
        - owner_telegram_id (int): Telegram user ID.
        - description (str): New task description.
    """
    with Session() as session:
        query = text(
            "UPDATE user_tasks SET description =:description "
            "WHERE owner_telegram_id =:owner_telegram_id;"
        )
        session.execute(
            query,
            {
                "id_task": id_task,
                "owner_telegram_id": owner_telegram_id,
                "description": description
            }
        )
        session.commit()


def update_task_start_time(
    id_task: int,
    owner_telegram_id: int,
    start_time: str
) -> None:
    """
        Update the start time of a task.

        Options:
        - id_task (int): Task ID.
        - owner_telegram_id (int): Telegram user ID.
        - start_time (str): New task start time in the format DD.MM.YYYY HH:MM.
    """
    start_time = transform_utc_time(time=start_time)
    with Session() as session:
        query = text(
            "UPDATE user_tasks SET start_time =:start_time "
            "WHERE owner_telegram_id =:owner_telegram_id;")
        session.execute(
            query,
            {
                "id_task": id_task,
                "owner_telegram_id": owner_telegram_id,
                "start_time": start_time
            }
        )
        session.commit()


def update_task_end_time(
    id_task: int,
    owner_telegram_id: int,
    end_time: str
) -> None:
    """
        Update the completion time of a task.

        Options:
        - id_task (int): Task ID.
        - owner_telegram_id (int): Telegram user ID.
        - end_time (str): New task end time in the format DD.MM.YYYY HH:MM.
    """
    end_time = transform_utc_time(time=end_time)
    with Session() as session:
        query = text(
            "UPDATE user_tasks SET end_time =:end_time "
            "WHERE owner_telegram_id =:owner_telegram_id AND user_tasks.id_task = :id_task;")
        session.execute(
            query,
            {
                "id_task": id_task,
                "owner_telegram_id": owner_telegram_id,
                "end_time": end_time
            }
        )
        session.commit()


def update_task_completion(id_task: int, owner_telegram_id: int) -> bool:
    """
        Update the status and completion time of a task.

        Options:
        - id_task (int): Task ID.
        - owner_telegram_id (int): Telegram user ID.

        Returns:
        - bool: Task completion status (True - completed, False - not completed).
    """
    task: UserTasks = get_task_by_id(
        id_task=id_task,
        owner_telegram_id=owner_telegram_id
    )
    status = True if not task.status else False
    completion_time = datetime.now(UTC) if status else None
    with Session() as session:
        query = text(
            "UPDATE user_tasks SET completion_time =:completion_time, status=:status "
            "WHERE owner_telegram_id =:owner_telegram_id AND user_tasks.id_task = :id_task;")
        session.execute(
            query,
            {
                "id_task": id_task,
                "owner_telegram_id": owner_telegram_id,
                "completion_time": completion_time,
                "status": status
            }
        )
        session.commit()
    return status


def delete_task(owner_telegram_id: int, id_task: int = None) -> None:
    """
        Remove a user's task from the database.

        Options:
        - owner_telegram_id (int): Telegram user ID.
        - id_task (int): Task ID (optional).
    """
    with Session() as session:
        if id_task:
            query = text(
                "DELETE FROM user_tasks "
                "WHERE owner_telegram_id =:owner_telegram_id AND id_task = :id_task;"
            )
            session.execute(
                query,
                {
                    "owner_telegram_id": owner_telegram_id,
                    "id_task": id_task
                }
            )
        else:
            query = text(
                "DELETE FROM user_tasks "
                "WHERE owner_telegram_id =:owner_telegram_id;"
            )
            session.execute(query, {"owner_telegram_id": owner_telegram_id})
        session.commit()


def check_valid_date(start_time: str, end_time: str = None) -> bool:
    """
        Check the correctness of the specified dates and times.

        Options:
        - start_time (str): Start time of the task in the format DD.MM.YYYY HH:MM.
        - end_time (str): Task completion time in the format DD.MM.YYYY HH:MM (None by default).

        Returns:
        - bool: True if the dates and times are specified correctly, otherwise False.
    """
    datetime_regex = r'^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.20([0-9][0-9]) ([0-1][0-9]|2[0-3])\:([0-5][0-9])'
    is_true_match_check = re.match(datetime_regex, start_time) \
        if not end_time else re.match(datetime_regex, end_time)
    if not is_true_match_check:
        return False
    start_date = (datetime.strptime(start_time, '%d.%m.%Y %H:%M')).astimezone(UTC)
    if end_time:
        end_date = (datetime.strptime(end_time, '%d.%m.%Y %H:%M')).astimezone(UTC)
        if end_date <= start_date:
            return False
    return True


def transform_utc_time(time: str) -> datetime:
    """
        Convert a time in the format DD.MM.YYYY HH:MM to a datetime object based on UTC time.

        Options:
        - time (str): Time in the format DD.MM.YYYY HH:MM.

        Returns:
        - datetime: A datetime object based on UTC time.
    """
    return datetime.strptime(time, '%d.%m.%Y %H:%M').astimezone(UTC)


def get_text_set_time(start_time: datetime | str = None, is_error: bool = False) -> str:
    """
        Generate a text message to set the task time.

        Options:
        - start_time (datetime | str): Task start time (None by default).
        - is_error (bool): Error flag in time format (default False).

        Returns:
        - str: Text message with instructions for setting the task time.
    """
    text_message = (
        f"{('Вы ввели неверный формат даты и времени!!!' if is_error else '')}\n"
        f"Введите дату и время {('старта' if not start_time else 'завершения')} "
        "вашей новой задачи в формате DD.MM.YYYY HH:MM. Ввод в таком формате обязателен.\n"
        f"{(f'Дата не должна быть меньше, чем {(start_time.strftime("%d.%m.%Y %H:%M") if isinstance(
            start_time, datetime) else start_time)}' if start_time else '')}"
    )
    return text_message


async def send_messages_get_all_tasks(
    list_tasks: list[UserTasks],
    message: types.CallbackQuery
) -> None:
    """
        Asynchronously sends messages with information about tasks.

        Options:
        - list_tasks (list[UserTasks]): List of user task objects.
        - message (types.CallbackQuery) -> None: Telegram message object.
    """
    list_text_messages = list()
    if not list_tasks:
        list_text_messages.append("Задачи данного типа у вас отсутствуют")
    else:
        for count, task in enumerate(list_tasks):
            message_text = (
                f"*                                 Задача {task.task_name} № {task.id_task}                     *\n\n"
                f"Описание задачи:\n{task.description}\n\n"
                f"Время старта данной задачи по Гринвичу:\n{task.start_time.astimezone(pytz.timezone('UTC'))}\n\n"
                f"Время завершения данной задачи по Гринвичу:\n{task.end_time.astimezone(pytz.timezone('UTC'))}\n\n"
                f"Статус завершения задачи:\nЗадача {(
                    'завершена' if task.status else 'просрочена' if 
                    task.end_time < datetime.now(UTC) else 'выполняется')}\n\n"
                f"{(f'Время завершения задачи по Гринвичу:\n{task.completion_time.astimezone(pytz.timezone('UTC'))}\n\n' 
                    if task.status else '')}"
            )
            list_text_messages.append(message_text)
    for count, text_message in enumerate(list_text_messages):
        telegram_utils = TelegramUtils(text=text_message, message=message)
        await telegram_utils.send_messages()
