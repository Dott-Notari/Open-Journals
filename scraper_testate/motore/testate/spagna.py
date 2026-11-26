"""Testate spagnole, scritte sulla ricognizione del 25 novembre 2026 (robots.txt, API, sitemap, prova di
scaricamento di un articolo con lo User-Agent dello strumento), senza reverse-api-engineer.

Non incluse (vedi schede.ESCLUSE): El País (DataDome, già esclusa), Cadena SER (anti-bot), El Periódico (406
allo User-Agent dichiarato), RTVE (il robots.txt esclude i file .xml, comprese le sitemap), La Voz de Galicia
(Crawl-delay di 60 secondi), La Vanguardia (archivio dietro CAPTCHA). El Confidencial solo dai feed RSS; La Razón
dalle sitemap mensili trovate con reverse-api-engineer. El Mundo
è già nel gruppo estere."""
import re
from datetime import date

from .generiche import _FileFissi, _Intervalli, re_dominio
from .base import Testata
from .napoli import _WordPress
from ..comune import giorni
from ..modello import SorgenteURL
from .venezuela import _Titolo


class _Es:
    lingua = "es"


class ABC(_Es, _FileFissi):
    chiave, nome, dominio = "abc", "ABC", "abc.es"
    FILES = ("https://www.abc.es/sitemap.xml",)
    DATA_URL = r"-(?P<a>\d{4})(?P<m>\d{2})(?P<g>\d{2})\d{6}-nt"
    re_articolo = re.compile(r"^https://www\.abc\.es/.+-\d{14}-nts?\.html$")
    note_ricerca_data = "solo le uscite recenti (sitemap news, ultimi giorni); il passato con --fonte wayback"


class _ElDiarioHash(_Es, _Intervalli):
    """eldiario.es e Ara: sitemap mensili sitemap_contents_AAAA_MM_<codice>_NNN.xml."""
    RE_FILE = r"sitemap_contents_(?P<a>\d{4})_(?P<m>\d{2})_"


class ElDiarioEs(_ElDiarioHash):
    chiave, nome, dominio = "eldiarioes", "elDiario.es", "eldiario.es"
    INDICI = ("https://www.eldiario.es/sitemap_index_25b87.xml",)
    INIZIO = date(2012, 9, 1)
    re_articolo = re.compile(r"^https://www\.eldiario\.es/.+_1_\d+\.html$")
    note_ricerca_data = "sitemap mensili dal 2012, filtrate per data di modifica"


class Ara(_ElDiarioHash):
    chiave, nome, dominio = "ara", "Ara", "ara.cat"
    lingua = "ca"
    INDICI = ("https://www.ara.cat/sitemap_index_ee125.xml",)
    INIZIO = date(2010, 11, 1)
    re_articolo = re.compile(r"^https://www\.ara\.cat/.+_1_\d+\.html$")
    note_ricerca_data = "sitemap mensili dal 2010, filtrate per data di modifica (in catalano)"


class VeinteMinutosEs(_Es, _FileFissi):
    chiave, nome, dominio = "20minutoses", "20minutos", "20minutos.es"
    FILES = ("https://www.20minutos.es/sitemap-google-news.xml",
             "https://www.20minutos.es/sitemap-noticias-incremental.xml",
             "https://www.20minutos.es/sitemap-noticias-latest.xml")
    re_articolo = re.compile(r"^https://www\.20minutos\.es/.+_\d+_\d+\.html$")
    note_ricerca_data = "solo le uscite recenti (circa due settimane); il passato con --fonte wayback"


class ElEspanol(_Es, _FileFissi):
    chiave, nome, dominio = "elespanol", "El Español", "www.elespanol.com"   # non vandal.elespanol.com
    FILES = ("https://www.elespanol.com/sitemap_google_news.xml", "https://www.elespanol.com/sitemap.xml")
    DATA_URL = r"/(?P<a>\d{4})(?P<m>\d{2})(?P<g>\d{2})/"
    SOLO_RECENTI = False
    re_articolo = re.compile(r"^https://www\.elespanol\.com/.+/\d{8}/[^/]+/\d+_\d+\.html$")
    note_ricerca_data = ("sitemap news e una sitemap di circa 7.000 articoli scelti dal 2016: copertura parziale "
                         "per gli anni passati, completa solo per gli ultimi giorni")


class Publico(_Es, _Intervalli):
    chiave, nome, dominio = "publico", "Público", "publico.es"
    INDICI = ("https://www.publico.es/sitemap-index.xml",)
    RE_FILE = r"/sitemap-noticias-(?P<a>\d{4})(?P<m>\d{2})\.xml(?:\.gz)?$"
    re_articolo = re_dominio("publico.es")
    note_ricerca_data = ("sitemap mensili delle notizie, filtrate per data di modifica; il robots.txt chiede 5 "
                         "secondi tra le richieste")


class LibertadDigital(_Es, _FileFissi):
    chiave, nome, dominio = "libertaddigital", "Libertad Digital", "libertaddigital.com"
    # l'archivio completo (sitemaps/news.xml) sono 15 file da 12 MB non ordinati per data: troppo pesante;
    # la sitemap «ultimo anno» rimanda a se stessa
    FILES = ("https://www.libertaddigital.com/sitemaps/last-news.xml",
             "https://www.libertaddigital.com/sitemaps/last-news-libremercado.xml")
    DATA_URL = r"/(?P<a>\d{4})-(?P<m>\d{2})-(?P<g>\d{2})/"
    re_articolo = re.compile(r"^https://www\.libertaddigital\.com/.+/\d{4}-\d{2}-\d{2}/[^/]+/?$")
    note_ricerca_data = "solo le uscite recenti (ultimi giorni); il passato con --fonte wayback"


class _WPEs(_Es, _Titolo, _WordPress):
    pass


class OkDiario(_Es, _Titolo, Testata):
    """L'API di WordPress risponde ma ignora il filtro per date: si leggono le pagine d'archivio giornaliere
    /archivos/AAAA/MM/GG/ (paginate con /page/N/), che il robots.txt consente."""
    chiave, nome, dominio = "okdiario", "OkDiario", "okdiario.com"
    re_articolo = re.compile(r"^https://okdiario\.com/(?!archivos/)(?:[a-z0-9-]+/)+[a-z0-9-]+-\d{6,}/?$")
    paginazione = "{base}page/{n}/"
    PAGINE_MAX = 40
    note_ricerca_data = ("pagine d'archivio giornaliere del sito (l'API di WordPress ignora il filtro per date); "
                         "circa 150-300 articoli al giorno")

    def piano_per_data(self, rete, dal, al, log, parole=None):
        urls = []
        for g in reversed(list(giorni(dal, al))):
            base = f"https://okdiario.com/archivos/{g:%Y/%m/%d}/"
            for n in range(1, self.PAGINE_MAX + 1):
                r = rete.get(self.pagina_elenco(base, n))
                if r is None or r.status_code != 200:
                    break
                nuovi = [u for u in self.link_articoli(r.text, base) if u not in urls]
                if not nuovi:
                    break
                urls += nuovi
        log(f"  {self.nome}: pagine d'archivio di {len(list(giorni(dal, al)))} giorni, {len(urls)} articoli da verificare")
        return [SorgenteURL("pagine d'archivio giornaliere", urls)]


class EFE(_WPEs):
    chiave, nome, dominio = "efe", "Agencia EFE", "efe.com"
    API = "https://efe.com/wp-json/wp/v2/posts"
    re_articolo = re.compile(r"^https://(?:www\.)?efe\.com/[a-z0-9-]+/\d{4}-\d{2}-\d{2}/[^/]+/?$")
    note_ricerca_data = "API REST di WordPress con filtro per date (circa 180.000 notizie dell'agenzia)"


class EuropaPress(_Es, _Intervalli):
    chiave, nome, dominio = "europapress", "Europa Press", "europapress.es"
    INDICI = ("https://www.europapress.es/sitemap_index/",)
    RE_FILE = r"/sitemap_diario/(?P<a>\d{4})-(?P<m>\d{2})-(?P<g>\d{2})/$"
    DATA_URL = r"-(?P<a>\d{4})(?P<m>\d{2})(?P<g>\d{2})\d{6}\.html$"
    INIZIO = date(2006, 1, 1)
    re_articolo = re.compile(r"^https://www\.europapress\.es/.+-\d{14}\.html$")
    note_ricerca_data = "sitemap giornaliere dal 2006 (agenzia di stampa), data nell'indirizzo"


class _Vocento(_Es, _FileFissi):
    """Gruppo Vocento: sitemap news e incrementale (circa sei settimane); data e ora nell'indirizzo."""
    DATA_URL = r"-(?P<a>\d{4})(?P<m>\d{2})(?P<g>\d{2})\d{4,6}(?:_amp)?-n"
    note_ricerca_data = "solo le uscite recenti (circa sei settimane); il passato con --fonte wayback"

    @property
    def FILES(self):
        return tuple(f"https://www.{self.dominio}/{f}" for f in ("sitemap.xml", "sitemap.incremental.xml"))

    @property
    def re_articolo(self):
        return re.compile(rf"^https://www\.{re.escape(self.dominio)}/.+-\d{{12,14}}-n[tv]s?\.html$")


class DiarioVasco(_Vocento):
    chiave, nome, dominio = "diariovasco", "El Diario Vasco", "diariovasco.com"


class ElCorreo(_Vocento):
    chiave, nome, dominio = "elcorreo", "El Correo", "elcorreo.com"


class Ideal(_Vocento):
    chiave, nome, dominio = "ideal", "Ideal", "ideal.es"


class DiarioSur(_Vocento):
    chiave, nome, dominio = "diariosur", "Diario Sur", "diariosur.es"


class SurInEnglish(_Vocento):
    chiave, nome, dominio = "surinenglish", "Sur in English", "surinenglish.com"
    lingua = "en"


class ElConfidencial(_Es, _Titolo, Testata):
    """Nessuna sitemap; il robots.txt vieta /hemeroteca/, /archivo/ e /buscar/ (mappatura rae del 26 novembre
    2026). Restano i feed Atom delle sezioni (circa 15 articoli ciascuno), con la data nell'indirizzo."""
    chiave, nome, dominio = "elconfidencial", "El Confidencial", "elconfidencial.com"
    SEZIONI = ("espana", "mundo", "economia", "mercados", "tecnologia", "cultura", "deportes", "sociedad",
               "alma-corazon-vida", "comunicacion", "medioambiente", "vivienda", "empresas", "television", "motor",
               "espana/madrid", "espana/cataluna", "espana/andalucia", "espana/comunidad-valenciana",
               "deportes/futbol", "mercados/finanzas-personales")
    re_articolo = re.compile(r"^https://www\.elconfidencial\.com/(?:[a-z0-9-]+/)+\d{4}-\d{2}-\d{2}/[^/]+/?$")
    paginazione = None
    note_ricerca_data = ("solo le uscite recenti dai feed RSS delle sezioni (circa 15 articoli ciascuno, copertura "
                         "parziale): niente sitemap e il robots.txt vieta l'archivio per data; il passato con "
                         "--fonte wayback")

    def pagina_elenco(self, base, n):
        return base if n == 1 else None

    def piano_per_data(self, rete, dal, al, log, parole=None):
        trovati, minima = {}, None
        for s in self.SEZIONI:
            r = rete.get(f"https://rss.elconfidencial.com/{s}/")
            if r is None or r.status_code != 200:
                continue
            for u in re.findall(r'<link rel="alternate" type="text/html" href="([^"]+)"', r.text):
                m = re.search(r"/(\d{4})-(\d{2})-(\d{2})/", u)
                if not m or not self.e_articolo(u):
                    continue
                g = date(*map(int, m.groups()))
                minima = g if minima is None else min(minima, g)
                if dal <= g <= al:
                    trovati[u] = g
        urls = sorted(trovati, key=lambda u: -trovati[u].toordinal())
        log(f"  {self.nome}: feed di {len(self.SEZIONI)} sezioni, {len(urls)} articoli nel periodo")
        avviso = (f"{self.nome}: i feed arrivano solo al {minima} e sono parziali (circa 15 articoli per "
                  f"sezione); per i giorni precedenti usare --fonte wayback") if minima and dal < minima else (
                  f"{self.nome}: copertura parziale (ultimi articoli di ogni sezione)")
        return [SorgenteURL("feed RSS delle sezioni", urls, avviso)]


class LaRazon(_Es, _Intervalli):
    """Sitemap mensili dei contenuti dal 2007, trovate con reverse-api-engineer il 26 novembre 2026 (le sitemap e
    i feed della piattaforma Arc rispondono 403, ma /sitemaps/ è aperto e consentito dal robots.txt)."""
    chiave, nome, dominio = "larazon", "La Razón", "larazon.es"
    INDICI = ("https://www.larazon.es/sitemaps/content_sitemap_index.xml",)
    RE_FILE = r"/content_(?P<a>\d{4})_(?P<m>\d{1,2})\.xml$"
    DATA_URL = r"_(?P<a>\d{4})(?P<m>\d{2})(?P<g>\d{2})[0-9a-f]{20,}\.html$"
    INIZIO = date(2007, 1, 1)
    re_articolo = re.compile(r"^https://www\.larazon\.es/.+_\d{8}[0-9a-f]{20,}\.html$")
    note_ricerca_data = "sitemap mensili dei contenuti dal 2007, data nell'indirizzo"


SPAGNA = (ABC(), ElDiarioEs(), VeinteMinutosEs(), ElEspanol(), Publico(), LibertadDigital(), OkDiario(), EFE(),
          EuropaPress(), Ara(), ElConfidencial(), LaRazon(), DiarioVasco(), ElCorreo(), Ideal(), SurInEnglish(), DiarioSur())


def _registra_motori():
    from .ricerca import MOTORI
    for t in SPAGNA:
        if isinstance(t, _WordPress):
            MOTORI[t.chiave] = (t.motore_ricerca, "API REST di WordPress con ricerca e filtro per date", False)


_registra_motori()
