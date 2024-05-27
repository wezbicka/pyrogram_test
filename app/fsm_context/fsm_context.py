"""
    A module containing the FSM (Finite State Machine) class and a function to initialize an FSM instance.

    The FSM class provides methods for working with the fsm_context table in the database,
    representing the state machine context for users.

    The fsm_context_init function and the global variable _fsm_context are used for initialization
    a single instance of FSM when the application starts.
"""

import json

from sqlalchemy import text

from app.db.db_config import Session
from app.db.models import FSMContext


class FSM:
    """
    State machine management (FSM) for users.

    Options:
        __list_fsm_contexts (dict[int, FSMContext]):
            A dictionary containing FSMContext objects for each user.

    Methods:
        get_list_fsm_contexts(): Retrieves a dictionary of FSMContext objects for all users.
        __update_list_fsm_contexts(): Private method for updating the list of FSMContext objects from the database.
        __get_fsm_context(telegram_id: int) -> FSMContext | None: Private method to get FSMContext
            object for the user.
        __set_fsm_context(telegram_id: int, state: str, data: dict) -> None: Private method for
            installing a new FSMContext object in the database.
        __update_fsm_context(telegram_id: int, state: str, data: dict) -> None: Private method for
            updating an existing FSMContext object in the database.
        __delete_fsm_context(telegram_id: int) -> None: Private method to delete FSMContext
            object from the database.
        get_state(telegram_id: int) -> str | None: Gets the current state of the user in FSM.
        update_state(telegram_id: int, state: str) -> None: Updates the user's state in FSM.
        get_data(telegram_id: int) -> dict: Retrieves additional user data in the FSM.
        update_data(telegram_id: int, data: dict) -> dict: Updates additional user data in FSM.
        clear(telegram_id: int) -> None: Clears the FSMContext object for the user.
    """

    def __init__(self):
        self.__list_fsm_contexts: dict[int, FSMContext] = dict()
        self.__update_list_fsm_contexts()

    def get_list_fsm_contexts(self) -> dict[int, FSMContext]:
        """
        Get a dictionary of FSMContext objects for all users.

        Returns:
            dict[int, FSMContext]: Dictionary of FSMContext objects for all users.
        """
        return self.__list_fsm_contexts

    def __update_list_fsm_contexts(self) -> None:
        """
        Update the list of FSMContext objects from the database.
        """
        with Session() as session:
            query = text("SELECT * FROM fsm_context")
            fsm_context_list: list[FSMContext] = session.execute(query).all()
        self.__list_fsm_contexts: dict[int, FSMContext] = {x.telegram_id: x for x in fsm_context_list}

    @staticmethod
    def __get_fsm_context(telegram_id: int) -> FSMContext | None:
        """
        Get the FSMContext object for the user.

        Options:
            telegram_id (int): Telegram user ID.

        Returns:
            FSMContext | None: The FSMContext object, or None if the object is not found.
        """
        with Session() as session:
            query = text("SELECT * FROM fsm_context WHERE telegram_id=:telegram_id")
            fsm_context: FSMContext | None = session.execute(
                query, {"telegram_id": telegram_id}
            ).first()
        return fsm_context

    def __set_fsm_context(self, telegram_id: int, state: str, data: dict) -> None:
        """
        Set a new FSMContext object in the database.

        Options:
            telegram_id (int): Telegram user ID.
            state (str): New user state in FSM.
            data (dict): New additional user data in FSM.
        """
        with Session() as session:
            query = text("INSERT INTO fsm_context VALUES (:telegram_id, :state, :data)")
            session.execute(
                query,
                {
                    "telegram_id": telegram_id,
                    "state": state,
                    "data": json.dumps(data)
                }
            )
            session.commit()
        self.__list_fsm_contexts[telegram_id] = self.__get_fsm_context(
            telegram_id=telegram_id
        )

    def __update_fsm_context(self, telegram_id: int, state: str, data: dict) -> None:
        """
        Update an existing FSMContext object in the database.

        Options:
            telegram_id (int): Telegram user ID.
            state (str): New user state in FSM.
            data (dict): New additional user data in FSM.
        """
        with Session() as session:
            query = text(
                "UPDATE fsm_context SET state=:state, data=:data "
                "WHERE telegram_id=:telegram_id"
            )
            session.execute(
                query,
                {
                    "telegram_id": telegram_id,
                    "state": state,
                    "data": json.dumps(data)
                }
            )
            session.commit()
        self.__list_fsm_contexts[telegram_id] = self.__get_fsm_context(
            telegram_id=telegram_id
        )

    def __delete_fsm_context(self, telegram_id: int) -> None:
        """Remove the FSMContext object from the database."""
        with Session() as session:
            query = text("DELETE FROM fsm_context WHERE telegram_id=:telegram_id")
            session.execute(query, {"telegram_id": telegram_id})
            session.commit()
        del self.__list_fsm_contexts[telegram_id]

    def get_state(self, telegram_id: int) -> str | None:
        """
        Get the current state of the user in FSM.

        Options:
            telegram_id (int): Telegram user ID.

        Returns:
            str | None: User status in FSM or None if object not found.
        """
        if self.__list_fsm_contexts.get(telegram_id):
            return self.__list_fsm_contexts[telegram_id].state

    def update_state(self, telegram_id: int, state: str) -> None:
        """Update the user's state in FSM."""
        fsm_context: FSMContext | None = self.__get_fsm_context(telegram_id=telegram_id)
        if fsm_context:
            self.__update_fsm_context(
                telegram_id=telegram_id,
                state=state,
                data=fsm_context.data
            )
        else:
            self.__set_fsm_context(telegram_id=telegram_id, state=state, data=dict())

    def get_data(self, telegram_id: int) -> dict:
        """
        Get additional user data in the FSM.

        Options:
            telegram_id (int): Telegram user ID.

        Returns:
            dict: Additional user data in the FSM or an empty dictionary if the object is not found.
        """
        return self.__list_fsm_contexts[telegram_id].data \
            if self.__list_fsm_contexts.get(telegram_id) else dict()

    def update_data(self, telegram_id: int, data: dict) -> dict:
        """
        Update additional user data in FSM.

        Options:
            telegram_id (int): Telegram user ID.
            data (dict): New additional user data in FSM.

        Returns:
            dict: Updated additional user data in FSM.

        """
        fsm_context: FSMContext | None = self.__get_fsm_context(
            telegram_id=telegram_id
        )
        if fsm_context:
            self.__update_fsm_context(
                telegram_id=telegram_id,
                data=data,
                state=fsm_context.state
            )
        else:
            self.__set_fsm_context(telegram_id=telegram_id, data=data, state=str())
        return self.get_data(telegram_id=telegram_id)

    def clear(self, telegram_id: int) -> None:
        """Clear the FSMContext object for the user."""
        self.__update_fsm_context(telegram_id=telegram_id, state=str(), data=dict())


_fsm_context: FSM


async def fsm_context_init() -> None:
    global _fsm_context
    _fsm_context = FSM()


def get_fsm_context() -> FSM:
    return _fsm_context
