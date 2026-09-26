---
source_hash: eec1d3cb7a38
title: "Problemas reales de JPA"
number: 30
part: p6
kicker: "El ORM hace exactamente lo que le mandaste. El problema es que se lo mandaste sin saber."
epigraph: "Toda abstracción no trivial tiene fugas."
epigraph_by: "Joel Spolsky, ley de las abstracciones con fugas"
goal: >-
  Diagnosticar el problema N+1 por el log, elegir entre `JOIN FETCH` y
  `@EntityGraph`, y explicar `LazyInitializationException` sin adivinar.
---

Este es el capítulo en que mucha gente abandona JPA, y es también el
capítulo que, una vez entendido, convierte a JPA en una herramienta. Todos
los problemas de aquí tienen la misma raíz: **Java esconde cuándo ocurre una
consulta**.

## El problema N+1

```java title="Parece inofensivo" numbered
List<Product> productos = repository.findAll();

for (Product p : productos) {
    System.out.println(p.getName() + " — "
            + p.getCategory().getName());
}
```

```text title="El log con show-sql activado"
select ... from product
select ... from category where id = 1
select ... from category where id = 2
select ... from category where id = 1
select ... from category where id = 3
... 11.996 veces más
```

**Una** consulta para traer la lista, más **N** consultas —una por ítem—
para buscar la categoría de cada uno. De ahí el nombre: N+1.

:::diagram type="sequence" caption="Cada `getCategory()` de un campo LAZY es un viaje a la base."
actors:
  - { id: s, name: "Service" }
  - { id: h, name: "Hibernate" }
  - { id: d, name: "Base" }
messages:
  - { from: s, to: h, text: "findAll()" }
  - { from: h, to: d, text: "select * from product" }
  - { from: d, to: h, text: "11.000 filas", dashed: true }
  - { from: s, to: h, text: "getCategory() del ítem 1" }
  - { from: h, to: d, text: "select ... category" }
  - { from: s, to: h, text: "getCategory() del ítem 2" }
  - { from: h, to: d, text: "select ... category" }
:::

:::key
El N+1 es invisible en el código Java. `p.getCategory().getName()` parece un
acceso a un campo y es una consulta a la base. La única forma de verlo es
**leer el log de SQL**, y por eso este libro pidió `show-sql=true` desde el
capítulo 20.
:::

## Las tres soluciones

```java title="1. JOIN FETCH: lo trae todo en una consulta" numbered
@Query("""
       SELECT p FROM Product p
       JOIN FETCH p.category
       """)
List<Product> findAllConCategoria();
```

```java title="2. @EntityGraph: lo mismo, sin escribir JPQL" numbered
@EntityGraph(attributePaths = "category")
List<Product> findAll();
```

```java title="3. No navegar: buscar solo lo que muestra la pantalla" numbered
@Query("""
       SELECT new com.tienda.catalog.product.dto.ProductSummary(
              p.id, p.name, c.name)
       FROM Product p JOIN p.category c
       """)
List<ProductSummary> resumen();
```

La tercera es la más rápida de las tres, porque ni siquiera arma entidades:
la base devuelve exactamente las tres columnas que necesita la pantalla e
Hibernate construye el record directamente.

| Solución | Consultas | Cuándo |
|---|---|---|
| `JOIN FETCH` | 1 | necesitas la entidad completa |
| `@EntityGraph` | 1 | lo mismo, declarativo |
| proyección a DTO | 1 | la pantalla solo lee |
| nada | N+1 | nunca a propósito |

Tabla: Tres formas de resolver el mismo problema, y la cuarta fila, que es
el estado natural de quien no miró el log.

:::pitfall
`JOIN FETCH` con paginación es una trampa específica: Hibernate avisa
`firstResult/maxResults specified with collection fetch; applying in memory`
y trae **la tabla entera** para paginar en Java. Con una colección
(`@OneToMany`), usa `@EntityGraph` con `Pageable` o haz dos consultas: la de
los ids, paginada, y la de los datos.
:::

## `LazyInitializationException`

```java title="El error que solo aparece fuera de la transacción" numbered
@Transactional(readOnly = true)
public Product buscar(Long id) {
    return repository.findById(id).orElseThrow();
}

// en el controlador, FUERA de la transacción:
producto.getCategory().getName();
// → LazyInitializationException: could not initialize proxy
```

Un campo `LAZY` no es la categoría: es un **proxy**, un objeto vacío que
sabe cómo buscar la categoría cuando alguien la pida. Solo puede buscarla
mientras la sesión de Hibernate está abierta, es decir, dentro de la
transacción. Fuera de ella, el proxy no tiene a quién preguntarle.

:::diagram type="flowchart" caption="El proxy solo funciona mientras existe la sesión."
nodes:
  - { id: t1, type: start,    text: "abre la transacción" }
  - { id: q,  type: process,  text: "carga Product (categoría = proxy)" }
  - { id: t2, type: process,  text: "cierra la transacción" }
  - { id: g,  type: decision, text: "¿getCategory()?" }
  - { id: ok, type: process,  text: "dentro: consulta la base" }
  - { id: er, type: process,  text: "fuera: LazyInitializationException" }
edges:
  - { from: t1, to: q }
  - { from: q,  to: t2 }
  - { from: t2, to: g }
  - { from: g,  to: ok, label: "antes" }
  - { from: g,  to: er, label: "después" }
:::

Las tres salidas, en orden de calidad:

1. **Convertir a DTO dentro de la transacción**: la solución del capítulo
   24, que por casualidad ya resuelve esto.
2. **`JOIN FETCH`** cuando la navegación siempre hace falta.
3. **`open-in-view`**: la configuración que mantiene la sesión abierta hasta
   el final de la petición. Es lo predeterminado en Spring Boot, y es una
   mala idea.

:::pitfall
`spring.jpa.open-in-view=true` viene **activado** por defecto. Hace
desaparecer el `LazyInitializationException` y, junto con él, hace que el
N+1 ocurra durante la serialización del JSON, lejos de cualquier código
tuyo. Desactívalo:

```properties
spring.jpa.open-in-view=false
```

Vas a romper algunas pantallas al día siguiente. Cada rotura es un lugar
donde tu código consultaba la base sin saberlo.
:::

:::story Cuatro mil consultas para una pantalla
La pantalla del catálogo se puso lenta de una forma extraña: rápida a
principios de mes, insoportable a fin de mes.

Carlos abrió el log de producción y tardó seis minutos en localizar la
petición, no porque fuera difícil, sino porque había cuatro mil treinta y
dos líneas de `select ... from category` entre su inicio y su final.

El gráfico coincidía con la historia: la lentitud crecía con el número de
productos registrados. Era el N+1 creciendo junto con el catálogo.

Lo interesante no fue el defecto. Fue la discusión que vino después.

Roberto quería cambiar la base de datos. Un proveedor había llamado
ofreciendo una solución "optimizada para alto volumen". El gráfico de la
presentación era muy convincente.

Marina pidió quince minutos y una anotación: `@EntityGraph`.

La pantalla pasó de 4.032 consultas a una. El tiempo de respuesta bajó de
once segundos a cuarenta milisegundos. El proveedor siguió llamando dos
semanas más.
:::

## La transacción: dónde empieza y dónde termina

```java title="Dos operaciones, una transacción" numbered
@Transactional
public Order finalizar(Long orderId) {
    Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));

    for (OrderItem item : order.getItems()) {
        Product p = item.getProduct();
        p.descontarStock(item.getQuantity());
    }

    order.setStatus(OrderStatus.CONFIRMADO);
    return order;
}
```

Si el descuento del tercer ítem falla por stock insuficiente, la excepción
sube, la transacción deshace **todo** —incluidos los dos descuentos ya
hechos— y el pedido sigue pendiente. Ese comportamiento de "todo o nada" es
lo que justifica la anotación.

:::pitfall
Una transacción abierta es un recurso retenido: mientras vive, una conexión
del *pool* está reservada. Un `@Transactional` alrededor de una llamada HTTP
a un servicio externo —que puede tardar treinta segundos— agota el pool en
minutos. Regla: **nada de entrada y salida lenta dentro de una
transacción**.
:::

## El checklist de JPA en producción

```properties title="application.properties: lo que vale la pena"
spring.jpa.open-in-view=false
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.properties.hibernate.jdbc.batch_size=30
logging.level.org.hibernate.SQL=DEBUG
```

Y el hábito que vale más que las cuatro líneas: **abrir el log de SQL
después de escribir cualquier consulta nueva** y contar cuántas líneas
aparecieron. Si son más de una, tienes algo que entender antes de seguir.

:::summary
- El N+1 es invisible en Java y obvio en el log de SQL.
- `JOIN FETCH`, `@EntityGraph` o una proyección a DTO lo resuelven, en ese
  orden de esfuerzo.
- `LazyInitializationException` significa acceder a un proxy fuera de la
  transacción.
- `open-in-view` esconde el problema y viene por defecto: desactívalo.
- Una transacción es todo o nada; nunca pongas una llamada externa dentro de
  ella.
:::

:::checkpoint
Identificas un N+1 leyendo el log, eliges la solución adecuada, explicas qué
es un proxy LAZY y sabes por qué es mejor `open-in-view` desactivado.
:::

:::milestone
Fin de la Parte 6. La API tiene relaciones y consultas que no multiplican
los viajes a la base. También sigue completamente abierta: cualquier persona
con la URL borra cualquier producto. La Parte 7 cierra la puerta.
:::

:::exercise level=1
Activa `show-sql`, llama a `GET /products` con diez productos de categorías
distintas y cuenta las consultas. Después agrega `@EntityGraph` y cuenta de
nuevo.

:::answer
Once consultas se vuelven una. Es el experimento más barato de este libro y
el que más cambia la forma de escribir consultas de aquí en adelante.
:::

:::exercise level=2
Provoca un `LazyInitializationException` a propósito: devuelve la entidad
`Product` directo desde el controlador con `open-in-view=false` y un campo
LAZY. Después arréglalo con un DTO.

:::answer
El arreglo con DTO no es un parche: es la forma correcta. Convertir dentro
de la transacción garantiza que todo lo que necesita el JSON ya se cargó, y
el controlador pasa a trabajar con un objeto que no tiene ninguna conexión
con la base.
:::

:::exercise level=3
Escribe la proyección `ProductSummary(Long id, String name, String category)`
con `SELECT new` y compara el SQL generado con el del `JOIN FETCH`. ¿Cuál
trae menos datos?

:::answer
La proyección trae tres columnas; el `JOIN FETCH` trae todas las columnas de
las dos tablas, incluida `description`, que puede tener dos mil caracteres
por fila. En un listado de cien ítems, la diferencia es de megabytes. Traer
solo lo que muestra la pantalla es la optimización más subestimada del
acceso a datos.
:::
