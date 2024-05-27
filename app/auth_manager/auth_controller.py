"""
Module for working with the database and managing users.

This module contains functions for interacting with the database and managing users.
"""

from sqlalchemy import text

from app.db.db_config import Session
from app.db.models import Users


def update_is_login(owner_telegram_id: int, is_login: bool) -> None:
    """
    Updates the user's login status.

    Options:
        owner_telegram_id (int): Account owner ID.
        is_login (bool): New user login status.

    Returns:
        None
    """
    with Session() as session:
        query = text(
            "UPDATE users SET is_login=:is_login "
            "WHERE owner_telegram_id=:owner_telegram_id"
        )
        session.execute(
            query,
            {
                "owner_telegram_id": owner_telegram_id,
                "is_login": is_login
            }
        )
        session.commit()


def update_username(owner_telegram_id: int, username: str) -> None:
    """
    Updates the username in the database.

    Options:
        owner_telegram_id (int): Account owner ID.
        username (str): New username.

    Returns:
        None
    """
    with Session() as session:
        query = text(
            "UPDATE users SET username=:username "
            "WHERE owner_telegram_id=:owner_telegram_id"
        )
        session.execute(
            query,
            {
                "owner_telegram_id": owner_telegram_id,
                "username": username
            }
        )
        session.commit()


def update_login_name(owner_telegram_id: int, login_name: str) -> None:
    """
    Updates the user's unique login in the database.

    Options:
        owner_telegram_id (int): Account owner ID.
        login_name (str): New unique login.

    Returns:
        None
    """
    with Session() as session:
        query = text(
            "UPDATE users SET login_name=:login_name "
            "WHERE owner_telegram_id=:owner_telegram_id"
        )
        session.execute(
            query,
            {
                "owner_telegram_id": owner_telegram_id,
                "login_name": login_name
            }
        )
        session.commit()


def update_password(owner_telegram_id: int, password: str) -> None:
    """
    Updates the user's password in the database.

    Options:
        owner_telegram_id (int): Account owner ID.
        password (str): New password.
    """
    with Session() as session:
        query = text(
            "UPDATE users SET password=:password "
            "WHERE owner_telegram_id=:owner_telegram_id"
        )
        session.execute(
            query,
            {
                "owner_telegram_id": owner_telegram_id,
                "password": password
            }
        )
        session.commit()


def set_user(
        login_name: str,
        owner_telegram_id: int,
        username: str,
        password: str,
        is_login: bool = True
    ) -> None:
    """
    Adds a new user to the database.

    Options:
        login_name (str): Unique user login.
        owner_telegram_id (int): Account owner ID.
        username (str): Username.
        password (str): User password.
        is_login (bool, optional): User login status (default True).
    """
    with Session() as session:
        query = text(
            "INSERT INTO users (login_name, owner_telegram_id, password, username, is_login) "
            "VALUES (:login_name, :owner_telegram_id, :password, :username, :is_login)")
        session.execute(
            query,
            {
                "owner_telegram_id": owner_telegram_id,
                "password": password,
                "login_name": login_name,
                "username": username,
                "is_login": is_login
            }
        )
        session.commit()


def get_user(
        owner_telegram_id: int = None,
        login_name: str = None
    ) -> Users | None:
    """
    Retrieves a user from the database by account owner ID or unique login.

    Options:
        owner_telegram_id (int, optional): Account owner ID.
        login_name (str, optional): Unique user login.

    Returns:
        Users | None: The user object, or None if the user is not found.
    """
    user = None
    with Session() as session:
        if owner_telegram_id:
            query = text(
                "SELECT owner_telegram_id, password, login_name, username, is_login "
                "FROM users "
                "WHERE owner_telegram_id = :owner_telegram_id"
            )
            user: Users | None = session.execute(
                query, {"owner_telegram_id": owner_telegram_id}
            ).first()
        elif login_name:
            query = text(
                "SELECT owner_telegram_id, password, login_name, username, is_login "
                "FROM users "
                "WHERE login_name = :login_name")
            user: Users | None = session.execute(
                query, {"login_name": login_name}
            ).first()
    return user


def delete_user(owner_telegram_id: int) -> None:
    """
    Removes a user from the database.

    Options:
        owner_telegram_id (int): Account owner ID.
    """
    with Session() as session:
        query = text(
            "DELETE FROM users "
            "WHERE owner_telegram_id = :owner_telegram_id"
        )
        session.execute(query, {"owner_telegram_id": owner_telegram_id})
        session.commit()


def check_user_is_owner(user_telegram_id: int, owner_telegram_id: int) -> bool:
    """
    Checks whether the user is the account owner.

    Options:
        user_telegram_id (int): User ID.
        owner_telegram_id (int): Account owner ID.

    Returns:
        bool: True if the user is the account owner, False otherwise.
    """
    return user_telegram_id == owner_telegram_id
