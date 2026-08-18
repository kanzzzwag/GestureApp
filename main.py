import logging

from utils.logger import setup_logging

logger = logging.getLogger(__name__)


def main():
    setup_logging()
    try:
        from gui.app_window import AppWindow
        app = AppWindow()
        app.mainloop()
    except Exception:
        # В --noconsole сборке трейсбек больше нигде не увидеть, кроме app.log.
        logger.exception("Необработанная ошибка, приложение завершилось аварийно")
        raise


if __name__ == "__main__":
    main()
