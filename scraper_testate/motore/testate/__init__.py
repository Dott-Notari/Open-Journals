"""Registro delle testate disponibili."""
from .ilgiornale import IlGiornale
from .avvenire import Avvenire
from .fatto import Fatto
from .ansa import Ansa
from .base import Generica, NonSupportato  # noqa: F401
from .seconda_ondata import NUOVE
from .estere import ESTERE
from .napoli import NAPOLI
from .venezuela import VENEZUELA

TESTATE = {t.chiave: t for t in (IlGiornale(), Avvenire(), Fatto(), Ansa(), *NUOVE, *ESTERE, *NAPOLI, *VENEZUELA)}
GENERICA = Generica()


def per_url(url):
    for t in TESTATE.values():
        if t.riconosce(url):
            return t
    return GENERICA

# gruppi selezionabili al posto delle chiavi (riga di comando e piattaforma)
_ESTERE = [t.chiave for t in ESTERE]
_NAPOLI = [t.chiave for t in NAPOLI]
_VENEZUELA = [t.chiave for t in VENEZUELA]
GRUPPI = {
    "tutte": list(TESTATE),
    "italiane": [k for k in TESTATE if k not in _ESTERE + _NAPOLI + _VENEZUELA],
    "estere": _ESTERE,
    "napoli": _NAPOLI,
    "venezuela": _VENEZUELA,
}


def gruppo_di(chiave):
    for g in ("napoli", "venezuela", "estere"):
        if chiave in GRUPPI[g]:
            return g
    return "italiane"
