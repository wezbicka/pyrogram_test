import re
from cryptography.fernet import Fernet
from app.config import SECRET_KEY


FERNET = Fernet(SECRET_KEY)


def validation_password(password: str) -> bool:
    """
    Checks whether the provided password meets the specified criteria.

    Options:
    - password (str): Password for validation.

    Returns:
    - bool: True if the password matches the criteria, False otherwise.
    """
    regex_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$"
    return bool(re.match(regex_pattern, password))


def encrypt_password(password: str) -> str:
    """
    Encrypts the provided password using Fernet encryption.

    Options:
    - password (str): Password for encryption.

    Returns:
    - str: Encrypted password.
    """
    encrypted_password = FERNET.encrypt(password.encode()).decode()
    return encrypted_password


def descript_password(password: str) -> str:
    """
    Decrypts the provided password using Fernet decryption.

    Options:
    - password (str): Encrypted password to decrypt.

    Returns:
    - str: Decrypted password.
    """
    decrypted_password = FERNET.decrypt(password.encode()).decode()
    return decrypted_password


def verify_password(password: str, encrypted_password: str) -> bool:
    """
    Checks whether the provided password matches the decrypted encrypted password.

    Options:
    - password (str): Plain password text.
    - encrypted_password (str): Encrypted password for comparison.

    Returns:
    - bool: True if the passwords are the same, False otherwise.
    """
    return password == descript_password(encrypted_password)


def text_set_password_message(is_error: bool = False) -> str:
    """
    Generates a message instructing the user to set a new password.

    Options:
    - is_error (bool): Flag indicating whether an error message should be included.

    Returns:
    - str: Instructional text message.
    """
    text_message = (
        f"{('Вы ввели пароль, не соответствующий критериям!!!\n' if is_error else '')}" 
        "Введите ваш новый пароль.\n\n"
        "Он должен соответствовать следующим критериям:\n\n"
        "1) Более 8 символов\n"
        "2) Должен содержать 1 спец.символ, число, большой и маленький символ\n"
        "3) Разрешено использовать только латиницу"
    )
    return text_message
