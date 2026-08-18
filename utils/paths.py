"""Пути приложения: dev-режим vs собранный .exe (PyInstaller)."""
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
