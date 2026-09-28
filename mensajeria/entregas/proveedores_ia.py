# Adapter: los proveedores externos pueden responder en JSON o XML.
# El dominio recibe siempre Sugerencia(medio, motivo) y nunca conoce
# route_hint, score ni etiquetas XML.
#
# Día 4 — fallback: obtener_sugerencia_con_fallback() nunca propaga
# excepciones de la IA al servicio. Si IA_CAIDA=True o cualquier error
# ocurre, devuelve una Sugerencia segura con MEDIO_FALLBACK.
from __future__ import annotations
import xml.etree.ElementTree as ET
from dataclasses import dataclass

IA_CAIDA: bool = False
MEDIO_FALLBACK: str = 'camioneta'


@dataclass
class Sugerencia:
    #Formato interno del dominio. Aísla al servicio del formato de cada proveedor.
    medio: str
    motivo: str


class ProveedorIAJson:
    #Proveedor falso cuya respuesta llega en JSON.
    #Formato: { "route_hint": "...", "score": 0.xx }
    

    _MAPA_ROUTE_HINT: dict[str, str] = {
        'urbana':       'motocicleta',
        'ultima_milla': 'bicicleta',
        'aerea':        'dron',
        'interurbana':  'camioneta',
    }

    def consultar(self, pedido_peso: float) -> dict:
        if pedido_peso <= 5:
            hint, score = 'aerea', 0.95
        elif pedido_peso <= 10:
            hint, score = 'ultima_milla', 0.88
        elif pedido_peso <= 30:
            hint, score = 'urbana', 0.91
        else:
            hint, score = 'interurbana', 0.78
        return {'route_hint': hint, 'score': score}


class ProveedorIAXml:
    #Proveedor falso cuya respuesta llega en XML.
    #Formato: <suggestion><vehicle>...</vehicle></suggestion>
    

    def consultar(self, pedido_peso: float) -> str:
        if pedido_peso <= 5:
            vehiculo = 'dron'
        elif pedido_peso <= 10:
            vehiculo = 'bicicleta'
        elif pedido_peso <= 30:
            vehiculo = 'motocicleta'
        else:
            vehiculo = 'camioneta'
        return f'<suggestion><vehicle>{vehiculo}</vehicle></suggestion>'


class AdapterJson:
    #Convierte la respuesta JSON del proveedor en Sugerencia interna.

    _MAPA: dict[str, str] = {
        'urbana':       'motocicleta',
        'ultima_milla': 'bicicleta',
        'aerea':        'dron',
        'interurbana':  'camioneta',
    }

    def __init__(self, proveedor: ProveedorIAJson):
        self._proveedor = proveedor

    def obtener_sugerencia(self, pedido_peso: float) -> Sugerencia:
        datos = self._proveedor.consultar(pedido_peso)
        route_hint = datos['route_hint']
        score = datos['score']
        medio = self._MAPA.get(route_hint, 'camioneta')
        return Sugerencia(
            medio=medio,
            motivo=f'ProveedorJSON sugirió route_hint="{route_hint}" (score={score})',
        )


class AdapterXml:
    #Convierte la respuesta XML del proveedor en Sugerencia interna.

    def __init__(self, proveedor: ProveedorIAXml):
        self._proveedor = proveedor

    def obtener_sugerencia(self, pedido_peso: float) -> Sugerencia:
        raiz = ET.fromstring(self._proveedor.consultar(pedido_peso))
        medio = raiz.findtext('vehicle') or 'camioneta'
        return Sugerencia(
            medio=medio,
            motivo=f'ProveedorXML sugirió vehiculo="{medio}"',
        )


def obtener_sugerencia_con_fallback(pedido_peso: float) -> Sugerencia:
    #Consulta la IA; si falla o IA_CAIDA=True devuelve Sugerencia de fallback.
    if IA_CAIDA:
        print(f'[IA] Proveedor marcado como caído (IA_CAIDA=True). Usando fallback: {MEDIO_FALLBACK}.')
        return Sugerencia(medio=MEDIO_FALLBACK, motivo='Fallback automático — IA no disponible (IA_CAIDA=True).')

    try:
        return AdapterJson(ProveedorIAJson()).obtener_sugerencia(pedido_peso)
    except Exception as exc:  # pylint: disable=broad-except
        print(f'[IA] Error inesperado: {exc}. Usando fallback: {MEDIO_FALLBACK}.')
        return Sugerencia(medio=MEDIO_FALLBACK, motivo=f'Fallback automático — excepción capturada: {exc}.')
