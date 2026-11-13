"""Registro delle testate disponibili."""
from .ilgiornale import IlGiornale
from .avvenire import Avvenire
from .fatto import Fatto
from .ansa import Ansa
from .base import Generica, NonSupportato  # noqa: F401
from .seconda_ondata import NUOVE
from .estere import ESTERE

TESTATE = {t.chiave: t for t in (IlGiornale(), Avvenire(), Fatto(), Ansa(), *NUOVE, *ESTERE)}
GENERICA = Generica()


def per_url(url):
    for t in TESTATE.values():
        if t.riconosce(url):
            return t
    return GENERICA
