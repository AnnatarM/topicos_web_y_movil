# Examen — Microservicios, gateway y el monolito con API

**Tópicos Selectos de Tecnologías Web y Móvil**

Nombre: Annatar Armando Murillo Rivera
Matrícula: 22121283

## 1

a) Con la API cree que separó al cliente del servidor, y en parte es cierto: si hay un contrato claro, el cliente pide datos sin conocer cómo está hecho Django por dentro. Pero eso solo separa *quién muestra* de *quién procesa*. Con Docker cree que separó el servidor en partes, y ahí está el error: Docker empaqueta y ejecuta una aplicación, no la divide. Si todo el proyecto vive en una sola imagen y se despliega junto, sigue siendo un monolito, aunque esté dentro de un contenedor.

b) Un Django con usuarios, pedidos y recomendaciones, que expone una API y corre completo en un contenedor, **sigue siendo un monolito**. Para empezar a dividirlo, sacaría primero **recomendar**: es la parte más pesada (scikit-learn y el `.joblib`) y la que cambia por razones distintas (cuando se reentrena el modelo). Tendría su propio proceso, su imagen y su API, y pedidos lo llamaría por HTTP. Así puedo actualizar el modelo sin volver a desplegar todo Django, que es justo lo que hicimos en la práctica con `pedidos` y `recomendar`.

c) La frase habla de **límites y responsabilidades**, no de herramientas. La API define cómo se comunican cliente y servidor; los microservicios separan partes del sistema para que se desplieguen y fallen por separado. REST y Docker ayudan, pero no crean esa separación por sí solos.

## 2

a) Las rutas solo organizan las operaciones. Tener `/usuarios`, `/pedidos` y `/recomendar` no significa que haya tres servicios: las tres pueden estar en el mismo `urls.py` del mismo proyecto. Las réplicas son copias de la misma aplicación: reparten la carga y aguantan si se cae una copia, pero no separan responsabilidades. Y tres réplicas tampoco garantizan alta disponibilidad por sí solas: hace falta un balanceador que detecte la copia caída y datos que no vivan en una sola instancia (lo vimos con `pedidos_en_memoria` en la etapa 5).

b) Sigue siendo un monolito, porque cada réplica ejecuta la aplicación completa. El pedido que se estaba procesando en la copia que se cayó queda en duda: pudo haberse guardado antes de que se perdiera la respuesta, o no haberse guardado. Si el cliente repite el POST sin ningún control, se puede duplicar.

c) Propondría estos servicios:

- **gateway:** la única entrada pública; dirige las rutas.
- **usuarios:** registro, login y perfiles.
- **pedidos:** crea pedidos y genera los folios.
- **recomendar:** carga el modelo y sugiere el medio.

Cada uno con su proceso y su despliegue. Usaría **cuatro imágenes**, una por servicio, porque cada uno tiene dependencias distintas (por ejemplo, solo recomendar necesita scikit-learn). Técnicamente el mínimo podría ser una imagen ejecutada con comandos distintos, pero eso volvería a empaquetar todo junto: cualquier cambio reconstruiría todo.

## 3

a) Tiene funciones de gateway, pero como además hace todo lo demás, en la práctica es un monolito. Es como un recepcionista que, además de recibir a la gente, decide el transporte, registra los pedidos y manda los correos. Validar el JWT y dirigir las peticiones le toca al gateway; elegir el transporte y guardar pedidos es lógica del negocio y debe vivir en otros servicios.

b) Tres consecuencias:

1. Para actualizar el modelo hay que volver a desplegar la misma pieza por la que entran todos los clientes.
2. Si el correo se manda dentro de la petición y el servidor de correo falla o tarda, la compra falla o tarda, aunque el pedido ya se haya guardado.
3. El modelo pesado comparte CPU y memoria con todo lo demás. Si se satura al predecir, también se vuelve lento recibir peticiones y crear pedidos.

c) Lo separaría así:

- **En el borde, gateway:** valida el JWT, dirige las rutas y sirve el HTML.
- **Detrás, pedidos:** valida la compra, genera el folio y guarda el pedido.
- **Detrás, recomendar:** carga el `.joblib` y propone el transporte.
- **Detrás, un trabajador de avisos:** manda los correos pendientes y reintenta cuando falla.

Pedidos guardaría el aviso como "pendiente" junto con el pedido. Así, si el correo falla, la compra no se pierde ni el cliente tiene que repetirla.

## 4

a) Dentro de un contenedor, `127.0.0.1` es **el mismo contenedor**. Pedidos estaría buscando un proceso en su propio puerto 8002, donde no hay nada, en lugar de buscar al contenedor de recomendar.

b) `http://recomendar:8002` funciona porque Compose pone a todos los servicios en una red compartida con un DNS interno, y cada servicio se puede encontrar por su nombre en el `docker-compose.yml`. Además, recomendar tiene que escuchar en `0.0.0.0` y no solo en su `localhost` (en la práctica, `app.run(host="0.0.0.0", port=8002)`).

c) Usaría `RECOMENDAR_URL=http://192.168.0.57:8002`. Para que funcione:

1. Recomendar debe escuchar en una interfaz accesible (`0.0.0.0:8002`) y, si corre en Docker, publicar el puerto 8002 hacia esa laptop.
2. La red y el firewall de los dos equipos deben permitir la conexión a ese puerto.

Cambiar la URL no arregla un firewall cerrado, un servicio que solo escucha en `localhost` ni una red Wi-Fi que aísla a los clientes entre sí.

## 5

a) Unos **205 ms**, más el tiempo de red y procesamiento que no incluye el ejercicio: 200 ms de recomendar más 5 ms del gateway. El que marca el tiempo es recomendar. El timeout de 3 segundos solo se espera cuando recomendar no responde.

b) El cliente ve su pedido creado, con respuesta 200, pero tarda unos **3 055 ms**: 3 000 ms esperando el timeout, más 50 ms del plan B y 5 ms del gateway. La "mentira" es que la respuesta se ve igual que una normal, aunque la moto no la eligió el modelo sino el respaldo, y quizá no sea el mejor medio. El pedido debe guardar el medio que de verdad se va a usar y marcar que vino del plan B. En la práctica lo resolvimos distinto: pedidos responde 503 con `pedido_creado: false` y `motivo: "pendiente de validación"`, así que no se hace pasar el respaldo por una recomendación normal.

c) Si cada petición se queda reintentando unos 30 segundos, en 10 minutos llegan alrededor de 167 pedidos (con tráfico parejo), y todos se quedan esperando a la vez. Los reintentos le mandan todavía más llamadas a un servicio que ya está caído y ocupan los workers de pedidos y las conexiones del gateway. Si se acaban, las peticiones se empiezan a encolar y el gateway termina respondiendo con timeout: la caída de recomendar tumba también a pedidos.

El plan B no siempre es peor: si permite cumplir el envío, es mejor responder rápido con una opción aceptable que dejar al cliente esperando. Haría pocos reintentos, con un tiempo máximo corto, y si el fallo sigue dejaría de llamar a recomendar por un rato (*circuit breaker*) y usaría el respaldo directamente.

## 6

Supongo que el gateway sirve el HTML, que es la única entrada pública y que pedidos tiene el plan B del ejercicio anterior.

1. **Se apaga el gateway:** la página no carga y no se puede crear nada. Pedidos y recomendar siguen vivos, pero nadie de afuera llega a ellos.
2. **Se apaga pedidos:** la página sí carga, porque la sirve el gateway, pero crear un pedido falla; el gateway responde 502 o 503. Recomendar sigue vivo, aunque nadie lo llama.
3. **Se apaga recomendar:** la página carga y se siguen creando pedidos, solo que más lentos: pedidos espera el timeout y usa el respaldo. Es el fallo parcial que comprobamos en la práctica con `docker compose stop recomendar`.

Si el HTML lo sirviera pedidos, al apagarlo tampoco cargaría la página. Si pedidos no tuviera plan B, al apagar recomendar tampoco se podrían crear pedidos.

Con el gateway apagado, el sistema **se ve** completamente muerto desde afuera aunque las otras dos piezas funcionen. Eso muestra que el gateway es un punto único de falla: si toda la entrada depende de él, necesita estar replicado.

## 7

a) El problema es tener dos entradas que los clientes eligen a mano y que con el tiempo pueden quedar con reglas distintas: una pide autenticación y la otra no, o tienen rutas o límites diferentes. Que las dos respondan 200 no significa que se comporten igual. Dos instancias de gateway sí ayudan a la disponibilidad, pero deben verse como **una sola entrada** (con un balanceador o un DNS delante), compartir la misma configuración y poder sustituirse si una falla.

b) `localhost` es la máquina de Beto (o el contenedor de pedidos, si corre en Docker), no la de Carla. Debe usar la IP de Carla: `RECOMENDAR_URL=http://192.168.0.57:8002`. Además, Carla tiene que exponer el puerto y permitir el acceso en su firewall.

c) Con aislamiento de clientes en la red, la práctica no se puede hacer como está planteada. Que falle `ping` no prueba por sí solo que HTTP esté bloqueado (muchos firewalls bloquean solo ICMP), pero si el aislamiento es real, ninguna conexión entre laptops va a pasar. Como plan B, levantaría gateway, pedidos y recomendar en una sola computadora con Compose, cada uno en su contenedor. La lección se mantiene: son procesos separados, se llaman por red y pueden fallar por separado.

## 8

a)

1. El navegador tiene que conocer las direcciones internas de cada servicio; si se mueve uno, hay que cambiar el frontend.
2. Cada servicio queda expuesto a internet y las llamadas se saltan los controles del gateway (autenticación, límites de uso). Hay más puertas que cuidar.
3. El frontend termina coordinando la lógica del negocio: si recomendar responde pero pedidos falla, el navegador tiene que decidir qué hacer y cómo reintentar sin duplicar el pedido.

Además, al ser orígenes distintos, aparecen los problemas de CORS.

b) El navegador hace **una sola** llamada al gateway (`POST /pedidos`). El gateway la manda a pedidos; pedidos consulta a recomendar, aplica el plan B si hace falta, guarda el pedido y regresa el folio y el medio a través del gateway. Es lo que hace el `index.html` de la práctica. Pedidos es quien habla con recomendar porque es el dueño del flujo de crear un pedido y el que decide qué hacer si la recomendación falla. El navegador ni siquiera necesita saber que recomendar existe.

c) El folio lo crea **pedidos**. Recomendar solo recibe los datos del paquete (y, si acaso, qué modelo usar: árbol, bosque o red) y devuelve una sugerencia, sin guardar nada. Si los dos crearan pedidos o folios por su cuenta, una compra podría terminar con dos registros distintos que no coinciden, o duplicados. Cada dato debe tener un solo dueño.

## 9

a) `cerebro` es un nombre que no dice qué hace. Además, junta dos responsabilidades que no tienen nada que ver: elegir el transporte y generar textos de venta. Si `/inteligente` tiene que esperar las dos cosas, los 8 segundos del LLM hacen imposible cumplir los menos de 500 ms que necesita el despacho.

b) Lo partiría en dos:

- `POST /textos-producto`: genera el texto de venta. Lo usa el frontend de la tienda a través del gateway, y mientras tanto puede mostrar un texto ya guardado.
- `POST /sugerir-transporte`: devuelve el medio recomendado. Lo usa pedidos dentro del flujo de envío.

Cada uno en su propio servicio, porque tienen dependencias, tiempos y recursos (GPU contra CPU) muy diferentes. Así, si el LLM se pone lento, el despacho no se entera.

c) El frontend apunta al gateway y solo el servicio de textos habla con el servidor de GPU. Si cambia el proveedor, se cambia una sola configuración (por ejemplo, una variable de entorno con la URL) en el servicio de textos. Si además cambia el formato de su API, se ajusta un adaptador dentro de ese mismo servicio, igual que hicimos con el Adapter de `proveedores_ia.py`. Nadie más se entera.

## 10

a)

> En siete días sí podemos reducir riesgos reales y mejorar la app de clientes.
> El panel funciona y tiene poco tráfico; dividirlo ahora no resuelve ningún problema demostrado.
> Con cinco personas, seis servicios nuevos son seis despliegues y muchas conexiones que pueden fallar.
> Si lo hacemos con prisa, podemos romper cosas que hoy sí funcionan.
> Propongo proteger el gateway y aislar el reentrenamiento del modelo esta semana.
> El panel lo dividimos después, cuando los datos muestren dónde hace falta.

b) Mi orden: **3, 2, 1, 4**.

- **(3) Auth y rate limit en el gateway público:** es una puerta que ya está expuesta; cerrarla protege todo lo demás.
- **(2) Separar el reentrenamiento:** permite actualizar el modelo sin tumbar pedidos, y validar el modelo nuevo antes de ponerlo en uso.
- **(1) Partir el panel en seis servicios:** lo dejo para después; funciona, tiene poco tráfico y no hay un problema medido que lo justifique.
- **(4) Subir el LLM sin timeouts ni plan B:** no lo llevaría a producción así. Primero necesita un tiempo máximo de espera y una respuesta de respaldo.

Este orden supone que el reentrenamiento hoy no está tirando pedidos. Si ya lo estuviera haciendo, lo atendería primero.

c) Una métrica: si durante cuatro semanas los reportes del panel usan más del 60 % de la CPU y, mientras corren, el 95 % de las demás peticiones tarda más de 2 segundos. Eso sería una razón medible para sacar los reportes a su propio proceso, después de revisar si se puede resolver optimizando las consultas.

d) Los microservicios resuelven problemas concretos; tener más servicios no hace mejor a un sistema.
