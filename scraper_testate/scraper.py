#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper didattico delle testate giornalistiche
Corso di Sociologia della comunicazione interculturale

Senza argomenti parte la modalità guidata:
    python scraper.py

Oppure da riga di comando:
    python scraper.py data avvenire --dal 2026-10-01 --al 2026-10-31 --parole "migrant*,sbarc*"
    python scraper.py elenco https://www.avvenire.it/tag/migranti_4439 --dal 2026-01-01
    python scraper.py link https://www.ilgiornale.it/news/... https://www.ansa.it/...
    python scraper.py youtube "https://www.youtube.com/watch?v=..." --lingua it
    python scraper.py youtube --cerca "migranti lampedusa" --max 20 --media nessuno
    python scraper.py youtube "https://www.youtube.com/@canale" --dal 2026-01-01
    python scraper.py verifica ilgiornale
    python scraper.py testate
    python scraper.py diagnosi

Opzioni comuni: --formati docx,txt,html,xlsx,jsonl,tlab  --max 200  --pausa 2
                --cerca-in titolo  --tutte  --cartella <radice>  --no-grezzi
"""
import argparse
import re
import sys
from datetime import date
from pathlib import Path

from motore.config import FORMATI, PAUSA_DEFAULT, radice_locale
from motore.destinazioni import CartellaLocale
from motore.esecuzione import cartella_per, esegui
from motore.modello import Parametri
from motore.rete import Rete
from motore.testate import TESTATE
from motore.verifiche import verifica
from motore.youtube import ParametriYT, cartella_yt, esegui_youtube

RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def data_valida(s):
    if not RE_DATA.match(s):
        raise argparse.ArgumentTypeError("usa il formato AAAA-MM-GG")
    date.fromisoformat(s)
    return s


def lista(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def avvia(p, args):
    radice = Path(args.cartella) if getattr(args, "cartella", None) else radice_locale()
    cartella = cartella_per(p, radice)
    print(f"\nCartella dell'estrazione: {cartella}\n")
    rete = Rete(pausa=getattr(args, "pausa", PAUSA_DEFAULT), log=print)
    esegui(p, CartellaLocale(cartella), cartella / "_lavoro", rete=rete, log=print,
           salva_grezzi=not getattr(args, "no_grezzi", False))
    print(f"\nFatto. I file sono in: {cartella}")


def avvia_youtube(p, cartella=None):
    radice = Path(cartella) if cartella else radice_locale()
    c = cartella_yt(p, radice)
    print(f"\nCartella dell'estrazione: {c}\n")
    if esegui_youtube(p, c, log=print):
        print(f"\nFatto. I file sono in: {c}")


def opzioni_comuni(sp):
    sp.add_argument("--parole", type=lista, default=[], help="parole chiave separate da virgola; * per i suffissi")
    sp.add_argument("--tutte", action="store_true", help="richiede tutte le parole (altrimenti basta una)")
    sp.add_argument("--cerca-in", choices=["testo", "titolo"], default="testo")
    sp.add_argument("--escludi-riservati", action="store_true",
                    help="scarta gli articoli che la testata dichiara riservati agli abbonati")
    sp.add_argument("--formati", type=lista, default=list(FORMATI))
    sp.add_argument("--max", type=int, default=None, help="numero massimo di articoli")
    sp.add_argument("--pausa", type=float, default=PAUSA_DEFAULT, help="secondi tra le richieste (minimo 1)")
    sp.add_argument("--cartella", default=None, help="radice alternativa al Desktop/Scraper_Testate")
    sp.add_argument("--no-grezzi", action="store_true", help="non conservare gli HTML originali")


def riga_di_comando(argv):
    ap = argparse.ArgumentParser(description="Scraper didattico delle testate giornalistiche")
    sub = ap.add_subparsers(dest="comando", required=True)
    sp = sub.add_parser("data", help="articoli di una testata in un intervallo di date")
    sp.add_argument("testata", choices=list(TESTATE))
    sp.add_argument("--dal", type=data_valida, required=True)
    sp.add_argument("--al", type=data_valida, default=date.today().isoformat())
    opzioni_comuni(sp)
    sp = sub.add_parser("elenco", help="articoli a partire da una pagina di sezione, tag o rubrica")
    sp.add_argument("url")
    sp.add_argument("--dal", type=data_valida)
    sp.add_argument("--al", type=data_valida)
    opzioni_comuni(sp)
    sp = sub.add_parser("link", help="uno o più articoli dai loro indirizzi")
    sp.add_argument("urls", nargs="+")
    opzioni_comuni(sp)
    sp = sub.add_parser("verifica", help="controllo tecnico di una testata")
    sp.add_argument("testata", choices=list(TESTATE))
    sp.add_argument("--pausa", type=float, default=PAUSA_DEFAULT)
    sub.add_parser("testate", help="elenco delle testate disponibili")
    sub.add_parser("diagnosi", help="controlla Python, librerie, ffmpeg e deno")
    sp = sub.add_parser("prova", help="estrazioni reali su periodi casuali per tutte le testate")
    sp.add_argument("casi", nargs="*", help="testate o casi da provare (tutti se omessi)")
    sp.add_argument("--max", type=int, default=20)
    sp.add_argument("--seme", type=int, default=None, help="per ripetere esattamente una prova")
    sp.add_argument("--minuti", type=int, default=10, help="tempo massimo per ciascuna testata")
    sp = sub.add_parser("collaudo", help="breve estrazione di prova e verifica della paginazione")
    sp.add_argument("chiavi", nargs="*", help="testate da collaudare (le nuove se omesse)")
    sp = sub.add_parser("ricognizione", help="analisi tecnica di nuove testate candidate")
    sp.add_argument("chiavi", nargs="*", help="testate da analizzare (tutte se omesse)")
    sp = sub.add_parser("youtube", help="trascrizioni e metadati di video YouTube")
    sp.add_argument("urls", nargs="*", help="link di video, playlist o canali (tra virgolette)")
    sp.add_argument("--file", help="file di testo con un link per riga")
    sp.add_argument("--cerca", help="ricerca su YouTube per parole")
    sp.add_argument("--per-data", action="store_true", help="ordina la ricerca per data invece che per pertinenza")
    sp.add_argument("--dal", type=data_valida)
    sp.add_argument("--al", type=data_valida)
    sp.add_argument("--parole", type=lista, default=[], help="filtro su titolo, descrizione e trascrizione")
    sp.add_argument("--max", type=int, default=None)
    sp.add_argument("--trascrizione", choices=["auto", "sottotitoli", "whisper"], default="auto")
    sp.add_argument("--lingua", default=None, help="es. it; consigliata per Whisper su audio scadente")
    sp.add_argument("--modello", default="small", help="tiny, base, small, medium, large-v3")
    sp.add_argument("--device", default="auto")
    sp.add_argument("--compute-type", default="int8")
    sp.add_argument("--media", choices=["entrambi", "video", "audio", "nessuno"], default="entrambi")
    sp.add_argument("--max-altezza", type=int, default=None, help="altezza massima del video, es. 720")
    sp.add_argument("--timecode-docx", action="store_true")
    sp.add_argument("--cookies-from-browser", default=None, help="chrome, firefox, safari, edge")
    sp.add_argument("--cookies-file", default=None)
    sp.add_argument("--cartella", default=None)
    args = ap.parse_args(argv)

    if args.comando == "youtube":
        sorgenti = list(args.urls)
        if args.file:
            sorgenti += [r.strip() for r in Path(args.file).read_text(encoding="utf-8").splitlines()
                         if r.strip() and not r.startswith("#")]
        if not sorgenti and not args.cerca:
            sys.exit("Indica almeno un link, un file di link (--file) o una ricerca (--cerca).")
        p = ParametriYT(sorgenti=list(dict.fromkeys(sorgenti)), cerca=args.cerca,
                        ordina_per_data=args.per_data, dal=args.dal, al=args.al, parole=args.parole,
                        max_video=args.max, trascrizione=args.trascrizione, lingua=args.lingua,
                        modello=args.modello, device=args.device, compute_type=args.compute_type,
                        media=args.media, max_altezza=args.max_altezza, timecode_docx=args.timecode_docx,
                        cookies_browser=args.cookies_from_browser, cookies_file=args.cookies_file)
        avvia_youtube(p, args.cartella)
        return

    if args.comando == "prova":
        from motore.prova import PIANO, prova
        ignoti = [c for c in args.casi if c not in PIANO]
        if ignoti:
            sys.exit(f"Casi non previsti: {ignoti}. Disponibili: {', '.join(PIANO)}")
        prova(args.casi, massimo=args.max, seme=args.seme, minuti=args.minuti)
        return
    if args.comando == "collaudo":
        from motore.collaudo import collauda
        from motore.testate.seconda_ondata import NUOVE
        chiavi = args.chiavi or [t.chiave for t in NUOVE]
        ignote = [k for k in chiavi if k not in TESTATE]
        if ignote:
            sys.exit(f"Testate non previste: {ignote}")
        collauda(chiavi)
        return
    if args.comando == "ricognizione":
        from motore.ricognizione import CANDIDATE, esegui_ricognizione
        ignote = [k for k in args.chiavi if k not in CANDIDATE]
        if ignote:
            sys.exit(f"Testate non previste: {ignote}. Disponibili: {', '.join(CANDIDATE)}")
        esegui_ricognizione(args.chiavi)
        return
    if args.comando == "diagnosi":
        from motore.diagnosi import diagnosi
        diagnosi()
        return
    if args.comando == "testate":
        for k, t in TESTATE.items():
            print(f"{k:12} {t.nome:22} {t.note_ricerca_data}")
        return
    if args.comando == "verifica":
        rete = Rete(pausa=args.pausa, log=print)
        rep = verifica(args.testata, rete, log=print)
        out = radice_locale() / "_ricognizione" / date.today().isoformat()
        out.mkdir(parents=True, exist_ok=True)
        (out / f"verifica_{args.testata}.txt").write_text(rep, encoding="utf-8")
        print("\n" + rep + f"\nSalvato in {out}")
        return
    comuni = dict(parole=args.parole, tutte=args.tutte, cerca_in=args.cerca_in,
                  escludi_riservati=args.escludi_riservati,
                  formati=[f for f in args.formati if f in FORMATI], max_articoli=args.max)
    if args.comando == "data":
        if args.dal > args.al:
            sys.exit("La data iniziale è successiva a quella finale.")
        p = Parametri("data", testata=args.testata, dal=args.dal, al=args.al, **comuni)
    elif args.comando == "elenco":
        p = Parametri("elenco", elenco=args.url, dal=args.dal, al=args.al, **comuni)
    else:
        p = Parametri("link", link=args.urls, **comuni)
    avvia(p, args)


# ------------------------------------------------------------------ modalità guidata
def chiedi(domanda, valida=None, default=None):
    while True:
        r = input(f"{domanda}{f' [{default}]' if default else ''}: ").strip() or (default or "")
        if valida is None or valida(r):
            return r
        print("  Valore non valido, riprova.")


def guidata():
    print("SCRAPER DIDATTICO DELLE TESTATE GIORNALISTICHE\n")
    chiavi = list(TESTATE)
    print("Come vuoi partire?")
    print("  1  Articoli di una testata in un intervallo di date")
    print("  2  Da una pagina di sezione, tag o rubrica (incolla il link)")
    print("  3  Da uno o più link di articoli")
    print("  4  YouTube: video, playlist, canali o ricerca")
    modo = chiedi("Scelta", lambda r: r in ("1", "2", "3", "4"))
    if modo == "4":
        return guidata_youtube()
    def ok_data(r):
        try:
            return bool(RE_DATA.match(r)) and bool(date.fromisoformat(r))
        except ValueError:
            return False
    ok_data_o_vuoto = lambda r: r == "" or ok_data(r)
    testata = elenco = None
    link, dal, al = [], None, None
    if modo == "1":
        for i, k in enumerate(chiavi, 1):
            print(f"  {i}  {TESTATE[k].nome}")
        testata = chiavi[int(chiedi("Testata", lambda r: r.isdigit() and 1 <= int(r) <= len(chiavi))) - 1]
        dal = chiedi("Dal (AAAA-MM-GG)", ok_data)
        al = chiedi("Al (AAAA-MM-GG)", lambda r: ok_data(r) and r >= dal, date.today().isoformat())
    elif modo == "2":
        elenco = chiedi("Link della pagina elenco", lambda r: r.startswith("http"))
        dal = chiedi("Dal (AAAA-MM-GG, invio per nessun limite)", ok_data_o_vuoto) or None
        al = chiedi("Al (AAAA-MM-GG, invio per nessun limite)", ok_data_o_vuoto) or None
    else:
        print("Incolla i link, uno per riga; riga vuota per finire.")
        while True:
            r = input("  > ").strip()
            if not r:
                break
            if r.startswith("http"):
                link.append(r)
        if not link:
            sys.exit("Nessun link inserito.")
    parole = lista(chiedi("Parole chiave separate da virgola (invio per nessuna)", default=""))
    cerca_in = "testo"
    if parole:
        cerca_in = "titolo" if chiedi("Cercarle solo nel titolo? (s/n)", lambda r: r in "sn", "n") == "s" else "testo"
    formati = lista(chiedi("Formati", default=",".join(FORMATI)))
    p = Parametri({"1": "data", "2": "elenco", "3": "link"}[modo], testata=testata, link=link,
                  elenco=elenco, dal=dal, al=al, parole=parole, cerca_in=cerca_in,
                  formati=[f for f in formati if f in FORMATI] or list(FORMATI))
    avvia(p, argparse.Namespace(cartella=None, pausa=PAUSA_DEFAULT, no_grezzi=False))


def guidata_youtube():
    print("Incolla link di video, playlist o canali, uno per riga; riga vuota per finire.")
    print("(Lascia vuoto per fare invece una ricerca su YouTube.)")
    sorgenti = []
    while True:
        r = input("  > ").strip()
        if not r:
            break
        if r.startswith("http"):
            sorgenti.append(r)
    cerca = None
    if not sorgenti:
        cerca = chiedi("Parole da cercare su YouTube", lambda r: bool(r))
    ok = lambda r: r == "" or bool(RE_DATA.match(r))
    dal = chiedi("Dal (AAAA-MM-GG, invio per nessun limite)", ok) or None
    al = chiedi("Al (AAAA-MM-GG, invio per nessun limite)", ok) or None
    mx = chiedi("Numero massimo di video (invio per nessun limite)", lambda r: r == "" or r.isdigit())
    lingua = chiedi("Lingua dei video (es. it; invio per riconoscimento automatico)", default="") or None
    media = {"1": "entrambi", "2": "video", "3": "audio", "4": "nessuno"}[chiedi(
        "Scaricare 1 video e audio, 2 solo video, 3 solo audio, 4 nessuno", lambda r: r in "1234", "1")]
    p = ParametriYT(sorgenti=sorgenti, cerca=cerca, dal=dal, al=al, max_video=int(mx) if mx else None,
                    lingua=lingua, media=media)
    avvia_youtube(p)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        guidata()
    else:
        riga_di_comando(sys.argv[1:])
