# La empresa de entregas

Proyecto con Django que implementa una API web para una empresa de entregas, aplicando patrones de diseño concretos al problema planteado.


## Qué es este proyecto

Una aplicación web que permite registrar pedidos de entrega, asignarles un medio de transporte (dron, bicicleta, motocicleta, camioneta) y consultar su seguimiento.

El mismo pedido se expone en dos formatos:
- **HTML** en `/pedidos/<id>/` — para el panel web.
- **JSON** en `/api/pedidos/<id>/` — para una futura aplicación móvil.


## Requisitos

- Python 3.11+
- Django 4.2+ (incluido en `requirements.txt`)
- SQLite (incluido en Python)


## Configuración del entorno

```bash
# Crear entorno virtual
python -m venv venv

# Activar (Windows PowerShell)
venv\Scripts\Activate.ps1

# Instalar dependencias
pip install django
```


## Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```



## Iniciar el servidor

```bash
python manage.py runserver
```

El servidor queda disponible en http://127.0.0.1:8000/



## Uso de los endpoints

### Crear un pedido

```
POST /pedidos/
```

Campos del formulario:

| Campo    | Tipo    | Ejemplo    |
|----------|---------|------------|
| origen   | texto   | Morelia    |
| destino  | texto   | Tarimbaro  |
| peso     | decimal | 5.0        |

Después del POST, el navegador redirige a la página de seguimiento (patrón PRG).

---

### Seguimiento HTML

```
GET /pedidos/<id>/
```

Devuelve la página de seguimiento con mapa interactivo, estado, ETA, medio de entrega y pago simulado.

Ejemplo:

```
GET /pedidos/10/   →   HTML con mapa, folio, ruta Morelia → Tarimbaro, dron, ETA, pago
```

---

### Seguimiento JSON (Día 5)

```
GET /api/pedidos/<id>/
```

Devuelve el mismo pedido en formato JSON. Sin Django REST Framework; usa `JsonResponse` nativo de Django.

Ejemplo:

```http
GET /api/pedidos/10/
```

```json
{
    "folio": 10,
    "estado": "Registrado",
    "eta": "1 hora (dron urgente)"
}
```

Si el pedido no existe:

```http
GET /api/pedidos/999999/
→ HTTP 404
```


## Patrones de diseño implementados

### Strategy — `entregas/medios.py`

**Problema que resuelve:** cada medio de entrega (dron, camioneta, etc.) tiene su propio algoritmo para calcular el ETA. Sin Strategy, la lógica de todos los medios quedaría mezclada en un único bloque `if/elif` dentro del servicio.

**Dónde está:** `EntregaDron`, `EntregaCamioneta`, `EntregaMotocicleta`, `EntregaBicicleta` — cada una implementa `planear(pedido, contexto) → Plan`.

**Cómo encaja:** `registrar_pedido()` recibe un Strategy (creado por la Fábrica) y llama a `strategy.planear(...)`. Si mañana se agrega un triciclo, solo se crea `EntregaTricicleta` y se registra en la Fábrica; el servicio no cambia.

---

### Adapter — `entregas/proveedores_ia.py`

**Problema que resuelve:** existen dos proveedores de IA externos con formatos incompatibles (uno devuelve JSON, el otro XML). Sin Adapter, la lógica de parseo quedaría mezclada con la lógica de dominio.

**Dónde está:** `AdapterJson` y `AdapterXml` — ambos exponen `obtener_sugerencia(peso) → Sugerencia`. El dominio nunca ve `route_hint` ni `<vehicle>`.

---

### Fábrica simple — `entregas/fabrica.py`

**Problema que resuelve:** decidir qué Strategy instanciar según el medio sugerido por la IA. Sin Fábrica, el servicio tendría que saber qué clase concreta instanciar en cada caso.

**Dónde está:** `fabrica.crear(medio) → Strategy`. Un `dict` mapea el nombre del medio a la clase correspondiente.

---

### Service Layer / `registrar_pedido` — `entregas/services.py`

**Problema que resuelve:** la vista no debe conocer el detalle de cómo se registra un pedido (IA, Strategy, persistencia, pago, notificación). Sin esta capa, toda esa lógica viviría en la vista.

**Dónde está:** `registrar_pedido(datos_formulario) → Pedido`. Coordina: fallback de IA → Adapter → Fábrica → Strategy → `transaction.atomic()`.

---

### Post/Redirect/Get (PRG) — `entregas/views.py`

**Problema que resuelve:** si el usuario recarga la página después de enviar el formulario, el navegador repetiría el POST y se crearía un pedido duplicado.

**Dónde está:** `crear_pedido_view` hace `redirect('seguimiento_pedido', pk=...)` después del POST.

---

### `transaction.atomic()` — `entregas/services.py`

**Problema que resuelve:** garantizar que el Pedido y el Pago se crean juntos o no se crea ninguno. Sin `atomic()`, podría quedar un Pedido sin Pago si la segunda operación falla.

**Dónde está:** bloque `with transaction.atomic():` dentro de `registrar_pedido()`.

---

### `transaction.on_commit()` — `entregas/services.py`

**Problema que resuelve:** la notificación al cliente no debe ejecutarse si la transacción falla. Sin `on_commit()`, la notificación podría dispararse antes de que el pedido sea confirmado en la BD.

**Dónde está:** `transaction.on_commit(lambda: _notificar_pedido(...), robust=True)` dentro del bloque `atomic()`.

`robust=True` garantiza que si la notificación falla, el pedido ya confirmado no desaparece ni la respuesta HTTP devuelve un error 500.

---

## Qué proporciona Django

| Funcionalidad        | Dónde la proporciona Django           |
|----------------------|---------------------------------------|
| Enrutamiento         | `urls.py` + `path()`                  |
| Middleware           | `MIDDLEWARE` en `settings.py`         |
| Sistema de plantillas| `render()` + templates HTML           |
| ORM                  | `Pedido.objects.create()`, `.get()`   |
| Transacciones        | `transaction.atomic()`, `on_commit()` |
| Formularios básicos  | `request.POST`                        |
| Respuesta JSON       | `JsonResponse`                        |
| 404 automático       | `get_object_or_404()`                 |

Estas funcionalidades no fueron reimplementadas porque Django ya las resuelve correctamente para la escala de este proyecto.

---

## Qué no se implementó

| No implementado           | Por qué no es necesario aquí                                              |
|---------------------------|---------------------------------------------------------------------------|
| Event Sourcing            | El estado del pedido no necesita historial de eventos                    |
| CQRS                      | La carga de lecturas y escrituras no justifica separar los modelos       |
| Redux                     | No hay estado complejo en el cliente; el servidor maneja todo            |
| Django REST Framework     | Un solo endpoint JSON no requiere un framework completo de serialización |
| Aplicación móvil nativa   | Solo se expone el JSON; la app móvil es trabajo futuro                   |
| Pagos reales              | El pago es una simulación para demostrar atomicidad                      |
| Correo real               | La notificación es un `print()`; el mecanismo está demostrado            |
| Idempotencia completa     | El pago es simulado; en producción sería necesaria para evitar doble cobro|

---

## Recorrido completo del flujo (para presentación oral)

```
POST /pedidos/
    ↓
crear_pedido_view()          ← vista — recibe el formulario
    ↓
registrar_pedido()           ← servicio — coordina todo
    ↓
obtener_sugerencia_con_fallback()   ← Adapter hacia proveedor externo
    ↓                               ← si falla → fallback automático
Sugerencia(medio, motivo)    ← objeto de dominio limpio
    ↓
fabrica.crear(medio)         ← Fábrica → devuelve el Strategy correcto
    ↓
strategy.planear(pedido, contexto)  ← Strategy → calcula ETA
    ↓
Plan(medio, eta)
    ↓
transaction.atomic()
    ├─ Pedido.objects.create(...)   ← persistencia
    ├─ Pago.objects.create(...)     ← pago simulado (mismo atomic)
    └─ on_commit(notificar, robust=True)
    ↓
COMMIT
    ↓
notificación post-commit
    ↓
redirect → GET /pedidos/<id>/

                        ┌───────────────────────────────┐
GET /pedidos/<id>/  →   │   HTML con mapa y seguimiento │
GET /api/pedidos/<id>/  │   JSON { folio, estado, eta } │
                        └───────────────────────────────┘
```

Ambas vistas leen el mismo Pedido de la BD a través de `_datos_pedido()`.

---

## Ejecutar las pruebas

```bash
python manage.py test entregas
```

**70 tests, 0 fallos** 
