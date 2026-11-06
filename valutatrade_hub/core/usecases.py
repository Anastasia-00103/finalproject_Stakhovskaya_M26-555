from .models import Portfolio, User
from .utils import load_json, save_json

CURRENT_USER: User | None = None

# Заглушка курсов (вместо API)
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
        raise ValueError("Пользователь с таким именем уже существует")

    new_id = max([u["user_id"] for u in users_data], default=0) + 1
    user = User.register(user_id=new_id, username=username, password=password)
    users_data.append(user.to_dict())
    save_json("users.json", users_data)

    portfolios_data = load_json("portfolios.json")
    portfolio = Portfolio(user_id=user.user_id, user=user)
    portfolios_data.append(portfolio.to_dict())
    save_json("portfolios.json", portfolios_data)

    return f"Пользователь {username} успешно зарегистрирован (ID: {new_id})."


def login(username: str, password: str) -> str:
    global CURRENT_USER
    users_data = load_json("users.json")

    for u_data in users_data:
        if u_data["username"] == username:
            user = User.from_dict(u_data)
            if user.verify_password(password):
                CURRENT_USER = user
                return f"Вы вошли как {username} (ID: {user.user_id})."
            else:
                raise ValueError("Неверный пароль")

    raise ValueError("Пользователь не найден")


def get_portfolio() -> dict:
    if not CURRENT_USER:
        raise ValueError("Необходимо войти в систему (login).")

    portfolios_data = load_json("portfolios.json")
    for p_data in portfolios_data:
        if p_data["user_id"] == CURRENT_USER.user_id:
            p = Portfolio.from_dict(p_data, CURRENT_USER)
            return {code: w.balance for code, w in p.wallets.items()}

    return {}


def _get_rate(currency_code: str) -> float:
    currency_code = currency_code.upper()
    if currency_code in MOCK_RATES:
        return MOCK_RATES[currency_code]

    rates_data = load_json("rates.json")
    key = f"{currency_code}_USD"
    if isinstance(rates_data, dict) and key in rates_data:
        return rates_data[key]["rate"]

    raise ValueError(f"Курс для {currency_code} не найден.")


def get_rate(currency_code: str) -> str:
    rate = _get_rate(currency_code)
    return f"Курс {currency_code.upper()} к USD: {rate}"


def _execute_trade(action: str, from_curr: str, to_curr: str, amount: float) -> str:
    if not CURRENT_USER:
        raise ValueError("Необходимо войти в систему (login).")

    if amount <= 0:
        raise ValueError("Сумма должна быть больше нуля.")

    from_curr = from_curr.upper()
    to_curr = to_curr.upper()

    rate_from = _get_rate(from_curr)
    rate_to = _get_rate(to_curr)

    exchange_rate = rate_from / rate_to
    converted_amount = amount * exchange_rate

    portfolios_data = load_json("portfolios.json")
    
    p_idx = None
    for i, p in enumerate(portfolios_data):
        if p["user_id"] == CURRENT_USER.user_id:
            p_idx = i
            break

    if p_idx is None:
        raise ValueError("Портфель не найден.")

    portfolio = Portfolio.from_dict(portfolios_data[p_idx], CURRENT_USER)

    if not portfolio.wallets.get(from_curr):
        portfolio.add_currency(from_curr)
    if not portfolio.wallets.get(to_curr):
        portfolio.add_currency(to_curr)

    wallet_from = portfolio.get_wallet(from_curr)
    wallet_to = portfolio.get_wallet(to_curr)

    if action == "buy" or action == "sell":
        if wallet_from.balance < amount:
            raise ValueError(
                f"Недостаточно средств в {from_curr}. Баланс: {wallet_from.balance}"
            )
        wallet_from.withdraw(amount)
        wallet_to.deposit(converted_amount)

    portfolios_data[p_idx] = portfolio.to_dict()
    save_json("portfolios.json", portfolios_data)

    return (
        f"Успешно {action}: потрачено {amount} {from_curr}, "
        f"получено {converted_amount:.6f} {to_curr}."
    )


def buy(from_curr: str, to_curr: str, amount: float) -> str:
    return _execute_trade("buy", from_curr, to_curr, amount)


def sell(from_curr: str, to_curr: str, amount: float) -> str:
    return _execute_trade("sell", from_curr, to_curr, amount)