"""Accesso a Supabase (database e storage) e a GitHub, con la sola libreria requests.

Le chiavi arrivano dalle variabili d'ambiente impostate come segreti di GitHub Actions:
SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY. Nessun messaggio d'errore riporta le chiavi.
"""
import os
import re
from urllib.parse import quote

import requests

BUCKET = "estrazioni"
RE_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class ErroreServizio(RuntimeError):
    pass


class Supabase:
    def __init__(self, url=None, chiave=None):
        self.url = (url or os.environ["SUPABASE_URL"]).rstrip("/")
        if not (self.url.startswith("https://") or re.match(r"^http://(127\.0\.0\.1|localhost)(:\d+)?$", self.url)):
            raise ErroreServizio("SUPABASE_URL deve iniziare con https://")
        chiave = chiave or os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        self.s = requests.Session()
        self.s.headers.update({"apikey": chiave})
        if chiave.startswith("eyJ"):   # chiave service_role in formato JWT; le nuove chiavi segrete bastano in apikey
            self.s.headers["Authorization"] = f"Bearer {chiave}"

    # ----------------------------------------------------------------- database
    def _verifica(self, r, cosa):
        if r.status_code >= 400:
            # il corpo della risposta di PostgREST non contiene segreti: aiuta a capire l'errore
            raise ErroreServizio(f"{cosa}: HTTP {r.status_code} {r.text[:300]}")
        return r

    def rpc(self, funzione, **argomenti):
        r = self._verifica(self.s.post(f"{self.url}/rest/v1/rpc/{funzione}", json=argomenti, timeout=60),
                           f"rpc {funzione}")
        return r.json() if r.content else None

    def seleziona(self, tabella, **parametri):
        r = self._verifica(self.s.get(f"{self.url}/rest/v1/{tabella}", params=parametri, timeout=60),
                           f"lettura {tabella}")
        return r.json()

    def aggiorna(self, tabella, valori, **filtri):
        if not filtri:
            raise ErroreServizio("aggiornamento senza filtro rifiutato")
        self._verifica(self.s.patch(f"{self.url}/rest/v1/{tabella}", params=filtri, json=valori,
                                    headers={"Prefer": "return=minimal"}, timeout=60),
                       f"aggiornamento {tabella}")

    def inserisci(self, tabella, righe, conflitto=None):
        intestazioni = {"Prefer": "return=minimal"}
        parametri = {}
        if conflitto:
            intestazioni["Prefer"] += ",resolution=merge-duplicates"
            parametri["on_conflict"] = conflitto
        self._verifica(self.s.post(f"{self.url}/rest/v1/{tabella}", params=parametri, json=righe,
                                   headers=intestazioni, timeout=120),
                       f"inserimento {tabella}")

    def elimina(self, tabella, **filtri):
        if not filtri:
            raise ErroreServizio("cancellazione senza filtro rifiutata")
        self._verifica(self.s.delete(f"{self.url}/rest/v1/{tabella}", params=filtri,
                                     headers={"Prefer": "return=minimal"}, timeout=60),
                       f"cancellazione {tabella}")

    def impostazioni(self):
        return self.seleziona("impostazioni", select="*", id="eq.true")[0]

    # ----------------------------------------------------------------- storage
    def carica(self, percorso, dati, tipo):
        """Carica nel bucket privato. dati: bytes oppure un file aperto in lettura binaria."""
        url = f"{self.url}/storage/v1/object/{BUCKET}/{quote(percorso)}"
        r = self.s.post(url, data=dati, headers={"Content-Type": tipo, "x-upsert": "false",
                                                 "cache-control": "no-store"}, timeout=1800)
        self._verifica(r, f"caricamento di {percorso.rsplit('/', 1)[-1]}")

    def scarica(self, percorso):
        r = self.s.get(f"{self.url}/storage/v1/object/authenticated/{BUCKET}/{quote(percorso)}", timeout=600)
        return self._verifica(r, f"lettura di {percorso.rsplit('/', 1)[-1]}").content

    def elimina_file(self, percorsi):
        for i in range(0, len(percorsi), 100):
            r = self.s.delete(f"{self.url}/storage/v1/object/{BUCKET}",
                              json={"prefixes": percorsi[i:i + 100]}, timeout=120)
            self._verifica(r, "cancellazione dallo storage")


def avvia_workflow(id_estrazione, fonte):
    """Avvia estrazione.yml con workflow_dispatch usando il token del job (permesso actions: write)."""
    if not RE_UUID.match(str(id_estrazione)) or not re.match(r"^[a-z0-9_]{2,30}$", str(fonte)):
        raise ErroreServizio("identificativo o fonte non validi")
    repo = os.environ["GITHUB_REPOSITORY"]
    ramo = os.environ.get("RAMO_PRINCIPALE") or os.environ.get("GITHUB_REF_NAME") or "main"
    r = requests.post(
        f"https://api.github.com/repos/{repo}/actions/workflows/estrazione.yml/dispatches",
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                 "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
        json={"ref": ramo, "inputs": {"id": str(id_estrazione), "fonte": fonte}}, timeout=30)
    if r.status_code not in (200, 204):
        raise ErroreServizio(f"avvio del workflow non riuscito: HTTP {r.status_code}")
