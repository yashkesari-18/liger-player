"""Interface strings. The table is generated from ../js/i18n.js so the web and desktop apps share translations."""
import json

from .theme import ASSETS

# code, native name, English name, tier (r reviewed, d draft, h help wanted), right-to-left
LANGS = [
    ("en", "English", "English", "r", False), ("ru", "Русский", "Russian", "r", False), ("ko", "한국어", "Korean", "r", False),
    ("zh-CN", "简体中文", "Chinese (Simplified)", "r", False), ("ja", "日本語", "Japanese", "r", False), ("fr", "Français", "French", "r", False),
    ("de", "Deutsch", "German", "r", False), ("th", "ไทย", "Thai", "r", False),
    ("as", "অসমীয়া", "Assamese", "r", False), ("bn", "বাংলা", "Bengali", "r", False), ("brx", "बड़ो", "Bodo", "h", False),
    ("doi", "डोगरी", "Dogri", "d", False), ("gu", "ગુજરાતી", "Gujarati", "r", False), ("hi", "हिन्दी", "Hindi", "r", False),
    ("kn", "ಕನ್ನಡ", "Kannada", "r", False), ("ks", "کٲشُر", "Kashmiri", "h", True), ("gom", "कोंकणी", "Konkani", "d", False),
    ("mai", "मैथिली", "Maithili", "d", False), ("ml", "മലയാളം", "Malayalam", "r", False), ("mni", "ꯃꯤꯇꯩꯂꯣꯟ", "Manipuri (Meitei)", "h", False),
    ("mr", "मराठी", "Marathi", "r", False), ("ne", "नेपाली", "Nepali", "r", False), ("or", "ଓଡ଼ିଆ", "Odia", "r", False),
    ("pa", "ਪੰਜਾਬੀ", "Punjabi", "r", False), ("sa", "संस्कृतम्", "Sanskrit", "d", False), ("sat", "ᱥᱟᱱᱛᱟᱲᱤ", "Santali", "h", False),
    ("sd", "سنڌي", "Sindhi", "d", True), ("ta", "தமிழ்", "Tamil", "r", False), ("te", "తెలుగు", "Telugu", "r", False), ("ur", "اردو", "Urdu", "r", True),
]
INTL = ("en", "ru", "ko", "zh-CN", "ja", "fr", "de", "th")

with open(ASSETS / "locales.json", encoding="utf-8") as fh:
    TABLE = json.load(fh)


class Tr:
    def __init__(self, lang="en"):
        self.lang = lang

    def __call__(self, key):
        return TABLE.get(self.lang, {}).get(key) or TABLE["en"].get(key) or key

    def label(self, x):
        return self(x[1:]) if isinstance(x, str) and x.startswith("@") else x

    def rtl(self):
        return next((l[4] for l in LANGS if l[0] == self.lang), False)

    def tier(self):
        return next((l[3] for l in LANGS if l[0] == self.lang), "r")
