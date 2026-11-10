# Microservicios de la plataforma de entregas

Tres contenedores: `gateway` (nginx + formulario HTML), `pedidos` (crea el pedido) y `recomendar` (carga el modelo y aplica las reglas del negocio).

```
navegador → gateway:8080 → pedidos:8001 → recomendar:8002 → modelo_medios.joblib
```

## Levantar

```bash
docker compose up --build
```

Abrir http://127.0.0.1:8080/ y crear un pedido desde el formulario.

## Probar con curl

```bash
curl -i -X POST http://127.0.0.1:8080/pedidos -H "Content-Type: application/json" --data-binary "@paquete.json"
curl http://127.0.0.1:8080/salud/pedidos
curl http://127.0.0.1:8080/salud/recomendar
```

## Fallo parcial

```bash
docker compose stop recomendar
curl -i -X POST http://127.0.0.1:8080/pedidos -H "Content-Type: application/json" --data-binary "@paquete.json"
docker compose start recomendar
```

Con `recomendar` apagado, `pedidos` sigue vivo y responde `503` con un plan B (camioneta por defecto, sin crear el pedido).

## Notas

- `recomendar/entregas/modelo/modelo_medios.joblib` es el mismo modelo de `dataset-medios/`. Si se reentrena, hay que copiarlo aquí y reconstruir solo `recomendar`: `docker compose up --build recomendar`.
- Las versiones de `recomendar/requirements.txt` son las mismas con las que se entrenó el modelo; si se cambian, el `.joblib` puede no cargar.
