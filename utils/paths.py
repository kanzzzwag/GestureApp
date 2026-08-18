"""Определение путей приложения.

Во время разработки всё (config.json, app.log, модель MediaPipe) лежит
в корне проекта. В собранном .exe (PyInstaller) же:
  - бандлованные ресурсы (модель MediaPipe) распаковываются во временную
    папку sys._MEIPASS;
  - пользовательские данные (config.json, app.log) НЕЛЬЗЯ писать рядом
    с .exe, если он установлен в Program Files - обычному пользователю
    туда нельзя писать без прав администратора. Поэтому они уходят
    в %APPDATA%\\GestureApp.
"""
import os
import sys


def is_frozen():
    """True, если код выполняется из собранного PyInstaller .exe."""
    return getattr(sys, "frozen", False)


def get_resource_dir():
    """Папка с бандлованными ресурсами (модель MediaPipe и т.п.), только для чтения."""
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_dir():
    """Папка для пользовательских данных (config.json, app.log), доступная на запись."""
    if is_frozen():
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "GestureApp")
    else:
        base = get_resource_dir()
    os.makedirs(base, exist_ok=True)
    return base
