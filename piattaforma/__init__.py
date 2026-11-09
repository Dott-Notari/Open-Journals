"""Collegamento tra il motore dello scraper, Supabase e GitHub Actions.

Il motore (cartella scraper_testate) è usato così com'è: questo pacchetto lo importa,
lo esegue sui runner di GitHub Actions e scrive esiti e file su Supabase.
"""
import logging
import sys
from pathlib import Path

# Le librerie (trafilatura, yt-dlp, urllib3) possono scrivere avvisi con indirizzi e titoli:
# i log di Actions sono pubblici, quindi si tacciono. Il dettaglio resta nella colonna log su Supabase.
logging.disable(logging.ERROR)

MOTORE = Path(__file__).resolve().parent.parent / "scraper_testate"
if str(MOTORE) not in sys.path:
    sys.path.insert(0, str(MOTORE))
