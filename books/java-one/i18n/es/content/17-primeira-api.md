---
source_hash: 7d5a0eaa2014
title: "La primera API"
number: 17
part: p3
kicker: "Cuatro verbos, una ruta y una decisión sobre qué devolver en cada caso."
goal: >-
  Escribir endpoints para los cinco verbos del CRUD, recibir datos por la
  ruta, por la query y por el cuerpo, y elegir el código de estado correcto.
---

Este es el capítulo en que el proyecto pasa a ser una API. Los datos todavía
viven en un `Map` en memoria —la base de datos llega en el capítulo 19—,
pero el contrato HTTP que nace aquí es el mismo que sale en línea en el
capítulo 42.

## HTTP en una página

Toda petición tiene cuatro partes, y vas a tocar las cuatro:

:::anatomy title="Las partes de una petición HTTP"
lang: http
code: |
  POST /products?notify=true HTTP/1.1
  Content-Type: application/json
  Authorization: Bearer eyJhbGci...

  {"nombre": "Teclado", "precio": 349.90}
notes:
  - { line: 1, text: "**Verbo**: la intención. `POST` crea, `GET` lee, `PUT` reemplaza, `DELETE` borra." }
  - { line: 1, text: "**Ruta**: el recurso. Sustantivo en plural, sin verbo adentro." }
  - { line: 1, text: "**Query**: parámetros opcionales, después del `?`." }
  - { line: 2, text: "**Encabezados**: metadatos: tipo de contenido, autenticación, idioma." }
  - { line: 5, text: "**Cuerpo**: los datos. Solo en `POST`, `PUT` y `PATCH`." }
:::

Y toda respuesta tiene un número de tres dígitos que lo resume todo:

| Rango | Significado | Vas a usar |
|---|---|---|
| `2xx` | salió bien | `200`, `201`, `204` |
| `4xx` | el cliente se equivocó | `400`, `401`, `403`, `404`, `409` |
| `5xx` | el servidor se equivocó | `500` (y vas a querer evitarlo) |

Tabla: El primer dígito cuenta la historia. Si devuelves `200` con un
mensaje de error adentro, le estás mintiendo al cliente.

## El controlador

```java title="ProductController.java" numbered
package com.tienda.catalog.product;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

@RestController
@RequestMapping("/products")
public class ProductController {

    private final Map<Long, Product> base = new LinkedHashMap<>();
    private final AtomicLong secuencia = new AtomicLong();

    @GetMapping
    public List<Product> listar() {
        return new ArrayList<>(base.values());
    }
}
```

:::anatomy title="Las anotaciones que convierten un método en endpoint"
lang: java
code: |
  @RestController
  @RequestMapping("/products")
  public class ProductController {

      @GetMapping
      public List<Product> listar() {
          return new ArrayList<>(base.values());
      }
  }
notes:
  - { line: 1, text: "`@RestController` = `@Controller` + `@ResponseBody`: el retorno se vuelve el cuerpo de la respuesta." }
  - { line: 2, text: "`@RequestMapping` define el prefijo de la ruta para todos los métodos de la clase." }
  - { line: 5, text: "`@GetMapping` sin argumento hereda la ruta de la clase: `GET /products`." }
  - { line: 6, text: "Jackson convierte el retorno en JSON, sin una línea de conversión tuya." }
:::

:::trivia
Esa conversión automática a JSON la hace Jackson, una biblioteca que no
forma parte de Spring. Entra por la puerta de `spring-boot-starter-web` y
la elige la autoconfiguración: si está en el classpath, Spring la usa. Es la
filosofía de Boot en acción: la decisión ya se tomó, y solo discutes si
quieres.
:::

## Leer datos: tres orígenes, tres anotaciones

```java title="De dónde viene cada dato" numbered
// 1. de la ruta:  GET /products/7
@GetMapping("/{id}")
public Product buscar(@PathVariable Long id) {
    return base.get(id);
}

// 2. de la query:  GET /products/search?nombre=teclado
@GetMapping("/search")
public List<Product> buscarPorNombre(@RequestParam String nombre) {
    return base.values().stream()
            .filter(p -> p.getNombre().contains(nombre))
            .toList();
}

// 3. del cuerpo:  POST /products
@PostMapping
public Product crear(@RequestBody Product nuevo) {
    nuevo.setId(secuencia.incrementAndGet());
    base.put(nuevo.getId(), nuevo);
    return nuevo;
}
```

| Anotación | Lee de | ¿Obligatorio? |
|---|---|---|
| `@PathVariable` | un pedazo de la ruta | sí, es parte de la ruta |
| `@RequestParam` | la query string | opcional con `required = false` |
| `@RequestBody` | el cuerpo | sí, y necesita `Content-Type` |

Tabla: Las tres puertas de entrada de datos en un controlador.

## El CRUD completo

```java title="ProductController.java (el resto)" numbered
@PutMapping("/{id}")
public ResponseEntity<Product> actualizar(
        @PathVariable Long id,
        @RequestBody Product datos) {

    Product actual = base.get(id);
    if (actual == null) {
        return ResponseEntity.notFound().build();
    }
    datos.setId(id);
    base.put(id, datos);
    return ResponseEntity.ok(datos);
}

@DeleteMapping("/{id}")
public ResponseEntity<Void> borrar(@PathVariable Long id) {
    if (base.remove(id) == null) {
        return ResponseEntity.notFound().build();
    }
    return ResponseEntity.noContent().build();
}
```

`ResponseEntity` es el objeto que lleva **estado, encabezados y cuerpo**.
Úsalo siempre que la respuesta pueda variar, y en una API real casi siempre
puede.

## Los cinco diálogos, en orden

:::http title="Crear: devuelve 201 y el recurso creado"
POST /products
Content-Type: application/json

{
  "nombre": "Teclado mecánico",
  "precio": 349.90,
  "stock": 12
}
---
201 Created
Location: /products/1

{
  "id": 1,
  "nombre": "Teclado mecánico",
  "precio": 349.90,
  "stock": 12
}
:::

:::http title="Buscar uno: 200 cuando existe"
GET /products/1
---
200 OK
Content-Type: application/json

{ "id": 1, "nombre": "Teclado mecánico", "precio": 349.90 }
:::

:::http title="Buscar uno que no existe: 404, sin cuerpo"
GET /products/999
---
404 Not Found
:::

:::http title="Borrar: 204, también sin cuerpo"
DELETE /products/1
---
204 No Content
:::

:::key
`201` al crear, con el encabezado `Location` apuntando al recurso nuevo.
`204` al borrar, porque no hay nada que devolver. `404` cuando el id no
existe. Esos tres detalles separan una API que respeta el protocolo de una
que solo devuelve `200` para todo.
:::

```java title="Devolviendo 201 correctamente" numbered
@PostMapping
public ResponseEntity<Product> crear(@RequestBody Product nuevo) {
    nuevo.setId(secuencia.incrementAndGet());
    base.put(nuevo.getId(), nuevo);

    URI ubicacion = URI.create("/products/" + nuevo.getId());
    return ResponseEntity.created(ubicacion).body(nuevo);
}
```

## Probando desde la línea de comandos

```bash title="curl: el cliente HTTP que ya está instalado"
curl localhost:8080/products

curl -X POST localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Mouse","precio":89.90,"stock":5}'

curl -i localhost:8080/products/999
```

El `-i` muestra los encabezados y el estado, y es lo que vas a usar para
verificar si el `404` realmente es un `404`. El capítulo 39 presenta
herramientas con interfaz; por ahora, `curl` basta y enseña más.

:::pitfall
Olvidar el `-H "Content-Type: application/json"` en el `POST` devuelve
`415 Unsupported Media Type`. El mensaje es oscuro y la causa es simple: sin
el encabezado, Spring no sabe qué conversor usar para leer el cuerpo.
:::

:::story ¿Se lo podemos mostrar al cliente?
El `GET /products` respondió con una lista vacía —`[]`— y Carlos se quedó
diez segundos mirando esos dos caracteres con una emoción desproporcionada.

Registró un producto con `curl`. Lo corrió de nuevo. La lista tenía un
ítem.

Roberto, que había desarrollado un sexto sentido para aparecer exactamente
en esos momentos, apareció.

—¿Funcionó?

—Funcionó.

—¿Entonces se lo podemos mostrar al cliente el jueves?

Marina, sin levantar los ojos del monitor:

—Se lo podemos mostrar al cliente el jueves si el cliente acepta que los
datos desaparecen cuando alguien reinicia la aplicación.

—¿Y cuándo reinicia alguien la aplicación?

—Cada vez que hacemos deploy.

Roberto se quedó en silencio tres segundos —otra vez, una eternidad— y dijo
que lo iba a reprogramar para la semana siguiente.
:::

## Qué está mal en esta versión

Este controlador funciona y tiene cuatro defectos graves, todos a
propósito:

1. **guarda los datos en memoria**: reiniciar lo borra todo (capítulos 19 a
   21);
2. **el controlador contiene las reglas**: filtrar y numerar no es su
   trabajo (capítulo 22);
3. **expone la entidad directamente**: el cliente ve el diseño interno de
   la base (capítulo 24);
4. **no valida nada**: `precio: -5` entra (capítulo 25).

Reconocer los cuatro ahora es lo que va a hacer que los próximos capítulos
parezcan inevitables, y no burocráticos.

:::summary
- `@RestController` + `@RequestMapping` definen la clase; `@GetMapping` y
  su familia definen cada ruta.
- `@PathVariable`, `@RequestParam` y `@RequestBody` son las tres puertas de
  entrada.
- `ResponseEntity` controla estado, encabezado y cuerpo.
- `201` + `Location` al crear, `204` al borrar, `404` cuando no existe.
:::

:::checkpoint
Escribes los cinco endpoints del CRUD, lees datos de los tres orígenes,
eliges el estado correcto y lo pruebas todo con `curl`.
:::

:::milestone
La API responde a los cinco verbos en `/products`. Los datos mueren cuando
el proceso termina y el controlador hace cosas que no le corresponden: los
dos problemas que resuelve la Parte 4.
:::

:::exercise level=1
Agrega `GET /products/count` que devuelva la cantidad de productos
registrados. Después responde: ¿por qué no debería ser un endpoint separado
en una API bien diseñada?

:::answer
```java
@GetMapping("/count")
public long contar() {
    return base.size();
}
```
Porque el conteo es **metadato de una lista**, no un recurso. La forma REST
correcta es devolver el total en un encabezado o dentro de la respuesta
paginada, que es exactamente lo que hace el capítulo 27 con `Page`.
:::

:::exercise level=2
Haz que el `POST` rechace un producto sin nombre, devolviendo
`400 Bad Request`. Después compara tu código con la anotación `@NotBlank`
del capítulo 25.

:::answer
```java
if (nuevo.getNombre() == null || nuevo.getNombre().isBlank()) {
    return ResponseEntity.badRequest().build();
}
```
Funciona y no escala: con diez campos tendrías diez `if` en cada endpoint.
El capítulo 25 cambia todo eso por una anotación en el campo y un `@Valid`
en la firma.
:::

:::exercise level=3
Implementa `PATCH /products/{id}` que cambie **solo** los campos enviados.
Piensa cómo distinguir "campo ausente" de "campo enviado como nulo".

:::answer
La distinción exige un tipo que conozca la diferencia, normalmente un DTO
con campos `Optional` o un `Map<String, Object>`. Por eso muchas API
maduras simplemente no ofrecen `PATCH`: la semántica de la actualización
parcial es más difícil de acertar de lo que parece, y un `PUT` bien
documentado resuelve el 95% de los casos.
:::
