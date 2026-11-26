"""Testate di videogiochi e recensioni, scritte sulla ricognizione del 25 novembre 2026 (robots.txt, API di
WordPress, sitemap, prova di scaricamento di un articolo con lo User-Agent dello strumento).

Quattro famiglie, tutte senza reverse-api-engineer:
- sitemap mensili o annuali riconoscibili dal nome (Valnet: Polygon, TheGamer, GameRant; Future: PC Gamer,
  GamesRadar+; ReedPop: Eurogamer, Rock Paper Shotgun, GamesIndustry.biz; IGN; Kotaku; Game Developer):
  si leggono solo i file del periodo e si tengono le voci modificate nel periodo o nei MARGINE giorni successivi;
- sitemap numerate in ordine cronologico (VGC, IGN Italia, Everyeye, Spaziogames, GameSource, Game Informer):
  ricerca binaria del primo file utile, come per le testate venezuelane;
- sitemap a file fissi (Multiplayer.it);
- API REST di WordPress aperta (Gamereactor Italia): per data e per parola.

Non incluse (vedi schede.ESCLUSE): GameSpot, Destructoid e GamesVillage (protezione anti-bot, 403 allo
strumento), Eurogamer Italia (il dominio rimanda a eurogamer.net). OpenCritic e Metacritic sono aggregatori di
voti: il dato utile sono i punteggi, non gli articoli, e richiederebbero una modalità a parte."""
import re
from datetime import date, timedelta

from .base import Testata
from .napoli import _WordPress, _giorno
from .seconda_ondata import _avviso
from .venezuela import _SitemapOrdinate, _Titolo
from .. import comune as C
from .. import sitemap as SM
from ..modello import SorgenteURL

MESI_EN = ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
           "november", "december")


def _re(dominio, percorso=r"(?:[^/?#]+/)*[^/?#]*-[^/?#]*/?"):
    """Indirizzi degli articoli: dominio e almeno uno slug con un trattino (esclude home e sezioni)."""
    return re.compile(rf"^https?://(?:www\.)?{re.escape(dominio)}/(?!authors?/|autori/|tag/|games/|search){percorso}$")


def _mesi(dal, al):
    out, g = [], date(dal.year, dal.month, 1)
    while g <= al:
        out.append((g.year, g.month))
        g = date(g.year + (g.month == 12), g.month % 12 + 1, 1)
    return out


# ------------------------------------------------------------------ sitemap per mese o per anno
class _Periodiche(_Titolo, Testata):
    """Una sitemap per mese (RE_FILE con gruppo AAAA-MM) o per anno (gruppo AAAA), elencate nell'INDICE o
    costruite da MODELLO. Si leggono solo i file del periodo; con FILTRO_LASTMOD si tengono le voci modificate
    tra `dal` e `al` + MARGINE giorni (prima quelle nel periodo); la data esatta si verifica sull'articolo."""
    lingua = "en"
    INDICE = ""
    RE_FILE = r"sitemap-(\d{4}-\d{2})\.xml$"
    MODELLI = ()            # in alternativa all'indice: URL con {anno}, {mese} (01-12) o {mese_en} (january…)
    PER_ANNO = False
    FILTRO_LASTMOD = True
    MARGINE = 7
    INIZIO = None
    paginazione = None

    def pagina_elenco(self, base, n):
        return base if n == 1 else None

    def _chiavi(self, dal, al):
        if self.PER_ANNO:
            return [str(a) for a in range(al.year, dal.year - 1, -1)]
        return [f"{a}-{m:02d}" for a, m in reversed(_mesi(dal, al))]

    def _files(self, rete, dal, al):
        chiavi = self._chiavi(dal, al)
        if self.MODELLI:
            return [m.format(anno=k[:4], mese=k[5:], mese_en=MESI_EN[int(k[5:]) - 1] if len(k) > 4 else "")
                    for k in chiavi for m in self.MODELLI]
        trovati = {}
        for loc, _ in SM.leggi_indice(rete, self.INDICE):
            m = re.search(self.RE_FILE, loc)
            if m and m.group(1) in chiavi:
                trovati.setdefault(m.group(1), []).append(loc)
        return [f for k in chiavi for f in trovati.get(k, [])]

    def piano_per_data(self, rete, dal, al, log, parole=None):
        files = self._files(rete, dal, al)
        tetto = al + timedelta(days=self.MARGINE)
        voci = {}
        for f in files:
            for u, lastmod, pub in SM.leggi_urlset(rete, f):
                if not self.e_articolo(u):
                    continue
                g = C.data_da_url(u) or _giorno(pub or lastmod)
                if not self.FILTRO_LASTMOD:
                    voci[u] = g or al
                elif g and dal <= g <= tetto:
                    voci[u] = g
        urls = sorted(voci, key=lambda u: (voci[u] > al, -voci[u].toordinal()))
        cosa = "annuali" if self.PER_ANNO else "mensili"
        log(f"  {self.nome}: {len(files)} sitemap {cosa}, {len(urls)} articoli da verificare")
        avvisi = [_avviso(self.nome, self.INIZIO, dal)]
        if not files:
            avvisi.append(f"{self.nome}: nessuna sitemap per il periodo richiesto")
        return [SorgenteURL(f"sitemap {cosa} ({len(files)})", urls, "; ".join(a for a in avvisi if a))]


class IGN(_Periodiche):
    chiave, nome, dominio = "ign", "IGN", "ign.com"
    MODELLI = ("https://www.ign.com/rss/sitemap-articles-{anno}.xml",)
    PER_ANNO = True
    INIZIO = date(1996, 1, 1)
    re_articolo = re.compile(r"^https://www\.ign\.com/articles/.+")
    note_ricerca_data = ("sitemap annuali degli articoli dal 1996 (recensioni, notizie, guide), filtrate per data "
                         "di modifica")


class Eurogamer(_Periodiche):
    chiave, nome, dominio = "eurogamer", "Eurogamer", "eurogamer.net"
    MODELLI = ("https://www.eurogamer.net/sitemap-{anno}.xml",)
    PER_ANNO = True
    INIZIO = date(1999, 1, 1)
    re_articolo = re.compile(r"^https://www\.eurogamer\.net/(?!games/|authors/|tags?/)[a-z0-9-]+-[a-z0-9-]+$")
    note_ricerca_data = ("sitemap annuali dal 1999, filtrate per data di modifica (gli articoli aggiornati molto "
                         "dopo l'uscita possono finire nell'anno dell'aggiornamento)")


class RockPaperShotgun(Eurogamer):
    chiave, nome, dominio = "rockpapershotgun", "Rock Paper Shotgun", "rockpapershotgun.com"
    MODELLI = ("https://www.rockpapershotgun.com/sitemap-{anno}.xml",)
    INIZIO = date(2007, 1, 1)
    re_articolo = re.compile(r"^https://www\.rockpapershotgun\.com/(?!games/|authors/|tags?/)[a-z0-9-]+-[a-z0-9-]+$")
    note_ricerca_data = "sitemap annuali dal 2007, filtrate per data di modifica"


class GamesIndustry(Eurogamer):
    chiave, nome, dominio = "gamesindustry", "GamesIndustry.biz", "gamesindustry.biz"
    MODELLI = ("https://www.gamesindustry.biz/sitemap-{anno}.xml",)
    INIZIO = date(2000, 1, 1)
    re_articolo = re.compile(r"^https://www\.gamesindustry\.biz/(?!video-games/|authors/|tags?/)[a-z0-9-]+-[a-z0-9-]+$")
    note_ricerca_data = "sitemap annuali, filtrate per data di modifica (notizie sull'industria del videogioco)"


class _Valnet(_Periodiche):
    """Polygon, TheGamer, GameRant: sitemap-AAAA-MM-partN-articles.xml."""
    RE_FILE = r"sitemap-(\d{4}-\d{2})-part\d+-articles\.xml$"


class Polygon(_Valnet):
    chiave, nome, dominio = "polygon", "Polygon", "polygon.com"
    INDICE = "https://www.polygon.com/sitemap.xml"
    INIZIO = date(2023, 3, 1)
    re_articolo = _re(dominio)
    note_ricerca_data = "sitemap mensili degli articoli (circa gli ultimi tre anni e mezzo), filtrate per data di modifica"


class TheGamer(_Valnet):
    chiave, nome, dominio = "thegamer", "TheGamer", "thegamer.com"
    INDICE = "https://www.thegamer.com/sitemap.xml"
    INIZIO = date(2023, 1, 1)
    re_articolo = _re(dominio)
    note_ricerca_data = "sitemap mensili degli articoli (circa gli ultimi quattro anni), filtrate per data di modifica"


class GameRant(_Valnet):
    chiave, nome, dominio = "gamerant", "GameRant", "gamerant.com"
    INDICE = "https://gamerant.com/sitemap.xml"
    INIZIO = date(2023, 1, 1)
    re_articolo = _re(dominio)
    note_ricerca_data = ("sitemap mensili degli articoli, filtrate per data di modifica; molti articoli al giorno "
                         "(conviene --cerca-in titolo o un periodo breve)")


class _Future(_Periodiche):
    """PC Gamer e GamesRadar+: sitemap-AAAA-MM.xml nell'indice principale."""
    RE_FILE = r"/sitemap-(\d{4}-\d{2})\.xml$"


class PCGamer(_Future):
    chiave, nome, dominio = "pcgamer", "PC Gamer", "pcgamer.com"
    INDICE = "https://www.pcgamer.com/sitemap.xml"
    INIZIO = date(2005, 6, 1)
    re_articolo = re.compile(r"^https://www\.pcgamer\.com/(?!uk/|au/|authors?/|tag/)(?:[^/?#]+/)*[^/?#]*-[^/?#]*/?$")
    note_ricerca_data = "sitemap mensili dal 2005 (fitte dal 2008), filtrate per data di modifica"


class GamesRadar(_Future):
    chiave, nome, dominio = "gamesradar", "GamesRadar+", "gamesradar.com"
    INDICE = "https://www.gamesradar.com/sitemap.xml"
    INIZIO = date(1999, 11, 1)
    re_articolo = re.compile(r"^https://www\.gamesradar\.com/(?!uk/|au/|authors?/|tag/)(?:[^/?#]+/)*[^/?#]*-[^/?#]*/?$")
    note_ricerca_data = "sitemap mensili dal 1999, filtrate per data di modifica (anche cinema, TV e fumetti)"


class Kotaku(_Periodiche):
    chiave, nome, dominio = "kotaku", "Kotaku", "kotaku.com"
    INDICE = "https://kotaku.com/sitemap_index.xml"
    RE_FILE = r"post-sitemap-(\d{4}-\d{2})\.xml$"
    INIZIO = date(2005, 8, 1)
    # dopo il passaggio di proprietà del 2025 le date di modifica sono state riscritte in blocco: si tiene tutto
    # il mese e la data si verifica sull'articolo
    FILTRO_LASTMOD = False
    re_articolo = re.compile(r"^https://kotaku\.com/[a-z0-9-]+-\d{6,}$")
    note_ricerca_data = ("sitemap mensili dal 2005; le date di modifica non sono affidabili, quindi si verifica "
                         "ogni articolo del mese (lento sui periodi brevi: circa 300 articoli al mese)")


class GameDeveloper(_Periodiche):
    chiave, nome, dominio = "gamedeveloper", "Game Developer", "gamedeveloper.com"
    MODELLI = ("https://www.gamedeveloper.com/news/archive/{anno}/{mese_en}.xml",
               "https://www.gamedeveloper.com/article/archive/{anno}/{mese_en}.xml")
    INIZIO = date(1999, 1, 1)
    re_articolo = re.compile(r"^https://www\.gamedeveloper\.com/(?!author/|program/|search)[a-z0-9-]+/[a-z0-9-]+-[a-z0-9-]+$")
    note_ricerca_data = ("sitemap mensili di notizie e articoli dal 1999 (ex Gamasutra), filtrate per data; "
                         "testata di settore, in inglese")


# ------------------------------------------------------------------ sitemap numerate in ordine cronologico
class _Ordinate(_SitemapOrdinate):
    lingua = "it"


class VGC(_Ordinate):
    chiave, nome, dominio = "vgc", "Video Games Chronicle", "videogameschronicle.com"
    lingua = "en"
    INDICE = "https://www.videogameschronicle.com/sitemap.xml"
    RE_FILE = r"/post-sitemap(\d*)\.xml$"
    INIZIO = date(2019, 1, 1)
    re_articolo = re.compile(r"^https://www\.videogameschronicle\.com/(?:news|features|review|reviews|guide|"
                             r"video|opinion)/[a-z0-9-]+/?$")
    note_ricerca_data = ("sitemap degli articoli in ordine di pubblicazione dal 2019; le date di modifica arrivano "
                         "settimane dopo l'uscita, quindi gli estremi del periodo si trovano con una ricerca binaria "
                         "sulla data dichiarata dagli articoli (circa 30 richieste, 2-3 minuti con la pausa di 5 "
                         "secondi chiesta dal robots.txt)")

    def piano_per_data(self, rete, dal, al, log, parole=None):
        """Le voci delle sitemap, concatenate, sono in ordine di pubblicazione: si cercano con una ricerca binaria
        la prima uscita dal `dal` in poi e la prima dopo `al`, leggendo la data dell'articolo stesso."""
        fs = self._files(rete)
        if not fs:
            return [SorgenteURL("sitemap degli articoli", [], f"{self.nome}: sitemap degli articoli non raggiungibili")]
        cache_f, cache_d = {}, {}

        def voci(i):
            if i not in cache_f:
                cache_f[i] = [u for u, _, _ in SM.leggi_urlset(rete, fs[i]) if self.e_articolo(u)]
            return cache_f[i]

        def data(u):
            if u not in cache_d:
                r = rete.get(u)
                g = None
                if r is not None and r.status_code == 200:
                    d = C.parse_data(self.estrai(r.text, u).data)
                    g = d.date() if d else None
                cache_d[u] = g
            return cache_d[u]

        def primo_file(limite):     # ultimo file il cui primo articolo esce prima di `limite`
            lo, hi = 0, len(fs) - 1
            while lo < hi:
                mid = (lo + hi + 1) // 2
                v = voci(mid)
                g = data(v[0]) if v else None
                if g is not None and g < limite:
                    lo = mid
                else:
                    hi = mid - 1
            return lo

        def prima_posizione(lista, limite):   # prima voce pubblicata il giorno `limite` o dopo
            lo, hi = 0, len(lista)
            while lo < hi:
                mid = (lo + hi) // 2
                g = data(lista[mid])
                if g is not None and g < limite:
                    lo = mid + 1
                else:
                    hi = mid
            return lo

        dopo = al + timedelta(days=1)
        a, b = primo_file(dal), primo_file(dopo)
        lista = [u for i in range(a, min(b + 1, len(fs) - 1) + 1) for u in voci(i)]
        i, j = prima_posizione(lista, dal), prima_posizione(lista, dopo)
        urls = list(reversed(lista[i:j]))
        log(f"  {self.nome}: {b - a + 1} sitemap lette, {len(cache_d)} articoli consultati per la ricerca binaria, "
            f"{len(urls)} articoli nel periodo")
        return [SorgenteURL("sitemap in ordine di pubblicazione con ricerca binaria sulle date", urls,
                            _avviso(self.nome, self.INIZIO, dal, "le sitemap"))]


class IGNItalia(_Ordinate):
    chiave, nome, dominio = "ignitalia", "IGN Italia", "it.ign.com"
    INDICE = "https://it.ign.com/sitemap.xml"
    RE_FILE = r"/sitemap-article-(\d+)\.xml$"
    re_articolo = re.compile(r"^https://it\.ign\.com/[^/]+/\d+/(?:[a-z-]+/)?[a-z0-9-]+$")
    note_ricerca_data = "sitemap degli articoli numerate (circa 100.000 articoli), filtrate per data di modifica"


class Everyeye(_Ordinate):
    chiave, nome, dominio = "everyeye", "Everyeye.it", "everyeye.it"
    INDICE = "https://www.everyeye.it/sitemaps/sitemap.xml"
    RE_FILE = r"/contenuti-videogioco-(\d+)\.xml$"
    re_articolo = re.compile(r"^https://www\.everyeye\.it/(?:notizie|articoli)/[a-z0-9-]+-\d+\.html$")
    note_ricerca_data = ("sitemap dei contenuti in ordine cronologico (notizie, recensioni, speciali), filtrate "
                         "per data di modifica")


class Spaziogames(_Ordinate):
    chiave, nome, dominio = "spaziogames", "Spaziogames", "spaziogames.it"
    INDICE = "https://www.spaziogames.it/sitemap.xml"
    RE_FILE = r"/post-sitemap(\d+)\.xml$"
    AFFIDABILE_DAL = date(2018, 6, 1)
    re_articolo = re.compile(r"^https://www\.spaziogames\.it/(?:notizie|articoli|recensioni|speciali|anteprime|"
                             r"guide)/[A-Za-z0-9-]+$")
    note_ricerca_data = ("sitemap degli articoli in ordine cronologico; date di modifica affidabili dal giugno "
                         "2018 (prima riportano il 1980)")
    MODELLO = "https://www.spaziogames.it/post-sitemap{}.xml"
    NOTO = 22

    def _files(self, rete):
        """L'indice a volte risponde con due sole voci: in quel caso i file si leggono per numero, fino al primo
        che manca."""
        fs = super()._files(rete)
        if len(fs) >= 5:
            return fs
        def esiste(n):
            r = rete.get(self.MODELLO.format(n))
            return r is not None and r.status_code == 200 and "<urlset" in r.text[:2000]

        n = self.NOTO                       # ultimo file visto il 25 novembre 2026: si sale o si scende da lì
        if esiste(n):
            while esiste(n + 1):
                n += 1
        else:
            while n > 1 and not esiste(n - 1):
                n -= 1
            n -= 1
        return [self.MODELLO.format(i) for i in range(1, n + 1)]


class GameInformer(_Ordinate):
    chiave, nome, dominio = "gameinformer", "Game Informer", "gameinformer.com"
    lingua = "en"
    INDICE = "https://gameinformer.com/sitemaps/articles/sitemap.xml"
    RE_FILE = r"/articles/sitemap-(\d+)\.xml$"
    date_nell_url = True
    # le recensioni hanno sitemap a parte e, dal nuovo sito, indirizzi senza data
    ALTRE = ("https://gameinformer.com/sitemaps/reviews/sitemap.xml",
             "https://gameinformer.com/sitemaps/previews/sitemap-1.xml",
             "https://gameinformer.com/sitemaps/previews/sitemap-2.xml")
    re_articolo = re.compile(r"^https://gameinformer\.com/(?!sitemaps/|search)(?:[^/?#]+/)*[^/?#]*-[^/?#]*$|"
                             r"^https://gameinformer\.com/games/.+/review$")
    note_ricerca_data = ("sitemap degli articoli in ordine cronologico dal 2001 (data nell'indirizzo), più le "
                         "sitemap di recensioni e anteprime filtrate per data di modifica")

    def piano_per_data(self, rete, dal, al, log, parole=None):
        sorgenti = super().piano_per_data(rete, dal, al, log, parole)
        noti = set(sorgenti[0].urls)
        tetto = al + timedelta(days=self.MARGINE)
        extra = []
        for f in self.ALTRE:
            for u, lm, pub in SM.leggi_urlset(rete, f):
                g = C.data_da_url(u) or _giorno(pub or lm)
                if g and dal <= g <= tetto and u not in noti and self.e_articolo(u):
                    extra.append(u)
        log(f"  {self.nome}: {len(extra)} recensioni e anteprime da verificare")
        return sorgenti + [SorgenteURL("sitemap di recensioni e anteprime", list(dict.fromkeys(extra)))]


class GameSource(_Ordinate):
    chiave, nome, dominio = "gamesource", "GameSource", "gamesource.it"
    INDICE = "https://www.gamesource.it/sitemap_index.xml"
    SERIE = ("notizie", "recensioni", "anteprime", "editoriali")
    re_articolo = re.compile(r"^https://www\.gamesource\.it/(?:notizie|recensioni|anteprime|editoriali)/[a-z0-9-]+/$")
    note_ricerca_data = ("sitemap numerate per tipo (notizie, recensioni, anteprime, editoriali) in ordine "
                         "cronologico dal 2008, filtrate per data di modifica")

    def piano_per_data(self, rete, dal, al, log, parole=None):
        sorgenti = []
        for s in self.SERIE:
            self.RE_FILE = rf"/{s}-sitemap(\d*)\.xml$"
            sorgenti += super().piano_per_data(rete, dal, al, log, parole)
        return sorgenti


# ------------------------------------------------------------------ sitemap a file fissi
class Multiplayer(_Titolo, Testata):
    chiave, nome, dominio = "multiplayer", "Multiplayer.it", "multiplayer.it"
    FILES = ("https://multiplayer.it/sitemap-articles.xml", "https://multiplayer.it/sitemap-articles.2.xml",
             "https://multiplayer.it/sitemap-notizie.xml")
    MARGINE = 7
    NOTIZIE_GIORNI = 90
    paginazione = None
    re_articolo = re.compile(r"^https://multiplayer\.it/(?:articoli|notizie|recensioni|anteprime|speciali)/"
                             r"[a-z0-9-]+\.html$")
    note_ricerca_data = ("sitemap di articoli e recensioni (archivio completo) e di notizie (solo gli ultimi tre "
                         "mesi circa), filtrate per data di modifica")

    def pagina_elenco(self, base, n):
        return base if n == 1 else None

    def piano_per_data(self, rete, dal, al, log, parole=None):
        tetto = al + timedelta(days=self.MARGINE)
        voci = {}
        for f in self.FILES:
            for u, lm, pub in SM.leggi_urlset(rete, f):
                g = _giorno(pub or lm)
                if g and dal <= g <= tetto and self.e_articolo(u):
                    voci[u] = g
        urls = sorted(voci, key=lambda u: (voci[u] > al, -voci[u].toordinal()))
        log(f"  {self.nome}: {len(urls)} articoli da verificare")
        limite = date.today() - timedelta(days=self.NOTIZIE_GIORNI)
        avviso = (f"{self.nome}: le notizie brevi sono nelle sitemap solo per gli ultimi tre mesi circa; prima "
                  f"del {limite} si trovano articoli, recensioni e speciali") if dal < limite else ""
        return [SorgenteURL("sitemap di articoli e notizie", urls, avviso)]


# ------------------------------------------------------------------ API REST di WordPress
class Gamereactor(_Titolo, _WordPress):
    chiave, nome, dominio = "gamereactor", "Gamereactor Italia", "gamereactor.it"
    API = "https://www.gamereactor.it/wp-json/wp/v2/posts"
    re_articolo = re.compile(r"^https://www\.gamereactor\.it/[a-z0-9-]+-[a-z0-9-]+/?$")
    note_ricerca_data = "API REST di WordPress con filtro per date (circa 118.000 articoli)"


# ------------------------------------------------------------------ in spagnolo e Hookshot (25 novembre 2026, sera)
from .generiche import _FileFissi, _Intervalli, re_dominio  # noqa: E402


class EurogamerEs(Eurogamer):
    chiave, nome, dominio = "eurogameres", "Eurogamer España", "eurogamer.es"
    lingua = "es"
    MODELLI = ("https://www.eurogamer.es/sitemap-{anno}.xml",)
    INIZIO = date(2005, 1, 1)
    re_articolo = re.compile(r"^https://www\.eurogamer\.es/(?!games/|authors/|tags?/)[a-z0-9-]+-[a-z0-9-]+$")
    note_ricerca_data = "sitemap annuali, filtrate per data di modifica"


class IGNEspana(IGNItalia):
    chiave, nome, dominio = "ignespana", "IGN España", "es.ign.com"
    lingua = "es"
    INDICE = "https://es.ign.com/sitemap.xml"
    re_articolo = re.compile(r"^https://es\.ign\.com/[^/]+/\d+/(?:[a-z-]+/)?[a-z0-9-]+$")
    note_ricerca_data = "sitemap degli articoli numerate, filtrate per data di modifica"


class GamereactorEs(Gamereactor):
    chiave, nome, dominio = "gamereactores", "Gamereactor España", "gamereactor.es"
    lingua = "es"
    API = "https://www.gamereactor.es/wp-json/wp/v2/posts"
    re_articolo = re.compile(r"^https://www\.gamereactor\.es/[a-z0-9-]+-[a-z0-9-]+/?$")
    note_ricerca_data = "API REST di WordPress con filtro per date (circa 105.000 articoli)"


class TresDJuegos(_Intervalli):
    chiave, nome, dominio = "3djuegos", "3DJuegos", "3djuegos.com"
    lingua = "es"
    INDICI = ("https://www.3djuegos.com/sitemap_index.xml",)
    RE_FILE = r"/noticias/(?P<a>\d{4})/(?P<m>\d{2})/sitemap\.xml$"
    re_articolo = re.compile(r"^https://www\.3djuegos\.com/.+/noticias/[^/]+$")
    note_ricerca_data = ("sitemap mensili delle notizie (circa 1.200 al mese), filtrate per data di modifica; "
                         "recensioni e speciali non hanno una sitemap per data")


class Vandal(_FileFissi):
    chiave, nome, dominio = "vandal", "Vandal", "vandal.elespanol.com"
    lingua = "es"
    FILES = ("https://vandal.elespanol.com/noticias2.xml",)
    re_articolo = re.compile(r"^https://vandal\.elespanol\.com/noticia/\d+/[^/]+/?$")
    note_ricerca_data = "solo le notizie recenti (sitemap news); il passato con --fonte wayback"


class HobbyConsolas(_FileFissi):
    chiave, nome, dominio = "hobbyconsolas", "Hobby Consolas", "hobbyconsolas.com"
    lingua = "es"
    FILES = ("https://www.hobbyconsolas.com/sitemap-google-news.xml",
             "https://www.hobbyconsolas.com/sitemap-noticias-incremental.xml",
             "https://www.hobbyconsolas.com/sitemap-noticias-latest.xml")
    re_articolo = re.compile(r"^https://www\.hobbyconsolas\.com/.+_\d+_\d+\.html$")
    note_ricerca_data = "solo le uscite recenti (circa due settimane); il passato con --fonte wayback"


class _Hookshot(_Periodiche):
    """Push Square, Pure Xbox, Nintendo Life: sitemap annuali degli articoli; Crawl-delay 5."""
    PER_ANNO = True
    note_ricerca_data = ("sitemap annuali degli articoli, filtrate per data di modifica; il robots.txt chiede 5 "
                         "secondi tra le richieste")

    @property
    def MODELLI(self):
        return (f"https://www.{self.dominio}/sitemap.articles.{{anno}}.xml",)

    @property
    def re_articolo(self):
        return re.compile(rf"^https://www\.{re.escape(self.dominio)}/(?:news|reviews|features|guides|previews|"
                          rf"talking-point|feature|review|guide)/(?:\d{{4}}/\d{{2}}/)?[a-z0-9_-]+$")


class PushSquare(_Hookshot):
    chiave, nome, dominio = "pushsquare", "Push Square", "pushsquare.com"
    INIZIO = date(2008, 7, 1)


class PureXbox(_Hookshot):
    chiave, nome, dominio = "purexbox", "Pure Xbox", "purexbox.com"
    INIZIO = date(2008, 1, 1)


class NintendoLife(_Hookshot):
    chiave, nome, dominio = "nintendolife", "Nintendo Life", "nintendolife.com"
    INIZIO = date(2006, 1, 1)


VIDEOGIOCHI = (IGN(), IGNItalia(), Eurogamer(), Polygon(), Kotaku(), PCGamer(), RockPaperShotgun(), GamesRadar(),
               GameInformer(), VGC(), TheGamer(), GameRant(), Multiplayer(), Everyeye(), Spaziogames(),
               Gamereactor(), GameSource(), GamesIndustry(), GameDeveloper(),
               EurogamerEs(), IGNEspana(), GamereactorEs(), TresDJuegos(), Vandal(), HobbyConsolas(), PushSquare(),
               PureXbox(), NintendoLife())


def _registra_motori():
    from .ricerca import MOTORI
    for t in VIDEOGIOCHI:
        if isinstance(t, _WordPress):
            MOTORI[t.chiave] = (t.motore_ricerca, "API REST di WordPress con ricerca e filtro per date", False)


_registra_motori()
