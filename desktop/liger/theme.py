"""Colour tokens, fonts, icons and the Qt stylesheet for Liger Player."""
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QFontDatabase, QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

ASSETS = Path(__file__).resolve().parent / "assets"

LIGHT = dict(paper="#f6f7fa", panel="#ffffff", ink="#151821", muted="#687085", line="#e2e5ed", screen="#eceff5", soft="#eef2fb")
DARK = dict(paper="#0c0e13", panel="#14171f", ink="#e7eaf1", muted="#8b93a7", line="#252a36", screen="#0f1218", soft="#18203a")

DISPLAY = "Chakra Petch"
BODY = "Manrope"
MONO = "JetBrains Mono"


def load_fonts():
    for f in (ASSETS / "fonts").glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(f))


def system_is_dark():
    try:
        return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        return False


def tokens(theme):
    dark = theme == "dark" or (theme == "system" and system_is_dark())
    t = dict(DARK if dark else LIGHT)
    t["dark"] = dark
    return t


def ink_on(hex_color):
    c = QColor(hex_color)
    return "#111111" if (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) > 165 else "#ffffff"


def mix(a, b, k):
    a, b = QColor(a), QColor(b)
    return QColor(round(a.red() + (b.red() - a.red()) * k), round(a.green() + (b.green() - a.green()) * k), round(a.blue() + (b.blue() - a.blue()) * k)).name()


ICONS = {
    "prev": "M6 5h2v14H6zM20 5v14L9 12z",
    "back": "M11 6v12L3 12zM21 6v12l-8-6z",
    "play": "M7 4l13 8-13 8z",
    "pause": "M6 4h4v16H6zM14 4h4v16h-4z",
    "fwd": "M3 6v12l8-6zM13 6v12l8-6z",
    "next": "M16 5h2v14h-2zM4 5v14l11-7z",
    "loop": "M7 7h10v3l4-4-4-4v3H5v6h2zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2z",
    "shuffle": "M10.6 9.2L5.4 4 4 5.4l5.2 5.2zM14.5 4l2 2L4 18.6 5.4 20 18 7.5l2 2V4zm.3 9.4l-1.4 1.4 3.1 3.1-2 2H20v-5.5l-2 2z",
    "volume": "M3 9v6h4l5 5V4L7 9zm13.5 3A4.5 4.5 0 0014 8v8a4.5 4.5 0 002.5-4zM14 3.2v2.1a7 7 0 010 13.4v2.1a9 9 0 000-17.6z",
    "mute": "M3 9v6h4l5 5V4L7 9zm16.6 3l2.1-2.1-1.4-1.4-2.1 2.1-2.1-2.1-1.4 1.4 2.1 2.1-2.1 2.1 1.4 1.4 2.1-2.1 2.1 2.1 1.4-1.4z",
    "cc": "M19 4H5a2 2 0 00-2 2v12a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2zM11 11H9.5v-.5h-2v3h2V13H11v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-4a1 1 0 011-1h3a1 1 0 011 1zm7 0h-1.5v-.5h-2v3h2V13H18v1a1 1 0 01-1 1h-3a1 1 0 01-1-1v-4a1 1 0 011-1h3a1 1 0 011 1z",
    "shot": "M9 3L7.2 5H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V7a2 2 0 00-2-2h-3.2L15 3zm3 15a5 5 0 110-10 5 5 0 010 10zm0-2a3 3 0 100-6 3 3 0 000 6z",
    "full": "M7 14H5v5h5v-2H7zm-2-4h2V7h3V5H5zm12 7h-3v2h5v-5h-2zM14 5v2h3v3h2V5z",
    "close": "M6.4 5L5 6.4 10.6 12 5 17.6 6.4 19l5.6-5.6 5.6 5.6 1.4-1.4-5.6-5.6L19 6.4 17.6 5 12 10.6z",
    "tv": "M21 3H3a2 2 0 00-2 2v12a2 2 0 002 2h5v2h8v-2h5a2 2 0 002-2V5a2 2 0 00-2-2zm0 14H3V5h18z",
    "gear": "M19.4 13a7.6 7.6 0 000-2l2.1-1.6-2-3.5-2.5 1a7.4 7.4 0 00-1.7-1L15 3h-4l-.4 2.9a7.4 7.4 0 00-1.7 1l-2.5-1-2 3.5L6.6 11a7.6 7.6 0 000 2l-2.1 1.6 2 3.5 2.5-1a7.4 7.4 0 001.7 1L11 21h4l.4-2.9a7.4 7.4 0 001.7-1l2.5 1 2-3.5zM13 15.5a3.5 3.5 0 110-7 3.5 3.5 0 010 7z",
}


def icon(name, color, size=20):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="{ICONS[name]}"/></svg>'
    r = QSvgRenderer(QByteArray(svg.encode()))
    px = QPixmap(QSize(size * 2, size * 2))
    px.fill(Qt.transparent)
    p = QPainter(px)
    r.render(p)
    p.end()
    return QIcon(px)


def app_icon():
    ico = ASSETS / "icon.ico"
    return QIcon(str(ico)) if ico.exists() else QIcon(str(ASSETS / "icon.png"))


def stylesheet(t, accent):
    ai = ink_on(accent)
    soft = mix(t["panel"], accent, 0.14)
    return f"""
* {{ font-family: "{BODY}", "Nirmala UI", "Segoe UI", sans-serif; font-size: 13px; color: {t['ink']}; }}
QMainWindow, QDialog, #root {{ background: {t['paper']}; }}
QWidget#panel, QFrame#panel {{ background: {t['panel']}; border: 1px solid {t['line']}; }}
QLabel#brand {{ font-family: "{DISPLAY}"; font-weight: 700; font-size: 20px; letter-spacing: 1px; }}
QLabel#brandSmall, QLabel.mono, QLabel#mono {{ font-family: "{MONO}"; font-size: 11px; color: {t['muted']}; }}
QLabel#muted {{ color: {t['muted']}; font-size: 12px; }}
QLabel#h2 {{ font-family: "{DISPLAY}"; font-weight: 700; font-size: 18px; }}
QLabel#grp {{ font-family: "{DISPLAY}"; font-weight: 600; font-size: 12px; letter-spacing: 2px; color: {t['muted']}; padding-top: 14px; }}
QLabel#note {{ background: {soft}; border-left: 3px solid {accent}; padding: 8px 10px; font-size: 12px; }}
QPushButton {{ font-family: "{DISPLAY}"; font-weight: 600; letter-spacing: .5px; padding: 8px 14px; background: {t['panel']}; border: 1px solid {t['line']}; }}
QPushButton:hover {{ background: {t['ink']}; color: {t['panel']}; }}
QPushButton:disabled {{ color: {t['muted']}; background: {t['paper']}; }}
QPushButton#primary {{ background: {accent}; color: {ai}; border-color: {accent}; }}
QPushButton#primary:hover {{ background: {t['ink']}; color: {t['panel']}; }}
QPushButton#seg {{ font-family: "{BODY}"; font-weight: 600; font-size: 12px; padding: 6px 11px; color: {t['muted']}; border: 1px solid {t['line']}; }}
QPushButton#seg:checked {{ background: {accent}; color: {ai}; border-color: {accent}; }}
QPushButton#seg:hover:!checked {{ background: {t['paper']}; color: {t['ink']}; }}
QPushButton#pill {{ font-family: "{MONO}"; font-weight: 400; font-size: 12px; padding: 5px 9px; }}
QPushButton#pill:checked {{ background: {accent}; color: {ai}; border-color: {accent}; }}
QToolButton {{ border: none; padding: 8px; background: transparent; }}
QToolButton:hover {{ background: {soft}; }}
QToolButton:checked {{ background: {soft}; border-bottom: 2px solid {accent}; }}
QLineEdit, QComboBox, QSpinBox {{ background: {t['paper']}; border: 1px solid {t['line']}; padding: 6px 9px; selection-background-color: {accent}; selection-color: {ai}; }}
QLineEdit:focus, QComboBox:focus {{ border-color: {accent}; }}
QComboBox QAbstractItemView {{ background: {t['panel']}; border: 1px solid {t['line']}; selection-background-color: {soft}; selection-color: {t['ink']}; }}
QListWidget, QListView, QTreeWidget {{ background: {t['panel']}; border: none; outline: 0; }}
QListWidget::item {{ padding: 9px 8px; border-left: 3px solid transparent; }}
QListWidget::item:hover {{ background: {t['paper']}; }}
QListWidget::item:selected {{ background: {soft}; border-left: 3px solid {accent}; color: {t['ink']}; }}
QListWidget#cats::item {{ padding: 10px 12px; font-weight: 600; color: {t['muted']}; }}
QListWidget#cats::item:selected {{ color: {accent}; }}
QTabBar::tab {{ font-family: "{DISPLAY}"; font-weight: 600; letter-spacing: 1px; padding: 11px 16px; background: transparent; color: {t['muted']}; border: none; border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {t['ink']}; border-bottom: 2px solid {accent}; }}
QTabWidget::pane {{ border: none; border-top: 1px solid {t['line']}; }}
QSlider::groove:horizontal {{ height: 4px; background: {t['line']}; }}
QSlider::sub-page:horizontal {{ background: {accent}; }}
QSlider::handle:horizontal {{ width: 12px; height: 12px; margin: -5px 0; background: {t['panel']}; border: 3px solid {accent}; }}
QSlider::groove:vertical {{ width: 4px; background: {t['line']}; }}
QSlider::add-page:vertical {{ background: {accent}; }}
QSlider::handle:vertical {{ width: 12px; height: 12px; margin: 0 -5px; background: {t['panel']}; border: 3px solid {accent}; }}
QScrollBar:vertical {{ width: 10px; background: transparent; }}
QScrollBar::handle:vertical {{ background: {t['line']}; min-height: 30px; }}
QScrollBar:horizontal {{ height: 8px; background: transparent; }}
QScrollBar::handle:horizontal {{ background: {t['line']}; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollArea {{ border: none; background: {t['panel']}; }}
QWidget#page {{ background: {t['panel']}; }}
QFrame#row {{ border: none; border-bottom: 1px solid {t['line']}; }}
QMenu {{ background: {t['panel']}; border: 1px solid {t['line']}; padding: 6px 0; }}
QMenu::item {{ padding: 8px 22px 8px 30px; color: {t['ink']}; }}
QMenu::item:selected {{ background: {soft}; color: {t['ink']}; }}
QMenu::item:checked {{ color: {accent}; font-weight: 600; }}
QMenu::item:disabled {{ color: {t['muted']}; }}
QMenu::indicator {{ width: 8px; height: 8px; margin-left: 12px; }}
QMenu::indicator:checked {{ background: {accent}; border: none; }}
QMenu::indicator:unchecked {{ background: transparent; border: none; }}
QMenu::separator {{ height: 1px; background: {t['line']}; margin: 6px 0; }}
QMenu::scroller {{ height: 14px; background: {t['panel']}; }}
QLabel#menuHead {{ font-family: "{DISPLAY}"; font-weight: 600; font-size: 11px; letter-spacing: 2px; color: {t['muted']}; padding: 8px 22px 6px 22px; }}
QLabel#menuHead[accent="true"] {{ color: {accent}; }}
QToolTip {{ background: {t['ink']}; color: {t['panel']}; border: none; padding: 4px 8px; }}
"""
