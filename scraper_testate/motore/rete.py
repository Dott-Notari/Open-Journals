"""Accesso alla rete: una sola sessione, pause per sito, nuovi tentativi, piccola cache."""
import gzip
import re
import time
from collections import OrderedDict
from urllib.parse import urlparse

import requests

from .config import UA, PAUSA_DEFAULT, PAUSA_MINIMA, TIMEOUT

SEGNALI_BLOCCO = ("cf-chl", "just a moment...", "attention required", "captcha")


class Bloccato(Exception):
    """Il sito ha risposto con una pagina di protezione anti-bot."""


class Rete:
    def __init__(self, pausa=PAUSA_DEFAULT, log=None, cache_max=80):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA,
                               "Accept-Language": "it-IT,it;q=0.9,en;q=0.5"})
        self.pausa = max(PAUSA_MINIMA, float(pausa))
        self.log = log or (lambda m: None)
        self._ultimo = {}
        self._cache = OrderedDict()
        self._cache_max = cache_max
        self.richieste = 0

    def _attendi(self, host):
        attesa = self.pausa - (time.monotonic() - self._ultimo.get(host, 0.0))
        if attesa > 0:
            time.sleep(attesa)

    def get(self, url, cache=False, tentativi=4):
        """Restituisce la risposta (anche se non 200) oppure None se la rete non risponde."""
        if cache and url in self._cache:
            self._cache.move_to_end(url)
            return self._cache[url]
        host = urlparse(url).netloc
        for t in range(tentativi):
            self._attendi(host)
            try:
                r = self.s.get(url, timeout=TIMEOUT, allow_redirects=True)
            except requests.RequestException as e:
                self._ultimo[host] = time.monotonic()
                self.log(f"  rete: {e.__class__.__name__} su {url}, nuovo tentativo")
                time.sleep(self.pausa * 2 ** t)
                continue
            self._ultimo[host] = time.monotonic()
            self.richieste += 1
            if r.status_code in (429, 500, 502, 503, 504):
                ra = r.headers.get("Retry-After", "")
                attesa = int(ra) if ra.isdigit() else self.pausa * 2 ** (t + 1)
                self.log(f"  il sito risponde {r.status_code}, attendo {attesa:.0f} s")
                time.sleep(min(attesa, 120))
                continue
            if r.status_code == 403 and any(s in r.text[:4000].lower() for s in SEGNALI_BLOCCO):
                raise Bloccato(f"{host} ha attivato la protezione anti-bot su {url}")
            ct = r.headers.get("content-type", "").lower()
            if "charset" not in ct and ("html" in ct or "xml" in ct or not ct):
                m = re.search(rb"""<meta[^>]+charset=["']?([\w-]+)""", r.content[:4000], re.I)
                r.encoding = m.group(1).decode() if m else "utf-8"
            if cache and r.status_code == 200:
                self._cache[url] = r
                if len(self._cache) > self._cache_max:
                    self._cache.popitem(last=False)
            return r
        return None


def contenuto_xml(r) -> bytes:
    dati = r.content
    if dati[:2] == b"\x1f\x8b":
        dati = gzip.decompress(dati)
    return dati
