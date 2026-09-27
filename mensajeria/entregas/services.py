"""
Día 3 — Servicio de dominio
Día 4 — Transacción + pago simulado + notificación post-commit + tolerancia a falla de IA
==========================================================================================
registrar_pedido() es el único punto de entrada que usa la vista.

Flujo Día 4 completo:
    datos_formulario
        ↓
    obtener_sugerencia_con_fallback()   ← nunca lanza excepción de IA
        ↓
    Sugerencia  (real o fallback)
        ↓
    fabrica.crear(sugerencia.medio)
        ↓
    Strategy.planear(...)
        ↓
    Plan
        ↓
    transaction.atomic()
        ├─ Pedido.objects.create(...)   ← persistencia atómica
        ├─ Pago.objects.create(...)     ← pago simulado en la MISMA transacción
        │   Si el pago falla → rollback de Pedido también
        └─ transaction.on_commit(
               _notificar_pedido        ← se ejecuta DESPUÉS del COMMIT
           )
        ↓
    return pedido
"""
import decimal
from django.db import transaction

from .models import Pedido, Pago
from .proveedores_ia import obtener_sugerencia_con_fallback
from . import fabrica


# ---------------------------------------------------------------------------
# Tarifa simulada (Día 4 — pago ficticio)
# ---------------------------------------------------------------------------

_TARIFA_BASE: decimal.Decimal = decimal.Decimal('50.00')   # MXN por pedido
_TARIFA_KG:   decimal.Decimal = decimal.Decimal('10.00')   # MXN por kg


def _calcular_monto(peso: float) -> decimal.Decimal:
    """
    Tarifa ficticia simple: base fija + precio por kilogramo.
    No representa un precio real; sirve para demostrar la operación de cobro.
    """
    return _TARIFA_BASE + _TARIFA_KG * decimal.Decimal(str(peso))


# ---------------------------------------------------------------------------
# Notificación simulada (Día 4)
# ---------------------------------------------------------------------------

def _notificar_pedido(pedido_id: int, medio: str) -> None:
    """
    Notificación simulada que se ejecuta DESPUÉS del commit.

    Al dispararse mediante transaction.on_commit(), una excepción aquí
    ya NO puede deshacer el pedido (el commit ya ocurrió).

    robust=True garantiza que si falla, Django loguea el error pero
    no propaga la excepción a la respuesta HTTP.
    """
    print(
        f'[NOTIFICACIÓN] Pedido #{pedido_id} confirmado. '
        f'Medio asignado: {medio}. '
        f'El cliente puede hacer seguimiento en /pedidos/{pedido_id}/'
    )


# ---------------------------------------------------------------------------
# Servicio principal
# ---------------------------------------------------------------------------

def registrar_pedido(datos_formulario):
    """
    Trámite encargado de dar de alta un pedido en la base de datos.

    Garantías del Día 4:
    1. La consulta a la IA nunca tumba el flujo (fallback automático).
    2. Pedido + Pago son atómicos: si cualquiera falla, ambos se revierten.
    3. La notificación ocurre DESPUÉS del commit; si falla, el pedido
       y el pago ya están guardados y no desaparecen (robust=True).
    """
    peso = float(datos_formulario.get('peso', 0.0))

    # ------------------------------------------------------------------
    # 1. Consultar IA con tolerancia a falla (Día 4)
    #    Si la IA está caída o lanza excepción, devuelve fallback.
    #    Esto ocurre FUERA de la transacción porque no escribe en BD.
    # ------------------------------------------------------------------
    sugerencia = obtener_sugerencia_con_fallback(peso)

    # ------------------------------------------------------------------
    # 2. Obtener Strategy y planear (Día 3, sin cambios)
    # ------------------------------------------------------------------
    strategy = fabrica.crear(sugerencia.medio)

    class _PedidoTransitorio:
        pass

    pedido_tmp = _PedidoTransitorio()
    pedido_tmp.peso = peso
    contexto = {'sugerencia': sugerencia}

    plan = strategy.planear(pedido_tmp, contexto)

    # ------------------------------------------------------------------
    # 3. Persistir de forma atómica (Día 4 — transaction.atomic)
    #
    #    Dentro del bloque se crean DOS registros:
    #      a) Pedido — el pedido en sí.
    #      b) Pago   — el cobro simulado asociado al pedido.
    #
    #    Si cualquiera de los dos falla, la BD vuelve al estado anterior:
    #      - No queda Pedido sin Pago.
    #      - No queda Pago sin Pedido.
    # ------------------------------------------------------------------
    with transaction.atomic():

        # 3a. Crear el pedido
        pedido = Pedido.objects.create(
            origen=datos_formulario.get('origen'),
            destino=datos_formulario.get('destino'),
            peso=peso,
            estado='Registrado',
            eta=plan.eta,
            medio=plan.medio,
        )

        # 3b. Crear el pago simulado en la MISMA transacción.
        #     Si esta línea lanza una excepción, el Pedido también
        #     se revierte (rollback completo del bloque atomic).
        monto = _calcular_monto(peso)
        Pago.objects.create(
            pedido=pedido,
            monto=monto,
            estado='aprobado',
        )

        # 3c. Registrar notificación post-commit.
        #     robust=True: si falla, Django loguea pero NO propaga.
        #     En este punto el commit aún NO ocurrió; la notificación
        #     se ejecutará solo cuando el bloque atomic confirme.
        pedido_id = pedido.pk
        medio_asignado = plan.medio

        transaction.on_commit(
            lambda: _notificar_pedido(pedido_id, medio_asignado),
            robust=True,
        )

    return pedido