from datetime import datetime

from .models import Portfolio, User
from .utils import load_json, save_json

CURRENT_USER: User | None = None

# Заглушка курсов
MOCK_RATES = {
    "USD": 1.0,
    "EUR": 1.08,
    "BTC": 60000.0,
    "ETH": 3000.0,
    "RUB": 0.011,
}


def get_current_user() -> User | None:
    return CURRENT_USER


def register(username: str, password: str) -> str:
    global CURRENT_USER
    users_data = load_json("users.json")

    if any(u["username"] == username for u in users_data):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    new_id = max([u["user_id"] for u in users_data], default=0) + 1
    user = User.register(user_id=new_id, username=username, password=password)
    users_data.append(user.to_dict())
    save_json("users.json", users_data)

    portfolios_data = load_json("portfolios.json")
    portfolio = Portfolio(user_id=user.user_id, user=user)
    portfolios_data.append(portfolio.to_dict())
    save_json("portfolios.json", portfolios_data)

    return (
        f"Пользователь '{username}' зарегистрирован (id={new_id}). "
        f"Войдите: login --username {username} --password ****"
    )


def login(username: str, password: str) -> str:
    global CURRENT_USER
    users_data = load_json("users.json")

    for u_data in users_data:
        if u_data["username"] == username:
            user = User.from_dict(u_data)
            if user.verify_password(password):
                CURRENT_USER = user
                return f"Вы вошли как '{username}'"
            else:
                raise ValueError("Неверный пароль")

    raise ValueError(f"Пользователь '{username}' не найден")


def show_portfolio(base: str = "USD") -> str:
    if not CURRENT_USER:
        raise ValueError("Сначала выполните login")

    base = base.upper()
    if base not in MOCK_RATES:
        raise ValueError(f"Неизвестная базовая валюта '{base}'")

    portfolios_data = load_json("portfolios.json")
    p_data = None
    for p in portfolios_data:
        if p["user_id"] == CURRENT_USER.user_id:
            p_data = p
            break

    if not p_data:
        raise ValueError("Портфель не найден")

    portfolio = Portfolio.from_dict(p_data, CURRENT_USER)
    if not portfolio.wallets:
        return "Портфель пуст."

    base_rate = MOCK_RATES[base]
    lines = [f"Портфель пользователя '{CURRENT_USER.username}' (база: {base}):"]
    total_value = 0.0

    for code, wallet in portfolio.wallets.items():
        if wallet.balance == 0:
            continue

        if code not in MOCK_RATES:
            continue

        usd_value = wallet.balance * MOCK_RATES[code]
        base_value = usd_value / base_rate
        total_value += base_value

        if wallet.balance < 1:
            bal_fmt = f"{wallet.balance:.4f}"
        else:
            bal_fmt = f"{wallet.balance:.2f}"
        lines.append(f"- {code}: {bal_fmt}  → {base_value:.2f} {base}")

    lines.append("-" * 33)
    lines.append(f"ИТОГО: {total_value:,.2f} {base}".replace(",", " "))
    return "\n".join(lines)


def get_rate(from_curr: str, to_curr: str) -> str:
    from_curr = from_curr.upper()
    to_curr = to_curr.upper()

    if from_curr not in MOCK_RATES or to_curr not in MOCK_RATES:
        raise ValueError(
            f"Курс {from_curr}→{to_curr} недоступен. "
            f"Повторите попытку позже."
        )

    rate = MOCK_RATES[from_curr] / MOCK_RATES[to_curr]
    reverse_rate = MOCK_RATES[to_curr] / MOCK_RATES[from_curr]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fmt = ".8f" if rate < 0.01 else ".2f"

    return (
        f"Курс {from_curr}→{to_curr}: {rate:{fmt}} (обновлено: {now_str})\n"
        f"Обратный курс {to_curr}→{from_curr}: {reverse_rate:{fmt}}"
    )


def buy(currency: str, amount: float) -> str:
    if not CURRENT_USER:
        raise ValueError("Сначала выполните login")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    currency = currency.upper()
    if currency not in MOCK_RATES:
        raise ValueError(f"Не удалось получить курс для {currency}→USD")

    portfolios_data = load_json("portfolios.json")
    p_idx = None
    for i, p in enumerate(portfolios_data):
        if p["user_id"] == CURRENT_USER.user_id:
            p_idx = i
            break

    if p_idx is None:
        raise ValueError("Портфель не найден")

    portfolio = Portfolio.from_dict(portfolios_data[p_idx], CURRENT_USER)

    if not portfolio.wallets.get(currency):
        portfolio.add_currency(currency)

    wallet = portfolio.get_wallet(currency)
    old_balance = wallet.balance
    wallet.deposit(amount)

    portfolios_data[p_idx] = portfolio.to_dict()
    save_json("portfolios.json", portfolios_data)

    rate = MOCK_RATES[currency]
    cost_usd = amount * rate

    return (
        f"Покупка выполнена: {amount:.4f} {currency} "
        f"по курсу {rate:.2f} USD/{currency}\n"
        f"Изменения в портфеле:\n"
        f"- {currency}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
        f"Оценочная стоимость покупки: {cost_usd:,.2f} USD".replace(",", " ")
    )


def sell(currency: str, amount: float) -> str:
    if not CURRENT_USER:
        raise ValueError("Сначала выполните login")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    currency = currency.upper()

    portfolios_data = load_json("portfolios.json")
    p_idx = None
    for i, p in enumerate(portfolios_data):
        if p["user_id"] == CURRENT_USER.user_id:
            p_idx = i
            break

    if p_idx is None:
        raise ValueError("Портфель не найден")

    portfolio = Portfolio.from_dict(portfolios_data[p_idx], CURRENT_USER)

    if not portfolio.wallets.get(currency):
        raise ValueError(
            f"У вас нет кошелька '{currency}'. Добавьте валюту: "
            f"она создаётся автоматически при первой покупке."
        )

    wallet = portfolio.get_wallet(currency)
    if wallet.balance < amount:
        raise ValueError(
            f"Недостаточно средств: доступно {wallet.balance:.4f} {currency}, "
            f"требуется {amount:.4f} {currency}"
        )

    old_balance = wallet.balance
    wallet.withdraw(amount)

    portfolios_data[p_idx] = portfolio.to_dict()
    save_json("portfolios.json", portfolios_data)

    rate = MOCK_RATES.get(currency, 1.0)
    revenue_usd = amount * rate

    return (
        f"Продажа выполнена: {amount:.4f} {currency} "
        f"по курсу {rate:.2f} USD/{currency}\n"
        f"Изменения в портфеле:\n"
        f"- {currency}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
        f"Оценочная выручка: {revenue_usd:,.2f} USD".replace(",", " ")
    )