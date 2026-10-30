"""Live TV panel: search, category filter, country chips with waving flags, and the channel list."""
import time

from PySide6.QtCore import QEvent, QModelIndex, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (QAbstractButton, QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
                               QScrollArea, QStyle, QStyledItemDelegate, QVBoxLayout, QWidget)

from .flags import country_name, draw_flag
from .theme import MONO


class FlagChip(QAbstractButton):
    def __init__(self, panel, cid, cc, label, count):
        super().__init__()
        self.p, self.cid, self.cc, self.label, self.count = panel, cid, cc, label, count
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self._t = QTimer(self); self._t.setInterval(33); self._t.timeout.connect(self.update)
        f = QFont(); f.setPixelSize(12); f.setWeight(QFont.DemiBold)
        self._f = f
        from PySide6.QtGui import QFontMetrics
        fm = QFontMetrics(f)
        w = 18 + (30 if cc else 0) + fm.horizontalAdvance(label) + 8 + QFontMetrics(QFont(MONO)).horizontalAdvance(str(count))
        self.setFixedSize(w, 30)

    def enterEvent(self, e):
        self._t.start(); super().enterEvent(e)

    def leaveEvent(self, e):
        self._t.stop(); self.update(); super().leaveEvent(e)

    def paintEvent(self, _):
        tok, acc = self.p.a.tok, self.p.a.accent()
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        on = self.isChecked()
        p.setPen(QColor(acc if (on or self.underMouse()) else tok["line"]))
        p.setBrush(QColor(acc).lighter(185) if on and not tok["dark"] else QColor(acc).darker(260) if on else QColor(tok["panel"]))
        p.drawRect(r)
        x = 9
        if self.cc:
            draw_flag(p, x, 8, self.cc, 22, 14, waving=self.underMouse())
            x += 30
        p.setFont(self._f); p.setPen(QColor(acc if on else tok["ink"]))
        tw = p.fontMetrics().horizontalAdvance(self.label)
        p.drawText(QRectF(x, 0, tw + 2, 30), Qt.AlignVCenter, self.label)
        f = QFont(MONO); f.setPixelSize(10); p.setFont(f); p.setPen(QColor(tok["muted"]))
        p.drawText(QRectF(x + tw + 7, 0, 40, 30), Qt.AlignVCenter | Qt.AlignLeft, str(self.count))
        p.end()


class ChannelDelegate(QStyledItemDelegate):
    def __init__(self, panel):
        super().__init__()
        self.p = panel
        self.hover = QModelIndex()

    def sizeHint(self, option, index):
        return QSize(100, 48)

    def paint(self, p: QPainter, opt, index):
        a = self.p.a
        tok, acc = a.tok, a.accent()
        ch = index.data(Qt.UserRole)
        r = opt.rect
        p.save(); p.setRenderHint(QPainter.Antialiasing)
        cur = a.live and ch and a.live.get("id") == ch.get("id")
        if cur:
            p.fillRect(r, QColor(acc).lighter(185) if not tok["dark"] else QColor(acc).darker(280))
            p.fillRect(QRect(r.left(), r.top(), 3, r.height()), QColor(acc))
        elif opt.state & QStyle.State_MouseOver:
            p.fillRect(r, QColor(tok["paper"]))
        if not ch:
            p.restore(); return
        dead = ch.get("id") in self.p.tv.dead
        if dead:
            p.setOpacity(0.45)
        draw_flag(p, r.left() + 12, r.top() + 16, ch.get("cc"), 22, 15, waving=bool(opt.state & QStyle.State_MouseOver))
        f = QFont(); f.setPixelSize(13); f.setWeight(QFont.DemiBold); p.setFont(f); p.setPen(QColor(tok["ink"]))
        tr = QRect(r.left() + 44, r.top() + 6, r.width() - 84, 20)
        p.drawText(tr, Qt.AlignVCenter | Qt.AlignLeft, p.fontMetrics().elidedText(ch.get("n", ""), Qt.ElideRight, tr.width()))
        meta = f"{ch.get('cc') or '—'} · {ch.get('cat', '')}"
        if ch.get("q"): meta += " · " + ch["q"]
        if ch.get("sample"): meta += " · SAMPLE"
        if dead: meta += " · OFFLINE"
        fm = QFont(MONO); fm.setPixelSize(10); p.setFont(fm); p.setPen(QColor(tok["muted"]))
        p.drawText(QRect(r.left() + 44, r.top() + 26, r.width() - 84, 16), Qt.AlignVCenter | Qt.AlignLeft, meta.upper())
        p.setOpacity(1)
        fav = ch.get("id") in self.p.a.s["tvFav"]
        fs = QFont(); fs.setPixelSize(16); p.setFont(fs); p.setPen(QColor("#f5a524" if fav else tok["muted"]))
        p.drawText(self.star_rect(r), Qt.AlignCenter, "★" if fav else "☆")
        p.restore()

    def star_rect(self, r):
        return QRect(r.right() - 36, r.top() + 8, 30, 32)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease and self.star_rect(option.rect).contains(event.position().toPoint()):
            ch = index.data(Qt.UserRole)
            if ch:
                self.p._star_t = time.monotonic()
                self.p.toggle_fav(ch["id"])
            return True
        return False


class TVPanel(QWidget):
    play = Signal(dict)

    def __init__(self, app, tv):
        super().__init__()
        self.a, self.tv = app, tv
        self.view = []
        self.shown = 200
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        bar = QHBoxLayout(); bar.setContentsMargins(10, 10, 10, 6)
        self.search = QLineEdit(); self.search.setPlaceholderText("Search channels"); self.search.setClearButtonEnabled(True)
        self.cat = QComboBox(); self.cat.setMinimumWidth(110)
        bar.addWidget(self.search, 1); bar.addWidget(self.cat)
        v.addLayout(bar)
        self.chips_area = QScrollArea(); self.chips_area.setFixedHeight(46); self.chips_area.setWidgetResizable(True)
        self.chips_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        v.addWidget(self.chips_area)
        self.list = QListWidget(); self.list.setMouseTracking(True); self.list.setUniformItemSizes(True)
        self.delegate = ChannelDelegate(self); self.list.setItemDelegate(self.delegate)
        self.list.itemClicked.connect(self._click)
        v.addWidget(self.list, 1)
        foot = QVBoxLayout(); foot.setContentsMargins(12, 10, 12, 12); foot.setSpacing(8)
        self.status = QLabel(); self.status.setObjectName("muted"); self.status.setWordWrap(True)
        self.note = QLabel(); self.note.setObjectName("note"); self.note.setWordWrap(True); self.note.hide()
        self.upd = QPushButton(); self.upd.setObjectName("primary"); self.upd.clicked.connect(lambda: app.action("tvUpdate"))
        acts = QHBoxLayout(); acts.setSpacing(6)
        self.imp = QPushButton("Import M3U…"); self.imp.clicked.connect(lambda: app.action("m3uFile"))
        self.more = QPushButton("Live TV settings"); self.more.clicked.connect(lambda: app.open_settings("tv"))
        acts.addWidget(self.imp, 1); acts.addWidget(self.more, 1)
        foot.addWidget(self.note); foot.addWidget(self.status); foot.addWidget(self.upd); foot.addLayout(acts)
        v.addLayout(foot)
        self._deb = QTimer(self); self._deb.setSingleShot(True); self._deb.setInterval(200); self._deb.timeout.connect(self.refresh_list)
        self.search.textChanged.connect(lambda _: self._deb.start())
        self.cat.currentIndexChanged.connect(lambda _: self.refresh_list())
        self._hover = QTimer(self); self._hover.setInterval(40); self._hover.timeout.connect(self.list.viewport().update); self._hover.start()
        self.retranslate()

    def retranslate(self):
        t = self.a.tr
        self.upd.setText(t("tvupdate"))
        self.rebuild()

    def toggle_fav(self, cid):
        fav = list(self.a.s["tvFav"])
        fav.remove(cid) if cid in fav else fav.append(cid)
        self.a.s.set("tvFav", fav, emit=False)
        self.rebuild_chips()
        self.list.viewport().update()

    def rebuild(self):
        chs = self.tv.channels
        cats = sorted({c.get("cat", "general") for c in chs})
        cur = self.cat.currentData()
        self.cat.blockSignals(True); self.cat.clear(); self.cat.addItem("All categories", "")
        for c in cats:
            self.cat.addItem(c[:1].upper() + c[1:], c)
        i = self.cat.findData(cur); self.cat.setCurrentIndex(max(0, i)); self.cat.blockSignals(False)
        self.rebuild_chips()
        self.refresh_list()

    def rebuild_chips(self):
        t, s = self.a.tr, self.a.s
        chs = self.tv.channels
        counts = {}
        for c in chs:
            if c.get("cc"):
                counts[c["cc"]] = counts.get(c["cc"], 0) + 1
        order = sorted(counts, key=lambda cc: (cc != "IN", -counts[cc]))
        w = QWidget(); w.setObjectName("page"); h = QHBoxLayout(w); h.setContentsMargins(10, 4, 10, 8); h.setSpacing(6)
        self.chips = []
        names = self.tv.data.get("countries") or {}
        for cid, cc, label, n in [("all", "", "🌐 " + t("all"), len(chs)), ("fav", "", "★ " + t("favorites"), len(s["tvFav"]))] + [(cc, cc, country_name(cc, names), counts[cc]) for cc in order]:
            b = FlagChip(self, cid, cc, label, n); b.setChecked(s["tvCountry"] == cid)
            b.clicked.connect(lambda _=False, cid=cid: self.pick(cid))
            h.addWidget(b); self.chips.append(b)
        h.addStretch(1)
        self.chips_area.setWidget(w)

    def pick(self, cid):
        self.a.s.set("tvCountry", cid, emit=False)
        for b in self.chips:
            b.setChecked(b.cid == cid)
        self.shown = 200
        self.refresh_list()

    def filtered(self):
        s = self.a.s
        q = self.search.text().strip().lower()
        cat = self.cat.currentData() or ""
        cc = s["tvCountry"]
        fav = set(s["tvFav"])
        out = []
        for c in self.tv.channels:
            if cc == "fav" and c["id"] not in fav: continue
            if cc not in ("all", "fav") and c.get("cc") != cc: continue
            if cat and c.get("cat") != cat: continue
            if q and q not in c.get("n", "").lower(): continue
            if s["tvHideDead"] and c["id"] in self.tv.dead: continue
            out.append(c)
        return out

    def refresh_list(self):
        self.view = self.filtered()
        self.list.setUpdatesEnabled(False)
        self.list.clear()
        for c in self.view[: self.shown]:
            it = QListWidgetItem(); it.setData(Qt.UserRole, c); it.setSizeHint(QSize(100, 48)); self.list.addItem(it)
        if len(self.view) > self.shown:
            it = QListWidgetItem(f"Show {min(500, len(self.view) - self.shown)} more"); it.setData(Qt.UserRole, None)
            self.list.addItem(it)
        if not self.view:
            it = QListWidgetItem("No favourites yet. Click ☆ beside a channel to add it." if self.a.s["tvCountry"] == "fav" else "No channels match.")
            it.setData(Qt.UserRole, None); it.setFlags(Qt.NoItemFlags); self.list.addItem(it)
        self.list.setUpdatesEnabled(True)
        self.update_status()

    def _click(self, it):
        if time.monotonic() - getattr(self, "_star_t", 0) < 0.4:
            return
        ch = it.data(Qt.UserRole)
        if ch:
            self.play.emit(ch)
        elif it.text().startswith("Show"):
            self.shown += 500
            self.refresh_list()

    def update_status(self):
        d = self.tv.data
        real = [c for c in self.tv.channels if not c.get("sample")]
        when = time.strftime("%d %b %Y, %H:%M", time.localtime(d["updated"])) if d.get("updated") else "never"
        self.status.setText("Updating channel list…" if self.tv.busy else f"{len(real)} channels · updated {when}")
        msg = self.tv.error or ("Showing sample channels. Click Update channels to download the free public list." if d.get("src") == "sample" else "")
        self.note.setText(msg); self.note.setVisible(bool(msg))
        self.upd.setEnabled(not self.tv.busy)

    def step(self, cur, d):
        lst = [c for c in self.view if not c.get("sample") and c["id"] not in self.tv.dead]
        if not lst:
            return None
        ids = [c["id"] for c in lst]
        i = ids.index(cur["id"]) if cur and cur["id"] in ids else -1
        return lst[(i + d) % len(lst)]
