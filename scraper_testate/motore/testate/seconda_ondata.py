"""Testate della seconda e terza ondata, scritte sulla ricognizione dell'8 novembre 2026."""
import re
from datetime import date, timedelta

from .base import Testata
from .. import sitemap as SM
from ..comune import giorni, mesi
from ..modello import SorgenteURL

MESI_IT = {m: i for i, m in enumerate(("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
                                        "agosto", "settembre", "ottobre", "novembre", "dicembre"), 1)}


def _avviso(nome, minima, dal, cosa="le sitemap disponibili"):
    if minima and dal < minima:
        return (f"{nome}: {cosa} arrivano solo al {minima.isoformat()}; "
                f"i giorni precedenti non sono raggiungibili per data")
    return ""


# ------------------------------------------------------------------ sitemap mensili
class _Mensile(Testata):
    """Siti con una sitemap per mese: si leggono solo i mesi richiesti."""
    indice = ""
    re_file = r"(\d{4}-\d{2})"          # gruppo 1: AAAA-MM
    modello_file = ""                   # in alternativa all'indice: URL con {anno} e {mese}

    def file_mesi(self, rete, dal, al):
        richiesti = set(mesi(dal, al))
        if self.modello_file:
            return [self.modello_file.format(anno=m[:4], mese=m[5:]) for m in sorted(richiesti, reverse=True)]
        out = []
        for loc, _ in SM.leggi_indice(rete, self.indice):
            m = re.search(self.re_file, loc)
            if m and m.group(1) in richiesti:
                out.append(loc)
        return out

    def piano_per_data(self, rete, dal, al, log, parole=None):
        files = self.file_mesi(rete, dal, al)
        urls = []
        for f in files:
            urls += [v[0] for v in SM.leggi_urlset(rete, f) if self.e_articolo(v[0])]
        urls = list(dict.fromkeys(urls))
        log(f"  {self.nome}: {len(files)} sitemap mensili, {len(urls)} articoli da verificare")
        avviso = "" if files else f"{self.nome}: nessuna sitemap per i mesi richiesti"
        return [SorgenteURL(f"sitemap mensili ({len(files)})", urls, avviso)]


class IlPost(_Mensile):
    paginazione = "{base}page/{n}/"   # verificata con il collaudo dell'8 novembre 2026
    elenchi_prova = ("https://www.ilpost.it/tag/migranti/", "https://www.ilpost.it/italia/")
    chiave, nome, dominio = "ilpost", "Il Post", "ilpost.it"
    indice = "https://www.ilpost.it/sitemaps/sitemap-posts-index.xml"
    re_file = r"/posts/sitemap-(\d{4}-\d{2})\.xml"
    re_articolo = re.compile(r"^https://www\.ilpost\.it/\d{4}/\d{2}/\d{2}/[^/]+/?$")
    date_nell_url = True
    note_ricerca_data = "sitemap mensili degli articoli dal 2009 (le brevi «flashes» sono escluse)"

    def normalizza(self, url):
        u = super().normalizza(url)
        return u if u.endswith("/") else u + "/"

    def estrai(self, html, url):
        art = super().estrai(html, url)
        # i «PostIt» (frequenti nei primi anni) non hanno testo: rimandano alla fonte esterna citata nel titolo
        if "categoria PostIt" in html:
            m = re.search(r'<h1[^>]*>\s*<a[^>]+href="([^"]+)"', html)
            art.testo = ""
            art.metodo = "PostIt: rimando a fonte esterna"
            art = self.valuta(art)
            art.note = "PostIt, solo titolo: il testo è sulla fonte esterna" + (f" ({m.group(1)})" if m else "")
        return art


class _Gedi(_Mensile):
    """Repubblica e La Stampa (stessa piattaforma GEDI): sitemap mensili compresse."""
    re_file = r"/sitemap-(\d{4}-\d{2})\.xml\.gz$"
    selettori_corpo = ("div.story__text", "#article-body", "div.story__content")
    date_nell_url = True
    note_ricerca_data = ("sitemap mensili; gli articoli riservati agli abbonati espongono spesso solo "
                         "titolo e sommario e risultano come testo parziale")

    def piano_per_data(self, rete, dal, al, log, parole=None):
        sorgenti = super().piano_per_data(rete, dal, al, log, parole)
        oggi = date.today()
        if not sorgenti[0].urls:   # riserva: sitemap news con le sole uscite recenti
            urls, minima = SM.per_data_pubblicazione(rete, [self.news], dal, al, self.e_articolo)
            sorgenti = [SorgenteURL("sitemap news", urls, _avviso(self.nome, minima, dal))]
        elif (al.year, al.month) == (oggi.year, oggi.month):
            # la sitemap del mese in corso elenca solo gli ultimi uno o due giorni: si aggiunge la sitemap
            # news e si segnala che i giorni già usciti da entrambe non sono raggiungibili per data
            urls, minima = SM.per_data_pubblicazione(rete, [self.news], dal, al, self.e_articolo)
            noti = set(sorgenti[0].urls)
            sorgenti.append(SorgenteURL("sitemap news (uscite recenti)", [u for u in urls if u not in noti]))
            date_mese = [d for d in map(self.data_da_url, noti) if d] + ([minima] if minima else [])
            prima = min(date_mese) if date_mese else None
            inizio_mese = date(oggi.year, oggi.month, 1)
            if prima and max(dal, inizio_mese) < prima:
                sorgenti[0].avviso = (f"{self.nome}: per il mese in corso le sitemap arrivano solo al "
                                      f"{prima.isoformat()}; i giorni dal {max(dal, inizio_mese).isoformat()} "
                                      f"al {(prima - timedelta(days=1)).isoformat()} non sono raggiungibili per data "
                                      f"(si recuperano a mese chiuso, o dalle pagine di sezione con il comando elenco)")
        return sorgenti


class Repubblica(_Gedi):
    paginazione = "{base}?page={n}"   # verificata con il collaudo dell'8 novembre 2026
    elenchi_prova = ("https://www.repubblica.it/cronaca/",)
    chiave, nome, dominio = "repubblica", "la Repubblica", "repubblica.it"
    indice = "https://www.repubblica.it/sitemap.xml"
    news = "https://www.repubblica.it/sitemap-n.xml"
    re_articolo = re.compile(r"^https://[a-z]+\.repubblica\.it/.*\d{4}/\d{2}/\d{2}/news/[^/]+-\d{6,}/?$")


class LaStampa(_Gedi):
    paginazione = "{base}?page={n}"   # verificata con il collaudo dell'8 novembre 2026
    elenchi_prova = ("https://www.lastampa.it/cronaca/",)
    chiave, nome, dominio = "lastampa", "La Stampa", "lastampa.it"
    indice = "https://www.lastampa.it/sitemap.xml"
    news = "https://www.lastampa.it/sitemap-n.xml"
    re_articolo = re.compile(r"^https://www\.lastampa\.it/(?!la-zampa/).*\d{4}/\d{2}/\d{2}/news/[^/]+-\d{6,}/?$")


class Libero(Testata):
    """Dal novembre 2026 su Arc XP, come il Giornale: le vecchie sitemap mensili non esistono più.
    Per data: sitemap giornaliere (dalla migrazione) e l'elenco API ei-feed-paginated-api, ordinato dal
    più recente e consultabile per circa 9.900 articoli per richiesta (tutto il sito o una sezione)."""
    chiave, nome, dominio = "libero", "Libero Quotidiano", "liberoquotidiano.it"
    re_articolo = re.compile(r"^https://www\.liberoquotidiano\.it/news/[a-z0-9-]+/(?:\d+/)?[^/?#]+/?$")
    note_ricerca_data = ("dal novembre 2026 piattaforma Arc XP: sitemap giornaliere dalla migrazione e, per i "
                         "periodi precedenti, l'elenco degli articoli del sito (circa tre mesi e mezzo) e delle "
                         "sezioni (alcuni mesi o anni, fino a 9.900 articoli ciascuna); oltre, --fonte wayback")
    BASE = "https://www.liberoquotidiano.it"
    API = BASE + "/pf/api/v3/content/fetch/ei-feed-paginated-api"
    INDICE = BASE + "/arc/outboundfeeds/sitemap-index/?outputType=xml"
    SEZIONI = BASE + "/arc/outboundfeeds/sitemap-section-index/?outputType=xml"
    ESCLUSE = ("agenzie", "blog", "multimedia", "x-video-embed", "general")
    PER_PAGINA, MASSIMO = 100, 9900

    def normalizza(self, url):
        u = super().normalizza(url)
        return u if u.endswith("/") else u + "/"

    def pagina_elenco(self, base, n):
        return base if n == 1 else None   # le pagine HTML di sezione non sono paginabili

    def _elenco(self, rete, sezione, dal, al, minime):
        import json
        from .ricerca import FuoriPortata, _giorno, _ordinati

        def pagina(n):
            q = {"from": n * self.PER_PAGINA, "size": self.PER_PAGINA, **({"sections": sezione} if sezione else {})}
            r = rete.get(self.API, params={"query": json.dumps(q)})
            try:
                els = r.json().get("content_elements", []) if r is not None and r.status_code == 200 else []
            except ValueError:
                els = []
            voci = [(self.BASE + e["canonical_url"], _giorno(e.get("display_date"))) for e in els
                    if e.get("type") == "story" and e.get("canonical_url")]
            date = [g for _, g in voci if g]
            if date:
                minime[sezione] = min(date + ([minime[sezione]] if minime.get(sezione) else []))
            return voci
        try:
            return list(_ordinati(pagina, dal, al, prima=0, ultima=self.MASSIMO // self.PER_PAGINA - 1))
        except FuoriPortata:
            return []

    def piano_per_data(self, rete, dal, al, log, parole=None):
        oggi = date.today().isoformat()
        mappa = {}
        for loc, _ in SM.leggi_indice(rete, self.INDICE):
            m = re.search(r"/sitemap/(\d{4}-\d{2}-\d{2}|latest)/", loc)
            if m:
                mappa[oggi if m.group(1) == "latest" else m.group(1)] = loc
        urls, coperti = [], set()
        for g in giorni(dal, al):
            if g.isoformat() in mappa:
                voci = SM.leggi_urlset(rete, mappa[g.isoformat()])
                urls += [v[0] for v in voci if self.e_articolo(self.normalizza(v[0]))]
                coperti.add(g)
        sorgenti = [SorgenteURL(f"sitemap giornaliere ({len(coperti)} giorni)", urls)] if urls else []
        if len(coperti) == len(list(giorni(dal, al))):
            return sorgenti
        minime = {}
        tutti = self._elenco(rete, None, dal, al, minime)
        if minime.get(None) and minime[None] <= dal:
            log(f"  Libero: elenco del sito, {len(tutti)} articoli nel periodo")
            return sorgenti + [SorgenteURL("elenco degli articoli del sito (API Arc)", tutti)]
        # il periodo è più vecchio di quanto raggiunge l'elenco generale: si passa sezione per sezione
        sezioni = []
        for loc, _ in SM.leggi_indice(rete, self.SEZIONI):
            m = re.search(r"/sitemap/category/([a-z0-9-]+)/\?", loc)
            if m and m.group(1) not in self.ESCLUSE:
                sezioni.append("/" + m.group(1))
        per_sezione = list(tutti)
        for s in sezioni:
            trovati = self._elenco(rete, s, dal, al, minime)
            per_sezione += trovati
            log(f"  Libero: sezione {s}, {len(trovati)} articoli nel periodo"
                + (f" (l'elenco risale al {minime[s].isoformat()})" if minime.get(s) and minime[s] > dal else ""))
        corte = [s for s in sezioni if minime.get(s) and minime[s] > dal]
        avviso = (f"Libero: {len(corte)} sezioni su {len(sezioni)} non risalgono fino al {dal.isoformat()} "
                  f"(elenchi online limitati a 9.900 articoli); per completare usare --fonte wayback") if corte else ""
        return sorgenti + [SorgenteURL(f"elenchi delle sezioni (API Arc, {len(sezioni)} sezioni)",
                                       list(dict.fromkeys(per_sezione)), avviso)]


# ------------------------------------------------------------------ sitemap giornaliere
class Corriere(Testata):
    elenchi_prova = ("https://www.corriere.it/cronache/",)
    chiave, nome, dominio = "corriere", "Corriere della Sera", "corriere.it"
    re_articolo = re.compile(r"^https://(?!video\.)[a-z]+\.corriere\.it/(?!lodicoalcorriere).+/\d{2}_[a-z]+_\d{2}/[^/]+\.shtml$")
    note_ricerca_data = ("sitemap giornaliere dal maggio 2020; per gli ultimi giorni le sitemap "
                         "di sezione con le cento uscite più recenti")

    def data_da_url(self, url):
        m = re.search(r"/(\d{2})_([a-z]+)_(\d{2})/", url)
        if m and m.group(2) in MESI_IT:
            try:
                return date(2000 + int(m.group(1)), MESI_IT[m.group(2)], int(m.group(3)))
            except ValueError:
                return None
        return None

    def piano_per_data(self, rete, dal, al, log, parole=None):
        files = [f"https://www.corriere.it/rss/sitemaps/{g:%Y}/sitemap_{g:%m}_{g:%d}_items.xml"
                 for g in giorni(dal, al)]
        # le sitemap giornaliere compaiono con un paio di giorni di ritardo: per il recente si
        # aggiungono quelle di sezione dichiarate nel robots.txt
        if (date.today() - al).days < 4:
            r = rete.get("https://www.corriere.it/robots.txt")
            if r is not None and r.status_code == 200:
                files += [u for u in re.findall(r"(?im)^sitemap:\s*(\S+)", r.text)
                          if "sitemap-last-100" in u and "/video/" not in u]
        urls, _ = SM.per_data_pubblicazione(rete, files, dal, al, self.e_articolo)
        log(f"  Corriere: {len(files)} sitemap, {len(urls)} articoli nell'intervallo")
        return [SorgenteURL("sitemap giornaliere e di sezione", urls,
                            "" if dal >= date(2020, 5, 27) else
                            "Corriere: le sitemap giornaliere partono dal maggio 2020")]


# ------------------------------------------------------------------ solo sitemap recenti
class _Caltagirone(Testata):
    """Il Mattino e Il Messaggero: sitemap news con le uscite degli ultimi giorni."""
    selettori_corpo = ("div.body-text",)
    note_ricerca_data = ("solo le uscite degli ultimi giorni (sitemap news); per periodi precedenti "
                         "si parte dalle pagine di sezione con il comando elenco")

    def piano_per_data(self, rete, dal, al, log, parole=None):
        urls, minima = SM.per_data_pubblicazione(rete, [self.news], dal, al, self.e_articolo)
        return [SorgenteURL("sitemap news", urls, _avviso(self.nome, minima, dal))]


class Mattino(_Caltagirone):
    paginazione = "{base}?p={n}"   # verificata con il collaudo dell'8 novembre 2026
    elenchi_prova = ("https://www.ilmattino.it/napoli/cronaca/",)
    chiave, nome, dominio = "mattino", "Il Mattino", "ilmattino.it"
    news = "https://www.ilmattino.it/?sez=XML&p=MapNews"
    re_articolo = re.compile(r"^https://www\.ilmattino\.it/.+-\d{6,}\.html$")


class Messaggero(_Caltagirone):
    paginazione = "{base}?p={n}"   # verificata con il collaudo dell'8 novembre 2026
    elenchi_prova = ("https://www.ilmessaggero.it/roma/",)
    chiave, nome, dominio = "messaggero", "Il Messaggero", "ilmessaggero.it"
    news = "https://www.ilmessaggero.it/?sez=XML&p=MapNews"
    re_articolo = re.compile(r"^https://www\.ilmessaggero\.it/.+-\d{6,}\.html$")


class Sole24Ore(Testata):
    elenchi_prova = ("https://www.ilsole24ore.com/sez/italia",)
    chiave, nome, dominio = "sole24ore", "Il Sole 24 Ore", "ilsole24ore.com"
    indice = "https://www.ilsole24ore.com/sitemap/sitemap-news.xml"
    re_articolo = re.compile(r"^https://www\.ilsole24ore\.com/art/[^/]+-[A-Za-z0-9]{6,}$")
    note_ricerca_data = "sitemap news delle sezioni, con profondità diversa da sezione a sezione"

    def piano_per_data(self, rete, dal, al, log, parole=None):
        files = [loc for loc, _ in SM.leggi_indice(rete, self.indice)]
        urls, minima = SM.per_data_pubblicazione(rete, files, dal, al, self.e_articolo)
        log(f"  Sole 24 Ore: {len(files)} sitemap di sezione, {len(urls)} articoli nell'intervallo")
        return [SorgenteURL("sitemap news di sezione", urls,
                            _avviso(self.nome, minima, dal, "le sitemap di sezione"))]


# ------------------------------------------------------------------ sitemap non ordinate per data
class Verita(Testata):
    paginazione = "{base}page/{n}/"   # verificata con il collaudo dell'8 novembre 2026
    elenchi_prova = ("https://www.laverita.info/mondo",)
    chiave, nome, dominio = "verita", "La Verità", "laverita.info"
    re_articolo = re.compile(
        r"^https://www\.laverita\.info/(?:(?!video/|podcast|author/|tag/|category/|edicola|feed|page/)"
        r"[a-z0-9-]+/[a-z0-9-]+/?|[a-z0-9-]+-\d{9,}\.html)$")
    selettori_corpo = (".lv-article__body", ".article-body__text")
    note_ricerca_data = ("API REST di WordPress con filtro per date (verifica del 12 novembre 2026): archivio "
                         "completo dal dicembre 2018; per i mesi precedenti solo pochi articoli, il resto "
                         "si recupera con --fonte wayback. Le vecchie sitemap non sono ordinate per data")
    API = "https://www.laverita.info/wp-json/wp/v2/posts"
    INIZIO_API = date(2018, 12, 1)

    def piano_per_data(self, rete, dal, al, log, parole=None):
        urls = []
        for n in range(1, 1000):
            r = rete.get(self.API, params={"after": f"{dal}T00:00:00", "before": f"{al}T23:59:59",
                                           "per_page": 100, "page": n, "orderby": "date", "order": "desc",
                                           "_fields": "link"})
            try:
                voci = r.json() if r is not None and r.status_code == 200 else []
            except ValueError:
                voci = []
            urls += [v["link"] for v in voci if v.get("link")]
            if not voci or n >= int(r.headers.get("X-WP-TotalPages", 1)):
                break
        urls = [u for u in dict.fromkeys(urls) if self.e_articolo(u)]
        log(f"  La Verità: API di WordPress, {len(urls)} articoli nel periodo")
        avviso = (f"La Verità: l'archivio interrogabile per data parte dal dicembre 2018; per i giorni precedenti "
                  f"usare --fonte wayback") if dal < self.INIZIO_API else ""
        return [SorgenteURL("API REST di WordPress per data", urls, avviso)]


class Manifesto(Testata):
    elenchi_prova = ("https://ilmanifesto.it/sezioni/politica",)
    chiave, nome, dominio = "manifesto", "il manifesto", "ilmanifesto.it"
    indice = "https://ilmanifesto.it/sitemap_index.xml"
    re_articolo = re.compile(
        r"^https://ilmanifesto\.it/(?!edizioni|lettere|topics/|tags/|sezioni/|abbonamenti|autori/)"
        r"[a-z0-9]+(?:-[a-z0-9]+){3,}/?$")
    note_ricerca_data = ("sitemap degli articoli filtrate per data di modifica (che sul manifesto coincide "
                         "con la pubblicazione, entro tre giorni); molti articoli sono "
                         "riservati agli abbonati e possono risultare come testo parziale")

    RUMORE = re.compile(r"^(dalla parte del torto|gratis per sempre|registrati|aggiornamenti$|"
                        r"\d{2}/\d{2}/\d{4}, \d{2}:\d{2} articolo aggiornato)", re.I)

    BIOGRAFIA = re.compile(r"^(giornalista|un[a']? giornalista|nat[oa] a|storic[oa]|cronista|scrittric|scrittore|"
                           r"autore|autrice|reporter|fotograf|docente|ricercat|insegna|vive a|lavora |"
                           r"collabora|si occupa)|si occupa (di|per lo più)|ha scritto (alcuni|diversi|numerosi)", re.I)

    def estrai(self, html, url):
        art = super().estrai(html, url)
        par = art.testo.split("\n")
        # riassunto generato da un'intelligenza artificiale: non è testo giornalistico e va tolto
        sintesi = set()
        for k, p in enumerate(par):
            if p.strip().lower().startswith("generato da") and k + 1 < len(par):
                sintesi.add(par[k + 1].strip())
        tenuti, salta = [], 0
        for k, p in enumerate(par):
            t = p.strip()
            if t.lower().startswith("in edicola il"):      # riquadro promozionale: titolo, descrizione, data
                for _ in range(2):
                    if tenuti and len(tenuti[-1]) < 250:
                        tenuti.pop()
                continue
            if t in sintesi or t.lower() in ("l'articolo in breve", "l’articolo in breve") or \
                    t.lower().startswith("generato da") or self.RUMORE.search(t):
                continue
            tenuti.append(p)
        # negli articoli riservati la pagina mostra, al posto del testo, la scheda biografica dell'autore
        if art.accesso_libero is False and sum(map(len, tenuti)) < 1500:
            tenuti = [p for p in tenuti if not self.BIOGRAFIA.search(p.strip())]
        art.testo = "\n".join(dict.fromkeys(tenuti))     # toglie anche i paragrafi ripetuti
        return self.valuta(art)

    def piano_per_data(self, rete, dal, al, log, parole=None):
        urls = SM.per_lastmod(rete, self.indice, r"/sitemap-articoli/\d+\.xml$", dal, lambda u: True, al, margine=3)
        log(f"  il manifesto: {len(urls)} articoli candidati")
        return [SorgenteURL("sitemap degli articoli", urls)]


NUOVE = (IlPost(), Libero(), Manifesto(), Mattino(), Corriere(), Repubblica(), LaStampa(),
         Messaggero(), Verita(), Sole24Ore())
