from valutatrade_hub.core.models import Portfolio, User


def main():
    print("--- Создаём пользователя ---")
    user = User.register(user_id=1, username="alice", password="qwerty")

    print("\n--- Создаём портфель ---")
    portfolio = Portfolio(user_id=user.user_id, user=user)
    
    # Добавляем кошельки
    usd_wallet = portfolio.add_currency("usd")
    usd_wallet.deposit(1500.0)
    
    btc_wallet = portfolio.add_currency("BTC")
    btc_wallet.deposit(0.05)
    
    eur_wallet = portfolio.add_currency("EUR")
    eur_wallet.deposit(200.0)

    print(f"Кошельки в портфеле: {list(portfolio.wallets.keys())}")
    print(f"Баланс USD: {portfolio.get_wallet('USD').get_balance_info()}")

    print("\n--- Общая стоимость в USD ---")
    total_usd = portfolio.get_total_value(base_currency="USD")
    print(f"Всего в USD: {total_usd:.2f}")

    print("\n--- Общая стоимость в EUR ---")
    total_eur = portfolio.get_total_value(base_currency="EUR")
    print(f"Всего в EUR: {total_eur:.2f}")

    print("\n--- Проверка ошибок ---")
    try:
        portfolio.add_currency("USD")  # Должна быть ошибка, он уже есть
    except ValueError as e:
        print("Поймали ошибку:", e)

    print("\n--- Данные для JSON ---")
    print(portfolio.to_dict())


if __name__ == "__main__":
    main()