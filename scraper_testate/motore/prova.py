"""Prova estesa: per ogni testata un'estrazione reale in un periodo scelto a caso entro la copertura
verificata, con riepilogo unico. Le estrazioni restano nelle normali cartelle, per controllarle."""
import json
import random
import statistics
import time
from datetime import date, timedelta
from pathlib import Path

from .config import radice_locale
from .destinazioni import CartellaLocale
from .esecuzione import cartella_per, esegui
from .modello import Parametri
from .rete import Rete
from .testate import TESTATE

OGGI = date.today()

# (modalità, inizio della copertura, giorni del periodo, elenco di partenza per i casi "elenco")
PIANO = {
    "ilgiornale": ("data", OGGI - timedelta(days=150), 3, None),
    "ilgiornale_tag": ("elenco", date(2017, 1, 1), 7, "https://www.ilgiornale.it/tag/immigrazione/"),
    "avvenire": ("data", date(2012, 1, 1), "mese", None),
    "fatto": ("data", date(2012, 1, 1), 2, None),
    "ansa": ("data", OGGI - timedelta(days=2), 2, None),
    "ilpost": ("data", date(2010, 6, 1), "mese", None),
    "libero": ("data", date(2008, 1, 1), "mese", None),
    "manifesto": ("data", OGGI - timedelta(days=700), 7, None),
    "mattino": ("data", OGGI, 1, None),
    "mattino_sezione": ("elenco", OGGI - timedelta(days=60), 5, "https://www.ilmattino.it/napoli/cronaca/"),
    "messaggero": ("data", OGGI, 1, None),
    "corriere": ("data", date(2020, 6, 1), 2, None),
    "repubblica": ("data", date(2021, 1, 1), "mese", None),
    "lastampa": ("data", date(2022, 8, 1), "mese", None),
    "verita": ("data", OGGI - timedelta(days=700), 7, None),
    "sole24ore": ("data", OGGI - timedelta(days=30), 5, None),
    "independent": ("data", OGGI - timedelta(days=80), 2, None),
    "mirror": ("data", date(2010, 1, 1), 1, None),
    "elmundo": ("data", date(2015, 1, 1), 2, None),
    "fatto_parole": ("data", date(2015, 1, 1), 30, None),
    "avvenire_parole": ("data", date(2015, 1, 1), "mese", None),
    "verita_parole": ("data", OGGI - timedelta(days=700), 30, None),
    "ilpost_parole": ("data", date(2015, 1, 1), "mese", None),
    "corriere_parole": ("data", OGGI - timedelta(days=200), 30, None),
    "sole24ore_parole": ("data", OGGI - timedelta(days=200), 30, None),
}

# pagine elenco (sezioni, tag) di ogni testata, per provare il comando «elenco»
ELENCHI = {
    "avvenire": "https://www.avvenire.it/tag/migranti_4439",
    "fatto": "https://www.ilfattoquotidiano.it/cronaca/",
    "ilpost": "https://www.ilpost.it/italia/",
    "libero": "https://www.liberoquotidiano.it/politica/",
    "manifesto": "https://ilmanifesto.it/sezioni/politica",
    "messaggero": "https://www.ilmessaggero.it/roma/",
    "corriere": "https://www.corriere.it/cronache/",
    "repubblica": "https://www.repubblica.it/cronaca/",
    "lastampa": "https://www.lastampa.it/cronaca/",
    "verita": "https://www.laverita.info/mondo",
    "sole24ore": "https://www.ilsole24ore.com/sez/italia",
    "independent": "https://www.independent.co.uk/news/uk/politics",
    "mirror": "https://www.mirror.co.uk/news/politics/",
    "elmundo": "https://www.elmundo.es/espana.html",
}
# pagine elenco che il sito non permette di sfogliare oltre la prima: si provano sugli ultimi giorni
SOLO_PRIMA_PAGINA = ("corriere", "manifesto", "sole24ore", "independent", "mirror", "elmundo", "libero")
for _k, _u in ELENCHI.items():
    PIANO.setdefault(f"{_k}_elenco", ("elenco", OGGI - timedelta(days=2), 3, _u) if _k in SOLO_PRIMA_PAGINA
                     else ("elenco", OGGI - timedelta(days=20), 5, _u))

# fonti esterne di scoperta: Wayback per le testate con la data nel percorso, GDELT su due testate
PIANO.update({
    "ansa_wayback": ("data", date(2023, 1, 1), 1, None),
    "fatto_wayback": ("data", date(2018, 1, 1), 1, None),
    "repubblica_gdelt": ("data", date(2019, 1, 1), 7, None),
    "corriere_gdelt": ("data", date(2019, 1, 1), 7, None),
})

# casi che provano la ricerca per parole con il motore della testata
PAROLE = {c: ["migrant*"] for c in PIANO if c.endswith(("_parole", "_gdelt"))}
FONTE = {c: c.rsplit("_", 1)[1] for c in PIANO if c.endswith(("_wayback", "_gdelt"))}
PAROLE_GDELT = {c: ["migrants", "refugees"] for c in PIANO if c.endswith("_gdelt")}


def periodo(rnd, inizio, durata):
    fine_max = OGGI - timedelta(days=1)
    if durata == "mese":
        mesi = (fine_max.year - inizio.year) * 12 + fine_max.month - inizio.month
        k = rnd.randint(0, max(0, mesi - 1))
        a, m = inizio.year + (inizio.month - 1 + k) // 12, (inizio.month - 1 + k) % 12 + 1
        dal = date(a, m, 1)
        al = (date(a + (m == 12), m % 12 + 1, 1) - timedelta(days=1))
        return dal, min(al, fine_max)
    spazio = max(0, (fine_max - inizio).days - durata)
    dal = inizio + timedelta(days=rnd.randint(0, spazio))
    return dal, min(dal + timedelta(days=durata - 1), OGGI)


def prova(chiavi=None, massimo=20, seme=None, log=print, minuti=10):
    seme = seme if seme is not None else int(time.time()) % 100000
    chiavi = chiavi or list(PIANO)
    radice = radice_locale()
    R = [f"PROVA SU PERIODI CASUALI  {OGGI.isoformat()}  seme {seme}  (al massimo {massimo} articoli per testata)",
         "Per ripetere la stessa prova: python scraper.py prova --seme " + str(seme), "=" * 78]
    sintesi, esiti = [], []
    for caso in chiavi:
        modalita, inizio, durata, elenco = PIANO[caso]
        k = caso.rsplit("_", 1)[0] if caso.rsplit("_", 1)[0] in TESTATE else caso.split("_")[0]
        t = TESTATE[k]
        dal, al = periodo(random.Random(f"{seme}-{caso}"), inizio, durata)
        log(f"\n>>> {t.nome} ({caso}): {dal} / {al}  (lettura delle sitemap e degli elenchi in corso...)")
        p = Parametri(modalita, testata=k if modalita == "data" else None, elenco=elenco,
                      dal=dal.isoformat(), al=al.isoformat(), max_articoli=massimo, parole=PAROLE.get(caso, []),
                      fonte=FONTE.get(caso, "auto"), parole_gdelt=PAROLE_GDELT.get(caso, []))
        cart = cartella_per(p, radice)
        t0 = time.monotonic()
        R += ["", f"## {t.nome}  [{caso}]  {modalita}  {dal} / {al}" + (f"  da {elenco}" if elenco else "")]
        try:
            rete = Rete(log=lambda m: None)
            esegui(p, CartellaLocale(cart), cart / "_lavoro", rete=rete, salva_grezzi=False,
                   log=lambda m: log("   " + m.strip()) if m.strip().startswith(("[", "ATTENZIONE", "Fermata")) else None,
                   tempo_max=minuti * 60)
            durata_min = (time.monotonic() - t0) / 60
            scheda = (cart / "scheda_estrazione.txt").read_text(encoding="utf-8")
            arts = [json.loads(r) for r in (cart / "corpus.jsonl").read_text(encoding="utf-8").splitlines()] \
                if (cart / "corpus.jsonl").exists() else []
            fuori = [a for a in arts if a["data"][:10] and not (dal.isoformat() <= a["data"][:10] <= al.isoformat())]
            sosp = sum(a["sospetto"] for a in arts)
            parz = sum(a["parziale"] for a in arts)
            ris = sum(a["accesso_libero"] is False for a in arts)
            coer = statistics.mean(a["coerenza"] for a in arts) if arts else 0
            parole = statistics.median(len(a["testo"].split()) for a in arts) if arts else 0
            esaminati = scheda.split("Indirizzi esaminati: ")[1].split("\n")[0]
            R.append(f"  raccolti {len(arts)}  esaminati {esaminati}  richieste {rete.richieste}  "
                     f"durata {durata_min:.1f} min")
            R.append(f"  coerenza media {coer:.2f}  parole (mediana) {parole:.0f}  da controllare {sosp}  "
                     f"parziali {parz}  riservati {ris}  date fuori periodo {len(fuori)}")
            for blocco in ("AVVISI SULLA COPERTURA", "ERRORI"):
                if blocco in scheda:
                    righe = scheda.split(blocco)[1].strip().split("\n\n")[0].splitlines()[:3]
                    R.append(f"  {blocco.lower()}: " + " | ".join(r.strip() for r in righe))
            for a in arts[:3]:
                R.append(f"  - {a['data'][:10]}  {a['titolo'][:85]}  ({len(a['testo'].split())} parole, "
                         f"{a['metodo']}, coerenza {a['coerenza']})")
            sosp_es = [a for a in arts if a["sospetto"]][:2]
            for a in sosp_es:
                R.append(f"    da controllare: {a['url']}  inizio {a['testo'][:120]!r}")
            R.append(f"  cartella: {cart}")
            sintesi.append((t.nome, caso, len(arts), sosp, parz, len(fuori), durata_min))
            esiti.append({"caso": caso, "testata": k, "modalita": modalita, "fonte": FONTE.get(caso, "auto"),
                          "dal": dal.isoformat(), "al": al.isoformat(), "elenco": elenco,
                          "parole": PAROLE.get(caso, []), "raccolti": len(arts), "esaminati": esaminati,
                          "da_controllare": sosp, "parziali": parz, "riservati": ris,
                          "fuori_periodo": len(fuori), "parole_mediana": parole, "coerenza": round(coer, 2),
                          "minuti": round(durata_min, 1), "interrotta": "INTERROTTA" in scheda,
                          "avvisi": scheda.split("AVVISI SULLA COPERTURA")[1].strip().split("\n\n")[0]
                          if "AVVISI SULLA COPERTURA" in scheda else "",
                          "esempi": [a["titolo"][:100] for a in arts[:3]], "cartella": str(cart)})
        except KeyboardInterrupt:
            R.append("  interrotta dall'utente")
            break
        except Exception as e:
            R.append(f"  ERRORE: {e!r}")
            sintesi.append((t.nome, caso, 0, 0, 0, 0, (time.monotonic() - t0) / 60))
            esiti.append({"caso": caso, "testata": k, "modalita": modalita, "fonte": FONTE.get(caso, "auto"),
                          "dal": dal.isoformat(), "al": al.isoformat(), "elenco": elenco, "raccolti": 0,
                          "errore": str(e), "minuti": round((time.monotonic() - t0) / 60, 1)})
    R += ["", "SINTESI", f"  {'testata':22} {'caso':16} {'raccolti':>8} {'da contr.':>9} {'parziali':>8} {'fuori':>6} {'min':>5}"]
    R += [f"  {n:22} {c:16} {a:>8} {s:>9} {p:>8} {f:>6} {m:>5.1f}" for n, c, a, s, p, f, m in sintesi]
    out = radice / "_ricognizione" / OGGI.isoformat()
    out.mkdir(parents=True, exist_ok=True)
    f = out / f"prova_periodi_{seme}.txt"
    f.write_text("\n".join(R) + "\n", encoding="utf-8")
    (out / f"esiti_{seme}.json").write_text(json.dumps({"data": OGGI.isoformat(), "seme": seme, "massimo": massimo,
                                                         "esiti": esiti}, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
    log(f"\nFatto. Riepilogo in {f}")
    return f
