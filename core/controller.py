import logging
import time
import pyautogui

logger = logging.getLogger(__name__)


class ActionController:
    def __init__(self, config_manager):
        self.cfg = config_manager.config

        # Таймеры и счетчики из твоего кода
        self.is_eyes_closed = False
        self.blink_counter = 0
        self.first_blink_time = 0
        self.last_swipe_up_time = 0
        self.last_smile_time = 0

        # Phase 1: таймеры для новых жестов
        self.last_eyebrow_time = 0
        self.last_wink_left_time = 0
        self.last_wink_right_time = 0

    def _fire(self, gesture_name, log_message):
        """Выполняет действие, привязанное к жесту в config["gestures"].
        Если для жеста не назначена клавиша (null в конфиге), действие не
        выполняется - жест просто логируется (удобно для калибровки новых жестов).
        """
        logger.info(log_message)
        key = self.cfg["gestures"].get(gesture_name)
        if key:
            try:
                pyautogui.press(key)
            except Exception:
                # Например, сработал pyautogui FAILSAFE (курсор в углу экрана) -
                # не должно ронять весь поток распознавания из-за одного жеста.
                logger.exception("Не удалось выполнить действие для жеста '%s' (клавиша '%s')", gesture_name, key)

    def process_actions(self, features):
        if features["landmarks"] is None:
            return

        current_time = time.time()
        avg_ear = features["ear"]
        left_ear = features["left_ear"]
        right_ear = features["right_ear"]
        mar = features["mar"]
        smile_ratio = features["smile"]
        eyebrow_raise = features["eyebrow_raise"]

        ear_threshold = self.cfg["ear_threshold"]

        # Различаем обычное моргание (закрыты ОБА глаза) и подмигивание (закрыт один,
        # второй явно открыт) - иначе подмигивание могло бы ложно засчитаться как
        # моргание из-за усреднённого avg_ear.
        both_eyes_closed = left_ear < ear_threshold and right_ear < ear_threshold
        is_wink_left = left_ear < ear_threshold and right_ear > (ear_threshold + self.cfg["wink_open_margin"])
        is_wink_right = right_ear < ear_threshold and left_ear > (ear_threshold + self.cfg["wink_open_margin"])

        # 1. Логика двойного моргания (Стрелка Вниз)[cite: 1]
        if both_eyes_closed:
            if not self.is_eyes_closed:
                self.is_eyes_closed = True
                if self.blink_counter == 0:
                    self.first_blink_time = current_time
                    self.blink_counter = 1
                elif self.blink_counter == 1:
                    if (current_time - self.first_blink_time) <= self.cfg["double_blink_delay"]:
                        self._fire("double_blink", "Double Blink Detected")
                        self.blink_counter = 0
                    else:
                        self.first_blink_time = current_time
                        self.blink_counter = 1
        else:
            self.is_eyes_closed = False

        if self.blink_counter == 1 and (current_time - self.first_blink_time) > self.cfg["double_blink_delay"]:
            self.blink_counter = 0

        # 2. Логика открытия рта (Стрелка Вверх)[cite: 1]
        if mar > self.cfg["mar_threshold"] and (current_time - self.last_swipe_up_time) > self.cfg["swipe_up_cooldown"]:
            self._fire("mouth_open", "Mouth Opened! Swipe Up Detected")
            self.last_swipe_up_time = current_time

        # 3. Логика улыбки (Клавиша L)[cite: 1]
        if smile_ratio > self.cfg["smile_threshold"] and (current_time - self.last_smile_time) > self.cfg["smile_cooldown"]:
            self._fire("smile", "Smile Detected! Like Pressed")
            self.last_smile_time = current_time

        # --- Phase 1 жесты. Действие берётся из config["gestures"]; пока там
        # null - жест только логируется, ничего не нажимается. ---

        # 4. Подмигивание левым/правым глазом (Wink)
        if is_wink_left and (current_time - self.last_wink_left_time) > self.cfg["wink_cooldown"]:
            self._fire("wink_left", f"Wink Detected (Left) | left_ear={left_ear:.2f} right_ear={right_ear:.2f}")
            self.last_wink_left_time = current_time
        elif is_wink_right and (current_time - self.last_wink_right_time) > self.cfg["wink_cooldown"]:
            self._fire("wink_right", f"Wink Detected (Right) | left_ear={left_ear:.2f} right_ear={right_ear:.2f}")
            self.last_wink_right_time = current_time

        # 5. Поднятие бровей (Eyebrow Raise)
        if eyebrow_raise > self.cfg["eyebrow_threshold"] and (current_time - self.last_eyebrow_time) > self.cfg["eyebrow_cooldown"]:
            self._fire("eyebrow_raise", f"Eyebrow Raise Detected | value={eyebrow_raise:.2f}")
            self.last_eyebrow_time = current_time