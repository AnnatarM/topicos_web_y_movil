# ¿Qué lenguaje usaría?

## Caso 1: mensajería tipo WhatsApp con LoRa

Usaría **React Native con TypeScript**. Desarrollar una app nativa para Android y otra para iOS sería duplicar el trabajo; con React Native mantengo una sola base de código para ambas plataformas. TypeScript me ayuda a detectar errores antes de ejecutar: si construyo mal el payload de un mensaje, el compilador lo marca y no me entero hasta que la app falla en el teléfono.

Para la arquitectura aplicaría el **patrón Observer** en los eventos que llegan del hardware. La app no tiene que estar preguntando constantemente si hay mensajes nuevos; el servicio que escucha el módulo LoRa avisa a la interfaz en el momento en que recibe un mensaje.

## Caso 2: detección de lugares libres en un estacionamiento con cámara

El backend lo haría en **Python** con **OpenCV** y un modelo ligero de detección de objetos como **YOLO**. El sistema procesa los cuadros del video en tiempo real, el modelo identifica los autos y se compara contra el mapa de cajones para saber cuáles están libres y actualizar su estado. Esa información se expone con un endpoint en **FastAPI** para que la aplicación la consulte.
