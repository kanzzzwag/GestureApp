# Сборка GestureApp в .exe и инсталлятор

## 1. Сборка .exe (PyInstaller)

Уже настроено, повторить сборку можно одной командой (использует `GestureApp.spec`
в корне проекта - там уже прописаны иконка, модель MediaPipe и `--collect-all mediapipe`):

```
.venv\Scripts\pyinstaller.exe GestureApp.spec --noconfirm
```

Результат: `dist\GestureApp.exe` (собран в режиме `--windowed`/`--onefile`, без консоли).

Если нужно собрать с нуля (например, добавили новую зависимость) - команда, из которой
сгенерирован `GestureApp.spec`:

```
.venv\Scripts\pyinstaller.exe ^
  --name GestureApp ^
  --windowed ^
  --onefile ^
  --icon assets\icon.ico ^
  --add-data "models\face_landmarker.task;models" ^
  --add-data "assets\icon.png;assets" ^
  --add-data "assets\icon.ico;assets" ^
  --collect-all mediapipe ^
  main.py
```

`--collect-all mediapipe` обязателен: у mediapipe нет готового PyInstaller-хука
(в отличие от cv2/customtkinter/pystray), поэтому бинарники и данные пакета
нужно собирать явно, иначе .exe упадёт при импорте.

### Важно про пути

- Модель `models/face_landmarker.task` и иконки бандлуются внутрь .exe и
  распаковываются во временную папку (`sys._MEIPASS`) при каждом запуске -
  см. `utils/paths.py::get_resource_dir()`.
- `config.json` и `app.log` **не** пишутся рядом с .exe - они идут в
  `%APPDATA%\GestureApp\`, потому что после установки в Program Files обычный
  пользователь не имеет прав на запись в папку программы - см.
  `utils/paths.py::get_data_dir()`. Проверено вручную: после запуска собранного
  .exe файлы появляются в `%APPDATA%\GestureApp\config.json` и `...\app.log`.

## 2. Сборка инсталлятора (Inno Setup)

1. Установить [Inno Setup](https://jrsoftware.org/isinfo.php) (не входит в проект).
2. Собрать `dist\GestureApp.exe` (шаг 1).
3. Открыть `installer\setup.iss` в Inno Setup Compiler и нажать Compile,
   либо из командной строки:
   ```
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
   ```
4. Готовый инсталлятор появится в `installer\output\GestureApp-Setup-<версия>.exe`.

Инсталлятор:
- ставит приложение в `Program Files` (требует прав администратора);
- создаёт ярлык на рабочем столе (задача включена по умолчанию, можно снять);
- предлагает опционально добавить в автозапуск Windows (по умолчанию выключено -
  через ярлык в папке "Автозагрузка" текущего пользователя);
- деинсталлятор не трогает `%APPDATA%\GestureApp` - настройки пользователя
  переживают удаление/переустановку.

## 3. Публикация на GitHub Releases

Прикладывать в релиз `installer\output\GestureApp-Setup-<версия>.exe`
(инсталлятор уже содержит .exe приложения - отдельно `dist\GestureApp.exe`
прикладывать не обязательно).
