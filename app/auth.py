from passlib.context import CryptContext

password_contex = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """Хешировка пароля"""
    return password_contex.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return password_contex.verify(plain_password, hashed_password)
