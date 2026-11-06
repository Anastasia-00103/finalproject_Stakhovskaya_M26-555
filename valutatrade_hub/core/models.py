"""Классы предметной области ValutaTrade Hub."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime


class User:
    """Пользователь системы.

    Все атрибуты приватные (по требованию задания):
      _user_id, _username, _hashed_password, _salt, _registration_date.
    Доступ — через геттеры/сеттеры с валидацией.
    """

    MIN_PASSWORD_LENGTH = 4

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ) -> None:
        # Присваиваем через сеттеры, чтобы валидация отработала и в конструкторе
        self.user_id = user_id
        self.username = username
        self._hashed_password = hashed_password  # без сеттера — менять только через change_password
        self._salt = salt
        self.registration_date = registration_date

    # ------------------------------------------------------------------ #
    # Геттеры / сеттеры
    # ------------------------------------------------------------------ #

    @property
    def user_id(self) -> int:
        return self._user_id

    @user_id.setter
    def user_id(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("user_id должен быть положительным целым числом")
        self._user_id = value

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    @registration_date.setter
    def registration_date(self, value: datetime) -> None:
        if not isinstance(value, datetime):
            raise ValueError("registration_date должен быть datetime")
        self._registration_date = value

    # ------------------------------------------------------------------ #
    # Хеширование
    # ------------------------------------------------------------------ #

    @staticmethod
    def _make_hash(password: str, salt: str) -> str:
        """Односторонний псевдо-хеш: sha256(password + salt)."""
        return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

    @staticmethod
    def _generate_salt() -> str:
        return secrets.token_hex(8)

    # ------------------------------------------------------------------ #
    # Публичные методы
    # ------------------------------------------------------------------ #

    def verify_password(self, password: str) -> bool:
        """Проверяет, совпадает ли пароль с сохранённым хешем."""
        return secrets.compare_digest(
            self._make_hash(password, self._salt),
            self._hashed_password,
        )

    def change_password(self, new_password: str) -> None:
        """Меняет пароль: валидирует длину, генерирует новую соль и хеш."""
        if not isinstance(new_password, str) or len(new_password) < self.MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Пароль должен быть не короче {self.MIN_PASSWORD_LENGTH} символов"
            )
        self._salt = self._generate_salt()
        self._hashed_password = self._make_hash(new_password, self._salt)

    def get_user_info(self) -> str:
        """Возвращает информацию о пользователе (без пароля и соли)."""
        return (
            f"User(id={self._user_id}, "
            f"username='{self._username}', "
            f"registered={self._registration_date.isoformat()})"
        )

    # ------------------------------------------------------------------ #
    # Фабричный метод для регистрации нового пользователя
    # ------------------------------------------------------------------ #

    @classmethod
    def register(cls, user_id: int, username: str, password: str) -> "User":
        """Создаёт нового пользователя с хешированием пароля."""
        if len(password) < cls.MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Пароль должен быть не короче {cls.MIN_PASSWORD_LENGTH} символов"
            )
        salt = cls._generate_salt()
        hashed = cls._make_hash(password, salt)
        return cls(
            user_id=user_id,
            username=username,
            hashed_password=hashed,
            salt=salt,
            registration_date=datetime.now(),
        )

    # ------------------------------------------------------------------ #
    # Сериализация (формат совпадает с users.json из задания)
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            user_id=int(data["user_id"]),
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=datetime.fromisoformat(data["registration_date"]),
        )

class Wallet:
    """Кошелёк пользователя для одной конкретной валюты.

    Приватный атрибут: _balance.
    Публичное свойство: balance (геттер + сеттер с валидацией).
    """

    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")
        # Код валюты храним в верхнем регистре: usd -> USD
        self.currency_code = currency_code.strip().upper()
        # Присваиваем через сеттер, чтобы валидация отработала и в конструкторе
        self.balance = balance

    # ------------------------------------------------------------------ #
    # Свойство balance (геттер + сеттер)
    # ------------------------------------------------------------------ #

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    # ------------------------------------------------------------------ #
    # Публичные методы
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate_amount(amount: float) -> float:
        """Проверяет, что сумма — положительное число, возвращает float."""
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом")
        return float(amount)

    def deposit(self, amount: float) -> None:
        """Пополнение баланса."""
        amount = self._validate_amount(amount)
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        """Снятие средств. Проверяет, что сумма не превышает баланс."""
        amount = self._validate_amount(amount)
        if amount > self._balance:
            raise ValueError(
                f"Недостаточно средств: баланс {self._balance} {self.currency_code}"
            )
        self.balance -= amount

    def get_balance_info(self) -> str:
        """Возвращает строку с текущим балансом."""
        return f"{self._balance:.8f} {self.currency_code}"

    # ------------------------------------------------------------------ #
    # Сериализация (формат совпадает с portfolios.json из задания)
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        return cls(
            currency_code=data["currency_code"],
            balance=float(data["balance"]),
        )