"""
Data classes to represent users, state of a finite state machine (FSM) and user tasks.

Data-classes:
    1. Users: Represents user information.
        Options:
            - owner_telegram_id: int - owner identifier (in this case, Telegram ID).
            - login_name: str - login name.
            - username: str - user name.
            - password: str - user password.
            - is_login: bool - flag indicating the user's login status.

    2. FSMContext: Represents the state machine (FSM) context for the user.
        Options:
            - telegram_id: int - user ID in Telegram.
            - state: str - current state of the FSM.
            - data: dict - additional FSM context data.

    3. UserTasks: Represents a user task.
        Options:
            - id_task: int - task identifier.
            - user: Users - an object representing the user.
            - task_name: str - task name.
            - description: str - description of the task.
            - start_time: datetime - task start time.
            - end_time: datetime - task end time.
            - completion_time: datetime | None - task completion time (can be None if the task is not completed).
            - status: bool - task execution status (True if completed, False otherwise).

Note:
    - These classes use generic annotations that provide information about the types of variables.
    - Data classes provide immutable objects with automatic generation of methods such as __init__ and __repr__.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Users:
    owner_telegram_id: int
    login_name: str
    username: str
    password: str
    is_login: bool


@dataclass
class FSMContext:
    telegram_id: int
    state: str
    data: dict


@dataclass
class UserTasks:
    id_task: int
    user: Users
    task_name: str
    description: str
    start_time: datetime
    end_time: datetime
    completion_time: datetime | None
    status: bool
