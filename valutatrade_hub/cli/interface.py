import sys

from valutatrade_hub.core import usecases


def run_cli():
    """Главный цикл командной строки."""
    print("Добро пожаловать в ValutaTrade Hub!")
    print("Доступные команды:")
    print("  register, login, show-portfolio, buy, sell, get-rate, exit.")

    while True:
        try:
            cmd_input = input("\nvalutatrade> ").strip()
            if not cmd_input:
                continue

            parts = cmd_input.split()
            command = parts[0].lower()
            args = parts[1:]

            if command == "exit":
                print("Выход...")
                sys.exit(0)

            elif command == "register":
                if len(args) != 2:
                    print("Использование: register <username> <password>")
                    continue
                print(usecases.register(args[0], args[1]))

            elif command == "login":
                if len(args) != 2:
                    print("Использование: login <username> <password>")
                    continue
                print(usecases.login(args[0], args[1]))

            elif command == "show-portfolio":
                portfolio = usecases.get_portfolio()
                if not portfolio:
                    print("Портфель пуст.")
                else:
                    print("Ваш портфель:")
                    for curr, bal in portfolio.items():
                        print(f"  {curr}: {bal}")

            elif command == "get-rate":
                if len(args) != 1:
                    print("Использование: get-rate <currency_code>")
                    continue
                print(usecases.get_rate(args[0]))

            elif command == "buy":
                if len(args) != 3:
                    print("Использование: buy <from_currency> <to_currency> <amount>")
                    continue
                print(usecases.buy(args[0], args[1], float(args[2])))

            elif command == "sell":
                if len(args) != 3:
                    print("Использование: sell <from_currency> <to_currency> <amount>")
                    continue
                print(usecases.sell(args[0], args[1], float(args[2])))

            else:
                print(f"Неизвестная команда: {command}")

        except ValueError as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Системная ошибка: {e}")