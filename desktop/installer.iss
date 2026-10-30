; Inno Setup script for Liger Player. Built by .github/workflows/windows.yml:  iscc desktop\installer.iss
#define AppName "Liger Player"
#ifndef AppVersion
  #define AppVersion "0.3.0"
#endif

[Setup]
AppId={{6F1C2A8E-4B7D-4E59-9A1F-2C7B3D9E5A10}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Liger Player contributors
AppPublisherURL=https://github.com/yashkesari-18/liger-player
DefaultDirName={autopf}\Liger Player
DefaultGroupName=Liger Player
UninstallDisplayIcon={app}\LigerPlayer.exe
OutputDir=..\dist
OutputBaseFilename=LigerPlayer-{#AppVersion}-Setup
SetupIconFile=liger\assets\icon.ico
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern
LicenseFile=..\LICENSE-DESKTOP.txt
ChangesAssociations=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "assoc"; Description: "Add Liger Player to ""Open with"" for video and audio files"; GroupDescription: "File types:"

[Files]
Source: "dist\LigerPlayer\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "..\LICENSE-DESKTOP.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "THIRD-PARTY-NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Liger Player"; Filename: "{app}\LigerPlayer.exe"
Name: "{group}\Uninstall Liger Player"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Liger Player"; Filename: "{app}\LigerPlayer.exe"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\LigerPlayer.Media"; ValueType: string; ValueName: ""; ValueData: "Liger Player media"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\LigerPlayer.Media\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\LigerPlayer.exe,0"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\LigerPlayer.Media\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\LigerPlayer.exe"" ""%1"""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\LigerPlayer.exe\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\LigerPlayer.exe"" ""%1"""; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\.mp4\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.mkv\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.webm\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.avi\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.mov\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.wmv\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.flv\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.m4v\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.ts\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.mp3\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.flac\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.wav\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.ogg\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.opus\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.m4a\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.aac\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.m3u\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.m3u8\OpenWithProgids"; ValueType: string; ValueName: "LigerPlayer.Media"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc

[Run]
Filename: "{app}\LigerPlayer.exe"; Description: "Start Liger Player"; Flags: nowait postinstall skipifsilent
