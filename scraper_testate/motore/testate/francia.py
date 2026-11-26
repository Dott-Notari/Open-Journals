"""Testate francesi, scritte sulla ricognizione del 25 novembre 2026 (robots.txt, API, sitemap, prova di
scaricamento di un articolo con lo User-Agent dello strumento), senza reverse-api-engineer.

Non incluse (vedi schede.ESCLUSE): Libération, Le Parisien, Les Échos, Le Point, Marianne e AFP (protezione
anti-bot o 403 allo strumento)."""
import re
from datetime import date

from .generiche import _FileFissi, _Intervalli, re_dominio
from .venezuela import _SitemapOrdinate


class _Fr:
    lingua = "fr"


class LeMonde(_Fr, _Intervalli):
    chiave, nome, dominio = "lemonde", "Le Monde", "lemonde.fr"
    INDICI = ("https://www.lemonde.fr/sitemap_index.xml",)
    RE_FILE = r"/sitemap/articles/(?P<a>\d{4})-(?P<m>\d{2})-(?P<g>\d{2})\.xml$"
    date_nell_url = True
    re_articolo = re.compile(r"^https://www\.lemonde\.fr/(?!en/).+/article/\d{4}/\d{2}/\d{2}/[^/]+\.html$")
    note_ricerca_data = ("sitemap settimanali degli articoli (archivio dal 1944), data nell'indirizzo; molti articoli "
                         "sono riservati agli abbonati e risultano con il testo parziale")


class LeFigaro(_Fr, _Intervalli):
    chiave, nome, dominio = "lefigaro", "Le Figaro", "lefigaro.fr"
    INDICI = ("https://sitemaps.lefigaro.fr/lefigaro.fr/articles.xml",)
    RE_FILE = r"/articles/(?P<a>\d{4})-(?P<m>\d{2})-(?P<g>\d{2})\.xml$"
    FILTRO_LASTMOD = False     # un file per giorno di pubblicazione
    re_articolo = re_dominio("lefigaro.fr")
    note_ricerca_data = "sitemap giornaliere degli articoli; parte degli articoli è riservata agli abbonati"


class VentiMinutesFr(_Fr, _Intervalli):
    chiave, nome, dominio = "20minutesfr", "20 Minutes", "20minutes.fr"
    INDICI = ("https://www.20minutes.fr/sitemap-index.xml",)
    RE_FILE = r"/contents-(?P<a>\d{4})-(?P<m>\d{2})\.xml\.gz$"
    DATA_URL = r"/\d+-(?P<a>\d{4})(?P<m>\d{2})(?P<g>\d{2})-"
    INIZIO = date(2006, 2, 1)
    re_articolo = re.compile(r"^https://www\.20minutes\.fr/.+/\d+-\d{8}-[^/]+$")
    note_ricerca_data = "sitemap mensili dal 2006, data nell'indirizzo"


class FranceInfo(_Fr, _Intervalli):
    chiave, nome, dominio = "franceinfo", "franceinfo", "franceinfo.fr"
    INDICI = ("https://www.franceinfo.fr/sitemap_index.xml",)
    RE_FILE = r"/sitemap/(?P<a>\d{4})-(?P<m>\d{2})-article\.xml$"
    re_articolo = re.compile(r"^https://www\.franceinfo\.fr/.+_\d+\.html$")
    note_ricerca_data = "sitemap mensili degli articoli dal 2011, filtrate per data di modifica"


class BFMTV(_Fr, _Intervalli):
    chiave, nome, dominio = "bfmtv", "BFMTV", "bfmtv.com"
    INDICI = ("https://www.bfmtv.com/sitemap_index_arbo_contenu.xml",)
    RE_FILE = r"/rubriquesContenus/(?P<a>\d{4})-(?P<m>\d{2})-\d+\.xml\.gz$"
    re_articolo = re.compile(r"^https://www\.bfmtv\.com/(?!videos?/).+_[A-Z]{2}-\d{9,}\.html$")
    note_ricerca_data = "sitemap mensili dei contenuti dal 2006, filtrate per data di modifica"


class LCI(_Fr, _SitemapOrdinate):
    chiave, nome, dominio = "lci", "TF1 Info (LCI)", "tf1info.fr"
    INDICE = "https://www.tf1info.fr/sitemap.xml"
    RE_FILE = r"/sitemap-contents-(\d+)\.xml$"
    re_articolo = re.compile(r"^https://www\.tf1info\.fr/(?!replay-lci/)[a-z0-9-]+/[a-z0-9-]+-\d+\.html$")
    note_ricerca_data = "sitemap dei contenuti numerate in ordine cronologico dal 2011, filtrate per data di modifica"


class CNews(_Fr, _SitemapOrdinate):
    chiave, nome, dominio = "cnews", "CNews", "cnews.fr"
    INDICE = "https://www.cnews.fr/sitemap.xml"
    RE_FILE = r"sitemap\.xml\?page=(\d+)$"
    re_articolo = re.compile(r"^https://www\.cnews\.fr/(?!videos/)(?:[a-z0-9-]+/)+\d{4}-\d{2}-\d{2}/[a-z0-9-]+$")
    note_ricerca_data = ("sitemap numerate in ordine cronologico dal 2012, data nell'indirizzo; il robots.txt chiede "
                         "10 secondi tra le richieste")

    def _data(self, u, lastmod, pub):
        m = re.search(r"/(\d{4})-(\d{2})-(\d{2})/", u)
        if m:
            try:
                return date(*map(int, m.groups()))
            except ValueError:
                pass
        return super()._data(u, lastmod, pub)


class France24(_Fr, _Intervalli):
    chiave, nome, dominio = "france24", "France 24", "france24.com"
    INDICI = ("https://www.france24.com/sitemaps/fr/index.xml",)
    RE_FILE = r"/contents_(?P<a>\d{4})(?P<m>\d{2})\.xml$"
    DATA_URL = r"/fr/(?:[a-z0-9-]+/)*(?P<a>\d{4})(?P<m>\d{2})(?P<g>\d{2})-"
    INIZIO = date(2007, 1, 1)
    re_articolo = re.compile(r"^https://www\.france24\.com/fr/(?:[a-z0-9-]+/)*\d{8}-[^/]+$")
    note_ricerca_data = "sitemap mensili dell'edizione francese dal 2007, data nell'indirizzo"


class LaTribune(_Fr, _Intervalli):
    chiave, nome, dominio = "latribune", "La Tribune", "latribune.fr"
    INDICI = ("https://www.latribune.fr/sitemaps/sitemap.xml",)
    RE_FILE = r"/edito/(?P<g>\d{2})-(?P<m>\d{2})-(?P<a>\d{4})-au-\d{2}-\d{2}-\d{4}\.xml$"
    re_articolo = re.compile(r"^https://www\.latribune\.fr/article/.+/\d{6,}/[^/]+$")
    note_ricerca_data = "sitemap settimanali degli articoli, filtrate per data di modifica"


class Humanite(_Fr, _Intervalli):
    chiave, nome, dominio = "humanite", "L'Humanité", "humanite.fr"
    INDICI = ("https://www.humanite.fr/sitemap.xml",)
    RE_FILE = r"yyyy=(?P<a>\d{4})&(?:amp;)?mm=(?P<m>\d{2})&(?:amp;)?dd=(?P<g>\d{2})"
    FILTRO_LASTMOD = False     # un file per giorno di pubblicazione
    re_articolo = re_dominio("humanite.fr")
    note_ricerca_data = "sitemap giornaliere (archivio dal 1997); parte degli articoli è riservata agli abbonati"


class LaCroix(_Fr, _Intervalli):
    chiave, nome, dominio = "lacroix", "La Croix", "la-croix.com"
    INDICI = ("https://www.la-croix.com/feeds/sitemaps/sitemaps_articles.xml",)
    RE_FILE = r"/articles/(?P<a>\d{4})-(?P<m>\d{2})\.xml$"
    INIZIO = date(1998, 1, 1)
    re_articolo = re_dominio("la-croix.com")
    note_ricerca_data = "sitemap mensili degli articoli dal 1998, filtrate per data di modifica"


class LObs(_Fr, _Intervalli):
    chiave, nome, dominio = "lobs", "L'Obs", "nouvelobs.com"
    INDICI = ("https://www.nouvelobs.com/sitemap/sitemap-index-articles.xml",)
    RE_FILE = r"/edito/(?P<a>\d{4})-(?P<m>\d{2})\.xml$"
    DATA_URL = r"/(?P<a>\d{4})(?P<m>\d{2})(?P<g>\d{2})\.OBS"
    INIZIO = date(1999, 2, 1)
    re_articolo = re.compile(r"^https://www\.nouvelobs\.com/.+/\d{8}\.OBS\d+/[^/]+\.html$")
    note_ricerca_data = "sitemap mensili dal 1999, data nell'indirizzo"


class LExpress(_Fr, _Intervalli):
    chiave, nome, dominio = "lexpress", "L'Express", "lexpress.fr"
    INDICI = ("https://www.lexpress.fr/arc/outboundfeeds/sitemap-by-week-2020-now.xml",)
    RE_FILE = r"/weeks/(?P<a>\d{4})-(?P<s>\d{2})/"
    INIZIO = date(2020, 1, 1)
    re_articolo = re.compile(r"^https://www\.lexpress\.fr/.+-[A-Z0-9]{20,}/?$")
    note_ricerca_data = "sitemap settimanali dal 2020, filtrate per data di modifica"


class Mediapart(_Fr, _FileFissi):
    chiave, nome, dominio = "mediapart", "Mediapart", "mediapart.fr"
    FILES = tuple(f"https://www.mediapart.fr/journal/{s}/sitemap.xml"
                  for s in ("international", "france", "politique", "economie", "ecologie", "culture-idees"))
    DATA_URL = r"/journal/[a-z-]+/(?P<g>\d{2})(?P<m>\d{2})(?P<y>\d{2})/"
    re_articolo = re.compile(r"^https://www\.mediapart\.fr/journal/[a-z-]+/\d{6}/[^/]+$")
    note_ricerca_data = ("sitemap delle sezioni (alcuni mesi), data nell'indirizzo; quasi tutto è riservato agli "
                         "abbonati: si raccolgono titolo e attacco; il robots.txt chiede 3 secondi tra le richieste")


class CanardEnchaine(_Fr, _FileFissi):
    chiave, nome, dominio = "canard", "Le Canard enchaîné", "lecanardenchaine.fr"
    FILES = ("https://www.lecanardenchaine.fr/sitemap.xml",)
    re_articolo = re.compile(r"^https://www\.lecanardenchaine\.fr/[a-z-]+/(?:[a-z-]+/)?\d+-[a-z0-9-]+/?$")
    note_ricerca_data = ("una sitemap con circa 11.000 articoli, filtrata per data di modifica; quasi tutto è "
                         "riservato agli abbonati: si raccolgono titolo e attacco")


class CourrierInternational(_Fr, _Intervalli):
    chiave, nome, dominio = "courrier", "Courrier international", "courrierinternational.com"
    INDICI = ("https://www.courrierinternational.com/sitemap_index.xml",)
    RE_FILE = r"/sitemap/articles/(?P<a>\d{4})-(?P<m>\d{2})-(?P<g>\d{2})\.xml$"
    date_nell_url = True
    INIZIO = date(2001, 1, 1)
    re_articolo = re_dominio("courrierinternational.com")
    note_ricerca_data = ("sitemap settimanali dal 2001; il robots.txt chiede 10 secondi tra le richieste; parte "
                         "degli articoli è riservata agli abbonati")


FRANCIA = (LeMonde(), LeFigaro(), VentiMinutesFr(), FranceInfo(), BFMTV(), LCI(), CNews(), France24(), LaTribune(),
           Humanite(), LaCroix(), LObs(), LExpress(), Mediapart(), CanardEnchaine(), CourrierInternational())
