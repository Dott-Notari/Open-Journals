"""Avvenire (piattaforma Nuxt)."""
import re

from .base import Testata
from .. import sitemap as SM
from ..comune import mesi, testo_pulito
from ..modello import SorgenteURL

INDICE = "https://www.avvenire.it/sitemap.xml"


class Avvenire(Testata):
    chiave = "avvenire"
    nome = "Avvenire"
    dominio = "avvenire.it"
    re_articolo = re.compile(
        r"^https://www\.avvenire\.it/(?!tag/|redazione/|info/|ecosistema-avvenire/)"
        r"(?:[a-z0-9-]+/){0,2}(?!pubblicita_|credits_|termini-|privacy-)[a-z0-9-]+_\d{2,}$")
    fine_testo = ("© riproduzione riservata", "seguici anche su google discover")
    note_ricerca_data = ("sitemap mensili dal 2000; la data esatta si legge in ogni articolo; "
                         "per gli anni meno recenti l'archivio online è una selezione")

    def pagina_elenco(self, base, n):
        return base if n == 1 else base.rstrip("/") + f"/{n}"

    ETICHETTE = {"attualita": "Attualità", "agora": "Agorà", "idee-e-commenti": "Idee e commenti",
                 "chiesa": "Chiesa", "mondo": "Mondo", "politica": "Politica", "economia": "Economia",
                 "rubriche": "Rubriche", "vita-e-cura": "Vita e cura", "sport": "Sport",
                 "opinioni": "Opinioni", "famiglia-e-vita": "Famiglia e vita"}

    def sezione_da_url(self, url):
        m = re.match(r"https://www\.avvenire\.it/([a-z0-9-]+)/", url)
        if not m:
            return ""
        return self.ETICHETTE.get(m.group(1), m.group(1).replace("-", " ").capitalize())

    def tag_pagina(self, soup):
        """Tag del blocco «Temi» in fondo all'articolo (non quelli delle schede correlate)."""
        for el in soup.find_all(string=re.compile(r"^\s*Temi\s*$")):
            box = el.find_parent()
            for _ in range(3):
                if box is None:
                    break
                link = box.find_all("a", href=re.compile(r"/tag/"))
                if link:
                    return [testo_pulito(a.get_text(" ", strip=True)) for a in link]
                box = box.find_parent()
        return []

    def piano_per_data(self, rete, dal, al, log, parole=None):
        richiesti = set(mesi(dal, al))
        files = []
        for loc, _ in SM.leggi_indice(rete, INDICE):
            m = re.search(r"sitemap-stories__(\d{4}-\d{2})__\d+\.xml", loc)
            if m and m.group(1) in richiesti and m.group(1) >= "1990":
                files.append(loc)
        urls = []
        for f in sorted(files, reverse=True):
            urls += [v[0] for v in SM.leggi_urlset(rete, f) if self.e_articolo(v[0])]
        log(f"  Avvenire: {len(files)} sitemap mensili, {len(urls)} articoli da verificare")
        return [SorgenteURL(f"sitemap mensili ({len(files)})", urls)]
