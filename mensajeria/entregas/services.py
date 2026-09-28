import decimal
from django.db import transaction

from .models import Pedido, Pago
from .proveedores_ia import obtener_sugerencia_con_fallback
from . import fabrica


_TARIFA_BASE: decimal.Decimal = decimal.Decimal('50.00')
_TARIFA_KG:   decimal.Decimal = decimal.Decimal('10.00')


def _calcular_monto(peso: float) -> decimal.Decimal:
    return _TARIFA_BASE + _TARIFA_KG * decimal.Decimal(str(peso))


def _notificar_pedido(pedido_id: int, medio: str) -> None:
    # Se ejecuta después del commit (on_commit). Una excepción aquí no puede
    # revertir el pedido; robust=True hace que Django la absorba sin propagar.
    print(
        f'[NOTIFICACIÓN] Pedido #{pedido_id} confirmado. '
        f'Medio: {medio}. Seguimiento en /pedidos/{pedido_id}/'
    )


def registrar_pedido(datos_formulario):
    """
    Trámite central: coordina fallback/Adapter → Factory → Strategy → persistencia.

    Garantías:
    - La IA nunca tumba el flujo (fallback automático en obtener_sugerencia_con_fallback).
    - Pedido + Pago son atómicos: si uno falla, ambos se revierten.
    - La notificación ocurre solo después del commit; si falla, el pedido persiste.
    """
    peso = float(datos_formulario.get('peso', 0.0))

    sugerencia = obtener_sugerencia_con_fallback(peso)
    strategy = fabrica.crear(sugerencia.medio)

    class _PedidoTransitorio:
        pass

    pedido_tmp = _PedidoTransitorio()
    pedido_tmp.peso = peso
    plan = strategy.planear(pedido_tmp, {'sugerencia': sugerencia})

    # Pedido + Pago en la misma transacción: si el Pago falla, el Pedido
    # también se revierte y no queda ningún registro inconsistente.
    with transaction.atomic():
        pedido = Pedido.objects.create(
            origen=datos_formulario.get('origen'),
            destino=datos_formulario.get('destino'),
            peso=peso,
            estado='Registrado',
            eta=plan.eta,
            medio=plan.medio,
        )

        Pago.objects.create(
            pedido=pedido,
            monto=_calcular_monto(peso),
            estado='aprobado',
        )

        pedido_id = pedido.pk
        medio_asignado = plan.medio

        # on_commit: la lambda solo se ejecuta si el bloque atomic confirma.
        transaction.on_commit(
            lambda: _notificar_pedido(pedido_id, medio_asignado),
            robust=True,
        )

    return pedido