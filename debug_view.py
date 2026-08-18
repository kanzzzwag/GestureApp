"""Отладочный CLI-режим: окно OpenCV с оверлеем сырых метрик (EAR/MAR/Smile/
Eyebrow) для калибровки порогов жестов. Основное приложение запускается
через main.py (GUI)."""
import cv2
import sys
from utils.config_mgr import ConfigManager
from core.detector import BlinkDetector
from core.controller import ActionController


def main():
    config_mgr = ConfigManager()
    detector = BlinkDetector()
    controller = ActionController(config_mgr)

    cap = cv2.VideoCapture(config_mgr.config["camera_index"])

    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to capture frame from camera. Exiting...")
            break

        # Отражение кадра по горизонтали[cite: 1]
        frame = cv2.flip(frame, 1)

        # Получаем данные лица
        features = detector.process_frame(frame)

        # Выполняем действия pyautogui
        controller.process_actions(features)

        # Отрисовка значений, как в оригинале[cite: 1]
        if features["landmarks"]:
            cv2.putText(frame, f'Eyebrow Raise: {features["eyebrow_raise"]:.2f}', (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f'Smile Ratio: {features["smile"]:.2f}', (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f'MAR: {features["mar"]:.2f}', (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f'EAR (L/R avg): {features["left_ear"]:.2f} / {features["right_ear"]:.2f} / {features["ear"]:.2f}', (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow('Blink To Swipe (debug)', frame)

        # Выход по кнопке 'q'[cite: 1]
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    cap.release()
    sys.exit()


if __name__ == "__main__":
    main()
