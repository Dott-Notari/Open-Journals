"""Accesso alla rete: una sola sessione, pause per sito, nuovi tentativi, piccola cache, rispetto del robots.txt."""
import gzip
import re
import time
from collections import OrderedDict
from urllib.parse import urlparse

import requests

from .config import UA, PAUSA_DEFAULT, PAUSA_MINIMA, TIMEOUT
from .robots import Robots

SEGNALI_BLOCCO = ("cf-chl", "just a moment...", "attention required", "captcha")


# pause minime per servizi che le dichiarano nella documentazione invece che nel robots.txt
PAUSE_SERVIZI = {"api.gdeltproject.org": 6.0, "web.archive.org": 2.0}


class Bloccato(Exception):
    """Il sito ha risposto con una pagina di protezione anti-bot."""


class Rete:
    """Ogni richiesta è prima confrontata con il robots.txt del sito: gli indirizzi esclusi non vengono
    scaricati (get restituisce None) e il Crawl-delay dichiarato, se maggiore, sostituisce la pausa."""

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
        self._robots = {}
        self.esclusi = []          # indirizzi non scaricati perché esclusi dal robots.txt

    def robots(self, host):
        if host not in self._robots:
            testo = ""
            try:
                r = self.s.get(f"https://{host}/robots.txt", timeout=TIMEOUT)
                # 4xx: nessuna regola; 5xx o rete assente: per prudenza si considera tutto escluso (RFC 9309)
                if r.status_code == 200:
                    testo = r.text
                elif r.status_code >= 500:
                    testo = "User-agent: *\nDisallow: /"
            except requests.RequestException:
                testo = "User-agent: *\nDisallow: /"
            self._robots[host] = Robots(testo, UA)
            rit = self._robots[host].ritardo
            if rit and rit > self.pausa:
                self.log(f"  {host} chiede {rit:.0f} s tra una richiesta e l'altra (Crawl-delay): rispettato")
        return self._robots[host]

    def consentito(self, url):
        return self.robots(urlparse(url).netloc).consentito(url)

    def pausa_per(self, host):
        return max(self.pausa, self.robots(host).ritardo or 0, PAUSE_SERVIZI.get(host, 0))

    def _attendi(self, host):
        attesa = self.pausa_per(host) - (time.monotonic() - self._ultimo.get(host, 0.0))
        if attesa > 0:
            time.sleep(attesa)

    def get(self, url, cache=False, tentativi=4, **opzioni):
        """Restituisce la risposta (anche se non 200) oppure None se la rete non risponde
        o se l'indirizzo è escluso dal robots.txt. opzioni: params, headers, json (con json si fa POST)."""
        if cache and url in self._cache:
            self._cache.move_to_end(url)
            return self._cache[url]
        host = urlparse(url).netloc
        completo = requests.Request("GET", url, params=opzioni.get("params")).prepare().url
        if not self.consentito(completo):
            if completo not in self.esclusi:
                self.esclusi.append(completo)
                self.log(f"  escluso dal robots.txt di {host}, non scaricato: {completo}")
            return None
        for t in range(tentativi):
            self._attendi(host)
            try:
                metodo = self.s.post if "json" in opzioni else self.s.get
                r = metodo(url, allow_redirects=True, **{"timeout": TIMEOUT, **opzioni})
            except requests.RequestException as e:
                self._ultimo[host] = time.monotonic()
                self.log(f"  rete: {e.__class__.__name__} su {url}, nuovo tentativo")
                time.sleep(self.pausa_per(host) * 2 ** t)
                continue
            self._ultimo[host] = time.monotonic()
            self.richieste += 1
            if r.status_code in (429, 500, 502, 503, 504):
                ra = r.headers.get("Retry-After", "")
                attesa = int(ra) if ra.isdigit() else self.pausa_per(host) * 2 ** (t + 1)
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
