"""Dove finiscono i file: una cartella sul disco (uso locale) o uno zip in memoria (piattaforma)."""
import io
import zipfile
from pathlib import Path


class CartellaLocale:
    def __init__(self, cartella: Path):
        self.cartella = Path(cartella)
        self.cartella.mkdir(parents=True, exist_ok=True)

    def scrivi(self, rel, dati):
        p = self.cartella / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(dati, str):
            p.write_text(dati, encoding="utf-8")
        else:
            p.write_bytes(dati)

    def pulisci(self, sottocartelle):
        """Svuota le sottocartelle dei singoli articoli prima di riscriverle (dopo una ripresa)."""
        import shutil
        for sc in sottocartelle:
            shutil.rmtree(self.cartella / sc, ignore_errors=True)

    def chiudi(self):
        return self.cartella


class ZipMemoria:
    def __init__(self, radice=""):
        self.buf = io.BytesIO()
        self.zip = zipfile.ZipFile(self.buf, "w", zipfile.ZIP_DEFLATED)
        self.radice = radice.strip("/")

    def scrivi(self, rel, dati):
        nome = f"{self.radice}/{rel}" if self.radice else rel
        self.zip.writestr(nome, dati.encode("utf-8") if isinstance(dati, str) else dati)

    def chiudi(self):
        self.zip.close()
        return self.buf.getvalue()
