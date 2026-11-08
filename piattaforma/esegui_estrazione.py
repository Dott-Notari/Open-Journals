"""Esegue un'estrazione registrata su Supabase. Lo avvia il workflow estrazione.yml.

Uso: ESTRAZIONE_ID=<uuid> python -m piattaforma.esegui_estrazione
"""
import os
import sys
from datetime import datetime, timezone

from .servizi import RE_UUID, Supabase
from .stato import Stato, pubblico


def adesso():
    return datetime.now(timezone.utc).isoformat()


def carica_file(sb, dati, file):
    """Carica i file nel bucket privato e li registra; restituisce la dimensione totale."""
    totale = 0
    for f in file:
        percorso = f"{dati['utente']}/{dati['id']}/{f['nome']}"
        if "dati" in f:
            dimensione = len(f["dati"])
            sb.carica(percorso, f["dati"], f["mime"])
        else:
            dimensione = f["percorso_locale"].stat().st_size
            with open(f["percorso_locale"], "rb") as aperto:
                sb.carica(percorso, aperto, f["mime"])
        sb.inserisci("estrazione_file", [{"estrazione_id": dati["id"], "percorso": percorso,
                                          "tipo": f["tipo"], "nome": f["nome"], "dimensione": dimensione}])
        totale += dimensione
    return totale


def main():
    id_estrazione = os.environ.get("ESTRAZIONE_ID", "")
    if not RE_UUID.match(id_estrazione):
        pubblico("identificativo dell'estrazione non valido")
        return 1
    sb = Supabase()
    dati = sb.rpc("inizia_estrazione", p_id=id_estrazione, p_run_id=int(os.environ.get("GITHUB_RUN_ID", "0")))
    if not dati:
        pubblico("estrazione già avviata, annullata o inesistente: nulla da fare")
        return 0
    if not dati.get("utente"):
        sb.aggiorna("estrazioni", {"stato": "annullata", "conclusa_il": adesso(),
                                   "errore": "account cancellato"}, id=f"eq.{id_estrazione}")
        return 0

    impostazioni = sb.impostazioni()
    stato = Stato(sb, id_estrazione)
    cartella_tmp = None
    pubblico(f"[avvio] fonte {dati['fonte']}, modalità {dati['modalita']}")
    try:
        if dati["fonte"] == "youtube":
            from . import youtube_piattaforma as Y
            cartella_tmp = Y.nuova_cartella_temporanea()
            esito = Y.esegui_video(dati, sb, stato, impostazioni, cartella_tmp)
        else:
            from .testate_piattaforma import esegui_testata
            esito = esegui_testata(dati, sb, stato, impostazioni)

        stato.fase("caricamento dei file")
        totale = carica_file(sb, dati, esito["file"])
        stato.chiudi()
        sb.aggiorna("estrazioni", {
            "stato": esito["stato"], "conclusa_il": adesso(), "articoli": esito["articoli"],
            "esaminati": esito["esaminati"], "scheda": esito["scheda"], "errore": esito["errore"],
            "dimensione_totale": totale, "avanzamento": "conclusa", "log": stato.testo_log()},
            id=f"eq.{id_estrazione}")
        pubblico(f"[fine] {esito['stato']}: {esito['articoli']} elementi raccolti, {len(esito['file'])} file")
        return 0
    except Exception as e:
        stato.chiudi()
        stato.log(f"ERRORE: {e!r}")
        try:
            sb.aggiorna("estrazioni", {
                "stato": "errore", "conclusa_il": adesso(), "avanzamento": "errore",
                "errore": f"{e.__class__.__name__}: {str(e)[:800]}", "log": stato.testo_log()},
                id=f"eq.{id_estrazione}")
        except Exception:
            pass
        pubblico(f"[errore] {e.__class__.__name__}: dettagli nel registro della piattaforma")
        return 1
    finally:
        if cartella_tmp:
            from .youtube_piattaforma import pulisci
            pulisci(cartella_tmp)


if __name__ == "__main__":
    sys.exit(main())
