"""
Día 3 — Servicio de dominio
===========================
registrar_pedido() es el único punto de entrada que usa la vista.
Coordina: proveedor IA → Adapter → Sugerencia → Factory → Strategy → Pedido.
"""
from .models import Pedido
from .proveedores_ia import AdapterJson, ProveedorIAJson
from . import fabrica


def registrar_pedido(datos_formulario):
    """
    Trámite encargado de dar de alta un pedido en la base de datos.

    Flujo (Día 3):
        datos_formulario
            ↓
        proveedor IA (JSON stub)
            ↓
        AdapterJson
            ↓
        Sugerencia  ← formato interno; ya no hay route_hint ni XML en el dominio
            ↓
        fabrica.crear(sugerencia.medio)
            ↓
        Strategy.planear(pedido_provisional, contexto)
            ↓
        Plan  (medio, eta, notas)
            ↓
        Pedido guardado en BD
    """
    peso = float(datos_formulario.get('peso', 0.0))

    # 1. Consultar proveedor externo y adaptar al formato interno
    proveedor = ProveedorIAJson()
    adapter = AdapterJson(proveedor)
    sugerencia = adapter.obtener_sugerencia(peso)

    # 2. Obtener el Strategy correspondiente al medio sugerido
    strategy = fabrica.crear(sugerencia.medio)

    # 3. Crear un objeto transitorio para pasar al Strategy
    #    (aún no está en BD; solo necesitamos el peso para planear)
    class _PedidoTransitorio:
        pass

    pedido_tmp = _PedidoTransitorio()
    pedido_tmp.peso = peso

    contexto = {'sugerencia': sugerencia}

    # 4. El Strategy planea la entrega y devuelve un Plan
    plan = strategy.planear(pedido_tmp, contexto)

    # 5. Persistir el pedido con los datos del Plan
    pedido = Pedido.objects.create(
        origen=datos_formulario.get('origen'),
        destino=datos_formulario.get('destino'),
        peso=peso,
        estado='Registrado',
        eta=plan.eta,
        medio=plan.medio,
    )

    return pedido