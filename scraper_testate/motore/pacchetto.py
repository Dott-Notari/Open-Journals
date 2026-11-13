"""Pacchetto per aggiornare la piattaforma online con Claude (chat): regole per testata, interfaccia del
motore, istruzioni e codice. python scraper.py pacchetto  scrive la cartella sul Desktop.

Le regole sono ricavate dal codice (testate, motori di ricerca, paginazione, Wayback) e dalle schede,
più i dati di copertura qui sotto, verificati con le prove del 12 novembre 2026."""
import json
import re
import shutil
import zipfile
from dataclasses import fields
from datetime import date
from pathlib import Path

from .config import PAUSA_DEFAULT, PAUSA_MINIMA, UA, VERSIONE, cartella_desktop
from .modello import Parametri

# copertura verificata: (archivio per data dal, nota sulla profondità dell'archivio, profondità della ricerca)
COPERTURA = {
    "fatto": ("2009-01-01", "completo", "circa due anni (il feed si ferma dopo 150-200 pagine)"),
    "avvenire": ("2000-01-01", "completo; per gli anni meno recenti l'archivio online è una selezione", "filtro per date sul sito"),
    "ilgiornale": (None, "sitemap giornaliere solo recenti; prima, pagine tag e macrosezioni (circa 10.000 articoli ciascuna)", None),
    "ansa": (None, "solo gli ultimi due giorni circa; il passato con fonte wayback", None),
    "ilpost": ("2009-01-01", "completo (brevi «flashes» escluse)", "tutto l'archivio"),
    "libero": (None, "dalla migrazione dell'11 novembre 2026 sitemap giornaliere; prima elenchi API (circa 3,5 mesi per "
                     "tutto il sito, mesi o anni per sezione); oltre, fonte wayback", None),
    "manifesto": (None, "sitemap per data di modifica, verificate articolo per articolo", None),
    "mattino": (None, "solo le uscite del giorno (sitemap news); il passato con elenco o wayback", None),
    "messaggero": (None, "solo le uscite del giorno (sitemap news); il passato con elenco o wayback", None),
    "corriere": ("2020-05-27", "sitemap giornaliere", "tutto l'archivio della ricerca (anche prima del 2020)"),
    "repubblica": ("2010-01-01", "sitemap mensili; il mese in corso solo gli ultimi giorni", None),
    "lastampa": ("2022-08-01", "sitemap mensili (circa 50 mesi); il mese in corso solo gli ultimi giorni", None),
    "verita": ("2018-12-01", "completo tramite API WordPress", "filtro per date sul sito"),
    "sole24ore": (None, "sitemap news di sezione, profondità variabile", "al massimo circa 12.500 risultati per parola"),
    "independent": (None, "ultimi 90 giorni circa (sitemap giornaliere); prima, fonte wayback", None),
    "mirror": ("1998-01-01", "sitemap mensili filtrate per data di modifica", None),
    "elmundo": (None, "emeroteca giornaliera (profondità non verificata oltre il 2015)", None),
    "guardian": ("1999-01-01", "API ufficiale con chiave", "API ufficiale"),
}

STATO = {"guardian": "non attivata: serve la chiave GUARDIAN_API_KEY, il progetto ha scelto di non usarla"}

ESCLUSE_MOTIVI = None   # dalle schede


def regole():
    from .schede import ESCLUSE, FONTI_NUOVE, S
    from .testate import TESTATE
    from .testate.base import Testata
    from .testate.ricerca import MOTORI
    from .testate.estere import ESTERE
    estere = {t.chiave for t in ESTERE}
    out = []
    for k, t in TESTATE.items():
        sc = S.get(k, {})
        dal, nota_arch, prof_ric = COPERTURA.get(k, (None, "", None))
        motore = MOTORI.get(k)
        ha_ricerca = bool(motore) or k == "guardian"
        pag = t.pagina_elenco("https://esempio/elenco/", 2)
        solo_prima = pag is None
        wb_eff = type(t).wayback_prefissi is not Testata.wayback_prefissi   # interrogazioni per giorno
        crawl = {"mirror": 10}.get(k)
        fonti = ["auto", "archivio"] + (["ricerca"] if ha_ricerca else []) + ["wayback", "gdelt"]
        out.append({
            "chiave": k, "nome": t.nome, "sito": sc.get("sito", ""), "dominio": t.dominio,
            "lingua": "en" if k in ("independent", "mirror", "guardian") else "es" if k == "elmundo" else "it",
            "gruppo": "estere" if k in estere else "italiane",
            "stato": STATO.get(k, "attiva"), "piattaforma_sito": sc.get("piattaforma", ""),
            "modalita": {
                "data": {
                    "disponibile": True, "copertura_dal": dal, "copertura": nota_arch,
                    "come": t.note_ricerca_data,
                    "fonti_consentite": fonti, "fonte_predefinita": "auto",
                },
                "parole_con_ricerca_del_sito": {
                    "disponibile": ha_ricerca,
                    "motore": motore[1] if motore else ("API ufficiale" if k == "guardian" else None),
                    "solo_parole_intere": bool(motore and motore[2]),
                    "profondita": prof_ric,
                    "se_non_arriva_al_periodo": "passa da solo all'archivio per data" if ha_ricerca else None,
                    "motivo_se_assente": None if ha_ricerca else sc.get("ricerca", ("", ""))[1],
                },
                "parole_come_filtro": {"disponibile": True, "cerca_in": ["testo", "titolo"],
                                       "nota": "con cerca_in=titolo gli articoli senza le parole nell'indirizzo non vengono scaricati"},
                "elenco": {"disponibile": True, "solo_prima_pagina": solo_prima,
                           "paginazione": None if solo_prima else
                           re.sub(r"(?<=[/=])2(?=/|$)", "{n}", pag.replace("https://esempio/elenco", "{base}")),
                           "pagine": sc.get("elenchi", "")},
                "link": {"disponibile": True},
                "wayback": {"disponibile": True, "efficiente": bool(wb_eff), "nota": sc.get("wayback", "")},
                "gdelt": {"disponibile": True, "sperimentale": True, "parole": "in inglese (parole_gdelt)",
                          "nota": sc.get("gdelt", "")},
                "rss": {"nel_motore": False, "nota": sc.get("rss", "")},
            },
            "vincoli": {
                "robots_txt": sc.get("robots", ""), "crawl_delay_secondi": crawl,
                "pausa_minima_secondi": max(PAUSA_MINIMA, crawl or 0),
                "testo": sc.get("testo", ""),
                "paywall": "mai aggirato: gli articoli riservati hanno il testo che la testata rende pubblico",
            },
            "consigli": sc.get("consigli", ""),
            "risorse_non_usate": sc.get("altre", []),
        })
    escluse = [{"testata": n, "motivo": m} for n, m in ESCLUSE.items()]
    fonti = [{"nome": n, "descrizione": m} for n, m in FONTI_NUOVE]
    return out, escluse, fonti


def interfaccia():
    campi = []
    note = {
        "modalita": "\"data\" | \"elenco\" | \"link\"",
        "testata": "chiave della testata (solo con modalita=data; con elenco/link si riconosce dall'indirizzo)",
        "link": "lista di URL di articoli (modalita=link)",
        "elenco": "URL di una pagina di sezione, tag o autore (modalita=elenco)",
        "dal": "AAAA-MM-GG (obbligatoria con modalita=data)", "al": "AAAA-MM-GG, predefinita oggi",
        "parole": "lista; * per i suffissi (migrant*)", "tutte": "true = tutte le parole, false = almeno una",
        "escludi_riservati": "scarta gli articoli dichiarati riservati agli abbonati",
        "cerca_in": "\"testo\" | \"titolo\"", "formati": "sottoinsieme di docx, txt, html, xlsx, jsonl, tlab",
        "max_articoli": "intero o null", "usa_ricerca": "false = non usare la ricerca del sito (come fonte=archivio)",
        "fonte": "\"auto\" | \"archivio\" | \"ricerca\" | \"wayback\" | \"gdelt\" (solo modalita=data)",
        "parole_gdelt": "parole in inglese per fonte=gdelt",
    }
    for f in fields(Parametri):
        d = f.default if f.default is not f.default_factory else []
        try:
            json.dumps(d)
        except TypeError:
            d = []
        campi.append({"campo": f.name, "predefinito": d, "descrizione": note.get(f.name, "")})
    return campi


def _md_regole(testate, escluse, fonti):
    R = [f"# Regole di estrazione per testata (motore {VERSIONE}, {date.today().isoformat()})", "",
         "Generato da `python scraper.py pacchetto`. La versione leggibile da un programma è `02_regole_testate.json`.", ""]
    for t in testate:
        m = t["modalita"]
        R += [f"## {t['nome']} (`{t['chiave']}`)", "",
              f"Sito {t['sito']} · lingua {t['lingua']} · stato: {t['stato']}", "",
              f"- **Per data**: " + (f"copertura dal {m['data']['copertura_dal']}" if m['data']['copertura_dal']
                                     else "copertura non fissa") + f"; {m['data']['copertura']}. "
              f"Fonti consentite: {', '.join(m['data']['fonti_consentite'])}.",
              f"- **Parole con la ricerca del sito**: " + (
                  f"sì, {m['parole_con_ricerca_del_sito']['motore']}"
                  + (" (parole intere: migrant* viene cercato come migrant, migranta, migrante, migranti, migranto)"
                     if m['parole_con_ricerca_del_sito']['solo_parole_intere'] else "")
                  + (f"; profondità: {m['parole_con_ricerca_del_sito']['profondita']}" if m['parole_con_ricerca_del_sito']['profondita'] else "")
                  if m['parole_con_ricerca_del_sito']['disponibile'] else
                  f"no ({m['parole_con_ricerca_del_sito']['motivo_se_assente']})"),
              "- **Parole come filtro**: sì, su testo o solo titolo.",
              f"- **Elenco**: " + ("solo la prima pagina" if m['elenco']['solo_prima_pagina'] else
                                   f"paginazione `{m['elenco']['paginazione']}`") + f"; {m['elenco']['pagine']}.",
              "- **Link**: sì.",
              f"- **Wayback**: {'efficiente' if m['wayback']['efficiente'] else 'lenta'}; {m['wayback']['nota']}.",
              f"- **GDELT**: sperimentale; {m['gdelt']['nota']}.",
              f"- **RSS** (non nel motore): {m['rss']['nota']}.",
              f"- **Vincoli**: pausa minima {t['vincoli']['pausa_minima_secondi']} s"
              + (f" (Crawl-delay {t['vincoli']['crawl_delay_secondi']} s)" if t['vincoli']['crawl_delay_secondi'] else "")
              + f"; robots.txt: {t['vincoli']['robots_txt']}; testo: {t['vincoli']['testo']}.",
              f"- **Consiglio**: {t['consigli']}", ""]
    R += ["## Testate escluse", ""] + [f"- **{e['testata']}**: {e['motivo']}" for e in escluse]
    R += ["", "## Fonti e modalità da valutare", ""] + [f"- **{f['nome']}**: {f['descrizione']}" for f in fonti]
    return "\n".join(R) + "\n"


def _md_interfaccia(campi):
    R = [f"# Interfaccia del motore {VERSIONE}", "",
         "La piattaforma usa il motore così:", "", "```python",
         "from motore.esecuzione import esegui",
         "from motore.destinazioni import ZipMemoria",
         "from motore.modello import Parametri",
         "from motore.rete import Rete", "",
         "p = Parametri(modalita=\"data\", testata=\"verita\", dal=\"2026-01-01\", al=\"2026-01-31\",",
         "              parole=[\"migrant*\"], fonte=\"auto\", formati=[\"xlsx\", \"jsonl\", \"docx\"])",
         "zip_bytes = esegui(p, ZipMemoria(), None, rete=Rete(pausa=2), tempo_max=None)", "```", "",
         "`esegui` restituisce lo zip dell'estrazione (stessa struttura della cartella locale, senza `_lavoro`). "
         "Se la testata non si può interrogare in quel modo solleva `motore.testate.NonSupportato` con un messaggio "
         "da mostrare all'utente.", "",
         "## Campi di `Parametri`", "", "| Campo | Predefinito | Descrizione |", "|---|---|---|"]
    R += [f"| `{c['campo']}` | `{json.dumps(c['predefinito'], ensure_ascii=False)}` | {c['descrizione']} |" for c in campi]
    R += ["", "## Regole generali di esecuzione", "",
          f"- User-Agent fisso: `{UA}`.",
          f"- Pausa predefinita {PAUSA_DEFAULT} s, minima {PAUSA_MINIMA} s tra richieste allo stesso sito; il Crawl-delay "
          "del robots.txt, se maggiore, la sostituisce. GDELT almeno 6 s, Wayback almeno 2 s.",
          "- Ogni richiesta è confrontata con il robots.txt del sito (RFC 9309, con caratteri jolly): gli indirizzi "
          "esclusi non vengono scaricati e sono contati nella scheda di estrazione.",
          "- Nessun aggiramento di paywall o protezioni anti-bot: con una protezione attiva il motore solleva "
          "`motore.rete.Bloccato` e l'estrazione si ferma.",
          "- `tempo_max` (secondi) vale per lo scaricamento degli articoli, non per la raccolta degli indirizzi.",
          "- Con Wayback e GDELT si usano solo gli indirizzi; gli articoli si scaricano dal sito della testata.",
          "- Doppioni (stesso titolo e data) scartati; ricerche che non arrivano al periodo passano all'archivio.", "",
          "## Novità rispetto alla versione 1.12", "",
          "- Nuovi campi `usa_ricerca`, `fonte`, `parole_gdelt` (i vecchi parametri restano validi).",
          "- Nuove testate: independent, mirror, elmundo, guardian (non attivata). Libero riscritto (nuova piattaforma "
          "del sito), La Verità per data via API, Mirror filtrato per data di modifica.",
          "- Nuovi moduli: `motore/robots.py`, `motore/scoperta.py`, `motore/testate/ricerca.py`, "
          "`motore/testate/estere.py`, `motore/schede.py`, `motore/pacchetto.py`.",
          "- `config.RADICE` vale ora `Siti_API/estrazioni` (solo uso locale; la piattaforma usa ZipMemoria).",
          "- Requisiti invariati (`requirements.txt`)."]
    return "\n".join(R) + "\n"


ISTRUZIONI = """# Istruzioni per Claude: aggiornamento della piattaforma di scraping didattico

## Contesto
Gestisco una piattaforma online che permette a studenti e ricercatori del corso di Sociologia della
comunicazione interculturale di estrarre corpora di articoli di giornale. La piattaforma usa il motore Python
«Scraper didattico delle testate» chiamando `motore.esecuzione.esegui(parametri, ZipMemoria(), None)`.
Ho aggiornato il motore in locale alla versione {versione}: nuove testate, ricerca con i motori dei siti,
fonti Wayback e GDELT, rispetto del robots.txt. Ora devo portare la piattaforma allo stesso livello.

## File allegati
- `02_regole_testate.json`: per ogni testata le modalità consentite, le coperture, i vincoli e i testi d'aiuto.
  È la fonte di verità per le impostazioni.
- `03_regole_testate.md`: la stessa cosa in forma leggibile.
- `04_interfaccia_motore.md`: come chiamare il motore, i campi di `Parametri`, le regole di esecuzione e le
  novità rispetto alla versione 1.12.
- `05_esiti_prove.json`: esiti delle prove reali del {oggi}, caso per caso.
- `06_motore_{versione_file}.zip`: il codice aggiornato del motore (cartella `motore/` e `scraper.py`).
- `07_schede/`: schede dettagliate per testata (Markdown) e riepilogo Excel.

## Cosa ti chiedo
1. **Prima di modificare qualcosa, chiedimi il codice o la configurazione della piattaforma** (form, validazioni,
   elenco testate, chiamata al motore) se non te li ho già dati, e dimmi quali file ti servono.
2. **Aggiorna il motore** sostituendo la cartella `motore/` con quella dello zip. Conserva eventuali personalizzazioni
   della piattaforma e segnalamele.
3. **Aggiorna le impostazioni per testata** seguendo `02_regole_testate.json`:
   - elenco delle testate selezionabili: solo quelle con `"stato": "attiva"`, raggruppate per `gruppo`
     (italiane, estere);
   - per ogni testata mostra solo le opzioni consentite: la scelta della fonte (`fonti_consentite`), l'opzione
     «usa la ricerca del sito» solo se `parole_con_ricerca_del_sito.disponibile` è vero, l'avviso «solo la
     prima pagina» per gli elenchi con `solo_prima_pagina`;
   - validazione delle date: se `dal` è precedente a `copertura_dal`, o la copertura è «solo recente», mostra un
     avviso che proponga `fonte = wayback` invece di bloccare;
   - testi d'aiuto accanto ai campi, presi da `copertura`, `motore`, `profondita`, `consigli`;
   - GDELT solo come opzione avanzata, marcata «sperimentale», con il campo delle parole in inglese;
   - pausa: mai sotto `pausa_minima_secondi` della testata.
4. **Aggiorna la chiamata al motore**, passando i nuovi campi `fonte`, `usa_ricerca` e `parole_gdelt`, e gestisci
   l'eccezione `NonSupportato` mostrando il suo messaggio all'utente.
5. **Restituiscimi** l'elenco delle modifiche, i file modificati completi e una breve lista di controlli da fare
   dopo la pubblicazione (per esempio un'estrazione di prova per testata, con le date indicate in `05_esiti_prove.json`).

## Vincoli da rispettare (non negoziabili)
- Il motore deve continuare a rispettare il robots.txt, a usare il suo User-Agent dichiarato e le pause minime.
  Non aggiungere opzioni per disattivare questi controlli.
- Nessun aggiramento di paywall, verifiche anti-bot, login altrui o copie archiviate per leggere testi riservati.
  Gli articoli riservati restano segnalati e con il testo che la testata rende pubblico.
- Le testate escluse (sezione `escluse` del JSON) non vanno aggiunte.
- Il Guardian resta non attivo finché non lo chiedo.
- I testi raccolti servono per studio e ricerca e non vanno ridistribuiti: mantieni questa nota nell'interfaccia
  e nella scheda di estrazione.

## Domande utili
Se una regola del JSON non trova posto nell'interfaccia attuale, proponi la soluzione più semplice e chiedimi
conferma prima di aggiungere nuove schermate.
"""

LEGGIMI = """# Come usare questo pacchetto con Claude (chat)

Questa cartella contiene tutto quello che serve per far aggiornare a Claude le impostazioni della piattaforma
online di scraping, partendo dal motore locale (`Desktop/Siti_API/motore_testate`, versione {versione}).

## Passi
1. Apri https://claude.ai e crea un **Progetto** (per esempio «Piattaforma scraping testate»).
2. Nelle **conoscenze del progetto** carica:
   - `02_regole_testate.json`, `03_regole_testate.md` e `04_interfaccia_motore.md`;
   - `05_esiti_prove.json`, `06_motore_{versione_file}.zip` e i file di `07_schede/` (bastano i `.md` e l'Excel).
3. Copia il contenuto di `01_ISTRUZIONI_PER_CLAUDE.md` nelle **istruzioni del progetto**, oppure incollalo come
   primo messaggio di una nuova chat nel progetto.
4. Claude ti chiederà il codice o la configurazione attuale della piattaforma: caricali nella chat (i file del
   form, delle validazioni, della lista testate e il punto in cui si chiama il motore).
5. Applica le modifiche che Claude restituisce, poi fai le estrazioni di prova che indica.

## Quando rigenerare il pacchetto
Dopo ogni aggiornamento del motore o nuova prova:
```
cd ~/Desktop/Siti_API/motore_testate
source .venv/bin/activate
python scraper.py prova          # facoltativo: riverifica tutte le testate
python scraper.py schede
python scraper.py pacchetto
```
Il pacchetto viene riscritto in questa cartella con i dati aggiornati.

## Contenuto
| File | A cosa serve |
|---|---|
| `01_ISTRUZIONI_PER_CLAUDE.md` | il compito da dare a Claude, con i vincoli |
| `02_regole_testate.json` | le regole per testata, da usare come configurazione |
| `03_regole_testate.md` | le stesse regole in forma leggibile |
| `04_interfaccia_motore.md` | come la piattaforma chiama il motore e cosa è cambiato |
| `05_esiti_prove.json` | le prove reali, utili per i controlli dopo la pubblicazione |
| `06_motore_{versione_file}.zip` | il codice aggiornato del motore |
| `07_schede/` | le schede per testata e il riepilogo Excel |

## Nota
Non caricare chiavi, password o file `.env`: il pacchetto non ne contiene e non ne servono.
"""


def scrivi_pacchetto(cartella=None, log=print):
    from .config import radice_locale
    from .schede import ultimi_esiti
    radice_motore = Path(__file__).resolve().parent.parent
    cartella = Path(cartella or cartella_desktop() / "Pacchetto_Claude_Piattaforma")
    cartella.mkdir(parents=True, exist_ok=True)
    versione_file = VERSIONE.split()[0]
    testate, escluse, fonti = regole()
    dati = {"motore": VERSIONE, "generato": date.today().isoformat(),
            "regole_generali": {"user_agent": UA, "pausa_predefinita_secondi": PAUSA_DEFAULT,
                                "pausa_minima_secondi": PAUSA_MINIMA, "rispetto_robots_txt": True,
                                "aggiramento_paywall": False,
                                "fonti": {"auto": "ricerca del sito se ci sono parole e la testata la consente, altrimenti archivio",
                                          "archivio": "sitemap, archivi ed elenchi della testata",
                                          "ricerca": "solo il motore di ricerca della testata",
                                          "wayback": "indirizzi dall'indice CDX dell'Internet Archive; articoli scaricati dal sito",
                                          "gdelt": "indirizzi dall'indice GDELT (parole in inglese); sperimentale"}},
            "testate": testate, "escluse": escluse, "fonti_da_valutare": fonti}
    sostituzioni = {"versione": VERSIONE, "versione_file": versione_file, "oggi": date.today().isoformat()}
    (cartella / "00_LEGGIMI.md").write_text(LEGGIMI.format(**sostituzioni), encoding="utf-8")
    (cartella / "01_ISTRUZIONI_PER_CLAUDE.md").write_text(ISTRUZIONI.format(**sostituzioni), encoding="utf-8")
    (cartella / "02_regole_testate.json").write_text(json.dumps(dati, ensure_ascii=False, indent=2), encoding="utf-8")
    (cartella / "03_regole_testate.md").write_text(_md_regole(testate, escluse, fonti), encoding="utf-8")
    (cartella / "04_interfaccia_motore.md").write_text(_md_interfaccia(interfaccia()), encoding="utf-8")
    esiti = sorted(ultimi_esiti(radice_locale()).values(), key=lambda e: (e.get("testata", ""), e["caso"]))
    for e in esiti:
        e.pop("cartella", None)   # percorsi del Mac locale: non servono alla piattaforma
        e.pop("esempi", None)     # titoli degli articoli raccolti: non servono alla configurazione
    (cartella / "05_esiti_prove.json").write_text(json.dumps(esiti, ensure_ascii=False, indent=1), encoding="utf-8")
    for vecchio in cartella.glob("06_motore_*.zip"):
        vecchio.unlink()
    with zipfile.ZipFile(cartella / f"06_motore_{versione_file}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(radice_motore.glob("motore/**/*.py")) + [radice_motore / n for n in
                                                                ("scraper.py", "requirements.txt", "README.md", ".env.esempio")]:
            if f.exists() and "__pycache__" not in f.parts:
                z.write(f, f.relative_to(radice_motore))
    schede = cartella_desktop() / "Siti_API" / "schede_testate"
    dest = cartella / "07_schede"
    shutil.rmtree(dest, ignore_errors=True)
    if schede.exists():
        shutil.copytree(schede, dest, ignore=shutil.ignore_patterns("*.docx", "~$*"))
    log(f"Pacchetto scritto in {cartella}")
    return cartella
