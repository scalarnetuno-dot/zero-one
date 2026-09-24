---
source_hash: edf0391b87c0
title: "Proyecto final"
number: 41
part: p10
kicker: "Ya sin darte todo masticado. Recibes los requisitos y construyes la tienda entera."
epigraph: "No sabía lo que estaba haciendo, así que lo hice. Y entonces lo supe."
epigraph_by: "Dicho de programador, atribuido a todo el mundo"
goal: >-
  Construir por tu cuenta, desde cero, la API completa de la tienda, con las
  decisiones de modelado, arquitectura, seguridad y pruebas tomadas por ti.
---

Los cuarenta capítulos anteriores mostraron cada pieza encajando. Este
capítulo no muestra nada: **pide**.

Recibes los requisitos, como los recibirías de cualquier Cláudia, y
construyes. Cuando te trabes, vuelve al capítulo que trata el tema: siguen
donde estaban.

## Los requisitos

Aurora Comércio quiere la tienda entera, no solo el catálogo.

```text title="Lo que el sistema tiene que hacer"
1.  Registrar, listar, buscar, editar y quitar productos.
2.  Organizar los productos en categorías.
3.  Registrar clientes con e-mail único.
4.  Registrar pedidos con varios ítems.
5.  Calcular el total del pedido en el momento de la compra.
6.  Descontar el stock al confirmar el pedido.
7.  Rechazar un pedido con un ítem sin stock suficiente.
8.  Listar los pedidos de un cliente.
9.  Solo ADMIN registra, edita y quita productos y categorías.
10. El cliente ve solo sus propios pedidos.
```

Y las reglas que no están en la lista, las que Cláudia diría en la tercera
reunión:

```text title="Las reglas de negocio"
· Un producto con stock cero pasa a AGOTADO automáticamente.
· Una categoría con productos no se puede quitar.
· El precio del ítem del pedido es el del momento de la compra.
· Un pedido confirmado no se puede cambiar ni cancelar.
· El e-mail del cliente es único y no cambia después de creado.
```

## El modelo

:::diagram type="er" caption="Cinco entidades. Todas aparecieron en el libro; ahora conviven."
columns: 2
entities:
  - name: "Category"
    fields: ["id (PK)", "name (unique)", "description"]
  - name: "Product"
    fields: ["id (PK)", "name", "price", "quantity", "status", "category_id (FK)"]
  - name: "Customer"
    fields: ["id (PK)", "name", "email (unique)", "created_at"]
  - name: "Order"
    fields: ["id (PK)", "customer_id (FK)", "status", "total", "created_at"]
  - name: "OrderItem"
    fields: ["id (PK)", "order_id (FK)", "product_id (FK)", "quantity", "unit_price"]
relations:
  - { from: "Category", to: "Product", label: "1:N" }
  - { from: "Customer", to: "Order", label: "1:N" }
  - { from: "Order", to: "OrderItem", label: "1:N" }
:::

## El contrato de la API

| Verbo | Ruta | Quién puede |
|---|---|---|
| `POST` | `/auth/login` | todos |
| `GET` | `/products` | todos |
| `POST` `PUT` `DELETE` | `/products` | ADMIN |
| `GET` | `/categories` | todos |
| `POST` `DELETE` | `/categories` | ADMIN |
| `POST` | `/customers` | todos |
| `POST` | `/orders` | autenticado |
| `GET` | `/orders/mios` | autenticado (solo los suyos) |
| `GET` | `/orders/{id}` | dueño o ADMIN |

Tabla: Nueve filas que describen el sistema entero. Escríbelas antes del
código.

## El pedido, que es la parte nueva

:::http title="Crear un pedido"
POST /orders
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...

{
  "items": [
    { "productId": 7, "quantity": 2 },
    { "productId": 3, "quantity": 1 }
  ]
}
---
201 Created
Location: /orders/15

{
  "id": 15,
  "status": "CONFIRMADO",
  "total": 789.70,
  "createdAt": "2026-03-20T14:02:11Z",
  "items": [
    { "productName": "Teclado mecánico",
      "quantity": 2, "unitPrice": 349.90 },
    { "productName": "Mouse", "quantity": 1, "unitPrice": 89.90 }
  ]
}
:::

:::http title="Y cuando falta stock"
POST /orders
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...

{ "items": [ { "productId": 7, "quantity": 500 } ] }
---
409 Conflict

{
  "status": 409,
  "message": "stock insuficiente para Teclado mecánico",
  "path": "/orders"
}
:::

:::key
`POST /orders` es la operación más difícil del proyecto y la que mejor mide
si entendiste el libro. Involucra: validación de entrada, búsqueda de
varias entidades, una regla de negocio con excepción, cambio de estado de
otra entidad, cálculo de dinero, y **todo eso en una transacción**. Si falla
el descuento del tercer ítem, los dos primeros tienen que volver atrás.
:::

## El orden sugerido

```text title="Quince pasos, del vacío a lo terminado"
 1. Proyecto en Initializr: web, jpa, postgres, security,
    validation, flyway, springdoc, test.
 2. Docker: levantar PostgreSQL.
 3. Flyway: V1 con las cinco tablas.
 4. Entidades y repositorios.
 5. Category: service, controlador, DTOs, pruebas.
 6. Product: service, controlador, DTOs, pruebas.
 7. Manejo de errores centralizado.
 8. Validación en los DTOs de entrada.
 9. Paginación, orden y filtros en productos.
10. Customer: registro con e-mail único.
11. User, login y JWT.
12. Autorización por rol y por dueño del recurso.
13. Order: la operación transaccional entera.
14. Pruebas: unidad, web y repositorio con Testcontainers.
15. OpenAPI, README y archivo .http.
```

Fíjate en que el orden no es el del libro: aquí construyes **una rebanada
completa** por vez (entidad → servicio → controlador → prueba), en vez de
una capa entera por vez. Así se trabaja en un proyecto real, y es más
difícil, porque cada rebanada exige acordarse de todo.

## Lo que cuenta como terminado

:::checkpoint
Un `git clone`, un `docker compose up` y un `./mvnw spring-boot:run` deben
bastar para que otra persona corra el sistema en su máquina sin hablar
contigo. Si hay que explicar algún paso, debería estar en el `README.md`.
:::

```text title="La lista de verificación"
□ Compila y arranca con un comando.
□ Las pruebas pasan y cubren las reglas, no los getters.
□ POST /orders es transaccional de verdad (¡pruébalo!).
□ Ningún endpoint devuelve 500 ante un error previsible.
□ Ninguna contraseña, secreto o token en el repositorio.
□ Swagger arranca y permite ejercitar todo, autenticado.
□ El README explica qué es, cómo correrlo y cómo probarlo.
□ El historial de commits cuenta la evolución, no "ajustes".
```

## Tres trampas que este proyecto tiene a propósito

:::pitfall
**El total del pedido.** Si lo calculas sumando `product.getPrice()` en el
momento de la lectura, el total de un pedido viejo cambia cuando cambia el
precio del producto. El precio tiene que copiarse a `OrderItem.unitPrice`
en la creación: es el *snapshot* del capítulo 18, y la mayoría de las
primeras implementaciones se equivocan aquí.
:::

:::pitfall
**El listado de pedidos.** `GET /orders/mios` con los ítems de cada pedido
es un N+1 esperando a ocurrir: un `SELECT` para los pedidos y otro más para
los ítems de cada uno. Resuélvelo con `@EntityGraph`, y confírmalo en el
log, no por intuición.
:::

:::pitfall
**El descuento de stock concurrente.** Dos personas comprando la última
unidad al mismo tiempo: las dos leen `quantity = 1`, las dos pasan la
verificación, las dos descuentan. El stock queda en `-1`. La solución
involucra bloqueo optimista (`@Version` en la entidad), un tema que este
libro no cubre y que acabas de descubrir por tu cuenta que existe. Así se
aprende el siguiente nivel.
:::

:::story Ahora eres tú quien revisa
Carlos recibió la tarea un lunes: "la tienda entera, desde cero, solo".

No era un ejercicio. Aurora le había vendido el mismo sistema a una segunda
tienda, y la segunda tienda quería una instancia propia, sin los cuatro
meses de parches acumulados en la primera.

Empezó por el `docker compose`. Después por Flyway. El miércoles tenía
categoría y producto con pruebas. El viernes, el pedido entero,
transaccional, fallando correctamente cuando no alcanzaba el stock.

El lunes siguiente entró alguien nuevo al equipo: Bruna, que sabe lógica,
no sabe Java y fue asignada a "ese proyectito de la API".

Carlos abrió el *pull request* de Bruna el martes y, antes de aprobarlo,
escribió un comentario en la línea 14:

> "Explica en voz alta, sin leer, qué hace esta línea."

Marina vio el comentario desde el otro lado de la sala y no dijo nada. Solo
le sonrió a la pantalla, como quien reconoce su propia frase volviendo.
:::

:::summary
- Diez requisitos, cinco reglas de negocio y nueve rutas describen el
  sistema.
- Construye en rebanadas completas: entidad, servicio, controlador, prueba.
- `POST /orders` es el examen final: transacción, regla, excepción y dinero.
- Terminado significa que otra persona lo corre sin hablar contigo.
:::

:::checkpoint
Construyes una API REST completa a partir de requisitos, tomas solo las
decisiones de modelado y arquitectura, y sabes verificar si está terminada.
:::

:::milestone
El proyecto del libro terminó. Falta ponerlo en un lugar donde otras
personas puedan usarlo, y de eso trata el último capítulo.
:::

:::exercise level=1
Escribe el `README.md` del proyecto antes de escribir el código. Describe
qué hace el sistema, cómo correrlo y cómo probarlo.

:::answer
Escribir el README primero es una técnica vieja y subestimada: obliga a
describir el producto antes de construirlo, y casi siempre revela un
requisito mal entendido mientras el cambio todavía es gratis.
:::

:::exercise level=2
Implementa `POST /orders` y escribe la prueba que demuestra que la
transacción deshace todo cuando el tercer ítem no tiene stock.

:::answer
La prueba tiene que verificar **tres** cosas: el estado `409`, que no se
creó ningún pedido y que el stock de los dos primeros productos sigue
intacto. La tercera es la que la mayoría olvida, y es la única que de verdad
prueba la transacción.
:::

:::exercise level=3
Averigua qué es el bloqueo optimista, agrega `@Version` a la entidad
`Product` y escribe una prueba con dos hilos comprando la última unidad.

:::answer
`@Version` hace que Hibernate incluya la versión en el `WHERE` del
`UPDATE`: si otra transacción cambió la fila en el medio, se afectan cero
filas y recibes `OptimisticLockException`. La prueba con dos hilos es
difícil de escribir y es la mejor forma de entender por qué los sistemas de
verdad tienen reintentos. Acabas de salir del alcance de este libro por tu
cuenta, que era exactamente su objetivo.
:::
