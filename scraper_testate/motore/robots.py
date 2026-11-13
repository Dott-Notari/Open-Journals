"""Lettura del robots.txt secondo lo standard RFC 9309 (gruppi per user-agent, caratteri jolly * e $,
regola più lunga vincente, Allow a parità di lunghezza). Il modulo urllib.robotparser della libreria
standard ignora i caratteri jolly, che molte testate usano (es. «Disallow: /*?s=»)."""
import re
from urllib.parse import urlparse, unquote


class Robots:
    def __init__(self, testo, agente):
        self.agente = agente.lower()
        self.regole, self.ritardo, self.sitemap = self._gruppo(testo or "")

    def _gruppo(self, testo):
        gruppi, agenti, corrente, in_regole, sitemap = [], [], None, False, []
        for riga in testo.splitlines():
            riga = riga.split("#", 1)[0].strip()
            if ":" not in riga:
                continue
            campo, valore = (x.strip() for x in riga.split(":", 1))
            campo = campo.lower()
            if campo == "sitemap":
                sitemap.append(valore)
            elif campo == "user-agent":
                if in_regole or corrente is None:   # comincia un nuovo gruppo
                    corrente = {"agenti": [], "regole": [], "ritardo": None}
                    gruppi.append(corrente)
                    in_regole = False
                corrente["agenti"].append(valore.lower())
            elif corrente is not None and campo in ("allow", "disallow"):
                in_regole = True
                if valore or campo == "allow":
                    corrente["regole"].append((campo == "allow", valore))
            elif corrente is not None and campo == "crawl-delay":
                in_regole = True
                try:
                    corrente["ritardo"] = float(valore)
                except ValueError:
                    pass
        # il gruppo che nomina questo agente vince su quello generico «*»
        nominati = [g for g in gruppi if any(a != "*" and a in self.agente for a in g["agenti"])]
        scelti = nominati or [g for g in gruppi if "*" in g["agenti"]]
        regole = [r for g in scelti for r in g["regole"]]
        ritardi = [g["ritardo"] for g in scelti if g["ritardo"] is not None]
        return regole, (max(ritardi) if ritardi else None), sitemap

    @staticmethod
    def _regex(percorso):
        fine = percorso.endswith("$")
        corpo = re.escape(percorso.rstrip("$")).replace(r"\*", ".*")
        return re.compile(corpo + ("$" if fine else ""))

    def consentito(self, url):
        u = urlparse(url)
        percorso = unquote(u.path or "/") + (f"?{u.query}" if u.query else "")
        if percorso == "/robots.txt":
            return True
        migliore = None   # (lunghezza della regola, consentita)
        for consenti, p in self.regole:
            if self._regex(p).match(percorso):
                chiave = (len(p), consenti)
                if migliore is None or chiave > migliore:
                    migliore = chiave
        return True if migliore is None else migliore[1]
