"""RGB lighting: palettes and animated brushes (wave, rotate, ripple, breathing, spectrum, solid)."""
import math
import time

from PySide6.QtCore import QPointF
from PySide6.QtGui import QBrush, QColor, QConicalGradient, QGradient, QLinearGradient, QRadialGradient

PALETTES = {
    "rainbow": ["#ff3b3b", "#ffb020", "#f5e43b", "#2ee66b", "#2fd3ff", "#3b6bff", "#b23bff"],
    "cyber": ["#00f0ff", "#7a5cff", "#ff2fd6"],
    "ember": ["#ff3d00", "#ff9100", "#ffd000"],
    "ocean": ["#00c2ff", "#0066ff", "#00e0b8"],
    "tiranga": ["#ff9933", "#ffffff", "#138808", "#000080"],
    "aurora": ["#14f195", "#00c2ff", "#9945ff"],
}
PALETTE_NAMES = {"rainbow": "Rainbow", "cyber": "Cyber", "ember": "Ember", "ocean": "Ocean", "tiranga": "Tiranga", "aurora": "Aurora", "mono": "Mono (accent)", "custom": "Custom"}
DIRS = {"e": (1, 0), "w": (-1, 0), "s": (0, 1), "n": (0, -1), "ne": (0.707, -0.707), "nw": (-0.707, -0.707), "se": (0.707, 0.707), "sw": (-0.707, 0.707)}


def tune(hex_color, bright, sat):
    c = QColor(hex_color)
    h, s, l, _ = c.getHslF()
    out = QColor()
    out.setHslF(max(0.0, h), min(1.0, s * sat), min(0.97, l * bright))
    return out


class Lighting:
    """Holds the current effect settings and produces a brush for any rectangle at the current time."""

    def __init__(self, settings):
        self.s = settings
        self.start = time.monotonic()
        self.calm = False
        self.frozen_phase = 0.0

    def restart(self):
        self.start = time.monotonic()

    def colors(self):
        s = self.s
        pal = s["rgbPal"]
        if pal == "custom":
            base = s["rgbCustom"]
        elif pal == "mono":
            a = QColor(s["accent"])
            base = [s["accent"], QColor(a.red() + (255 - a.red()) * 0.6, a.green() + (255 - a.green()) * 0.6, a.blue() + (255 - a.blue()) * 0.6).name()]
        else:
            base = PALETTES[pal]
        return [tune(c, s["rgbBright"] / 100, s["rgbSat"] / 100) for c in base]

    def animating(self):
        return self.s["rgbMotion"] != "static" and self.s["rgbFx"] != "solid" and not self.calm

    def phase(self):
        """0..1 position in the cycle. Static motion freezes it; Play once stops after one cycle; calm pauses it."""
        s = self.s
        if s["rgbMotion"] == "static":
            return 0.0
        if self.calm:
            return self.frozen_phase
        e = (time.monotonic() - self.start) / max(0.5, s["rgbSpeed"])
        if s["rgbMotion"] == "once" and e >= 1:
            e = 1.0
        self.frozen_phase = e % 1.0
        return self.frozen_phase

    def _stops(self, grad, cols, phase):
        n = len(cols)
        steps = 6 * n
        for j in range(steps + 1):
            x = (j / steps - phase) % 1.0
            f = x * n
            i = int(f) % n
            k = f - int(f)
            a, b = cols[i], cols[(i + 1) % n]
            grad.setColorAt(j / steps, QColor(round(a.red() + (b.red() - a.red()) * k), round(a.green() + (b.green() - a.green()) * k), round(a.blue() + (b.blue() - a.blue()) * k)))

    def brush(self, rect, accent):
        s = self.s
        fx = s["rgbFx"]
        dim = 0.55 if self.calm else 1.0
        if fx == "solid":
            return QBrush(QColor(accent))
        cols = self.colors()
        ph = self.phase()
        if fx == "spectrum":
            c = QColor(accent)
            h, sa, l, _ = c.getHslF()
            out = QColor()
            out.setHslF((max(0.0, h) + ph) % 1.0, min(1.0, 0.85 * s["rgbSat"] / 100), min(0.9, 0.55 * s["rgbBright"] / 100 * dim))
            return QBrush(out)
        d = s["rgbDir"]
        rev = d in ("w", "n", "nw", "sw")
        if fx == "wave":
            dx, dy = DIRS.get(d, (1, 0))
            if rev:
                dx, dy = -dx, -dy
            period = 480.0
            g = QLinearGradient(QPointF(rect.left(), rect.top()), QPointF(rect.left() + abs(dx) * period, rect.top() + abs(dy) * period))
            g.setSpread(QGradient.RepeatSpread)
            self._stops(g, cols, ph if (dx + dy) >= 0 else -ph)
        elif fx == "rotate":
            g = QConicalGradient(rect.center(), (-1 if rev else 1) * ph * 360)
            self._stops(g, cols, 0)
        elif fx == "ripple":
            g = QRadialGradient(QPointF(rect.left() + rect.width() * 0.12, rect.bottom()), 480.0)
            g.setSpread(QGradient.RepeatSpread)
            self._stops(g, cols, -ph if rev else ph)
        else:  # breath
            g = QLinearGradient(QPointF(rect.left(), rect.top()), QPointF(rect.right(), rect.top()))
            k = 0.55 + 0.45 * (0.5 - 0.5 * math.cos(ph * 2 * math.pi))
            cols = [QColor(round(c.red() * k), round(c.green() * k), round(c.blue() * k)) for c in cols]
            for i, c in enumerate(cols):
                g.setColorAt(i / max(1, len(cols) - 1), c)
        if self.calm:
            for i in range(len(g.stops())):
                pass
        return QBrush(g)
