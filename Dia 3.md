# Día 3 — Strategy, Adapter y quién hace el `new`

## Strategy

**Qué inconveniente resuelve:** la asignación de medios de entrega no debe concentrarse en un bloque grande de condiciones que crezca cada vez que aparezca un nuevo medio.

**Cómo se resolvió:** se definió el contrato `MedioDeEntrega.planear(pedido, contexto) -> Plan` y se creó una implementación independiente para camioneta, motocicleta, bicicleta y dron.

**Qué vecino no es:** no es Adapter, porque aquí no se están transformando formatos externos; se está encapsulando la forma de planear cada medio de entrega.



## Adapter

**Qué inconveniente resuelve:** los proveedores externos de IA pueden devolver información en formatos diferentes, como JSON o XML, y esos formatos no deben mezclarse con el dominio.

**Cómo se resolvió:** `AdapterJson` y `AdapterXml` convierten las respuestas de sus respectivos proveedores a un objeto interno común `Sugerencia(medio, motivo)`.

**Qué vecino no es:** no es Strategy, porque su responsabilidad no es decidir cómo realizar una entrega, sino traducir una interfaz/formato externo a la representación que entiende el dominio.



## Fábrica simple

**Qué inconveniente resuelve:** el código que conoce las clases concretas de los medios no debe estar repartido por la vista o por el trámite.

**Cómo se resolvió:** `fabrica.crear(medio)` centraliza la creación de `EntregaCamioneta`, `EntregaMotocicleta`, `EntregaBicicleta` y `EntregaDron`.

**Por qué no usamos Factory Method:** no existen familias de trámites que necesiten redefinir un método de creación. El problema de esta práctica solamente requiere centralizar la creación a partir de un string, por lo que una fábrica simple es suficiente.



## Flujo del trámite

El alta del pedido sigue este recorrido:

`registrar_pedido() → Adapter → Sugerencia → Factory → Strategy → Pedido`

La vista solamente llama a `registrar_pedido()` y no conoce las clases concretas de los medios.

## Resultado

Se pueden agregar nuevos medios de entrega sin colocar toda su lógica dentro de la vista. Además, los formatos externos de los proveedores de IA quedan aislados mediante los Adapter y el dominio trabaja únicamente con `Sugerencia`.