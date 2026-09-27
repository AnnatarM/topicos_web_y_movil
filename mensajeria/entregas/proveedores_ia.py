"""
Día 3 — Adapter
Día 4 — Tolerancia a falla de IA
=================================
ProveedorIA*: proveedores falsos que simulan respuestas externas.
Sugerencia:   formato interno común (lo que ve el dominio).
Adapter*:     convierten el formato externo al formato interno.

Día 4 agrega:
  IA_CAIDA              — flag para simular que el proveedor está caído.
  obtener_sugerencia_con_fallback() — nunca lanza excepción al dominio;
                          si IA_CAIDA=True o cualquier error ocurre,
                          devuelve una Sugerencia de fallback segura.
"""
from __future__ import annotations
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Día 4 — Interruptor de falla (actívalo poniendo IA_CAIDA = True)
# Para las pruebas se puede parchear directamente: proveedores_ia.IA_CAIDA = True
# ---------------------------------------------------------------------------
IA_CAIDA: bool = False

# Medio que se usa cuando la IA no está disponible
MEDIO_FALLBACK: str = 'camioneta'


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


# ---------------------------------------------------------------------------
# Día 4 — Función de tolerancia a falla
# ---------------------------------------------------------------------------

def obtener_sugerencia_con_fallback(pedido_peso: float) -> Sugerencia:
    """
    Día 4 — Consulta la IA y adapta la respuesta al formato interno.

    Si IA_CAIDA es True (o si ocurre cualquier excepción), captura el error
    y devuelve una Sugerencia de fallback con MEDIO_FALLBACK.

    El dominio (services.py) llama a esta función en lugar de instanciar
    directamente el adapter, de modo que nunca recibe una excepción de IA.

    Flujo normal:   ProveedorIAJson → AdapterJson → Sugerencia real
    Flujo fallback: excepción capturada → Sugerencia(medio=MEDIO_FALLBACK)
    """
    if IA_CAIDA:
        print(
            '[IA] Proveedor marcado como caído (IA_CAIDA=True). '
            f'Usando fallback: {MEDIO_FALLBACK}.'
        )
        return Sugerencia(
            medio=MEDIO_FALLBACK,
            motivo=f'Fallback automático — IA no disponible (IA_CAIDA=True).',
        )

    try:
        proveedor = ProveedorIAJson()
        adapter = AdapterJson(proveedor)
        return adapter.obtener_sugerencia(pedido_peso)
    except Exception as exc:  # pylint: disable=broad-except
        print(f'[IA] Error inesperado al consultar proveedor: {exc}. '
              f'Usando fallback: {MEDIO_FALLBACK}.')
        return Sugerencia(
            medio=MEDIO_FALLBACK,
            motivo=f'Fallback automático — excepción capturada: {exc}.',
        )
