"""Fonti esterne per scoprire gli indirizzi degli articoli, in aggiunta agli archivi delle testate.

- GDELT (api.gdeltproject.org, DOC 2.0): indice internazionale delle notizie, dal 2017 circa.
  Le parole si cercano sulla traduzione inglese che GDELT fa di ogni articolo, quindi vanno date
  in inglese (--parole-gdelt "migrants,asylum"); la copertura di ciascuna testata è parziale.
- Wayback Machine (web.archive.org, indice CDX): indirizzi delle pagine catturate dall'Internet
  Archive nel periodo. Serve per i periodi che sitemap ed elenchi del sito non raggiungono più.

In entrambi i casi da qui arrivano solo gli indirizzi: ogni articolo viene poi scaricato dal sito
della testata (robots.txt compreso) e verificato. Le copie archiviate non vengono usate, per non
aggirare paywall o rimozioni decise dalla testata."""
import re
from datetime import datetime, timedelta

from .config import LIMITE_PAGINE
from .modello import SorgenteURL

GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
CDX = "https://web.archive.org/cdx/search/cdx"
MAX_GDELT = 250   # risultati massimi per richiesta


def _gdelt_finestra(rete, query, inizio, fine, log, profondita=0):
    r = rete.get(GDELT, tentativi=3, params={
        "query": query, "mode": "artlist", "format": "json", "maxrecords": MAX_GDELT, "sort": "dateasc",
        "startdatetime": inizio.strftime("%Y%m%d%H%M%S"), "enddatetime": fine.strftime("%Y%m%d%H%M%S")})
    if r is None or r.status_code != 200:
        log(f"  GDELT: nessuna risposta per {inizio:%Y-%m-%d} / {fine:%Y-%m-%d}")
        return []
    try:
        arts = r.json().get("articles", [])
    except ValueError:      # GDELT risponde in testo semplice agli errori di sintassi della query
        log(f"  GDELT: {r.text.strip()[:160]}")
        return []
    # finestra piena: probabilmente ci sono altri risultati, si divide a metà
    if len(arts) >= MAX_GDELT and fine - inizio > timedelta(hours=6) and profondita < 8:
        meta = inizio + (fine - inizio) / 2
        return (_gdelt_finestra(rete, query, inizio, meta, log, profondita + 1) +
                _gdelt_finestra(rete, query, meta, fine, log, profondita + 1))
    return [a["url"] for a in arts if a.get("url")]


def gdelt(rete, testata, termini, dal, al, log):
    dominio = testata.dominio
    parole = " OR ".join(f'"{t}"' if " " in t else t for t in termini)
    query = (f"({parole}) " if len(termini) > 1 else f"{parole} " if termini else "") + f"domain:{dominio}"
    urls, g = [], dal
    while g <= al:
        fine = min(g + timedelta(days=6), al)
        urls += _gdelt_finestra(rete, query, datetime.combine(g, datetime.min.time()),
                                datetime.combine(fine, datetime.max.time().replace(microsecond=0)), log)
        g = fine + timedelta(days=1)
    urls = [testata.normalizza(u) for u in urls]
    urls = list(dict.fromkeys(u for u in urls if testata.e_articolo(u)))
    log(f"  GDELT: {len(urls)} articoli di {testata.nome} per «{query}»")
    avviso = ("GDELT: indice parziale, le parole sono cercate sulla traduzione inglese degli articoli; "
              "non sostituisce l'archivio della testata")
    return [SorgenteURL(f"GDELT, query «{query}»", urls, avviso)]


def wayback(rete, testata, dal, al, log):
    """Indirizzi catturati dall'Internet Archive. Per le testate con la data nel percorso si chiede
    ogni giorno senza limiti di cattura; per le altre le catture tra dal e al + 7 giorni (un articolo
    viene di solito catturato nei giorni della pubblicazione). Si filtrano con le regole della testata."""
    urls, mancati = [], 0
    prefissi = testata.wayback_prefissi(dal, al)
    for url, tipo in prefissi:
        n_prima = len(urls)
        ok = _wayback_prefisso(rete, testata, url, tipo, dal, al, urls)
        mancati += not ok
        if len(prefissi) > 1 and len(urls) > n_prima:
            log(f"  Wayback: {url}  {len(urls) - n_prima} articoli")
    urls = list(dict.fromkeys(urls))
    log(f"  Wayback: {len(urls)} articoli di {testata.nome}" +
        (f" ({mancati} interrogazioni su {len(prefissi)} senza risposta)" if mancati else ""))
    avviso = ("Wayback Machine: indirizzi delle pagine catturate dall'Internet Archive nel periodo; "
              "la copertura dipende da cosa è stato archiviato e gli articoli non più online risultano errori"
              + (f"; {mancati} interrogazioni dell'indice non hanno avuto risposta" if mancati else ""))
    return [SorgenteURL("indice CDX della Wayback Machine", urls, avviso)]


def _wayback_prefisso(rete, testata, url, tipo, dal, al, urls):
    chiave = None
    params = {"url": url, "matchType": tipo, "output": "json", "fl": "original",
              "filter": ["statuscode:200", "mimetype:text/html"], "collapse": "urlkey",
              "limit": 20000, "showResumeKey": "true"}
    if tipo == "domain":
        params.update({"from": f"{dal:%Y%m%d}", "to": f"{al + timedelta(days=7):%Y%m%d}"})
    for _ in range(LIMITE_PAGINE):
        if chiave:
            params["resumeKey"] = chiave
        r = rete.get(CDX, params=params, tentativi=4, timeout=90)
        if r is None or r.status_code != 200:
            return False
        try:
            righe = r.json()
        except ValueError:
            return False
        chiave = None
        if len(righe) >= 2 and righe[-2] == []:     # ultima riga = chiave per la pagina successiva
            chiave = righe[-1][0]
            righe = righe[:-2]
        for riga in righe[1:]:
            u = re.sub(r":80/", "/", riga[0]).replace("http://", "https://")
            u = testata.normalizza(u)
            if testata.e_articolo(u):
                d = testata.data_da_url(u)
                if d is None or dal <= d <= al:
                    urls.append(u)
        if not chiave:
            return True
    return True
