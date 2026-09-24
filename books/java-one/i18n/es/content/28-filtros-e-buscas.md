---
source_hash: 480b398eaec7
title: "Filtros y búsquedas"
number: 28
part: p5
kicker: "Filtrar en la base es una consulta. Filtrar en memoria es traerlo todo y tirar casi todo."
goal: >-
  Escribir filtros combinables con Specification, entender por qué `LIKE
  '%termino%'` ignora el índice y decidir entre *query method*, `@Query` y
  búsqueda dinámica.
---

El listado está paginado. Falta lo que todo el mundo pide a continuación:
buscar. Y buscar es donde se separan una API bien escrita y una API lenta.

## La forma equivocada, que funciona durante seis meses

```java title="Filtrar después de traerlo todo" numbered
public List<ProductResponse> buscar(String termino) {
    return repository.findAll().stream()
            .filter(p -> p.getName()
                    .toLowerCase()
                    .contains(termino.toLowerCase()))
            .map(ProductResponse::of)
            .toList();
}
```

Eso trae **todos** los productos de la base a la memoria de la aplicación y
descarta casi todos. Con cien productos, nadie lo nota. Con cien mil, cada
búsqueda mueve cien mil filas por la red para devolver tres.

:::key
La pregunta que separa las dos implementaciones: *¿quién filtra?* Si la
respuesta es "Java", ya perdiste. Quien filtra tiene que ser la base: tiene
índices, estadísticas y treinta años de optimizador. Tu aplicación tiene un
`for`.
:::

## Filtro simple: el nombre del método lo resuelve

```java title="ProductRepository.java" numbered
Page<Product> findByNameContainingIgnoreCase(
        String termino, Pageable pageable);

Page<Product> findByStatusAndPriceBetween(
        Status status, BigDecimal min, BigDecimal max,
        Pageable pageable);
```

:::http title="La búsqueda del catálogo"
GET /products?name=teclado&page=0&size=20
---
200 OK

{
  "content": [
    { "id": 3, "name": "Teclado mecánico", "price": 349.90 }
  ],
  "totalElements": 1
}
:::

Funciona bien mientras los filtros son **fijos**. El problema aparece
cuando se combinan.

## La explosión combinatoria de los filtros opcionales

Cuatro filtros opcionales —nombre, estado, precio mínimo, precio máximo—
producen dieciséis combinaciones posibles. Escribir un método para cada una
es inviable, y escribir `if` anidados es peor:

:::compare left="Un método por combinación" right="Un filtro que se arma solo"
if (nombre != null
    && status != null) {
  return repo
    .findByNameAndStatus(...);
}
if (nombre != null) {
  return repo.findByName(...);
}
// ... 14 más
---
var filtro = Specification
    .where(nombreContiene(nombre))
    .and(statusIgual(status))
    .and(precioEntre(min, max));

return repo.findAll(
    filtro, pageable);
:::

## Specification: el filtro como objeto

```java title="ProductSpecs.java" numbered
public class ProductSpecs {

    public static Specification<Product> nombreContiene(String t) {
        return (root, query, cb) -> t == null ? null
                : cb.like(cb.lower(root.get("name")),
                          "%" + t.toLowerCase() + "%");
    }

    public static Specification<Product> statusIgual(Status s) {
        return (root, query, cb) -> s == null ? null
                : cb.equal(root.get("status"), s);
    }

    public static Specification<Product> precioHasta(BigDecimal t) {
        return (root, query, cb) -> t == null ? null
                : cb.lessThanOrEqualTo(root.get("price"), t);
    }
}
```

:::anatomy title="Por qué devolver `null` es el truco central"
lang: java
code: |
  public static Specification<Product> nombreContiene(
          String termino) {
      return (root, query, cb) ->
          termino == null ? null
              : cb.like(root.get("name"), "%" + termino + "%");
  }
notes:
  - { line: 3, text: "La Specification es una lambda: recibe la raíz, la consulta y un constructor de criterios." }
  - { line: 4, text: "`null` significa *sin restricción*: Spring Data simplemente ignora este filtro." }
  - { line: 5, text: "`cb.like` arma el `WHERE` como árbol, no como texto: nada de concatenar SQL." }
:::

El repositorio necesita una interfaz más:

```java
public interface ProductRepository extends
        JpaRepository<Product, Long>,
        JpaSpecificationExecutor<Product> {
}
```

Y el servicio arma el filtro según lo que llegó:

```java title="ProductService.java" numbered
@Transactional(readOnly = true)
public Page<ProductResponse> buscar(ProductFilter f,
                                    Pageable pageable) {
    Specification<Product> spec = Specification
            .where(ProductSpecs.nombreContiene(f.name()))
            .and(ProductSpecs.statusIgual(f.status()))
            .and(ProductSpecs.precioHasta(f.maxPrice()));

    return repository.findAll(spec, pageable)
            .map(ProductResponse::of);
}
```

```java title="dto/ProductFilter.java"
public record ProductFilter(
        String name, Status status, BigDecimal maxPrice) {
}
```

El controlador recibe el record directo de la query string, sin ninguna
anotación:

```java
@GetMapping
public Page<ProductResponse> listar(
        ProductFilter filtro, Pageable pageable) {
    return service.buscar(filtro, pageable);
}
```

:::story La búsqueda igual a la de Google
—La búsqueda está mal —dijo Roberto, el lunes.

—¿Mal cómo?

—Escribí "teclad" y no encontró nada.

—Lo escribió incompleto.

—Google lo encuentra.

Marina explicó que Google tiene veinte años de inversión en indexación,
corrección ortográfica, sinónimos y un centro de datos por continente.
Roberto lo escuchó todo e hizo la pregunta que ya tenía formada antes de la
respuesta:

—¿Pero se puede hacer algo parecido para el jueves?

Quedó acordado lo posible: búsqueda por un fragmento del nombre, sin
distinguir mayúsculas ni tildes. Tomó dos días.

El jueves, Roberto probó "tecladdo", con dos d, no encontró nada, y volvió
a mencionar a Google.
:::

## Por qué `LIKE '%termino%'` es lento

```sql
SELECT * FROM product WHERE name LIKE '%teclado%';
```

El índice de una base relacional es una estructura **ordenada por el
comienzo** del valor. `LIKE 'teclado%'` usa el índice: la base salta
directo al rango que empieza con esas letras. `LIKE '%teclado%'` no: el
término puede estar en cualquier posición, y no hay orden que ayude. La base
lo lee todo.

:::diagram type="blocks" caption="Tres estrategias de búsqueda de texto, en orden de costo y de capacidad."
flow: false
rows:
  - [{ text: "LIKE 'termino%'", note: "usa índice · solo prefijo" }]
  - [{ text: "LIKE '%termino%'", note: "recorre la tabla · cualquier posición" }]
  - [{ text: "Full-text (tsvector)", note: "índice propio · raíz, ranking" }]
:::

:::tip
Hasta algunas decenas de miles de filas, `LIKE '%termino%'` es perfectamente
aceptable, y mucho más simple que la alternativa. Cuando deja de serlo,
PostgreSQL ofrece búsqueda *full-text* nativa con `to_tsvector` e índice
GIN, y solo entonces vale la pena considerar un Elasticsearch. Cambiar de
herramienta antes de tener el problema es la forma más cara de optimizar.
:::

## Tildes: el detalle que nadie recuerda

En español, `cafe` tiene que encontrar `café`. PostgreSQL lo resuelve con
la extensión `unaccent`:

```sql
CREATE EXTENSION IF NOT EXISTS unaccent;

SELECT * FROM product
WHERE unaccent(lower(name)) LIKE unaccent(lower('%cafe%'));
```

```java title="La misma idea con @Query nativa" numbered
@Query(value = """
       SELECT * FROM product
       WHERE unaccent(lower(name))
             LIKE unaccent(lower(concat('%', :termino, '%')))
       """, nativeQuery = true)
Page<Product> buscarSinTilde(@Param("termino") String termino,
                             Pageable pageable);
```

:::pitfall
Nunca armes la consulta concatenando texto:

```java
// JAMÁS
"SELECT * FROM product WHERE name = '" + termino + "'"
```

Un término con `'; DROP TABLE product; --` deja de ser una búsqueda y pasa
a ser una instrucción. Eso se llama **inyección de SQL** y es la
vulnerabilidad más antigua que todavía tumba sistemas en producción. Usa
siempre un parámetro (`:termino` o `?`): el driver envía el valor separado
del comando, y nunca se interpreta como código.
:::

## Cuál de las tres formas usar

| Situación | Herramienta |
|---|---|
| uno o dos filtros fijos | *query method* por el nombre |
| una consulta compleja, pero fija | `@Query` (JPQL) |
| filtros opcionales combinables | `Specification` |
| un recurso específico de la base | `@Query` nativa |

Tabla: El orden de la tabla es el orden en que debes intentarlo. Sube un
escalón solo cuando el anterior no alcance.

:::summary
- Quien filtra es la base; filtrar en memoria es traerlo todo para
  descartar casi todo.
- `Specification` arma el `WHERE` por partes e ignora el filtro que llegó
  nulo.
- Un `record` de filtro llega directo de la query string, sin anotación.
- `LIKE '%termino%'` no usa índice; *full-text* solo cuando el volumen lo
  exija.
- Nunca concatenes texto en SQL: usa un parámetro.
:::

:::checkpoint
Escribes filtros combinables con `Specification`, sabes cuándo alcanza el
nombre del método, explicas por qué la búsqueda por fragmento es lenta y no
escribes SQL por concatenación.
:::

:::milestone
Fin de la Parte 5. La API lista con páginas, ordena, filtra por tres
criterios opcionales, rechaza la basura y falla con honestidad. Es una API
que otra persona puede usar sin tener que hablar contigo.
:::

:::exercise level=1
Agrega un filtro opcional por `status` a la búsqueda y prueba las cuatro
combinaciones: sin filtro, solo nombre, solo estado, los dos.

:::answer
La gracia está en la prueba sin ningún filtro: como las dos
`Specification` devuelven `null`, el `WHERE` sale vacío y la consulta se
vuelve un `findAll` paginado. No hizo falta ningún `if` para que eso pase.
:::

:::exercise level=2
Escribe una `Specification` `conStock()` que filtre `quantity > 0` y
combínala con las demás. Después activa `show-sql` y revisa el `WHERE`
generado.

:::answer
```java
public static Specification<Product> conStock() {
    return (root, query, cb) ->
            cb.greaterThan(root.get("quantity"), 0);
}
```
En el log ves un único `SELECT` con todas las condiciones unidas por `and`:
la prueba de que el filtro fue a la base y no al `for`.
:::

:::exercise level=3
Mide. Registra cincuenta mil productos, corre la búsqueda por fragmento con
`EXPLAIN ANALYZE` y después crea un índice GIN con `pg_trgm`. Compara.

:::answer
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_product_name_trgm
    ON product USING gin (name gin_trgm_ops);
```
`pg_trgm` indexa trigramas —pedazos de tres letras— y es una de las pocas
formas de hacer que `LIKE '%termino%'` use un índice. El plan deja de ser
`Seq Scan` y pasa a `Bitmap Index Scan`. Medir antes y después es el hábito
que separa la optimización de la superstición.
:::
