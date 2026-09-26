---
source_hash: a7a80fc4abf9
title: "Repository"
number: 21
part: p4
kicker: "Una interfaz vacía que gana veinte métodos. Vale la pena entender de dónde vienen antes de confiar en ellos."
goal: >-
  Crear un repositorio con `JpaRepository`, usar los métodos listos,
  escribir *query methods* por el nombre y explicar quién implementa la
  interfaz.
---

Este capítulo tiene la mejor relación costo-beneficio del libro: tres
líneas de código entregan el acceso completo a la base de datos.

```java title="ProductRepository.java" numbered
package com.tienda.catalog.product;

import org.springframework.data.jpa.repository.JpaRepository;

public interface ProductRepository
        extends JpaRepository<Product, Long> {
}
```

Eso es todo. Una interfaz, sin ningún método declarado, sin ninguna clase
que la implemente. Y a partir de aquí puedes guardar, buscar, listar, contar
y borrar productos.

## Lo que acaba de pasar

Al arrancar, Spring Data encuentra toda interfaz que extiende
`JpaRepository`, genera en tiempo de ejecución una clase que implementa cada
método y registra el resultado como un bean. El `@Repository` es implícito.

:::diagram type="blocks" caption="Tú declaras la interfaz; Spring Data fabrica la implementación al arrancar."
rows:
  - [{ text: "ProductRepository", note: "la interfaz que escribiste" }]
  - [{ text: "SimpleJpaRepository", note: "la implementación genérica de Spring Data" }]
  - [{ text: "EntityManager", note: "la API de JPA" }]
  - [{ text: "Hibernate → JDBC → PostgreSQL", note: "el SQL de verdad" }]
:::

:::anatomy title="Los dos parámetros que exige JpaRepository"
lang: java
code: |
  public interface ProductRepository
          extends JpaRepository<Product, Long> {
  }
notes:
  - { line: 2, text: "`Product` es la entidad que administra este repositorio." }
  - { line: 2, text: "`Long` es el tipo de la clave primaria: el mismo del campo `@Id`." }
  - { line: 2, text: "Equivocarse en el segundo parámetro (`Integer` en vez de `Long`) solo falla al arrancar, con un mensaje largo." }
:::

## Los métodos que vienen gratis

```java title="Todo esto existe sin que lo escribas" numbered
Product guardado = repository.save(nuevo);      // INSERT o UPDATE
Optional<Product> uno = repository.findById(1L); // SELECT por id
List<Product> todos = repository.findAll();     // SELECT *
long total = repository.count();
boolean existe = repository.existsById(1L);
repository.deleteById(1L);
repository.saveAll(listaDeProductos);           // lote
```

Tres detalles que ahorran horas de depuración:

`save` hace `INSERT` **o** `UPDATE`: si el id es nulo, inserta; si tiene
valor, actualiza. Es cómodo y esconde una trampa: guardar un objeto con un
id que no existe en la base genera un `INSERT` con ese id, no un error.

`findById` devuelve `Optional` (capítulo 13), no `null`. La API está
comunicando en el tipo que el producto puede no existir.

`deleteById` de un id inexistente lanza `EmptyResultDataAccessException`: no
es un silencioso "no hizo nada".

## Query methods: la consulta que nace del nombre

Aquí está el recurso que parece magia y es solo convención:

```java title="ProductRepository.java" numbered
public interface ProductRepository
        extends JpaRepository<Product, Long> {

    List<Product> findByStatus(Status status);

    List<Product> findByNameContainingIgnoreCase(String termino);

    List<Product> findByPriceBetween(BigDecimal min, BigDecimal max);

    Optional<Product> findByNameIgnoreCase(String name);

    boolean existsByName(String name);

    long countByStatus(Status status);

    List<Product> findByStatusOrderByPriceDesc(Status status);
}
```

Spring Data **lee el nombre del método**, lo parte en palabras clave y arma
la consulta. `findByNameContainingIgnoreCase` se vuelve:

```sql
SELECT * FROM product WHERE upper(name) LIKE upper('%' || ? || '%')
```

| Palabra en el nombre | Se vuelve en SQL |
|---|---|
| `findBy`, `countBy`, `existsBy` | `SELECT`, `COUNT`, `EXISTS` |
| `Containing` | `LIKE %...%` |
| `IgnoreCase` | `upper(campo) = upper(?)` |
| `Between`, `GreaterThan`, `LessThan` | comparadores |
| `And`, `Or` | conectores |
| `OrderBy...Desc` | `ORDER BY ... DESC` |
| `Top10`, `First` | `LIMIT` |

Tabla: El vocabulario de los *query methods*. La lista completa está en la
documentación de Spring Data, y cabe en una página.

:::pitfall
El nombre tiene que coincidir con el **campo de la entidad**, no con la
columna de la base. `findByCreatedAt` funciona; `findByCreated_at` no. Y si
te equivocas en el nombre del campo, el error aparece al arrancar con el
mensaje `No property 'xyz' found for type 'Product'`, lo que es excelente:
es un error de tipeo atrapado antes de la primera petición.
:::

:::pitfall
Un nombre de método es bueno hasta que deja de serlo. Cuando te encuentras
escribiendo `findByStatusAndPriceBetweenAndQuantityGreaterThanOrderByNameAsc`,
ya pasaste el límite. A partir de ahí usa `@Query`, que es el tema del
capítulo 28.
:::

## `@Query`: cuando el nombre no alcanza

```java title="JPQL y SQL nativo" numbered
@Query("SELECT p FROM Product p WHERE p.quantity = 0")
List<Product> sinStock();

@Query("""
       SELECT p FROM Product p
       WHERE p.status = :status
         AND p.price <= :tope
       ORDER BY p.price
       """)
List<Product> baratosPorStatus(
        @Param("status") Status status,
        @Param("tope") BigDecimal tope);

@Query(value = "SELECT * FROM product WHERE price > :min",
       nativeQuery = true)
List<Product> porEncimaDe(@Param("min") BigDecimal min);
```

La primera y la segunda usan **JPQL**: parecido a SQL, pero escrito en
términos de **entidades y campos** (`Product p`, `p.price`), no de tablas y
columnas. La tercera es SQL nativo, útil para recursos específicos de
PostgreSQL.

:::trivia
Ese texto de varias líneas entre `"""` es un *text block*, de Java 15. Antes
de él, un JPQL de cinco líneas era una concatenación con `+` y espacios al
final de cada pedazo, y olvidarse de un espacio producía
`WHERE p.status = :statusORDER BY`. Una funcionalidad de sintaxis que borró
toda una categoría de bugs.
:::

## Probando el repositorio de verdad

```java title="ProductRepositoryTest.java" numbered
@DataJpaTest
class ProductRepositoryTest {

    @Autowired
    ProductRepository repository;

    @Test
    void debeEncontrarPorStatus() {
        repository.save(new Product("Teclado",
                new BigDecimal("349.90"), 12));

        List<Product> activos =
                repository.findByStatus(Status.ACTIVO);

        assertThat(activos).hasSize(1);
    }
}
```

`@DataJpaTest` levanta **solo** la capa de datos, en una base en memoria, y
lo deshace todo al final de cada prueba. El capítulo 37 profundiza, incluido
por qué probar en una base distinta de la de producción es una idea que
pasa la cuenta.

:::summary
- `JpaRepository<Entidad, TipoDelId>` entrega el CRUD completo sin
  implementación.
- Spring Data genera la clase al arrancar; el `@Repository` es implícito.
- `save` inserta o actualiza; `findById` devuelve `Optional`.
- Los *query methods* nacen del nombre del método y fallan al arrancar si el
  campo no existe.
- Un nombre demasiado largo es señal de que la consulta merece `@Query`.
:::

:::checkpoint
Creas un repositorio, usas los métodos listos, escribes consultas por el
nombre del método, sabes cuándo pasar a `@Query` y pruebas con
`@DataJpaTest`.
:::

:::milestone
La API habla con la base de datos. Los datos sobreviven al reinicio: el
defecto número uno del capítulo 17 está resuelto. Falta sacar las reglas de
negocio del controlador.
:::

:::exercise level=1
Crea `CategoryRepository` y escribe un *query method* que busque una
categoría por nombre, sin distinguir mayúsculas.

:::answer
```java
public interface CategoryRepository
        extends JpaRepository<Category, Long> {
    Optional<Category> findByNameIgnoreCase(String name);
}
```
El retorno es `Optional` porque la búsqueda por un nombre específico puede
no encontrar nada, y la firma se lo avisa a quien llama.
:::

:::exercise level=2
Escribe un método que devuelva los cinco productos más caros con stock
disponible, usando solo el nombre del método.

:::answer
```java
List<Product> findTop5ByQuantityGreaterThanOrderByPriceDesc(int min);
```
Llamado con `0`. Es el límite de lo que el nombre todavía comunica bien: un
campo más y la versión con `@Query` se vuelve más legible.
:::

:::exercise level=3
Escribe, con `@Query`, una consulta que devuelva el valor total en stock
(suma de precio × cantidad) de todos los productos activos. Fíjate en que
el resultado no es una entidad.

:::answer
```java
@Query("""
       SELECT SUM(p.price * p.quantity) FROM Product p
       WHERE p.status = com.tienda.catalog.product.Status.ACTIVO
       """)
BigDecimal valorTotalEnStock();
```
El retorno es un `BigDecimal`, no un `Product`, y puede volver **nulo** si
no hay ningún producto activo, porque en SQL el `SUM` de un conjunto vacío
es `NULL`. Tratarlo es responsabilidad del servicio, que es el próximo
capítulo.
:::
