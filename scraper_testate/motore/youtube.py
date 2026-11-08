"""Modulo YouTube: metadati, sottotitoli o trascrizione Whisper, video e audio.

Riprende la logica del vecchio YouTube_Transcript_Repository (preferenza per i sottotitoli
manuali in italiano e poi in inglese, poi quelli automatici, infine faster-whisper con filtro VAD;
mp3 ricavato dall'mp4 già scaricato; pulizia delle righe ripetute dei sottotitoli automatici)
e la inserisce nella stessa struttura di estrazione delle testate."""
import json
import re
import shutil
import subprocess
import time
from collections import Counter, deque
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from . import comune as C
from . import formati as F
from .config import STOP_VECCHI, VERSIONE

LINGUE_PREFERITE = ["it", "it-IT", "it-orig", "en", "en-US", "en-GB", "en-orig"]
RE_CANALE = re.compile(r"youtube\.com/(@[^/?#]+|channel/[^/?#]+|c/[^/?#]+|user/[^/?#]+)/?$")
_WHISPER = {}


# ======================================================================== dati
@dataclass
class ParametriYT:
    sorgenti: list = field(default_factory=list)   # link di video, playlist o canali
    cerca: Optional[str] = None                     # ricerca su YouTube per parole
    ordina_per_data: bool = False
    dal: Optional[str] = None
    al: Optional[str] = None
    parole: list = field(default_factory=list)      # filtro su titolo, descrizione e trascrizione
    max_video: Optional[int] = None
    trascrizione: str = "auto"                      # auto | sottotitoli | whisper
    lingua: Optional[str] = None
    modello: str = "small"
    device: str = "auto"
    compute_type: str = "int8"
    media: str = "entrambi"                         # entrambi | video | audio | nessuno
    max_altezza: Optional[int] = None
    timecode_docx: bool = False
    cookies_browser: Optional[str] = None
    cookies_file: Optional[str] = None

    def chiave_ripresa(self):
        d = asdict(self)
        for k in ("media", "timecode_docx", "cookies_browser", "cookies_file", "device", "compute_type"):
            d.pop(k, None)
        return d


@dataclass
class Video:
    video_id: str
    url: str
    titolo: str = ""
    canale: str = ""
    canale_url: str = ""
    data: str = ""               # AAAA-MM-GG
    durata_sec: int = 0
    visualizzazioni: Optional[int] = None
    mi_piace: Optional[int] = None
    n_commenti: Optional[int] = None
    descrizione: str = ""
    tag: list = field(default_factory=list)
    categorie: list = field(default_factory=list)
    metodo: str = ""             # come è stato ottenuto il testo
    lingua: str = ""
    testo: str = ""
    segmenti: list = field(default_factory=list)   # [[secondi, testo], ...]
    cartella: str = ""
    file_video: str = ""
    file_audio: str = ""
    note: str = ""
    id: int = 0

    def parole(self):
        return len(re.findall(r"\w+", self.testo))

    def giorno(self):
        try:
            return date.fromisoformat(self.data)
        except ValueError:
            return None

    def dt(self):   # compatibilità con le funzioni di formato
        g = self.giorno()
        return datetime(g.year, g.month, g.day) if g else None


# ======================================================================== utilità
def timecode(s):
    s = int(max(0, s))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def trova_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe, str(Path(exe).parent)
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        return exe, exe
    except Exception:
        return None, None


def controlli(log):
    """Avvisi sulle dipendenze di sistema che, se mancano, rendono YouTube inaccessibile."""
    ok = True
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        log('Manca yt-dlp: python -m pip install --upgrade "yt-dlp[default]"')
        return False
    if not any(shutil.which(c) for c in ("deno", "node", "bun")):
        log("ATTENZIONE: nessun runtime JavaScript (deno). Senza, YouTube rifiuta molte richieste.")
        log("  macOS: brew install deno    Windows: winget install DenoLand.Deno")
    if not trova_ffmpeg()[0]:
        log("ATTENZIONE: ffmpeg assente: il video sarà scaricato in qualità ridotta (file unico)")
        log("  e l'audio resterà nel formato originale invece che mp3. Rimedio: brew install ffmpeg")
    return ok


class _Silenzioso:
    def debug(self, m): pass
    def info(self, m): pass
    def warning(self, m): pass
    def error(self, m): pass


def opzioni_base(p: ParametriYT, ffmpeg_loc):
    o = {"logger": _Silenzioso(), "quiet": True, "no_warnings": True, "noprogress": True, "retries": 5,
         "fragment_retries": 5, "socket_timeout": 30, "noplaylist": True,
         "sleep_interval_requests": 1}
    if ffmpeg_loc:
        o["ffmpeg_location"] = ffmpeg_loc
    if p.cookies_browser:
        o["cookiesfrombrowser"] = (p.cookies_browser,)
    if p.cookies_file:
        o["cookiefile"] = p.cookies_file
    return o


# ======================================================================== sottotitoli
RE_TAG = re.compile(r"<[^>]+>")


def _secondi(raw):
    raw = raw.strip().replace(",", ".").split(" ")[0]
    parti = raw.split(":")
    try:
        h, m, s = (["0"] + parti)[-3:] if len(parti) < 3 else parti
        return int(h) * 3600 + int(m) * 60 + float(s)
    except ValueError:
        return 0.0


def leggi_vtt(testo):
    """VTT o SRT -> [(secondi, testo)], togliendo le righe ripetute dei sottotitoli automatici."""
    blocchi = re.split(r"\n\s*\n", testo.replace("\r\n", "\n").replace("\r", "\n"))
    cue = []
    for b in blocchi:
        righe = [r.strip() for r in b.split("\n") if r.strip()]
        i = next((k for k, r in enumerate(righe) if "-->" in r), None)
        if i is None:
            continue
        inizio = _secondi(righe[i].split("-->")[0])
        testi = []
        for r in righe[i + 1:]:
            r = RE_TAG.sub("", r)
            r = (r.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<")
                 .replace("&gt;", ">").replace("&#39;", "'").replace("&quot;", '"'))
            r = re.sub(r"\s+", " ", r).strip()
            if r:
                testi.append(r)
        if testi:
            cue.append((inizio, testi))
    recenti, puliti = deque(maxlen=6), []
    for inizio, righe in cue:
        nuove = []
        for r in righe:
            k = r.lower()
            if k in recenti:
                continue
            recenti.append(k)
            nuove.append(r)
        if nuove:
            puliti.append((inizio, " ".join(nuove)))
    return puliti


def scegli_sottotitoli(info, lingua=None):
    """(lingua, tipo, url_vtt) con la stessa preferenza del vecchio strumento."""
    pref = ([lingua, f"{lingua}-orig"] if lingua else []) + LINGUE_PREFERITE
    for tipo, chiave in (("manuali", "subtitles"), ("automatici", "automatic_captions")):
        tracce = info.get(chiave) or {}
        candidati = [l for l in pref if l in tracce] or (sorted(tracce) if tipo == "manuali" else [])
        for l in candidati:
            formati = tracce.get(l) or []
            vtt = next((f for f in formati if f.get("ext") == "vtt"), None) or \
                next((f for f in formati if f.get("ext") == "srv3" or f.get("ext") == "srt"), None)
            if vtt and vtt.get("url"):
                return l, tipo, vtt["url"]
    return None, None, None


def paragrafi_da_cue(cue, caratteri=700):
    """Paragrafi di circa `caratteri`. Si chiude a fine frase; quando la punteggiatura manca
    (sottotitoli automatici) si chiude dove la pausa stimata è più lunga, cioè dove il tempo
    fino alla riga successiva supera di più quello necessario a pronunciare la riga."""
    fine = lambda t: bool(re.search(r"[.!?…][\"'»)]?$", t))

    def pausa(k):
        if k + 1 >= len(cue):
            return 99.0
        return (cue[k + 1][0] - cue[k][0]) - len(cue[k][1]) / 15.0   # circa 15 caratteri al secondo

    out, s = [], 0
    while s < len(cue):
        lung, k = 0, s
        while k < len(cue) and lung < caratteri:
            lung += len(cue[k][1]) + 1
            k += 1
        if k >= len(cue):
            out.append(" ".join(t for _, t in cue[s:]))
            break
        # finestra in cui cercare il punto di chiusura migliore
        fin, tot = [k - 1], lung
        while fin[-1] + 1 < len(cue) and tot < 1.6 * caratteri:
            fin.append(fin[-1] + 1)
            tot += len(cue[fin[-1]][1]) + 1
        frasi = [x for x in fin if fine(cue[x][1])]
        taglio = frasi[0] if frasi else max(fin, key=pausa)
        out.append(" ".join(t for _, t in cue[s:taglio + 1]))
        s = taglio + 1
    return [p for p in out if p.strip()]


# ======================================================================== whisper
def trascrivi_whisper(audio, p: ParametriYT, log):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError("faster-whisper non installato (serve un ambiente con Python 3.12, vedi README)")
    chiave = (p.modello, p.device, p.compute_type)
    if chiave not in _WHISPER:
        log(f"    carico il modello Whisper «{p.modello}»...")
        _WHISPER[chiave] = WhisperModel(p.modello, device=p.device, compute_type=p.compute_type)
    log("    trascrizione automatica in corso (può richiedere alcuni minuti)...")
    seg, info = _WHISPER[chiave].transcribe(
        str(audio), language=p.lingua, beam_size=5, vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        condition_on_previous_text=False)   # riduce i cicli di allucinazione su audio scadente
    cue = [(float(s.start), re.sub(r"\s+", " ", s.text).strip()) for s in seg if s.text.strip()]
    return cue, getattr(info, "language", None) or (p.lingua or "")


# ======================================================================== elenco dei video
def espandi(p: ParametriYT, ydl_cls, opts, log):
    """Generatore di (url_video, cronologico) a partire da link, playlist, canali e ricerca."""
    flat = dict(opts, extract_flat="in_playlist", noplaylist=False, skip_download=True)
    sorgenti = list(p.sorgenti)
    if p.cerca:
        n = p.max_video or 50
        sorgenti.append(f"ytsearch{'date' if p.ordina_per_data else ''}{n}:{p.cerca}")
    for s in sorgenti:
        s = s.strip()
        if RE_CANALE.search(s):
            s = s.rstrip("/") + "/videos"
        e_video = re.search(r"(youtu\.be/|watch\?v=|/shorts/|/live/)", s) and "list=" not in s
        if e_video:
            yield s, False
            continue
        try:
            with ydl_cls(flat) as ydl:
                info = ydl.extract_info(s, download=False)
        except Exception as e:
            log(f"  impossibile leggere l'elenco {s}: {str(e)[:200]}")
            continue
        cronologico = "/videos" in s or "/streams" in s or s.startswith("ytsearchdate")
        voci = list(_appiattisci(info, ydl_cls, flat))
        log(f"  {s}: {len(voci)} video")
        for v in voci:
            yield v, cronologico


def _appiattisci(info, ydl_cls, flat, profondita=0):
    for e in (info or {}).get("entries") or []:
        if not e:
            continue
        if e.get("_type") in ("playlist", "url") and e.get("ie_key") == "YoutubeTab" and profondita < 1:
            try:
                with ydl_cls(flat) as ydl:
                    sotto = ydl.extract_info(e.get("url"), download=False)
                yield from _appiattisci(sotto, ydl_cls, flat, profondita + 1)
            except Exception:
                continue
            continue
        vid = e.get("id")
        if vid and len(vid) == 11:
            yield f"https://www.youtube.com/watch?v={vid}"
        elif str(e.get("url", "")).startswith("http"):
            yield e["url"]


# ======================================================================== un video
def elabora_video(url, p, ydl_cls, opts, cart_base, lavoro_dir, ffmpeg, log, dal=None, al=None):
    """Restituisce (Video | None, esito, motivo)."""
    with ydl_cls(dict(opts, skip_download=True)) as ydl:
        info = ydl.extract_info(url, download=False)
    up = str(info.get("upload_date") or "")
    v = Video(
        video_id=info.get("id") or "", url=info.get("webpage_url") or url,
        titolo=info.get("title") or "", canale=info.get("channel") or info.get("uploader") or "",
        canale_url=info.get("channel_url") or info.get("uploader_url") or "",
        data=f"{up[:4]}-{up[4:6]}-{up[6:8]}" if len(up) == 8 else "",
        durata_sec=int(info.get("duration") or 0), visualizzazioni=info.get("view_count"),
        mi_piace=info.get("like_count"), n_commenti=info.get("comment_count"),
        descrizione=info.get("description") or "", tag=info.get("tags") or [],
        categorie=info.get("categories") or [])
    g = v.giorno()
    if g and ((dal and g < dal) or (al and g > al)):
        return v, "fuori_intervallo", ""
    cart = None
    if cart_base is not None:
        cart = cart_base / "video" / f"{v.data or 'senza-data'}_{F.ascii_slug(v.titolo, 50)}_{v.video_id}"
        cart.mkdir(parents=True, exist_ok=True)
        v.cartella = str(cart.relative_to(cart_base))
    mp4 = mp3 = None
    if cart is not None and p.media in ("video", "entrambi"):
        log("    scarico il video...")
        mp4 = scarica_video(v.url, cart, p, ydl_cls, opts, log)
    if cart is not None and p.media in ("audio", "entrambi"):
        if mp4 and ffmpeg:
            mp3 = mp3_da_video(mp4, cart / "audio.mp3", ffmpeg, log)
        if not mp3:
            log("    scarico l'audio...")
            mp3 = scarica_audio(v.url, cart, p, ydl_cls, opts, log, mp3=True)
    v.file_video = mp4.name if mp4 else ""
    v.file_audio = mp3.name if mp3 else ""

    cue = []
    if p.trascrizione in ("auto", "sottotitoli"):
        lingua, tipo, u = scegli_sottotitoli(info, p.lingua)
        if u:
            try:
                with ydl_cls(dict(opts, skip_download=True)) as ydl:
                    grezzo = ydl.urlopen(u).read().decode("utf-8", errors="ignore")
                cue = leggi_vtt(grezzo)
                if cue:
                    v.metodo, v.lingua = f"sottotitoli YouTube {tipo}", lingua
                    if cart is not None:
                        (cart / f"sottotitoli_originali.{lingua}.vtt").write_text(grezzo, encoding="utf-8")
            except Exception as e:
                log(f"    sottotitoli non scaricabili: {str(e)[:150]}")
    if not cue and p.trascrizione in ("auto", "whisper"):
        audio, temporaneo = mp3 or mp4, None
        if audio is None:
            tmp = Path(lavoro_dir or ".") / "audio_temporaneo"
            tmp.mkdir(parents=True, exist_ok=True)
            audio = temporaneo = scarica_audio(v.url, tmp, p, ydl_cls, opts, log, mp3=False)
        if audio:
            try:
                cue, lingua = trascrivi_whisper(audio, p, log)
                v.metodo, v.lingua = f"faster-whisper ({p.modello})", lingua
            except Exception as e:
                v.note = f"trascrizione non riuscita: {str(e)[:150]}"
                log(f"    {v.note}")
            finally:
                if temporaneo:
                    shutil.rmtree(temporaneo.parent, ignore_errors=True)
        else:
            v.note = "audio non disponibile per la trascrizione"
    if not cue:
        v.metodo = v.metodo or "nessun testo"
        v.note = v.note or "nessun sottotitolo disponibile"
    v.segmenti = [[round(s, 2), t] for s, t in cue]
    v.testo = "\n".join(paragrafi_da_cue(cue))
    if cart is not None:
        scrivi_file_video(cart, v, p)
    return v, "ok" if cue else "senza_testo", v.note


def scarica_video(url, cart, p, ydl_cls, opts, log):
    h = p.max_altezza
    if not opts.get("ffmpeg_location"):
        # senza ffmpeg non si possono unire video e audio separati: si prende il miglior file unico
        fmt = f"best[ext=mp4][height<={h}]/best[height<={h}]" if h else "best[ext=mp4]/best"
        try:
            with ydl_cls(dict(opts, format=fmt, outtmpl=str(cart / "video.%(ext)s"))) as ydl:
                ydl.download([url])
        except Exception as e:
            log(f"    video non scaricato: {str(e)[:150]}")
            return None
        trovati = sorted(cart.glob("video.*"))
        return trovati[0] if trovati else None
    fmt = (f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
           if h else "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best")
    try:
        with ydl_cls(dict(opts, format=fmt, merge_output_format="mp4",
                          outtmpl=str(cart / "video.%(ext)s"))) as ydl:
            ydl.download([url])
    except Exception as e:
        log(f"    video non scaricato: {str(e)[:150]}")
        return None
    trovati = sorted(cart.glob("video.*"))
    return trovati[0] if trovati else None


def scarica_audio(url, cart, p, ydl_cls, opts, log, mp3=True):
    o = dict(opts, format="bestaudio[ext=m4a]/bestaudio/best", outtmpl=str(cart / "audio.%(ext)s"))
    if mp3 and not opts.get("ffmpeg_location"):
        mp3 = False   # senza ffmpeg niente conversione: resta l'audio originale (di solito m4a)
    if mp3:
        o["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                                "preferredquality": "192"}]
    try:
        with ydl_cls(o) as ydl:
            ydl.download([url])
    except Exception as e:
        log(f"    audio non scaricato: {str(e)[:150]}")
        return None
    trovati = sorted(cart.glob("audio.mp3" if mp3 else "audio.*"))
    return trovati[0] if trovati else None


def mp3_da_video(src, dest, ffmpeg, log):
    try:
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(src), "-vn",
                        "-acodec", "libmp3lame", "-b:a", "192k", "-ar", "44100", str(dest)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except Exception as e:
        log(f"    mp3 non ricavato dal video: {str(e)[:150]}")
        return None
    return dest if dest.exists() else None


# ======================================================================== file
def _durata(v):
    return timecode(v.durata_sec) if v.durata_sec else "n.d."


def righe_meta(v):
    r = [f"Canale: {v.canale}", f"Data di pubblicazione: {v.data or 'n.d.'}", f"Durata: {_durata(v)}"]
    if v.visualizzazioni is not None:
        r.append(f"Visualizzazioni: {v.visualizzazioni}")
    r += [f"Trascrizione: {v.metodo}" + (f" (lingua {v.lingua})" if v.lingua else ""),
          f"Parole: {v.parole()}", f"URL: {v.url}"]
    if v.note:
        r.append(f"Note: {v.note}")
    return r


def txt_video(v, con_timecode=False):
    corpo = "\n".join(f"[{timecode(s)}] {t}" for s, t in v.segmenti) if con_timecode \
        else "\n\n".join(v.testo.split("\n"))
    return "\n".join([v.titolo, *righe_meta(v), "", corpo]).strip() + "\n"


def _scrivi_docx(doc, v, p):
    from docx.shared import Pt
    run = doc.add_paragraph().add_run(v.titolo or "(senza titolo)")
    run.bold, run.font.size = True, Pt(13)
    for riga in righe_meta(v):
        doc.add_paragraph().add_run(riga).font.size = Pt(9.5)
    doc.add_paragraph()
    for par in v.testo.split("\n"):
        if par.strip():
            doc.add_paragraph(par)
    if p.timecode_docx and v.segmenti:
        doc.add_paragraph()
        doc.add_paragraph().add_run("Trascrizione con marcatori temporali").bold = True
        for s, t in v.segmenti:
            q = doc.add_paragraph()
            q.add_run(f"[{timecode(s)}] ").bold = True
            q.add_run(t)


def docx_video(v, p):
    import io
    doc = F._documento()
    _scrivi_docx(doc, v, p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def docx_corpus_video(videos, p, titolo):
    import io
    from docx.enum.text import WD_BREAK
    doc = F._documento()
    doc.add_paragraph().add_run(titolo).bold = True
    doc.add_paragraph(f"{len(videos)} video")
    for v in videos:
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        _scrivi_docx(doc, v, p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def scrivi_file_video(cart, v, p):
    (cart / "trascrizione.txt").write_text(txt_video(v), encoding="utf-8")
    (cart / "trascrizione_timecode.txt").write_text(txt_video(v, True), encoding="utf-8")
    (cart / "trascrizione.docx").write_bytes(docx_video(v, p))
    meta = {k: val for k, val in asdict(v).items() if k not in ("segmenti", "testo")}
    meta["parole"] = v.parole()
    (cart / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


COLONNE = [("ID", 6), ("Video ID", 14), ("Data", 11), ("Canale", 24), ("Titolo", 60),
           ("Durata", 9), ("Visualizzazioni", 12), ("Mi piace", 9), ("Commenti", 9),
           ("Trascrizione", 26), ("Lingua", 7), ("Parole", 8), ("Segmenti", 9), ("Tag", 30),
           ("Categorie", 16), ("Video", 8), ("Audio", 8), ("Note", 30), ("Cartella", 45), ("URL", 45)]


def xlsx_video(videos):
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, Side
    wb = Workbook()
    ws = wb.active
    ws.title = "Video"
    linea = Side(style="thin", color="000000")
    for c, (nome, larg) in enumerate(COLONNE, 1):
        cell = ws.cell(row=1, column=c, value=nome)
        cell.font = Font(name=F.FONT, size=11, bold=True)
        cell.border = Border(top=linea, bottom=linea)
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[cell.column_letter].width = larg
    for r, v in enumerate(videos, 2):
        valori = [v.id, v.video_id, v.data, v.canale, v.titolo, _durata(v), v.visualizzazioni,
                  v.mi_piace, v.n_commenti, v.metodo, v.lingua, v.parole(), len(v.segmenti),
                  ", ".join(v.tag), ", ".join(v.categorie), "sì" if v.file_video else "no",
                  "sì" if v.file_audio else "no", v.note, v.cartella, v.url]
        for c, val in enumerate(valori, 1):
            ws.cell(row=r, column=c, value=val).font = Font(name=F.FONT, size=11)
        ws.cell(row=r, column=len(COLONNE)).hyperlink = v.url
    if videos:
        for c in range(1, len(COLONNE) + 1):
            ws.cell(row=len(videos) + 1, column=c).border = Border(bottom=linea)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def tlab_video(videos):
    blocchi = []
    for v in videos:
        if not v.testo.strip():
            continue   # senza trascrizione il video resta nell'indice ma non entra nel corpus
        g = v.giorno()
        tipo = ("whisper" if "whisper" in v.metodo else "manuali" if "manuali" in v.metodo
                else "automatici" if "automatici" in v.metodo else "nessuna")
        var = [f"*CANALE_{F._var(v.canale)}", f"*ANNO_{g.year if g else 'nd'}",
               f"*MESE_{g.strftime('%Y_%m') if g else 'nd'}", f"*TRASCR_{tipo}", f"*ID_{v.id:04d}"]
        blocchi.append("**** " + " ".join(var) + "\n" + "\n".join(x for x in (v.titolo, v.testo) if x).replace("*", ""))
    return "\n\n".join(blocchi) + "\n"


# ======================================================================== esecuzione
def descrittore_yt(p: ParametriYT):
    if p.cerca:
        base = "ricerca_" + F.ascii_slug(p.cerca, 40)
    elif len(p.sorgenti) == 1 and not re.search(r"watch\?v=|youtu\.be/", p.sorgenti[0]):
        base = "elenco_" + F.ascii_slug(re.sub(r"https?://(www\.)?youtube\.com/", "", p.sorgenti[0]), 40)
    else:
        base = f"video-{len(p.sorgenti)}"
    if p.dal or p.al:
        base += f"_{p.dal or 'inizio'}_{p.al or 'oggi'}"
    return base


def cartella_yt(p: ParametriYT, radice):
    base = Path(radice) / "youtube"
    desc = descrittore_yt(p)
    if base.exists():
        for c in sorted(base.iterdir(), reverse=True):
            st = c / "_lavoro" / "stato.json"
            if c.is_dir() and c.name.endswith(desc) and st.exists():
                d = json.loads(st.read_text(encoding="utf-8"))
                if not d.get("completata") and d.get("parametri") == p.chiave_ripresa():
                    return c
    nuova, k = base / f"{date.today().isoformat()}_{desc}", 2
    while nuova.exists():
        nuova, k = base / f"{date.today().isoformat()}_{desc}_{k}", k + 1
    return nuova


def esegui_youtube(p: ParametriYT, cartella: Path, log=print, ydl_cls=None):
    if ydl_cls is None:
        if not controlli(log):
            return None
        from yt_dlp import YoutubeDL as ydl_cls
    cartella = Path(cartella)
    lav = cartella / "_lavoro"
    lav.mkdir(parents=True, exist_ok=True)
    st_path, vid_path = lav / "stato.json", lav / "video.jsonl"
    stato = json.loads(st_path.read_text(encoding="utf-8")) if st_path.exists() else {}
    fatti, errori, avvisi = stato.get("fatti", {}), stato.get("errori", []), stato.get("avvisi", [])
    videos = [Video(**{k: v for k, v in json.loads(r).items() if k in Video.__dataclass_fields__})
              for r in vid_path.read_text(encoding="utf-8").splitlines() if r] if vid_path.exists() else []
    if fatti:
        log(f"Riprendo un'estrazione interrotta: {len(fatti)} video già esaminati.")
    inizio = stato.get("inizio", datetime.now().isoformat(timespec="seconds"))
    ffmpeg, ffmpeg_loc = trova_ffmpeg()
    opts = opzioni_base(p, ffmpeg_loc)
    dal = date.fromisoformat(p.dal) if p.dal else None
    al = date.fromisoformat(p.al) if p.al else None
    pat = C.compila_parole(p.parole)
    t0, interrotta, vecchi = time.monotonic(), False, 0

    def salva(completata=False):
        st_path.write_text(json.dumps({"parametri": p.chiave_ripresa(), "inizio": inizio,
                                       "completata": completata, "fatti": fatti, "errori": errori,
                                       "avvisi": avvisi}, ensure_ascii=False, indent=1), encoding="utf-8")

    try:
        for url, cronologico in espandi(p, ydl_cls, opts, log):
            if p.max_video and len(videos) >= p.max_video:
                break
            m = re.search(r"(?:v=|youtu\.be/|/shorts/|/live/)([\w-]{11})", url)
            chiave = m.group(1) if m else url
            if chiave in fatti:
                continue
            log(f"> {url}")
            try:
                v, esito, motivo = elabora_video(url, p, ydl_cls, opts, cartella, lav, ffmpeg, log, dal, al)
            except Exception as e:
                errori.append(f"{url}  {str(e)[:200]}")
                fatti[chiave] = {"esito": "errore"}
                log(f"    errore: {str(e)[:200]}")
                salva()
                continue
            g = v.giorno()
            if esito == "fuori_intervallo":
                fatti[chiave] = {"esito": esito}
                if cronologico and dal and g and g < dal:
                    vecchi += 1
                    if vecchi >= STOP_VECCHI:
                        log("  video ormai più vecchi della data iniziale: mi fermo con questo elenco")
                        break
                continue
            vecchi = 0
            campo = f"{v.titolo} {v.descrizione} {' '.join(v.tag)} {v.testo}"
            if not C.corrisponde(pat, campo, False):
                fatti[chiave] = {"esito": "parole_assenti"}
                if v.cartella:
                    shutil.rmtree(cartella / v.cartella, ignore_errors=True)
                continue
            fatti[chiave] = {"esito": esito}
            videos.append(v)
            with open(vid_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(v), ensure_ascii=False) + "\n")
            log(f"    [{len(videos)}] {v.data}  {v.titolo[:80]}  ({v.metodo}, {v.parole()} parole)")
            salva()
    except KeyboardInterrupt:
        interrotta = True
        log("\nInterrotta. Rilancia lo stesso comando per riprendere.")
    salva(completata=not interrotta)

    videos.sort(key=lambda v: (v.data or "9999", v.titolo))
    for i, v in enumerate(videos, 1):
        v.id = i
    titolo = f"Corpus YouTube {descrittore_yt(p)}"
    if videos:
        (cartella / "indice_video.xlsx").write_bytes(xlsx_video(videos))
        (cartella / "corpus_completo.docx").write_bytes(docx_corpus_video(videos, p, titolo))
        (cartella / "corpus.jsonl").write_text("".join(json.dumps(asdict(v), ensure_ascii=False) + "\n"
                                                       for v in videos), encoding="utf-8")
        (cartella / "corpus_tlab.txt").write_text(tlab_video(videos), encoding="utf-8")
    (cartella / "scheda_estrazione.txt").write_text(
        scheda_yt(p, videos, fatti, errori, avvisi, inizio, not interrotta, time.monotonic() - t0),
        encoding="utf-8")
    return cartella


def scheda_yt(p, videos, fatti, errori, avvisi, inizio, completata, durata):
    c = Counter(v["esito"] for v in fatti.values())
    metodi = Counter(v.metodo for v in videos)
    R = ["SCHEDA DI ESTRAZIONE YOUTUBE", "=" * 60,
         f"Strumento: Scraper didattico testate, versione {VERSIONE}",
         f"Avvio: {inizio}    Fine: {datetime.now().isoformat(timespec='seconds')}"
         f"    Durata di questa sessione: {durata / 60:.1f} minuti",
         f"Stato: {'completata' if completata else 'INTERROTTA (rilanciare per completare)'}", "",
         "PARAMETRI"]
    R += [f"  Sorgente: {s}" for s in p.sorgenti]
    if p.cerca:
        R.append(f"  Ricerca su YouTube: «{p.cerca}» ({'per data' if p.ordina_per_data else 'per pertinenza'})")
    R += [f"  Intervallo: {p.dal or '-'} / {p.al or '-'}",
          f"  Parole chiave di filtro: {', '.join(p.parole) or 'nessuna'}",
          f"  Limite video: {p.max_video or 'nessuno'}",
          f"  Testo: {p.trascrizione} (sottotitoli manuali, poi automatici, poi Whisper «{p.modello}»)",
          f"  Lingua indicata: {p.lingua or 'riconoscimento automatico'}",
          f"  File multimediali: {p.media}", "",
          "ESITI",
          f"  Video esaminati: {len(fatti)}",
          f"  Video raccolti: {len(videos)}",
          f"  Fuori dall'intervallo di date: {c.get('fuori_intervallo', 0)}",
          f"  Scartati perché senza le parole chiave: {c.get('parole_assenti', 0)}",
          f"  Raccolti ma senza testo (esclusi dal corpus T-LAB): {sum(1 for v in videos if not v.segmenti)}",
          f"  Errori: {c.get('errore', 0)}", "",
          "PROVENIENZA DEL TESTO"]
    R += [f"  {m}: {n} video" for m, n in metodi.most_common()]
    if avvisi:
        R += ["", "AVVISI"] + [f"  {a}" for a in avvisi]
    if errori:
        R += ["", "ERRORI"] + [f"  {e}" for e in errori[:200]]
    R += ["", "NOTE METODOLOGICHE",
          "  Sottotitoli manuali, sottotitoli automatici di YouTube e trascrizioni Whisper hanno",
          "  profili di errore diversi: la provenienza del testo di ogni video è indicata nell'indice,",
          "  nei file del video e nel corpus T-LAB (variabile TRASCR) e va dichiarata nelle analisi.",
          "  Dai sottotitoli automatici sono state tolte le righe ripetute tipiche dello scorrimento.",
          "  I materiali sono raccolti per finalità di studio e ricerca e non vanno ridistribuiti."]
    return "\n".join(R) + "\n"
