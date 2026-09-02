# Análisis Extendido: Paradigmas de Programación y Patrones de Diseño

## 1. Glosario de Paradigmas de Programación

| Paradigma | Definición | Idea central |
|-----------|-----------|---------------|
| **Orientado a Objetos (OO)** | Organiza el código en "objetos" que combinan datos (atributos) y comportamiento (métodos) | Encapsulamiento, herencia, polimorfismo, abstracción |
| **Funcional** | Trata la computación como evaluación de funciones matemáticas, evita estado mutable | Funciones puras, inmutabilidad, composición de funciones |
| **Procedural / Imperativo** | El programa es una secuencia de instrucciones que modifican el estado paso a paso | Uso de variables, bucles, condicionales, procedimientos |
| **Declarativo** | Se describe *qué* se quiere lograr, no *cómo* lograrlo | El motor/intérprete decide la ejecución (ej. SQL) |
| **Orientado a Eventos** | El flujo del programa se determina por eventos (clics, mensajes, señales) | Listeners, callbacks, manejadores de eventos |
| **Concurrente / Actor Model** | Diseñado para ejecutar múltiples procesos simultáneamente de forma segura | Procesos aislados que se comunican por mensajes (actores) |
| **Orientado a Protocolos** | Variante de OO donde el comportamiento se define mediante protocolos/interfaces en vez de herencia | Composición sobre herencia |
| **Multiparadigma** | El lenguaje permite combinar dos o más de los anteriores según la necesidad | Flexibilidad para elegir el mejor enfoque por problema |

---

## 2. Glosario de Patrones de Diseño (GoF y afines)

### Patrones Creacionales
| Patrón | Qué resuelve |
|--------|---------------|
| **Singleton** | Garantiza que una clase tenga una única instancia global y un punto de acceso a ella |
| **Factory Method** | Delega la creación de objetos a subclases, evitando el uso directo de `new` |
| **Builder** | Construye objetos complejos paso a paso, separando construcción de representación |
| **Prototype** | Crea nuevos objetos clonando una instancia existente en vez de crearla desde cero |

### Patrones Estructurales
| Patrón | Qué resuelve |
|--------|---------------|
| **Decorator** | Añade funcionalidades a un objeto dinámicamente sin alterar su clase original |
| **Facade** | Ofrece una interfaz simplificada para un subsistema complejo |
| **Adapter** | Permite que interfaces incompatibles trabajen juntas |
| **Composite** | Trata objetos individuales y composiciones de objetos de manera uniforme (estructuras de árbol) |

### Patrones de Comportamiento
| Patrón | Qué resuelve |
|--------|---------------|
| **Observer** | Notifica automáticamente a varios objetos cuando cambia el estado de otro (pub/sub) |
| **Strategy** | Permite intercambiar algoritmos en tiempo de ejecución sin modificar el objeto que los usa |
| **Template Method** | Define el esqueleto de un algoritmo, dejando pasos específicos a las subclases |
| **Visitor** | Permite añadir operaciones nuevas a una jerarquía de clases sin modificarlas |
| **Delegate** | Un objeto transfiere responsabilidad de una tarea a otro objeto auxiliar (muy usado en Swift) |

### Patrones Funcionales (no GoF, pero equivalentes conceptuales)
| Patrón | Qué resuelve |
|--------|---------------|
| **Monad** | Encadena operaciones que pueden fallar o tener efectos secundarios, manteniendo pureza funcional |
| **Functor** | Permite aplicar una función dentro de un contexto (ej. `Maybe`, `List`) sin "desempaquetarlo" manualmente |
| **Applicative** | Permite aplicar funciones que están también envueltas en un contexto (combinación de Functores) |
| **Pipeline / Functional Composition** | Encadena funciones donde la salida de una es la entrada de la siguiente (`%>%`, `|>`) |

### Patrones de Arquitectura / Sistema
| Patrón | Qué resuelve |
|--------|---------------|
| **MVC (Model-View-Controller)** | Separa datos, lógica de negocio y presentación |
| **MVVM (Model-View-ViewModel)** | Similar a MVC pero con enlace de datos bidireccional (usado en C#, Swift) |
| **Repository** | Abstrae el acceso a datos, separando la lógica de negocio de la persistencia |
| **Active Record** | El objeto de dominio contiene tanto los datos como la lógica de acceso a la base de datos |
| **Data Mapper** | Separa el objeto de dominio de la lógica de persistencia (a diferencia de Active Record) |
| **Dependency Injection (DI)** | Provee las dependencias de un objeto desde fuera en vez de crearlas internamente |
| **Actor Model / Supervisor Tree / GenServer** | Patrones de Erlang/Elixir para manejar concurrencia mediante procesos aislados supervisados |
| **Worker Pool** | Distribuye tareas entre un grupo fijo de procesos/hilos concurrentes (común en Go) |
| **Functional Options** | Patrón de Go para configurar structs de forma flexible usando funciones como parámetros |
| **RAII (Resource Acquisition Is Initialization)** | Ata la gestión de recursos (memoria, archivos) al ciclo de vida de un objeto (C++/Rust) |
| **Newtype** | Envuelve un tipo primitivo en un tipo nuevo para dar seguridad y semántica (Rust) |
| **Module / Revealing Module** | Encapsula código en un espacio de nombres, exponiendo solo lo necesario (JS) |
| **Metatable-based OO** | Simula orientación a objetos en Lua usando tablas y metatablas |

---

## 3. Tabla comparativa completa (referencia rápida)

| # | Lenguaje | Paradigma(s) | Patrones de diseño típicos |
|---|----------|--------------|------------------------------|
| 1 | **Python** | Multiparadigma (OO, funcional, imperativo) | Singleton, Factory, Decorator, Observer |
| 2 | **Java** | OO (con algo de funcional desde Java 8) | Singleton, Factory Method, Builder, Observer, Strategy, Decorator |
| 3 | **C++** | Multiparadigma (OO, procedural, genérico) | Factory, RAII, Singleton, Visitor, Template Method |
| 4 | **C#** | Multiparadigma (OO, funcional, eventos) | Singleton, Observer, Factory, MVVM, Repository |
| 5 | **JavaScript** | Multiparadigma (funcional, OO prototípico, eventos) | Module, Observer/PubSub, Factory, Singleton, Revealing Module |
| 6 | **TypeScript** | Multiparadigma (OO tipado, funcional) | Los de JS + Dependency Injection, Decorator nativo |
| 7 | **Ruby** | Multiparadigma (OO puro, funcional, metaprogramación) | Singleton, Observer, Decorator, DSL builder |
| 8 | **PHP** | Multiparadigma (OO, procedural) | Singleton, Factory, MVC, Active Record |
| 9 | **Go** | Concurrente, procedural, sin herencia clásica | Composition, Worker Pool, Functional Options, Strategy vía interfaces |
| 10 | **Rust** | Multiparadigma (funcional, procedural, sistemas) | Builder, Strategy (traits), RAII, Newtype |
| 11 | **Swift** | Multiparadigma (OO, funcional, protocolos) | Protocol-Oriented, Delegate, Singleton, Observer (Combine) |
| 12 | **Kotlin** | Multiparadigma (OO, funcional) | Singleton (`object`), Builder (DSL), Factory, Observer |
| 13 | **Haskell** | Funcional puro | Monad, Functor, Applicative |
| 14 | **Scala** | Multiparadigma (funcional + OO) | Monad, Factory, Builder, Cake Pattern (DI) |
| 15 | **SQL** | Declarativo | Active Record, Data Mapper (vía ORM) |
| 16 | **C** | Procedural puro | Handle/Opaque Pointer, State Machine manual |
| 17 | **Erlang / Elixir** | Funcional + concurrente (actores) | Actor Model, Supervisor Tree, GenServer |
| 18 | **Lua** | Multiparadigma (procedural, OO ligero) | Prototype, Module, Metatable-based OO |
| 19 | **Perl** | Multiparadigma (procedural, OO opcional) | Singleton, Factory (uso informal) |
| 20 | **R** | Funcional + orientado a datos | Pipeline / Functional composition |

---

## 4. Lenguajes que se alejan del diseño orientado a patrones clásicos (GoF)

| Lenguaje | Por qué no aplica GoF directamente | Qué usa en su lugar |
|----------|--------------------------------------|------------------------|
| **C** | No tiene clases ni objetos | Structs, punteros a función, máquinas de estado manuales |
| **SQL** | Es declarativo, no describe estructura de objetos | Patrones de acceso a datos (Active Record, Data Mapper) vía ORMs |
| **Haskell** | Es funcional puro, no tiene mutabilidad ni objetos | Monad, Functor, Applicative |
| **R** | Orientado a análisis estadístico y datos | Pipelines funcionales (`%>%`, `|>`) |
| **Perl / Lua** | Usados para scripting rápido, patrones formales suelen ser innecesarios | Soluciones ad-hoc, Module pattern (Lua) |

---

## 5. Notas finales

- El catálogo **GoF (Gang of Four)** fue creado en 1994 pensando en lenguajes **orientados a objetos** como C++ y Smalltalk, por eso lenguajes funcionales o declarativos tienen equivalentes distintos.
- En lenguajes **funcionales puros** (Haskell) o **multiparadigma con fuerte influencia funcional** (Scala, Elixir), los patrones se reemplazan por **abstracciones algebraicas** (Monad, Functor) que cumplen un rol similar pero desde otra lógica.
- En lenguajes de **scripting** (Perl, Lua, PHP en sus inicios) el uso de patrones formales es opcional y depende del tamaño del proyecto, no del lenguaje en sí.

---

# Tabla de Frameworks por Lenguaje: Paradigmas y Patrones que Refuerzan

## 6. Frameworks principales y su relación con paradigmas/patrones

| # | Lenguaje | Framework(s) principales | Patrón(es) de diseño que impone o favorece | Paradigma que refuerza |
|---|----------|---------------------------|----------------------------------------------|--------------------------|
| 1 | **Python** | Django, Flask, FastAPI | Django: MVC (MTV), Active Record (ORM) / Flask: Factory, Singleton (app context) / FastAPI: Dependency Injection | OO + funcional |
| 2 | **Java** | Spring, Spring Boot, Hibernate | Dependency Injection, Factory, Proxy, Repository, MVC | OO |
| 3 | **C++** | Qt, Boost, Unreal Engine | Observer (signals/slots en Qt), Factory, Template Method, Singleton | OO + genérico |
| 4 | **C#** | .NET / ASP.NET Core, Entity Framework | MVVM, Repository, Dependency Injection, MVC | OO + eventos |
| 5 | **JavaScript** | React, Vue, Express.js | React: Composition, Observer (hooks/estado) / Vue: MVVM / Express: Middleware pattern | Funcional + eventos |
| 6 | **TypeScript** | Angular, NestJS | Angular: Dependency Injection, MVVM / NestJS: Decorator, Module, DI | OO tipado + funcional |
| 7 | **Ruby** | Ruby on Rails | Active Record, MVC, Convention over Configuration | OO |
| 8 | **PHP** | Laravel, Symfony | Laravel: Active Record (Eloquent), Facade, Service Container (DI) / Symfony: MVC, DI | OO + procedural |
| 9 | **Go** | Gin, Echo, Fiber | Middleware pattern, Functional Options, Interface-based DI | Concurrente + procedural |
| 10 | **Rust** | Actix-web, Rocket, Tokio | Builder, Strategy (traits), Async/Await pattern | Funcional + sistemas |
| 11 | **Swift** | SwiftUI, UIKit, Vapor | SwiftUI: Declarative UI, Observer (Combine) / UIKit: Delegate, MVC | OO + protocolos |
| 12 | **Kotlin** | Ktor, Jetpack Compose | Ktor: DSL Builder, DI / Compose: Declarative UI, Observer (State) | OO + funcional |
| 13 | **Haskell** | Yesod, Servant | Monad Transformer, Type-level DSL | Funcional puro |
| 14 | **Scala** | Play Framework, Akka | Akka: Actor Model / Play: MVC, DI (Guice) | Funcional + OO |
| 15 | **SQL** | (no aplica framework tradicional; motores: PostgreSQL, MySQL) | Query Builder (via ORMs externos) | Declarativo |
| 16 | **C** | GTK, libuv | Callback pattern, Event Loop, Opaque Pointer | Procedural |
| 17 | **Erlang / Elixir** | Phoenix (Elixir), OTP (Erlang) | Supervisor Tree, GenServer, MVC (Phoenix) | Funcional + concurrente |
| 18 | **Lua** | Love2D, OpenResty | Module pattern, Event-driven callbacks | Procedural + OO ligero |
| 19 | **Perl** | Mojolicious, Catalyst | MVC, Factory (uso informal) | Procedural + OO opcional |
| 20 | **R** | Shiny, tidyverse | Shiny: Reactive Programming (Observer) / tidyverse: Pipeline/Functional composition | Funcional + datos |

---

## 7. Glosario de conceptos nuevos en esta tabla

| Concepto | Definición |
|-----------|-----------|
| **Middleware pattern** | Cadena de funciones que procesan una petición/respuesta de forma secuencial antes de llegar al destino final (común en frameworks web como Express, Gin) |
| **Convention over Configuration** | Filosofía de diseño donde el framework asume configuraciones por defecto sensatas, reduciendo la necesidad de configurarlo todo explícitamente (Rails) |
| **Service Container** | Contenedor que gestiona la creación y resolución de dependencias de una aplicación (usado