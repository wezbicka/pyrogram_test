"""
Create dynamic Pyrogram filters.

This module contains code for creating dynamic Pyrogram filters,
based on the state of the finite state machine (FSM) of the users.

Options:
    _filters (Filters): Static Filters object for managing dynamic filters.
"""

from pyrogram import filters, types
from pyrogram.filters import Filter

from app.fsm_context.fsm_context import get_fsm_context


class Filters:

    __instance = None

    def __new__(cls, *args, **kwargs):
        """
        Create and return a single instance of the Filters class.

        Returns:
            Filters: A single instance of the Filters class.
        """
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self.message_filter = self.__message_dynamic_filter

    @staticmethod
    def __message_dynamic_filter(state: str, is_regex: bool = False) -> Filter:
        """
        Create a dynamic Pyrogram filter based on the state of the FSM.

        Options:
            state (str): State of the state machine (FSM).
            is_regex (bool): Flag indicating whether the condition is a regular expression.

        Returns:
            Filter: Dynamic Pyrogram filter.
        """

        async def __func(flt: filters, __, message: types.Message | types.CallbackQuery) -> bool:
            user_fsm_state_object = get_fsm_context().get_list_fsm_contexts().get(message.from_user.id)
            user_state = str() if not user_fsm_state_object else user_fsm_state_object.state
            if is_regex:
                return flt.state in user_state
            return flt.state == user_state

        return filters.create(__func, state=state, is_regex=is_regex)


_filters: Filters = Filters()


def get_filters() -> Filters:
    return _filters
