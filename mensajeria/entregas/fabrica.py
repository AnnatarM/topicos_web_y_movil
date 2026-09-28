# Fábrica simple: centraliza la creación de la implementación concreta de
# MedioDeEntrega a partir de un string.
# Se usa fábrica simple (dict de constructores) en lugar de Factory Method
# porque no existen familias de trámites que redefinan un hook.
# Para agregar un medio nuevo basta con registrarlo aquí; la vista y el
# servicio no cambian.
from __future__ import annotations

from .medios import (
    MedioDeEntrega,
    EntregaCamioneta,
    EntregaMotocicleta,
    EntregaBicicleta,
    EntregaDron,
)


_REGISTRO: dict[str, type[MedioDeEntrega]] = {
    'camioneta':   EntregaCamioneta,
    'motocicleta': EntregaMotocicleta,
    'bicicleta':   EntregaBicicleta,
    'dron':        EntregaDron,
}


class MedioDesconocidoError(ValueError):
    pass


def crear(medio: str) -> MedioDeEntrega:
    clave = medio.strip().lower()
    clase = _REGISTRO.get(clave)
    if clase is None:
        disponibles = ', '.join(_REGISTRO.keys())
        raise MedioDesconocidoError(
            f'Medio "{medio}" no reconocido. '
            f'Medios disponibles: {disponibles}.'
        )
    return clase()
