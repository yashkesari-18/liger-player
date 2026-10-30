"""Tigu, the 16-bit tiger cub. The sprite is drawn procedurally into a 44x32 pixel grid and outlined automatically."""
import math
import random
import time

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter

COL = {"O": "#2b1810", "B": "#f28a2e", "S": "#c8621f", "L": "#ffc27a", "C": "#fff1dc", "K": "#2d1a12", "P": "#e8728a", "E": "#141414", "W": "#ffffff"}
QCOL = {k: QColor(v) for k, v in COL.items()}
GW, GH = 44, 32
GLYPHS = {
    "!": ["..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "..##.", ".....", "..#.."],
    "z": ["#####", "...#.", "..#..", ".#...", "#####"],
    "heart": [".#.#.", "#####", "#####", ".###.", "..#.."],
    "star": ["..#..", "#.#.#", ".###.", "#.#.#", "..#.."],
    "dots": [".....", ".....", ".....", ".....", "#.#.#"],
}


def tiger_grid(o):
    g = [[0] * GW for _ in range(GH)]

    def put(x, y, c):
        x, y = round(x), round(y)
        if 0 <= x < GW and 0 <= y < GH:
            g[y][x] = c

    def ell(cx, cy, rx, ry, c):
        for y in range(math.floor(cy - ry), math.ceil(cy + ry) + 1):
            for x in range(math.floor(cx - rx), math.ceil(cx + rx) + 1):
                dx, dy = (x - cx) / rx, (y - cy) / ry
                if dx * dx + dy * dy <= 1:
                    put(x, y, c)

    def rect(x, y, w, h, c):
        for j in range(h):
            for i in range(w):
                put(x + i, y + j, c)

    lie = o.get("lie")
    ground = GH - 1
    c = 0 if lie else min(4, round(o.get("crouch", 0)))
    leg_h = 1 if lie else 6 - c
    cy = ground - 4 if lie else ground - leg_h - 3
    cx = 19
    f = int(o.get("walk", 0))
    bx, by = cx - 9, cy - 2
    curl = o.get("curl", 1)
    for i in range(10):
        x = bx - i * 0.85
        y = by - (i * i) / 14 * curl + math.sin(o.get("tail", 0) + i * 0.5) * i * 0.18
        col = "K" if (i >= 8 or i % 3 == 2) else "B"
        put(x, y, col)
        put(x, y + 1, col)
    if not lie:
        for lx, up in ((14, f == 1), (27, f == 3)):
            l = 1 if up else 0
            rect(lx + l, ground - leg_h + 1 - l, 3, leg_h, "S")
            rect(lx + l, ground - l, 3, 1, "C")
    ell(cx, cy, 10, 5, "B")
    for y in range(cy + 3, cy + 6):
        for x in range(cx - 7, cx + 8):
            if 0 <= y < GH and g[y][x] == "B":
                g[y][x] = "C"
    if not lie:
        for lx, up in ((10, f == 3), (23, f == 1)):
            l = 1 if up else 0
            rect(lx - l, ground - leg_h + 1 - l, 3, leg_h, "B")
            rect(lx - l, ground - l, 3, 1, "C")
    else:
        rect(cx + 8, ground - 1, 7, 2, "C")
        rect(cx - 9, ground - 1, 4, 2, "B")
    for sx in (12, 15, 18, 21, 24):
        for y in range(cy - 5, cy - 1):
            x = sx + (1 if y < cy - 3 else 0)
            if 0 <= y < GH and g[y][x] == "B":
                g[y][x] = "K"
    hx = 31 + (1 if lie else 0)
    hy = cy - 5 + (3 if o.get("sniff") else 0) + (2 if lie else 0)
    flat = o.get("flat")
    ey = hy - 6 + (2 if flat else 0)

    def ear(x, y):
        put(x, y, "B")
        rect(x - 1, y + 1, 3, 2, "B")
        put(x, y + 1, "P")

    ear(hx - 4 - (1 if flat else 0), ey)
    ear(hx + 3 + (1 if flat else 0), ey + (1 if o.get("ear") else 0))
    ell(hx, hy, 7, 6, "B")
    ell(hx + 4, hy + 2.5, 3, 2, "C")
    ell(hx - 2, hy + 3, 2, 1.5, "C")
    for x, y in ((hx - 1, hy - 5), (hx - 1, hy - 4), (hx + 1, hy - 5), (hx + 1, hy - 4), (hx - 6, hy), (hx - 5, hy), (hx - 6, hy + 2), (hx - 5, hy + 2)):
        put(x, y, "K")
    ex, eY = hx + 2, hy - 1
    if o.get("happy"):
        put(ex, eY + 1, "E"); put(ex + 1, eY, "E"); put(ex + 2, eY + 1, "E")
    elif o.get("closed") or o.get("blink"):
        put(ex, eY + 1, "E"); put(ex + 1, eY + 1, "E")
    else:
        rect(ex, eY, 2, 2, "E"); put(ex, eY, "W")
    put(hx + 7, hy + 1, "P"); put(hx + 6, hy + 1, "P"); put(hx + 6, hy + 3, "K")
    if o.get("yawn"):
        rect(hx + 4, hy + 3, 3, 2, "K"); put(hx + 5, hy + 4, "P")
    if o.get("lick"):
        rect(hx + 3, hy + 5, 3, 3, "C")
    if o.get("paws"):
        rect(hx + 1, hy - 7, 3, 3, "C")
    for x in range(GW):
        for y in range(GH):
            if g[y][x]:
                if g[y][x] == "B":
                    g[y][x] = "L"
                break
    out = [row[:] for row in g]
    for y in range(GH):
        for x in range(GW):
            if not g[y][x]:
                n = (y > 0 and g[y - 1][x]) or (y < GH - 1 and g[y + 1][x]) or (x > 0 and g[y][x - 1]) or (x < GW - 1 and g[y][x + 1])
                if n:
                    out[y][x] = "O"
    return out


class Tigu:
    """State machine: idle → hiding → hidden → peek → emerge → idle; idle → roam → nap; roam/nap → wake → return → idle."""

    def __init__(self, settings):
        self.s = settings
        now = time.monotonic()
        self.st = "idle"; self.x = -1.0; self.dir = -1; self.y_off = 0.0; self.t0 = now; self.tx = 0.0; self.walk = 0.0
        self.blink_until = 0; self.next_blink = now + 2; self.act = None; self.act_until = 0; self.next_act = now + 6
        self.bubble = None; self.bubble_until = 0; self.fly = None; self.leaves = []; self.zs = []; self.next_z = 0
        self.poke_until = 0; self.rustle = 0.0; self.jump = 0.0; self.grass = 1.0; self.react = None; self.react_until = 0
        self.paused_at = 0; self.last = now; self.last_input = now; self.sw = 0; self.sh = 0
        self._key = None; self._img = None

    # --- helpers -------------------------------------------------------
    def home(self):
        return self.sw - GW - round(self.sw * 0.05)

    def go(self, st, now):
        self.st, self.t0 = st, now

    def walk_to(self, x, speed, dt, o, run=False):
        dx = x - self.x
        if abs(dx) < 1:
            self.x = x
            return True
        self.dir = 1 if dx > 0 else -1
        self.x += self.dir * min(abs(dx), speed * dt)
        self.walk = (self.walk + dt * (22 if run else 11)) % 4
        o["walk"] = int(self.walk)
        return False

    def say(self, glyph, secs, now):
        self.bubble, self.bubble_until = glyph, now + secs

    def poke(self):
        self.last_input = time.monotonic()

    def react_to(self, kind):
        if not self.s["tiguOn"] or not self.s["tiguReact"] or self.st in ("hidden", "hiding", "peek"):
            return
        now = time.monotonic()
        self.react, self.react_until = kind, now + (0.7 if kind == "pounce" else 1.6)
        self.say({"purr": "heart", "loud": "!", "shot": "star", "huh": "?", "pounce": "!", "mute": "dots"}.get(kind, "!"), 1.5, now)

    def roam_now(self):
        self.last_input = time.monotonic() - 3600
        self.st = "idle"
        self.y_off = 0.0

    def hit(self, x, y):
        """x, y in scene pixels."""
        if not self.s["tiguOn"] or self.st in ("hidden", "hiding"):
            return False
        Y = self.sh - GH + self.y_off - self.jump
        return self.x + 4 <= x <= self.x + GW - 2 and Y + 6 <= y <= self.sh

    # --- update --------------------------------------------------------
    def update(self, playing, has_media, ended, is_video, sw, sh):
        now = time.monotonic()
        dt = min(0.1, now - self.last)
        self.last = now
        if (sw, sh) != (self.sw, self.sh):
            self.sw, self.sh = sw, sh
            self.x = -1
        if self.x < 0 or self.x > sw:
            self.x = float(self.home())
        idle = now - self.last_input
        roam = float("inf") if self.s["tiguRoam"] == "never" else float(self.s["tiguRoam"]) * 60
        o = {"walk": 0, "tail": now / 0.42, "crouch": 0}
        if now > self.next_blink:
            self.blink_until = now + 0.15
            self.next_blink = now + 2.5 + random.random() * 3.5
        o["blink"] = now < self.blink_until
        st = self.st
        if st == "idle":
            self.y_off = 0.0
            if playing:
                self.go("hiding", now)
            else:
                if abs(self.x - self.home()) > 1:
                    self.walk_to(self.home(), 24, dt, o)
                else:
                    self.dir = -1
                if idle > roam:
                    self.go("roam", now); self.act = None; self.tx = 8 + random.random() * max(1, sw - GW - 16)
                if now > self.next_act:
                    r = random.random()
                    self.act = "lick" if r < 0.4 else "yawn" if r < 0.7 else "ear"
                    self.act_until = now + {"lick": 1.6, "yawn": 1.3, "ear": 0.45}[self.act]
                    self.next_act = now + 8 + random.random() * 9
                if self.act and now < self.act_until and self.st == "idle":
                    if self.act == "lick": o["lick"] = int(now / 0.25) % 2
                    if self.act == "yawn": o["yawn"] = 1; o["closed"] = 1
                    if self.act == "ear": o["ear"] = 1
                o["curl"] = 1 + math.sin(now / 1.3) * 0.3
        elif st == "hiding":
            p = (now - self.t0) / 0.7
            o["crouch"] = min(4, p * 8)
            self.y_off = 0 if p < 0.4 else min(1, (p - 0.4) / 0.6) * 16
            self.rustle = 1
            if p >= 1: self.go("hidden", now)
        elif st == "hidden":
            self.y_off = 16; o["crouch"] = 4
            if not playing:
                if not self.paused_at: self.paused_at = now
                if now - self.paused_at > (5 if has_media and not ended else 1.5):
                    self.paused_at = 0; self.go("peek", now)
            else:
                self.paused_at = 0
            if not self.poke_until and random.random() < dt / 9: self.poke_until = now + 1.8
            if self.poke_until and now > self.poke_until: self.poke_until = 0
        elif st == "peek":
            p = now - self.t0
            self.y_off = 16 - 11 * (p / 0.3) if p < 0.3 else 5
            self.dir = -1 if p < 0.9 else 1 if p < 1.7 else -1
            if playing: self.go("hiding", now)
            elif p > 2.6:
                self.go("emerge", now)
                for _ in range(7):
                    self.leaves.append([self.x + GW / 2, sh - 8, (random.random() - 0.5) * 40, -20 - random.random() * 30, 0.9])
        elif st == "emerge":
            p = (now - self.t0) / 0.6
            self.y_off = max(0, 5 * (1 - p)); self.jump = math.sin(min(1, p) * math.pi) * 7
            if p >= 1: self.y_off = 0; self.jump = 0; self.go("idle", now)
        elif st == "roam":
            if playing: self.go("hiding", now)
            elif idle < 1: self.go("wake", now); self.say("!", 0.8, now)
            elif idle > 600 and self.s["tiguNap"] and not self.act: self.go("nap", now)
            elif self.act:
                if now > self.act_until:
                    if self.act == "chase": self.jump = 0; self.fly = None
                    self.act = None; self.tx = 8 + random.random() * max(1, sw - GW - 16)
                elif self.act == "sit": o["crouch"] = 2; o["curl"] = 1.6
                elif self.act == "sniff": o["sniff"] = 1; o["tail"] = now / 0.25
                elif self.act == "look": self.dir = 1 if math.sin((now - self.t0) / 0.6) > 0 else -1
                elif self.act == "chase" and self.fly:
                    f = self.fly
                    f[2] += dt / 0.7
                    f[0] = min(max(f[0] + math.cos(f[2]) * dt * 30 + f[3] * dt, 4), sw - 6)
                    f[1] = sh - 24 + math.sin(f[2] * 1.7) * 7
                    tx = f[0] - (GW - 8 if self.dir > 0 else 8)
                    self.walk_to(min(max(tx, 0), sw - GW), 30, dt, o, True)
                    left = self.act_until - now
                    self.jump = math.sin((0.6 - left) / 0.6 * math.pi) * 9 if left < 0.6 else 0
                    if left < 0.6: o["paws"] = 1
            elif self.walk_to(self.tx, 16, dt, o):
                self.act = random.choice(["sit", "sniff", "look", "chase", "sit", "look"])
                self.act_until = now + (4.2 if self.act == "chase" else 2.2 + random.random() * 2.5)
                self.t0 = now
                if self.act == "chase":
                    self.fly = [self.x + (GW + 6 if self.dir > 0 else -6), sh - 24, 0.0, random.choice((-14, 14))]
        elif st == "nap":
            o.update(lie=1, closed=1, curl=0.4, tail=now / 1.4)
            if playing: self.go("hiding", now)
            elif idle < 1: self.go("wake", now); self.say("!", 0.8, now)
            elif now > self.next_z:
                self.zs.append([self.x + (34 if self.dir > 0 else 8), sh - 22, now]); self.next_z = now + 1.4
        elif st == "wake":
            p = now - self.t0
            self.jump = math.sin(p / 0.5 * math.pi) * 7 if p < 0.5 else 0
            o["flat"] = p < 0.3
            if p > 0.55: self.jump = 0; self.go("return", now)
        elif st == "return":
            if playing: self.go("hiding", now)
            elif self.walk_to(self.home(), 48, dt, o, True): self.go("idle", now)
        if self.react and now < self.react_until:
            k = self.react
            if k == "purr": o["happy"] = 1; o["tail"] = now / 0.15
            if k == "loud": o["flat"] = 1; o["paws"] = 1
            if k == "shot": o["happy"] = 1
            if k == "huh": o["ear"] = 1
            if k == "pounce":
                q = 1 - (self.react_until - now) / 0.7
                self.jump = math.sin(q * math.pi) * 10; o["crouch"] = 3 if q < 0.2 else 0
        elif self.react:
            self.react = None
            if self.st not in ("wake", "emerge"): self.jump = 0
        want = 0.0 if (is_video and playing and self.st in ("hidden", "hiding") and not self.s["tiguGrassVideo"]) else 1.0
        self.grass += (want - self.grass) * min(1, dt / 0.4)
        self.rustle = max(0.0, self.rustle - dt / 1.2)
        self._sprite(o)
        self.leaves = [l for l in self.leaves if l[4] > 0]
        for l in self.leaves:
            l[4] -= dt; l[3] += dt * 80; l[0] += l[2] * dt; l[1] += l[3] * dt
        self.zs = [z for z in self.zs if now - z[2] < 2.2]

    def _sprite(self, o):
        key = tuple(sorted((k, round(v, 1) if isinstance(v, float) else v) for k, v in o.items()))
        if key == self._key:
            return
        self._key = key
        g = tiger_grid(o)
        img = QImage(GW, GH, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        for y in range(GH):
            for x in range(GW):
                c = g[y][x]
                if c:
                    img.setPixelColor(x, y, QCOL[c])
        self._img = img

    # --- draw (scene coordinates are low-res pixels; caller scales the painter) -----
    def draw(self, p: QPainter, dark):
        if self._img is None:
            return
        now = time.monotonic()
        sw, sh = self.sw, self.sh
        X = round(self.x)
        Y = sh - GH + round(self.y_off - self.jump)
        if self.st != "hidden":
            img = self._img.mirrored(True, False) if self.dir < 0 else self._img
            p.drawImage(X, Y, img)
        if self.fly and self.st == "roam":
            glow = math.sin(now / 0.12) > 0
            p.fillRect(round(self.fly[0]), round(self.fly[1]), 2, 2, QColor("#fff7a8" if glow else "#ffd84a"))
        for l in self.leaves:
            p.fillRect(round(l[0]), round(l[1]), 1, 1, QColor("#4cb84a" if int(l[4] * 10) % 3 else "#86d65a"))
        if self.grass > 0.02:
            p.setOpacity(self.grass)
            self._grass(p, now, X)
            if self.st == "hidden" and self.poke_until:
                q = 1 - (self.poke_until - now) / 1.8
                hgt = round(math.sin(q * math.pi) * 6)
                tx = X + GW - 10 if self.dir < 0 else X + 8
                for i in range(hgt):
                    xx = tx + round(math.sin(now / 0.2 + i * 0.6) * (i / 3))
                    p.fillRect(xx - 1, sh - 8 - i, 4, 1, QCOL["O"])
                    p.fillRect(xx, sh - 8 - i, 2, 1, QCOL["K"] if (i >= hgt - 2 or i % 3 == 1) else QCOL["B"])
            p.setOpacity(1)
        for z in self.zs:
            q = (now - z[2]) / 2.2
            p.setOpacity(1 - q)
            self._glyph(p, "z", z[0] + math.sin(q * 6) * 2, z[1] - q * 14, QColor("#cfd6e6" if dark else "#4b5468"))
            p.setOpacity(1)
        if self.bubble and now < self.bubble_until and self.st != "hidden":
            hx = X + 31 if self.dir > 0 else X + GW - 32
            by = Y + 2
            p.fillRect(hx - 5, by - 10, 11, 9, QCOL["O"]); p.fillRect(hx - 4, by - 9, 9, 7, QColor("#ffffff"))
            p.fillRect(hx - 1, by - 1, 3, 1, QCOL["O"]); p.fillRect(hx, by - 2, 1, 1, QColor("#ffffff"))
            self._glyph(p, self.bubble, hx - 2, by - 8, QColor("#e5383b" if self.bubble == "heart" else "#1b1b1b"))

    def _glyph(self, p, k, x, y, col):
        for j, row in enumerate(GLYPHS.get(k, [])):
            for i, ch in enumerate(row):
                if ch == "#":
                    p.fillRect(round(x) + i, round(y) + j, 1, 1, col)

    def _grass(self, p, now, X):
        sw, sh = self.sw, self.sh
        base = sh - 3
        p.fillRect(0, base, sw, 3, QColor("#1f6b2c"))
        c1, c2, t1, t2 = QColor("#2f8f3a"), QColor("#3fa544"), QColor("#4cb84a"), QColor("#86d65a")
        fl1, fl2 = QColor("#ffd84a"), QColor("#ff8fb1")
        for x in range(sw):
            hsh = (x * 73 + 11) % 17
            h = 3 + hsh % 6
            near = self.rustle * 2.5 if abs(x - (X + GW / 2)) < GW * 0.7 else 0
            sway = round(math.sin(now / 0.7 + x * 0.35) * (0.7 + near))
            p.fillRect(x, base - h + 2, 1, h - 2, c1 if hsh % 3 else c2)
            p.fillRect(x + sway, base - h, 1, 2, t1 if hsh % 4 else t2)
            if hsh == 5:
                p.fillRect(x + sway, base - h - 1, 1, 1, fl1 if x % 2 else fl2)
