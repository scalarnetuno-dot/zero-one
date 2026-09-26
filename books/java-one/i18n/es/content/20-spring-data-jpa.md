---
source_hash: c96c680175ba
title: "Spring Data JPA"
number: 20
part: p4
kicker: "Una capa que traduce objetos en filas de tabla. Poderosa, cómoda y llena de trampas que este libro va a nombrar."
goal: >-
  Anotar una clase como entidad, mapear campos y enums, entender qué es
  Hibernate y qué es JPA, y saber cuándo estorba la traducción automática.
---

Tienes una clase Java y una tabla SQL describiendo lo mismo. Escribir a mano
la conversión entre las dos —`SELECT` a `Product`, `Product` a `INSERT`— es
un trabajo repetitivo y mecánico. JPA lo hace.

## Tres nombres, tres papeles

| Nombre | Qué es |
|---|---|
| **JPA** | la especificación: las anotaciones y el contrato |
| **Hibernate** | la implementación que la ejecuta (la estándar de Boot) |
| **Spring Data JPA** | la capa que te ahorra escribir el repositorio |

Tabla: Programas contra JPA, Hibernate hace el trabajo, y Spring Data te
ahorra el código repetitivo. Confundir los tres es común y estorba a la hora
de buscar una solución en internet.

:::trivia
Antes de JPA (2006), cada proyecto escribía su propia capa de acceso a
datos, o usaba la API cruda de JDBC, en la que una consulta de tres columnas
ocupaba veinte líneas con `ResultSet`, `try/finally` y conversión manual de
tipos. Hibernate apareció en 2001 como proyecto independiente y se volvió
tan dominante que la especificación oficial se escribió **después**, sobre
él. Es uno de los pocos casos en que el estándar siguió a la práctica.
:::

## La entidad

```java title="Product.java" numbered
package com.tienda.catalog.product;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "product")
public class Product {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 120)
    private String name;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal price;

    @Column(nullable = false)
    private Integer quantity = 0;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Status status = Status.ACTIVO;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    protected Product() { }   // exigido por JPA

    public Product(String name, BigDecimal price, Integer quantity) {
        this.name = name;
        this.price = price;
        this.quantity = quantity;
    }

    // getters y setters omitidos
}
```

:::anatomy title="Las anotaciones que hacen la traducción"
lang: java
code: |
  @Entity
  @Table(name = "product")
  public class Product {
      @Id
      @GeneratedValue(strategy = GenerationType.IDENTITY)
      private Long id;

      @Enumerated(EnumType.STRING)
      private Status status;
  }
notes:
  - { line: 1, text: "`@Entity` le dice a Hibernate: esta clase se vuelve fila de tabla." }
  - { line: 2, text: "`@Table` nombra la tabla. Sin ella, se usa el nombre de la clase." }
  - { line: 4, text: "`@Id` marca la clave primaria, obligatoria en toda entidad." }
  - { line: 5, text: "`IDENTITY` delega la generación al `BIGSERIAL` de la base." }
  - { line: 8, text: "`EnumType.STRING` graba `'ACTIVO'`. Nunca uses `ORDINAL`." }
:::

:::pitfall
`@Enumerated(EnumType.ORDINAL)` —que es lo **predeterminado** cuando no
declaras nada— graba la **posición** del enum: `0`, `1`, `2`. Si alguien
inserta un valor nuevo en medio de la lista, todos los registros de la base
pasan a significar otra cosa, en silencio. Declara siempre
`EnumType.STRING`. Este es, sin competencia, el defecto más caro de este
capítulo.
:::

## Por qué la entidad necesita un constructor vacío

Ese `protected Product() { }` parece inútil y es obligatorio: Hibernate crea
el objeto por reflexión, sin saber nada de tus constructores, y después
completa los campos. `protected` basta: no necesita ser público, y así nadie
crea un producto vacío por accidente.

Es también el motivo por el que **una entidad no puede ser un `record`**
(capítulo 12): el record no tiene constructor vacío ni setters.

:::story El día en que INACTIVO se volvió PROMOCION
El enum tenía tres valores y estaba grabado como número en la base: la
configuración predeterminada, que nadie había elegido conscientemente.

El cero era `ACTIVO`, el uno era `INACTIVO`, el dos era `AGOTADO`.

En marzo, Cláudia pidió un estado nuevo: `PROMOCION`. Carlos abrió el enum y
agregó el valor donde tenía sentido semánticamente: entre `ACTIVO` e
`INACTIVO`, porque un producto en promoción está más cerca de activo que de
inactivo.

El deploy fue el miércoles. El jueves, cuatro mil productos inactivos
aparecieron en la vidriera con etiqueta de promoción.

Nadie había cambiado ningún dato. Los números de la base seguían siendo
exactamente los mismos. Lo que había cambiado era su significado.
:::

## El ciclo de vida de una entidad

:::diagram type="flowchart" caption="Los cuatro estados de una entidad, y por qué un cambio puede grabarse sin que lo pidas."
nodes:
  - { id: novo,  type: io,      text: "new Product(): transitoria" }
  - { id: save,  type: process, text: "save(): gestionada" }
  - { id: dirty, type: process, text: "setPrice(): sucia" }
  - { id: flush, type: process, text: "flush: UPDATE automático" }
  - { id: fim,   type: start,   text: "fin de la transacción: separada" }
edges:
  - { from: novo,  to: save }
  - { from: save,  to: dirty }
  - { from: dirty, to: flush }
  - { from: flush, to: fim }
:::

Este es el comportamiento que más sorprende a quien llega: dentro de una
transacción, cambiar un objeto **gestionado** genera un `UPDATE` al final,
aun sin llamar a `save`. Hibernate compara el estado actual con lo que leyó
de la base (*dirty checking*) y graba la diferencia.

:::key
Una entidad gestionada no es un objeto común: es un objeto que Hibernate
está vigilando. Por eso el capítulo 24 insiste en no dejar que la entidad
salga de la capa de servicio: fuera de ella, nadie sabe si un cambio se va a
volver `UPDATE` o no.
:::

## Verificando el mapeo

```properties title="application.properties"
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
```

`validate` compara la entidad con la tabla al arrancar y **falla si no
coinciden**. Es la configuración que quieres: si agregaste un campo en la
clase y te olvidaste de la columna, te enteras en dos segundos, no en
producción.

```text title="Salida con show-sql, al guardar"
Hibernate:
    insert into product
        (created_at, description, name, price, quantity, status)
    values
        (?, ?, ?, ?, ?, ?)
```

:::tip
Deja `show-sql=true` durante todo el desarrollo. Ver el SQL que genera
Hibernate es el hábito que evita el problema N+1 del capítulo 30, y es la
única forma de darte cuenta de que un listado simple disparó 200 consultas.
:::

## Cuando la traducción automática estorba

JPA es excelente para operaciones por entidad: cargar un producto, guardar,
borrar. Es malo para:

- **informes** con agregación y unión de cinco tablas;
- **actualizaciones masivas** (`UPDATE product SET status = 'INACTIVO'` en
  un millón de filas);
- consultas en las que la **forma del resultado** no es una entidad.

Para esos casos, Spring ofrece `JdbcTemplate` y consultas nativas, y usar
SQL directo no es una derrota, es elegir la herramienta correcta. Una
aplicación madura tiene las dos cosas.

:::history
La crítica organizada a este tipo de herramienta tiene nombre:
*object-relational impedance mismatch*. Los objetos tienen herencia y
referencias; las tablas tienen claves y uniones. La traducción funciona en
el 90% de los casos y cobra el 10% restante con intereses: el famoso "el ORM
está lento" que, casi siempre, es el ORM haciendo exactamente lo que se le
mandó.
:::

:::term Entidad gestionada
Un objeto que Hibernate está siguiendo dentro de una transacción. Los
cambios en él se graban automáticamente al final.
:::

:::summary
- JPA es la especificación; Hibernate la ejecuta; Spring Data ahorra
  código.
- `@Entity`, `@Id`, `@GeneratedValue` y `@Column` hacen el mapeo.
- Usa siempre `@Enumerated(EnumType.STRING)`.
- La entidad necesita un constructor vacío, y por eso no puede ser un
  `record`.
- Dentro de la transacción, cambiar una entidad gestionada genera un
  `UPDATE` automático.
- `ddl-auto=validate` y `show-sql=true` son los valores sanos.
:::

:::checkpoint
Anotas una entidad completa, sabes qué anotación hace qué, explicas el
ciclo de vida de una entidad y reconoces los casos en que JPA no es la
herramienta correcta.
:::

:::milestone
`Product` ahora es una entidad JPA mapeada a la tabla `product`. Falta quién
ejecute las consultas, y el próximo capítulo muestra que eso es una
interfaz vacía.
:::

:::exercise level=1
Anota la clase `Category` como entidad, con un `name` único y obligatorio.
Confirma con `ddl-auto=validate` que la tabla coincide con la clase.

:::answer
```java
@Entity
@Table(name = "category")
public class Category {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 80)
    private String name;

    protected Category() { }
}
```
:::

:::exercise level=2
Agrega un campo `updatedAt` que se complete automáticamente en cada cambio.
Descubre `@PreUpdate`.

:::answer
```java
@Column(name = "updated_at")
private Instant updatedAt;

@PreUpdate
void alActualizar() {
    this.updatedAt = Instant.now();
}
```
`@PreUpdate` y `@PrePersist` son ganchos del ciclo de vida. Útiles, con un
pero: corren dentro de Hibernate, lo que significa que no corren cuando
haces una actualización masiva con SQL nativo.
:::

:::exercise level=3
Cambia `@Enumerated` a `ORDINAL`, guarda dos productos, agrega un valor en
el **medio** del enum y lee los datos otra vez. Describe lo que pasó.

:::answer
Los productos grabados como `1` (que era `INACTIVO`) pasan a leerse como el
valor nuevo que ocupó la posición 1. Ningún error, ningún aviso: solo datos
que cambiaron de significado. Es el tipo de defecto que solo descubre un
cliente que se queja, meses después, y arreglarlo exige un script de
migración hecho a mano.
:::
