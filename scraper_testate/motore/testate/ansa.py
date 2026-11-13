"""ANSA (sitemap tematiche con le sole uscite recenti)."""
import re

from .base import Testata
from .. import sitemap as SM
from ..comune import parse_data
from ..modello import SorgenteURL

INDICE = "https://www.ansa.it/sito/sitemaps/sito_sitemap_index.xml"
ESCLUSE = re.compile(r"/(foto|video|podcast|english|indiaen|china|ansamedar|nuovaeuropaen)_sitemap")
NAZIONALI = ("ultimaora", "cronaca", "politica", "mondo", "economia", "europa", "cultura", "scienza",
             "tecnologia", "saluteebenessere", "vaticano", "scuola", "donne", "sport", "lifestyle")
REGIONI = ("abruzzo", "basilicata", "calabria", "campania", "emiliaromagna", "friuliveneziagiulia",
           "lazio", "liguria", "lombardia", "marche", "molise", "piemonte", "puglia", "sardegna",
           "sicilia", "toscana", "trentino", "umbria", "valledaosta", "veneto")


class Ansa(Testata):
    chiave = "ansa"
    nome = "ANSA"
    dominio = "ansa.it"
    re_articolo = re.compile(r"^https://www\.ansa\.it/.+/\d{4}/\d{2}/\d{2}/[^/]+\.html$")
    selettori_corpo = (".news-txt", ".post-single-text", "[itemprop=articleBody]")
    date_nell_url = True
    note_ricerca_data = ("le sitemap contengono solo le uscite recenti; non esiste un archivio "
                         "interrogabile per date lontane")

    def wayback_prefissi(self, dal, al):
        from ..comune import giorni
        return [(p, "prefix") for g in giorni(dal, al) for p in
                [f"www.ansa.it/sito/notizie/{s}/{g:%Y/%m/%d}/" for s in NAZIONALI] +
                [f"www.ansa.it/{r}/notizie/{g:%Y/%m/%d}/" for r in REGIONI]]

    def sezione_da_url(self, url):
        m = re.search(r"ansa\.it/(?:sito/notizie/)?([a-z0-9]+)/", url)
        return m.group(1) if m else ""

    def estrai(self, html, url):
        art = super().estrai(html, url)
        # nelle pagine regionali la sezione dichiarata è il generico «Notizie»: meglio la regione
        reg = self.sezione_da_url(url)
        if reg in REGIONI and art.sezione.lower() in ("notizie", ""):
            art.sezione = reg.capitalize()
        return art

    @staticmethod
    def _ordine(loc):
        nome = re.sub(r".*/|_sitemap_new\.xml", "", loc)
        if nome in NAZIONALI:
            return (0, NAZIONALI.index(nome))
        return (2, nome) if nome in REGIONI else (1, nome)

    def piano_per_data(self, rete, dal, al, log, parole=None):
        urls, piu_vecchia = [], None
        indice = [loc for loc, _ in SM.leggi_indice(rete, INDICE) if not ESCLUSE.search(loc)]
        for loc in sorted(indice, key=self._ordine):   # prima le sezioni nazionali, poi le regioni
            for u, lastmod, pub in SM.leggi_urlset(rete, loc):
                d = parse_data(pub or lastmod)
                if d is None or not self.e_articolo(u):
                    continue
                piu_vecchia = d.date() if piu_vecchia is None else min(piu_vecchia, d.date())
                if dal <= d.date() <= al:
                    urls.append(u)
        urls = list(dict.fromkeys(urls))
        avviso = ""
        if piu_vecchia and dal < piu_vecchia:
            avviso = (f"ANSA: le sitemap arrivano solo al {piu_vecchia.isoformat()}; "
                      f"i giorni precedenti non sono raggiungibili")
        return [SorgenteURL("sitemap tematiche ANSA", urls, avviso)]
