import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging():
    """Настраивает корневой логгер с ротацией файлов."""
    # Создаем папку logs в корне проекта
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "actions.log"

    logger = logging.getLogger("valutatrade")
    logger.setLevel(logging.INFO)

    # Если логгер уже настроен (при повторном импорте), не дублируем хендлеры
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Ротация: максимум 1 МБ на файл, храним 5 старых копий
    file_handler = RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Дублируем в консоль (опционально, но удобно для отладки)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()