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
        if not sorgenti[0].urls:   # riserva: sitemap news con le sole uscite recenti
            urls, minima = SM.per_data_pubblicazione(rete, [self.news], dal, al, self.e_articolo)
            sorgenti = [SorgenteURL("sitemap news", urls, _avviso(self.nome, minima, dal))]
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


class Libero(_Mensile):
    elenchi_prova = ("https://www.liberoquotidiano.it/news/italia/",)
    chiave, nome, dominio = "libero", "Libero", "liberoquotidiano.it"
    modello_file = "https://www.liberoquotidiano.it/sitemap/Articolo-{anno}-{mese}.xml"
    re_articolo = re.compile(r"^https://www\.liberoquotidiano\.it/[a-z]+/.*/\d{5,}/[^/]+/?$")
    note_ricerca_data = "sitemap mensili dal 2006; la data esatta si legge in ogni articolo"


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
    indice = "https://www.laverita.info/sitemap_index.xml"
    re_articolo = re.compile(
        r"^https://www\.laverita\.info/(?:(?!video/|podcast|author/|tag/|category/|edicola|feed|page/)"
        r"[a-z0-9-]+/[a-z0-9-]+/?|[a-z0-9-]+-\d{9,}\.html)$")
    selettori_corpo = (".lv-article__body", ".article-body__text")
    note_ricerca_data = ("fino al giugno 2026 le vecchie sitemap ordinate per data di pubblicazione; dopo la "
                         "migrazione del sito le sitemap degli articoli filtrate per data di modifica (entro dieci "
                         "giorni dalla fine del periodo), con verifica della data su ogni articolo")

    MIGRAZIONE = date(2026, 7, 1)
    VECCHIO_INDICE = "https://www.laverita.info/sitemap.xml"

    def piano_per_data(self, rete, dal, al, log, parole=None):
        sorgenti = []
        if dal < self.MIGRAZIONE:
            urls = self.archivio_precedente(rete, dal, min(al, self.MIGRAZIONE), log)
            sorgenti.append(SorgenteURL("archivio precedente alla migrazione (sitemap per data)", urls))
        if al >= self.MIGRAZIONE - timedelta(days=10):
            urls = SM.per_lastmod(rete, self.indice, r"/post-sitemap\d*\.xml$", max(dal, self.MIGRAZIONE),
                                  self.e_articolo, al, margine=10)
            sorgenti.append(SorgenteURL("sitemap degli articoli", urls))
        log(f"  La Verità: {sum(len(s.urls) for s in sorgenti)} articoli candidati")
        return sorgenti

    def archivio_precedente(self, rete, dal, al, log):
        """Le vecchie sitemap (feeds/sitemaps/sitemap_N.xml, 250 articoli ciascuna) sono ordinate per
        identificativo, cioè per data di pubblicazione, dal più recente (N=1) al più vecchio; la loro data
        di modifica invece non è affidabile per gli anni più vecchi. La data vera si legge quindi da pochi
        articoli campione, con ricerche binarie prima sui file e poi dentro i file di confine."""
        files = sorted((loc for loc, _ in SM.leggi_indice(rete, self.VECCHIO_INDICE)
                        if re.search(r"/feeds/sitemaps/sitemap_\d+\.xml$", loc)),
                       key=lambda u: int(re.search(r"_(\d+)\.xml$", u).group(1)))
        if not files:
            return []
        voci, date_art = {}, {}

        def urls_file(i):
            if i not in voci:
                voci[i] = [u for u, _, _ in SM.leggi_urlset(rete, files[i]) if self.e_articolo(u)]
            return voci[i]

        def data_articolo(u):
            if u not in date_art:
                r = rete.get(u, cache=True)
                try:
                    date_art[u] = self.estrai(r.text, u).giorno() if r is not None and r.status_code == 200 else None
                except Exception:
                    date_art[u] = None
            return date_art[u]

        def piu_vecchia(i):
            for u in reversed(urls_file(i)[-3:]):      # l'ultimo articolo del file, o uno vicino
                g = data_articolo(u)
                if g:
                    return g
            return None

        def primo(n, cond):                            # primo indice in [0, n) per cui cond è vera
            lo, hi = 0, n
            while lo < hi:
                mid = (lo + hi) // 2
                if cond(mid):
                    hi = mid
                else:
                    lo = mid + 1
            return lo

        vecchia_ok = lambda i: (lambda g: g is None or g <= al)(piu_vecchia(i))
        f_inizio = primo(len(files), vecchia_ok)
        f_fine = f_inizio + primo(len(files) - f_inizio, lambda k: (lambda g: g is None or g < dal)(piu_vecchia(f_inizio + k)))
        f_fine = min(f_fine, len(files) - 1)
        candidati = [u for i in range(f_inizio, f_fine + 1) for u in urls_file(i)]

        def data_k(k):
            return data_articolo(candidati[k])
        a = primo(len(candidati), lambda k: (lambda g: g is None or g <= al)(data_k(k)))
        b = primo(len(candidati), lambda k: (lambda g: g is not None and g < dal)(data_k(k)))
        log(f"  La Verità: archivio precedente, sitemap {f_inizio + 1}-{f_fine + 1} di {len(files)}, "
            f"{max(0, b - a)} articoli nel periodo")
        return candidati[a:b]


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
