---
source_hash: 7b18bda34f43
title: "Controller"
number: 23
part: p4
kicker: "La capa más delgada del sistema, y la única que ve el cliente."
goal: >-
  Escribir el CRUD completo con las tres capas, devolver el estado correcto
  en cada caso y probar la API entera desde la línea de comandos.
---

Con el servicio listo, el controlador se vuelve lo que siempre debió ser: un
traductor. Recibe HTTP, llama a un método, devuelve HTTP. Este capítulo
cierra el CRUD y es el primer punto del libro en que la API está completa de
punta a punta.

## El CRUD entero

```java title="ProductController.java" numbered
package com.tienda.catalog.product;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;

@RestController
@RequestMapping("/products")
public class ProductController {

    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @GetMapping
    public List<Product> listar() {
        return service.listar();
    }

    @GetMapping("/{id}")
    public Product buscar(@PathVariable Long id) {
        return service.buscar(id);
    }

    @PostMapping
    public ResponseEntity<Product> crear(@RequestBody Product nuevo) {
        Product guardado = service.crear(nuevo);
        URI ubicacion = URI.create("/products/" + guardado.getId());
        return ResponseEntity.created(ubicacion).body(guardado);
    }

    @PutMapping("/{id}")
    public Product actualizar(@PathVariable Long id,
                              @RequestBody Product datos) {
        return service.actualizar(id, datos);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void borrar(@PathVariable Long id) {
        service.borrar(id);
    }
}
```

Treinta líneas para cinco endpoints. Fíjate en lo que **no** existe aquí:
ningún `if`, ninguna verificación de existencia, ningún `try/catch`. Todo eso
es trabajo de otra capa.

## Dos formas de declarar el estado

```java title="ResponseEntity o @ResponseStatus" numbered
// 1. cuando el estado varía o hay un encabezado que incluir
@PostMapping
public ResponseEntity<Product> crear(@RequestBody Product nuevo) {
    Product guardado = service.crear(nuevo);
    return ResponseEntity
            .created(URI.create("/products/" + guardado.getId()))
            .body(guardado);
}

// 2. cuando el estado es siempre el mismo
@DeleteMapping("/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
public void borrar(@PathVariable Long id) {
    service.borrar(id);
}
```

`ResponseEntity` da control total y cuesta verbosidad. `@ResponseStatus` es
declarativo y limpio, y solo sirve cuando la respuesta es siempre igual. Usa
la segunda por defecto y la primera cuando necesites el encabezado
`Location` o más de un estado posible.

## La operación que no es CRUD

Un CRUD puro no alcanza para el negocio. Descontar stock no es "actualizar
un producto": es una **acción**.

```java title="Una acción de negocio como subrecurso" numbered
@PostMapping("/{id}/stock-withdrawals")
public Product descontarStock(
        @PathVariable Long id,
        @RequestParam int cantidad) {
    return service.descontarStock(id, cantidad);
}
```

:::http title="Una acción con nombre de recurso"
POST /products/7/stock-withdrawals?cantidad=3
---
200 OK
Content-Type: application/json

{ "id": 7, "name": "Teclado", "quantity": 9, "status": "ACTIVO" }
:::

:::key
REST habla de **recursos** (sustantivos), no de acciones (verbos). Una ruta
como `/products/7/withdraw-stock` funciona y delata la intención equivocada.
La convención que mejor envejece: convierte la acción en un recurso;
`stock-withdrawals` es un registro de descuento, y crear ese registro es un
`POST`.
:::

## La API completa, en una tabla

| Verbo | Ruta | Estado de éxito | Estado de error |
|---|---|---|---|
| `GET` | `/products` | `200` | — |
| `GET` | `/products/{id}` | `200` | `404` |
| `POST` | `/products` | `201` + `Location` | `400`, `409` |
| `PUT` | `/products/{id}` | `200` | `400`, `404` |
| `DELETE` | `/products/{id}` | `204` | `404` |
| `POST` | `/products/{id}/stock-withdrawals` | `200` | `404`, `409` |

Tabla: El contrato de la API del libro. Esa tabla es la especificación, y
el capítulo 38 la va a generar automáticamente a partir del código.

## Demostrando que funciona

```bash title="El CRUD entero en seis comandos"
# crear
curl -i -X POST localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Teclado","price":349.90,"quantity":12}'

# listar
curl localhost:8080/products

# buscar
curl localhost:8080/products/1

# actualizar
curl -X PUT localhost:8080/products/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Teclado mecánico","price":299.90,"quantity":10}'

# descontar stock
curl -X POST \
  "localhost:8080/products/1/stock-withdrawals?cantidad=3"

# borrar
curl -i -X DELETE localhost:8080/products/1
```

:::checkpoint
Si el `POST` devuelve `201` con `Location`, el `DELETE` devuelve `204` y el
`GET` de un id borrado devuelve... bueno, mira el próximo párrafo. Ahí es
donde este capítulo revela el próximo problema.
:::

:::story Quinientos para todo
La aplicación del cliente empezó a ponerse lenta un martes por la tarde.

No era la base. No era la red. Era la propia aplicación, que intentaba
buscar un producto, recibía `500` y, siguiendo la regla que sigue todo
cliente HTTP bien escrito, lo intentaba de nuevo. Tres veces, con espera
exponencial.

El producto no existía. Nunca había existido. Un enlace viejo, compartido en
el grupo de WhatsApp del barrio de don Antônio, apuntaba al id 4821.

Cada persona que hacía clic generaba tres peticiones en vez de una.
Doscientas personas hicieron clic.

—La API está mintiendo —dijo Marina—. Está diciendo "fallé", y el cliente
está haciendo lo que se hace cuando un servidor falla: insistir. Si dijera
"eso no existe", nadie insistiría.
:::

## Lo que todavía está feo

```bash
curl -i localhost:8080/products/999
```

```text title="La respuesta de hoy"
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "timestamp": "2026-03-14T18:22:10.123+00:00",
  "status": 500,
  "error": "Internal Server Error",
  "path": "/products/999"
}
```

El servicio lanzó `ProductNotFoundException` y nadie la tradujo. Spring hizo
lo que hace con una excepción desconocida: `500`. Y `500` significa "tengo
un bug", cuando en realidad el cliente pidió algo que no existe, que es un
`404`.

:::pitfall
Un `500` que debería ser `404` no es solo cosmético. El monitoreo cuenta los
`5xx` para disparar alarmas; un cliente bien escrito no repite una petición
que dio `4xx` pero sí repite la que dio `5xx`. Devolver el estado equivocado
hace que tu sistema les mienta a las herramientas que lo cuidan.
:::

Falta también tratar los dos defectos restantes del capítulo 17: la entidad
se está exponiendo directamente (capítulo 24) y nada se valida (capítulo
25). Los tres próximos capítulos existen para cerrar esa lista.

:::summary
- El controlador solo traduce: sin `if`, sin `try`, sin reglas.
- `@ResponseStatus` para un estado fijo; `ResponseEntity` cuando varía o hay
  encabezado.
- Una acción de negocio se vuelve un subrecurso con `POST`, no un verbo en
  la ruta.
- Una excepción de negocio sin traductor se vuelve `500`, y `500` es una
  mentira sobre quién se equivocó.
:::

:::checkpoint
Escribes los cinco endpoints delegando en el servicio, modelas una acción
como subrecurso, eliges el estado correcto y pruebas la API completa con
`curl`.
:::

:::milestone
La API está completa: cinco endpoints, tres capas, datos en PostgreSQL.
Funciona y todavía miente en los errores, expone el modelo interno y acepta
basura. La Parte 5 resuelve los tres.
:::

:::exercise level=1
Escribe el `CategoryController` completo, delegando todo en el
`CategoryService`.

:::answer
La misma estructura del `ProductController`, con `/categories` en el
`@RequestMapping`. Si tu versión quedó parecida línea por línea, es buena
señal: la coherencia entre controladores es lo que permite que alguien nuevo
en el proyecto adivine dónde están las cosas.
:::

:::exercise level=2
Agrega `GET /products?status=ACTIVO` que filtre por estado cuando venga el
parámetro, y liste todo cuando no venga.

:::answer
```java
@GetMapping
public List<Product> listar(
        @RequestParam(required = false) Status status) {
    return status == null
            ? service.listar()
            : service.listarPorStatus(status);
}
```
El `if` aquí es aceptable porque es una decisión **de protocolo** (vino el
parámetro o no), no de negocio. Esa es la línea divisoria.
:::

:::exercise level=3
Descubre qué pasa si envías `{"name":"X","price":"abc"}` en el `POST` y
explica por qué el estado devuelto tiene sentido, o no.

:::answer
Jackson falla al convertir `"abc"` en `BigDecimal` y Spring devuelve
`400 Bad Request` con un mensaje de deserialización. El estado es correcto
(el cliente se equivocó), pero el cuerpo expone detalles internos de la
biblioteca: nombre de clase, posición del carácter. El capítulo 26
estandariza también ese caso.
:::
