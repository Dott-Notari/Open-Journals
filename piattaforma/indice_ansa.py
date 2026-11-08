"""Indice delle uscite ANSA: ogni giorno si leggono le sitemap tematiche dell'agenzia e se ne
registrano indirizzo, titolo, data, sezione e regione (nessun testo). Con il tempo l'ANSA diventa
interrogabile per date anche oltre i pochi giorni esposti dal sito.

Uso: python -m piattaforma.indice_ansa
"""
import re
import sys
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from . import MOTORE  # noqa: F401  (rende importabile il motore)
from motore import comune as C
from motore.rete import Rete, contenuto_xml
from motore.testate.ansa import ESCLUSE, INDICE, REGIONI, Ansa

from .servizi import Supabase
from .stato import pubblico

ROMA = ZoneInfo("Europe/Rome")
RE_DATA_PUB = re.compile(r"(^|:)publication_date$")
RE_TITOLO = re.compile(r"(^|:)title$")


def _titolo_news(u):
    for t in u.find_all(RE_TITOLO):
        genitore = t.parent.name.split(":")[-1] if t.parent else ""
        if t.prefix == "news" or genitore == "news":
            return t.get_text(strip=True)[:500]
    return None


def leggi(rete, log=lambda m: None):
    """Restituisce le voci delle sitemap tematiche, senza duplicati."""
    ansa = Ansa()
    voci = {}
    r = rete.get(INDICE)
    if r is None or r.status_code != 200:
        raise RuntimeError("indice delle sitemap ANSA non raggiungibile")
    indice = BeautifulSoup(contenuto_xml(r), "xml")
    file = [s.loc.get_text(strip=True) for s in indice.find_all("sitemap") if s.loc]
    file = [f for f in file if not ESCLUSE.search(f)]
    for f in sorted(file, key=ansa._ordine):
        r = rete.get(f)
        if r is None or r.status_code != 200:
            log(f"  sitemap non raggiungibile: {f}")
            continue
        for u in BeautifulSoup(contenuto_xml(r), "xml").find_all("url"):
            if not u.loc:
                continue
            url = ansa.normalizza(u.loc.get_text(strip=True))
            if url in voci or not ansa.e_articolo(url):
                continue
            pub = u.find(RE_DATA_PUB)
            d = C.parse_data((pub.get_text(strip=True) if pub else "")
                             or (u.lastmod.get_text(strip=True) if u.lastmod else ""))
            if d is None:
                continue
            seg = ansa.sezione_da_url(url)
            voci[url] = {"url": url, "titolo": _titolo_news(u), "pubblicato_il": d.isoformat(),
                         "sezione": seg or None, "regione": seg if seg in REGIONI else None}
    return list(voci.values())


def aggiorna(sb, rete, log=lambda m: None):
    voci = leggi(rete, log)
    for i in range(0, len(voci), 500):
        sb.inserisci("ansa_indice", voci[i:i + 500], conflitto="url")
    return len(voci)


def inizio_indice(sb):
    r = sb.seleziona("ansa_indice", select="pubblicato_il", order="pubblicato_il.asc", limit="1")
    return C.parse_data(r[0]["pubblicato_il"]).date() if r else None


def indirizzi(sb, dal, al):
    """Voci dell'indice pubblicate tra dal e al compresi (giorni in ora italiana)."""
    inizio = datetime.combine(dal, time.min, ROMA).isoformat()
    fine = datetime.combine(al + timedelta(days=1), time.min, ROMA).isoformat()
    voci, passo = [], 1000
    while True:
        blocco = sb.seleziona("ansa_indice", select="url,titolo,pubblicato_il",
                              order="pubblicato_il.asc,url.asc",
                              limit=str(passo), offset=str(len(voci)),
                              **{"pubblicato_il": f"gte.{inizio}", "and": f"(pubblicato_il.lt.{fine})"})
        voci += blocco
        if len(blocco) < passo:
            return voci


def main():
    sb = Supabase()
    if not sb.impostazioni()["ansa_indicizzazione_attiva"]:
        pubblico("[indice ANSA] sospeso dal docente")
        return 0
    if sb.seleziona("estrazioni", select="id", fonte="eq.ansa", stato="eq.in_corso", limit="1"):
        pubblico("[indice ANSA] un'estrazione ANSA è in corso e aggiorna l'indice da sé: salto questo giro")
        return 0
    n = aggiorna(sb, Rete())
    pubblico(f"[indice ANSA] voci lette dalle sitemap: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
