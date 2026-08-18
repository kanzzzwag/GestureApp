"""Глобальное логирование в файл (app.log)."""
import logging
import sys
from logging.handlers import RotatingFileHandler
import os

from utils.paths import get_data_dir, is_frozen

_configured = False


def setup_logging():
    """Настраивает root-логгер один раз за запуск приложения."""
    global _configured
    if _configured:
        return
    _configured = True

    log_path = os.path.join(get_data_dir(), "app.log")

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        log_path, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    root.addHandler(file_handler)

    # Dev-режим: дублируем в консоль
    if not is_frozen():
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        root.addHandler(console_handler)

    logging.getLogger(__name__).info("=== GestureApp запущен (log: %s) ===", log_path)
