---
source_hash: 1cc4d0141f18
title: "DTO"
number: 24
part: p4
kicker: "El cliente no necesita saber cómo está diseñada tu tabla. Y no quieres que dependa de eso."
goal: >-
  Separar la entidad del contrato con records de entrada y salida,
  convertir entre los dos y enumerar tres problemas concretos que causa la
  exposición directa.
---

Hasta ahora el `ProductController` devuelve la entidad `Product`. Funciona,
es menos código y crea un acoplamiento que sale caro. Este capítulo trata de
una frontera.

## Tres problemas concretos

**1. Renombrar una columna rompe al cliente.** Si `name` pasa a ser `title`
en la base, el JSON cambia con ella, y la aplicación de celular que está en
la tienda hace seis meses deja de funcionar.

**2. Expones lo que no querías.** Todo campo nuevo en la entidad aparece
automáticamente en la respuesta. Un día alguien agrega `costoDeCompra` y el
margen de la tienda se vuelve público.

**3. La entrada acepta lo que no debería.** `POST /products` con
`{"id": 9999}` intenta grabar un id elegido por el cliente. Con
`{"createdAt": "1990-01-01"}`, reescribe la fecha de creación.

:::pitfall
El problema 3 tiene nombre e historia: *mass assignment*. En 2012, alguien
lo usó en GitHub para agregarse como administrador de un repositorio
público, a través de un campo que la API aceptaba sin querer. La corrección
no es validar más: es **no aceptar** el campo.
:::

:::story El campo que nadie quería mostrar
El campo se llamaba `costoDeCompra` y se agregó a la entidad un martes, para
un informe interno de margen.

El informe quedó listo. Nadie se acordó de que la API devolvía la entidad
entera.

El jueves, un desarrollador de un socio —de esos que integran el catálogo en
un comparador de precios— mandó un e-mail simpático preguntando si el campo
`costoDeCompra` era de verdad el costo de compra, porque, si lo era, se
volvía fácil calcular el margen de Aurora en cada ítem.

El e-mail era educado. También fue el peor e-mail que recibió Roberto en ese
trimestre.
:::

:::art caption="Exponer la entidad es publicar toda columna que alguien agregue en el futuro."
src="expor-a-entidade-e-publicar-toda-coluna-que-alguem-acrescentar-no-futuro.png"
Charge editorial minimalista: janela de resposta JSON desenhada como se fosse
a vitrine de uma loja, com vários campos visíveis em prateleiras; um deles,
destacado em vermelho, diz "custoDeCompra". Do lado de fora da vitrine, um
desenvolvedor de outra empresa observa com sorriso discreto e uma calculadora
na mão. Do lado de dentro, um gerente de camisa social tenta cobrir aquele
campo com as duas mãos. Fundo branco, poucos elementos, humor seco, estética
editorial de tecnologia.
:::

## Dos records, dos contratos

```java title="dto/ProductRequest.java" numbered
package com.tienda.catalog.product.dto;

import java.math.BigDecimal;

public record ProductRequest(
        String name,
        String description,
        BigDecimal price,
        Integer quantity) {
}
```

```java title="dto/ProductResponse.java" numbered
public record ProductResponse(
        Long id,
        String name,
        String description,
        BigDecimal price,
        Integer quantity,
        Status status,
        Instant createdAt) {

    public static ProductResponse of(Product p) {
        return new ProductResponse(
                p.getId(),
                p.getName(),
                p.getDescription(),
                p.getPrice(),
                p.getQuantity(),
                p.getStatus(),
                p.getCreatedAt());
    }
}
```

Fíjate en la asimetría: la **entrada** no tiene `id`, `status` ni
`createdAt`; esos tres no son del cliente. La **salida** tiene todo lo que
el cliente necesita y nada más.

:::key
La entrada y la salida son contratos distintos y merecen tipos distintos.
Usar el mismo record para los dos es la versión elegante del mismo error: o
la entrada acepta campos que no debería, o la salida esconde campos que
debería mostrar.
:::

:::diagram type="blocks" caption="El DTO es la frontera: la forma del JSON deja de ser la forma de la tabla."
rows:
  - [{ text: "Cliente", note: "JSON" }]
  - [{ text: "ProductRequest / ProductResponse", note: "contrato público, estable" }]
  - [{ text: "Product (entidad)", note: "diseño interno, libre para cambiar" }]
  - [{ text: "tabla product", note: "columnas" }]
:::

## La conversión

```java title="ProductService.java (con DTO en la frontera)" numbered
@Transactional(readOnly = true)
public List<ProductResponse> listar() {
    return repository.findAll().stream()
            .map(ProductResponse::of)
            .toList();
}

@Transactional
public ProductResponse crear(ProductRequest datos) {
    if (repository.existsByNameIgnoreCase(datos.name())) {
        throw new DuplicateProductException(datos.name());
    }
    Product nuevo = new Product(
            datos.name(), datos.price(), datos.quantity());
    nuevo.setDescription(datos.description());
    return ProductResponse.of(repository.save(nuevo));
}
```

`ProductResponse::of` es la referencia a método del capítulo 14 haciendo el
trabajo: un stream de entidades se vuelve un stream de respuestas en una
línea.

:::pitfall
Dónde convertir es una decisión de diseño con dos escuelas. Convertir en el
**servicio** (como aquí) mantiene trivial el controlador y hace que el
servicio hable el vocabulario del contrato. Convertir en el **controlador**
deja el servicio puro en términos de dominio, y es la elección preferida en
proyectos más grandes. Elige una y sé coherente: lo que duele de verdad es
la mitad en cada lugar.
:::

## El controlador final de la Parte 4

```java title="ProductController.java" numbered
@RestController
@RequestMapping("/products")
public class ProductController {

    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @GetMapping
    public List<ProductResponse> listar() {
        return service.listar();
    }

    @GetMapping("/{id}")
    public ProductResponse buscar(@PathVariable Long id) {
        return service.buscar(id);
    }

    @PostMapping
    public ResponseEntity<ProductResponse> crear(
            @RequestBody ProductRequest datos) {
        ProductResponse creado = service.crear(datos);
        return ResponseEntity
                .created(URI.create("/products/" + creado.id()))
                .body(creado);
    }
}
```

:::http title="El contrato público, ahora estable"
POST /products
Content-Type: application/json

{
  "name": "Teclado mecánico",
  "description": "ABNT2, switch marrón",
  "price": 349.90,
  "quantity": 12
}
---
201 Created
Location: /products/7

{
  "id": 7,
  "name": "Teclado mecánico",
  "description": "ABNT2, switch marrón",
  "price": 349.90,
  "quantity": 12,
  "status": "ACTIVO",
  "createdAt": "2026-03-14T18:22:10Z"
}
:::

Fíjate: el cliente envió cuatro campos y recibió siete. El `id`, el
`status` y el `createdAt` los decidió el servidor, y así debe ser.

## Ajustando el JSON sin tocar la entidad

```java title="Anotaciones de Jackson en el DTO" numbered
public record ProductResponse(
        Long id,
        @JsonProperty("nombre") String name,
        BigDecimal price,
        @JsonInclude(JsonInclude.Include.NON_NULL)
        String description) {
}
```

Como el DTO es una clase solo tuya, puedes renombrar campos, esconder nulos
y formatear fechas sin que nada de eso toque la entidad o la base. Esa
libertad es la ganancia concreta de la separación.

:::trivia
La sigla DTO viene de *Data Transfer Object*, catalogado por Martin Fowler
en 2002 para un problema distinto: reducir la cantidad de llamadas remotas
en sistemas distribuidos. El nombre se quedó, el motivo cambió. Hoy nadie
usa un DTO para ahorrar llamadas: lo usa para desacoplar el contrato del
modelo.
:::

## Cuándo el DTO no vale la pena

Sé honesto sobre el costo: son dos clases, dos conversiones y más líneas por
endpoint. En un proyecto interno pequeño, con un único cliente que mantienes
tú mismo, exponer la entidad es una decisión defendible.

La pregunta que decide: **¿hay alguien del otro lado que no controlas?** Si
la respuesta es sí —una aplicación publicada, un socio, un equipo distinto—,
el DTO deja de ser opcional.

:::summary
- Exponer la entidad acopla al cliente con la base, filtra campos y acepta
  campos que no debería.
- La entrada y la salida son contratos distintos: dos records.
- La entrada no tiene `id`, `status` ni fechas del sistema.
- Convierte en un solo lugar, y siempre en el mismo.
- Las anotaciones de Jackson viven en el DTO, nunca en la entidad.
:::

:::checkpoint
Separas la entidad del contrato con records, conviertes con un método de
fábrica, justificas la separación con tres problemas concretos y sabes
cuándo no se paga.
:::

:::milestone
Fin de la Parte 4. La API tiene CRUD completo, tres capas, base PostgreSQL y
un contrato público que no es el diseño de la tabla. Tres de los cuatro
defectos del capítulo 17 están resueltos; falta la validación, que abre la
Parte 5.
:::

:::exercise level=1
Escribe `CategoryRequest` y `CategoryResponse` y ajusta el
`CategoryController` para usarlos.

:::answer
```java
public record CategoryRequest(String name, String description) { }

public record CategoryResponse(Long id, String name,
                               String description) {
    public static CategoryResponse of(Category c) {
        return new CategoryResponse(c.getId(), c.getName(),
                c.getDescription());
    }
}
```
:::

:::exercise level=2
Crea `ProductSummary`, un record con solo `id`, `name` y `price`, para el
listado. Explica la ganancia.

:::answer
Un `GET /products` de mil ítems deja de transportar descripción, fecha y
estado: quizá la mitad de los bytes. En un listado de catálogo abierto en
una red móvil, esa es la diferencia entre rápido y lento. Es común que una
API tenga un DTO "resumen" para listas y uno "completo" para el detalle.
:::

:::exercise level=3
Envía `POST /products` con `{"name":"X","price":10,"id":9999}` y observa qué
pasa con el campo `id`. Después explica por qué este es el resultado
correcto.

:::answer
El campo se **ignora**: `ProductRequest` no lo declara, y Jackson descarta
las propiedades desconocidas por defecto. El producto se crea con el id de
la secuencia de la base. Es correcto porque el servidor es la autoridad
sobre la identidad de sus recursos: aceptar un id del cliente abriría la
puerta a colisiones y a sobrescribir un registro existente.
:::
