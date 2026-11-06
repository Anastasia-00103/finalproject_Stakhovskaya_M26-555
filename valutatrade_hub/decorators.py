import functools
import inspect

from .logging_config import logger


def log_action(action_name: str):
    """Декоратор для логирования доменных операций."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Связываем аргументы функции с их именами
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Безопасно достаем аргументы для лога
            currency = bound_args.arguments.get("currency", "N/A")
            amount = bound_args.arguments.get("amount", "N/A")

            try:
                result = func(*args, **kwargs)
                logger.info(
                    f"{action_name} currency='{currency}' amount={amount} "
                    f"result=OK"
                )
                return result
            except Exception as e:
                # Логируем ошибку, но пробрасываем исключение дальше
                logger.error(
                    f"{action_name} currency='{currency}' amount={amount} "
                    f"result=ERROR error_type='{type(e).__name__}' msg='{e}'"
                )
                raise

        return wrapper

    return decorator