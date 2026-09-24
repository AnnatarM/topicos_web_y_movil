# Paso 1 — ¿Qué está pasando aquí?

**Plataforma de mensajería.** Cliente ya decidido: panel web **y** app móvil.
Sin nombres del catálogo. El objetivo es describir el inconveniente, no bautizarlo.

---

## Tabla

| # | Cuál es el inconveniente principal (una frase) | Qué está cambiando o va a cambiar | Qué no debería reescribirse cada vez | Qué se mezcló que no debía |
|---|---|---|---|---|
| **1** | Cada trámite repite por su cuenta el control de entrada, así que una política que es **una sola** se mantiene en cuarenta copias. | La caducidad del token, el formato de la bitácora, el contenido del encabezado. Y la cantidad de trámites, que crece cada semana. | El cuerpo de cada trámite. Cambiar la política debería costar un archivo, no cuarenta. | Lo que **rodea** a un trámite (sesión, bitácora, encabezado) con lo que el trámite **hace** (dar de alta un pedido, cobrar). |
| **2a** | La decisión de cómo se entrega vive en un `switch` único, así que agregar un medio obliga a editar y volver a probar código que ya funcionaba. | El catálogo de medios (llega el dron, mañana el triciclo) y también el costo, el tiempo y las restricciones de los que ya existen. | El procedimiento general de asignar. Y los otros cuatro medios cuando entra el quinto. | Las reglas particulares de cada medio con el procedimiento común de asignar. Y cuatro medios que no se parecen en nada, revueltos en un mismo bloque. |
| **2b** | Cada proveedor de IA habla su propio idioma (`route_hint`, `score`, XML, objeto interno) y ese vocabulario ajeno se mete hacia adentro en vez de traducirse una vez en la puerta. | El proveedor, su formato, y los nombres de sus campos incluso **sin** cambiar de proveedor. | El dominio, que solo quiere `Sugerencia{ medio, motivo }`. Ni el panel ni la app deberían enterarse. | El **formato** del mensaje externo con el **significado** que el negocio le da. Y algo más grave: *recomendar* con *decidir*. La IA opina; quien asigna es el sistema. |
| **3** | La plantilla consulta la base y calcula el ETA, así que el mismo cálculo vive duplicado en el seguimiento y en el reporte de gerencia, con formatos distintos. | Los formatos de salida (mapa, reporte, app móvil) y la forma de calcular el ETA o de consultar. | El cálculo del ETA cuando se agrega un formato. La consulta cuando cambia el diseño de la pantalla. | Obtener datos y calcular con **pintarlos**. La vista conoce la bodega. |
| **4** | Un mismo script hace lo indivisible (dar de alta el envío) junto con lo que puede fallar y reintentarse (correo, aviso), y además no distingue un pago repetido de uno nuevo. | Quién se entera: cliente, repartidor, administrador, notificaciones, estadísticas, IA. Esa lista solo crece. Y los canales. | El cobro y el alta del envío cada vez que alguien nuevo quiere enterarse. | Tres cosas distintas: (a) que el hecho ocurra completo o no ocurra, (b) avisar de sus consecuencias, (c) reconocer que **esta** operación ya se hizo. El doble clic es el tercero, y no se arregla con transacciones. |
| **5** | No hay un contrato pensado por pantalla: se expone la estructura interna y cada cliente la recompone como puede, doce peticiones para pintar un inicio. | Las pantallas y qué necesita cada una. Los tres clientes (panel, app cliente, app repartidor) y sus versiones, que no se actualizan el mismo día. | El pedido y su estado cuando una pantalla cambia de forma. La lógica de negocio cuando cambia un formato. | Cómo se **guarda y se razona** un pedido con cómo lo **necesita ver** cada pantalla. Un JSON mínimo y un HTML con mapa no son el mismo problema. |
| **6** | Colaboradores externos que son opcionales están en el camino crítico, así que una falla ajena bloquea consultas que solo dependen de nuestra base. | La disponibilidad y la lentitud de terceros. No lo controlamos y no va a mejorar. | Nada, en realidad: aquí no falta código, falta un **límite**. Cuánto se espera y qué se hace cuando no hubo respuesta. | Lo indispensable con lo accesorio. El dato propio (está en nuestra base) con el dato prestado (mapa, sugerencia). |
| **7** | Se propone una arquitectura cara para un trámite que solo lee: autenticar, consultar un pedido existente, generar un archivo. | Casi nada. No hay historia que reconstruir, ni estado compartido complejo, ni asimetría de carga. | No aplica: no hay eje de cambio que pague esa estructura. Lo que sí se pagaría es la complejidad, todos los días. | La madurez con el prestigio del vocabulario. Se eligió la solución antes de tener el problema. |

---

## Las cuatro preguntas

### 1. Si mañana aparece un quinto medio (triciclo eléctrico), ¿cuántos archivos abrirían hoy?

Muchos, y ninguno se llama «triciclo». Contando lo que el relato describe:

1. El `switch` de asignación (punto 2a).
2. Donde se calcula el **costo**, si el precio depende del medio (punto 4, el cobro).
3. Donde se calcula el **tiempo estimado**, que hoy vive dentro de la plantilla (punto 3).
4. Las **restricciones** (peso, dimensiones): un triciclo no carga lo mismo que una camioneta ni lo mismo que una bici.
5. La **plantilla del seguimiento** (ícono, etiqueta, ETA).
6. El **reporte de gerencia**, que duplica esas consultas.
7. El **panel web** y **la app móvil**, que muestran el medio (punto 5). Son dos clientes, y la app instalada en los teléfonos no se actualiza el mismo día.
8. El **traductor de la IA**, si el proveedor empieza a devolver un identificador que hoy no existe (punto 2b).

Estimación honesta: **entre 6 y 10 archivos, repartidos en tres capas distintas**.

Lo que nos preocupa no es el número, es de qué depende: hoy crece con el **tamaño del sistema**, no con el tamaño del cambio. Agregar el sexto medio costará más que el quinto. En un diseño sano, agregar un medio debería costar **un archivo nuevo más un registro**, y ningún archivo existente editado.

---

### 2. Si el proveedor de IA cambia `route_hint` por `vehicle`, ¿se rompe también el panel? ¿Y la app?

Depende de una sola cosa: **cuántos archivos mencionan la palabra `route_hint`**. Es una prueba que se puede hacer hoy mismo con una búsqueda de texto en el proyecto.

- Si aparece en **un solo lugar** (la puerta por donde entra la respuesta del proveedor), se rompe ese lugar y nada más. El panel y la app siguen recibiendo `Sugerencia{ medio, motivo }` y ni se enteran de que hubo un cambio.
- Si aparece **regado**, tal como está descrito hoy, entonces sí: se rompe donde se decide el medio, se rompe el panel si la plantilla lee ese campo, y se rompe la app si ese nombre viaja dentro del JSON que consume.

El caso de la app es el peor de los tres, y conviene decirlo en voz alta: **el panel se arregla desplegando; la app instalada en los teléfonos, no**. Hay versiones viejas allá afuera esperando un campo que ya no existe. Un cambio de nombre en un servicio ajeno no debería tener forma de llegar hasta el teléfono de un cliente.

Conclusión del equipo: el nombre del campo de un tercero **no es un dato del negocio**. Es un detalle del formato de entrada y tiene que morir en la frontera.

---

### 3. Si el correo al cliente falla, ¿el cobro se deshace?

Hoy pasa lo peor de los dos mundos.

El **cobro no se deshace**: ya hay un cargo real en el proveedor de pagos, y eso no se cancela porque un script se haya caído. Pero **a veces no queda envío**. O sea: el cliente pagó y no tiene pedido. El correo, que es el efecto menos importante de los tres, terminó decidiendo si existe el hecho más importante.

Cómo debería ser:

- El correo **no puede deshacer nada**. Si falla, se reintenta; el envío ya existe y el cliente ya puede verlo en la app aunque nunca le llegue el correo.
- El aviso al repartidor es igual: importante, pero llega después y puede llegar tarde.
- Y el dinero cobrado casi nunca «se deshace»: se **reembolsa**, que es otra operación, con su propio registro y su propia autorización. No es un `rollback`.

Aparte, y esto es un problema distinto que el correo tapa: **si el cliente pulsa dos veces, hay dos cargos**. Eso no se arregla haciendo la transacción más grande. Se arregla si el sistema puede reconocer que esa petición ya la atendió.

---

### 4. Si la IA está caída, ¿pueden ver un pedido que ayer sí se guardó?

Deberían, y hoy no pueden. Ese pedido está completo en **nuestra** base: folio, origen, destino, peso, estado. No necesita ninguna recomendación para poder mostrarse.

Consultar un pedido guardado es **leer un dato propio**. Recomendar un medio es **pedirle una opinión a un tercero**. Cuando una sola pantalla pide las dos cosas y espera a que lleguen juntas, la parte que sí funciona queda secuestrada por la que no, y el usuario ve la rueda por algo que ni siquiera pidió.

Vale la pena estirar la pregunta: **tampoco debería bloquearse asignar**. Si la IA no contesta, el sistema elige el medio con sus propias reglas (peso, distancia, urgencia, fecha límite) y deja anotado que esta vez no hubo sugerencia. La recomendación es un lujo que mejora la decisión, no un requisito para poder decidir. Si el negocio se detiene porque un tercero se cayó, el tercero dejó de ser un colaborador y se volvió un dueño.

---

## Notas del equipo

Dos celdas nos costaron, y creemos que por la misma razón que dice el enunciado (dos cosas pegadas):

- **Punto 4**, columna «qué se mezcló»: al principio escribimos solo «transacción y correo». Nos faltaba el tercero, el doble clic, que no es un problema de transacción sino de **identidad de la operación**.
- **Punto 6**, columna «qué no debería reescribirse»: no encontrábamos qué. Al final entendimos que ahí el problema no es código repetido, es una **decisión que nadie tomó**: cuánto esperar y qué mostrar mientras tanto.

---

# Paso 2 — Pongan un nombre del catálogo (o escriban «ninguno»)

| # | Nombre del catálogo, o «ninguno» | ¿Por qué este? (con algo del relato) | Uno que se parece pero no es (y por qué) |
|---|---|---|---|
| **1** | **Chain of Responsibility** | «¿Hay sesión?», bitácora y encabezado son verificaciones que se ejecutan **en secuencia** antes de que el trámite haga lo suyo, y cualquiera puede detener el paso (si no hay sesión, no se llega ni a intentar el cobro). Eso es exactamente una cadena de manejadores: cada uno resuelve su parte y pasa al siguiente, sin que el trámite sepa que la cadena existe. Así un cambio en la caducidad del token se hace en **un** manejador, no en cuarenta archivos. | **Decorator.** También «envuelve» comportamiento alrededor de una operación, y por eso se confunde fácil. La diferencia: Decorator añade responsabilidades a un objeto y **siempre** las ejecuta todas, pensado para combinar capacidades (por ejemplo, «pedido con seguro y con urgente»). Aquí lo que necesitamos es que un paso pueda **cortar la cadena** (sin sesión, ni se sigue), que es el comportamiento propio de Chain of Responsibility, no de Decorator. |
| **2a** | **Strategy** | El `switch` decide, para cada medio, restricciones, costo y tiempo: eso es **variación de comportamiento** sobre la misma operación («calcular si este medio sirve y cuánto cuesta»). Con Strategy cada medio es su propia clase intercambiable y agregar el triciclo del punto 1 (pregunta 1) es sumar una clase, no editar las que ya funcionan. | **Factory Method.** Se confunde porque también aparece cuando hay «varios tipos» de algo. La diferencia: Factory resuelve **cómo se crea** un objeto; Strategy resuelve **cómo se comporta** un objeto que ya existe. Aquí el problema no es instanciar el medio, es que las doscientas líneas deciden y calculan; eso es comportamiento, no creación. |
| **2b** | **Adapter** | Tres proveedores de IA, tres formatos (JSON con `route_hint`/`score`, XML, un objeto interno), y el dominio solo quiere `Sugerencia{ medio, motivo }`. Adapter existe justo para esto: convertir una interfaz incompatible (la del proveedor) en la que el cliente (el dominio) ya espera, sin que el dominio sepa que hubo traducción. | **Facade.** Ambos «esconden» algo detrás de una interfaz simple, por eso se confunden. La diferencia: Facade simplifica el acceso a un subsistema **propio**, complejo pero coherente (varias clases que ya trabajan juntas). Adapter reconcilia una interfaz **ajena** que no fue diseñada para encajar con la nuestra. Aquí el problema es literalmente eso: un vocabulario externo (`route_hint`) que no es el nuestro. |
| **3** | **Facade** | El seguimiento y el reporte de gerencia repiten la misma consulta y el mismo cálculo de ETA en dos formatos distintos, y de paso «la vista conoce la bodega». Una Facade da **un** punto de entrada («dame este pedido con su ETA») que esconde la consulta y el cálculo; el seguimiento y el reporte la usan igual, cada uno pinta el resultado como quiera. | **Adapter.** Tentador porque también «pone algo en medio», pero aquí no hay dos formatos incompatibles que reconciliar (no viene de un proveedor externo con su propio vocabulario, como en 2b). Lo que hay es un subsistema propio (base + cálculo) que dos clientes internos repiten por no tener una puerta común. Eso es Facade, no Adapter. |
| **4** | **Observer** | Cuando el envío queda confirmado, correo y aviso al repartidor son reacciones a ese hecho, no partes de él. Con Observer, el cobro solo publica «envío creado» y quien quiera enterarse (correo, repartidor, notificaciones, estadísticas, IA — los seis del enunciado) se suscribe aparte. Así un correo caído ya no puede impedir que el envío exista. | **Mediator.** Se confunde porque también hay «varios objetos que se coordinan». La diferencia: Mediator centraliza una conversación de **ida y vuelta** entre componentes que se necesitan mutuamente. Aquí no hay ida y vuelta: es un hecho que ocurrió y varios interesados que solo escuchan, sin responderle al emisor. Eso es Observer. <br><br>**Aclaración del equipo:** Observer resuelve el acoplamiento entre el cobro y los avisos, pero **no** resuelve la atomicidad (que el envío se cree completo o no) ni el doble clic (idempotencia). Esas dos no son problemas de patrón, son de transacción y de identificar la operación; ningún patrón del catálogo las arregla por sí solo. |
| **5** | **ninguno** | El panel quiere HTML con mapa, la app quiere un JSON mínimo, y hoy la app hace doce peticiones porque nadie diseñó una respuesta pensada para ella. Eso es un problema de **diseño de la API por tipo de cliente** (lo que en la industria se llama backend-for-frontend), no de relación entre objetos dentro de un mismo programa, que es de lo que habla el catálogo GoF. | Lo tentador es escribir **Adapter**: «adaptamos la respuesta para cada cliente». Pero Adapter parte de una interfaz ajena ya existente que hay que reconciliar con una esperada; aquí no hay una interfaz ajena, hay una que **nosotros** diseñamos mal desde el principio. Ponerle Adapter sería nombrar el síntoma (falta traducir) sin nombrar la causa (falta diseñar el contrato por cliente). |
| **6** | **ninguno** | Que el mapa o la IA se caigan y bloqueen una consulta que no los necesita es un problema de **qué tan disponible** es el sistema cuando algo externo falla: cuánto se espera, qué se muestra mientras tanto. El catálogo GoF describe relaciones entre objetos dentro de un programa que ya corre; no dice nada sobre tiempos de espera ni sobre qué hacer cuando la respuesta nunca llega. | Lo tentador es **Proxy**, porque sí está en el catálogo y sí sirve para controlar el acceso a algo remoto (y hasta se le puede sumar una caché). Pero un Proxy no decide por sí solo cuánto esperar antes de rendirse ni qué devolver si no hay respuesta; eso es una política (tiempo límite, y qué mostrar si no llega) que hay que definir aparte. Poner Proxy sin esa política sería nombrar el molde y dejar vacío lo que realmente falla. |
| **7** | **ninguno** | El trámite es autenticar, leer un pedido, generar un archivo: sin historia que reconstruir, sin cargas ni modelos distintos entre lectura y escritura, sin estado compartido en el cliente. No hay ningún eje de cambio (de los que sí encontramos en los puntos 1 a 6) que ese aparato esté resolviendo aquí. Y de hecho Event Sourcing, CQRS y Redux **ni siquiera son parte de los 23 del catálogo GoF**: son ceremonia de otro nivel, mal aplicada a un trámite pequeño. | Lo tentador sería **Command** (sí está en el catálogo): «encapsular la petición de generar el PDF como un objeto». Pero Command paga por poder deshacer, encolar o parametrizar la ejecución de una acción; aquí no hay nada de eso, es leer y generar un archivo una sola vez. Envolverlo en un objeto Command sería la misma ceremonia del punto 7, solo que con un nombre del catálogo en vez de tres de fuera. |

---

## Nota del equipo sobre el paso 2

Nos costó no escribir «ninguno» por pereza en el 3, el 4 y el 2a, que sí tienen un patrón razonable, y por el mismo motivo nos costó **no** inventar uno para el 5, el 6 y el 7 solo por completar la tabla. La prueba que usamos: si al explicar el «por qué» terminábamos describiendo el patrón en vez de describiendo el inconveniente del relato, era señal de que estábamos forzando el nombre.

También notamos un patrón (con perdón del juego de palabras) en nuestras respuestas «ninguno»: el 5, el 6 y el 7 no son problemas de **relación entre objetos**, que es de lo único que habla GoF. Son problemas de **contrato entre sistemas** (5), de **qué hacer cuando algo externo no responde** (6), y de **proporción entre el problema y la solución** (7). Ninguno de los tres vive en el catálogo, y forzar un nombre ahí no sería un error de detalle: sería no haber entendido para qué sirve el catálogo.

---

# Paso 3 — Un conflicto y el cliente web + móvil

**Punto elegido: 4 — «cobro acreditado dispara envío, correo y aviso en el mismo script».**

Lo elegimos porque fue el que más nos costó en los dos pasos anteriores: en el paso 1 nos faltó ver el tercer problema (el doble clic) hasta que lo discutimos en equipo, y en el paso 2 tuvimos que aclarar por separado que Observer resuelve el acoplamiento de avisos pero no la atomicidad ni la idempotencia. Es el único de los siete donde el costo de equivocarse es dinero real de un cliente real, y eso lo hace el más urgente de arreglar aunque no sea el más grande.

## 1. El primer corte (no la arquitectura soñada)

No proponemos un bus de eventos, ni una cola de mensajes, ni un sistema de reintentos elaborado. Eso es exactamente la tentación del punto 7: resolver un problema chico con un aparato grande. El corte mínimo, para mañana, es separar dos momentos que hoy están pegados en un mismo script:

**Momento A — lo que no puede quedar a medias.** Confirmar el cobro y dar de alta el envío se hacen juntos, en el sentido más literal: si algo de eso falla, no debe quedar ni cobro ni envío sueltos. No hace falta inventar infraestructura nueva para esto; alcanza con que ambas escrituras ocurran dentro de la misma operación de base de datos, como ya debería estar (aunque el relato sugiere que hoy ni eso está garantizado).

Junto con esto, y en el mismo corte, agregamos algo que hoy no existe: cuando el cliente manda "pagar", ese intento lleva consigo un identificador propio (que ya se generó al momento de armar el pedido, no al momento de pulsar el botón). Si el mismo identificador llega dos veces —por doble clic, por reintento de la app, por lo que sea— la segunda vez el sistema responde "ya está hecho" y no genera un segundo cargo. Esto no es una funcionalidad nueva y vistosa: es una pregunta que el sistema debe poder responder ("¿ya atendí esto?") y hoy no puede.

**Momento B — lo que sí puede fallar y esperar.** Una vez que el Momento A ya ocurrió (el envío existe, de verdad, en la base), *después* se intenta avisar: correo al cliente, aviso al repartidor. Para el primer corte no hace falta una cola formal; alcanza con que cada aviso se intente en su propio bloque, que si falla no deshaga nada del Momento A, y que quede una marca de "correo pendiente" o "aviso pendiente" que se pueda reintentar más tarde (aunque sea con un botón manual de "reenviar" al principio, antes de automatizarlo).

Con este corte, la pregunta de la actividad anterior ("si el correo falla, ¿el cobro se deshace?") ya tiene una respuesta clara: no, porque el correo ni siquiera puede tocar esa parte.

## 2. Qué no tocaríamos

- El esquema del pedido y del envío (origen, destino, peso, dimensiones, urgencia, fecha límite): no es parte de este conflicto, y tocarlo aquí sería arreglar algo que no está roto.
- La integración con el cobro en sí (cómo se autoriza un pago): el problema no es *cómo* se cobra, es *qué pasa alrededor* de que ya se cobró.
- El switch de medios (punto 2a) y el traductor de la IA (punto 2b): son otro conflicto, con otro ritmo de cambio. Mezclarlos aquí sería repetir el mismo error que estamos corrigiendo.
- Quiénes se enteran del cambio de estado, más allá de correo y repartidor: el relato menciona también notificaciones, administrador, estadísticas e IA. No los agregamos en este primer corte porque no es necesario resolver los seis de una vez; el corte de hoy deja el lugar (el "después del Momento A") donde los demás se van a enchufar cuando les toque, sin tener que reabrir el cobro otra vez.
- Cualquier cola de mensajes, bus de eventos o mecanismo de reintento automático sofisticado: eso es una mejora legítima, pero no es el primer corte. El primer corte es que el fallo de un aviso deje de poder romper un cobro.

## 3. Cómo se nota que hay web y móvil

Para este conflicto en particular (confirmar un pago y dar de alta un envío), lo que tiene que ser **idéntico** en panel y app no es la pantalla: es el hecho.

**Lo que no puede cambiar entre los dos clientes:**
- El folio del pedido.
- El estado (pagado / envío creado / pendiente de aviso, etc.).
- El medio asignado.
- El identificador de idempotencia que evita el doble cobro: **tiene que generarse del mismo modo en el panel y en la app**, porque si cada cliente inventa su propio esquema, un doble clic en la app y un doble clic en el panel se comportarían distinto, y eso vuelve a abrir el problema que estamos cerrando.

Este punto nos pareció el más importante de responder: la garantía contra el doble cobro no es solo del servidor, también depende de que ambos clientes manden la petición de la misma manera. Si el panel manda un identificador nuevo cada vez que se reintenta una petición fallida y la app reutiliza el mismo, uno de los dos va a fallar en silencio.

**Lo que sí puede (y debe) cambiar:**
- El panel, después de confirmar el pago, puede mostrar una pantalla con el recibo completo, el mapa y el detalle del envío: tiene espacio y una persona sentada esperando esa respuesta.
- La app, en cambio, no necesita todo eso de inmediato: le basta una confirmación corta (folio, estado, medio) para no bloquear al repartidor o al cliente con una pantalla pesada, y el detalle completo lo puede pedir después, cuando el usuario lo abra explícitamente.
- Cómo se reintenta también puede diferir en el nivel de la interfaz: el panel puede permitirle al operador reintentar el aviso a mano con un botón; la app, más adelante, podría hacerlo sola en segundo plano. Pero ambas cosas están reintentando el **mismo** aviso pendiente, guardado en un único lugar — no cada cliente llevando su propia cuenta de qué avisos faltan.

En resumen: el hecho de que el envío existe y está pagado es uno solo, y vive en el servidor; lo que cada cliente hace con ese hecho —cuánto detalle pinta, cuándo lo pide, cómo deja reintentar un aviso— es donde sí hay lugar para que panel y app sean distintos sin que eso signifique que están viendo cosas distintas.

