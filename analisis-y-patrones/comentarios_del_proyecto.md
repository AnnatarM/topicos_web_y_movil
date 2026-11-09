# Revisión del Proyecto

###  Versionado manual
En todas esas carpetas y archivos duplicados como config1, index1.php, kardex1.php.
Andar copiando archivos y poniéndoles un 1 o final al nombre es un peligro. Tarde o temprano alguien va a sobreescribir algo importante y nos va a generar problemas. La solución seria borrar toda esa duplicidad y apoyarnos en Git. 
Deberíamos implementar Git Flow o alguna estrategia de ramas bien definida para llevar el control de versiones sin ensuciar el código.

###  Archivos de conexión expuestos
Los archivos config/db_connect.php y config/db_connect_produccion.php.
Tener las credenciales  directo en el código y separadas por archivos es un riesgo de seguridad. Además, hace súper difícil escalar la app. Lo ideal es usar un archivo .env para manejar las variables de entorno. 

###  Modificaciones a la BD
Analizando el archivo bd/script_produccion_real_no_tocar.sql. Sabemos que correr scripts directo en producción es arriesgarse mucho. Necesitamos un historial real de cómo cambia nuestra base de datos para poder echar atrás un cambio si algo sale mal.
Hay que meter un sistema de migraciones. Así tratamos los cambios de la base de datos como si fueran código.

###  Un archivo hace todo
Tenemos toda la lógica amontonada en un solo lugar. Esto hace que hacer pruebas unitarias sea muy dificil y consume mucha memoria porque cargamos funciones que ni estamos usando. Nos toca mover esto hacia orientación a objetos, separando las cosas en clases más pequeñas y usando un autoloader.


### Lógica revuelta
En los archivos de la raíz como index.php, kardex.php, pagar.php, etc.
Tenemos el HTML revuelto con consultas SQL y validaciones, es un código espagueti. Si el día de mañana queremos cambiar el diseño, seguro rompemos algo de la lógica sin querer. 
Necesitamos aplicar MVC (Modelo-Vista-Controlador). Los controladores validan, los modelos hablan con la base de datos, y las vistas solo pintan el HTML.

###  Embudo en API
Usar un solo archivo para cachar todas las peticiones externas nos va a terminar dejando con un switch o if/else gigante y súper difícil de mantener. 
Nos hace falta un Front Controller que intercepte todo y un Router que se encargue de reedirigir la request.
