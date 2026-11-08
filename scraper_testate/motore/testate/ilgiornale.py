"""il Giornale (piattaforma Arc XP)."""
import re
from datetime import date

from .base import Testata
from .. import sitemap as SM
from ..comune import giorni, piega
from ..modello import SorgenteURL, SorgenteElenco

INDICE = "https://www.ilgiornale.it/arc/outboundfeeds/sitemap-index/?outputType=xml"
SEZIONI = "https://www.ilgiornale.it/arc/outboundfeeds/sitemap-section-index/?outputType=xml"
MACRO_RISERVA = ["politica", "cronache", "esteri", "economia", "cultura", "sport", "spettacoli"]


class IlGiornale(Testata):
    chiave = "ilgiornale"
    nome = "il Giornale"
    dominio = "ilgiornale.it"
    re_articolo = re.compile(r"^https://www\.ilgiornale\.it/news/[^/]+/[^/?#]+(?:/|\.html)$")
    selettori_corpo = ()
    note_ricerca_data = ("le sitemap coprono solo gli ultimi giorni; per i periodi precedenti si scorrono "
                         "le pagine tag delle parole chiave e le macrosezioni, ciascuna consultabile online "
                         "solo per circa 10.000 articoli (le sezioni generali risalgono di pochi mesi, "
                         "i tag tematici anche di anni)")

    def pagina_elenco(self, base, n):
        return base if n == 1 else base.rstrip("/") + f"/{n}/"

    def sezione_da_url(self, url):
        m = re.search(r"/news/([^/]+)/", url)
        return m.group(1).replace("-", " ") if m else ""

    def piano_per_data(self, rete, dal, al, log, parole=None):
        mappa = {}
        oggi = date.today().isoformat()
        for loc, _ in SM.leggi_indice(rete, INDICE):
            m = re.search(r"/sitemap\d?/(\d{4}-\d{2}-\d{2}|latest)/", loc)
            if m:
                mappa[oggi if m.group(1) == "latest" else m.group(1)] = loc
        coperti, urls = [], []
        for g in giorni(dal, al):
            loc = mappa.get(g.isoformat())
            if not loc:
                continue
            voci = SM.leggi_urlset(rete, loc)
            if voci:
                coperti.append(g)
                urls += [v[0] for v in voci if self.e_articolo(v[0])]
        sorgenti = []
        if urls:
            sorgenti.append(SorgenteURL(f"sitemap giornaliere ({len(coperti)} giorni)", urls))
        mancanti = [g for g in giorni(dal, al) if g not in coperti]
        if mancanti:
            log(f"  il Giornale: {len(mancanti)} giorni non coperti dalle sitemap, "
                f"scorro le pagine tag delle parole chiave e le macrosezioni")
            # le pagine tag risalgono molto più indietro delle sezioni (limite di circa 10.000 articoli per elenco)
            for parola in parole or []:
                if "*" not in parola:
                    tag = re.sub(r"[^a-z0-9]+", "-", piega(parola)).strip("-")
                    sorgenti.append(SorgenteElenco(f"tag /{tag}/", f"https://www.ilgiornale.it/tag/{tag}/"))
            for sez in self.macrosezioni(rete):
                sorgenti.append(SorgenteElenco(f"macrosezione /{sez}/",
                                               f"https://www.ilgiornale.it/{sez}/"))
        return sorgenti

    def macrosezioni(self, rete):
        sez = []
        for loc, _, _ in SM.leggi_urlset(rete, SEZIONI):
            m = re.fullmatch(r"https://www\.ilgiornale\.it/([a-z0-9-]+)/?", loc)
            if m:
                sez.append(m.group(1))
        return sez or MACRO_RISERVA
