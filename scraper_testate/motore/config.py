"""Impostazioni generali del motore."""
from pathlib import Path

VERSIONE = "1.13 (Siti_API)"
UA = ("ScraperDidattico/1.0 (ricerca e didattica universitaria, "
      "Sociologia della comunicazione interculturale)")
PAUSA_DEFAULT = 2.0      # secondi minimi tra due richieste allo stesso sito
PAUSA_MINIMA = 1.0
TIMEOUT = 30
RADICE = "Siti_API/estrazioni"
FUSO = "Europe/Rome"
FORMATI = ("docx", "txt", "html", "xlsx", "jsonl", "tlab")
STOP_VECCHI = 6          # articoli consecutivi più vecchi di "dal" prima di fermare uno scorrimento
LIMITE_PAGINE = 3000     # tetto di sicurezza per gli scorrimenti delle pagine elenco


def cartella_desktop() -> Path:
    home = Path.home()
    for c in (home / "Desktop", home / "OneDrive" / "Desktop",
              home / "OneDrive" / "Scrivania", home / "Scrivania"):
        if c.exists():
            return c
    return home


def radice_locale() -> Path:
    return cartella_desktop() / RADICE
