"""Liger Player — main window."""
import ctypes
import locale
import math
import os
import random
import sys
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QComboBox, QListWidget, QListWidgetItem,
                               QMainWindow, QMenu, QPushButton, QSlider, QSplitter, QTabWidget, QToolButton, QVBoxLayout, QWidget, QAbstractSpinBox)

from . import theme
from .i18n import Tr
from .livetv import LiveTV
from .rgb import Lighting
from .settings import EQ_BANDS, Store, data_dir
from .settings_ui import SettingsDialog
from .tvui import TVPanel
from .video import LogoMark, PlayButton, SeekBar, StageFrame, VideoView, fmt

MEDIA_EXT = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".wmv", ".flv", ".m4v", ".ts", ".m2ts", ".mpg", ".mpeg", ".3gp", ".ogv",
             ".mp3", ".flac", ".wav", ".ogg", ".opus", ".m4a", ".aac", ".wma", ".alac", ".ape", ".mka"}
SUB_EXT = {".srt", ".ass", ".ssa", ".vtt", ".sub"}
LIST_EXT = {".m3u", ".m3u8"}
VERSION = "0.3.0"


class Bridge(QObject):
    end_file = Signal(int)


class App(QMainWindow):
    def __init__(self, files):
        super().__init__()
        self.s = Store()
        self.tr = Tr(self.s["lang"])
        self.tok = theme.tokens(self.s["theme"])
        self.lighting = Lighting(self.s)
        self.rgb_widgets = set()
        self.queue, self.cur, self.live = [], -1, None
        self.loop, self.shuffle = 0, False
        self.ended = False
        self.is_video = False
        self.pos = self.dur = 0.0
        self.paused = True
        self.dialog = None
        self.bridge = Bridge()
        self.bridge.end_file.connect(self._end_file)
        self._init_mpv()
        self.tv = LiveTV(self.s)
        self._build()
        self.setWindowTitle("Liger Player")
        self.setWindowIcon(theme.app_icon())
        self.resize(1280, 780)
        self.setAcceptDrops(True)
        self.s.changed.connect(self.apply)
        self.apply("*")
        self.tv.updated.connect(self._tv_updated)
        self.poll = QTimer(self); self.poll.setInterval(100); self.poll.timeout.connect(self._poll); self.poll.start()
        self.anim = QTimer(self); self.anim.setInterval(33); self.anim.timeout.connect(self._tick); self.anim.start()
        self.stat_t = QTimer(self); self.stat_t.setInterval(500); self.stat_t.timeout.connect(self._stats); self.stat_t.start()
        self.idle_t = QTimer(self); self.idle_t.setSingleShot(True); self.idle_t.timeout.connect(self._hide_deck)
        QApplication.instance().installEventFilter(self)
        QApplication.instance().applicationStateChanged.connect(self._app_state)
        if files:
            QTimer.singleShot(50, lambda: self.add_files(files, play=True))
        if self.tv.due():
            QTimer.singleShot(1500, self.tv.refresh)

    # ------------------------------------------------------------------ mpv
    def _init_mpv(self):
        import mpv
        shots = Path(self.s["shotDir"]) if self.s["shotDir"] else Path.home() / "Pictures" / "Liger Player"
        wl = data_dir() / "watch_later"
        wl.mkdir(exist_ok=True)
        self.m = mpv.MPV(vo="libmpv", ytdl=False, input_default_bindings=False, input_vo_keyboard=False, osc=False, idle="yes",
                         keep_open="no", config=False, terminal=False, watch_later_directory=str(wl), screenshot_template="Liger-%F-%P",
                         screenshot_directory=str(shots), audio_client_name="Liger Player", title="Liger Player")
        self.m.volume_max = 100
        self.m.volume = self.s["volume"]

        @self.m.event_callback("end-file")
        def _ef(ev):
            try:
                self.bridge.end_file.emit(int(ev.data.reason))
            except Exception:
                pass

    def prop(self, name, default=None):
        import mpv
        try:
            v = self.m._get_property(name, mpv.lazy_decoder)
            return default if v is None else v
        except Exception:
            return default

    def setp(self, name, value):
        try:
            self.m._set_property(name, value)
        except Exception:
            try:
                self.m[name] = value
            except Exception:
                pass

    # ------------------------------------------------------------------ ui
    def _build(self):
        root = QWidget(); root.setObjectName("root"); self.setCentralWidget(root)
        v = QVBoxLayout(root); v.setContentsMargins(16, 14, 16, 16); v.setSpacing(12)
        self.header = QWidget()
        hl = QHBoxLayout(self.header); hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(8)
        self.logo = LogoMark(self); self.rgb_widgets.add(self.logo)
        brand = QLabel("LIGER"); brand.setObjectName("brand")
        small = QLabel(f"PLAYER · v{VERSION}"); small.setObjectName("brandSmall")
        hl.addWidget(self.logo); hl.addWidget(brand); hl.addWidget(small); hl.addStretch(1)
        self.b_open = QPushButton(); self.b_open.setObjectName("primary"); self.b_open.clicked.connect(self.open_dialog)
        self.b_sub = QPushButton(); self.b_sub.clicked.connect(self.open_subs)
        self.b_set = QPushButton(); self.b_set.clicked.connect(lambda: self.open_settings())
        for b in (self.b_open, self.b_sub, self.b_set):
            hl.addWidget(b)
        v.addWidget(self.header)

        body = QHBoxLayout(); body.setSpacing(16)
        self.stage = StageFrame(self); self.rgb_widgets.add(self.stage)
        sv = QVBoxLayout(self.stage); sv.setContentsMargins(6, 6, 6, 6); sv.setSpacing(0)
        self.video = VideoView(self)
        self.video.clicked.connect(self._video_click)
        self.video.double_clicked.connect(lambda: self.fullscreen() if self.s["dbl"] == "fullscreen" else self.toggle())
        self.video.wheel.connect(self._wheel)
        self.video.files_dropped.connect(lambda f: self.add_files(f, play=True))
        sv.addWidget(self.video, 1)
        self.deck = QFrame(); self.deck.setObjectName("panel")
        dv = QVBoxLayout(self.deck); dv.setContentsMargins(16, 12, 16, 12); dv.setSpacing(8)
        sr = QHBoxLayout()
        self.l_pos = QLabel("0:00"); self.l_pos.setObjectName("mono")
        self.seek = SeekBar(self); self.seek.seek.connect(self.seek_to); self.rgb_widgets.add(self.seek)
        self.l_dur = QLabel("0:00"); self.l_dur.setObjectName("mono")
        sr.addWidget(self.l_pos); sr.addWidget(self.seek, 1); sr.addWidget(self.l_dur)
        dv.addLayout(sr)
        cr = QHBoxLayout(); cr.setSpacing(2)
        self.btn = {}

        def tb(name, slot, checkable=False):
            b = QToolButton(); b.setIconSize(QSize(20, 20)); b.setCheckable(checkable); b.clicked.connect(slot); b.setCursor(Qt.PointingHandCursor)
            self.btn[name] = b; cr.addWidget(b); return b
        tb("prev", lambda: self.prev())
        tb("back", lambda: self.skip(-self.s["stepShort"]))
        self.play_btn = PlayButton(self); self.play_btn.clicked.connect(self.toggle); self.rgb_widgets.add(self.play_btn); cr.addWidget(self.play_btn)
        tb("fwd", lambda: self.skip(self.s["stepShort"]))
        tb("next", lambda: self.next(1))
        tb("loop", self.cycle_loop, True)
        tb("shuffle", self.toggle_shuffle, True)
        self.b_ab = QPushButton("A–B"); self.b_ab.setObjectName("pill"); self.b_ab.setCheckable(True); self.b_ab.clicked.connect(self.ab_step); cr.addWidget(self.b_ab)
        cr.addStretch(1)
        self.b_speed = QPushButton("1.00×"); self.b_speed.setObjectName("pill"); self.b_speed.clicked.connect(self.cycle_speed); cr.addWidget(self.b_speed)
        tb("volume", self.toggle_mute)
        self.vol = QSlider(Qt.Horizontal); self.vol.setFixedWidth(100); self.vol.setRange(0, 100); self.vol.setValue(int(self.s["volume"]))
        self.vol.valueChanged.connect(self.set_volume); cr.addWidget(self.vol)
        self.l_vol = QLabel("80%"); self.l_vol.setObjectName("mono"); self.l_vol.setFixedWidth(40); cr.addWidget(self.l_vol)
        tb("cc", self.cycle_subs)
        tb("shot", self.screenshot)
        tb("full", self.fullscreen)
        dv.addLayout(cr)
        sv.addWidget(self.deck)
        body.addWidget(self.stage, 1)

        self.side = QFrame(); self.side.setObjectName("panel"); self.side.setFixedWidth(350)
        sl = QVBoxLayout(self.side); sl.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget(); self.tabs.setDocumentMode(True)
        qw = QWidget(); ql = QVBoxLayout(qw); ql.setContentsMargins(0, 0, 0, 0)
        self.qlist = QListWidget(); self.qlist.itemDoubleClicked.connect(lambda it: self.load(self.qlist.row(it), True))
        self.qlist.setContextMenuPolicy(Qt.CustomContextMenu); self.qlist.customContextMenuRequested.connect(self._queue_menu)
        ql.addWidget(self.qlist, 1)
        self.keys = QLabel(); self.keys.setObjectName("muted"); self.keys.setContentsMargins(16, 10, 16, 12); self.keys.setTextFormat(Qt.RichText)
        ql.addWidget(self.keys)
        self.tvp = TVPanel(self, self.tv); self.tvp.play.connect(self.play_live)
        self.tabs.addTab(qw, "Queue"); self.tabs.addTab(self.tvp, "Live TV")
        sl.addWidget(self.tabs)
        body.addWidget(self.side)
        v.addLayout(body, 1)

    def retranslate(self):
        t = self.tr
        QApplication.instance().setLayoutDirection(Qt.RightToLeft if t.rtl() else Qt.LeftToRight)
        self.b_open.setText(t("open")); self.b_sub.setText(t("subs")); self.b_set.setText(t("settings"))
        tips = dict(prev=t("prev"), back=f"−{self.s['stepShort']} s", fwd=f"+{self.s['stepShort']} s", next=t("next"), loop="Repeat", shuffle="Shuffle",
                    volume=t("mute"), cc=t("c_subtitles"), shot=t("screenshot"), full=t("fullscreen"))
        for k, b in self.btn.items():
            b.setToolTip(tips.get(k, k))
        self.play_btn.setToolTip(t("play"))
        self.tabs.setTabText(0, f"{t('queue')}  {len(self.queue)}")
        real = len([c for c in self.tv.channels if not c.get("sample")])
        self.tabs.setTabText(1, f"{t('livetv')}  {real or ''}".strip())
        hk = self.s["hotkeys"]
        rows = [("play", t("play") + " / " + t("pause")), ("back", f"{t('prev')} / {t('next')} {self.s['stepShort']} s"), ("volup", t("volume")),
                ("slower", t("speed")), ("next", f"{t('next')} / {t('prev')}"), ("shot", t("screenshot")), ("tv", t("livetv")), ("settings", t("settings"))]
        pair = {"back": "fwd", "volup": "voldown", "slower": "faster", "next": "prev"}
        html = "<table cellspacing=4>" + "".join(
            f"<tr><td><code>{hk.get(a) or '—'}{(' ' + (hk.get(pair[a]) or '')) if a in pair else ''}</code></td><td>{lab}</td></tr>" for a, lab in rows) + "</table>"
        self.keys.setText(html)
        self.render_queue()
        self.tvp.retranslate()
        if self.dialog:
            self.dialog.retranslate()

    def restyle(self):
        self.tok = theme.tokens(self.s["theme"])
        self.video.tok = self.tok
        QApplication.instance().setStyleSheet(theme.stylesheet(self.tok, self.accent()))
        ink = self.tok["ink"]
        for k, b in self.btn.items():
            name = {"volume": "mute" if self.prop("mute", False) else "volume"}.get(k, k)
            b.setIcon(theme.icon(name, self.accent() if b.isChecked() else ink))
        self.update()

    def accent(self):
        return self.s["accent"]

    # ------------------------------------------------------------------ settings → mpv
    def apply(self, k):
        s = self.s
        every = k == "*"
        if every or k == "lang":
            self.tr.lang = s["lang"]
            self.retranslate()
        if every or k in ("theme", "accent"):
            self.restyle()
        if every or k.startswith("rgb"):
            self.lighting.restart()
        if every or k == "speed":
            self.setp("speed", float(s["speed"]))
        if every or k == "pitch":
            self.setp("audio-pitch-correction", s["pitch"])
        if every or k == "resume":
            self.setp("save-position-on-quit", s["resume"]); self.setp("resume-playback", s["resume"])
        if every or k in ("brightness", "contrast", "saturation", "hue", "gamma"):
            self.setp("brightness", s["brightness"] - 100); self.setp("contrast", s["contrast"] - 100)
            self.setp("saturation", max(-100, min(100, s["saturation"] - 100))); self.setp("hue", round(s["hue"] / 1.8)); self.setp("gamma", s["gamma"])
        if every or k in ("flip", "sharpen"):
            vf = []
            if s["flip"]:
                vf.append("hflip")
            amt = {"1": 0.4, "2": 0.8, "3": 1.4}.get(s["sharpen"])
            if amt:
                vf.append(f"lavfi=[unsharp=5:5:{amt}]")
            try:
                self.m.command("vf", "set", ",".join(vf))
            except Exception:
                pass
        if every or k == "aspect":
            a = s["aspect"]
            self.setp("video-aspect-override", a if ":" in a else "no")
            self.setp("keepaspect", a != "fill")
            self.setp("panscan", 1.0 if a == "crop" else 0.0)
        if every or k == "zoom":
            self.setp("video-zoom", math.log2(s["zoom"] / 100))
        if every or k == "rotate":
            self.setp("video-rotate", int(s["rotate"]))
        if every or k == "hwdec":
            self.setp("hwdec", s["hwdec"])
        if every or k == "scale":
            self.setp("scale", s["scale"])
        if every or k == "interp":
            on = s["interp"]
            scr = self.screen() or QGuiApplication.primaryScreen()
            if on and scr:
                self.setp("override-display-fps", scr.refreshRate())
            self.setp("video-sync", "display-resample" if on else "audio")
            self.setp("interpolation", on)
            self.setp("tscale", "oversample")
        if every or k == "deband":
            self.setp("deband", s["deband"])
        if every or k == "deint":
            self.setp("deinterlace", s["deint"])
        if every or k == "tonemap":
            self.setp("tone-mapping", s["tonemap"])
        if every or k == "peak":
            self.setp("target-peak", s["peak"])
        if every or k == "dither":
            self.setp("dither-depth", s["dither"])
        if every or k == "boost":
            mx = int(s["boost"])
            self.setp("volume-max", mx)
            self.vol.blockSignals(True); self.vol.setMaximum(mx); self.vol.setValue(min(int(s["volume"]), mx)); self.vol.blockSignals(False)
            self.set_volume(min(int(s["volume"]), mx))
        if every or k in ("eq", "night", "channels", "normalize"):
            af = []
            if any(s["eq"]):
                af.append("lavfi=[" + ",".join(f"equalizer=f={f}:t=q:w=1.1:g={g}" for f, g in zip(EQ_BANDS, s["eq"])) + "]")
            if s["night"]:
                af.append("lavfi=[acompressor=threshold=-30dB:ratio=8:makeup=4]")
            if s["normalize"]:
                af.append("lavfi=[loudnorm=I=-16:TP=-1.5:LRA=11]")
            if s["channels"] == "mono":
                af.append("lavfi=[pan=mono|c0=0.5*c0+0.5*c1]")
            elif s["channels"] == "swap":
                af.append("lavfi=[pan=stereo|c0=c1|c1=c0]")
            try:
                self.m.command("af", "set", ",".join(af))
            except Exception:
                pass
        if every or k == "adelay":
            self.setp("audio-delay", s["adelay"] / 1000)
        if every or k == "exclusive":
            self.setp("audio-exclusive", s["exclusive"])
        if every or k == "passthrough":
            self.setp("audio-spdif", "ac3,eac3,dts,dts-hd,truehd" if s["passthrough"] else "")
        if every or k in ("subSize", "subColor", "subBg", "subOutline", "subFont", "subPos", "subDelay", "subAuto"):
            self.setp("sub-scale", s["subSize"] / 100)
            self.setp("sub-color", s["subColor"])
            self.setp("sub-back-color", "#%02X000000" % round(s["subBg"] * 2.55))
            self.setp("sub-border-size", 3 if s["subOutline"] else 0)
            self.setp("sub-font", s["subFont"])
            self.setp("sub-pos", 100 - s["subPos"] * 5)
            self.setp("sub-delay", s["subDelay"] / 1000)
            self.setp("sub-auto", "fuzzy" if s["subAuto"] else "no")
        if every or k == "cache":
            self.setp("demuxer-max-bytes", f"{s['cache']}MiB")
        if every or k in ("shotFmt", "shotQ", "shotDir"):
            self.setp("screenshot-format", s["shotFmt"]); self.setp("screenshot-jpeg-quality", s["shotQ"]); self.setp("screenshot-webp-quality", s["shotQ"])
            d = Path(s["shotDir"]) if s["shotDir"] else Path.home() / "Pictures" / "Liger Player"
            self.setp("screenshot-directory", str(d))
        if k in ("stepShort", "hotkeys"):
            self.retranslate()
        if k == "tvHideDead":
            self.tvp.refresh_list()
        if k == "tiguSize":
            self.video.tigu.x = -1

    def action(self, name):
        if name == "tvUpdate":
            self.tv.refresh(); self.tvp.update_status(); self.tabs.setCurrentIndex(1)
        elif name == "tvRetry":
            self.tv.clear_dead(); self.tvp.refresh_list(); self.osd("Offline list cleared")
        elif name == "m3uFile":
            f, _ = QFileDialog.getOpenFileName(self, "Import M3U playlist", "", "Playlists (*.m3u *.m3u8)")
            if f:
                n = self.tv.import_file(f)
                self.osd(f"{n} channels added" if n else "No channels found in that playlist")
                self.tabs.setCurrentIndex(1)
        elif name == "tiguRoam":
            if self.dialog:
                self.dialog.accept()
            self.video.tigu.roam_now()
        elif name == "shot":
            if self.dialog:
                self.dialog.accept()
            self.screenshot()

    def open_settings(self, cat=None):
        if not self.dialog:
            self.dialog = SettingsDialog(self)
        if cat:
            self.dialog.open_category(cat)
        else:
            self.dialog.retranslate()
        self.dialog.show(); self.dialog.raise_(); self.dialog.activateWindow()

    # ------------------------------------------------------------------ media
    def has_media(self):
        return self.cur >= 0 or bool(self.live)

    def playing(self):
        return self.has_media() and not self.paused and not self.ended

    def show_big_play(self):
        return not self.playing()

    def title(self):
        if self.live:
            return self.live.get("n", "")
        if 0 <= self.cur < len(self.queue):
            return self.prop("media-title") or Path(self.queue[self.cur]).stem
        return ""

    def osd(self, text):
        self.video.osd(text)

    def add_files(self, paths, play=False):
        start = len(self.queue)
        subs = []
        for p in paths:
            ext = Path(p).suffix.lower()
            if ext in LIST_EXT:
                n = self.tv.import_file(p)
                self.osd(f"{n} channels added"); self.tabs.setCurrentIndex(1)
            elif ext in SUB_EXT:
                subs.append(p)
            elif os.path.isdir(p):
                for f in sorted(Path(p).iterdir()):
                    if f.suffix.lower() in MEDIA_EXT:
                        self.queue.append(str(f))
            elif ext in MEDIA_EXT or p.startswith(("http://", "https://")):
                self.queue.append(p)
        self.render_queue()
        if len(self.queue) > start:
            self.video.tigu.react_to("pounce")
            if play or not self.has_media():
                self.load(start, True)
        for sub in subs:
            if self.has_media():
                try:
                    self.m.command("sub-add", sub, "select"); self.osd(self.tr("subs") + " ✓")
                except Exception:
                    pass

    def render_queue(self):
        self.qlist.clear()
        if not self.queue:
            it = QListWidgetItem(self.tr("empty")); it.setFlags(Qt.NoItemFlags); self.qlist.addItem(it)
        for i, p in enumerate(self.queue):
            it = QListWidgetItem(f"{i + 1:02d}   {Path(p).stem if not p.startswith('http') else p}")
            self.qlist.addItem(it)
            if i == self.cur:
                it.setSelected(True)
        self.tabs.setTabText(0, f"{self.tr('queue')}  {len(self.queue)}")

    def _queue_menu(self, pt):
        it = self.qlist.itemAt(pt)
        if not it or not self.queue:
            return
        row = self.qlist.row(it)
        menu = QMenu(self)
        a1 = menu.addAction(self.tr("play")); a2 = menu.addAction("Remove from queue"); a3 = menu.addAction("Clear queue")
        r = menu.exec(self.qlist.mapToGlobal(pt))
        if r == a1:
            self.load(row, True)
        elif r == a2:
            self.queue.pop(row)
            if row == self.cur:
                self.cur = -1; self.m.command("stop")
            elif row < self.cur:
                self.cur -= 1
            self.render_queue()
        elif r == a3:
            self.queue.clear(); self.cur = -1; self.m.command("stop"); self.render_queue()

    def _before_switch(self):
        if self.s["resume"] and self.cur >= 0 and not self.live:
            try:
                self.m.command("write-watch-later-config")
            except Exception:
                pass

    def load(self, i, play=True):
        if not 0 <= i < len(self.queue):
            return
        self._before_switch()
        self.live = None
        self.cur = i
        self.ended = False
        self.setp("referrer", ""); self.setp("user-agent", "")
        self.setp("ab-loop-a", "no"); self.setp("ab-loop-b", "no"); self.b_ab.setChecked(False); self.b_ab.setText("A–B")
        self.m.loadfile(self.queue[i])
        self.setp("pause", not play)
        self.setp("speed", float(self.s["speed"]))
        self.video.now_text = f"{i + 1:02d} / {Path(self.queue[i]).stem}"
        self.video.live = False
        self.render_queue()
        self.tvp.list.viewport().update()

    def play_live(self, ch):
        if ch.get("sample") or not ch.get("u"):
            self.osd("Update channels to load the live link"); self.video.tigu.react_to("huh")
            self.tabs.setCurrentIndex(1)
            return
        self._before_switch()
        self.live, self.cur, self.ended = ch, -1, False
        self.setp("referrer", ch.get("r") or ""); self.setp("user-agent", ch.get("ua") or "Mozilla/5.0 LigerPlayer")
        if self.s["lowlat"]:
            try:
                self.m.command("apply-profile", "low-latency")
            except Exception:
                pass
        self.m.loadfile(ch["u"])
        self.setp("pause", False); self.setp("speed", 1.0)
        self.video.now_text, self.video.live = ch.get("n", ""), True
        self.osd(ch.get("n", ""))
        self.render_queue()
        self.tvp.list.viewport().update()

    def _end_file(self, reason):
        import mpv
        if reason == mpv.MpvEventEndFile.ERROR:
            if self.live:
                bad = self.live
                self.tv.mark_dead(bad["id"]); self.osd("Channel offline"); self.video.tigu.react_to("huh"); self.tvp.list.viewport().update()
                if self.s["tvSkipDead"]:
                    QTimer.singleShot(1200, lambda: self.live is bad and self.next(1))
            else:
                self.osd("This file can’t be played"); self.video.tigu.react_to("huh")
        elif reason == mpv.MpvEventEndFile.EOF:
            self.ended = True
            if self.live:
                return
            if self.loop == 2:
                self.load(self.cur, True)
            elif self.s["autonext"]:
                self.next(1, auto=True)

    def toggle(self):
        if not self.has_media():
            if self.queue:
                self.load(0, True)
            else:
                self.open_dialog()
            return
        if self.ended and self.cur >= 0:
            self.load(self.cur, True); return
        self.setp("pause", not self.prop("pause", True))

    def next(self, d=1, auto=False):
        if self.live:
            ch = self.tvp.step(self.live, d)
            if ch:
                self.play_live(ch)
            return
        if not self.queue:
            return
        if self.shuffle and len(self.queue) > 1:
            n = random.choice([i for i in range(len(self.queue)) if i != self.cur])
        else:
            n = self.cur + d
        if n >= len(self.queue):
            if self.loop == 1 or self.s["queueEnd"] == "repeat":
                n = 0
            elif auto:
                return
            else:
                n = len(self.queue) - 1
        if n < 0:
            n = len(self.queue) - 1
        self.load(n, True)

    def prev(self):
        if not self.live and self.pos > 3:
            self.seek_to(0)
        else:
            self.next(-1)

    def seekable(self):
        return bool(self.dur) and not (self.live and not self.prop("seekable", False))

    def skip(self, secs):
        if not self.has_media():
            return
        try:
            self.m.command("seek", secs, "relative+exact" if abs(secs) < 3 else "relative")
            self.osd(("+" if secs > 0 else "−") + f"{abs(secs)} s")
        except Exception:
            pass

    def seek_to(self, t):
        try:
            self.m.command("seek", t, "absolute")
        except Exception:
            pass

    def set_volume(self, v):
        v = int(v)
        self.setp("mute", False)
        self.setp("volume", v)
        self.s.set("volume", v, emit=False)
        self.l_vol.setText(f"{v}%")
        if self.vol.value() != v:
            self.vol.blockSignals(True); self.vol.setValue(v); self.vol.blockSignals(False)
        if v >= 150 and getattr(self, "_last_vol", 0) < 150:
            self.video.tigu.react_to("loud")
        self._last_vol = v
        self.btn["volume"].setIcon(theme.icon("volume", self.tok["ink"]))

    def nudge_volume(self, d):
        self.set_volume(max(0, min(int(self.s["boost"]), int(self.s["volume"]) + d)))
        self.osd(f"{self.tr('volume')} {int(self.s['volume'])}%")

    def toggle_mute(self):
        m = not self.prop("mute", False)
        self.setp("mute", m)
        self.btn["volume"].setIcon(theme.icon("mute" if m else "volume", self.accent() if m else self.tok["ink"]))
        self.osd(self.tr("mute") if m else f"{self.tr('volume')} {int(self.s['volume'])}%")
        if m:
            self.video.tigu.react_to("mute")

    def set_speed(self, x):
        x = max(0.1, min(8.0, round(x, 2)))
        self.setp("speed", x)
        self.osd(f"{x:.2f}×")

    def cycle_speed(self):
        opts = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 3, 4]
        cur = self.prop("speed", 1.0)
        nxt = next((o for o in opts if o > cur + 0.001), opts[0])
        self.set_speed(nxt)

    def cycle_loop(self):
        self.loop = (self.loop + 1) % 3
        self.btn["loop"].setChecked(self.loop > 0)
        self.btn["loop"].setIcon(theme.icon("loop", self.accent() if self.loop else self.tok["ink"]))
        self.osd(["Repeat off", "Repeat all", "Repeat one"][self.loop])

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        self.btn["shuffle"].setChecked(self.shuffle)
        self.btn["shuffle"].setIcon(theme.icon("shuffle", self.accent() if self.shuffle else self.tok["ink"]))
        self.osd("Shuffle on" if self.shuffle else "Shuffle off")

    def ab_step(self):
        a, b = self.prop("ab-loop-a", "no"), self.prop("ab-loop-b", "no")
        if a == "no":
            self.setp("ab-loop-a", self.pos); self.b_ab.setText("A→?"); self.b_ab.setChecked(True); self.osd("A")
        elif b == "no":
            self.setp("ab-loop-b", self.pos); self.b_ab.setText("A↔B"); self.b_ab.setChecked(True); self.osd("A–B ✓")
        else:
            self.setp("ab-loop-a", "no"); self.setp("ab-loop-b", "no"); self.b_ab.setText("A–B"); self.b_ab.setChecked(False); self.osd("A–B ✕")

    def cycle_subs(self):
        if not self.has_media():
            self.osd(self.tr("nomedia")); return
        tracks = [t for t in (self.prop("track-list", []) or []) if t.get("type") == "sub"]
        if not tracks:
            self.open_subs(); return
        try:
            self.m.command("cycle", "sub")
            sid = self.prop("sid", False)
            self.osd(f"{self.tr('c_subtitles')}: {'off' if sid in (False, 'no', None) else sid}")
        except Exception:
            pass

    def sub_shift(self, ms):
        self.s.set("subDelay", max(-5000, min(5000, self.s["subDelay"] + ms)))
        self.osd(f"Sub {self.s['subDelay']:+d} ms")

    def screenshot(self):
        if not self.has_media():
            self.osd(self.tr("nomedia")); return
        try:
            d = Path(self.prop("screenshot-directory", ""))
            d.mkdir(parents=True, exist_ok=True)
            self.m.command("screenshot", "subtitles" if self.s["shotSubs"] else "video")
            self.osd(f"{self.tr('screenshot')} ✓  {d.name}")
            self.video.tigu.react_to("shot")
        except Exception:
            self.osd("Screenshot failed")

    def frame_step(self, d):
        if self.has_media():
            try:
                self.m.command("frame-step" if d > 0 else "frame-back-step")
            except Exception:
                pass

    def fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.header.show(); self.side.show(); self.deck.show()
            self.centralWidget().layout().setContentsMargins(16, 14, 16, 16)
        else:
            self.header.hide(); self.side.hide()
            self.centralWidget().layout().setContentsMargins(0, 0, 0, 0)
            self.showFullScreen()
            self.idle_t.start(self.s["autohide"] * 1000)

    def _hide_deck(self):
        if self.isFullScreen() and self.playing():
            self.deck.hide()
            self.setCursor(Qt.BlankCursor)

    def open_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, self.tr("open"), "", "Media (" + " ".join("*" + e for e in sorted(MEDIA_EXT)) + ");;All files (*)")
        if files:
            self.add_files(files, play=True)

    def open_subs(self):
        if not self.has_media():
            self.osd(self.tr("nomedia")); return
        f, _ = QFileDialog.getOpenFileName(self, self.tr("subs"), "", "Subtitles (*.srt *.ass *.ssa *.vtt *.sub)")
        if f:
            self.add_files([f])

    def _video_click(self):
        self.toggle()

    def _wheel(self, d):
        if self.s["wheel"] == "volume":
            self.nudge_volume(5 * d)
        elif self.s["wheel"] == "seek":
            self.skip(self.s["stepShort"] * d)

    # ------------------------------------------------------------------ timers
    def _poll(self):
        self.pos = self.prop("time-pos", 0.0) or 0.0
        self.dur = self.prop("duration", 0.0) or 0.0
        self.paused = bool(self.prop("pause", True)) or self.prop("idle-active", True)
        vp = self.prop("video-params", None)
        img = self.prop("current-tracks/video/image", False) or self.prop("current-tracks/video/albumart", False)
        self.is_video = bool(vp) and not img
        live_unseekable = self.live and not self.prop("seekable", False)
        self.seek.pos, self.seek.dur, self.seek.live = self.pos, self.dur, bool(live_unseekable)
        self.seek.buf = self.pos + (self.prop("demuxer-cache-duration", 0.0) or 0.0)
        a, b = self.prop("ab-loop-a", "no"), self.prop("ab-loop-b", "no")
        self.seek.ab = (None if a == "no" else a, None if b == "no" else b)
        self.l_pos.setText(fmt(self.pos))
        self.l_dur.setText("LIVE" if live_unseekable else ("−" + fmt(self.dur - self.pos) if self.s["remaining"] and self.dur else fmt(self.dur)))
        sp = self.prop("speed", 1.0)
        self.b_speed.setText(f"{sp:.2f}×"); self.b_speed.setChecked(abs(sp - 1) > 0.001)
        if self.play_btn.playing != self.playing():
            self.play_btn.playing = self.playing()
            self.play_btn.setToolTip(self.tr("pause") if self.playing() else self.tr("play"))
            self.lighting.calm = self.s["rgbCalm"] and self.playing()
            self._keep_awake(self.playing())
        self.seek.update()

    def _tick(self):
        self.video.update()
        if self.lighting.animating() or self.s["rgbFx"] == "spectrum":
            for w in list(self.rgb_widgets):
                try:
                    w.update()
                except RuntimeError:
                    self.rgb_widgets.discard(w)

    def _stats(self):
        if not self.s["stats"] or not self.has_media():
            self.video.stats_text = ""
            return
        vp = self.prop("video-params", {}) or {}
        ap = self.prop("audio-params", {}) or {}
        lines = []
        if vp:
            lines.append(f"VIDEO  {vp.get('w', '?')}×{vp.get('h', '?')} · {self.prop('video-codec-name', self.prop('video-format', '?'))}")
            fps = self.prop("estimated-vf-fps", 0) or self.prop("container-fps", 0) or 0
            lines.append(f"FPS  {fps:.2f} · display {self.prop('display-fps', 0) or (self.screen().refreshRate() if self.screen() else 0):.0f} Hz")
            lines.append(f"DROPPED  {self.prop('frame-drop-count', 0)} · decoder {self.prop('decoder-frame-drop-count', 0)}")
            lines.append(f"HWDEC  {self.prop('hwdec-current', 'no')}")
        if ap:
            lines.append(f"AUDIO  {self.prop('audio-codec-name', '?')} · {ap.get('samplerate', 0) // 1000} kHz · {ap.get('channel-count', '?')} ch")
        lines.append(f"BUFFER  {self.prop('demuxer-cache-duration', 0) or 0:.1f} s")
        lines.append(f"SPEED  {self.prop('speed', 1.0):.2f}× · VOL {int(self.s['volume'])}%")
        self.video.stats_text = "\n".join(lines)

    def _keep_awake(self, on):
        if sys.platform == "win32" and self.s["keepAwake"]:
            try:
                ES_CONTINUOUS, ES_SYSTEM_REQUIRED, ES_DISPLAY_REQUIRED = 0x80000000, 0x00000001, 0x00000002
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ((ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED) if on else 0))
            except Exception:
                pass

    def _app_state(self, state):
        if state != Qt.ApplicationActive and self.s["pauseAway"] and self.playing():
            self.setp("pause", True)

    def _tv_updated(self, err):
        self.tvp.rebuild()
        self.retranslate()
        self.osd(self.tr("tvupdate") + (" ✕" if err and not self.tv.channels else " ✓"))

    # ------------------------------------------------------------------ input
    def eventFilter(self, obj, e):
        t = e.type()
        if t in (QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.Wheel, QEvent.KeyPress):
            self.video.tigu.poke()
            if self.isFullScreen():
                if not self.deck.isVisible():
                    self.deck.show(); self.unsetCursor()
                self.idle_t.start(self.s["autohide"] * 1000)
        if t == QEvent.KeyPress and QApplication.activeWindow() is self:
            fw = QApplication.focusWidget()
            if isinstance(fw, (QLineEdit, QAbstractSpinBox)) or (isinstance(fw, QComboBox) and fw.view().isVisible()):
                return False
            if self._hotkey(e):
                return True
        return False

    def _hotkey(self, e):
        if e.key() in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
            return False
        if e.key() == Qt.Key_Escape and self.isFullScreen():
            self.fullscreen(); return True
        mods = e.modifiers()
        seq = QKeySequence(e.keyCombination()).toString()
        base = QKeySequence(e.key()).toString()
        hk = self.s["hotkeys"]
        act = next((a for a, k in hk.items() if k and k == seq), None)
        long_seek = False
        if not act and mods & (Qt.ShiftModifier | Qt.ControlModifier):
            act = next((a for a, k in hk.items() if k and k == base and a in ("back", "fwd")), None)
            long_seek = bool(act)
        if e.key() in (Qt.Key_MediaPlay, Qt.Key_MediaPause, Qt.Key_MediaTogglePlayPause):
            act = "play"
        elif e.key() == Qt.Key_MediaNext:
            act = "next"
        elif e.key() == Qt.Key_MediaPrevious:
            act = "prev"
        if not act:
            return False
        st = self.s["stepLong"] if long_seek else self.s["stepShort"]
        {
            "play": self.toggle, "back": lambda: self.skip(-st), "fwd": lambda: self.skip(st),
            "volup": lambda: self.nudge_volume(5), "voldown": lambda: self.nudge_volume(-5), "next": lambda: self.next(1), "prev": self.prev,
            "fullscreen": self.fullscreen, "mute": self.toggle_mute, "slower": lambda: self.set_speed(self.prop("speed", 1.0) - float(self.s["speedStep"])),
            "faster": lambda: self.set_speed(self.prop("speed", 1.0) + float(self.s["speedStep"])), "ab": self.ab_step, "loop": self.cycle_loop,
            "shuffle": self.toggle_shuffle, "subs": self.cycle_subs, "subminus": lambda: self.sub_shift(-50), "subplus": lambda: self.sub_shift(50),
            "shot": self.screenshot, "stats": lambda: self.s.set("stats", not self.s["stats"]), "settings": lambda: self.open_settings(),
            "tv": lambda: self.tabs.setCurrentIndex(1 - self.tabs.currentIndex()), "frameNext": lambda: self.frame_step(1),
            "framePrev": lambda: self.frame_step(-1), "open": self.open_dialog,
        }[act]()
        return True

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self.add_files([u.toLocalFile() or u.toString() for u in e.mimeData().urls()], play=True)

    def closeEvent(self, e):
        self._before_switch()
        self._keep_awake(False)
        self.s.save()
        self.anim.stop(); self.poll.stop()
        self.video.free()
        try:
            self.m.terminate()
        except Exception:
            pass
        super().closeEvent(e)


def main():
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Liger.Player")
        except Exception:
            pass
    from PySide6.QtGui import QSurfaceFormat
    fmt_ = QSurfaceFormat.defaultFormat(); fmt_.setSwapInterval(1); QSurfaceFormat.setDefaultFormat(fmt_)
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName("Liger Player")
    app.setOrganizationName("Liger")
    locale.setlocale(locale.LC_NUMERIC, "C")
    theme.load_fonts()
    files = [a for a in sys.argv[1:] if not a.startswith("-")]
    w = App(files)
    w.show()
    sys.exit(app.exec())
