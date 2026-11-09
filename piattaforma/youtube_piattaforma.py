"""Estrazione da YouTube: metadati, testo (sottotitoli o Whisper), mp4 e mp3.

esegui_youtube del motore scrive in una cartella: la si fa lavorare in una cartella temporanea
del runner, poi i file video e audio si caricano separatamente (comprimerli non li riduce) e il
resto, senza la cartella _lavoro, va in uno zip con la stessa struttura della cartella locale.
"""
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from . import MOTORE  # noqa: F401
from motore.youtube import ParametriYT, cartella_yt, esegui_youtube

from .nota import testo_nota
from .stato import allarme
from .testate_piattaforma import numero

MIME = {".mp4": "video/mp4", ".mp3": "audio/mpeg", ".m4a": "audio/mp4"}


def classe_ydl(durata_max_sec):
    """YoutubeDL che rifiuta dirette e video più lunghi del limite della piattaforma.
    Il motore accetta la classe come parametro (ydl_cls): nessuna modifica al motore."""
    from yt_dlp import YoutubeDL

    class YoutubeDLPiattaforma(YoutubeDL):
        def extract_info(self, url, *args, **kwargs):
            info = super().extract_info(url, *args, **kwargs)
            if isinstance(info, dict) and info.get("_type", "video") == "video":
                if info.get("is_live") or info.get("live_status") in ("is_live", "is_upcoming"):
                    raise RuntimeError("video escluso: diretta in corso o programmata")
                if (info.get("duration") or 0) > durata_max_sec:
                    raise RuntimeError(f"video escluso: dura più di {durata_max_sec // 60} minuti, "
                                       "limite della piattaforma")
            return info

    return YoutubeDLPiattaforma


def parametri_da_riga(dati):
    p = dati["parametri"]
    return ParametriYT(
        sorgenti=list(p.get("sorgenti", [])), cerca=p.get("cerca"),
        ordina_per_data=bool(p.get("ordina_per_data", False)), dal=p.get("dal"), al=p.get("al"),
        parole=list(p.get("parole", [])), max_video=p.get("max_video"),   # None: nessun limite
        trascrizione=p.get("trascrizione", "auto"), lingua=p.get("lingua"),
        modello="small", device="cpu", compute_type="int8",
        media=p.get("media", "entrambi"), max_altezza=p.get("max_altezza"),   # None: migliore disponibile
        timecode_docx=bool(p.get("timecode_docx", False)),
        cookies_browser=None, cookies_file=None)    # mai cookie di account sulla piattaforma


def separa_media(cartella):
    """Toglie video e audio dalle cartelle dei singoli video e li restituisce da caricare."""
    media = []
    base = cartella / "video"
    if not base.exists():
        return media
    for cart in sorted(c for c in base.iterdir() if c.is_dir()):
        for f in sorted(cart.iterdir()):
            if f.stem in ("video", "audio") and f.suffix.lower() in MIME:
                media.append({"nome": f"{cart.name}_{f.stem}{f.suffix.lower()}",
                              "tipo": "video" if f.stem == "video" else "audio",
                              "percorso_locale": f, "mime": MIME[f.suffix.lower()]})
    return media


def comprimi(cartella, destinazione, esclusi):
    with zipfile.ZipFile(destinazione, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(cartella.rglob("*")):
            rel = f.relative_to(cartella)
            if f.is_dir() or rel.parts[0] == "_lavoro" or f in esclusi:
                continue
            z.write(f, f"{cartella.name}/{rel.as_posix()}")


def esegui_video(dati, sb, stato, impostazioni, cartella_tmp):
    p = parametri_da_riga(dati)
    cartella = cartella_yt(p, Path(cartella_tmp))
    tempo = int(dati["tempo_max_minuti"]) * 60
    stato.fase("raccolta dei video")
    try:
        with allarme(tempo, stato):
            esito = esegui_youtube(p, cartella, log=stato.log,
                                   ydl_cls=classe_ydl(int(dati["yt_max_durata_minuti"]) * 60))
    except KeyboardInterrupt:
        # il limite è scattato fuori dal ciclo dei video, durante la scrittura finale
        stato.fermata_per_tempo = True
        esito = cartella
    if esito is None or not cartella.exists():
        raise RuntimeError("yt-dlp non disponibile sul runner")

    scheda_file = cartella / "scheda_estrazione.txt"
    scheda = scheda_file.read_text(encoding="utf-8") if scheda_file.exists() else ""
    interrotta = stato.fermata_per_tempo or stato.interrotta or "INTERROTTA" in scheda or not scheda

    stato.fase("preparazione dei file")
    media = separa_media(cartella)
    righe = ["I file video (mp4) e audio (mp3) si scaricano separatamente dallo zip, perché comprimerli",
             "non ne riduce il peso. Ciascuno porta il nome della cartella del video a cui appartiene",
             "(per esempio 2025-03-01_titolo_ID_video.mp4): per ricostruire la struttura dello scraper",
             "locale basta spostarlo in quella cartella e rinominarlo video.mp4 o audio.mp3.", ""]
    (cartella / "nota_piattaforma.txt").write_text(
        testo_nota(dati["id"], impostazioni["giorni_conservazione"], False, righe)   # per i video non c'è ripresa, encoding="utf-8")
    archivio = Path(cartella_tmp) / f"{cartella.name}.zip"
    comprimi(cartella, archivio, {m["percorso_locale"] for m in media})

    errore = None
    if stato.fermata_richiesta:
        errore = "Fermata su richiesta: i file contengono i video già elaborati."
    elif stato.fermata_per_tempo:
        errore = f"Fermata dopo {dati['tempo_max_minuti']} minuti: i file contengono i video già elaborati."
    file = [{"nome": archivio.name, "tipo": "zip", "percorso_locale": archivio, "mime": "application/zip"}]
    return {
        "stato": "interrotta" if interrotta else "completata",
        "articoli": numero(scheda, "Video raccolti"),
        "esaminati": numero(scheda, "Video esaminati"),
        "scheda": scheda,
        "errore": errore,
        "file": file + media,
    }


def nuova_cartella_temporanea():
    return tempfile.mkdtemp(prefix="yt_")


def pulisci(cartella_tmp):
    shutil.rmtree(cartella_tmp, ignore_errors=True)
