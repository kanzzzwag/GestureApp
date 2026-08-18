; Inno Setup скрипт для GestureApp.
; Сборка: сначала собрать dist\GestureApp.exe (см. build.md в корне проекта),
; затем открыть этот файл в Inno Setup Compiler (или ISCC.exe setup.iss).

#define MyAppName "GestureApp"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "GestureApp"
#define MyAppExeName "GestureApp.exe"

[Setup]
; Уникальный GUID приложения - НЕ менять между версиями (нужен для апдейтов/деинсталляции).
AppId={{B7B6B9F0-6A2E-4E9C-9E7B-6B2E7C6C9A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Установка в Program Files требует прав администратора.
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=output
OutputBaseFilename=GestureApp-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\assets\icon.ico

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "startupicon"; Description: "Запускать GestureApp при старте Windows"; GroupDescription: "Автозапуск:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Удалить {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; Общесистемная папка "Автозагрузка" (не {userstartup}) - согласована с
; PrivilegesRequired=admin выше, автозапуск сработает для всех пользователей ПК.
Name: "{commonstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить {#MyAppName}"; Flags: nowait postinstall skipifsilent

; Пользовательские данные (config.json, app.log) хранятся в %APPDATA%\GestureApp
; (см. utils/paths.py) и намеренно НЕ удаляются деинсталлятором, чтобы не терять
; настройки пользователя при переустановке/обновлении.
