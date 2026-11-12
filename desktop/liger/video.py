"""The stage: libmpv rendered into an OpenGL widget, with Qt-painted overlays (Tigu, OSD, stats, RGB corners)."""
import math
import time

import mpv
from PySide6.QtCore import QPointF, QRectF, Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QOpenGLContext, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QAbstractButton, QWidget

from .theme import DISPLAY, MONO, ICONS
from .tigu import Tigu


def chamfer(r: QRectF, c):
    p = QPainterPath()
    p.moveTo(r.left() + c, r.top()); p.lineTo(r.right(), r.top()); p.lineTo(r.right(), r.bottom() - c)
    p.lineTo(r.right() - c, r.bottom()); p.lineTo(r.left(), r.bottom()); p.lineTo(r.left(), r.top() + c); p.closeSubpath()
    return p


class VideoView(QOpenGLWidget):
    frame_ready = Signal()
    clicked = Signal()
    double_clicked = Signal()
    wheel = Signal(int)
    files_dropped = Signal(list)

    def __init__(self, app):
        super().__init__()
        self.a = app
        self.m: mpv.MPV = app.m
        self.ctx = None
        self.tok = app.tok
        self.tigu = Tigu(app.s)
        self.osd_text, self.osd_until = "", 0
        self.stats_text = ""
        self.now_text, self.live = "", False
        self.frame_ready.connect(self.update, Qt.QueuedConnection)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setMinimumSize(320, 180)

    # ---- mpv render API ----
    def initializeGL(self):
        def gpa(_ctx, name):
            c = QOpenGLContext.currentContext()
            if not c:
                return 0
            addr = c.getProcAddress(name.decode() if isinstance(name, bytes) else name)
            return int(addr) if addr else 0
        self._gpa = mpv.MpvGlGetProcAddressFn(gpa)
        self.ctx = mpv.MpvRenderContext(self.m, "opengl", opengl_init_params={"get_proc_address": self._gpa})
        self.ctx.update_cb = self.frame_ready.emit

    def free(self):
        if self.ctx:
            self.makeCurrent()
            self.ctx.free()
            self.ctx = None
            self.doneCurrent()

    def paintGL(self):
        dpr = self.devicePixelRatioF()
        w, h = int(self.width() * dpr), int(self.height() * dpr)
        has_video = self.a.is_video
        p = QPainter(self)
        if self.ctx and has_video:
            # Let mpv draw with raw OpenGL, then hand the context back to QPainter for the overlays.
            p.beginNativePainting()
            self.ctx.render(flip_y=True, opengl_fbo={"w": w, "h": h, "fbo": self.defaultFramebufferObject()})
            p.endNativePainting()
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        if not has_video:
            p.fillRect(r, QColor(self.tok["screen"]))
            self._idle_art(p, r)
        self._corners(p, r)
        self._tigu(p)
        self._labels(p, r)
        if self.a.show_big_play():
            self._big_play(p, r)
        p.end()

    # ---- overlays ----
    def _idle_art(self, p, r):
        a = self.a
        cx, cy = r.center().x(), r.center().y() - 18
        if a.has_media():
            f = QFont(DISPLAY); f.setPixelSize(22); f.setWeight(QFont.Bold)
            p.setFont(f); p.setPen(QColor(self.tok["ink"]))
            p.drawText(QRectF(r.left() + 40, cy + 70, r.width() - 80, 30), Qt.AlignCenter | Qt.TextSingleLine,
                       p.fontMetrics().elidedText(a.title(), Qt.ElideRight, int(r.width() - 80)))
            f2 = QFont(MONO); f2.setPixelSize(11); p.setFont(f2); p.setPen(QColor(self.tok["muted"]))
            p.drawText(QRectF(r.left(), cy + 100, r.width(), 20), Qt.AlignCenter, "LIVE AUDIO" if self.live else "AUDIO")
        else:
            f = QFont(MONO); f.setPixelSize(12); p.setFont(f); p.setPen(QColor(self.tok["muted"]))
            p.drawText(QRectF(r.left(), cy + 76, r.width(), 24), Qt.AlignCenter, a.tr("empty"))

    def _corners(self, p, r):
        a = self.a
        if "corners" in a.s["rgbZones"]:
            pen = QPen(a.lighting.brush(r, a.accent()), 2)
        else:
            pen = QPen(QColor(a.accent()), 2)
        pen.setCapStyle(Qt.SquareCap)
        p.setPen(pen)
        p.setOpacity(0.85)
        m, L = 12, 18
        for x, y, dx, dy in ((m, m, 1, 1), (r.width() - m, m, -1, 1), (m, r.height() - m, 1, -1), (r.width() - m, r.height() - m, -1, -1)):
            p.drawLine(QPointF(x, y), QPointF(x + dx * L, y)); p.drawLine(QPointF(x, y), QPointF(x, y + dy * L))
        p.setOpacity(1)

    def _tigu(self, p):
        a = self.a
        s = a.s
        if not s["tiguOn"] or (a.isFullScreen() and not s["tiguFs"]):
            return
        px = int(s["tiguSize"])
        sw, sh = max(1, self.width() // px), max(1, self.height() // px)
        self.tigu.update(a.playing(), a.has_media(), a.ended, a.is_video, sw, sh)
        p.save()
        p.setRenderHint(QPainter.Antialiasing, False)
        p.setRenderHint(QPainter.SmoothPixmapTransform, False)
        p.translate(0, self.height() - sh * px)
        p.scale(px, px)
        self.tigu.draw(p, self.tok["dark"])
        p.restore()

    def _labels(self, p, r):
        f = QFont(MONO); f.setPixelSize(11)
        p.setFont(f)
        y = 18
        if self.now_text:
            x = 20
            if self.live:
                w = 38
                p.fillRect(QRectF(x, y - 1, w, 17), QColor("#e5383b")); p.setPen(QColor("#ffffff"))
                p.drawText(QRectF(x, y - 1, w, 17), Qt.AlignCenter, "LIVE"); x += w + 8
            p.setPen(QColor("#ffffff") if self.a.is_video else QColor(self.tok["muted"]))
            p.drawText(QRectF(x, y - 1, r.width() * 0.6, 17), Qt.AlignVCenter | Qt.AlignLeft, p.fontMetrics().elidedText(self.now_text, Qt.ElideRight, int(r.width() * 0.6)))
        if self.stats_text:
            lines = self.stats_text.split("\n")
            box = QRectF(20, 44, 260, 16 * len(lines) + 14)
            p.fillRect(box, QColor(0, 0, 0, 150) if self.a.is_video else QColor(self.tok["panel"]))
            p.fillRect(QRectF(box.left(), box.top(), 2, box.height()), QColor(self.a.accent()))
            for i, ln in enumerate(lines):
                k, _, v = ln.partition("  ")
                p.setPen(QColor(self.a.accent())); p.drawText(QPointF(box.left() + 12, box.top() + 19 + i * 16), k)
                p.setPen(QColor("#ffffff") if self.a.is_video else QColor(self.tok["ink"])); p.drawText(QPointF(box.left() + 84, box.top() + 19 + i * 16), v.strip())
        if self.osd_text and time.monotonic() < self.osd_until:
            fo = QFont(DISPLAY); fo.setPixelSize(20); fo.setWeight(QFont.Bold); p.setFont(fo)
            w = p.fontMetrics().horizontalAdvance(self.osd_text) + 26
            box = QRectF(r.width() - w - 20, 16, w, 34)
            p.setPen(Qt.NoPen); p.setBrush(QColor(self.tok["panel"])); p.drawPath(chamfer(box, 8))
            p.setPen(QColor(self.a.accent())); p.drawText(box, Qt.AlignCenter, self.osd_text)

    def _big_play(self, p, r):
        box = QRectF(r.center().x() - 38, r.center().y() - 38, 76, 76)
        p.setPen(QPen(QColor(self.tok["line"]), 1)); p.setBrush(QColor(self.tok["panel"])); p.drawPath(chamfer(box, 14))
        tri = QPolygonF([QPointF(box.left() + 30, box.top() + 23), QPointF(box.left() + 54, box.center().y()), QPointF(box.left() + 30, box.bottom() - 23)])
        p.setPen(Qt.NoPen); p.setBrush(QColor(self.a.accent())); p.drawPolygon(tri)

    def osd(self, text, secs=1.1):
        if not self.a.s["osd"]:
            return
        self.osd_text, self.osd_until = text, time.monotonic() + secs
        self.update()

    # ---- input ----
    def _scene(self, e):
        px = int(self.a.s["tiguSize"])
        sh = max(1, self.height() // px)
        off = self.height() - sh * px
        return e.position().x() / px, (e.position().y() - off) / px

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            x, y = self._scene(e)
            if self.tigu.hit(x, y):
                self.tigu.react_to("purr")
                return
            self._press = time.monotonic()
            QTimer.singleShot(220, self._maybe_click)
        super().mousePressEvent(e)

    def _maybe_click(self):
        if getattr(self, "_press", 0) and time.monotonic() - self._press >= 0.2:
            self._press = 0
            self.clicked.emit()

    def mouseDoubleClickEvent(self, e):
        self._press = 0
        x, y = self._scene(e)
        if not self.tigu.hit(x, y):
            self.double_clicked.emit()

    def wheelEvent(self, e):
        self.wheel.emit(1 if e.angleDelta().y() > 0 else -1)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self.files_dropped.emit([u.toLocalFile() or u.toString() for u in e.mimeData().urls()])


class SeekBar(QWidget):
    seek = Signal(float)

    def __init__(self, app):
        super().__init__()
        self.a = app
        self.pos, self.dur, self.buf, self.live = 0.0, 0.0, 0.0, False
        self.ab = (None, None)
        self.hover_x = None
        self.setMouseTracking(True)
        self.setFixedHeight(24)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        t, a = self.a.tok, self.a
        w = self.width()
        track = QRectF(0, 10, w, 4)
        p.fillRect(track, QColor(t["line"]))
        frac = 1.0 if self.live else (self.pos / self.dur if self.dur else 0)
        if self.dur and not self.live:
            p.fillRect(QRectF(0, 10, w * min(1, self.buf / self.dur), 4), QColor(t["muted"]).lighter(160) if not t["dark"] else QColor("#3a4152"))
        A, B = self.ab
        if A is not None and self.dur:
            e = B if B is not None else self.pos
            p.fillRect(QRectF(w * A / self.dur, 6, max(2, w * (e - A) / self.dur), 12), QColor(a.accent()).lighter(170) if not t["dark"] else QColor(a.accent()).darker(250))
        fill = QRectF(0, 10, w * frac, 4)
        p.fillRect(fill, a.lighting.brush(QRectF(self.rect()), a.accent()) if "seek" in a.s["rgbZones"] else QColor(a.accent()))
        x = w * frac
        p.save(); p.translate(x, 12); p.rotate(45)
        p.setPen(QPen(QColor(a.accent()), 3)); p.setBrush(QColor(t["panel"])); p.drawRect(QRectF(-5, -5, 10, 10))
        p.restore()
        if self.hover_x is not None and self.dur and not self.live:
            t_at = self.hover_x / w * self.dur
            if self.a.live:
                behind = self.dur - t_at
                tt = "LIVE" if behind < 3 else "−" + fmt(behind)
            else:
                tt = fmt(t_at)
            f = QFont(MONO); f.setPixelSize(11); p.setFont(f)
            tw = p.fontMetrics().horizontalAdvance(tt) + 10
            bx = min(max(0, self.hover_x - tw / 2), w - tw)
            p.fillRect(QRectF(bx, -2, tw, 12), QColor(t["ink"])); p.setPen(QColor(t["panel"])); p.drawText(QRectF(bx, -2, tw, 12), Qt.AlignCenter, tt)
        p.end()

    def _emit(self, e):
        if self.dur and not self.live:
            self.seek.emit(max(0.0, min(1.0, e.position().x() / max(1, self.width()))) * self.dur)

    def mousePressEvent(self, e):
        self._emit(e)

    def mouseMoveEvent(self, e):
        self.hover_x = e.position().x()
        if e.buttons() & Qt.LeftButton:
            self._emit(e)
        self.update()

    def leaveEvent(self, _):
        self.hover_x = None
        self.update()


class LiveBadge(QAbstractButton):
    """Shown instead of the timers while a live channel plays.

    At the live edge it is a red tag with a pulsing dot and a radar ring.
    After a pause or rewind it turns into an outlined GO LIVE button that jumps back to the edge.
    """

    RED = "#e5383b"

    def __init__(self, app):
        super().__init__()
        self.a = app
        self.behind = False
        self.t0 = time.monotonic()
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(22)
        self._t = QTimer(self)
        self._t.setInterval(33)
        self._t.timeout.connect(self.update)
        self._resize()

    def set_behind(self, behind, secs=0.0):
        self.setToolTip(f"{fmt(secs)} behind live. Click to jump to the live edge." if behind else "Watching live")
        if behind != self.behind:
            self.behind = behind
            self._resize()
            self.update()

    def _font(self):
        f = QFont(DISPLAY)
        f.setPixelSize(11)
        f.setWeight(QFont.Bold)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 1.4)
        return f

    def _text(self):
        return "GO LIVE" if self.behind else "LIVE"

    def _resize(self):
        from PySide6.QtGui import QFontMetrics
        self.setFixedWidth(26 + QFontMetrics(self._font()).horizontalAdvance(self._text()) + 10)

    def showEvent(self, e):
        self._t.start()
        super().showEvent(e)

    def hideEvent(self, e):
        self._t.stop()
        super().hideEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        t = time.monotonic() - self.t0
        red = QColor(self.RED)
        path = chamfer(r, 5)
        cx, cy = 13.0, r.center().y()
        if self.behind:
            p.setPen(QPen(QColor(self.a.tok["muted"]) if not self.underMouse() else red, 1))
            p.setBrush(QColor(self.a.tok["panel"]))
            p.drawPath(path)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(self.a.tok["muted"]) if not self.underMouse() else red)
            p.drawEllipse(QPointF(cx, cy), 3.2, 3.2)
            ink = QColor(self.a.tok["ink"]) if not self.underMouse() else red
        else:
            p.setPen(Qt.NoPen)
            p.setBrush(red)
            p.drawPath(path)
            ph = (t % 1.6) / 1.6
            ring = QColor("#ffffff")
            ring.setAlphaF(max(0.0, 0.85 * (1 - ph)))
            p.setPen(QPen(ring, 1.4))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(cx, cy), 3.2 + 6.0 * ph, 3.2 + 6.0 * ph)
            beat = 0.55 + 0.45 * (0.5 + 0.5 * math.cos(t * math.tau / 1.6))
            dot = QColor("#ffffff")
            dot.setAlphaF(beat)
            p.setPen(Qt.NoPen)
            p.setBrush(dot)
            p.drawEllipse(QPointF(cx, cy), 3.2, 3.2)
            ink = QColor("#ffffff")
        p.setFont(self._font())
        p.setPen(ink)
        p.drawText(QRectF(24, 0, r.width() - 26, r.height()), Qt.AlignVCenter | Qt.AlignLeft, self._text())
        p.end()


class PlayButton(QAbstractButton):
    def __init__(self, app):
        super().__init__()
        self.a = app
        self.playing = False
        self.setFixedSize(48, 48)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        a = self.a
        br = a.lighting.brush(r, a.accent()) if "play" in a.s["rgbZones"] else QColor(a.accent())
        p.setPen(Qt.NoPen); p.setBrush(br); p.drawPath(chamfer(r, 10))
        if self.underMouse():
            p.setBrush(QColor(255, 255, 255, 40)); p.drawPath(chamfer(r, 10))
        p.setBrush(QColor("#ffffff"))
        if self.playing:
            p.drawRect(QRectF(16, 14, 5, 20)); p.drawRect(QRectF(27, 14, 5, 20))
        else:
            p.drawPolygon(QPolygonF([QPointF(18, 13), QPointF(35, 24), QPointF(18, 35)]))
        p.end()


class LogoMark(QWidget):
    def __init__(self, app):
        super().__init__()
        self.a = app
        self.setFixedSize(26, 26)

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        a = self.a
        br = a.lighting.brush(QRectF(self.rect()), a.accent()) if "logo" in a.s["rgbZones"] else QColor(a.accent())
        p.setPen(Qt.NoPen); p.setBrush(br)
        p.drawPolygon(QPolygonF([QPointF(0, 0), QPointF(26, 13), QPointF(0, 26)]))
        p.end()


class StageFrame(QWidget):
    """Holds the video and the control deck, and paints the RGB ring around them."""

    def __init__(self, app):
        super().__init__()
        self.a = app
        self.setObjectName("stage")

    def paintEvent(self, _):
        a = self.a
        p = QPainter(self)
        r = QRectF(self.rect()).adjusted(5, 5, -5, -5)
        if "ring" in a.s["rgbZones"] and not a.isFullScreen():
            br = a.lighting.brush(r, a.accent())
            p.setOpacity(0.5 if a.lighting.calm else 1.0)
            p.setPen(QPen(br, 2)); p.setBrush(Qt.NoBrush); p.drawRect(r)
            glow = a.s["glow"] / 100
            if glow > 0:
                for i, al in ((3, 0.35), (5, 0.18)):
                    p.setOpacity(glow * al * (0.4 if a.lighting.calm else 1))
                    p.setPen(QPen(br, 2)); p.drawRect(r.adjusted(-i, -i, i, i))
        else:
            p.setPen(QPen(QColor(a.tok["line"]), 1)); p.drawRect(r)
        p.end()


def fmt(s):
    try:
        s = int(abs(s))
    except Exception:
        return "0:00"
    h, m, x = s // 3600, (s % 3600) // 60, s % 60
    return f"{h}:{m:02d}:{x:02d}" if h else f"{m}:{x:02d}"
