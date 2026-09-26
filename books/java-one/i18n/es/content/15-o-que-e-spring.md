---
source_hash: 3708bd1d8b58
title: "Qué es Spring"
number: 15
part: p3
kicker: "Dejas de crear objetos con new. A cambio, alguien los crea por ti, y hace falta entender quién."
epigraph: "Un framework es una biblioteca que llama a tu código, en vez de ser llamada por él."
epigraph_by: "Martin Fowler, sobre la inversión de control"
goal: >-
  Explicar la inversión de control y la inyección de dependencias con un
  ejemplo de código, y decir qué es un *bean* y qué es el contenedor.
---

Hasta el capítulo 14 creaste todos los objetos del programa. A partir de
aquí, los crea el framework. Esa inversión tiene nombre, tiene motivo y
tiene un precio, y este capítulo trata de los tres. Todavía no vamos a
instalar nada: primero la idea.

## El problema que resuelve Spring

Considera la estructura que armaste en el capítulo 11:

```java title="¿Quién arma estas piezas?" numbered
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }
}
```

Alguien tiene que escribir:

```java title="El armado manual" numbered
var dataSource = new PostgresDataSource(url, user, pass);
var repository = new JdbcProductRepository(dataSource);
var service = new ProductService(repository);
var controller = new ProductController(service);
```

Con cuatro clases es aceptable. Una API real tiene cuarenta: servicio de
e-mail, cliente HTTP, caché, transacción, autenticación, y cada uno depende
de otros tres. Ese armado se vuelve un archivo de trescientas líneas que
nadie quiere abrir, y que hay que rehacer en cada prueba.

:::key
Spring no hace nada que no pudieras hacer a mano. Hace el **armado** por ti,
siempre de la misma forma, y se ocupa del orden. Es un constructor de grafos
de objetos, no un poder mágico.
:::

:::story La palabra framework
Roberto volvió de un evento con una palabra nueva y una certeza.

—Necesitamos un framework.

—¿Para qué? —preguntó Marina.

—Para acelerar. El tipo del panel dijo que reduce un 70% el tiempo de
desarrollo.

—Reduce el tiempo de escribir la plomería. Todavía no escribimos ni la
plomería ni el resto.

Roberto anotó "70%" en el cuaderno y lo encerró en un círculo. Dos semanas
después, ese número apareció en una diapositiva, sin contexto, al lado del
plazo de entrega.

Marina hizo lo que hacía siempre: abrió el proyecto y le mostró a Carlos las
cuatro líneas de armado manual que existían en el `main`.

—Esto es lo que el framework va a hacer por nosotros. No es poco. Pero
tampoco es el 70% de nada.
:::

## Inversión de control

La expresión describe exactamente el intercambio:

:::compare left="Control en tu código" right="Control invertido"
class ProductService {
  private Repo repo =
      new JdbcRepo();
}
---
class ProductService {
  private final Repo repo;

  ProductService(Repo repo) {
    this.repo = repo;
  }
}
:::

A la izquierda, la clase decide qué implementación usar, y queda atada a
ella para siempre. A la derecha, la clase **declara lo que necesita** y lo
recibe de afuera. Quien decide pasa a ser quien arma.

Esa segunda forma tiene nombre propio: **inyección de dependencias por
constructor**. Es la única que usa este libro, y la recomendada oficialmente
por Spring, por tres razones: el objeto nace completo, el atributo puede ser
`final`, y la clase sigue siendo comprobable sin ningún framework.

## El contenedor y los *beans*

```java title="Lo que lee Spring" numbered
@Service
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }
}
```

Una anotación, y el acuerdo cambia. `@Service` le dice a Spring: *"esta
clase es mía, crea una instancia de ella y guárdala"*. Esa instancia
guardada es un **bean**, y el lugar donde vive es el **contenedor**
(formalmente, el *application context*).

:::diagram type="blocks" caption="El contenedor arma el grafo al arrancar, mirando las anotaciones y los constructores."
rows:
  - [{ text: "@SpringBootApplication", note: "recorre el paquete buscando anotaciones" }]
  - [{ text: "ApplicationContext", note: "el contenedor: crea, guarda y conecta los beans" }]
  - [{ text: "@Controller", note: "recibe HTTP" }, { text: "@Service", note: "reglas" }, { text: "@Repository", note: "base de datos" }]
:::

Al arrancar, Spring recorre el paquete, encuentra las clases anotadas, mira
los constructores, descubre en qué orden crear cada una y lo arma todo. Si
falta una pieza, falla **al arrancar**, no en la petición del cliente.

:::anatomy title="Cómo decide Spring qué inyectar"
lang: java
code: |
  @Service
  public class ProductService {
      private final ProductRepository repo;

      public ProductService(ProductRepository repo) {
          this.repo = repo;
      }
  }
notes:
  - { line: 1, text: "La anotación marca la clase como candidata a bean." }
  - { line: 3, text: "`final` garantiza que la dependencia no cambia después de armada." }
  - { line: 5, text: "Un único constructor: Spring ni siquiera necesita `@Autowired` desde la versión 4.3." }
  - { line: 5, text: "El **tipo** del parámetro es la clave de búsqueda: busca un bean que sirva como `ProductRepository`." }
:::

## Cuatro anotaciones que dicen lo mismo

| Anotación | Capa | Diferencia real |
|---|---|---|
| `@Component` | cualquiera | la forma genérica |
| `@Service` | reglas de negocio | ninguna técnica; comunica intención |
| `@Repository` | acceso a datos | traduce las excepciones de la base |
| `@Controller` | entrada HTTP | habilita el mapeo de rutas |

Tabla: Todas crean un bean. Elegir la correcta es documentación y, en dos
casos, también comportamiento.

:::pitfall
`@Autowired` en un atributo (*field injection*) todavía aparece en muchos
tutoriales:

```java
@Autowired
private ProductRepository repository;   // evítalo
```

Funciona y cobra caro: el atributo no puede ser `final`, la clase miente
sobre sus dependencias (el constructor no las declara) y la prueba unitaria
necesita reflexión para completar el campo. Usa el constructor. Siempre.
:::

## Alcance: cuántos objetos existen

Por defecto, un bean es **singleton**: existe **uno** para la aplicación
entera, y todas las peticiones usan el mismo objeto. Eso tiene una
consecuencia que asusta a quien la descubre tarde:

:::pitfall
Un bean singleton **no puede guardar estado de petición**. Si
`ProductService` tiene un atributo `private Product actual`, dos peticiones
simultáneas se van a sobrescribir una a la otra, y el cliente A va a recibir
el dato del cliente B. La regla es simple: **los atributos de un bean son
solo sus dependencias**. El dato de la petición vive en parámetros y
variables locales.
:::

## Qué agrega exactamente Spring Boot

Spring Framework resuelve el armado. Spring Boot resuelve la configuración:

- **servidor embebido**: Tomcat viene dentro del JAR; no hay servidor que
  instalar;
- **autoconfiguración**: ¿vio PostgreSQL en el classpath? configura la
  conexión; ¿vio Jackson? configura JSON;
- **`application.properties`**: un archivo, claves con nombres previsibles;
- **arranque único**: `java -jar app.jar` y está en línea.

:::history
En 2003, escribir la misma aplicación exigía un archivo `web.xml`, dos
descriptores `ejb-jar.xml`, un servidor de aplicaciones instalado aparte y
un ciclo de *build-deploy* de varios minutos. Spring Boot es de 2014 y la
propuesta era recortar todo eso: convención en vez de configuración. La
comunidad lo llamó "opinionated": el framework tiene opinión, y tú solo
discutes cuando lo necesitas.
:::

## Donde la magia cobra su precio

Vale la pena decir esto ahora, antes de que empiece el encantamiento:

- el error se vuelve largo. Una traza de excepción de Spring tiene sesenta
  líneas, y las tres que importan están en el medio;
- el orden de creación es implícito. Cuando dos clases dependen una de la
  otra, el error es `circular reference` y la solución es repensar el
  diseño;
- la anotación esconde comportamiento. `@Transactional` cambia lo que pasa
  alrededor del método sin aparecer en su cuerpo, y el capítulo 30 muestra
  lo que eso significa en la práctica.

Nada de esto es motivo para no usarlo. Es motivo para saber qué está
pasando, que es la diferencia entre usar el framework y ser usado por él.

:::term Bean
Un objeto cuyo ciclo de vida controla Spring: lo crea, le inyecta las
dependencias, lo guarda y lo destruye.
:::

:::term Contenedor (ApplicationContext)
El registro de todos los beans de la aplicación. Arma el grafo al arrancar y
le entrega la instancia a quien la pida por tipo.
:::

:::summary
- Inversión de control: la clase declara lo que necesita; otro decide qué
  entregar.
- La inyección por constructor es la única forma recomendada: atributo
  `final`, objeto completo, prueba sin framework.
- `@Service`, `@Repository`, `@Controller` y `@Component` crean beans.
- Un bean es singleton por defecto: no guardes estado de petición en él.
- Spring arma; Spring Boot configura.
:::

:::checkpoint
Explicas la inversión de control con un ejemplo, sabes por qué gana la
inyección por constructor, reconoces las cuatro anotaciones y sabes por qué
un bean no puede guardar estado de petición.
:::

:::milestone
Ninguna línea nueva de proyecto, pero la estructura del capítulo 11 acaba
de cobrar sentido: `ProductService` recibiendo `ProductRepository` es
exactamente la forma que Spring espera encontrar. El capítulo 16 instala el
framework.
:::

:::exercise level=1
Reescribe el armado manual de cuatro líneas de este capítulo explicando, en
una frase por línea, qué dependencia recibe cada objeto.

:::answer
El `DataSource` recibe la configuración de conexión; el repositorio recibe
el `DataSource`; el servicio recibe el repositorio; el controlador recibe el
servicio. Cada capa conoce **solo la de abajo**, y es esa cadena la que
Spring va a armar solo.
:::

:::exercise level=2
Escribe dos clases, `EmailSender` (interfaz), `SmtpEmailSender` y
`FakeEmailSender`, y un `OrderService` que reciba la interfaz en el
constructor. Arma las dos combinaciones a mano, sin framework.

:::answer
```java
var real = new OrderService(new SmtpEmailSender());
var prueba = new OrderService(new FakeEmailSender());
```
Dos líneas, dos configuraciones del mismo sistema. Acabas de hacer a mano
exactamente lo que hace el `@MockBean` del capítulo 36, y por eso la
inyección por constructor vuelve trivial la prueba.
:::

:::exercise level=3
Explica, sin usar la palabra "magia", qué pasa entre `java -jar app.jar` y
la primera petición atendida.

:::answer
La JVM carga la clase principal; Spring Boot crea el `ApplicationContext`;
el contenedor recorre los paquetes buscando anotaciones; para cada clase
encontrada, resuelve las dependencias del constructor (creándolas antes, si
hace falta) y guarda el bean; la autoconfiguración levanta el Tomcat
embebido y registra las rutas de los controladores; el puerto se abre. Nada
de eso es magia: es un grafo que se arma en orden topológico.
:::
