---
source_hash: 3bb73ba7cc4a
title: "Paginación y ordenamiento"
number: 27
part: p5
kicker: "`GET /products` con un millón de ítems es un ataque de denegación de servicio que escribiste tú solo."
goal: >-
  Paginar y ordenar un listado con `Pageable`, entender el costo de
  `OFFSET` y devolverle al cliente los metadatos de la paginación.
---

El `GET /products` del capítulo 23 devuelve todo. Con cien productos nadie
lo nota; con cien mil, la consulta tarda, el JSON pesa treinta megabytes y
la memoria del servidor sube hasta el límite. Este capítulo lo resuelve con
dos parámetros.

## `Pageable`: Spring ya sabe hacerlo

```java title="ProductController.java" numbered
@GetMapping
public Page<ProductResponse> listar(Pageable pageable) {
    return service.listar(pageable);
}
```

```java title="ProductService.java" numbered
@Transactional(readOnly = true)
public Page<ProductResponse> listar(Pageable pageable) {
    return repository.findAll(pageable)
            .map(ProductResponse::of);
}
```

Ninguna anotación nueva. Spring reconoce el parámetro `Pageable`, lee
`page`, `size` y `sort` de la query string y arma el objeto:

:::http title="Tres parámetros que no tuviste que declarar"
GET /products?page=0&size=10&sort=price,desc
---
200 OK

{
  "content": [
    { "id": 7, "name": "Monitor 27", "price": 1899.00 },
    { "id": 3, "name": "Teclado", "price": 349.90 }
  ],
  "pageable": { "pageNumber": 0, "pageSize": 10 },
  "totalElements": 342,
  "totalPages": 35,
  "first": true,
  "last": false,
  "numberOfElements": 2
}
:::

`Page` no es solo la lista: es la lista **más** los metadatos que el cliente
necesita para dibujar la navegación. El `.map()` del servicio convierte cada
entidad en DTO sin perder ninguno de esos campos.

## El SQL que sale de eso

```sql title="Dos consultas, no una" numbered
SELECT * FROM product
ORDER BY price DESC
LIMIT 10 OFFSET 0;

SELECT count(*) FROM product;
```

La segunda consulta existe para completar `totalElements`. Si no necesitas
el total —y muchas pantallas no lo necesitan—, cambia `Page` por `Slice` y
ahórrate un conteo en cada petición:

```java
Slice<Product> findByStatus(Status status, Pageable pageable);
```

| Tipo | Trae | Costo |
|---|---|---|
| `List` | todo | peligroso |
| `Slice` | página + "¿hay siguiente?" | una consulta |
| `Page` | página + total + n.º de páginas | dos consultas |

Tabla: `Page` es el estándar cómodo. `Slice` es la elección consciente
cuando el conteo sale caro.

## Define el valor por defecto y el tope

```java title="ProductController.java" numbered
@GetMapping
public Page<ProductResponse> listar(
        @PageableDefault(size = 20, sort = "name")
        Pageable pageable) {
    return service.listar(pageable);
}
```

```properties title="application.properties"
spring.data.web.pageable.default-page-size=20
spring.data.web.pageable.max-page-size=100
```

:::pitfall
Sin `max-page-size`, `GET /products?size=1000000` vuelve a ser el problema
que acabas de resolver, y ahora con un parámetro que cualquiera puede
descubrir. El tope no es un detalle de configuración: es una medida de
seguridad.
:::

:::story El Black Friday del GET /products
A la medianoche del Black Friday, había once mil productos registrados y la
aplicación hacía exactamente lo que estaba programada para hacer: pedir la
lista de productos.

`GET /products`. Sin ningún parámetro. Sin ningún límite. Once mil ítems,
con la descripción completa, cada vez que se abría la pantalla.

El primer minuto tuvo cuatro mil aperturas.

La API no se cayó por falta de procesador. Se cayó por memoria: cada
petición cargaba once mil objetos para armar un JSON de treinta megabytes, y
el recolector de basura pasó a trabajar más que la aplicación.

Marina subió la corrección a las 00:19: un `Pageable` en el controlador y un
tope de cien ítems por página. Tres líneas.

Roberto preguntó, en la retrospectiva, por qué esas tres líneas no estaban
ahí desde el principio.

Fue la mejor pregunta que hizo en el trimestre.
:::

## El costo escondido del `OFFSET`

:::diagram type="flowchart" caption="La base descarta todo lo que viene antes del OFFSET, y lo cobra."
nodes:
  - { id: q,   type: io,      text: "LIMIT 10 OFFSET 100000" }
  - { id: ord, type: process, text: "ordena las primeras 100.010" }
  - { id: sk,  type: process, text: "descarta 100.000" }
  - { id: r,   type: start,   text: "devuelve 10" }
edges:
  - { from: q,   to: ord }
  - { from: ord, to: sk }
  - { from: sk,  to: r }
:::

`OFFSET` no es un atajo: la base tiene que ordenar y recorrer todo lo que
viene antes para saber dónde empezar. La página 1 es instantánea; la página
10.000 es lenta, siempre, en cualquier base relacional.

La alternativa se llama **paginación por cursor** (o *keyset
pagination*):

:::compare left="Por offset" right="Por cursor"
SELECT * FROM product
ORDER BY id
LIMIT 10
OFFSET 100000;
---
SELECT * FROM product
WHERE id > 100000
ORDER BY id
LIMIT 10;
:::

La segunda usa el índice y tiene un costo constante, sin importar qué tan
lejos estés. El precio es no poder "saltar a la página 500": solo avanzas y
retrocedes. Para un *feed* infinito y para exportaciones, es la elección
correcta.

:::trivia
Por eso servicios como Twitter, Stripe y GitHub no tienen páginas numeradas
en sus API: devuelven un `next_cursor`. La decisión no es estética. Con
miles de millones de registros, `OFFSET` volvería inalcanzable la última
página.
:::

## El ordenamiento y lo que puede exponer

```text title="Todas estas formas funcionan"
?sort=name                    → nombre ascendente
?sort=price,desc              → precio descendente
?sort=status&sort=price,desc  → dos criterios
```

:::pitfall
`sort` acepta **cualquier nombre de campo de la entidad**, incluso uno que
no querías que existiera en el contrato público. `?sort=costoDeCompra` no
devuelve el campo, pero revela que existe. En las API públicas, valida la
lista de campos ordenables:

```java
private static final Set<String> ORDENABLES =
        Set.of("name", "price", "createdAt");
```
:::

Y otra trampa, esta silenciosa:

:::pitfall
Paginar **sin** un ordenamiento explícito no garantiza un orden estable.
Sin `ORDER BY`, la base puede devolver las filas en cualquier orden, y el
mismo registro puede aparecer en la página 1 y en la página 2, o en
ninguna. Ordena siempre por algo único (o termina el ordenamiento con
`id`).
:::

## El contrato final del listado

| Parámetro | Por defecto | Tope |
|---|---|---|
| `page` | `0` | — |
| `size` | `20` | `100` |
| `sort` | `name,asc` | campos permitidos |

Tabla: El listado del proyecto. Documentarlo es el trabajo del capítulo 38.

:::summary
- `Pageable` como parámetro del controlador lee `page`, `size` y `sort` por
  su cuenta.
- `Page` trae el total y el número de páginas a costa de una consulta
  extra; `Slice` no.
- Define un tamaño por defecto y un **tope**: el tope es seguridad.
- `OFFSET` sale más caro a medida que avanza la página; el cursor tiene
  costo constante.
- La paginación sin un ordenamiento estable devuelve resultados
  inconsistentes.
:::

:::checkpoint
Paginas y ordenas un listado, eliges entre `Page` y `Slice`, limitas el
tamaño de la página y sabes explicar por qué la página 10.000 es lenta.
:::

:::milestone
El listado del proyecto está paginado, se puede ordenar y tiene un tope.
Falta poder buscar, y ese es el próximo capítulo.
:::

:::exercise level=1
Pagina el listado de categorías con un tamaño por defecto de 10, ordenado
por nombre.

:::answer
```java
@GetMapping
public Page<CategoryResponse> listar(
        @PageableDefault(size = 10, sort = "name")
        Pageable pageable) {
    return service.listar(pageable);
}
```
:::

:::exercise level=2
En vez de `Page`, devuelve un record propio con solo `content`, `page`,
`size` y `totalElements`. Explica por qué eso puede valer la pena.

:::answer
```java
public record PageResponse<T>(
        List<T> content, int page, int size, long totalElements) {

    public static <T> PageResponse<T> of(Page<T> p) {
        return new PageResponse<>(p.getContent(),
                p.getNumber(), p.getSize(), p.getTotalElements());
    }
}
```
Vale la pena porque el JSON del `Page` de Spring Data expone la estructura
interna del framework (`pageable.sort.sorted`, `unpaged`…) y **cambió de
formato entre versiones**. Un DTO propio es un contrato que controlas: la
misma lección del capítulo 24, aplicada a la paginación.
:::

:::exercise level=3
Implementa la paginación por cursor para `GET /products`: recibe `afterId`
y devuelve los 20 siguientes. Compara el SQL generado con el de la versión
por offset.

:::answer
```java
@Query("""
       SELECT p FROM Product p
       WHERE p.id > :afterId
       ORDER BY p.id
       """)
List<Product> pagina(@Param("afterId") Long afterId,
                     Pageable limite);
```
Llamado con `PageRequest.ofSize(20)`. El SQL se vuelve
`WHERE id > ? ORDER BY id LIMIT 20`: un acceso por índice, sin descarte. Lo
que pierdes: saber cuántas páginas existen, y la capacidad de saltar a una
página arbitraria.
:::
