# PyInstaller build file for LigerPlayer.exe. Run from the desktop/ folder:  pyinstaller --noconfirm liger.spec
import os
block_cipher = None
binaries = [("libmpv-2.dll", ".")] if os.path.exists("libmpv-2.dll") else []

a = Analysis(
    ["run_liger.py"],
    pathex=["."],
    binaries=binaries,
    datas=[("liger/assets", "liger/assets")],
    hiddenimports=["PySide6.QtSvg", "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets"],
    excludes=["tkinter", "numpy", "PIL", "PySide6.QtNetwork", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtDBus",
              "PySide6.QtConcurrent", "PySide6.QtXml", "PySide6.QtPrintSupport", "PySide6.QtDesigner", "PySide6.QtHelp"],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="LigerPlayer",
    icon="liger/assets/icon.ico",
    console=False,
    version="version_info.txt" if os.path.exists("version_info.txt") else None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="LigerPlayer")
