"""
Día 3 — Strategy
================
Contrato común: MedioDeEntrega
Implementaciones: EntregaCamioneta, EntregaMotocicleta,
                  EntregaBicicleta, EntregaDron
"""
from __future__ import annotations
import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Plan:
    """Resultado que devuelve cualquier Strategy tras planear una entrega."""
    medio: str
    eta: str
    notas: str


class MedioDeEntrega(abc.ABC):
    """Contrato (Strategy) que deben cumplir todos los medios de entrega."""

    @abc.abstractmethod
    def planear(self, pedido: Any, contexto: dict[str, Any]) -> Plan:
        """
        Recibe el pedido y un diccionario de contexto (p.ej. la Sugerencia
        de la IA ya adaptada) y devuelve un Plan listo para guardar.
        """


class EntregaCamioneta(MedioDeEntrega):
    """Strategy para entregas en camioneta (cargas pesadas, rutas largas)."""

    def planear(self, pedido: Any, contexto: dict[str, Any]) -> Plan:
        peso = float(getattr(pedido, 'peso', 0))
        if peso > 100:
            eta = '48 horas (carga extra-pesada en camioneta)'
        else:
            eta = '24 horas (camioneta estándar)'
        return Plan(
            medio='camioneta',
            eta=eta,
            notas=f'Ruta terrestre. Peso declarado: {peso} kg.',
        )


class EntregaMotocicleta(MedioDeEntrega):
    """Strategy para entregas en motocicleta (rapidez en ciudad)."""

    def planear(self, pedido: Any, contexto: dict[str, Any]) -> Plan:
        return Plan(
            medio='motocicleta',
            eta='4 horas (moto urbana)',
            notas='Apto para paquetes hasta 30 kg en zona metropolitana.',
        )


class EntregaBicicleta(MedioDeEntrega):
    """Strategy para entregas en bicicleta (últma milla, eco-friendly)."""

    def planear(self, pedido: Any, contexto: dict[str, Any]) -> Plan:
        return Plan(
            medio='bicicleta',
            eta='2 horas (bicicleta, última milla)',
            notas='Solo disponible dentro del perímetro urbano. Paquete ≤ 10 kg.',
        )


class EntregaDron(MedioDeEntrega):
    """Strategy para entregas en dron (zonas de difícil acceso)."""

    def planear(self, pedido: Any, contexto: dict[str, Any]) -> Plan:
        return Plan(
            medio='dron',
            eta='1 hora (dron autónomo)',
            notas='Requiere zona de aterrizaje habilitada. Paquete ≤ 5 kg.',
        )
