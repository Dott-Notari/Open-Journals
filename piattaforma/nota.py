"""Nota aggiunta a ogni archivio scaricato dalla piattaforma (nota_piattaforma.txt)."""
from datetime import datetime
from zoneinfo import ZoneInfo

from motore.config import VERSIONE


def testo_nota(id_estrazione, giorni_conservazione, interrotta=False, righe_extra=()):
    ora = datetime.now(ZoneInfo("Europe/Rome")).strftime("%d/%m/%Y %H:%M")
    R = ["NOTA DELLA PIATTAFORMA", "=" * 60,
         f"Estrazione {id_estrazione} eseguita il {ora} sulla piattaforma web del corso",
         f"di Sociologia della comunicazione interculturale, motore versione {VERSIONE}.", ""]
    R += list(righe_extra)
    if interrotta:
        R += ["L'estrazione si è fermata prima della fine. Dalla pagina Estrazioni si può riprendere",
              "dal punto in cui si è interrotta, finché i file restano disponibili: il nuovo archivio",
              "conterrà anche gli articoli già raccolti.", ""]
    R += [f"I file restano disponibili sulla piattaforma per {giorni_conservazione} giorni.",
          "I materiali sono raccolti per finalità di studio e ricerca e non vanno ridistribuiti."]
    return "\n".join(R) + "\n"
