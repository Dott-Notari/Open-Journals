"""Il Fatto Quotidiano (WordPress dietro Cloudflare)."""
import re

from .base import Testata
from ..comune import giorni
from ..modello import SorgenteElenco


class Fatto(Testata):
    chiave = "fatto"
    nome = "Il Fatto Quotidiano"
    dominio = "ilfattoquotidiano.it"
    re_articolo = re.compile(
        r"^https://www\.ilfattoquotidiano\.it/(?:[a-z0-9-]+/)*\d{4}/\d{2}/\d{2}/[^/]+/\d+/?$")
    selettori_corpo = ("[itemprop=articleBody]", ".article-body", ".entry-content",
                       ".article__body", ".ifq-article-content")
    fine_testo = ("sostieni ilfattoquotidiano", "leggi anche", "gentile lettore")
    date_nell_url = True
    note_ricerca_data = "archivi per giorno di WordPress, scorsi pagina per pagina"

    def pulisci_sommario(self, s):
        """La descrizione del Fatto comincia spesso con una formula SEO da togliere."""
        s = re.sub(r"^\s*Leggi su Il Fatto Quotidiano(\.it)?\s*[:,]?\s*", "", s or "", flags=re.I)
        return s[:1].upper() + s[1:]

    def normalizza(self, url):
        u = super().normalizza(url)
        return u if u.endswith("/") else u + "/"

    def pagina_elenco(self, base, n):
        return base if n == 1 else base.rstrip("/") + f"/page/{n}/"

    def piano_per_data(self, rete, dal, al, log, parole=None):
        return [SorgenteElenco(f"archivio del {g.isoformat()}",
                               f"https://www.ilfattoquotidiano.it/{g:%Y/%m/%d}/",
                               filtro=f"/{g:%Y/%m/%d}/", usa_date=False)
                for g in giorni(dal, al)]
