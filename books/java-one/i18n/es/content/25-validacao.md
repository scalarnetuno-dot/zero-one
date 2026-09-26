---
source_hash: ac0e4775dead
title: "Validación"
number: 25
part: p5
kicker: "Toda entrada es hostil hasta que se demuestre lo contrario, y la prueba es una anotación."
goal: >-
  Validar la entrada con Bean Validation, activar la validación con
  `@Valid`, escribir una restricción propia y decidir qué validar en cada
  capa.
---

La API del capítulo 24 acepta un producto con nombre vacío, precio negativo
y un stock de menos doscientas unidades. Lo graba todo sin quejarse, porque
nada verifica nada. Este capítulo cierra esa puerta con cuatro anotaciones.

## El problema, en una petición

:::http title="Lo que acepta hoy la API"
POST /products
Content-Type: application/json

{
  "name": "",
  "price": -50,
  "quantity": -200
}
---
201 Created

{ "id": 8, "name": "", "price": -50, "quantity": -200 }
:::

Un producto que no existe en el mundo real acaba de existir en tu base. Y va
a aparecer en el listado, en el informe y en la factura.

:::story Menos cincuenta reales
Don Antônio recibió acceso de registro para poner los productos de su tienda
en el marketplace de Aurora. Registró dieciocho ítems en una tarde, solo,
sin ayuda de nadie. Quedó orgulloso.

En el decimonoveno, escribió el precio en el campo equivocado —puso el
descuento donde iba el valor— y guardó un producto a menos cincuenta reales.

La API lo aceptó. La base lo aceptó. La vidriera lo mostró. Y, como un
precio negativo se ordena antes que todos los demás, el producto terminó en
primer lugar en el listado "menor precio".

Once personas lo compraron. El sistema calculó, para cada una, un total de
pedido negativo, y la pasarela de pago, que estaba mejor escrita que la API
de Aurora, rechazó las once transacciones con el mismo mensaje educado.

—Él no se equivocó —dijo Marina, en la reunión—. Nosotros lo dejamos.
:::

## Bean Validation

```xml title="pom.xml"
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
```

```java title="dto/ProductRequest.java" numbered
package com.tienda.catalog.product.dto;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;

public record ProductRequest(

        @NotBlank(message = "el nombre es obligatorio")
        @Size(max = 120, message = "nombre: hasta 120 caracteres")
        String name,

        @Size(max = 2000)
        String description,

        @NotNull(message = "el precio es obligatorio")
        @Positive(message = "el precio debe ser positivo")
        @Digits(integer = 8, fraction = 2)
        BigDecimal price,

        @NotNull
        @PositiveOrZero(message = "el stock no puede ser negativo")
        Integer quantity) {
}
```

Y una palabra en el controlador lo activa todo:

```java title="ProductController.java" numbered
@PostMapping
public ResponseEntity<ProductResponse> crear(
        @Valid @RequestBody ProductRequest datos) {
    ...
}
```

:::anatomy title="Cómo entra la validación en el camino de la petición"
lang: java
code: |
  @PostMapping
  public ResponseEntity<ProductResponse> crear(
          @Valid @RequestBody ProductRequest datos) {
      return ...;
  }
notes:
  - { line: 3, text: "`@RequestBody` convierte el JSON en el record: eso ya pasaba." }
  - { line: 3, text: "`@Valid` corre las anotaciones del record **antes** de que se ejecute el método." }
  - { line: 3, text: "Si falla, el método ni siquiera se llama: Spring lanza `MethodArgumentNotValidException`." }
  - { line: 4, text: "Dentro del método, `datos` es confiable. Ningún `if` de validación aquí." }
:::

## Las anotaciones que vas a usar

| Anotación | Garantiza | Sirve para |
|---|---|---|
| `@NotNull` | no es nulo | cualquier tipo |
| `@NotBlank` | no es nulo ni solo espacios | texto |
| `@NotEmpty` | no es nulo ni vacío | colección, texto |
| `@Size(min, max)` | tamaño | texto, colección |
| `@Positive` / `@PositiveOrZero` | signo | número |
| `@Min` / `@Max` | rango | entero |
| `@DecimalMin` / `@Digits` | rango y decimales | decimal |
| `@Email` | formato de e-mail | texto |
| `@Pattern(regexp)` | expresión regular | texto |
| `@Past` / `@Future` | momento | fecha |

Tabla: Las diez que resuelven casi todo. `@NotBlank` para texto y `@NotNull`
para el resto es la regla práctica que evita el error más común.

:::pitfall
`@NotNull` en un `String` acepta `""`: el texto vacío no es nulo. Para texto
obligatorio, la anotación correcta es `@NotBlank`, que rechaza nulo, vacío
y "solo espacios". Confundirlas es el defecto de validación número uno.
:::

## Lo que recibe el cliente

:::http title="Ahora la API rechaza, pero el mensaje todavía es feo"
POST /products
Content-Type: application/json

{ "name": "", "price": -50, "quantity": -200 }
---
400 Bad Request
Content-Type: application/json

{
  "timestamp": "2026-03-14T18:30:00.000+00:00",
  "status": 400,
  "errors": [ "el nombre es obligatorio", "el precio debe ser positivo" ],
  "path": "/products"
}
:::

El estado ya es correcto: `400` es culpa del cliente. Pero el cuerpo es el
formato estándar de Spring, que cambia entre versiones y no dice **qué
campo** falló de forma estructurada. El capítulo 26 lo estandariza.

## Validación propia

Cuando la regla no cabe en una anotación existente, escribes la tuya. Dos
piezas: la anotación y el validador.

```java title="SkuValido.java" numbered
@Documented
@Constraint(validatedBy = SkuValidator.class)
@Target({ElementType.FIELD, ElementType.RECORD_COMPONENT})
@Retention(RetentionPolicy.RUNTIME)
public @interface SkuValido {
    String message() default "SKU inválido";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
```

```java title="SkuValidator.java" numbered
public class SkuValidator
        implements ConstraintValidator<SkuValido, String> {

    private static final Pattern FORMATO =
            Pattern.compile("^[A-Z]{3}-\\d{4}$");

    @Override
    public boolean isValid(String valor,
                           ConstraintValidatorContext ctx) {
        if (valor == null) {
            return true;      // la nulidad es asunto del @NotNull
        }
        return FORMATO.matcher(valor).matches();
    }
}
```

```java
@SkuValido
private String sku;     // acepta "TEC-0042"
```

:::key
Un validador **no** debe verificar el nulo. Dejar pasar el `null` y delegar
la obligatoriedad en `@NotNull` es la convención de la especificación:
permite combinar las anotaciones sin duplicar reglas.
:::

## Dónde validar: las tres capas

:::diagram type="blocks" caption="Cada capa valida algo distinto, y las tres son necesarias."
rows:
  - [{ text: "DTO (@Valid)", note: "formato: obligatorio, tamaño, signo" }]
  - [{ text: "Service", note: "reglas: nombre duplicado, stock suficiente" }]
  - [{ text: "Base (NOT NULL, UNIQUE)", note: "la última línea de defensa" }]
:::

| Capa | Valida | Ejemplo |
|---|---|---|
| DTO | la forma de la entrada | "el precio es obligatorio y positivo" |
| Service | reglas de negocio | "no existe otro producto con este nombre" |
| Base | integridad | `UNIQUE`, `NOT NULL`, `FOREIGN KEY` |

Tabla: El DTO no consulta la base; el servicio no verifica formato; la base
no conoce la regla. Cada uno en su lugar.

:::pitfall
La tentación es validar la unicidad en el DTO, con un validador que
consulta la base. Funciona y crea dos problemas: el DTO pasa a depender del
repositorio (y la prueba del DTO pasa a necesitar una base), y la
verificación sigue sujeta a una condición de carrera: entre la verificación
y el `INSERT`, otra petición puede insertar el mismo nombre. Por eso la
restricción `UNIQUE` de la base no es opcional.
:::

## Validando objetos anidados y listas

```java title="@Valid baja un nivel si se lo pides" numbered
public record OrderRequest(
        @NotNull Long customerId,

        @NotEmpty(message = "el pedido necesita ítems")
        @Valid                     // valida cada ítem de la lista
        List<OrderItemRequest> items) {
}

public record OrderItemRequest(
        @NotNull Long productId,
        @NotNull @Positive Integer quantity) {
}
```

Sin el `@Valid` en la lista, las anotaciones de `OrderItemRequest` se
ignoran. Es un olvido silencioso y común.

:::summary
- Bean Validation valida la **forma** de la entrada con anotaciones en el
  DTO.
- `@Valid` en el parámetro activa la validación: sin él, no corre nada.
- `@NotBlank` para texto obligatorio; `@NotNull` para los demás tipos.
- Un validador propio no verifica el nulo.
- Formato en el DTO, reglas en el servicio, integridad en la base.
- `@Valid` en una colección es obligatorio para validar sus ítems.
:::

:::checkpoint
Validas la entrada con las diez anotaciones principales, la activas con
`@Valid`, escribes una restricción propia y sabes qué le corresponde a cada
capa.
:::

:::milestone
La API rechaza basura: nombre vacío, precio negativo, stock negativo. El
cuarto defecto del capítulo 17 está resuelto, pero el mensaje de error que
recibe el cliente todavía es el del framework, y el capítulo 26 lo arregla.
:::

:::exercise level=1
Valida `CategoryRequest`: nombre obligatorio de como máximo 80 caracteres,
descripción opcional de como máximo 500.

:::answer
```java
public record CategoryRequest(
        @NotBlank @Size(max = 80) String name,
        @Size(max = 500) String description) {
}
```
:::

:::exercise level=2
Haz que el `PUT` también valide. Después responde: ¿por qué tiene sentido
usar el mismo `ProductRequest` en el `POST` y en el `PUT`, y en qué
situación dejaría de tenerlo?

:::answer
Tiene sentido porque `PUT` reemplaza el recurso entero: los mismos campos
obligatorios. Dejaría de tenerlo en una API con actualización parcial
(`PATCH`), donde todo campo es opcional: ahí el `@NotBlank` del `POST`
rechazaría un cambio de precio legítimo que no envió el nombre. En ese caso
son dos DTO.
:::

:::exercise level=3
Escribe una validación de clase (no de campo) que garantice que `price` no
sea mayor que `1_000_000` cuando `quantity` sea mayor que `100`. Pista:
`@Constraint` en `ElementType.TYPE`.

:::answer
La anotación va en el tipo y el validador recibe el objeto entero, lo que
permite comparar dos campos:

```java
public class LoteCoherenteValidator implements
        ConstraintValidator<LoteCoherente, ProductRequest> {
    public boolean isValid(ProductRequest r,
                           ConstraintValidatorContext c) {
        if (r.quantity() == null || r.price() == null) {
            return true;
        }
        BigDecimal tope = new BigDecimal("1000000");
        return r.quantity() <= 100
                || r.price().compareTo(tope) <= 0;
    }
}
```
Una validación que involucra dos campos **tiene que** ser de clase.
Intentar hacerla en un campo es el camino hacia un validador que no tiene
acceso a lo que necesita.
:::
