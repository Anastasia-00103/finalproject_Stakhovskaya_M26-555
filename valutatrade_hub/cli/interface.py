import argparse
import sys

from valutatrade_hub.core import usecases


def parse_args(args: list[str]):
    """Парсит флаги, переданные после команды."""
    parser = argparse.ArgumentParser(exit_on_error=False, add_help=False)

    parser.add_argument("--username", type=str)
    parser.add_argument("--password", type=str)
    parser.add_argument("--base", type=str, default="USD")
    parser.add_argument("--currency", type=str)
    parser.add_argument("--amount", type=float)
    parser.add_argument("--from", dest="from_curr", type=str)
    parser.add_argument("--to", dest="to_curr", type=str)

    try:
        # parse_known_args позволяет игнорировать лишние флаги
        # (например, если передали --base для register)
        parsed, _ = parser.parse_known_args(args)
        return parsed
    except argparse.ArgumentError as e:
        raise ValueError(f"Ошибка в аргументах: {e}")


def run_cli():
    """Главный цикл командной строки."""
    print("Добро пожаловать в ValutaTrade Hub!")
    print("Доступные команды:")
    print("  register, login, show-portfolio, buy, sell, get-rate, exit.")
    print("Введите 'help' для подсказки по аргументам.")

    while True:
        try:
            cmd_input = input("\n> ").strip()
            if not cmd_input:
                continue

            parts = cmd_input.split()
            command = parts[0].lower()
            args = parts[1:]

            if command == "exit":
                print("Выход...")
                return     
            elif command == "help":
                print("Примеры:")
                print("  register --username alice --password 1234")
                print("  login --username alice --password 1234")
                print("  show-portfolio --base USD")
                print("  buy --currency BTC --amount 0.05")
                print("  sell --currency BTC --amount 0.01")
                print("  get-rate --from USD --to BTC")
                continue

            parsed_args = parse_args(args)

            if command == "register":
                if not parsed_args.username or not parsed_args.password:
                    raise ValueError("Необходимы флаги --username и --password")
                print(usecases.register(parsed_args.username, parsed_args.password))

            elif command == "login":
                if not parsed_args.username or not parsed_args.password:
                    raise ValueError("Необходимы флаги --username и --password")
                print(usecases.login(parsed_args.username, parsed_args.password))

            elif command == "show-portfolio":
                print(usecases.show_portfolio(base=parsed_args.base))

            elif command == "get-rate":
                if not parsed_args.from_curr or not parsed_args.to_curr:
                    raise ValueError("Необходимы флаги --from и --to")
                print(usecases.get_rate(parsed_args.from_curr, parsed_args.to_curr))

            elif command == "buy":
                if not parsed_args.currency or parsed_args.amount is None:
                    raise ValueError("Необходимы флаги --currency и --amount")
                print(usecases.buy(parsed_args.currency, parsed_args.amount))

            elif command == "sell":
                if not parsed_args.currency or parsed_args.amount is None:
                    raise ValueError("Необходимы флаги --currency и --amount")
                print(usecases.sell(parsed_args.currency, parsed_args.amount))

            else:
                print(f"Неизвестная команда: {command}")

        except ValueError as e:
            print(f"Ошибка: {e}")
        except SystemExit:
            pass
        except Exception as e:
            print(f"Системная ошибка: {e}")