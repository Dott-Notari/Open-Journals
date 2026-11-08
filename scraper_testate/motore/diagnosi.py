"""Controllo dell'ambiente: interprete Python, librerie e programmi di sistema."""
import importlib
import platform
import shutil
import subprocess
import sys

# (modulo, pacchetto da installare, a cosa serve: "testate", "youtube" o "facoltativa")
LIBRERIE = [
    ("requests", "requests", "testate"), ("bs4", "beautifulsoup4", "testate"), ("lxml", "lxml", "testate"),
    ("trafilatura", "trafilatura", "testate"), ("docx", "python-docx", "testate"),
    ("openpyxl", "openpyxl", "testate"), ("tzdata", "tzdata", "facoltativa"),
    ("yt_dlp", "yt-dlp[default]", "youtube"), ("yt_dlp_ejs", "yt-dlp[default]", "youtube"),
    ("imageio_ffmpeg", "imageio-ffmpeg", "facoltativa"), ("faster_whisper", "faster-whisper", "whisper"),
]
PROGRAMMI = [
    ("ffmpeg", "-version", "brew install ffmpeg", "unire video e audio e produrre gli mp3"),
    ("ffprobe", "-version", "brew install ffmpeg", "analizzare i file audio e video"),
    ("deno", "--version", "brew install deno", "superare i controlli di YouTube"),
]


def versione_programma(cmd, opz):
    try:
        out = subprocess.run([cmd, opz], capture_output=True, text=True, timeout=15).stdout
        return out.strip().splitlines()[0] if out.strip() else "presente"
    except Exception:
        return "presente"


def diagnosi():
    ok = True
    print(f"Python: {platform.python_version()}  ({sys.executable})")
    print("\nLibrerie Python")
    mancanti, assenti_per = [], set()
    for modulo, pacchetto, uso in LIBRERIE:
        nome = modulo.replace("_", "-") if modulo == "yt_dlp_ejs" else pacchetto
        try:
            m = importlib.import_module(modulo)
            print(f"  OK       {nome:20} {getattr(m, '__version__', '')}")
        except Exception:
            print(f"  MANCA    {nome:20} serve per: {uso}")
            assenti_per.add(uso)
            mancanti.append(pacchetto)
    try:
        import yt_dlp
        print(f"  versione yt-dlp: {yt_dlp.version.__version__} (se YouTube dà errori, aggiornala)")
    except Exception:
        pass
    print("\nProgrammi di sistema")
    prog_mancanti = set()
    for cmd, opz, rimedio, scopo in PROGRAMMI:
        if shutil.which(cmd):
            print(f"  OK       {cmd:8} {versione_programma(cmd, opz)[:70]}")
        else:
            print(f"  MANCA    {cmd:8} serve per {scopo}. Rimedio: {rimedio}")
            prog_mancanti.add(cmd)
    print("\nRimedi")
    if mancanti:
        pacchetti = " ".join(f'"{x}"' for x in sorted(set(mancanti)))
        print(f"  {sys.executable} -m pip install --upgrade {pacchetti}")
    for rimedio in sorted({r for c, _, r, _ in PROGRAMMI if c in prog_mancanti}):
        print(f"  {rimedio}")
    if prog_mancanti and not shutil.which("brew"):
        print("  (brew non risulta nel percorso del terminale: vedi README, sezione YouTube)")
    if not mancanti and not prog_mancanti:
        print("  nulla da installare")
    print("\nRiepilogo")
    print("  Testate: " + ("pronte" if "testate" not in assenti_per else "manca qualche libreria"))
    def stato(mancano):
        mancano = [m for m in mancano if m]
        return "pronto" if not mancano else "manca " + ", ".join(mancano)
    base = ["yt-dlp" if "youtube" in assenti_per else "", "deno" if "deno" in prog_mancanti else ""]
    print("  YouTube (sottotitoli): " + stato(base))
    print("  YouTube (mp4 e mp3): " + stato(base + ["ffmpeg" if prog_mancanti & {"ffmpeg", "ffprobe"} else ""]))
    print("  YouTube (Whisper): " + stato(base + ["faster-whisper" if "whisper" in assenti_per else ""]))
    return ok
