from datetime import datetime

from ..decorators import log_action
from ..infra.database import DatabaseManager
from ..logging_config import logger
from .currencies import get_currency
from .exceptions import InsufficientFundsError
from .models import Portfolio, User

CURRENT_USER: User | None = None
db = DatabaseManager()


def get_current_user() -> User | None:
    return CURRENT_USER


def register(username: str, password: str) -> str:
    global CURRENT_USER
    users_data = db.load("users.json")

    if any(u["username"] == username for u in users_data):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    new_id = max([u["user_id"] for u in users_data], default=0) + 1
    user = User.register(user_id=new_id, username=username, password=password)
    users_data.append(user.to_dict())
    db.save("users.json", users_data)

    portfolios_data = db.load("portfolios.json")
    portfolio = Portfolio(user_id=user.user_id, user=user)
    portfolios_data.append(portfolio.to_dict())
    db.save("portfolios.json", portfolios_data)

    logger.info(f"REGISTER user='{username}' result=OK")
    return (
        f"Пользователь '{username}' зарегистрирован (id={new_id}). "
        f"Войдите: login --username {username} --password ****"
    )


def login(username: str, password: str) -> str:
    global CURRENT_USER
    users_data = db.load("users.json")

    for u_data in users_data:
        if u_data["username"] == username:
            user = User.from_dict(u_data)
            if user.verify_password(password):
                CURRENT_USER = user
                logger.info(f"LOGIN user='{username}' result=OK")
                return f"Вы вошли как '{username}'"
            else:
                raise ValueError("Неверный пароль")

    raise ValueError(f"Пользователь '{username}' не найден")


def show_portfolio(base: str = "USD") -> str:
    if not CURRENT_USER:
        raise ValueError("Сначала выполните login")

    base = base.upper()
    get_currency(base)  # Валидация базовой валюты

    portfolios_data = db.load("portfolios.json")
    p_data = next(
        (p for p in portfolios_data if p["user_id"] == CURRENT_USER.user_id), None
    )
    if not p_data:
        raise ValueError("Портфель не найден")

    portfolio = Portfolio.from_dict(p_data, CURRENT_USER)
    if not portfolio.wallets:
        return "Портфель пуст."

    rates = {"USD": 1.0, "EUR": 1.08, "RUB": 0.011, "BTC": 60000.0, "ETH": 3000.0}

    lines = [f"Портфель пользователя '{CURRENT_USER.username}' (база: {base}):"]
    total_value = 0.0

    for code, wallet in portfolio.wallets.items():
        if wallet.balance == 0 or code not in rates:
            continue

        usd_value = wallet.balance * rates[code]
        base_value = usd_value / rates[base]
        total_value += base_value

        bal_fmt = (
            f"{wallet.balance:.4f}"
            if wallet.balance < 1
            else f"{wallet.balance:.2f}"
        )
        lines.append(f"- {code}: {bal_fmt}  → {base_value:.2f} {base}")

    lines.append("-" * 33)
    lines.append(f"ИТОГО: {total_value:,.2f} {base}".replace(",", " "))
    return "\n".join(lines)


def get_rate(from_curr: str, to_curr: str) -> str:
    from_curr = get_currency(from_curr).code
    to_curr = get_currency(to_curr).code

    rates = {"USD": 1.0, "EUR": 1.08, "RUB": 0.011, "BTC": 60000.0, "ETH": 3000.0}

    if from_curr not in rates or to_curr not in rates:
        raise ValueError("Курс недоступен.")

    rate = rates[from_curr] / rates[to_curr]
    reverse_rate = rates[to_curr] / rates[from_curr]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fmt = ".8f" if rate < 0.01 else ".2f"

    return (
        f"Курс {from_curr}→{to_curr}: {rate:{fmt}} (обновлено: {now_str})\n"
        f"Обратный курс {to_curr}→{from_curr}: {reverse_rate:{fmt}}"
    )


@log_action("BUY")
def buy(currency: str, amount: float) -> str:
    if not CURRENT_USER:
        raise ValueError("Сначала выполните login")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    currency = get_currency(currency).code

    portfolios_data = db.load("portfolios.json")
    p_idx = next(
        (
            i
            for i, p in enumerate(portfolios_data)
            if p["user_id"] == CURRENT_USER.user_id
        ),
        None,
    )
    if p_idx is None:
        raise ValueError("Портфель не найден")

    portfolio = Portfolio.from_dict(portfolios_data[p_idx], CURRENT_USER)

    if not portfolio.wallets.get(currency):
        portfolio.add_currency(currency)

    wallet = portfolio.get_wallet(currency)
    old_balance = wallet.balance
    wallet.deposit(amount)

    portfolios_data[p_idx] = portfolio.to_dict()
    db.save("portfolios.json", portfolios_data)

    rates = {"USD": 1.0, "EUR": 1.08, "RUB": 0.011, "BTC": 60000.0, "ETH": 3000.0}
    rate = rates.get(currency, 1.0)
    cost_usd = amount * rate

    return (
        f"Покупка выполнена: {amount:.4f} {currency} "
        f"по курсу {rate:.2f} USD/{currency}\n"
        f"Изменения в портфеле:\n"
        f"- {currency}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
        f"Оценочная стоимость покупки: {cost_usd:,.2f} USD".replace(",", " ")
    )


@log_action("SELL")
def sell(currency: str, amount: float) -> str:
    if not CURRENT_USER:
        raise ValueError("Сначала выполните login")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    currency = get_currency(currency).code

    portfolios_data = db.load("portfolios.json")
    p_idx = next(
        (
            i
            for i, p in enumerate(portfolios_data)
            if p["user_id"] == CURRENT_USER.user_id
        ),
        None,
    )
    if p_idx is None:
        raise ValueError("Портфель не найден")

    portfolio = Portfolio.from_dict(portfolios_data[p_idx], CURRENT_USER)

    if not portfolio.wallets.get(currency):
        raise ValueError(f"У вас нет кошелька '{currency}'.")

    wallet = portfolio.get_wallet(currency)
    if wallet.balance < amount:
        raise InsufficientFundsError(
            available=wallet.balance, required=amount, code=currency
        )

    old_balance = wallet.balance
    wallet.withdraw(amount)

    portfolios_data[p_idx] = portfolio.to_dict()
    db.save("portfolios.json", portfolios_data)

    rates = {"USD": 1.0, "EUR": 1.08, "RUB": 0.011, "BTC": 60000.0, "ETH": 3000.0}
    rate = rates.get(currency, 1.0)
    revenue_usd = amount * rate

    return (
        f"Продажа выполнена: {amount:.4f} {currency} "
        f"по курсу {rate:.2f} USD/{currency}\n"
        f"Изменения в портфеле:\n"
        f"- {currency}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
        f"Оценочная выручка: {revenue_usd:,.2f} USD".replace(",", " ")
    )