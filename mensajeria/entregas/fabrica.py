"""
Día 3 — Fábrica simple
======================
crear(medio) → implementación concreta de MedioDeEntrega.

Justificación de "fábrica simple" en lugar de Factory Method:
- No existen familias de procesos que redefinan un hook.
- El único problema es centralizar la creación a partir de un string.
- Un dict de constructores cumple ese propósito sin sobre-ingeniería.
"""
from __future__ import annotations

from .medios import (
    MedioDeEntrega,
    EntregaCamioneta,
    EntregaMotocicleta,
    EntregaBicicleta,
    EntregaDron,
)


# Registro de medios disponibles.
# Para agregar un nuevo medio basta con añadir una entrada aquí,
# sin tocar la vista ni el servicio.
_REGISTRO: dict[str, type[MedioDeEntrega]] = {
    'camioneta':   EntregaCamioneta,
    'motocicleta': EntregaMotocicleta,
    'bicicleta':   EntregaBicicleta,
    'dron':        EntregaDron,
}


class MedioDesconocidoError(ValueError):
    """Se lanza cuando se pide un medio que la fábrica no conoce."""


def crear(medio: str) -> MedioDeEntrega:
    """
    Fábrica simple: devuelve la implementación de MedioDeEntrega
    correspondiente al string 'medio'.

    Ejemplos:
        crear('dron')        → EntregaDron()
        crear('bicicleta')   → EntregaBicicleta()
        crear('motocicleta') → EntregaMotocicleta()
        crear('camioneta')   → EntregaCamioneta()
    """
    clave = medio.strip().lower()
    clase = _REGISTRO.get(clave)
    if clase is None:
        disponibles = ', '.join(_REGISTRO.keys())
        raise MedioDesconocidoError(
            f'Medio "{medio}" no reconocido. '
            f'Medios disponibles: {disponibles}.'
        )
    return clase()
