# Día 5 — Endpoint JSON

## Problema

El panel web ya funciona y devuelve HTML en `/pedidos/<id>/`.

Una futura aplicación móvil necesita los mismos datos en formato JSON.
Si se creara una fuente de datos separada, habría dos lugares donde actualizar
el estado de un pedido, con riesgo de inconsistencias.

## Solución

Se creó el endpoint:

    GET /api/pedidos/<id>/

que representa el mismo pedido almacenado en la base de datos.

La implementación usa `JsonResponse` de Django, sin necesidad de
Django REST Framework para un endpoint de esta magnitud.

## Datos

El JSON mínimo contiene:

```json
{
    "folio": 10,
    "estado": "Registrado",
    "eta": "1 hora (dron urgente)"
}
```

- **folio** — identificador del pedido en la BD.
- **estado** — estado actual del pedido (ej. "Registrado").
- **eta** — tiempo estimado de entrega calculado por el Strategy.

## Reutilización

Se creó el helper `_datos_pedido(pedido)` en `views.py`.

Devuelve un `dict` con los tres campos mínimos.

La vista HTML lo mezcla con datos adicionales (mapa, pago, coordenadas).
La vista JSON lo pasa directamente a `JsonResponse`.

```
Pedido (BD)
    ↓
_datos_pedido()          ← un solo lugar para leer folio, estado, eta
    ↓              ↓
  HTML           JSON
(contexto)   (JsonResponse)
```

No existe duplicación de la lógica de consulta.

## Pedido inexistente

```
GET /api/pedidos/999999/
→ HTTP 404
```

Django lo maneja automáticamente a través de `get_object_or_404()`.

## Defensa — "Si mañana hay triciclo, ¿cuántos archivos abrimos?"

**Dos archivos.**

1. `entregas/medios.py` — crear `EntregaTricicleta` con su método `planear()`.
2. `entregas/fabrica.py` — registrar `'triciclo': EntregaTricicleta` en el dict.

Ningún otro archivo cambia:

- `views.py` no cambia — no sabe qué medio usa el pedido.
- `services.py` no cambia — llama a `strategy.planear()` sin importar cuál es.
- `urls.py` no cambia — las rutas son independientes del medio.
- Los templates no cambian — solo muestran lo que el contexto les entrega.
- El endpoint JSON no cambia — lee el mismo `eta` del pedido ya guardado.

Esto es exactamente lo que garantiza el patrón Strategy: el algoritmo de cada
medio está encapsulado en su propia clase, y el código que lo usa (el servicio)
solo conoce la interfaz `planear()`, no la implementación concreta.

## Recorrido completo del flujo

```
POST /pedidos/
   ↓
crear_pedido_view()
   ↓ delega
registrar_pedido()
   ↓
obtener_sugerencia_con_fallback()
   ├─ IA disponible → Adapter → Sugerencia real
   └─ IA caída     → Sugerencia fallback (camioneta)
   ↓
fabrica.crear(sugerencia.medio)
   ↓ devuelve
Strategy correcto (dron / bicicleta / motocicleta / camioneta)
   ↓
strategy.planear(pedido, contexto)
   ↓ devuelve
Plan(medio, eta)
   ↓
transaction.atomic()
   ├─ Pedido.objects.create(...)
   ├─ Pago.objects.create(...)
   └─ on_commit(notificar, robust=True)
   ↓
COMMIT
   ↓
notificación post-commit
   ↓
redirect → GET /pedidos/<id>/

                 ┌──────────────────────────────────┐
/pedidos/<id>/  │  HTML — mapa, folio, ruta, pago   │
/api/pedidos/   │  JSON — { folio, estado, eta }     │
                └──────────────────────────────────┘

Ambas representaciones leen el mismo Pedido desde la BD
a través de _datos_pedido(). No hay dos fuentes de verdad.
```
