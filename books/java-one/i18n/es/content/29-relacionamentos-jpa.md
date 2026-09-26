---
source_hash: a22b8a89d8a7
title: "Relaciones JPA"
number: 29
part: p6
kicker: "Dos tablas que se conocen se vuelven dos clases que se apuntan, y ahí es donde JPA se vuelve poderoso y peligroso en la misma medida."
goal: >-
  Mapear `@ManyToOne`, `@OneToMany` y `@ManyToMany`, elegir el lado dueño de
  la relación y evitar las tres trampas clásicas del mapeo bidireccional.
---

Hasta ahora el proyecto tiene una sola entidad. El mundo real no: un
producto pertenece a una categoría, un pedido pertenece a un cliente, un
pedido tiene ítems. Este capítulo conecta las cajas del diagrama del
capítulo 18.

## La relación más común: `@ManyToOne`

```java title="Product.java (fragmento)" numbered
@ManyToOne(fetch = FetchType.LAZY, optional = false)
@JoinColumn(name = "category_id")
private Category category;
```

Cinco palabras y la tabla gana una columna `category_id` con clave foránea.
Fíjate en `fetch = LAZY`: es la decisión más importante de la línea, y el
capítulo 30 explica por qué.

:::anatomy title="La anotación que crea la clave foránea"
lang: java
code: |
  @ManyToOne(fetch = FetchType.LAZY, optional = false)
  @JoinColumn(name = "category_id")
  private Category category;
notes:
  - { line: 1, text: "`@ManyToOne`: muchos productos para una categoría. Este es el lado **dueño** de la relación." }
  - { line: 1, text: "`LAZY` solo carga la categoría cuando alguien llama a `getCategory()`." }
  - { line: 1, text: "`optional = false` se vuelve `NOT NULL` en la columna: todo producto necesita categoría." }
  - { line: 2, text: "`@JoinColumn` nombra la columna; sin ella, Hibernate inventa `category_id` igual." }
:::

:::key
El **lado dueño** es siempre donde está la clave foránea: el lado
`@ManyToOne`. Es el que consulta la base para saber quién apunta a quién.
Todo el resto del mapeo es comodidad de navegación en Java.
:::

## El otro lado: `@OneToMany`

```java title="Category.java (fragmento)" numbered
@OneToMany(mappedBy = "category")
private List<Product> products = new ArrayList<>();
```

`mappedBy = "category"` dice: *"la dueña de esta relación es el campo
`category` de `Product`; yo solo soy el espejo"*. Sin él, Hibernate crea una
**tercera tabla** para la relación, y te enteras por el error de esquema al
arrancar.

:::pitfall
`@OneToMany` sin `mappedBy` genera una tabla intermedia que nadie pidió:
`category_products`. El síntoma es `ddl-auto=validate` fallando con
"missing table". La causa es siempre la misma: declaraste dos lados dueños.
:::

## Lo bidireccional exige disciplina

Cuando los dos lados existen en Java, pueden no estar de acuerdo entre sí:

:::compare left="Solo la mitad" right="Los dos lados"
producto.setCategory(cat);
// cat.getProducts()
// sigue sin el producto
---
public void agregar(
    Product p) {
  products.add(p);
  p.setCategory(this);
}
:::

El objeto en memoria queda inconsistente hasta que alguien lo recarga de la
base, y la diferencia entre lo que está en memoria y lo que está en la tabla
es una de las fuentes de bugs más desconcertantes de JPA. Un método auxiliar
en un solo lado lo resuelve.

:::tip
Solo mapea el lado `@OneToMany` si **realmente navegas** por él. Una
categoría con once mil productos en una `List` es una invitación al
desastre. Si la navegación es rara, olvida el campo y usa
`productRepository.findByCategoryId(id)`: la información es la misma, el
riesgo no.
:::

## `@OneToMany` con dueño propio: los ítems del pedido

```java title="Order.java" numbered
@Entity
@Table(name = "orders")
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "customer_id")
    private Customer customer;

    @OneToMany(mappedBy = "order",
               cascade = CascadeType.ALL,
               orphanRemoval = true)
    private List<OrderItem> items = new ArrayList<>();

    public void agregar(OrderItem item) {
        items.add(item);
        item.setOrder(this);
    }
}
```

Aquí `cascade` y `orphanRemoval` tienen sentido: un ítem de pedido **no
existe** sin el pedido. Guardar el pedido guarda los ítems; quitar un ítem
de la lista lo borra de la base.

:::pitfall
`CascadeType.ALL` entre `Product` y `Category` sería un desastre: borrar una
categoría borraría todos sus productos. El cascade solo se justifica cuando
el hijo es **parte** del padre: los ítems de un pedido, las direcciones de
un cliente. Si el hijo tiene vida propia, nada de cascade.
:::

:::trivia
La tabla se llama `orders`, en plural, por un motivo prosaico: `ORDER` es
palabra reservada en SQL (`ORDER BY`). Mapear una entidad llamada `Order` a
una tabla `order` genera un error de sintaxis en el `CREATE TABLE` que ya
confundió a mucha gente. Otros nombres en la lista negra: `user`, `group`,
`table`, `select`.
:::

## `@ManyToMany`: cuando los dos lados son muchos

```java title="Product.java (fragmento)" numbered
@ManyToMany
@JoinTable(
    name = "product_tag",
    joinColumns = @JoinColumn(name = "product_id"),
    inverseJoinColumns = @JoinColumn(name = "tag_id"))
private Set<Tag> tags = new HashSet<>();
```

:::diagram type="er" caption="Muchos a muchos necesita una tercera tabla, siempre."
columns: 2
entities:
  - name: "Product"
    fields: ["id (PK)", "name", "price"]
  - name: "Tag"
    fields: ["id (PK)", "name"]
  - name: "product_tag"
    fields: ["product_id (FK)", "tag_id (FK)"]
relations:
  - { from: "Product", to: "product_tag", label: "1:N" }
  - { from: "Tag", to: "product_tag", label: "1:N" }
:::

:::pitfall
`@ManyToMany` funciona bien mientras la relación sea **solo** un vínculo.
En el instante en que alguien pregunte "¿cuándo se aplicó esta etiqueta?" o
"¿quién la aplicó?", la tabla intermedia tiene que volverse una entidad con
id propio, y la conversión a mitad del proyecto es dolorosa. Antes de usar
`@ManyToMany`, pregunta si el vínculo puede ganar atributos en el futuro.
Casi siempre puede.
:::

Usa `Set`, no `List`, en `@ManyToMany`: una `List` hace que Hibernate borre
y vuelva a insertar todas las filas de la tabla intermedia en cada cambio.

## El modelo del proyecto, completo

:::diagram type="er" caption="El dominio de Aurora Comércio al final de la Parte 6."
columns: 2
entities:
  - name: "Category"
    fields: ["id (PK)", "name"]
  - name: "Product"
    fields: ["id (PK)", "name", "price", "quantity", "category_id (FK)"]
  - name: "Customer"
    fields: ["id (PK)", "name", "email"]
  - name: "Order"
    fields: ["id (PK)", "customer_id (FK)", "created_at", "total"]
  - name: "OrderItem"
    fields: ["id (PK)", "order_id (FK)", "product_id (FK)", "quantity", "unit_price"]
relations:
  - { from: "Category", to: "Product", label: "1:N" }
  - { from: "Customer", to: "Order", label: "1:N" }
  - { from: "Order", to: "OrderItem", label: "1:N" }
:::

Fíjate en el `unit_price` dentro de `OrderItem`: es el *snapshot* del
capítulo 18. El precio del producto cambia; el del pedido, no.

:::story La categoría dentro de la categoría
—Necesitamos subcategorías —dijo Cláudia.

—¿Una categoría dentro de otra?

—Eso. "Periféricos" tiene "Teclados" y "Mouses".

Carlos lo mapeó en diez minutos: una `@ManyToOne` de `Category` a la propia
`Category`. Hasta quedó elegante.

La semana siguiente, Cláudia volvió:

—Y dentro de "Teclados" están "Mecánicos" y "Membrana".

El mapeo aguantó: un árbol es un árbol, sin importar la profundidad. Lo que
no aguantó fue la pantalla: el listado de productos de una categoría pasó a
necesitar todos los descendientes, y la consulta se volvió una recursión.

—¿Cuántos niveles piensan tener? —preguntó Marina.

—Unos tres, creo.

—"Creo" significa cinco.

Fueron siete, en cuatro meses. Y, en el séptimo, alguien creó una
subcategoría cuyo padre era ella misma. La base lo aceptó: la clave foránea
estaba satisfecha. La pantalla entró en un bucle infinito.
:::

:::summary
- `@ManyToOne` es el lado dueño: donde vive la clave foránea.
- `@OneToMany` necesita `mappedBy`; si no, se vuelve una tabla intermedia.
- En una relación bidireccional, un método auxiliar mantiene coherentes los
  dos lados.
- `cascade` y `orphanRemoval` solo cuando el hijo es parte del padre.
- `@ManyToMany` con `Set`; si el vínculo puede ganar atributos, usa una
  entidad.
:::

:::checkpoint
Mapeas las tres cardinalidades, identificas el lado dueño, evitas la tabla
intermedia accidental y sabes cuándo el cascade es peligroso.
:::

:::milestone
El dominio está completo: categoría, producto, cliente, pedido e ítem. Y,
junto con él, llegó un tipo de problema que antes no existía: el próximo
capítulo trata enteramente de él.
:::

:::exercise level=1
Mapea `Category` en `Product` con `@ManyToOne` y crea el *query method*
`findByCategoryId(Long id)`. Confirma la columna en la base.

:::answer
```java
Page<Product> findByCategoryId(Long categoryId, Pageable p);
```
Fíjate en que el nombre del método navega la relación: `Category` + `Id`.
Spring Data lo entiende y genera `WHERE category_id = ?` sin ningún join.
:::

:::exercise level=2
Crea `Order` y `OrderItem` con cascade y `orphanRemoval`. Después quita un
ítem de la lista, guarda el pedido y revisa el `DELETE` en el log.

:::answer
El `DELETE` aparece sin que lo pidas: `orphanRemoval = true` entiende que
un ítem fuera de la lista del padre dejó de existir. Es cómodo y peligroso
en la misma medida: si alguien hace `items.clear()` por error, el pedido lo
pierde todo.
:::

:::exercise level=3
Implementa la subcategoría de la historia: `Category` con una `@ManyToOne`
a sí misma. Después escribe la validación que impide que una categoría sea
su propio padre, directa o indirectamente.

:::answer
La validación directa es trivial (`parent.getId().equals(this.getId())`).
La indirecta exige subir por el árbol hasta la raíz buscando el propio id,
y por eso, en bases grandes, este tipo de jerarquía suele ganar una columna
`path` (algo como `/1/7/23/`) que convierte la verificación de ciclos en
una comparación de texto. Una estructura de datos resolviendo lo que el
algoritmo haría caro: la misma lección del capítulo 8.
:::
