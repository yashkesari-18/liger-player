"""Live TV: downloads the public iptv-org channel list (and the user's own M3U playlists) and caches it on disk."""
import json
import re
import time
import urllib.request

from PySide6.QtCore import QObject, QThread, Signal

from .settings import data_dir

ADULT = re.compile(r"\b(xxx|adult|18\+|porn|erotic|sexy|playboy|hustler)\b", re.I)
UA = "LigerPlayer/0.3 (+https://github.com/yashkesari-18/liger-player)"

SAMPLE = [("DD News", "IN", "news"), ("DD National", "IN", "general"), ("Sansad TV", "IN", "legislative"), ("France 24 English", "FR", "news"),
          ("DW English", "DE", "news"), ("NHK World-Japan", "JP", "news"), ("Arirang TV", "KR", "culture"), ("CGTN", "CN", "news"),
          ("Al Jazeera English", "QA", "news"), ("NASA TV", "US", "science"), ("Euronews", "FR", "news"), ("TRT World", "TR", "news")]


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_m3u(text, src):
    out, meta = [], None
    for ln in text.splitlines():
        l = ln.strip()
        if l.startswith("#EXTINF"):
            def at(k):
                m = re.search(k + r'="([^"]*)"', l)
                return m.group(1) if m else ""
            name = l.split(",", 1)[1].strip() if "," in l else ""
            meta = dict(n=name, cc=(re.split(r"[;,]", at("tvg-country"))[0] or "").upper(), cat=(at("group-title").split(";")[0] or "general").lower())
        elif l and not l.startswith("#") and meta:
            if not ADULT.search(meta["n"] + " " + meta["cat"]):
                out.append(dict(id="m3u:" + l, n=meta["n"] or l, cc=meta["cc"], cat=meta["cat"], u=l, src=src))
            meta = None
    return out


class _Worker(QObject):
    done = Signal(dict, str)

    def __init__(self, api, custom, imported):
        super().__init__()
        self.api, self.custom, self.imported = api, custom, imported

    def run(self):
        err, out, countries = "", [], {}
        base = self.api.rstrip("/")
        try:
            ch, st, co, bl = (json.loads(_get(f"{base}/{n}.json")) for n in ("channels", "streams", "countries", "blocklist"))
            block = {b.get("channel") for b in bl}
            meta = {c["id"]: c for c in ch if not c.get("is_nsfw") and c["id"] not in block and not c.get("closed") and "xxx" not in (c.get("categories") or [])}
            seen = set()
            for s in st:
                c = meta.get(s.get("channel"))
                if not c or not s.get("url"):
                    continue
                cid = s["channel"] + ("@" + s["feed"] if s.get("feed") else "")
                if cid in seen:
                    continue
                seen.add(cid)
                n = s.get("title") or c.get("name")
                if ADULT.search(n or ""):
                    continue
                out.append(dict(id=cid, n=n, cc=c.get("country") or "", cat=(c.get("categories") or ["general"])[0], u=s["url"],
                                q=s.get("quality") or "", r=s.get("referrer") or "", ua=s.get("user_agent") or ""))
            countries = {c["code"]: c.get("name", c["code"]) for c in co}
        except Exception as e:  # noqa: BLE001
            err = f"Couldn’t reach the channel list ({type(e).__name__})."
        for u in self.custom:
            try:
                out += parse_m3u(_get(u).decode("utf-8", "replace"), u)
            except Exception:
                err = err or f"Couldn’t load the playlist {u}."
        out += self.imported
        self.done.emit(dict(ch=out, countries=countries, updated=time.time() if out else 0, src="live" if out else "sample"), err)


class LiveTV(QObject):
    updated = Signal(str)  # error text or ""

    def __init__(self, store):
        super().__init__()
        self.s = store
        self.path = data_dir() / "tv.json"
        self.dead_path = data_dir() / "tv_dead.json"
        self.data = dict(ch=[], countries={}, updated=0, src="sample")
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            pass
        if not self.data.get("ch"):
            self.data["ch"] = [dict(id=f"sample{i}", n=n, cc=cc, cat=cat, u="", sample=True) for i, (n, cc, cat) in enumerate(SAMPLE)]
            self.data["src"] = "sample"
        try:
            self.dead = set(json.loads(self.dead_path.read_text(encoding="utf-8")))
        except Exception:
            self.dead = set()
        self.busy = False
        self.error = ""
        self._thread = None

    @property
    def channels(self):
        return self.data.get("ch", [])

    def due(self):
        age = time.time() - (self.data.get("updated") or 0)
        a = self.s["tvAuto"]
        return a == "launch" or (a == "daily" and age > 86400) or (a == "weekly" and age > 604800)

    def refresh(self):
        if self.busy:
            return
        self.busy = True
        imported = [c for c in self.channels if c.get("src") == "file"]
        self._thread = QThread()
        self._worker = _Worker(self.s["tvApi"], list(self.s["tvCustom"]), imported)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(self._finish)
        self._worker.done.connect(self._thread.quit)
        self._thread.start()

    def _finish(self, data, err):
        self.busy = False
        self.error = err
        if data["ch"]:
            self.data = data
            try:
                self.path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass
        self.updated.emit(err)

    def import_file(self, path):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                chans = parse_m3u(fh.read(), "file")
        except Exception:
            chans = []
        if chans:
            keep = [c for c in self.channels if not c.get("sample") and c.get("src") != "file"]
            self.data["ch"] = keep + chans
            self.data["updated"] = self.data.get("updated") or time.time()
            if self.data.get("src") == "sample":
                self.data["src"] = "file"
            try:
                self.path.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass
            self.updated.emit("")
        return len(chans)

    def mark_dead(self, cid):
        self.dead.add(cid)
        self._save_dead()

    def clear_dead(self):
        self.dead.clear()
        self._save_dead()

    def _save_dead(self):
        try:
            self.dead_path.write_text(json.dumps(sorted(self.dead)), encoding="utf-8")
        except Exception:
            pass
