"""Strutture dati: articolo, parametri di un'estrazione, sorgenti da cui leggere gli URL."""
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Optional


@dataclass
class Articolo:
    url: str
    testata: str
    titolo: str = ""
    sommario: str = ""
    testo: str = ""
    data: str = ""                 # ISO 8601, ora italiana
    autori: list = field(default_factory=list)
    sezione: str = ""
    tag: list = field(default_factory=list)
    accesso_libero: Optional[bool] = None   # dichiarato dalla testata (False = riservato agli abbonati)
    metodo: str = ""               # da dove è stato preso il corpo del testo
    coerenza: float = 0.0          # quota di parole del titolo presenti nell'avvio del testo
    sospetto: bool = False
    parziale: bool = False
    note: str = ""
    virgolettati: list = field(default_factory=list)
    id: int = 0

    def dt(self) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(self.data) if self.data else None
        except ValueError:
            return None

    def giorno(self) -> Optional[date]:
        d = self.dt()
        return d.date() if d else None

    def parole(self) -> int:
        return len(self.testo.split())

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        campi = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**campi)


@dataclass
class Parametri:
    modalita: str                  # "link" | "data" | "elenco"
    testata: Optional[str] = None
    link: list = field(default_factory=list)
    elenco: Optional[str] = None
    dal: Optional[str] = None      # AAAA-MM-GG
    al: Optional[str] = None
    parole: list = field(default_factory=list)
    tutte: bool = False            # tutte le parole (AND) invece di almeno una (OR)
    escludi_riservati: bool = False  # scarta gli articoli dichiarati riservati agli abbonati
    cerca_in: str = "testo"        # "testo" | "titolo"
    usa_ricerca: bool = True       # con parole chiave, usa la ricerca della testata dove il robots.txt la consente
    fonte: str = "auto"            # "auto" | "archivio" | "ricerca" | "gdelt" | "wayback"
    parole_gdelt: list = field(default_factory=list)   # parole in inglese per GDELT
    formati: list = field(default_factory=list)
    max_articoli: Optional[int] = None

    def d_dal(self) -> Optional[date]:
        return date.fromisoformat(self.dal) if self.dal else None

    def d_al(self) -> Optional[date]:
        return date.fromisoformat(self.al) if self.al else None

    def chiave_ripresa(self):
        """Ciò che identifica un'estrazione ai fini della ripresa (i formati possono cambiare)."""
        d = asdict(self)
        d.pop("formati", None)
        return d

    def to_dict(self):
        return asdict(self)


@dataclass
class SorgenteURL:
    """Un elenco di URL già noto (da sitemap, feed o link inseriti)."""
    descrizione: str
    urls: list
    avviso: str = ""               # limite di copertura da riportare nella scheda


@dataclass
class SorgenteElenco:
    """Una pagina elenco paginata da scorrere (sezione, tag, rubrica, archivio del giorno)."""
    descrizione: str
    base: str
    filtro: Optional[str] = None   # sottostringa che gli URL degli articoli devono contenere
    usa_date: bool = True          # fermarsi quando gli articoli diventano più vecchi di "dal"
