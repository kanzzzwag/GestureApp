import logging
import os
import threading
from tkinter import messagebox

import cv2
import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw

from utils.config_mgr import ConfigManager
from utils.paths import get_resource_dir
from core.detector import BlinkDetector
from core.controller import ActionController
from core.worker import GestureWorker

ICON_PATH = os.path.join(get_resource_dir(), "assets", "icon.png")

logger = logging.getLogger(__name__)

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

KEY_OPTIONS = ["(нет)", "up", "down", "left", "right", "space", "enter",
               "l", "m", "k", "f", "n", "b"]

GESTURE_LABELS = {
    "double_blink": "Двойное моргание",
    "mouth_open": "Открытие рта",
    "smile": "Улыбка",
    "eyebrow_raise": "Поднятие бровей",
    "wink_left": "Подмигивание (левый глаз)",
    "wink_right": "Подмигивание (правый глаз)",
}

# (ключ_в_конфиге, подпись, мин, макс)
THRESHOLD_SLIDERS = [
    ("ear_threshold", "Моргание (EAR)", 0.10, 0.35),
    ("mar_threshold", "Открытие рта (MAR)", 0.20, 0.90),
    ("smile_threshold", "Улыбка", 0.20, 0.60),
    ("eyebrow_threshold", "Поднятие бровей", 0.10, 0.30),
]


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GestureApp")
        self.geometry("560x680")
        self.minsize(480, 560)
        self._set_window_icon()

        self.config_mgr = ConfigManager()
        self.worker = GestureWorker(self.config_mgr, BlinkDetector, ActionController)

        self.preview_enabled = ctk.BooleanVar(value=True)
        self._preview_photo = None
        self.tray_icon = None

        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._poll_worker()

    def _set_window_icon(self):
        ico_path = os.path.join(get_resource_dir(), "assets", "icon.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                logger.exception("Не удалось установить иконку окна")

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=12, pady=12)
        tabs.add("Home")
        tabs.add("Settings")

        self._build_home_tab(tabs.tab("Home"))
        self._build_settings_tab(tabs.tab("Settings"))

    def _build_home_tab(self, tab):
        self.status_label = ctk.CTkLabel(tab, text="Камера: остановлена", text_color="gray")
        self.status_label.pack(pady=(16, 6))

        self.toggle_btn = ctk.CTkButton(tab, text="Старт", command=self._toggle_worker, width=160)
        self.toggle_btn.pack(pady=6)

        preview_check = ctk.CTkCheckBox(
            tab, text="Показывать превью камеры", variable=self.preview_enabled,
            command=self._update_preview_visibility,
        )
        preview_check.pack(pady=(16, 6))

        self.preview_label = ctk.CTkLabel(tab, text="", width=320, height=240)
        self.preview_label.pack(pady=6)

        hint = ctk.CTkLabel(
            tab,
            text="Закрытие окна сворачивает приложение в трей.",
            text_color="gray", justify="center",
        )
        hint.pack(pady=(20, 4))

        exit_btn = ctk.CTkButton(
            tab, text="Выход", command=self._confirm_exit, width=160,
            fg_color="#8B2020", hover_color="#6E1919",
        )
        exit_btn.pack(pady=(4, 6))

    def _build_settings_tab(self, tab):
        scroll = ctk.CTkScrollableFrame(tab)
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="Камера", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(4, 2))
        cam_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        cam_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(cam_frame, text="Индекс камеры:").pack(side="left")
        self.camera_index_entry = ctk.CTkEntry(cam_frame, width=60)
        self.camera_index_entry.insert(0, str(self.config_mgr.config["camera_index"]))
        self.camera_index_entry.pack(side="left", padx=8)

        ctk.CTkLabel(scroll, text="Чувствительность", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(8, 2))
        for key, label, lo, hi in THRESHOLD_SLIDERS:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=3)
            value = self.config_mgr.config.get(key, (lo + hi) / 2)
            value_label = ctk.CTkLabel(row, text=f"{label}: {value:.2f}", width=220, anchor="w")
            value_label.pack(side="left")

            def _on_change(v, cfg_key=key, lbl=value_label, text=label):
                lbl.configure(text=f"{text}: {float(v):.2f}")
                self.config_mgr.config[cfg_key] = round(float(v), 3)

            slider = ctk.CTkSlider(row, from_=lo, to=hi, command=_on_change)
            slider.set(value)
            slider.pack(side="left", fill="x", expand=True, padx=8)

        ctk.CTkLabel(scroll, text="Жесты -> клавиши", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(12, 2))
        for gesture_key, label in GESTURE_LABELS.items():
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, width=220, anchor="w").pack(side="left")

            current = self.config_mgr.config["gestures"].get(gesture_key)
            menu = ctk.CTkOptionMenu(
                row, values=KEY_OPTIONS,
                command=lambda choice, g=gesture_key: self._on_gesture_bind(g, choice),
            )
            menu.set(current if current else "(нет)")
            menu.pack(side="left", padx=8)

        save_btn = ctk.CTkButton(scroll, text="Сохранить настройки", command=self._save_settings)
        save_btn.pack(pady=16)

        self.save_status_label = ctk.CTkLabel(scroll, text="", text_color="gray")
        self.save_status_label.pack()

    # ------------------------------------------------------------- handlers
    def _on_gesture_bind(self, gesture_key, choice):
        self.config_mgr.config["gestures"][gesture_key] = None if choice == "(нет)" else choice

    def _save_settings(self):
        try:
            self.config_mgr.config["camera_index"] = int(self.camera_index_entry.get())
        except ValueError:
            pass
        self.config_mgr.save_config()
        self.save_status_label.configure(text="Сохранено")
        self.after(1500, lambda: self.save_status_label.configure(text=""))

    def _toggle_worker(self):
        if self.worker.is_running:
            self.worker.stop()
            self.toggle_btn.configure(text="Старт")
        else:
            self.worker.start()
            self.toggle_btn.configure(text="Стоп")

    def _update_preview_visibility(self):
        if not self.preview_enabled.get():
            self.preview_label.configure(image=None, text="Превью выключено")

    # ------------------------------------------------------------ обновление GUI
    def _poll_worker(self):
        if self.worker.is_running:
            if self.worker.error:
                self.status_label.configure(text=f"Ошибка: {self.worker.error}", text_color="red")
                self.toggle_btn.configure(text="Старт")
            elif self.worker.camera_ok:
                self.status_label.configure(text="Камера: активна", text_color="green")

            if self.preview_enabled.get():
                frame = self.worker.get_preview_frame()
                if frame is not None:
                    self._render_preview(frame)
        elif not self.worker.error:
            self.status_label.configure(text="Камера: остановлена", text_color="gray")

        self.after(33, self._poll_worker)

    def _render_preview(self, frame_bgr):
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb).resize((320, 240))
        self._preview_photo = ctk.CTkImage(light_image=image, dark_image=image, size=(320, 240))
        self.preview_label.configure(image=self._preview_photo, text="")

    # ------------------------------------------------------------------ трей
    def _on_close(self):
        self._setup_tray()
        self.withdraw()

    def _setup_tray(self):
        if self.tray_icon is not None:
            return
        menu = pystray.Menu(
            pystray.MenuItem("Показать", self._tray_show, default=True),
            pystray.MenuItem("Старт/Стоп", self._tray_toggle),
            pystray.MenuItem("Выход", self._tray_exit),
        )
        self.tray_icon = pystray.Icon("GestureApp", self._make_tray_icon_image(), "GestureApp", menu)
        threading.Thread(target=self._run_tray_icon, daemon=True).start()

    def _run_tray_icon(self):
        try:
            self.tray_icon.run()
        except Exception:
            logger.exception("Иконка в трее упала с ошибкой")

    @staticmethod
    def _make_tray_icon_image():
        if os.path.exists(ICON_PATH):
            return Image.open(ICON_PATH)
        # Фолбэк
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((6, 6, 58, 58), fill=(0, 150, 90, 255))
        return image

    def _tray_show(self, icon=None, item=None):
        self.after(0, self.deiconify)

    def _tray_toggle(self, icon=None, item=None):
        self.after(0, self._toggle_worker)

    def _tray_exit(self, icon=None, item=None):
        self.after(0, self._confirm_exit)

    def _confirm_exit(self):
        if not self.winfo_viewable():
            self.deiconify()
        self.lift()
        self.focus_force()

        confirmed = messagebox.askyesno(
            "Выход",
            "Вы уверены, что хотите выйти из GestureApp?\nРаспознавание жестов будет остановлено.",
            parent=self,
        )
        if confirmed:
            self._full_exit()

    def _full_exit(self):
        logger.info("Выход из приложения по запросу пользователя")
        self.worker.stop()
        if self.tray_icon is not None:
            self.tray_icon.stop()
            self.tray_icon = None
        self.destroy()
