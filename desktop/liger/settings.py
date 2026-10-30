"""Settings: defaults, storage in the user's app-data folder, and the catalog that builds the settings window."""
import copy
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Signal


def data_dir():
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    d = base / "LigerPlayer"
    d.mkdir(parents=True, exist_ok=True)
    return d


HOTKEYS = {"play": "Space", "back": "Left", "fwd": "Right", "volup": "Up", "voldown": "Down", "next": "N", "prev": "P", "fullscreen": "F",
           "mute": "M", "slower": "[", "faster": "]", "ab": "B", "loop": "L", "shuffle": "Z", "subs": "V", "subminus": "G", "subplus": "H",
           "shot": "S", "stats": "I", "settings": "C", "tv": "T", "frameNext": ".", "framePrev": ",", "open": "Ctrl+O"}

DEFAULTS = dict(
    mode="simple", theme="system", lang="en", accent="#2f6bff", glow=45, osd=True, remaining=False, autohide=3,
    rgbFx="wave", rgbMotion="loop", rgbDir="e", rgbSpeed=6, rgbBright=100, rgbSat=100, rgbPal="rainbow",
    rgbCustom=["#2f6bff", "#b23bff", "#ff2e88"], rgbZones=["ring", "seek", "play", "corners", "logo"], rgbCalm=True,
    speed="1", resume=True, autonext=True, stepShort=5, stepLong=30, speedStep="0.25", pitch=True, pauseAway=False, queueEnd="stop",
    brightness=100, contrast=100, saturation=100, hue=0, gamma=0, sharpen="0", aspect="auto", zoom=100, rotate="0", flip=False,
    hwdec="auto-safe", scale="ewa_lanczossharp", interp=False, deband=False, deint=False, tonemap="auto", peak="auto", dither="auto", icc=True,
    boost="100", eq=[0] * 10, eqPreset="flat", night=False, channels="stereo", adelay=0, exclusive=False, passthrough=False, normalize=False,
    subSize=100, subColor="#ffffff", subBg=40, subOutline=True, subFont="Manrope", subPos=0, subDelay=0, subAuto=True,
    tvAuto="daily", tvApi="https://iptv-org.github.io/api", tvCustom=[], tvHideDead=False, tvSkipDead=True, tvFav=[], tvCountry="all",
    tiguOn=True, tiguSize="3", tiguRoam="2", tiguNap=True, tiguReact=True, tiguFs=False, tiguGrassVideo=False,
    wheel="volume", dbl="fullscreen", hotkeys=dict(HOTKEYS),
    stats=False, cache="256", lowlat=False, keepAwake=True,
    shotFmt="png", shotQ=90, shotSubs=True, shotDir="",
    volume=80,
)


class Store(QObject):
    changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.path = data_dir() / "settings.json"
        self.v = copy.deepcopy(DEFAULTS)
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            for k, val in saved.items():
                if k in DEFAULTS:
                    self.v[k] = val
            self.v["hotkeys"] = {**HOTKEYS, **(saved.get("hotkeys") or {})}
        except Exception:
            pass

    def __getitem__(self, k):
        return self.v[k]

    def set(self, k, val, emit=True):
        self.v[k] = val
        self.save()
        if emit:
            self.changed.emit(k)

    def save(self):
        try:
            self.path.write_text(json.dumps(self.v, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:
            pass

    def reset(self):
        keep = {k: self.v[k] for k in ("lang", "tvFav", "tvCustom", "volume")}
        self.v = copy.deepcopy(DEFAULTS)
        self.v.update(keep)
        self.save()
        self.changed.emit("*")


SPEEDS = [(x, f"{float(x):.2f}×") for x in ("0.25", "0.5", "0.75", "1", "1.25", "1.5", "1.75", "2", "3", "4")]
EQ_BANDS = [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
EQ_PRESETS = {"flat": [0] * 10, "bass": [6, 5, 4, 2, 0, 0, 0, 0, 0, 0], "vocal": [-2, -2, -1, 1, 3, 4, 3, 1, 0, -1],
              "footsteps": [-4, -3, -2, 0, 1, 3, 5, 5, 2, 0], "treble": [0, 0, 0, 0, 0, 1, 3, 5, 6, 6]}
ZONES = [("ring", "Player border"), ("seek", "Seek bar"), ("play", "Play button"), ("corners", "Screen corners"), ("logo", "Logo")]

CATS = [("interface", "c_interface"), ("light", "c_light"), ("playback", "c_playback"), ("video", "c_video"), ("audio", "c_audio"),
        ("subtitles", "c_subtitles"), ("tv", "livetv"), ("tigu", "Tigu"), ("input", "c_input"), ("perf", "c_perf"), ("shots", "c_shots")]

# t: tog, seg, sel, range, color, text, act, lang, accent, pal, dir, zones, eq, urls, hk, folder.  s=True shows in Simple mode.
C = [
    dict(k="theme", c="interface", t="seg", l="@theme", o=[("light", "@light"), ("dark", "@dark"), ("system", "@system")], s=True),
    dict(k="lang", c="interface", t="lang", l="@language", s=True),
    dict(k="accent", c="interface", t="accent", l="@accent", h="Used by buttons, sliders and the Solid and Spectrum lighting effects."),
    dict(k="glow", c="interface", t="range", l="Glow intensity", min=0, max=100, step=5, u="%"),
    dict(k="autohide", c="interface", t="range", l="Hide controls in fullscreen after", min=1, max=10, step=1, u=" s"),
    dict(k="remaining", c="interface", t="tog", l="Show remaining time instead of length"),
    dict(k="osd", c="interface", t="tog", l="On-screen messages"),

    dict(k="rgbFx", c="light", t="seg", l="Effect", s=True, o=[("wave", "Wave"), ("rotate", "Rotate"), ("ripple", "Ripple"), ("breath", "Breathing"), ("spectrum", "Spectrum"), ("solid", "Solid")]),
    dict(k="rgbMotion", c="light", t="seg", l="Motion", s=True, o=[("static", "Static"), ("loop", "Loop"), ("once", "Play once")], h="Static freezes the colours in place. Play once runs one cycle when the player opens."),
    dict(k="rgbDir", c="light", t="dir", l="Direction", h="Wave: the way colours travel. Rotate: right-side arrows turn clockwise. Ripple: right-side arrows spread outward."),
    dict(k="rgbSpeed", c="light", t="range", l="Cycle length", min=2, max=30, step=1, u=" s", h="Lower is faster."),
    dict(k="rgbBright", c="light", t="range", l="@brightness", min=40, max=130, step=5, u="%"),
    dict(k="rgbSat", c="light", t="range", l="@saturation", min=0, max=100, step=5, u="%"),
    dict(k="rgbPal", c="light", t="pal", l="Palette"),
    dict(k="rgbZones", c="light", t="zones", l="Where it glows"),
    dict(k="rgbCalm", c="light", t="tog", l="Calm during playback", h="Pauses and dims the lighting while something plays."),

    dict(k="speed", c="playback", t="sel", l="@speed", o=SPEEDS, s=True),
    dict(k="resume", c="playback", t="tog", l="@resume", s=True),
    dict(k="autonext", c="playback", t="tog", l="@autonext", s=True),
    dict(k="stepShort", c="playback", t="range", l="Seek step (arrow keys)", min=1, max=30, step=1, u=" s"),
    dict(k="stepLong", c="playback", t="range", l="Long seek (Shift or Ctrl + arrow)", min=10, max=300, step=10, u=" s"),
    dict(k="speedStep", c="playback", t="seg", l="Speed step", o=[("0.05", "0.05"), ("0.1", "0.10"), ("0.25", "0.25")]),
    dict(k="pitch", c="playback", t="tog", l="Keep voice pitch at other speeds"),
    dict(k="pauseAway", c="playback", t="tog", l="Pause when I switch to another window", h="Useful when you alt-tab back into a game."),
    dict(k="queueEnd", c="playback", t="seg", l="When the queue ends", o=[("stop", "Stop"), ("repeat", "Repeat all")]),

    dict(k="brightness", c="video", t="range", l="@brightness", min=0, max=200, step=1, u="%", s=True),
    dict(k="contrast", c="video", t="range", l="@contrast", min=0, max=200, step=1, u="%"),
    dict(k="saturation", c="video", t="range", l="@saturation", min=0, max=200, step=1, u="%"),
    dict(k="hue", c="video", t="range", l="Hue", min=-180, max=180, step=1, u="°"),
    dict(k="gamma", c="video", t="range", l="Gamma", min=-100, max=100, step=1, u=""),
    dict(k="sharpen", c="video", t="seg", l="Sharpen", o=[("0", "Off"), ("1", "Low"), ("2", "Mid"), ("3", "High")]),
    dict(k="aspect", c="video", t="sel", l="Aspect ratio", o=[("auto", "Auto"), ("16:9", "16:9"), ("4:3", "4:3"), ("21:9", "21:9"), ("fill", "Stretch"), ("crop", "Crop to fill")]),
    dict(k="zoom", c="video", t="range", l="Zoom", min=100, max=300, step=5, u="%"),
    dict(k="rotate", c="video", t="seg", l="Rotate", o=[("0", "0°"), ("90", "90°"), ("180", "180°"), ("270", "270°")]),
    dict(k="flip", c="video", t="tog", l="Mirror horizontally"),
    dict(k="hwdec", c="video", t="sel", l="Hardware decoding", o=[("auto-safe", "Auto (safe)"), ("d3d11va", "D3D11VA"), ("nvdec", "NVDEC (NVIDIA)"), ("dxva2-copy", "DXVA2 (older GPUs)"), ("no", "Off (CPU)")], h="Takes effect from the next file."),
    dict(k="scale", c="video", t="sel", l="Upscaler", o=[("bilinear", "Bilinear (fastest)"), ("spline36", "Spline36"), ("ewa_lanczos", "EWA Lanczos"), ("ewa_lanczossharp", "EWA Lanczos Sharp (best)")]),
    dict(k="interp", c="video", t="tog", l="Motion smoothing for high-refresh displays", h="Resamples video to your 120/144/240 Hz display to remove judder."),
    dict(k="deband", c="video", t="tog", l="Deband", h="Removes colour banding in dark scenes and gradients."),
    dict(k="deint", c="video", t="tog", l="Deinterlace"),
    dict(k="tonemap", c="video", t="sel", l="HDR tone mapping", o=[("auto", "Auto"), ("bt.2390", "BT.2390"), ("spline", "Spline"), ("hable", "Hable"), ("st2094-40", "ST 2094-40")]),
    dict(k="peak", c="video", t="seg", l="Display peak brightness", o=[("auto", "Auto"), ("400", "400 nits"), ("600", "600"), ("1000", "1000")]),
    dict(k="dither", c="video", t="seg", l="Dither depth", o=[("auto", "Auto"), ("8", "8-bit"), ("10", "10-bit")]),
    dict(k="icc", c="video", t="tog", l="Use display colour profile (ICC)"),

    dict(k="boost", c="audio", t="seg", l="@boost", o=[("100", "100%"), ("150", "150%"), ("200", "200%")], s=True, h="Lets the volume slider go past 100% for quiet files."),
    dict(k="eq", c="audio", t="eq", l="@eq"),
    dict(k="night", c="audio", t="tog", l="Night mode (compress loud peaks)"),
    dict(k="channels", c="audio", t="seg", l="Channels", o=[("stereo", "Stereo"), ("mono", "Mono"), ("swap", "Swap L/R")]),
    dict(k="adelay", c="audio", t="range", l="Audio delay (lip sync)", min=-1000, max=1000, step=10, u=" ms"),
    dict(k="normalize", c="audio", t="tog", l="Loudness normalisation (EBU R128)"),
    dict(k="exclusive", c="audio", t="tog", l="Exclusive mode (WASAPI)"),
    dict(k="passthrough", c="audio", t="tog", l="Bitstream passthrough (AC3/DTS/TrueHD)", h="Sends surround audio untouched to an AV receiver."),

    dict(k="subSize", c="subtitles", t="range", l="@subsize", min=50, max=200, step=5, u="%", s=True),
    dict(k="subColor", c="subtitles", t="color", l="Text colour"),
    dict(k="subBg", c="subtitles", t="range", l="Background opacity", min=0, max=100, step=5, u="%"),
    dict(k="subOutline", c="subtitles", t="tog", l="Outline"),
    dict(k="subFont", c="subtitles", t="seg", l="Font", o=[("Manrope", "Sans"), ("Chakra Petch", "Gaming"), ("JetBrains Mono", "Mono")]),
    dict(k="subPos", c="subtitles", t="range", l="Raise subtitles", min=0, max=8, step=1, u=" lines"),
    dict(k="subDelay", c="subtitles", t="range", l="Subtitle delay", min=-5000, max=5000, step=50, u=" ms", h="Shortcut: G and H."),
    dict(k="subAuto", c="subtitles", t="tog", l="Load subtitles with the same name automatically"),

    dict(k="tvUpd", c="tv", t="act", l="Channel list", btn="@tvupdate", act="tvUpdate", h="Downloads the latest public channel list from iptv-org. Adult and blocklisted channels are always removed."),
    dict(k="tvAuto", c="tv", t="seg", l="Update automatically", o=[("launch", "On launch"), ("daily", "Daily"), ("weekly", "Weekly"), ("off", "Off")]),
    dict(k="tvApi", c="tv", t="text", l="Channel database address", h="Leave as is unless you host your own copy of the iptv-org API."),
    dict(k="tvCustom", c="tv", t="urls", l="Your playlists (M3U)", h="Add playlist links from broadcasters or other free sources. They load with every update."),
    dict(k="tvHideDead", c="tv", t="tog", l="Hide channels that failed to play"),
    dict(k="tvSkipDead", c="tv", t="tog", l="Skip to the next channel when one is offline"),
    dict(k="tvRetry", c="tv", t="act", l="Offline channels", btn="Retry all offline channels", act="tvRetry"),

    dict(k="tiguOn", c="tigu", t="tog", l="Show Tigu the tiger", s=True, h="Tigu idles in the grass, hides when you play something, and roams when you leave the player alone."),
    dict(k="tiguSize", c="tigu", t="seg", l="Size", o=[("2", "Small"), ("3", "Medium"), ("4", "Large")]),
    dict(k="tiguRoam", c="tigu", t="seg", l="Roam after inactivity", o=[("1", "1 min"), ("2", "2 min"), ("3", "3 min"), ("5", "5 min"), ("never", "Never")]),
    dict(k="tiguNap", c="tigu", t="tog", l="Nap after 10 minutes idle"),
    dict(k="tiguReact", c="tigu", t="tog", l="React to what you do", h="Purrs when clicked, covers ears at loud volume, poses for screenshots, pounces on dropped files."),
    dict(k="tiguFs", c="tigu", t="tog", l="Show in fullscreen"),
    dict(k="tiguGrassVideo", c="tigu", t="tog", l="Keep grass visible over playing video"),
    dict(k="tiguTest", c="tigu", t="act", l="Preview roaming", btn="Let Tigu roam now", act="tiguRoam"),

    dict(k="wheel", c="input", t="seg", l="Mouse wheel over video", o=[("volume", "Volume"), ("seek", "Seek"), ("off", "Off")]),
    dict(k="dbl", c="input", t="seg", l="Double-click", o=[("fullscreen", "Fullscreen"), ("play", "Play / pause")]),
    dict(k="hotkeys", c="input", t="hk", l="Keyboard shortcuts"),

    dict(k="stats", c="perf", t="tog", l="@stats", h="Codec, resolution, frame rate, dropped frames, display refresh, hardware decoding, buffer. Shortcut: I."),
    dict(k="keepAwake", c="perf", t="tog", l="Keep screen awake while playing"),
    dict(k="cache", c="perf", t="seg", l="Read-ahead cache", o=[("64", "64 MB"), ("256", "256 MB"), ("1024", "1 GB")]),
    dict(k="lowlat", c="perf", t="tog", l="Low-latency mode for live streams", h="Takes effect from the next channel or file."),

    dict(k="shot", c="shots", t="act", l="@screenshot", btn="@screenshot", act="shot"),
    dict(k="shotFmt", c="shots", t="seg", l="Format", o=[("png", "PNG"), ("jpg", "JPG"), ("webp", "WebP")]),
    dict(k="shotQ", c="shots", t="range", l="Quality (JPG / WebP)", min=50, max=100, step=5, u="%"),
    dict(k="shotSubs", c="shots", t="tog", l="Include subtitles"),
    dict(k="shotDir", c="shots", t="folder", l="Save screenshots to", h="Leave empty to use Pictures\\Liger Player."),
]

HOTKEY_LABELS = {"play": "@play", "back": "Seek back", "fwd": "Seek forward", "volup": "Volume up", "voldown": "Volume down", "next": "@next",
                 "prev": "@prev", "fullscreen": "@fullscreen", "mute": "@mute", "slower": "Slower", "faster": "Faster", "ab": "A–B loop",
                 "loop": "Repeat", "shuffle": "Shuffle", "subs": "Subtitles on/off", "subminus": "Subtitles earlier", "subplus": "Subtitles later",
                 "shot": "@screenshot", "stats": "@stats", "settings": "@settings", "tv": "@livetv", "frameNext": "Next frame", "framePrev": "Previous frame",
                 "open": "@open"}
