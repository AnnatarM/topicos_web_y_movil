# Día 4 — Plantilla limpia, transacción e IA caída

## Plantilla limpia

La plantilla de seguimiento presenta el folio, la ruta, el medio de entrega, el ETA y un mapa interactivo. La plantilla no consulta directamente la base de datos ni contiene SQL, ORM o llamadas a la IA.

Los datos llegan preparados desde la vista y el mapa utiliza las coordenadas proporcionadas por el contexto.

## Transacción

El alta del pedido utiliza `transaction.atomic()`.

Dentro de la misma transacción se crean:

- el pedido;
- el pago simulado.

Si alguna de estas operaciones falla, la transacción se revierte y no queda un pedido sin pago ni un pago sin pedido.

## Pago simulado

Se implementó un pago ficticio asociado uno a uno con cada pedido.

El monto se calcula mediante una tarifa simulada de:

    $50 MXN + $10 MXN por kilogramo.

El pago queda almacenado con estado `aprobado` y un identificador de transacción UUID.

## Notificación después del commit

La notificación se registra mediante `transaction.on_commit()`.

El flujo es:

    crear Pedido
    → crear Pago
    → COMMIT
    → ejecutar notificación

Se utiliza `robust=True` para que una excepción de la notificación no afecte al pedido ni al pago que ya fueron confirmados.

## IA caída

La aplicación permite simular la caída del proveedor mediante `IA_CAIDA`.

Cuando la IA está disponible se obtiene una sugerencia normalmente.

Cuando está caída o genera una excepción, se genera una sugerencia de fallback utilizando camioneta.

De esta manera, un fallo del proveedor externo no impide registrar el pedido.

## Seguimiento con IA caída

Una vez guardado el pedido, `GET /pedidos/<id>/` utiliza la información local almacenada.

Por lo tanto, aunque la IA continúe caída, el usuario puede consultar un pedido previamente registrado.

## ¿Qué sucede si el cliente pulsa dos veces "Crear"?

PRG evita que una recarga posterior al POST vuelva a crear el pedido:

    POST /pedidos/
    → redirect
    → GET /pedidos/<id>/

