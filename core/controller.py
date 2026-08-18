import logging
import time
import pyautogui

logger = logging.getLogger(__name__)


class ActionController:
    def __init__(self, config_manager):
        self.cfg = config_manager.config

        # Таймеры и счётчики
        self.is_eyes_closed = False
        self.blink_counter = 0
        self.first_blink_time = 0
        self.last_swipe_up_time = 0
        self.last_smile_time = 0
        self.last_eyebrow_time = 0
        self.last_wink_left_time = 0
        self.last_wink_right_time = 0

    def _fire(self, gesture_name, log_message):
        """Выполняет действие, привязанное к жесту в config["gestures"]."""
        logger.info(log_message)
        key = self.cfg["gestures"].get(gesture_name)
        if key:
            try:
                pyautogui.press(key)
            except Exception:
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

        # Моргание vs подмигивание
        both_eyes_closed = left_ear < ear_threshold and right_ear < ear_threshold
        is_wink_left = left_ear < ear_threshold and right_ear > (ear_threshold + self.cfg["wink_open_margin"])
        is_wink_right = right_ear < ear_threshold and left_ear > (ear_threshold + self.cfg["wink_open_margin"])

        # 1. Двойное моргание
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

        # 2. Открытие рта
        if mar > self.cfg["mar_threshold"] and (current_time - self.last_swipe_up_time) > self.cfg["swipe_up_cooldown"]:
            self._fire("mouth_open", "Mouth Opened! Swipe Up Detected")
            self.last_swipe_up_time = current_time

        # 3. Улыбка
        if smile_ratio > self.cfg["smile_threshold"] and (current_time - self.last_smile_time) > self.cfg["smile_cooldown"]:
            self._fire("smile", "Smile Detected! Like Pressed")
            self.last_smile_time = current_time

        # 4. Подмигивание
        if is_wink_left and (current_time - self.last_wink_left_time) > self.cfg["wink_cooldown"]:
            self._fire("wink_left", f"Wink Detected (Left) | left_ear={left_ear:.2f} right_ear={right_ear:.2f}")
            self.last_wink_left_time = current_time
        elif is_wink_right and (current_time - self.last_wink_right_time) > self.cfg["wink_cooldown"]:
            self._fire("wink_right", f"Wink Detected (Right) | left_ear={left_ear:.2f} right_ear={right_ear:.2f}")
            self.last_wink_right_time = current_time

        # 5. Поднятие бровей
        if eyebrow_raise > self.cfg["eyebrow_threshold"] and (current_time - self.last_eyebrow_time) > self.cfg["eyebrow_cooldown"]:
            self._fire("eyebrow_raise", f"Eyebrow Raise Detected | value={eyebrow_raise:.2f}")
            self.last_eyebrow_time = current_time