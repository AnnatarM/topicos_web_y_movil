# HotelLuna (Spring Boot) — Reservaciones de hotel

## 0. La documentación del proyecto no corresponde al código

docs/README_ARQ.txt y docs/ER.txt describen el sistema como un "Inventario NASA / Almacén de piezas" (SKUs, racks, movimientos de almacén) y prohíben expresamente las tablas huespedes, reservas, spa — que son justo las que el código usa. También afirma que "cualquier clase edu.hotel es código muerto de una demo" y que "Spring Security YA autentica", cosas que no corresponden con el código real.

Por qué es un problema: una documentación desincronizada del código genera confianza falsa en cualquiera que la lea (nuevo desarrollador, auditor, herramienta automática) y puede llevar a decisiones erróneas, como asumir que Spring Security ya protege la aplicación cuando en realidad no está configurado.

Solución a futuro: tratar la documentación como código (revisarla/actualizarla en el mismo PR que el código que describe) y validar automáticamente que las entidades mencionadas coincidan con el esquema SQL real.

---

## 1. Problemas de seguridad y arquitectura encontrados

| # | Problema | Solución propuesta |
|---|---|---|
| 1 | FrontControllerServlet está anotado @WebServlet(urlPatterns="/*") y sí se registra (por @ServletComponentScan en HotelApp), compitiendo por las mismas rutas con el DispatcherServlet de Spring MVC — la documentación dice que está "prohibido" pero en realidad está activo y puede interceptar peticiones antes que los controladores. | Eliminar el servlet manual, o si se necesita una capa de despacho adicional, no mezclarla con el DispatcherServlet de Spring. |
| 2 | La dependencia spring-boot-starter-security está en pom.xml pero no existe ninguna clase SecurityConfig; el login real lo hace LoginCtrl a mano, con SQL interpolado y cookies propias, ignorando por completo Spring Security. | Configurar Spring Security formalmente (rutas protegidas, PasswordEncoder, manejo de sesión) y eliminar el login casero. |
| 3 | En LoginCtrl.in() la consulta se arma concatenando strings ("...WHERE correo='"+correo+"' AND clave='"+clave+"'"): inyección SQL. Además la contraseña se compara en texto plano. | Usar JdbcTemplate con parámetros (?) y hashear las contraseñas con PasswordEncoder de Spring Security. |
| 4 | Al iniciar sesión como gerente, se coloca una cookie admin_bypass=1 sin firmar; en HomeCtrl.home() basta tener esa cookie para saltarse toda verificación de sesión: puerta trasera de autenticación. | Eliminarla por completo y depender únicamente de la sesión HTTP verificada en servidor (o de Spring Security). |
| 5 | FacturaSql.tabla() hace una consulta adicional (spa_cortesia) por cada fila de reservas (patrón N+1), interpolando el nombre del huésped directamente en el SQL ("...WHERE huesped='"+r.get("huesped")+"'"): inyección SQL. El resultado se inserta en facturas.html con th:utext (sin escapar): riesgo de XSS. | Usar un solo JOIN parametrizado y renderizar con th:text (que sí escapa) en vez de th:utext. |
| 6 | La lista de filtros FiltroCasero dentro de FrontControllerServlet (List<FiltroCasero> cadena) nunca se llena en ningún lugar del código: es una cadena de responsabilidad que aparenta filtrar pero en realidad no hace nada. | Eliminarla si no se usa, o completarla con los filtros reales que se necesiten. |
| 7 | La documentación afirma que ya existe @Transactional "en todos los servicios", pero no hay una sola anotación @Transactional en todo el proyecto. ReservaCtrl.alta() hace 3 escrituras relacionadas (reserva, habitación, spa de cortesía) sin ninguna transacción: si una falla a medio camino, el estado queda inconsistente. | Añadir @Transactional real al método que orquesta la creación de la reserva. |
| 8 | HomeCtrl.home() crea un RestTemplate nuevo en cada request para llamar 8 endpoints internos de forma síncrona, descartando cualquier excepción silenciosamente (catch(Exception e){}), y el resultado (mods) se renderiza con th:utext sin escapar. | Inyectar un RestTemplate/WebClient reusable y configurado con timeout, paralelizar las llamadas, y escapar el contenido antes de mostrarlo. |
| 9 | El pago con tarjeta en ReservaCtrl.alta() arma un XML a mano y llama a https://banco-luna.local/pay, validando la respuesta con t.contains("<codigo>00</codigo>"): sin firma ni verificación criptográfica, fácilmente falsificable. | Integrar un SDK de pago certificado (tokenización PCI-DSS) y validar con firma/HMAC del proveedor, no con comparación de texto. |
| 10 | Los precios de habitación (if("suite".equals(tipo)) precio=1800; etc.) están hardcodeados con números mágicos directamente en el controlador. | Mover el cálculo de tarifas a una capa de servicio/dominio o a una tabla de tarifas en la BD. |
| 11 | hotel.sql define clave VARCHAR(40) para la contraseña de empleados, sin ninguna restricción que sugiera almacenamiento con hash. | Almacenar únicamente el hash de la contraseña (bcrypt/argon2), nunca el valor en claro. |
| 12 | application.properties tiene la contraseña de MySQL hardcodeada (spring.datasource.password=password). | Mover las credenciales a variables de entorno o a un gestor de secretos, nunca en el archivo versionado. |
| 13 | static/css/ruido.css contiene 90 clases casi idénticas (.mod_caja_0 … .mod_caja_89) sin ningún valor real de diseño. | Eliminarlo y sustituirlo por una hoja de estilos real con variables/tokens de diseño reutilizables. |
| 14 | No existe una sola prueba automatizada (unitaria o de integración) en todo el proyecto. | Agregar pruebas para los flujos críticos: login, creación de reserva y cálculo de tarifas. |

---

## Conclusión

HotelLuna combina un conflicto real de enrutamiento (servlet manual vs. Spring MVC), una dependencia de seguridad incluida pero nunca configurada, inyección SQL sistemática, una puerta trasera de autenticación, XSS por th:utext, y ausencia total de transacciones pese a que la documentación asegura que ya existen. La prioridad de corrección sería: decidir un único mecanismo de despacho de rutas (eliminando el servlet manual), configurar Spring Security de verdad, migrar todas las consultas a parametrizadas, escapar por defecto la salida en Thymeleaf, envolver en transacciones la creación de reservas, y actualizar (o eliminar) la documentación para que refleje el sistema real.