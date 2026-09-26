---
source_hash: 21b4a6a3a531
title: "Modelando la aplicación"
number: 18
part: p4
kicker: "Antes de elegir la tecnología, decidir los sustantivos. Un modelo equivocado sobrevive a todas las refactorizaciones."
goal: >-
  Identificar las entidades, los atributos y las relaciones de un dominio,
  elegir la clave primaria y justificar cada tipo de campo.
---

El capítulo 17 entregó una API que guarda productos en memoria. Antes de
cambiar la memoria por una base de datos, hay que decidir **qué** guardar.
Esa decisión es la más duradera del proyecto: las tecnologías cambian, los
modelos se quedan.

## Entidad: el sustantivo que tiene identidad

Un producto no es un valor: es una cosa. Dos productos con el mismo nombre y
el mismo precio son productos distintos, porque son ítems distintos en el
stock. Eso tiene nombre: `Product` es una **entidad**, y una entidad tiene
**identidad**.

:::key
La prueba es esta: *si todos los atributos son iguales, ¿siguen siendo
cosas distintas?* Si es así, es una entidad y necesita un id. Si no —como
una dirección, un color, una cantidad de dinero— es un **valor**, y un
`record` del capítulo 12 lo resuelve.
:::

## El modelo del libro

:::diagram type="er" caption="El dominio completo: empieza en Product y crece hasta esto en la Parte 6."
columns: 2
entities:
  - name: "Category"
    fields: ["id (PK)", "name", "description"]
  - name: "Product"
    fields: ["id (PK)", "name", "description", "price", "quantity", "status", "category_id (FK)"]
  - name: "Customer"
    fields: ["id (PK)", "name", "email", "created_at"]
  - name: "Order"
    fields: ["id (PK)", "customer_id (FK)", "created_at", "total"]
relations:
  - { from: "Category", to: "Product", label: "1:N" }
  - { from: "Customer", to: "Order", label: "1:N" }
:::

La Parte 4 construye solo `Product`. `Category` entra en el capítulo 29,
`Customer` y `Order` en el proyecto final. Construirlo todo de una vez es la
receta más confiable para no terminar nada.

## Los atributos, uno por uno

```java title="Product.java: el borrador" numbered
public class Product {
    private Long id;
    private String name;
    private String description;
    private BigDecimal price;
    private Integer quantity;
    private Status status;
    private Instant createdAt;
}
```

Cada tipo ahí es una decisión, y vale la pena defenderlas todas.

| Campo | Tipo | Por qué |
|---|---|---|
| `id` | `Long` | caben 9 trillones; `Integer` se desborda en 2.100 millones |
| `name` | `String` | con límite de tamaño en la base |
| `price` | `BigDecimal` | el dinero no es `double` (capítulo 3) |
| `quantity` | `Integer` | objeto, no `int`: permite nulo mientras no se define |
| `status` | `Status` | enum, no texto (capítulo 12) |
| `createdAt` | `Instant` | momento absoluto, sin zona horaria |

Tabla: Tipos elegidos por un motivo, no por costumbre.

:::pitfall
`Long` y `long`, `Integer` e `int` no son lo mismo. Los primeros son objetos
y aceptan `null`; los segundos son primitivos y empiezan en cero. En una
entidad de base de datos, usa siempre los objetos: un `long id` ya vale `0`
antes de guardarse, y `0` no se distingue de "todavía no tiene id".
:::

## La clave primaria

Tres estrategias, y vas a encontrar las tres en código real:

| Estrategia | Ejemplo | Cuándo |
|---|---|---|
| Secuencial | `1, 2, 3` | por defecto; simple y legible |
| UUID | `9f1c...` | datos distribuidos, id generado por el cliente |
| Natural | `dni`, `sku` | casi nunca: el dato de negocio cambia |

Tabla: La clave secuencial resuelve la mayoría de los casos. Es la elección
del libro.

:::pitfall
Usar un dato de negocio como clave primaria parece elegante y pasa la cuenta
después. El SKU del proveedor cambia; el documento se tipea mal; el e-mail
del cliente se actualiza. Cuando eso pasa, descubres que la clave está
copiada en seis tablas. La clave primaria debe ser un número sin
significado: es lo único que nunca necesita cambiar.
:::

## Relaciones: quién conoce a quién

```text title="La frase que define la relación"
Una categoría tiene muchos productos.
Un producto pertenece a una categoría.
```

Esas dos frases describen la misma relación vista de los dos lados, y esa
es la esencia del capítulo 29. En la base de datos, se materializa como una
**clave foránea** en la tabla del lado "muchos":

:::diagram type="blocks" caption="La clave foránea vive del lado que tiene muchos."
flow: false
rows:
  - [{ text: "category", note: "id · name" }]
  - [{ text: "product", note: "id · name · category_id →" }]
:::

| Cardinalidad | Ejemplo | Dónde va la FK |
|---|---|---|
| 1:N | categoría → productos | en el producto |
| N:1 | producto → categoría | en el producto (lo mismo) |
| N:N | producto ↔ etiqueta | en una tabla intermedia |
| 1:1 | usuario → perfil | en cualquiera de los dos |

Tabla: Las cuatro cardinalidades. La mayoría de las relaciones reales son
1:N.

:::story El producto que también es servicio
La reunión de modelado duró dos horas y produjo un dibujo en la pizarra.

A los noventa minutos, Cláudia se acordó de algo.

—Ah, y están los servicios.

—¿Servicios?

—Instalación, configuración, garantía extendida. También los vendemos.

—¿Y eso es un producto?

—Lo es y no lo es. No tiene stock. Pero tiene precio. Y aparece en el
catálogo junto con los demás. Y el cliente lo pone en el carrito igual.

Marina le dio vueltas al marcador en la mano unos segundos.

—¿Cuántos servicios existen hoy?

—Tres.

—¿Y cuántos productos?

—Once mil.

Dibujó una caja en el rincón de la pizarra, escribió `Product` adentro y un
campo `type` abajo. Después dibujó una jerarquía de clases al lado, con
`Product` como padre, y la tachó.

—Empezamos con un campo. Si un día los servicios tienen reglas propias de
verdad, los separamos. Modelar el futuro que quizá no llegue cuesta más que
cambiar después.
:::

## Tres preguntas que evitan refactorizaciones

Antes de escribir la primera línea de SQL, responde:

1. **¿Qué identifica esto?** Si la respuesta es "el nombre", piénsalo dos
   veces: los nombres se repiten.
2. **¿Este campo puede ser nulo?** Cada campo opcional es un `if` más en el
   código, para siempre.
3. **¿Este dato es histórico o actual?** El precio actual es un campo. El
   precio en la fecha del pedido es otro campo, en el pedido. Confundirlos
   es el defecto clásico de cualquier sistema de ventas.

:::trivia
La pregunta 3 tiene nombre en los sistemas reales: *snapshot*. Cuando un
cliente compra por R$ 100 y el precio sube a R$ 120, el pedido viejo tiene
que seguir mostrando R$ 100. Las tiendas grandes copian el precio, el nombre
y hasta la descripción dentro del ítem del pedido: una duplicación
intencional, porque el pedido es un documento histórico y no un espejo del
catálogo.
:::

## Estructura de paquetes

A partir de aquí el proyecto pasa a tener paquetes por **funcionalidad**, no
por tipo técnico:

:::tree title="Paquete por dominio, no por capa"
com/tienda/catalog/
  CatalogApplication.java
  product/
    Product.java              # entidad
    ProductRepository.java    # acceso a datos
    ProductService.java       # reglas
    ProductController.java    # HTTP
    dto/
      ProductRequest.java
      ProductResponse.java
  category/
    Category.java
  shared/
    exception/
:::

:::compare left="Por capa (evítalo)" right="Por dominio (prefiérelo)"
controller/
  ProductController
  OrderController
service/
  ProductService
  OrderService
---
product/
  ProductController
  ProductService
order/
  OrderController
  OrderService
:::

La diferencia aparece cuando el sistema crece. En la organización por capa,
tocar productos exige abrir cuatro carpetas distantes; en la organización
por dominio, todo lo que habla de productos está en una. Y borrar una
funcionalidad pasa a ser borrar una carpeta.

:::summary
- Una entidad tiene identidad y necesita un id; un valor, no.
- `BigDecimal` para dinero, `Instant` para un momento, enum para un conjunto
  cerrado, `Long` (no `long`) para el id.
- La clave primaria es un número sin significado de negocio.
- Una relación 1:N pone la clave foránea del lado "muchos".
- Organiza los paquetes por dominio, no por capa.
:::

:::checkpoint
Distingues una entidad de un valor, eliges tipos y claves con
justificación, identificas la cardinalidad de una relación y organizas los
paquetes por dominio.
:::

:::milestone
El modelo está en el papel: `Product` con siete campos, y un mapa del
dominio que llega hasta `Order`. El capítulo 19 lo convierte en tablas de
verdad.
:::

:::exercise level=1
Enumera los campos de `Customer` con tipo y justificación. Incluye un campo
que pueda ser nulo y explica por qué.

:::answer
`id: Long`, `name: String`, `email: String` (único), `phone: String` (puede
ser nulo: no todo cliente lo informa), `createdAt: Instant`. Cada campo nulo
es una decisión: un `phone` nulo significa "no informado", y el código que
envía SMS va a tener que tratarlo, para siempre.
:::

:::exercise level=2
Modela un carrito de compras. Decide si `CartItem` es una entidad o un
valor y justifícalo.

:::answer
Es una entidad, con una salvedad. Dos ítems del mismo producto en el mismo
carrito podrían fusionarse (sumando la cantidad), lo que sugiere un valor.
Pero si el sistema necesita saber *cuándo* se agregó cada ítem, o permitir
precios distintos por ítem (una promoción aplicada solo a uno), cada ítem
gana identidad propia. La respuesta depende del requisito, y por eso el
modelado es conversación, no técnica.
:::

:::exercise level=3
El precio de un producto cambia. Dibuja cómo tu modelo preserva el valor
histórico de los pedidos ya realizados.

:::answer
`OrderItem` guarda un `unitPrice` copiado en el momento de la compra,
además del `product_id`. La clave foránea sirve para rastrear qué producto
se vendió; el precio copiado sirve para el documento histórico. Sin esa
duplicación, un reajuste de precio reescribiría el pasado de toda la base,
y es uno de los bugs más caros que puede tener un sistema de ventas.
:::
