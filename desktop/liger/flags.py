"""Country flags drawn as inline SVG, plus a painter that ripples them like cloth while hovered."""
import math
import time

from PySide6.QtCore import QByteArray, QLocale, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


def _h3(a, b, c): return f'<rect width="30" height="20" fill="{a}"/><rect y="6.67" width="30" height="6.67" fill="{b}"/><rect y="13.33" width="30" height="6.67" fill="{c}"/>'
def _v3(a, b, c): return f'<rect width="30" height="20" fill="{a}"/><rect x="10" width="10" height="20" fill="{b}"/><rect x="20" width="10" height="20" fill="{c}"/>'
def _h2(a, b): return f'<rect width="30" height="20" fill="{a}"/><rect y="10" width="30" height="10" fill="{b}"/>'


def _nord(bg, cr, inn=None):
    s = f'<rect width="30" height="20" fill="{bg}"/><rect x="8" width="5" height="20" fill="{cr}"/><rect y="7.5" width="30" height="5" fill="{cr}"/>'
    if inn:
        s += f'<rect x="9.25" width="2.5" height="20" fill="{inn}"/><rect y="8.75" width="30" height="2.5" fill="{inn}"/>'
    return s


def _star(cx, cy, r, f, rot=0):
    pts = []
    for i in range(10):
        a = math.radians(rot - 90 + i * 36)
        rr = r * 0.4 if i % 2 else r
        pts.append(f"{cx + math.cos(a) * rr:.2f},{cy + math.sin(a) * rr:.2f}")
    return f'<polygon points="{" ".join(pts)}" fill="{f}"/>'


def _stripes(n, a, b):
    return "".join(f'<rect y="{i * 20 / n:.2f}" width="30" height="{20 / n + .05:.2f}" fill="{b if i % 2 else a}"/>' for i in range(n))


_UJ = ('<rect width="30" height="20" fill="#012169"/><path d="M0 0L30 20M30 0L0 20" stroke="#fff" stroke-width="4"/>'
       '<path d="M0 0L30 20M30 0L0 20" stroke="#C8102E" stroke-width="1.4"/><path d="M15 0V20M0 10H30" stroke="#fff" stroke-width="6"/>'
       '<path d="M15 0V20M0 10H30" stroke="#C8102E" stroke-width="3.6"/>')


def _zig():
    p = "0,0 8,0"
    for i in range(9):
        p += f" 11,{i * 2.22 + 1.11:.2f} 8,{(i + 1) * 2.22:.2f}"
    return p + " 0,20"


F = {
    "IN": _h3("#FF9933", "#fff", "#138808") + '<circle cx="15" cy="10" r="2.6" fill="none" stroke="#000080" stroke-width=".7"/><circle cx="15" cy="10" r=".6" fill="#000080"/>',
    "US": _stripes(13, "#B22234", "#fff") + '<rect width="12" height="10.77" fill="#3C3B6E"/>' + "".join(f'<circle cx="{1.5 + (i % 4) * 3}" cy="{1.8 + (i // 4) * 3.4}" r=".55" fill="#fff"/>' for i in range(12)),
    "GB": _UJ, "FR": _v3("#0055A4", "#fff", "#EF4135"), "DE": _h3("#000", "#DD0000", "#FFCE00"), "IT": _v3("#009246", "#fff", "#CE2B37"),
    "ES": '<rect width="30" height="20" fill="#AA151B"/><rect y="5" width="30" height="10" fill="#F1BF00"/>', "RU": _h3("#fff", "#0039A6", "#D52B1E"),
    "JP": '<rect width="30" height="20" fill="#fff"/><circle cx="15" cy="10" r="6" fill="#BC002D"/>',
    "KR": '<rect width="30" height="20" fill="#fff"/><g transform="rotate(34 15 10)"><path d="M10 10a5 5 0 0 1 10 0z" fill="#CD2E3A"/><path d="M10 10a5 5 0 0 0 10 0z" fill="#0047A0"/></g>'
          + "".join(f'<rect x="{x - 2.5}" y="{y - 1.5}" width="5" height="3" fill="#000" transform="rotate({r} {x} {y})"/>' for x, y, r in ((5, 4, -34), (25, 4, 34), (5, 16, 34), (25, 16, -34))),
    "CN": '<rect width="30" height="20" fill="#EE1C25"/>' + _star(5, 5, 3, "#FFFF00") + _star(10, 2, 1, "#FFFF00") + _star(12, 4, 1, "#FFFF00") + _star(12, 7, 1, "#FFFF00") + _star(10, 9, 1, "#FFFF00"),
    "BR": '<rect width="30" height="20" fill="#009C3B"/><polygon points="15,2 28,10 15,18 2,10" fill="#FFDF00"/><circle cx="15" cy="10" r="4.2" fill="#002776"/>',
    "CA": '<rect width="30" height="20" fill="#fff"/><rect width="7.5" height="20" fill="#D80621"/><rect x="22.5" width="7.5" height="20" fill="#D80621"/><polygon points="15,4 16,7 18,6 17.5,9.5 20,8.5 19.5,10.5 21,11 16,14 15.6,16 14.4,16 14,14 9,11 10.5,10.5 10,8.5 12.5,9.5 12,6 14,7" fill="#D80621"/>',
    "AU": '<rect width="30" height="20" fill="#00247D"/><g transform="scale(.5)">' + _UJ + "</g>" + _star(7.5, 15, 2, "#fff") + _star(22, 4, 1, "#fff") + _star(25, 9, 1, "#fff") + _star(22, 16, 1.1, "#fff") + _star(19, 10, 1, "#fff"),
    "NP": '<polygon points="5,1 23,10 11,10 23,19 5,19" fill="#DC143C" stroke="#003893" stroke-width="1.2"/><circle cx="9" cy="7.5" r="1.4" fill="#fff"/><circle cx="9" cy="15" r="1.8" fill="#fff"/>',
    "BD": '<rect width="30" height="20" fill="#006A4E"/><circle cx="13.5" cy="10" r="5.5" fill="#F42A41"/>',
    "PK": '<rect width="30" height="20" fill="#01411C"/><rect width="7.5" height="20" fill="#fff"/><circle cx="19.5" cy="10" r="5" fill="#fff"/><circle cx="21" cy="8.8" r="4.3" fill="#01411C"/>' + _star(22.6, 8.3, 1.6, "#fff", 20),
    "AE": _h3("#00732F", "#fff", "#000") + '<rect width="7.5" height="20" fill="#FF0000"/>',
    "SA": '<rect width="30" height="20" fill="#006C35"/><rect x="8" y="6" width="14" height="3" rx="1" fill="#fff" opacity=".9"/><rect x="7" y="12" width="16" height="1" fill="#fff"/>',
    "TR": '<rect width="30" height="20" fill="#E30A17"/><circle cx="11" cy="10" r="5" fill="#fff"/><circle cx="12.3" cy="10" r="4" fill="#E30A17"/>' + _star(17.4, 10, 2.2, "#fff", -18),
    "ID": _h2("#CE1126", "#fff"),
    "TH": '<rect width="30" height="20" fill="#A51931"/><rect y="3.33" width="30" height="13.33" fill="#F4F5F8"/><rect y="6.67" width="30" height="6.67" fill="#2D2A4A"/>',
    "MX": _v3("#006847", "#fff", "#CE1126") + '<circle cx="15" cy="10" r="2" fill="#8B5A2B"/>', "AR": _h3("#74ACDF", "#fff", "#74ACDF") + '<circle cx="15" cy="10" r="1.8" fill="#F6B40E"/>',
    "NL": _h3("#AE1C28", "#fff", "#21468B"), "BE": _v3("#000", "#FDDA24", "#EF3340"), "SE": _nord("#006AA7", "#FECC00"), "NO": _nord("#BA0C2F", "#fff", "#00205B"),
    "DK": _nord("#C8102E", "#fff"), "FI": _nord("#fff", "#002F6C"), "UA": _h2("#0057B7", "#FFD700"), "PL": _h2("#fff", "#DC143C"),
    "EG": _h3("#CE1126", "#fff", "#000") + '<circle cx="15" cy="10" r="1.6" fill="#C09300"/>', "NG": _v3("#008751", "#fff", "#008751"),
    "ZA": '<rect width="30" height="20" fill="#fff"/><rect width="30" height="7" fill="#E03C31"/><rect y="13" width="30" height="7" fill="#001489"/><path d="M0 0L14 10H30M0 20L14 10" stroke="#fff" stroke-width="6" fill="none"/><path d="M0 0L14 10H30M0 20L14 10" stroke="#007749" stroke-width="3.6" fill="none"/><path d="M0 3L9.5 10L0 17Z" fill="#000" stroke="#FFB612" stroke-width="1.2"/>',
    "VN": '<rect width="30" height="20" fill="#DA251D"/>' + _star(15, 10, 5, "#FFFF00"),
    "PH": _h2("#0038A8", "#CE1126") + '<polygon points="0,0 17,10 0,20" fill="#fff"/><circle cx="5.5" cy="10" r="2" fill="#FCD116"/>',
    "MY": _stripes(14, "#CC0001", "#fff") + '<rect width="15" height="11.43" fill="#010066"/><circle cx="5.5" cy="5.7" r="3.5" fill="#FC0"/><circle cx="6.7" cy="5.7" r="2.9" fill="#010066"/>' + _star(10.6, 5.7, 1.8, "#FC0"),
    "SG": _h2("#EF3340", "#fff") + '<circle cx="6" cy="5" r="3.4" fill="#fff"/><circle cx="7.3" cy="5" r="3" fill="#EF3340"/><circle cx="9" cy="3.6" r=".5" fill="#fff"/><circle cx="10.4" cy="5" r=".5" fill="#fff"/><circle cx="9" cy="6.4" r=".5" fill="#fff"/>',
    "QA": f'<rect width="30" height="20" fill="#8A1538"/><polygon points="{_zig()}" fill="#fff"/>', "IE": _v3("#169B62", "#fff", "#FF883E"),
    "PT": '<rect width="30" height="20" fill="#FF0000"/><rect width="12" height="20" fill="#006600"/><circle cx="12" cy="10" r="3.5" fill="#FFFF00"/>',
    "CH": '<rect width="30" height="20" fill="#DA291C"/><rect x="13" y="4" width="4" height="12" fill="#fff"/><rect x="9" y="8" width="12" height="4" fill="#fff"/>',
    "AT": _h3("#C8102E", "#fff", "#C8102E"),
    "GR": _stripes(9, "#0D5EAF", "#fff") + '<rect width="11.1" height="11.1" fill="#0D5EAF"/><rect x="4.44" width="2.22" height="11.1" fill="#fff"/><rect y="4.44" width="11.1" height="2.22" fill="#fff"/>',
    "IL": '<rect width="30" height="20" fill="#fff"/><rect y="2" width="30" height="3" fill="#0038B8"/><rect y="15" width="30" height="3" fill="#0038B8"/><polygon points="15,6.3 18.2,11.8 11.8,11.8" fill="none" stroke="#0038B8" stroke-width=".8"/><polygon points="15,13.7 18.2,8.2 11.8,8.2" fill="none" stroke="#0038B8" stroke-width=".8"/>',
    "IR": _h3("#239F40", "#fff", "#DA0000"), "IQ": _h3("#CE1126", "#fff", "#000"),
    "KE": '<rect width="30" height="20" fill="#000"/><rect y="6" width="30" height="8" fill="#fff"/><rect y="7.2" width="30" height="5.6" fill="#BB0000"/><rect y="14" width="30" height="6" fill="#006600"/><ellipse cx="15" cy="10" rx="2.4" ry="5" fill="#BB0000" stroke="#000" stroke-width=".6"/>',
    "LK": '<rect width="30" height="20" fill="#FFBE29"/><rect x="1" y="1" width="3.5" height="18" fill="#00534E"/><rect x="4.5" y="1" width="3.5" height="18" fill="#EB7400"/><rect x="9" y="1" width="20" height="18" fill="#8D153A"/><circle cx="19" cy="10" r="3.5" fill="#FFBE29"/>',
    "BT": '<polygon points="0,0 30,0 0,20" fill="#FFD520"/><polygon points="30,0 30,20 0,20" fill="#FF4E12"/><circle cx="15" cy="10" r="3" fill="#fff"/>',
}

_cache = {}


def flag_pixmap(cc, w, h, dpr=2.0):
    cc = (cc or "").upper()
    key = (cc, w, h, dpr)
    if key in _cache:
        return _cache[key]
    px = QPixmap(int(w * dpr), int(h * dpr))
    px.setDevicePixelRatio(dpr)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    if cc in F:
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20" preserveAspectRatio="none">{F[cc]}</svg>'
        QSvgRenderer(QByteArray(svg.encode())).render(p, QRectF(0, 0, w, h))
    else:
        p.fillRect(QRectF(0, 0, w, h), QColor("#d5dae4"))
        f = QFont("JetBrains Mono")
        f.setPixelSize(max(7, int(h * 0.55)))
        p.setFont(f)
        p.setPen(QColor("#151821"))
        p.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, cc or "??")
    p.end()
    _cache[key] = px
    return px


def draw_flag(p: QPainter, x, y, cc, w=24, h=16, waving=False):
    """Draws a flag at (x, y). When waving, six vertical slices bob on a sine wave with matching light and shade."""
    px = flag_pixmap(cc, w, h)
    if not waving:
        p.drawPixmap(int(x), int(y), px)
        return
    t = time.monotonic()
    n = 6
    sw = w / n
    dpr = px.devicePixelRatio()
    for i in range(n):
        ph = t * 6.0 - i * 0.95
        dy = math.sin(ph) * 1.4
        src = QRectF(i * sw * dpr, 0, sw * dpr + 1, h * dpr)
        dst = QRectF(x + i * sw, y + dy, sw + 0.5, h * (1 - 0.03 * math.cos(ph)))
        p.drawPixmap(dst, px, src)
        shade = math.cos(ph)
        p.fillRect(dst, QColor(255, 255, 255, int(40 * shade)) if shade > 0 else QColor(0, 0, 0, int(-55 * shade)))


def country_name(cc, names=None):
    cc = (cc or "").upper()
    if names and cc in names:
        return names[cc]
    try:
        terr = QLocale.codeToTerritory(cc)
        name = QLocale.territoryToString(terr)
        if name and terr.value != 0:
            return name
    except Exception:
        pass
    return cc or "—"
