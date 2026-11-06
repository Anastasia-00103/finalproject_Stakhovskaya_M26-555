import argparse
import json
from pathlib import Path

from valutatrade_hub.core import usecases
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.parser_service.updater import RatesUpdater


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
    parser.add_argument("--source", type=str)
    parser.add_argument("--top", type=int)

    try:
        parsed, _ = parser.parse_known_args(args)
        return parsed
    except argparse.ArgumentError as e:
        raise ValueError(f"Ошибка в аргументах: {e}")


def run_cli():
    """Главный цикл командной строки."""
    print("Добро пожаловать в ValutaTrade Hub!")
    print("Доступные команды:")
    print("  register, login, show-portfolio, buy, sell, get-rate,")
    print("  update-rates, show-rates, exit.")
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
                print("  update-rates [--source coingecko]")
                print("  show-rates [--currency BTC] [--top 2]")
                continue

            parsed_args = parse_args(args)

            # --- Команды пользователя ---
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

            # --- Команды парсера ---
            elif command == "update-rates":
                updater = RatesUpdater()
                print(updater.run_update(target_source=parsed_args.source))

            elif command == "show-rates":
                rates_file = Path("data/rates.json")
                if not rates_file.exists():
                    print(
                        "Локальный кеш курсов пуст. "
                        "Выполните 'update-rates', чтобы загрузить данные."
                    )
                    continue

                with open(rates_file, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        print("Ошибка чтения кеша курсов.")
                        continue

                pairs = data.get("pairs", {})
                if not pairs:
                    print("Локальный кеш курсов пуст. Выполните 'update-rates'.")
                    continue

                # Фильтр по валюте
                if parsed_args.currency:
                    target = parsed_args.currency.upper()
                    pairs = {k: v for k, v in pairs.items() if k.startswith(target)}
                    if not pairs:
                        print(f"Курс для '{target}' не найден в кеше.")
                        continue

                # Фильтр по топу
                if parsed_args.top:
                    sorted_pairs = sorted(
                        pairs.items(), key=lambda x: x[1]["rate"], reverse=True
                    )
                    pairs = dict(sorted_pairs[: parsed_args.top])

                updated = data.get("last_refresh", "unknown")
                print(f"Rates from cache (updated at {updated}):")
                for pair, info in pairs.items():
                    print(f"- {pair}: {info['rate']}")

            else:
                print(f"Неизвестная команда: {command}")

        # Перехват пользовательских исключений
        except InsufficientFundsError as e:
            print(f"Ошибка: {e}")
        except CurrencyNotFoundError as e:
            print(
                f"Ошибка: {e}. Воспользуйтесь 'help', "
                f"чтобы увидеть поддерживаемые коды."
            )
        except ApiRequestError as e:
            print(f"Ошибка: {e}. Повторите попытку позже.")

        # Перехват стандартных исключений и ошибок валидации
        except ValueError as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Системная ошибка: {e}")