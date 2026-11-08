# Scraper didattico delle testate giornalistiche

Strumento per il corso di Sociologia della comunicazione interculturale. Raccoglie articoli da il Giornale, Avvenire, Il Fatto Quotidiano e ANSA (e, in modalità generica, da qualsiasi altro sito) e li salva in una cartella di lavoro organizzata, nei formati Word, testo, HTML, Excel, JSONL e T-LAB, con una scheda che documenta come è stato costruito il corpus.

## Installazione

Apri la cartella del progetto in Visual Studio Code (File > Apri cartella), seleziona l'interprete di Miniconda con Cmd+Shift+P > «Python: Select Interpreter», poi nel terminale:

```
pip install -r requirements.txt
```

## Uso guidato

```
python scraper.py
```

Lo script chiede come partire (intervallo di date, pagina elenco o link), la testata, le date, le eventuali parole chiave e i formati.

## Uso da riga di comando

```
python scraper.py data avvenire --dal 2026-10-01 --al 2026-10-31 --parole "migrant*,sbarc*"
python scraper.py data fatto --dal 2026-11-01 --al 2026-11-07
python scraper.py data ilgiornale --dal 2026-09-01 --al 2026-09-30 --parole immigrazione --cerca-in titolo
python scraper.py data ansa --dal 2026-11-01
python scraper.py elenco https://www.avvenire.it/tag/migranti_4439 --dal 2026-01-01
python scraper.py elenco https://www.ilfattoquotidiano.it/cervelli-fuga/
python scraper.py link https://www.ilgiornale.it/news/... https://www.ansa.it/...
python scraper.py verifica ilgiornale
python scraper.py testate
```

Le parole chiave si separano con la virgola; l'asterisco vale per qualsiasi finale (`migrant*` trova migrante e migranti, ma non migrazione). Con `--tutte` devono comparire tutte, altrimenti ne basta una. Con `--cerca-in titolo` la ricerca riguarda solo titolo e sommario ed è molto più veloce, perché gli articoli che non corrispondono vengono scartati dall'indirizzo, senza scaricarli. Con `--escludi-riservati` vengono scartati gli articoli che la testata dichiara riservati agli abbonati; senza l'opzione sono inclusi e segnalati nell'indice e nella scheda. Altre opzioni: `--formati docx,xlsx` per scegliere i formati, `--max 200` per fermarsi a un certo numero di articoli, `--pausa 3` per rallentare, `--no-grezzi` per non conservare gli HTML originali.

## Dove finiscono i file

```
Desktop/Scraper_Testate/
  <testata>/<data>_<modalità e parametri>/
    scheda_estrazione.txt      come è stato costruito il corpus
    indice_articoli.xlsx       un articolo per riga, con metadati e controlli di qualità
    corpus_completo.docx       tutti gli articoli in un unico documento
    corpus.jsonl               tutti i dati, per analisi automatiche
    corpus_tlab.txt            corpus con le variabili per T-LAB
    docx/  txt/  html/         un file per articolo
    _lavoro/                   HTML originali, stato per la ripresa, articoli raccolti
  _ricognizione/               verifiche tecniche
```

Se un'estrazione si interrompe (Ctrl+C, rete, blocco del sito), basta rilanciare lo stesso comando: riparte da dove si era fermata nella stessa cartella.

## Come lavora su ciascuna testata

Avvenire: sitemap mensili dal 2000; ogni articolo viene aperto per leggerne la data esatta, quindi su un mese intero servono circa quaranta minuti, molti meno con `--cerca-in titolo`. Le pagine tag (ad esempio /tag/migranti_4439) danno corpora tematici già pronti.

il Giornale: le sitemap coprono solo gli ultimi giorni. Per i periodi precedenti lo script scorre le pagine tag corrispondenti alle parole chiave (ad esempio `--parole immigrazione` usa anche /tag/immigrazione/) e le macrosezioni, saltando con una ricerca binaria alle pagine del periodo richiesto. Ogni elenco del sito è consultabile solo per circa 10.000 articoli: le sezioni generali risalgono di pochi mesi, i tag tematici anche di anni. Quando un periodo non è raggiungibile la scheda lo segnala. Per i periodi lontani conviene partire da un tag con il comando `elenco`.

Il Fatto Quotidiano: archivi per giorno, scorsi pagina per pagina; le date si leggono dall'indirizzo, quindi gli articoli fuori intervallo non vengono scaricati.

ANSA: le sitemap contengono solo le uscite recenti; il testo viene letto dal contenitore dell'articolo nella pagina.

## Testate della seconda ondata

Il Post, Libero, Corriere della Sera, la Repubblica e La Stampa hanno sitemap per mese o per giorno e consentono la ricerca per data su archivi di anni (Il Post dal 2009, Libero dal 2006, Corriere dal maggio 2020, Repubblica e La Stampa sui mesi pubblicati nelle sitemap). La Verità e il manifesto hanno sitemap non ordinate per data, filtrate per data di modifica e poi verificate articolo per articolo. Il Mattino, Il Messaggero e Il Sole 24 Ore espongono soltanto le uscite recenti: per i periodi precedenti si parte dalle pagine di sezione con il comando `elenco`. Fanpage respinge qualsiasi richiesta automatica, compresa quella al robots.txt, e non è inclusa; i suoi video restano raggiungibili dal modulo YouTube.

Il comando `python scraper.py collaudo` esegue una breve estrazione reale per ciascuna nuova testata e prova i formati di paginazione delle pagine elenco, scrivendo un unico riepilogo in `_ricognizione/<data>/collaudo.txt`. Si può limitare ad alcune testate (`python scraper.py collaudo corriere ilpost`).

## Prova estesa

`python scraper.py prova` esegue per ogni testata un'estrazione reale (20 articoli al massimo) in un periodo scelto a caso entro la copertura verificata della testata, più due casi di scorrimento delle pagine elenco (un tag del Giornale e una sezione del Mattino). Le estrazioni restano nelle normali cartelle, così si possono aprire i file Word; il riepilogo complessivo è in `_ricognizione/<data>/prova_periodi_<seme>.txt`. Il seme indicato nel riepilogo permette di ripetere esattamente la stessa prova (`--seme`); si può limitare la prova ad alcune testate (`python scraper.py prova corriere ilpost`) e cambiare il numero di articoli (`--max 10`).

## Uso dalla piattaforma

Il motore non dipende dal disco: la piattaforma chiama `motore.esecuzione.esegui(parametri, ZipMemoria(), None)` e ottiene lo zip dell'estrazione, con la stessa struttura della cartella locale, senza `_lavoro`.

## YouTube

```
python scraper.py youtube "https://www.youtube.com/watch?v=423IsNrOPCc" --lingua it
python scraper.py youtube --file lista_link.txt --lingua it --modello medium
python scraper.py youtube "https://www.youtube.com/@canale" --dal 2026-01-01 --media nessuno
python scraper.py youtube --cerca "migranti lampedusa" --per-data --max 30 --media audio
```

I link vanno sempre tra virgolette (sul Mac il punto interrogativo degli indirizzi YouTube altrimenti viene interpretato dal terminale). Si possono indicare video singoli, playlist, canali (per i canali si leggono i video dal più recente e ci si ferma quando diventano più vecchi della data iniziale) oppure una ricerca su YouTube.

Per ogni video il testo viene preso dai sottotitoli caricati dal canale, in italiano e poi in inglese, poi da quelli automatici di YouTube (togliendo le righe ripetute dello scorrimento), e solo se mancano entrambi dalla trascrizione con faster-whisper, con filtro sulle pause e senza condizionamento sul testo precedente per ridurre le allucinazioni su audio scadente. La provenienza del testo è registrata ovunque. Con `--lingua it` Whisper non deve indovinare la lingua dai primi secondi, che su audio scadente è la causa più frequente di errori. `--modello medium` migliora la trascrizione al costo di circa il triplo del tempo.

Ogni estrazione ha una sottocartella video/ con una cartella per video (video.mp4, audio.mp3 ricavato dal video senza secondo download, trascrizione.txt, trascrizione_timecode.txt, trascrizione.docx, metadata.json, sottotitoli originali) e, nella cartella principale, indice_video.xlsx, corpus_completo.docx, corpus.jsonl, corpus_tlab.txt (variabili canale, anno, mese, provenienza del testo) e la scheda di estrazione. Con `--media nessuno` si salvano solo testi e metadati.

Se dopo l'installazione di Homebrew il comando brew non viene trovato, va aggiunto al percorso del terminale una volta per tutte con `echo 'eval "$(/opt/homebrew/bin/brew shellenv zsh)"' >> ~/.zprofile` seguito da `eval "$(/opt/homebrew/bin/brew shellenv zsh)"`. Requisiti di sistema: deno (`brew install deno`), senza il quale YouTube rifiuta molte richieste, e ffmpeg (`brew install ffmpeg`). Senza ffmpeg lo script funziona comunque, ma scarica il video in un file unico di qualità ridotta e lascia l'audio nel formato originale (m4a) invece che mp3. faster-whisper richiede Python 3.12 o inferiore: se l'interprete è più recente conviene un ambiente dedicato (`conda create -n scraper python=3.12`, poi `conda activate scraper`, `pip install -r requirements.txt faster-whisper` e selezione di quell'interprete in VS Code). Se YouTube chiede di confermare di non essere un bot, aggiungi `--cookies-from-browser chrome`. Se compaiono errori 403, aggiorna yt-dlp con `python -m pip install --upgrade "yt-dlp[default]"`.
