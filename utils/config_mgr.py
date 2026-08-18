import json
import logging
import os

from utils.paths import get_data_dir

logger = logging.getLogger(__name__)


class ConfigManager:
    def __init__(self, config_path=None):
        # По умолчанию config.json лежит в data-папке приложения (%APPDATA%
        # в собранном .exe, корень проекта при разработке) - см. utils/paths.py.
        self.config_path = config_path or os.path.join(get_data_dir(), "config.json")
        self.config = self.load_config()

    def _default_config(self):
        return {
            "camera_index": 0,             # Индекс веб-камеры (cv2.VideoCapture)

            "ear_threshold": 0.23,         # Порог моргания
            "double_blink_delay": 0.4,     # Задержка двойного моргания
            "mar_threshold": 0.5,          # Порог открытия рта
            "swipe_up_cooldown": 1.2,      # Кулдаун для свайпа вверх
            "smile_threshold": 0.36,       # Порог улыбки
            "smile_cooldown": 2.0,         # Кулдаун для улыбки

            # --- Phase 1: новые жесты ---
            "eyebrow_threshold": 0.20,     # Порог поднятия бровей (обычно ~0.14, поднятые ~0.17)
            "eyebrow_cooldown": 1.0,       # Кулдаун для поднятия бровей

            "wink_open_margin": 0.03,      # Насколько открытый глаз должен быть выше ear_threshold, чтобы не спутать с обычным морганием
            "wink_cooldown": 1.0,          # Кулдаун для подмигивания (отдельно лев./прав.)

            # --- Phase 2: маппинг "жест -> клавиша". null = действие не назначено. ---
            "gestures": {
                "double_blink": "down",
                "mouth_open": "up",
                "smile": "l",
                "eyebrow_raise": None,
                "wink_left": None,
                "wink_right": None,
            },
        }

    def load_config(self):
        default_config = self._default_config()

        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as file:
                try:
                    loaded_config = json.load(file)
                except json.JSONDecodeError:
                    logger.warning("config.json повреждён/не является валидным JSON, использую значения по умолчанию: %s", self.config_path)
                    loaded_config = {}

            loaded_gestures = loaded_config.pop("gestures", None)
            # Подмешиваем только ключи, которые всё ещё существуют в дефолтах -
            # так убранные из кода настройки (например, старый Head Tilt/Gaze)
            # сами уходят из config.json при следующем запуске, а не воскресают.
            default_config.update({k: v for k, v in loaded_config.items() if k in default_config})
            if loaded_gestures:
                default_config["gestures"].update(
                    {k: v for k, v in loaded_gestures.items() if k in default_config["gestures"]}
                )

        # Генерируем/актуализируем файл настроек (первый запуск или новые ключи).
        self.save_config(default_config)
        return default_config

    def save_config(self, config=None):
        config = config if config is not None else self.config
        try:
            with open(self.config_path, "w", encoding="utf-8") as file:
                json.dump(config, file, indent=4, ensure_ascii=False)
        except OSError:
            logger.exception("Не удалось сохранить config.json: %s", self.config_path)
