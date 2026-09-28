# Strategy: cada medio de entrega encapsula su propio algoritmo para calcular
# el ETA, evitando un bloque if/elif en la vista o el servicio.
# La vista y registrar_pedido solo conocen MedioDeEntrega.planear(), nunca
# las clases concretas.
from __future__ import annotations
import abc
from dataclasses import dataclass
from typing import Any


@dataclass
class Plan:
    medio: str
    eta: str
    notas: str


class MedioDeEntrega(abc.ABC):
    @abc.abstractmethod
    def planear(self, pedido: Any, contexto: dict[str, Any]) -> Plan: ...


class EntregaCamioneta(MedioDeEntrega):
    def planear(self, pedido: Any, contexto: dict[str, Any]) -> Plan:
        peso = float(getattr(pedido, 'peso', 0))
        eta = '48 horas (carga extra-pesada en camioneta)' if peso > 100 else '24 horas (camioneta estándar)'
        return Plan(medio='camioneta', eta=eta, notas=f'Ruta terrestre. Peso declarado: {peso} kg.')


class EntregaMotocicleta(MedioDeEntrega):
    def planear(self, pedido: Any, contexto: dict[str, Any]) -> Plan:
        return Plan(
            medio='motocicleta',
            eta='4 horas (moto urbana)',
            notas='Apto para paquetes hasta 30 kg en zona metropolitana.',
        )


class EntregaBicicleta(MedioDeEntrega):
    def planear(self, pedido: Any, contexto: dict[str, Any]) -> Plan:
        return Plan(
            medio='bicicleta',
            eta='2 horas (bicicleta, última milla)',
            notas='Solo disponible dentro del perímetro urbano. Paquete ≤ 10 kg.',
        )


class EntregaDron(MedioDeEntrega):
    def planear(self, pedido: Any, contexto: dict[str, Any]) -> Plan:
        return Plan(
            medio='dron',
            eta='1 hora (dron autónomo)',
            notas='Requiere zona de aterrizaje habilitada. Paquete ≤ 5 kg.',
        )
