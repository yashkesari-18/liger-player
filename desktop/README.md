# Liger Player for Windows

A native Windows app with no web view. The interface is built with Qt (PySide6), and playback is handled by **libmpv**, the engine behind mpv. Like VLC, it plays almost any file: MKV, HEVC/H.265, AV1, AC3/DTS/TrueHD, HDR, subtitles, and network streams.

## Download

There are two ways to get the Windows build:

- **From Releases.** Open the repository's **Releases** page and download either:
  - `LigerPlayer-x.y.z-Setup.exe`, an installer with Start menu and desktop shortcuts and optional *Open with* entries for media files, or
  - `LigerPlayer-x.y.z-portable.zip`, which you unzip anywhere and run `LigerPlayer.exe`. Nothing is installed.
- **From a build.** Open **Actions → Build Windows app → the latest run**, and download the `LigerPlayer-windows` artifact.

Requirements: Windows 10 or 11, 64-bit, and a GPU with OpenGL 3.3 (any graphics card from the last ten years).

## What works in the desktop build

Everything from the web version is here. The settings that were marked *Desktop build* in the web version now work too:

- Hardware decoding: D3D11VA, NVDEC or DXVA2.
- High-quality upscaling: EWA Lanczos Sharp.
- Motion smoothing for 120/144/240 Hz displays.
- Deband, deinterlacing, and HDR tone mapping (BT.2390, Hable, Spline and others).
- Negative audio delay, exclusive WASAPI output, bitstream passthrough to an AV receiver, and EBU R128 loudness normalisation.
- Subtitles with the same name as the video load automatically.
- Live TV plays every channel, including HTTP ones, because there are no browser restrictions.

Settings are stored in `%APPDATA%\LigerPlayer\settings.json`. Screenshots go to `Pictures\Liger Player` unless you choose another folder.

## Build it yourself

The repository builds itself on GitHub:

1. Push to `main`, or open **Actions → Build Windows app → Run workflow**. GitHub's Windows machine then:
   - installs Python and the dependencies,
   - downloads the latest libmpv from [shinchiro/mpv-winbuild-cmake](https://github.com/shinchiro/mpv-winbuild-cmake),
   - builds the app with PyInstaller,
   - checks that the engine loads,
   - and packages the installer (Inno Setup) and the portable zip.
2. To publish a release, create and push a tag:

   ```
   git tag v0.3.0
   git push origin v0.3.0
   ```

To build by hand on a Windows PC with Python 3.12:

```powershell
cd desktop
pip install -r requirements.txt pyinstaller
# put libmpv-2.dll (from an mpv-dev-x86_64 package) in this folder
pyinstaller --noconfirm liger.spec
dist\LigerPlayer\LigerPlayer.exe
```

To run from source without building: `python run_liger.py`. This needs `libmpv-2.dll` on your PATH or next to `run_liger.py`.

## Layout

| File | What it does |
|---|---|
| `liger/app.py` | Main window, playback control, settings → mpv options, hotkeys |
| `liger/video.py` | The OpenGL stage where libmpv renders, plus overlays (OSD, stats, corners), seek bar, play button |
| `liger/tigu.py` | Tigu the tiger: procedural 16-bit sprite and behaviour (idle, hide, peek, roam, nap) |
| `liger/rgb.py` | RGB lighting effects |
| `liger/flags.py` | Flags drawn as SVG, with the hover ripple |
| `liger/livetv.py`, `liger/tvui.py` | Live TV data (iptv-org and M3U) and the panel |
| `liger/settings.py`, `liger/settings_ui.py` | Settings catalog and the settings window |
| `liger/assets/locales.json` | Translations, generated from `../js/i18n.js` |

## Licence

The Windows build bundles libmpv, which is GPL licensed, so the desktop app is released under **GPL-3.0-or-later** (see `../LICENSE-DESKTOP.txt` and `THIRD-PARTY-NOTICES.txt`). The web version stays MIT.
