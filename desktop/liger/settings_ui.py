"""The settings window: Simple mode by default, Advanced reveals every category, plus search."""
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QLinearGradient, QPainter
from PySide6.QtWidgets import (QButtonGroup, QColorDialog, QComboBox, QDialog, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QSlider, QVBoxLayout, QWidget)

from .i18n import INTL, LANGS
from .rgb import PALETTE_NAMES, PALETTES
from .settings import CATS, C, DEFAULTS, EQ_BANDS, EQ_PRESETS, HOTKEY_LABELS, ZONES


class Switch(QWidget):
    toggled = Signal(bool)

    def __init__(self, on, accent, line):
        super().__init__()
        self.on, self.accent, self.line = bool(on), accent, line
        self.setFixedSize(42, 24)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(self.accent if self.on else self.line))
        p.fillRect(QRectF(22 if self.on else 4, 4, 16, 16), QColor("#ffffff"))
        if self.hasFocus():
            p.setPen(QColor(self.accent)); p.drawRect(self.rect().adjusted(0, 0, -1, -1))
        p.end()

    def mousePressEvent(self, _):
        self.flip()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Space, Qt.Key_Return):
            self.flip()
        else:
            super().keyPressEvent(e)

    def flip(self):
        self.on = not self.on
        self.update()
        self.toggled.emit(self.on)


class GradBar(QWidget):
    def __init__(self, colors):
        super().__init__()
        self.colors = colors
        self.setFixedHeight(10)

    def paintEvent(self, _):
        p = QPainter(self)
        g = QLinearGradient(0, 0, self.width(), 0)
        for i, c in enumerate(self.colors):
            g.setColorAt(i / max(1, len(self.colors) - 1), QColor(c))
        p.fillRect(self.rect(), g)
        p.end()


class Preview(QWidget):
    """A strip that shows the live lighting effect."""

    def __init__(self, app):
        super().__init__()
        self.a = app
        self.setFixedHeight(34)

    def paintEvent(self, _):
        p = QPainter(self)
        r = QRectF(self.rect())
        p.fillRect(r, self.a.lighting.brush(r, self.a.accent()))
        p.end()


class SettingsDialog(QDialog):
    def __init__(self, app):
        super().__init__(app)
        self.a = app
        self.s = app.s
        self.cat = "interface"
        self.capture = None
        self.setWindowTitle("Liger Player · " + app.tr("settings"))
        self.resize(820, 640)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        head = QFrame(); head.setObjectName("panel")
        hl = QHBoxLayout(head); hl.setContentsMargins(18, 12, 18, 12)
        self.title = QLabel(); self.title.setObjectName("h2")
        hl.addWidget(self.title, 1)
        self.mode_btns = {}
        mg = QButtonGroup(self)
        for m in ("simple", "advanced"):
            b = QPushButton(); b.setObjectName("seg"); b.setCheckable(True)
            b.clicked.connect(lambda _=False, m=m: self._mode(m))
            mg.addButton(b); hl.addWidget(b); self.mode_btns[m] = b
        root.addWidget(head)
        sb = QFrame(); sl = QHBoxLayout(sb); sl.setContentsMargins(18, 10, 18, 10)
        self.search = QLineEdit(); self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _: self.render())
        sl.addWidget(self.search)
        root.addWidget(sb)
        body = QHBoxLayout(); body.setContentsMargins(0, 0, 0, 0); body.setSpacing(0)
        self.cats = QListWidget(); self.cats.setObjectName("cats"); self.cats.setFixedWidth(190)
        self.cats.currentRowChanged.connect(self._cat)
        body.addWidget(self.cats)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        body.addWidget(self.scroll, 1)
        root.addLayout(body, 1)
        foot = QFrame(); fl = QHBoxLayout(foot); fl.setContentsMargins(18, 10, 18, 12)
        fl.addStretch(1)
        self.reset_btn = QPushButton(); self.reset_btn.clicked.connect(self._reset)
        close = QPushButton(); close.setObjectName("primary"); close.clicked.connect(self.accept)
        self.close_btn = close
        fl.addWidget(self.reset_btn); fl.addWidget(close)
        root.addWidget(foot)
        self.retranslate()

    def retranslate(self):
        t = self.a.tr
        self.setLayoutDirection(Qt.RightToLeft if t.rtl() else Qt.LeftToRight)
        self.title.setText(t("settings"))
        self.mode_btns["simple"].setText(t("simple")); self.mode_btns["advanced"].setText(t("advanced"))
        self.search.setPlaceholderText(t("search"))
        self.reset_btn.setText(t("reset")); self.close_btn.setText(t("close"))
        self.cats.blockSignals(True); self.cats.clear()
        for cid, key in CATS:
            it = QListWidgetItem(t(key)); it.setData(Qt.UserRole, cid); self.cats.addItem(it)
        self.cats.setCurrentRow([c for c, _ in CATS].index(self.cat)); self.cats.blockSignals(False)
        self.render()

    def open_category(self, cid):
        self.cat = cid
        self.s.set("mode", "advanced", emit=False)
        self.retranslate()

    def _mode(self, m):
        self.s.set("mode", m, emit=False)
        self.render()

    def _cat(self, row):
        if row >= 0:
            self.cat = CATS[row][0]
            self.search.blockSignals(True); self.search.clear(); self.search.blockSignals(False)
            self.render()

    def _reset(self):
        self.s.reset()
        self.retranslate()

    def set(self, k, v, rerender=False):
        self.s.set(k, v)
        if rerender:
            self.render()

    # ---- building rows ----
    def render(self):
        t = self.a.tr
        simple = self.s["mode"] == "simple"
        for m, b in self.mode_btns.items():
            b.setChecked(self.s["mode"] == m)
        q = self.search.text().strip().lower()
        self.cats.setVisible(not simple and not q)
        if q:
            items = [x for x in C if q in (t.label(x["l"]) + " " + x.get("h", "") + " " + x["k"]).lower()]
        elif simple:
            items = [x for x in C if x.get("s")]
        else:
            items = [x for x in C if x["c"] == self.cat]
        page = QWidget(); page.setObjectName("page"); lay = QVBoxLayout(page); lay.setContentsMargins(18, 6, 18, 24); lay.setSpacing(0)
        last = None
        for it in items:
            if (simple or q) and it["c"] != last:
                last = it["c"]
                g = QLabel(t(dict(CATS)[it["c"]]).upper()); g.setObjectName("grp"); lay.addWidget(g)
            lay.addWidget(self.row(it))
        if q and not items:
            lay.addWidget(QLabel(f"No setting matches “{q}”."))
        if simple and not q:
            n = QLabel(f"{len(C) - len(items)} more options in {t('advanced')}."); n.setObjectName("muted"); n.setContentsMargins(0, 14, 0, 0)
            lay.addWidget(n)
        lay.addStretch(1)
        old = self.scroll.verticalScrollBar().value()
        self.scroll.setWidget(page)
        self.scroll.verticalScrollBar().setValue(old)

    def row(self, it):
        t = self.a.tr
        k, typ = it["k"], it["t"]
        wide = typ in ("accent", "eq", "hk", "lang", "pal", "zones", "urls", "text", "folder")
        w = QFrame(); w.setObjectName("row")
        g = QGridLayout(w); g.setContentsMargins(0, 12, 0, 12); g.setHorizontalSpacing(16)
        left = QVBoxLayout(); left.setSpacing(3)
        lb = QLabel(t.label(it["l"])); lb.setStyleSheet("font-weight:600;font-size:14px")
        left.addWidget(lb)
        if it.get("h"):
            h = QLabel(it["h"]); h.setObjectName("muted"); h.setWordWrap(True); left.addWidget(h)
        g.addLayout(left, 0, 0)
        ctl = self.control(it)
        if wide:
            g.addWidget(ctl, 1, 0)
        else:
            g.addWidget(ctl, 0, 1, Qt.AlignRight | Qt.AlignVCenter)
            g.setColumnStretch(0, 1)
        return w

    def control(self, it):
        t, s, a = self.a.tr, self.s, self.a
        k, typ = it["k"], it["t"]
        if typ == "tog":
            sw = Switch(s[k], a.accent(), a.tok["line"]); sw.toggled.connect(lambda v: self.set(k, v)); return sw
        if typ == "seg":
            box = QWidget(); h = QHBoxLayout(box); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(2)
            grp = QButtonGroup(box)
            for val, lab in it["o"]:
                b = QPushButton(t.label(lab)); b.setObjectName("seg"); b.setCheckable(True); b.setChecked(str(s[k]) == val)
                b.clicked.connect(lambda _=False, v=val: self.set(k, v, rerender=k == "rgbFx")); grp.addButton(b); h.addWidget(b)
            return box
        if typ == "sel":
            cb = QComboBox()
            for val, lab in it["o"]:
                cb.addItem(t.label(lab), val)
            cb.setCurrentIndex(max(0, [v for v, _ in it["o"]].index(str(s[k])) if str(s[k]) in [v for v, _ in it["o"]] else 0))
            cb.currentIndexChanged.connect(lambda i: self.set(k, cb.itemData(i))); return cb
        if typ == "range":
            box = QWidget(); h = QHBoxLayout(box); h.setContentsMargins(0, 0, 0, 0)
            sl = QSlider(Qt.Horizontal); sl.setRange(it["min"], it["max"]); sl.setSingleStep(it["step"]); sl.setPageStep(it["step"]); sl.setValue(int(s[k])); sl.setFixedWidth(200)
            out = QLabel(); out.setObjectName("mono"); out.setFixedWidth(70); out.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            def upd(v):
                v = round(v / it["step"]) * it["step"]
                out.setText(f"{'+' if k in ('subDelay', 'adelay') and v > 0 else ''}{v}{it.get('u', '')}")
                return v
            upd(s[k])
            sl.valueChanged.connect(lambda v: self.set(k, upd(v)))
            h.addWidget(sl); h.addWidget(out); return box
        if typ == "color":
            b = QPushButton(s[k]); b.setStyleSheet(f"background:{s[k]};color:{'#111' if QColor(s[k]).lightness() > 140 else '#fff'}")
            def pick():
                c = QColorDialog.getColor(QColor(s[k]), self)
                if c.isValid():
                    self.set(k, c.name(), rerender=True)
            b.clicked.connect(pick); return b
        if typ in ("text", "folder"):
            box = QWidget(); h = QHBoxLayout(box); h.setContentsMargins(0, 0, 0, 0)
            e = QLineEdit(s[k]); e.editingFinished.connect(lambda: self.set(k, e.text().strip() if (e.text().strip() or typ == "folder") else DEFAULTS[k]))
            h.addWidget(e)
            if typ == "folder":
                b = QPushButton("Choose…")
                def choose():
                    d = QFileDialog.getExistingDirectory(self, "Screenshots folder", s[k] or "")
                    if d:
                        e.setText(d); self.set(k, d)
                b.clicked.connect(choose); h.addWidget(b)
            return box
        if typ == "act":
            b = QPushButton(t.label(it["btn"])); b.setObjectName("primary"); b.clicked.connect(lambda: a.action(it["act"])); return b
        return getattr(self, "ctl_" + typ)(it)

    def ctl_lang(self, it):
        t, s = self.a.tr, self.s
        box = QWidget(); v = QVBoxLayout(box); v.setContentsMargins(0, 0, 0, 0)
        cb = QComboBox()
        def add_group(title, codes):
            cb.addItem(f"— {title} —"); cb.model().item(cb.count() - 1).setEnabled(False)
            for code, nat, eng, tier, _ in LANGS:
                if code in codes:
                    cb.addItem(f"{nat} · {eng}{' (draft)' if tier == 'd' else ' (help wanted)' if tier == 'h' else ''}", code)
        add_group("International", INTL)
        add_group("India", [l[0] for l in LANGS if l[0] not in INTL])
        cb.setCurrentIndex(cb.findData(s["lang"]))
        cb.currentIndexChanged.connect(lambda i: cb.itemData(i) and self.s.set("lang", cb.itemData(i)))
        v.addWidget(cb)
        tier = t.tier()
        if tier != "r":
            n = QLabel("Draft translation. A native speaker should review it before release." if tier == "d" else "No reviewed translation yet. The interface shows English until a native speaker contributes one.")
            n.setObjectName("note"); n.setWordWrap(True); v.addWidget(n)
        return box

    def ctl_accent(self, it):
        s = self.s
        box = QWidget(); v = QVBoxLayout(box); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        sw = QHBoxLayout()
        for c in ("#2f6bff", "#00b8d9", "#14c38e", "#a3e635", "#ffb020", "#ff5d3a", "#ff2e88", "#8b5cf6", "#111827"):
            b = QPushButton(); b.setFixedSize(28, 28); b.setToolTip(c)
            b.setStyleSheet(f"background:{c};border:{'2px solid ' + self.a.tok['ink'] if s['accent'] == c else '1px solid ' + self.a.tok['line']};padding:0")
            b.clicked.connect(lambda _=False, c=c: self.set("accent", c, rerender=True)); sw.addWidget(b)
        sw.addStretch(1); v.addLayout(sw)
        hexrow = QHBoxLayout()
        hx = QLineEdit(s["accent"]); hx.setFixedWidth(110); hx.setMaxLength(7)
        hexrow.addWidget(QLabel("Hex")); hexrow.addWidget(hx); hexrow.addStretch(1); v.addLayout(hexrow)
        c0 = QColor(s["accent"])
        sliders = []
        for i, (ch, col) in enumerate((("R", "#ff3b3b"), ("G", "#22c55e"), ("B", "#3b82f6"))):
            r = QHBoxLayout(); lab = QLabel(ch); lab.setStyleSheet(f"color:{col};font-weight:700"); lab.setFixedWidth(16)
            sl = QSlider(Qt.Horizontal); sl.setRange(0, 255); sl.setValue((c0.red(), c0.green(), c0.blue())[i])
            num = QLabel(str(sl.value())); num.setObjectName("mono"); num.setFixedWidth(34)
            sl.valueChanged.connect(lambda val, num=num: num.setText(str(val)))
            r.addWidget(lab); r.addWidget(sl, 1); r.addWidget(num); v.addLayout(r); sliders.append(sl)
        def from_sliders():
            c = QColor(*[x.value() for x in sliders]).name()
            hx.setText(c); self.set("accent", c)
        for sl in sliders:
            sl.sliderReleased.connect(from_sliders)
            sl.valueChanged.connect(lambda _: (not any(x.isSliderDown() for x in sliders)) and from_sliders())
        def from_hex():
            txt = hx.text().strip()
            txt = txt if txt.startswith("#") else "#" + txt
            if QColor.isValidColorName(txt) and len(txt) == 7:
                self.set("accent", txt.lower(), rerender=True)
        hx.editingFinished.connect(from_hex)
        return box

    def ctl_dir(self, it):
        s = self.s
        box = QWidget(); g = QGridLayout(box); g.setContentsMargins(0, 0, 0, 0); g.setSpacing(4)
        fx = s["rgbFx"]
        usable = fx in ("wave", "rotate", "ripple", "breath")
        grp = QButtonGroup(box)
        cells = [("nw", "↖"), ("n", "↑"), ("ne", "↗"), ("w", "←"), ("", "⟳" if fx == "rotate" else "◎" if fx == "ripple" else "·"), ("e", "→"), ("sw", "↙"), ("s", "↓"), ("se", "↘")]
        for i, (d, ar) in enumerate(cells):
            b = QPushButton(ar); b.setObjectName("seg"); b.setFixedSize(36, 34)
            if d:
                b.setCheckable(True); b.setChecked(s["rgbDir"] == d); b.setEnabled(usable)
                b.clicked.connect(lambda _=False, d=d: self.set("rgbDir", d)); grp.addButton(b)
            else:
                b.setEnabled(False)
            g.addWidget(b, i // 3, i % 3)
        return box

    def ctl_pal(self, it):
        s = self.s
        box = QWidget(); v = QVBoxLayout(box); v.setContentsMargins(0, 0, 0, 0)
        g = QGridLayout(); g.setSpacing(8)
        for i, key in enumerate(PALETTE_NAMES):
            cols = s["rgbCustom"] if key == "custom" else [s["accent"], "#ffffff"] if key == "mono" else PALETTES[key]
            b = QPushButton(); b.setCheckable(True); b.setChecked(s["rgbPal"] == key); b.setObjectName("seg"); b.setMinimumHeight(46)
            bl = QVBoxLayout(b); bl.setContentsMargins(6, 6, 6, 6); bl.addWidget(GradBar(cols)); nm = QLabel(PALETTE_NAMES[key]); nm.setStyleSheet("font-size:12px;font-weight:600;background:transparent"); bl.addWidget(nm)
            b.clicked.connect(lambda _=False, key=key: self.set("rgbPal", key, rerender=True))
            g.addWidget(b, i // 4, i % 4)
        v.addLayout(g)
        if s["rgbPal"] == "custom":
            row = QHBoxLayout()
            for i, c in enumerate(s["rgbCustom"]):
                b = QPushButton(); b.setFixedSize(34, 30); b.setStyleSheet(f"background:{c};padding:0")
                def pick(_=False, i=i):
                    col = QColorDialog.getColor(QColor(s["rgbCustom"][i]), self)
                    if col.isValid():
                        lst = list(s["rgbCustom"]); lst[i] = col.name(); self.set("rgbCustom", lst, rerender=True)
                b.clicked.connect(pick); row.addWidget(b)
            add = QPushButton("+ Add"); add.setEnabled(len(s["rgbCustom"]) < 6)
            add.clicked.connect(lambda: self.set("rgbCustom", s["rgbCustom"] + ["#ffffff"], rerender=True))
            rm = QPushButton("− Remove"); rm.setEnabled(len(s["rgbCustom"]) > 2)
            rm.clicked.connect(lambda: self.set("rgbCustom", s["rgbCustom"][:-1], rerender=True))
            row.addWidget(add); row.addWidget(rm); row.addStretch(1); v.addLayout(row)
        pv = Preview(self.a); v.addWidget(pv)
        self.a.rgb_widgets.add(pv)
        return box

    def ctl_zones(self, it):
        s = self.s
        box = QWidget(); h = QHBoxLayout(box); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(6)
        for z, lab in ZONES:
            b = QPushButton(lab); b.setObjectName("seg"); b.setCheckable(True); b.setChecked(z in s["rgbZones"])
            def tog(on, z=z):
                lst = [x for x in s["rgbZones"] if x != z] + ([z] if on else [])
                self.set("rgbZones", lst)
            b.toggled.connect(tog); h.addWidget(b)
        h.addStretch(1)
        return box

    def ctl_eq(self, it):
        s = self.s
        box = QWidget(); v = QVBoxLayout(box); v.setContentsMargins(0, 0, 0, 0)
        pr = QHBoxLayout(); pr.setSpacing(2); grp = QButtonGroup(box)
        for key, lab in (("flat", "Flat"), ("bass", "Bass"), ("vocal", "Vocal"), ("footsteps", "Footsteps"), ("treble", "Treble")):
            b = QPushButton(lab); b.setObjectName("seg"); b.setCheckable(True); b.setChecked(s["eqPreset"] == key)
            def preset(_=False, key=key):
                self.s.set("eqPreset", key, emit=False); self.set("eq", list(EQ_PRESETS[key]), rerender=True)
            b.clicked.connect(preset); grp.addButton(b); pr.addWidget(b)
        pr.addStretch(1); v.addLayout(pr)
        bands = QHBoxLayout()
        for i, f in enumerate(EQ_BANDS):
            col = QVBoxLayout(); col.setAlignment(Qt.AlignHCenter)
            val = QLabel(f"{s['eq'][i]:+d}"); val.setObjectName("mono"); val.setAlignment(Qt.AlignCenter)
            sl = QSlider(Qt.Vertical); sl.setRange(-12, 12); sl.setValue(s["eq"][i]); sl.setFixedHeight(110)
            def change(x, i=i, val=val):
                lst = list(s["eq"]); lst[i] = x; val.setText(f"{x:+d}"); self.s.set("eqPreset", "custom", emit=False); self.set("eq", lst)
            sl.valueChanged.connect(change)
            lab = QLabel(f"{f // 1000}k" if f >= 1000 else str(f)); lab.setObjectName("mono"); lab.setAlignment(Qt.AlignCenter)
            col.addWidget(val); col.addWidget(sl, 0, Qt.AlignHCenter); col.addWidget(lab); bands.addLayout(col)
        v.addLayout(bands)
        n = QLabel("Footsteps lifts 2–8 kHz, where steps and reloads sit in game clips. Range ±12 dB."); n.setObjectName("muted"); v.addWidget(n)
        return box

    def ctl_urls(self, it):
        s = self.s
        box = QWidget(); v = QVBoxLayout(box); v.setContentsMargins(0, 0, 0, 0)
        for i, u in enumerate(s["tvCustom"]):
            r = QHBoxLayout(); l = QLabel(u); l.setObjectName("mono"); l.setWordWrap(True); r.addWidget(l, 1)
            b = QPushButton("Remove"); b.clicked.connect(lambda _=False, i=i: self.set("tvCustom", [x for j, x in enumerate(s["tvCustom"]) if j != i], rerender=True)); r.addWidget(b)
            v.addLayout(r)
        add = QHBoxLayout(); e = QLineEdit(); e.setPlaceholderText("https://example.com/playlist.m3u")
        ab = QPushButton("Add link"); ab.setObjectName("primary")
        def do_add():
            u = e.text().strip()
            if u.lower().startswith(("http://", "https://")) and u not in s["tvCustom"]:
                self.set("tvCustom", s["tvCustom"] + [u], rerender=True); self.a.action("tvUpdate")
        ab.clicked.connect(do_add)
        fb = QPushButton("Import file…"); fb.clicked.connect(lambda: self.a.action("m3uFile"))
        add.addWidget(e, 1); add.addWidget(ab); add.addWidget(fb); v.addLayout(add)
        return box

    def ctl_hk(self, it):
        t, s = self.a.tr, self.s
        box = QWidget(); g = QGridLayout(box); g.setContentsMargins(0, 0, 0, 0); g.setVerticalSpacing(4)
        for i, (act, lab) in enumerate(HOTKEY_LABELS.items()):
            g.addWidget(QLabel(t.label(lab)), i, 0)
            b = QPushButton("Press a key…" if self.capture == act else (s["hotkeys"].get(act) or "—")); b.setObjectName("pill"); b.setMinimumWidth(110)
            if self.capture == act:
                b.setStyleSheet(f"border-color:{self.a.accent()};color:{self.a.accent()}")
            b.clicked.connect(lambda _=False, act=act: self._capture(act)); g.addWidget(b, i, 1, Qt.AlignRight)
        n = QLabel("Select a shortcut, then press the new key. Esc cancels."); n.setObjectName("muted")
        g.addWidget(n, len(HOTKEY_LABELS), 0, 1, 2)
        return box

    def _capture(self, act):
        self.capture = act
        self.render()
        self.setFocus()

    def keyPressEvent(self, e):
        if self.capture:
            if e.key() not in (Qt.Key_Escape, Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
                seq = QKeySequence(e.keyCombination()).toString()
                hk = {a: (None if v == seq else v) for a, v in self.s["hotkeys"].items()}
                hk[self.capture] = seq
                self.s.set("hotkeys", hk)
            if e.key() not in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
                self.capture = None
                self.render()
            return
        super().keyPressEvent(e)
