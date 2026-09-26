---
source_hash: 471a80651c9f
title: "El primer proyecto Spring Boot"
number: 16
part: p3
kicker: "Tres minutos entre un formulario en la web y una aplicación corriendo en el puerto 8080."
goal: >-
  Generar un proyecto en Spring Initializr, entender cada carpeta y cada
  línea del `pom.xml`, y levantar la aplicación por primera vez.
---

Basta de archivos sueltos. A partir de aquí el proyecto tiene estructura,
dependencias y un comando para correrlo. Y, por anticlimático que parezca,
el paso más importante de este capítulo es entender qué hace cada carpeta,
porque es en ellas donde van a vivir los próximos veintiséis capítulos.

## Generando el proyecto

Ve a `start.spring.io` y completa:

| Campo | Valor |
|---|---|
| Project | Maven |
| Language | Java |
| Spring Boot | 3.x (la versión estable más reciente) |
| Group | `com.tienda` |
| Artifact | `catalog` |
| Packaging | Jar |
| Java | 21 |

Tabla: Las elecciones del formulario. `Group` es tu dominio invertido;
`Artifact` es el nombre del proyecto.

En **Dependencies**, agrega dos por ahora:

- **Spring Web**: el servidor embebido y el soporte para REST;
- **Spring Boot DevTools**: reinicio automático al guardar.

Descarga el ZIP y descomprímelo. O, si prefieres la línea de comandos:

```bash title="El mismo proyecto, sin navegador"
curl https://start.spring.io/starter.zip \
  -d dependencies=web,devtools \
  -d groupId=com.tienda -d artifactId=catalog \
  -d javaVersion=21 -d type=maven-project \
  -o catalog.zip
```

:::trivia
Spring Initializr existe desde 2013 y es, en sí mismo, una aplicación Spring
Boot. El equipo la usa como vitrina y como prueba de fuego: cada nueva
versión del framework tiene que generar un proyecto que compile al primer
intento. Por eso la experiencia de "empezar" en Java es hoy mejor que en
muchos lenguajes más nuevos.
:::

## La estructura, carpeta por carpeta

:::tree title="Lo que vino en el ZIP"
catalog/
  pom.xml               # dependencias y build
  src/
    main/
      java/
        com/tienda/catalog/
          CatalogApplication.java   # el main
      resources/
        application.properties      # configuración
        static/                     # archivos servidos tal cual
        templates/                  # páginas HTML (no las vamos a usar)
    test/
      java/
        com/tienda/catalog/
          CatalogApplicationTests.java
  mvnw                  # Maven embebido (Linux/Mac)
  mvnw.cmd              # Maven embebido (Windows)
:::

Tres convenciones importantes en este árbol.

**`src/main/java` y `src/test/java`** están separados a propósito: el código
de prueba nunca va al paquete final. **`src/main/resources`** guarda todo lo
que no es código: configuración, SQL, imágenes. Y **el paquete del `main` es
la raíz del escaneo**: Spring busca anotaciones desde él hacia abajo, lo que
explica por qué una clase fuera de `com.tienda.catalog` simplemente no se
encuentra.

:::pitfall
Crear la clase en un paquete hermano (`com.tienda.web`, por ejemplo) y pasar
media hora sin entender por qué el endpoint responde `404` es un rito de
iniciación. No hay mensaje de error porque, para Spring, esa clase nunca
existió. Mantén todo por debajo del paquete de la clase principal.
:::

## La clase principal

```java title="CatalogApplication.java" numbered
package com.tienda.catalog;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class CatalogApplication {
    public static void main(String[] args) {
        SpringApplication.run(CatalogApplication.class, args);
    }
}
```

Aquel `public static void main(String[] args)` del capítulo 2 está de
vuelta, entero. La misma firma, por el mismo motivo: la JVM necesita un
punto de partida. La diferencia es la línea de adentro.

:::anatomy title="La anotación que hace tres cosas"
lang: java
code: |
  @SpringBootApplication
  public class CatalogApplication {
      public static void main(String[] args) {
          SpringApplication.run(
                  CatalogApplication.class, args);
      }
  }
notes:
  - { line: 1, text: "Equivale a tres anotaciones: `@Configuration`, `@EnableAutoConfiguration` y `@ComponentScan`." }
  - { line: 1, text: "El `@ComponentScan` es lo que define la raíz del escaneo: este paquete y los de abajo." }
  - { line: 4, text: "`run` crea el contenedor, arma los beans, levanta Tomcat y devuelve el contexto." }
  - { line: 5, text: "`args` llega hasta aquí: `--server.port=9090` en la línea de comandos funciona." }
:::

## `pom.xml`: las dependencias

```xml title="pom.xml (lo esencial)" numbered
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.3.0</version>
</parent>

<properties>
    <java.version>21</java.version>
</properties>

<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-test</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>
```

Dos ideas aquí valen más que la sintaxis.

El **`parent`** es un catálogo de versiones. Es lo que permite declarar la
dependencia sin `<version>`: Spring Boot ya sabe qué versión de cada
biblioteca funciona con cuál. Esa es la respuesta al infierno de
compatibilidad que dominó Java en la década de 2000.

Un **`starter`** es un paquete de dependencias relacionadas.
`spring-boot-starter-web` trae Spring MVC, Jackson (JSON), el Tomcat
embebido y la validación: diez bibliotecas en una línea.

:::pitfall
`<scope>test</scope>` significa "solo al compilar y correr pruebas". Sin él,
las bibliotecas de prueba irían al JAR de producción. Si alguna vez viste un
JAR de 300 MB, probablemente el motivo fue este.
:::

## Corriéndolo

```bash title="Tres formas, lo mismo"
./mvnw spring-boot:run          # Linux, Mac
mvnw.cmd spring-boot:run        # Windows

./mvnw package                  # genera el JAR
java -jar target/catalog-0.0.1-SNAPSHOT.jar
```

```text title="Salida (recortada)"
  .   ____          _            __ _ _
 /\\ / ___'_ __ _ _(_)_ __  __ _ \ \ \ \
( ( )\___ | '_ | '_| | '_ \/ _` | \ \ \ \
 \\/  ___)| |_)| | | | | || (_| |  ) ) ) )
  '  |____| .__|_| |_|_| |_\__, | / / / /

Tomcat initialized with port 8080 (http)
Started CatalogApplication in 1.284 seconds
```

`mvnw` es el **Maven Wrapper**: un script que descarga la versión correcta
de Maven en la primera ejecución. Existe para que el proyecto corra en
cualquier máquina sin instalación previa, incluida la del servidor de
integración continua, en el capítulo 40.

:::checkpoint
Si ves `Started CatalogApplication` y la aplicación no termina, está bien.
Ahora es un servidor: se queda esperando. `Ctrl+C` la termina.
:::

## `application.properties`

```properties title="src/main/resources/application.properties"
spring.application.name=catalog
server.port=8080

# log más conversador durante el desarrollo
logging.level.org.springframework.web=INFO
```

Este archivo crece a lo largo del libro: base de datos en el capítulo 19,
JWT en el 32, OpenAPI en el 38. La convención de nombres es previsible
—`server.port`, `spring.datasource.url`— y la documentación oficial enumera
todas las claves.

:::tip
Prefiere `application.properties` a la configuración en código. Un valor en
un archivo puede sobrescribirse con una variable de entorno sin recompilar
nada, y así es como el capítulo 42 va a pasar la contraseña de la base en
producción sin escribirla en ningún archivo.
:::

## Un endpoint de prueba, solo para demostrar que está vivo

```java title="HelloController.java" numbered
package com.tienda.catalog;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HelloController {

    @GetMapping("/hello")
    public String hello() {
        return "Java One en línea";
    }
}
```

:::http title="El primer diálogo del proyecto"
GET /hello
---
200 OK
Content-Type: text/plain

Java One en línea
:::

Cuatro líneas útiles y tienes un servidor HTTP funcionando. El capítulo 17
explica cada anotación: aquí la única cuestión era demostrar que la máquina
enciende.

:::summary
- Initializr genera un proyecto Maven con dependencias compatibles.
- `src/main/java` es código, `src/main/resources` es configuración,
  `src/test/java` no va a producción.
- Toda clase tiene que estar por debajo del paquete de la clase
  `@SpringBootApplication`.
- Un *starter* es un paquete de dependencias; el `parent` resuelve las
  versiones.
- `mvnw` evita tener que instalar Maven.
:::

:::checkpoint
Generas un proyecto, reconoces cada carpeta, sabes lo que declara el
`pom.xml`, levantas la aplicación y respondes una petición HTTP.
:::

:::milestone
El proyecto existe de verdad: `catalog`, en el puerto 8080, respondiendo
`GET /hello`. De aquí al capítulo 42 nada se crea desde cero: todo se
agrega a esta base.
:::

:::exercise level=1
Cambia el puerto a 9090 en el `application.properties`, reinicia y
confírmalo. Después haz lo mismo sin cambiar el archivo, usando la línea de
comandos.

:::answer
En el archivo: `server.port=9090`. En la línea de comandos:
`java -jar app.jar --server.port=9090`. La segunda forma le gana a la
primera: el orden de precedencia de configuración de Spring Boot tiene doce
niveles, y el argumento de línea de comandos está casi arriba de todo.
:::

:::exercise level=2
Crea un segundo endpoint `GET /version` que devuelva la versión del
proyecto. Lee el valor de `application.properties` con
`@Value("${app.version}")`.

:::answer
```java
@RestController
public class VersionController {
    private final String version;

    public VersionController(
            @Value("${app.version}") String version) {
        this.version = version;
    }

    @GetMapping("/version")
    public String version() {
        return version;
    }
}
```
Fíjate en que `@Value` entró por el **constructor**, no por el atributo: el
mismo principio del capítulo 15. Y si la clave no existe, la aplicación
falla al arrancar, que es donde quieres enterarte.
:::

:::exercise level=3
Mueve `HelloController` al paquete `com.tienda.web`, reinicia y observa el
`404`. Después arréglalo de dos formas distintas y explica cuál preferirías
en un proyecto real.

:::answer
Opción 1: volver a mover la clase dentro de `com.tienda.catalog`. Opción 2:
declarar `@SpringBootApplication(scanBasePackages = "com.tienda")`. La
primera es mejor: la convención de paquetes es lo que permite que cualquier
persona nueva en el proyecto sepa dónde están las cosas sin leer
configuración.
:::
