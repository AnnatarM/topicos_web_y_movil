# PasoFit (Flutter) — App de entrenamiento

## 0. La documentación del proyecto no corresponde al código

docs/ARQUITECTURA.md describe la app como el "token de firmas de un banco" (transferir, saldos, tokens) y afirma que "no hay 'rutinas'" — cuando el código completo es una app de ejercicio. También indica reglas de arquitectura razonables que el propio código ignora: dice que "flutter_bloc YA es el Observer" y que está "prohibido" usar listas de oyentes manuales en el widget, y que "el SQL vive en el repositorio, nunca en el State" — ambas reglas se incumplen (ver puntos 1 y 5 abajo).

Por qué es un problema: una documentación desincronizada del código genera confianza falsa en cualquiera que la lea, y en este caso además contradice sus propias reglas de arquitectura, lo que sugiere que nunca se validó contra el código real.

Solución a futuro: tratar la documentación como código (revisarla/actualizarla en el mismo PR que el código que describe) y validar automáticamente que la arquitectura descrita corresponda con la implementación real.

---

## 1. Problemas de arquitectura y seguridad encontrados

| # | Problema | Solución propuesta |
|---|---|---|
| 1 | El pubspec.yaml declara dependencias de flutter_bloc y provider, y existe estado/reloj_cubit.dart (un Cubit real), pero ninguna pantalla los usa. En su lugar se implementó a mano un "bus" de eventos con listas estáticas mutables (estado/oyentes.dart: RelojBus.ticks, PesoBus.kilos), justo el patrón que la propia documentación prohíbe explícitamente ("PROHIBIDO listas de oyentes en el widget"). | Elegir un solo manejador de estado (Bloc/Cubit *o* Provider, no ambos) y usarlo de verdad; eliminar el event-bus casero y el Cubit no usado (o integrarlo si se decide usarlo). |
| 2 | Los listeners agregados a RelojBus.ticks (en cronometro.dart) y PesoBus.kilos (en peso.dart) dentro de initState() nunca se remueven en dispose(): cada vez que se entra y sale de esas pantallas se acumula un listener más, lo que produce fuga de memoria y actualizaciones duplicadas/fantasma en pantallas ya cerradas. | Guardar la referencia del callback agregado y quitarla explícitamente en dispose(), o migrar a Cubit/Bloc, que ya maneja el ciclo de vida de sus suscriptores. |
| 3 | login.dart envía usuario y contraseña por http://127.0.0.1/fit/login (sin TLS, en texto plano), y decide si el login fue exitoso con una comparación ingenua (r.body.contains('ok') |\| r.body.contains('id')), además de hardcodear 'uid': '1' en la navegación sin importar qué id devolvió realmente el servidor. | Usar HTTPS, definir un contrato de respuesta tipado (JSON con status/id reales) y navegar usando el id que efectivamente regresó el backend. |
| 4 | En inicio.dart, el bloque que debería validar la sesión (cookie/admin_bypass) tiene un comentario que admite que no hace nada (// a veces entra igual): cualquiera puede llegar a esa pantalla sin haber iniciado sesión. | Implementar el control de acceso real: si no hay una sesión válida, redirigir a la pantalla de login en vez de continuar. |
| 5 | rutina.dart, peso.dart y logros.dart acceden a sqflite directamente desde el State del widget, con SQL armado por interpolación de strings (p. ej. "WHERE tipo='${r['tipo']}'" en logros.dart, "INSERT INTO sesiones (tipo, kcal, estatus) VALUES ('$tipo', $kcal, 'ok')" en rutina.dart): esto es justo lo que la documentación de arquitectura prohíbe ("el SQL vive en el repositorio, NUNCA en el State"), además de representar un riesgo de inyección SQL local. | Crear una capa de repositorio que centralice el acceso a sqflite con consultas parametrizadas (db.rawQuery(..., [valor])), y que los widgets solo la consuman. |
| 6 | inicio.dart hace, en cada carga de la pantalla, 8 llamadas HTTP síncronas y bloqueantes a http://127.0.0.1/fit/mod/0..7, cada una envuelta en un try/catch (_) {} que descarta cualquier error silenciosamente, y el resultado se muestra directamente sin validación. | Paralelizar las llamadas (Future.wait), agregar timeouts reales, y registrar (loggear) los errores en vez de ignorarlos. |
| 7 | El "quemado" de kilocalorías por tipo de rutina (if (tipo == 'cardio') kcal = 320;, etc.) está hardcodeado con números mágicos directamente dentro del widget RutinaPantalla. | Mover esa tabla de valores a una capa de dominio/configuración (o a la base de datos), separada de la UI. |
| 8 | rutina_old.dart define una pantalla (RutinaOld) que no está referenciada en ninguna ruta de main.dart: código muerto. | Eliminarla del proyecto; usar el historial de Git si se necesita recuperar versiones anteriores. |
| 9 | En rutina.dart, el cast (ModalRoute.of(context)!.settings.arguments as Map)['tipo'] no valida que arguments no sea nulo ni que tenga el formato esperado: si la pantalla se abre sin pasar argumentos (p. ej. por un deep link), la app se cae. | Validar los argumentos recibidos y mostrar un estado de error/valor por defecto en vez de forzar el cast. |
| 10 | No existe una sola prueba automatizada (unitaria o de widget) en todo el proyecto. | Agregar pruebas para los flujos críticos: login, registro de rutina y registro de peso. |

---

## Conclusión

PasoFit ignora sus propias reglas de arquitectura (usa exactamente el patrón de listeners manuales que su documentación prohíbe, y pone SQL directamente en los widgets cuando se supone que debe vivir en un repositorio), además de tener fugas de memoria por listeners nunca removidos, un login que confía en el cliente en vez del servidor, y llamadas de red bloqueantes sin manejo de errores. La prioridad de corrección sería: unificar el manejo de estado en Bloc/Cubit (eliminando el event-bus casero), crear una capa de repositorio real para el acceso a sqflite, corregir el flujo de login para que dependa de la respuesta real del servidor, y eliminar el código muerto (rutina_old.dart).