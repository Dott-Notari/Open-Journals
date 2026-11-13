"""Testate straniere, scritte sulla mappatura con reverse-api-engineer del 12 novembre 2026.

Escluse perché il robots.txt vieta l'accesso automatico o perché le pagine rispondono con una
protezione anti-bot che lo strumento non aggira: The Times (Disallow: / per tutti), Financial Times
e El País (articoli dietro verifica Cloudflare / DataDome), The Economist, The Telegraph, Daily Mail,
The Sun."""
import os
import re
from datetime import date, timedelta

from .base import NonSupportato, Testata, termini_ricerca
from .seconda_ondata import _Mensile, _avviso
from .. import comune as C
from .. import sitemap as SM
from ..comune import giorni
from ..modello import SorgenteURL

MESI_EN = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
                                        "oct", "nov", "dec"), 1)}


class Independent(Testata):
    chiave, nome, dominio = "independent", "The Independent", "independent.co.uk"
    re_articolo = re.compile(r"^https://www\.independent\.co\.uk/(?!advisor/|extras/indybest/).+-b\d{6,}\.html$")
    selettori_corpo = ("#articleContent",)
    fine_testo = ("join our commenting forum", "read more", "sign up to")
    paginazione = None    # il robots.txt esclude «?page=»: le pagine elenco si leggono solo alla prima pagina
    note_ricerca_data = "sitemap giornaliere degli articoli, solo per gli ultimi novanta giorni circa"
    GIORNI_SITEMAP = 90

    def pagina_elenco(self, base, n):
        return base if n == 1 else None

    # pulsanti e riquadri dei segnalibri che precedono il testo dentro #articleContent
    INTERFACCIA = re.compile(r"^(bookmark( popover)?|comments go to comments|removed from bookmarks|"
                             r"want to bookmark your favourite|already a member\?)", re.I)

    def estrai(self, html, url):
        art = super().estrai(html, url)
        # il primo <h1> della pagina può essere il riquadro «Become an Independent member to bookmark…»
        if art.titolo.lower().startswith("become an independent member"):
            art.titolo = C.testo_pulito(C.meta(C.soup_di(html), "og:title")) or art.titolo
        art.testo = "\n".join(p for p in art.testo.split("\n") if not self.INTERFACCIA.search(p.strip()))
        return self.valuta(art)

    def piano_per_data(self, rete, dal, al, log, parole=None):
        files = [f"https://www.independent.co.uk/sitemaps/sitemap-articles-{g.isoformat()}.xml"
                 for g in giorni(dal, al)]
        urls = []
        for f in reversed(files):
            urls += [v[0] for v in SM.leggi_urlset(rete, f) if self.e_articolo(v[0])]
        urls = list(dict.fromkeys(urls))
        log(f"  The Independent: {len(files)} sitemap giornaliere, {len(urls)} articoli da verificare")
        minima = date.today() - timedelta(days=self.GIORNI_SITEMAP)
        return [SorgenteURL("sitemap giornaliere", urls, _avviso(self.nome, minima, dal))]


class Mirror(_Mensile):
    chiave, nome, dominio = "mirror", "Daily Mirror", "mirror.co.uk"
    modello_file = "https://www.mirror.co.uk/sitemaps/map_art_{anno}-{mese}-01.xml"
    re_articolo = re.compile(r"^https://www\.mirror\.co\.uk/(?!all-about/|authors/|search/).+-\d{6,}$")
    paginazione = None
    note_ricerca_data = ("sitemap mensili dal 1998, con la data di ultima modifica di ogni articolo: si scaricano "
                         "solo quelli modificati nel periodo o nei sette giorni successivi (gli articoli aggiornati "
                         "molto dopo la pubblicazione possono sfuggire); il robots.txt chiede 10 secondi tra le "
                         "richieste: conviene anche --cerca-in titolo")
    MARGINE = 7

    def pagina_elenco(self, base, n):
        return base if n == 1 else None

    def piano_per_data(self, rete, dal, al, log, parole=None):
        tetto = al + timedelta(days=self.MARGINE)
        voci = {}
        files = self.file_mesi(rete, dal, al)
        for f in files:
            for u, lastmod, _ in SM.leggi_urlset(rete, f):
                g = C.parse_data(lastmod)
                if g and dal <= g.date() <= tetto and self.e_articolo(u):
                    voci[u] = g.date()
        # prima gli articoli modificati dentro il periodo, poi quelli modificati nei giorni successivi
        urls = sorted(voci, key=lambda u: (voci[u] > al, voci[u]))
        log(f"  Daily Mirror: {len(files)} sitemap mensili, {len(urls)} articoli modificati tra il {dal} e il {tetto}")
        return [SorgenteURL(f"sitemap mensili filtrate per data di modifica ({len(files)})", urls)]


class ElMundo(Testata):
    chiave, nome, dominio = "elmundo", "El Mundo", "elmundo.es"
    re_articolo = re.compile(r"^https://www\.elmundo\.es/(?!elmundo/hemeroteca/).+/\d{4}/\d{2}/\d{2}/[0-9a-f]{24}\.html$")
    selettori_corpo = ("div.ue-c-article__body",)
    date_nell_url = True
    paginazione = None
    note_ricerca_data = ("emeroteca giornaliera del sito; la ricerca interna (ariadna) è esclusa dal "
                         "robots.txt e non viene usata")

    def pagina_elenco(self, base, n):
        return base if n == 1 else None

    def piano_per_data(self, rete, dal, al, log, parole=None):
        urls, vuoti = [], 0
        for g in reversed(list(giorni(dal, al))):
            trovati = []
            for pagina in ("noticias.html", "m/index.html"):
                url = f"https://www.elmundo.es/elmundo/hemeroteca/{g:%Y/%m/%d}/{pagina}"
                r = rete.get(url)
                if r is not None and r.status_code == 200:
                    trovati = [u for u in self.link_articoli(r.text, url) if f"/{g:%Y/%m/%d}/" in u]
                    if trovati:
                        break
            vuoti += not trovati
            urls += trovati
        log(f"  El Mundo: emeroteca di {len(list(giorni(dal, al)))} giorni, {len(urls)} articoli")
        avviso = f"El Mundo: {vuoti} giorni senza pagina di emeroteca" if vuoti else ""
        return [SorgenteURL("emeroteca giornaliera", list(dict.fromkeys(urls)), avviso)]


class Guardian(Testata):
    """API ufficiale (Guardian Open Platform). Serve una chiave gratuita, da richiedere su
    https://open-platform.theguardian.com/access/ e da impostare nella variabile GUARDIAN_API_KEY."""
    chiave, nome, dominio = "guardian", "The Guardian", "theguardian.com"
    re_articolo = re.compile(r"^https://www\.theguardian\.com/[a-z0-9-]+(?:/[a-z0-9-]+)*/\d{4}/[a-z]{3}/\d{2}/[^/]+$")
    paginazione = "{base}?page={n}"
    note_ricerca_data = "API ufficiale The Guardian Open Platform (content.guardianapis.com), archivio dal 1999"
    nota_ricerca = "API ufficiale The Guardian Open Platform, ricerca nel testo con filtro per date"
    API = "https://content.guardianapis.com/search"

    def data_da_url(self, url):
        m = re.search(r"/(\d{4})/([a-z]{3})/(\d{2})/", url)
        if m and m.group(2) in MESI_EN:
            try:
                return date(int(m.group(1)), MESI_EN[m.group(2)], int(m.group(3)))
            except ValueError:
                return None
        return None

    def _chiave(self):
        k = os.environ.get("GUARDIAN_API_KEY", "").strip()
        if not k:
            raise NonSupportato("The Guardian: manca la chiave dell'API ufficiale. Richiedila gratis su "
                                "https://open-platform.theguardian.com/access/ e impostala con "
                                "export GUARDIAN_API_KEY=la_tua_chiave (oppure nel file .env di VS Code)")
        return k

    def _cerca(self, rete, dal, al, q, log):
        k, urls, n, pagine = self._chiave(), [], 1, 1
        while n <= pagine:
            params = {"from-date": dal.isoformat(), "to-date": al.isoformat(), "type": "article",
                      "page-size": 50, "page": n, "order-by": "oldest", "api-key": k}
            if q:
                params["q"] = q
            r = rete.get(self.API, params=params)
            if r is None or r.status_code != 200:
                log(f"  The Guardian: l'API ha risposto {r.status_code if r is not None else 'nulla'}")
                break
            res = r.json().get("response", {})
            pagine = res.get("pages", 0)
            urls += [it["webUrl"] for it in res.get("results", []) if it.get("webUrl")]
            n += 1
        return [u for u in dict.fromkeys(urls) if self.e_articolo(u)]

    def piano_per_data(self, rete, dal, al, log, parole=None):
        urls = self._cerca(rete, dal, al, None, log)
        log(f"  The Guardian: {len(urls)} articoli dall'API")
        return [SorgenteURL("API ufficiale per data", urls)]

    def piano_per_parole(self, rete, parole, dal, al, log):
        termini = termini_ricerca(parole)
        if not termini:
            return None
        q = " OR ".join(f'"{t}"' if " " in t else t for t in termini)
        urls = self._cerca(rete, dal, al, q, log)
        log(f"  The Guardian: la ricerca dell'API per «{q}» propone {len(urls)} articoli")
        return [SorgenteURL(f"ricerca dell'API ufficiale per «{q}»", urls)]


ESTERE = (Independent(), Mirror(), ElMundo(), Guardian())
