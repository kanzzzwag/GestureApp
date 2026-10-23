# GestureApp

Control your computer with your face. GestureApp uses a regular webcam to detect facial gestures in real time (blinks, winks, smile, open mouth, raised eyebrows) and turns them into keyboard actions.

No special hardware, no cloud: everything runs locally on your computer.

## Features

- **6 gestures:** double blink, left wink, right wink, mouth open, smile, eyebrow raise
- **Custom key binding:** assign any key to any gesture in the settings window
- **Live camera preview** to check how detection works
- **Adjustable sensitivity:** thresholds and cooldowns for every gesture, saved to `config.json`
- **System tray mode:** the app keeps working in the background
- **Windows installer:** packaged as `.exe` with PyInstaller and Inno Setup

Default bindings (work well for scrolling short videos hands-free):

| Gesture | Key |
|---|---|
| Double blink | Down arrow |
| Mouth open | Up arrow |
| Smile | `L` |
| Eyebrow raise, left / right wink | not set |

## How it works

1. A background worker thread reads frames from the webcam with OpenCV.
2. MediaPipe Face Landmarker finds face landmarks on every frame.
3. The detector calculates simple geometric metrics:
   - **EAR** (Eye Aspect Ratio): how open each eye is. Both eyes closed twice in a short time = double blink, one eye closed = wink.
   - **MAR** (Mouth Aspect Ratio): how open the mouth is.
   - Smile width and eyebrow height, normalized by face size, so distance to the camera does not matter.
4. The controller compares metrics with thresholds, applies cooldowns to avoid false triggers and presses the bound key with PyAutoGUI.

The camera loop runs in its own thread and shares frames with the GUI through a lock, so the interface never freezes.

## Project structure

```
GestureApp/
├── main.py               # entry point, logging setup
├── core/
│   ├── detector.py       # MediaPipe landmarks, EAR / MAR / smile / eyebrow metrics
│   ├── controller.py     # gesture logic, cooldowns, key presses
│   └── worker.py         # camera + recognition loop in a separate thread
├── gui/
│   └── app_window.py     # CustomTkinter window, settings, preview, tray icon
├── utils/
│   ├── config_mgr.py     # load / save config.json with safe defaults
│   ├── logger.py         # file + console logging
│   └── paths.py          # paths for dev mode and the built .exe
├── models/               # face_landmarker.task (MediaPipe model)
├── assets/               # app icons
├── installer/setup.iss   # Inno Setup script for the Windows installer
└── GestureApp.spec       # PyInstaller build config
```

## Tech stack

Python, OpenCV, MediaPipe Tasks API, CustomTkinter, PyAutoGUI, pystray, Pillow, PyInstaller, Inno Setup.

## Run from source

Requires Python 3.10 to 3.12 and a webcam.

```bash
git clone https://github.com/kanzzzwag/GestureApp.git
cd GestureApp
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux / macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Press **Старт** (Start) in the app window and try a double blink. The interface is in Russian.

## Build the Windows installer

```bash
pip install pyinstaller
pyinstaller GestureApp.spec
```

This creates `dist/GestureApp.exe`. Then open `installer/setup.iss` in Inno Setup Compiler and build the installer.

In the built version, `config.json` and `app.log` are stored in `%APPDATA%\GestureApp`.

## Configuration

All settings can be changed in the app. They are saved to `config.json`:

| Key | Default | Meaning |
|---|---|---|
| `camera_index` | 0 | which webcam to use |
| `ear_threshold` | 0.23 | eye is "closed" below this value |
| `double_blink_delay` | 0.4 s | max time between two blinks |
| `mar_threshold` | 0.5 | mouth is "open" above this value |
| `smile_threshold` | 0.36 | smile detection level |
| `eyebrow_threshold` | 0.20 | eyebrow raise detection level |
| `gestures` | see above | gesture to key mapping |

## Author

Batyrkhan Kanapiya, Software Engineering student at Astana IT University. [GitHub](https://github.com/kanzzzwag)
