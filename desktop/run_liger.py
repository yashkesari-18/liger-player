"""Entry point used by PyInstaller to build LigerPlayer.exe."""
import os
import sys
from pathlib import Path

_DLL_DIRS = []  # os.add_dll_directory handles must stay alive, or Windows drops the directory again

if sys.platform == "win32":
    # libmpv-2.dll ships next to the program; python-mpv looks for it on PATH when it is imported.
    here = [Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)), Path(sys.executable).resolve().parent]
    os.environ["PATH"] = os.pathsep.join(str(p) for p in here) + os.pathsep + os.environ.get("PATH", "")
    for p in here:
        try:
            _DLL_DIRS.append(os.add_dll_directory(str(p)))
        except Exception:
            pass


def selftest(out: Path):
    """Used by the build workflow. Writes one line per step, so a crash shows exactly where it happened."""
    log = open(out, "w", encoding="utf-8", buffering=1)

    def step(msg):
        log.write(msg + "\n")
        log.flush()
        os.fsync(log.fileno())

    import faulthandler
    faulthandler.enable(file=log, all_threads=True)
    step(f"start python={sys.version.split()[0]} frozen={getattr(sys, 'frozen', False)}")
    step("search=" + " | ".join(str(p) for p in ([Path(getattr(sys, "_MEIPASS", ""))] if hasattr(sys, "_MEIPASS") else []) + [Path(__file__).resolve().parent]))
    try:
        import ctypes.util
        step(f"find_library libmpv-2.dll -> {ctypes.util.find_library('libmpv-2.dll')}")
        import locale
        locale.setlocale(locale.LC_NUMERIC, "C")
        import mpv
        step("imported python-mpv")
        m = mpv.MPV(vo="null", ao="null", config=False)
        step("created player")
        ver = m.mpv_version
        step("ok " + str(ver))
        m.terminate()
        step("terminated")
    except BaseException as e:  # noqa: BLE001
        import traceback
        step("fail " + repr(e))
        step(traceback.format_exc())
    log.close()


if "--selftest" in sys.argv:
    selftest(Path(sys.argv[sys.argv.index("--selftest") + 1]))
    sys.exit(0)

from liger.app import main  # noqa: E402

if __name__ == "__main__":
    main()
