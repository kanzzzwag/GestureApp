import logging
import threading
import cv2

logger = logging.getLogger(__name__)


class GestureWorker:
    """Крутит цикл захвата камеры + распознавания жестов в отдельном потоке,
    чтобы GUI-mainloop (customtkinter/Tk) не блокировался обработкой кадров
    MediaPipe Tasks API, и наоборот - долгая отрисовка GUI не тормозила камеру.
    """

    def __init__(self, config_manager, detector_factory, controller_factory):
        self.config_manager = config_manager
        self._detector_factory = detector_factory
        self._controller_factory = controller_factory

        self._thread = None
        self._running = threading.Event()
        self._lock = threading.Lock()
        self._latest_frame = None

        self.camera_ok = False
        self.error = None

    @property
    def is_running(self):
        return self._running.is_set()

    def start(self):
        if self.is_running:
            return
        logger.info("Запуск распознавания (camera_index=%s)", self.config_manager.config["camera_index"])
        self.error = None
        self._running.set()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if self._thread is not None:
            logger.info("Остановка распознавания")
        self._running.clear()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        self.camera_ok = False
        with self._lock:
            self._latest_frame = None

    def get_preview_frame(self):
        """Возвращает копию последнего кадра (BGR) для превью в GUI, либо None."""
        with self._lock:
            return None if self._latest_frame is None else self._latest_frame.copy()

    def _run(self):
        try:
            # CAP_DSHOW: MSMF зависает при открытии камеры не из главного потока.
            cap = cv2.VideoCapture(self.config_manager.config["camera_index"], cv2.CAP_DSHOW)
        except Exception:
            logger.exception("Исключение при открытии камеры")
            self.error = "Не удалось открыть камеру"
            self._running.clear()
            return

        if not cap.isOpened():
            logger.error("Камера не открылась (index=%s)", self.config_manager.config["camera_index"])
            self.error = "Не удалось открыть камеру"
            self._running.clear()
            return

        try:
            detector = self._detector_factory()
            controller = self._controller_factory(self.config_manager)
        except Exception:
            logger.exception("Не удалось инициализировать детектор/контроллер (модель MediaPipe?)")
            self.error = "Ошибка инициализации распознавания"
            self._running.clear()
            cap.release()
            return

        self.camera_ok = True
        logger.info("Камера и детектор инициализированы, распознавание активно")

        # Разрыв связи с камерой считается только после нескольких неудач подряд
        MAX_CONSECUTIVE_READ_FAILURES = 15
        consecutive_read_failures = 0

        MAX_CONSECUTIVE_FRAME_ERRORS = 15
        consecutive_frame_errors = 0

        try:
            while self.is_running:
                success, frame = cap.read()
                if not success:
                    consecutive_read_failures += 1
                    if consecutive_read_failures >= MAX_CONSECUTIVE_READ_FAILURES:
                        logger.error("Потеряна связь с камерой после %d неудачных чтений подряд", consecutive_read_failures)
                        self.error = "Потеряна связь с камерой"
                        break
                    continue
                consecutive_read_failures = 0

                try:
                    frame = cv2.flip(frame, 1)
                    features = detector.process_frame(frame)
                    controller.process_actions(features)
                except Exception:
                    consecutive_frame_errors += 1
                    logger.exception("Ошибка обработки кадра (%d подряд)", consecutive_frame_errors)
                    if consecutive_frame_errors >= MAX_CONSECUTIVE_FRAME_ERRORS:
                        self.error = "Повторяющаяся ошибка распознавания"
                        break
                    continue
                consecutive_frame_errors = 0

                with self._lock:
                    self._latest_frame = frame
        finally:
            cap.release()
            self.camera_ok = False
            logger.info("Камера освобождена")
