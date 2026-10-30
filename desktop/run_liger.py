"""Entry point used by PyInstaller to build LigerPlayer.exe."""
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    # libmpv-2.dll ships next to the program; python-mpv looks for it on PATH when it is imported.
    here = [Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)), Path(sys.executable).resolve().parent]
    os.environ["PATH"] = os.pathsep.join(str(p) for p in here) + os.pathsep + os.environ.get("PATH", "")
    for p in here:
        try:
            os.add_dll_directory(str(p))
        except Exception:
            pass

if "--selftest" in sys.argv:
    # Used by the build workflow: proves the bundled libmpv loads, then exits without opening a window.
    out = Path(sys.argv[sys.argv.index("--selftest") + 1])
    try:
        import mpv
        m = mpv.MPV(vo="null", ao="null", config=False)
        out.write_text("ok " + str(m.mpv_version) + "\n", encoding="utf-8")
        m.terminate()
    except Exception as e:  # noqa: BLE001
        out.write_text("fail " + repr(e) + "\n", encoding="utf-8")
    sys.exit(0)

from liger.app import main  # noqa: E402

if __name__ == "__main__":
    main()
