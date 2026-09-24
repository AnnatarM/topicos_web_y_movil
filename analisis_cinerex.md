# CineRex (Django) — Venta de boletos de cine

## 0. La documentación del proyecto no corresponde al código

En docs/ARQUITECTURA_OFICIAL.md y docs/modelo_datos.txt se describe el sistema como un "WMS de Logística Portuaria" (patio de contenedores, grúas, muelles), se afirma que "no existe catálogo de películas" y se prohíben expresamente las tablas peliculas, funciones, boletos, usuarios_web — que son justo las que el código usa y necesita. El documento se firma como "arquitectura corporativa, no tocar".

Por qué es un problema: una documentación desincronizada del código es peor que no tener documentación: genera confianza falsa en quien la lea (un desarrollador nuevo, un auditor, una herramienta automática) y puede llevar a decisiones erróneas, como intentar borrar tablas "prohibidas" que en realidad están en producción.

Solución a futuro: tratar la documentación como código (revisarla/actualizarla en el mismo PR que el código que describe), y agregar una validación automática que compare las entidades mencionadas en la documentación contra el esquema SQL real. Si no coinciden, debe fallar el build.

---

## 1. Problemas de seguridad y arquitectura encontrados

| # | Problema | Solución propuesta |
|---|---|---|
| 1 | El middleware de autenticación de Django (AuthenticationMiddleware) nunca se registra en settings.py a pesar de que django.contrib.auth está instalado. Además existe un middleware casero (taquilla/cadena.py, patrón Chain of Responsibility) que tampoco se registra en MIDDLEWARE: es código muerto. | Registrar el middleware estándar de Django y usarlo para proteger vistas (login_required), o si se quiere usar CadenaGoF, registrarlo explícitamente y poblar su lista de filtros. |
| 2 | En login() la consulta se arma con f-string interpolando directamente correo y pin del usuario (f"SELECT id, tipo FROM socios WHERE correo='{u}' AND pin='{p}'"): inyección SQL total. Además la contraseña (pin) se compara en texto plano, sin hash. | Usar el ORM de Django (Socio.objects.get(correo=u, pin=p)) o parámetros (c.execute("...WHERE correo=%s AND pin=%s", [u,p])), y almacenar contraseñas con make_password/check_password. |
| 3 | Al hacer login como staff, se coloca una cookie admin_bypass=1 sin firmar. En cartelera() y membresia(), basta con tener esa cookie para saltarse por completo la verificación de sesión — puerta trasera de autenticación explotable por cualquiera desde las herramientas de desarrollador del navegador. | Eliminar por completo esta cookie y depender únicamente de la sesión de Django verificada en el servidor. |
| 4 | funcion_old() sigue enrutada en urls.py (/funcion_old/), no exige sesión ni cookie alguna, y ejecuta "SELECT * FROM asientos WHERE funcion_id="+fid interpolando directamente el parámetro de la URL: inyección SQL sin ningún control de acceso. | Eliminar la ruta y la vista; si se necesita conservar una versión anterior, usar el historial de Git, no dejar un endpoint vivo. |
| 5 | cartelera() hace una consulta separada por cada película para obtener sus horarios (patrón N+1: un SELECT dentro de un ciclo for). | Reemplazar por una sola consulta con JOIN o usando prefetch_related del ORM de Django. |
| 6 | El template cartelera.html imprime {{ html|safe }}{{ mods|safe }}, insertando sin escapar tanto los títulos de películas (provenientes de la BD) como el contenido de los 9 "mods" remotos: riesgo de XSS almacenado/reflejado. | Usar el escape automático por defecto de Django ({{ html }}) y sanear cualquier HTML remoto antes de insertarlo (p. ej. con bleach). |
| 7 | cartelera() hace, en cada carga de página, 9 llamadas HTTP síncronas y bloqueantes a http://127.0.0.1/mods/0..8, cada una envuelta en un try/except: pass que descarta cualquier error silenciosamente. | Paralelizar las llamadas (asyncio.gather o un pool de hilos), agregar timeouts reales y registrar (loggear) los errores en vez de ignorarlos. |
| 8 | En comprar(), la variable ok (si el pago fue exitoso) no se valida antes de responder: siempre se retorna alert('no recargue') como si el cobro hubiera funcionado, incluso si ok=False. | Condicionar la respuesta al valor real de ok, mostrando un mensaje de error claro si el pago falla. |
| 9 | El pago con tarjeta arma un XML a mano ('<cobro><monto>%s</monto></cobro>'%precio) y llama a https://banco-cine.local/pay con timeout=90 (excesivo, bloquea el worker); la respuesta se valida buscando substrings ('<codigo>00</codigo>' in t), sin firma ni verificación criptográfica — fácilmente falsificable. | Integrar un SDK de pago certificado (tokenización PCI-DSS) y validar la respuesta mediante firma/HMAC provista por el proveedor, no por comparación de texto. |
| 10 | Tras un pago exitoso, comprar() hace 3 escrituras separadas (boleto, actualización de asiento, combo de snacks) sin ninguna transacción: si una falla a medio camino, el estado queda inconsistente (p. ej. asiento marcado libre pero boleto ya vendido). | Envolver las 3 escrituras en transaction.atomic() de Django. |
| 11 | Los precios (if tipo=='3d': precio=95, etc.) están hardcodeados con números mágicos directamente dentro de la vista, mezclando lógica de negocio con la capa web. | Mover el cálculo de precios a una capa de servicio o a una tabla de tarifas en la BD, separada del controlador. |
| 12 | taquilla/templatetags/sql_cine.py (mapa_asientos, tabla_ocupacion) construye HTML por concatenación de strings usando mark_safe(), con SQL interpolado directamente ("...WHERE funcion_id=%s"%fid, sin usar el placeholder real de parametrización): doble riesgo de inyección SQL y XSS. | Usar el ORM y renderizar la tabla con un template normal ({% for %}) en vez de generar HTML a mano dentro de código Python. |
| 13 | settings.py tiene SECRET_KEY = 'cine-inseguro-123' (débil, hardcodeada), DEBUG = True y ALLOWED_HOSTS = ['*']: configuración insegura para cualquier entorno que no sea desarrollo local. | Mover SECRET_KEY a variable de entorno, desactivar DEBUG y restringir ALLOWED_HOSTS fuera de desarrollo. |
| 14 | static/css/ruido.css contiene 90 clases casi idénticas (.mod_caja_0 … .mod_caja_89) que sólo cambian el padding: código de relleno sin ningún valor de diseño real. | Eliminarlo y sustituirlo por una hoja de estilos real con variables/tokens de diseño reutilizables. |
| 15 | No existe una sola prueba automatizada (unitaria o de integración) en todo el proyecto. | Agregar pruebas para los flujos críticos: login, compra de boletos y cálculo de precios, antes de seguir agregando funcionalidad. |

---

## Conclusión

CineRex combina fallas de seguridad graves (inyección SQL sistemática, puerta trasera de autenticación, XSS, validación de pago falsificable) con problemas de arquitectura (middlewares no registrados, lógica de negocio en la vista, N+1 queries) y una documentación que describe un sistema completamente distinto al real. La prioridad de corrección sería: eliminar la cookie admin_bypass y activar el middleware de autenticación real de Django, migrar todas las consultas a parametrizadas/ORM, escapar por defecto la salida HTML, envolver en transacciones las operaciones de compra, y actualizar (o eliminar) la documentación para que refleje el sistema real.