"""Collaudo da GitHub Actions: per ogni testata una breve estrazione reale (ultimi due giorni,
al più cinque articoli) e la prova della paginazione, con le funzioni del motore; per YouTube un
video breve con metadati, sottotitoli, mp4, mp3 e trascrizione Whisper.

Gli esiti vanno in stato_testate. Con AGGIORNA_DISPONIBILITA=true (primo collaudo, avvio manuale)
l'esito decide anche se la fonte è disponibile online; i collaudi settimanali aggiornano solo
l'esito, e la decisione resta al docente.

Uso: python -m piattaforma.collaudo_online [chiavi...]
"""
import io
import json
import os
import shutil
import sys
import tempfile
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import MOTORE  # noqa: F401
from motore.collaudo import prova_paginazione
from motore.destinazioni import ZipMemoria
from motore.esecuzione import esegui
from motore.modello import Parametri
from motore.rete import Rete
from motore.testate import TESTATE
from motore.youtube import ParametriYT, esegui_youtube

from .servizi import Supabase
from .stato import pubblico
from .testate_piattaforma import numero
from .youtube_piattaforma import classe_ydl

VIDEO_PROVA = os.environ.get("COLLAUDO_YT_VIDEO") or "https://www.youtube.com/watch?v=jNQXAC9IVRw"


def collauda_testata(chiave):
    t = TESTATE[chiave]
    rete, righe = Rete(), []
    bloccato = []
    al = date.today()
    dal = al - timedelta(days=2)

    def log(m):
        if "Il sito ha bloccato le richieste" in str(m):
            bloccato.append(True)

    articoli = errori = 0
    try:
        z = esegui(Parametri("data", testata=chiave, dal=dal.isoformat(), al=al.isoformat(),
                             max_articoli=5, formati=["jsonl"]),
                   ZipMemoria(), None, rete=rete, log=log, salva_grezzi=False, tempo_max=600)
        scheda = zipfile.ZipFile(io.BytesIO(z)).read("scheda_estrazione.txt").decode("utf-8")
        articoli, errori = numero(scheda, "Articoli raccolti"), numero(scheda, "Errori")
        esiti = scheda.split("ESITI")[1].split("MODALITÀ")[0].strip().splitlines()
        righe += [e.strip() for e in esiti if e.strip()]
        if "AVVISI SULLA COPERTURA" in scheda:
            righe.append("Avvisi: " + scheda.split("AVVISI SULLA COPERTURA")[1].split("\n\n")[0].strip())
    except Exception as e:
        righe.append(f"Errore nell'estrazione di prova: {e.__class__.__name__}: {str(e)[:200]}")
        errori += 1
    paginazione_ok = True
    for base in getattr(t, "elenchi_prova", ()) or ():
        try:
            prova = prova_paginazione(t, base, rete)
            funziona = any("FUNZIONA" in r for r in prova)
            righe.append(f"Paginazione {base}: {'funziona' if funziona else 'non verificata'}")
            paginazione_ok = paginazione_ok and funziona
        except Exception as e:
            righe.append(f"Paginazione {base}: errore {e.__class__.__name__}")
            paginazione_ok = False
    if bloccato or articoli == 0:
        esito = "fallito"
    elif errori or not paginazione_ok:
        esito = "parziale"
    else:
        esito = "ok"
    if bloccato:
        righe.insert(0, "Il sito ha attivato una protezione anti-bot verso i server di GitHub Actions.")
    return esito, righe


def collauda_youtube():
    righe = []
    ydl = classe_ydl(600)
    tmp = Path(tempfile.mkdtemp(prefix="collaudo_yt_"))
    try:
        # 1. metadati e sottotitoli, senza file multimediali
        a = tmp / "a"
        esegui_youtube(ParametriYT(sorgenti=[VIDEO_PROVA], max_video=1, trascrizione="sottotitoli",
                                   media="nessuno"), a, log=lambda m: None, ydl_cls=ydl)
        sa = (a / "scheda_estrazione.txt").read_text(encoding="utf-8") if (a / "scheda_estrazione.txt").exists() else ""
        metadati = numero(sa, "Video raccolti") > 0
        righe.append(f"Metadati e sottotitoli: {'letti' if metadati else 'non raggiungibili'}")
        # 2. mp4, mp3 e trascrizione Whisper
        b = tmp / "b"
        esegui_youtube(ParametriYT(sorgenti=[VIDEO_PROVA], max_video=1, trascrizione="whisper",
                                   media="entrambi", max_altezza=360, device="cpu"),
                       b, log=lambda m: None, ydl_cls=ydl)
        mp4 = list(b.glob("video/*/video.mp4"))
        mp3 = list(b.glob("video/*/audio.mp3"))
        meta = list(b.glob("video/*/metadata.json"))
        whisper = bool(meta) and "whisper" in json.loads(meta[0].read_text(encoding="utf-8")).get("metodo", "")
        righe += [f"Video mp4: {'scaricato' if mp4 else 'non scaricato'}",
                  f"Audio mp3: {'ricavato' if mp3 else 'non ricavato'}",
                  f"Trascrizione Whisper: {'riuscita' if whisper else 'non riuscita'}"]
        if not metadati:
            esito = "fallito"
        elif mp4 and mp3 and whisper:
            esito = "ok"
        else:
            esito = "parziale"
    except Exception as e:
        righe.append(f"Errore: {e.__class__.__name__}: {str(e)[:200]}")
        esito = "fallito"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return esito, righe


def main(chiavi=None):
    sb = Supabase()
    aggiorna_disp = os.environ.get("AGGIORNA_DISPONIBILITA", "").lower() == "true"
    # solo le fonti presenti sulla piattaforma (il Guardian, per esempio, non è attivato)
    sulla_piattaforma = [r["chiave"] for r in sb.seleziona("stato_testate", select="chiave", order="ordine")]
    chiavi = chiavi or sulla_piattaforma
    sconosciute = [k for k in chiavi if k != "youtube" and k not in TESTATE]
    if sconosciute:
        pubblico(f"[collaudo] chiavi sconosciute: {', '.join(sconosciute)}")
        return 1
    riepilogo = []
    for k in chiavi:
        if sb.seleziona("estrazioni", select="id", fonte=f"eq.{k}", stato="eq.in_corso", limit="1"):
            pubblico(f"[collaudo] {k}: saltata, c'è un'estrazione in corso")
            continue
        pubblico(f"[collaudo] {k}")
        esito, righe = collauda_youtube() if k == "youtube" else collauda_testata(k)
        valori = {"esito_collaudo": esito, "collaudo_il": datetime.now(timezone.utc).isoformat(),
                  "dettaglio_collaudo": "\n".join(righe)[:4000]}
        if aggiorna_disp:
            valori["disponibile_online"] = esito in ("ok", "parziale")
        sb.aggiorna("stato_testate", valori, chiave=f"eq.{k}")
        riepilogo.append(f"{k}: {esito}")
        pubblico(f"[collaudo] {k}: {esito}")
    pubblico("[collaudo] riepilogo: " + ", ".join(riepilogo))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
