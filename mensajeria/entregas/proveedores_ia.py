"""
Día 3 — Adapter
===============
ProveedorIA*: proveedores falsos que simulan respuestas externas.
Sugerencia:   formato interno común (lo que ve el dominio).
Adapter*:     convierten el formato externo al formato interno.
"""
from __future__ import annotations
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Formato interno del dominio
# ---------------------------------------------------------------------------

@dataclass
class Sugerencia:
    """
    Representación interna de la recomendación de la IA.
    El dominio NUNCA debe conocer 'route_hint', 'score' ni etiquetas XML.
    """
    medio: str          # p.ej. "dron", "camioneta", etc.
    motivo: str         # texto legible para depuración / logs


# ---------------------------------------------------------------------------
# Proveedores externos falsos (no se conectan a ninguna API real)
# ---------------------------------------------------------------------------

class ProveedorIAJson:
    """
    Simula un proveedor externo cuya respuesta llega en JSON.

    Formato externo:
        {
            "route_hint": "urbana",
            "score": 0.91
        }
    El campo 'route_hint' determina el medio sugerido.
    """

    _MAPA_ROUTE_HINT: dict[str, str] = {
        'urbana':     'motocicleta',
        'ultima_milla': 'bicicleta',
        'aerea':      'dron',
        'interurbana': 'camioneta',
    }

    def consultar(self, pedido_peso: float) -> dict:
        """
        Devuelve un dict crudo simulando la respuesta JSON del proveedor.
        La lógica de decisión es simplista a propósito (es un stub).
        """
        if pedido_peso <= 5:
            hint = 'aerea'
            score = 0.95
        elif pedido_peso <= 10:
            hint = 'ultima_milla'
            score = 0.88
        elif pedido_peso <= 30:
            hint = 'urbana'
            score = 0.91
        else:
            hint = 'interurbana'
            score = 0.78

        # Respuesta cruda como el proveedor externo la daría
        return {'route_hint': hint, 'score': score}


class ProveedorIAXml:
    """
    Simula un proveedor externo cuya respuesta llega en XML.

    Formato externo:
        <suggestion>
            <vehicle>dron</vehicle>
        </suggestion>
    """

    def consultar(self, pedido_peso: float) -> str:
        """Devuelve una cadena XML cruda simulando la respuesta del proveedor."""
        if pedido_peso <= 5:
            vehiculo = 'dron'
        elif pedido_peso <= 10:
            vehiculo = 'bicicleta'
        elif pedido_peso <= 30:
            vehiculo = 'motocicleta'
        else:
            vehiculo = 'camioneta'

        # Respuesta cruda como el proveedor externo la daría
        return f'<suggestion><vehicle>{vehiculo}</vehicle></suggestion>'


# ---------------------------------------------------------------------------
# Adapters: traducen formato externo → Sugerencia (formato interno)
# ---------------------------------------------------------------------------

class AdapterJson:
    """
    Adapter para ProveedorIAJson.
    Convierte el dict crudo {route_hint, score} en una Sugerencia interna.
    """

    _MAPA: dict[str, str] = {
        'urbana':       'motocicleta',
        'ultima_milla': 'bicicleta',
        'aerea':        'dron',
        'interurbana':  'camioneta',
    }

    def __init__(self, proveedor: ProveedorIAJson):
        self._proveedor = proveedor

    def obtener_sugerencia(self, pedido_peso: float) -> Sugerencia:
        datos_crudos: dict = self._proveedor.consultar(pedido_peso)

        # Aquí ocurre la traducción: route_hint → medio, score → motivo
        route_hint = datos_crudos['route_hint']
        score = datos_crudos['score']
        medio = self._MAPA.get(route_hint, 'camioneta')

        return Sugerencia(
            medio=medio,
            motivo=f'ProveedorJSON sugirió route_hint="{route_hint}" (score={score})',
        )


class AdapterXml:
    """
    Adapter para ProveedorIAXml.
    Parsea la cadena XML cruda y la convierte en una Sugerencia interna.
    """

    def __init__(self, proveedor: ProveedorIAXml):
        self._proveedor = proveedor

    def obtener_sugerencia(self, pedido_peso: float) -> Sugerencia:
        xml_crudo: str = self._proveedor.consultar(pedido_peso)

        # Parsear la estructura XML del proveedor
        raiz = ET.fromstring(xml_crudo)
        medio = raiz.findtext('vehicle') or 'camioneta'

        return Sugerencia(
            medio=medio,
            motivo=f'ProveedorXML sugirió vehiculo="{medio}" (via <suggestion>/<vehicle>)',
        )
