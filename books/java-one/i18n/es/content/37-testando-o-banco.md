---
source_hash: 6aa85e209e8a
title: "Probando la base de datos"
number: 37
part: p8
kicker: "Probar contra una base distinta de la de producción es ensayar la obra en otro teatro."
goal: >-
  Probar repositorios con `@DataJpaTest`, levantar un PostgreSQL de verdad
  en la prueba con Testcontainers y entender por qué H2 engaña.
---

El repositorio es la única capa que los dos capítulos anteriores no
tocaron, y es donde viven el SQL, el mapeo, la restricción de unicidad y la
clave foránea. Nada de eso lo ejercita un mock.

## `@DataJpaTest`

```java title="ProductRepositoryTest.java" numbered
@DataJpaTest
class ProductRepositoryTest {

    @Autowired ProductRepository repository;
    @Autowired TestEntityManager em;

    @Test
    void debeBuscarPorNombreIgnorandoMayusculas() {
        em.persist(new Product("Teclado Mecánico",
                new BigDecimal("349.90"), 12));
        em.flush();

        var hallados = repository
                .findByNameContainingIgnoreCase("mecánico",
                        Pageable.unpaged());

        assertThat(hallados).hasSize(1);
    }

    @Test
    void noDebeAceptarNombreDuplicado() {
        em.persist(new Product("Cable", BigDecimal.TEN, 1));
        em.flush();

        assertThatThrownBy(() -> {
            em.persist(new Product("Cable", BigDecimal.TEN, 1));
            em.flush();
        }).isInstanceOf(PersistenceException.class);
    }
}
```

:::anatomy title="Lo que `@DataJpaTest` hace por ti"
lang: java
code: |
  @DataJpaTest
  class ProductRepositoryTest {

      @Autowired ProductRepository repository;
      @Autowired TestEntityManager em;
  }
notes:
  - { line: 1, text: "Levanta solo JPA, Hibernate y los repositorios: sin controlador, sin servicio." }
  - { line: 1, text: "Cada prueba corre en una transacción que se **deshace** al final: las pruebas no se ensucian entre sí." }
  - { line: 4, text: "`TestEntityManager` graba directo, sin pasar por el repositorio que estás probando." }
:::

:::key
Preparar el escenario con `TestEntityManager` en vez de `repository.save()`
no es un capricho: si el `save` está roto, la prueba que usa `save` para
armar el escenario falla por un motivo y tú buscas otro.
:::

## El problema de H2

Por defecto, `@DataJpaTest` reemplaza tu base por una en memoria —H2, si
está en el classpath—. Es rápida, no exige nada instalado y miente.

| Lo que cambia | H2 | PostgreSQL |
|---|---|---|
| `unaccent`, `pg_trgm` | no existen | existen |
| Tipo `jsonb`, arrays | no | sí |
| Comportamiento de `LIKE` | otro | el tuyo |
| Palabras reservadas | otra lista | tu lista |
| Precisión de `NUMERIC` | distinta | la tuya |

Tabla: Cada fila es una prueba que pasa en H2 y falla en producción.

:::pitfall
"En H2 pasaba" es una frase que solo aparece **después** del deploy. H2 es
una base distinta, con un dialecto distinto y un comportamiento distinto
justo en los puntos que suelen dar problemas. Si usas PostgreSQL en
producción, prueba en PostgreSQL.
:::

## Testcontainers: la base de verdad, descartable

```xml title="pom.xml"
<dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>postgresql</artifactId>
    <scope>test</scope>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-testcontainers</artifactId>
    <scope>test</scope>
</dependency>
```

```java title="Una clase base para las pruebas de datos" numbered
@DataJpaTest
@AutoConfigureTestDatabase(replace = Replace.NONE)
@Testcontainers
abstract class PostgresTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres =
            new PostgreSQLContainer<>("postgres:16-alpine");
}
```

```java title="Y las pruebas solo heredan" numbered
class ProductRepositoryTest extends PostgresTest {

    @Autowired ProductRepository repository;

    @Test
    void debeIgnorarTildesEnLaBusqueda() {
        // ahora unaccent existe de verdad
    }
}
```

Dos anotaciones hacen el trabajo pesado. `@AutoConfigureTestDatabase(replace
= NONE)` impide que Spring cambie la base por H2. `@ServiceConnection` toma
la URL, el usuario y la contraseña del contenedor y los inyecta en la
configuración, sin ninguna propiedad escrita a mano.

:::diagram type="flowchart" caption="El contenedor se levanta una vez, sirve a todas las pruebas y desaparece al final."
nodes:
  - { id: s,  type: start,   text: "mvn test" }
  - { id: c,  type: process, text: "Docker levanta postgres:16" }
  - { id: t,  type: process, text: "las pruebas corren contra él" }
  - { id: r,  type: process, text: "cada prueba deshace la transacción" }
  - { id: k,  type: start,   text: "el contenedor se destruye" }
edges:
  - { from: s, to: c }
  - { from: c, to: t }
  - { from: t, to: r }
  - { from: r, to: t, label: "siguiente" }
  - { from: t, to: k }
:::

:::trivia
El `static` en el campo del contenedor no es un detalle de estilo: con él,
el contenedor se levanta **una vez** para toda la clase. Sin él, Docker
levanta un PostgreSQL nuevo por cada método de prueba, y una suite de
treinta pruebas pasa de veinte segundos a seis minutos. Es la diferencia
entre una práctica adoptada y una abandonada en la segunda semana.
:::

:::pitfall
Testcontainers exige Docker corriendo en la máquina y en el servidor de
integración continua. Es la única dependencia de infraestructura de este
libro, y es real: si tu pipeline no tiene Docker, estas pruebas no corren.
La salida intermedia es correr las pruebas de repositorio en un perfil
separado (`mvn test -Pintegration`) y mantenerlas fuera del build rápido del
día a día.
:::

## Migraciones versionadas: la prueba que vale para producción

```xml title="pom.xml"
<dependency>
    <groupId>org.flywaydb</groupId>
    <artifactId>flyway-core</artifactId>
</dependency>
```

```sql title="src/main/resources/db/migration/V1__crear_product.sql"
CREATE TABLE product (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(120) NOT NULL,
    price       NUMERIC(10,2) NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 0,
    status      VARCHAR(20) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uk_product_name ON product (lower(name));
```

Flyway corre los archivos `V1__`, `V2__`, `V3__` en orden, una sola vez
cada uno, y guarda en una tabla lo que ya aplicó. Con él:

- la prueba levanta el esquema **exactamente** como producción;
- `ddl-auto` puede quedarse en `validate` para siempre;
- la evolución de la base queda en Git, revisable en un *pull request*.

:::key
Las migraciones versionadas son la diferencia entre "la base de producción
está en un estado que nadie sabe reproducir" y "la base es el resultado de
correr estos diecisiete archivos, en este orden". Adóptalas el primer día:
aplicarlas después sale caro.
:::

:::story En H2 pasaba
La búsqueda sin distinguir tildes se entregó un miércoles, con prueba.

La prueba buscaba "cafe" y encontraba "Café". Verde. Pasó el pipeline, pasó
la revisión, pasó el *merge*.

El viernes, Cláudia avisó que la búsqueda con tildes no funcionaba en
producción.

Carlos juró que lo había probado. Y era cierto: en H2, que por defecto
ignora las tildes al comparar. PostgreSQL no las ignora, y la extensión
`unaccent` nunca se había instalado en la base de producción porque la
prueba nunca la necesitó.

La prueba no estaba mal. Estaba corriendo en otra base.

La migración a Testcontainers llevó una tarde. La primera prueba que corrió
contra el PostgreSQL de verdad falló de inmediato, y esa falla fue lo más
útil que pasó esa semana.
:::

:::summary
- `@DataJpaTest` levanta solo la capa de datos y deshace cada prueba.
- Arma el escenario con `TestEntityManager`, no con el repositorio probado.
- H2 es otra base: tipos, dialecto y comportamiento distintos.
- Testcontainers levanta el PostgreSQL de verdad; el `static` en el
  contenedor es obligatorio para que la suite no tarde.
- Flyway versiona el esquema y hace que la prueba use la misma base que
  producción.
:::

:::checkpoint
Pruebas repositorios contra un PostgreSQL real, versionas el esquema con
Flyway y sabes explicar por qué "en H2 pasaba" no es una defensa.
:::

:::milestone
Fin de la Parte 8. Unidad, capa web y base: las tres capas tienen red. La
API se puede cambiar sin que el cambio dependa de que alguien se acuerde de
probar a mano.
:::

:::exercise level=1
Escribe una prueba de repositorio que demuestre que no pueden existir dos
productos con el mismo nombre.

:::answer
La prueba solo pasa si la restricción `UNIQUE` existe en la base, y por eso
vale: prueba el **esquema**, no el Java. Si alguien quita el índice único en
una migración futura, esta prueba se rompe el mismo día.
:::

:::exercise level=2
Configura Testcontainers y corre la suite. Después quita el `static` del
campo del contenedor y cronometra la diferencia.

:::answer
En una suite pequeña la diferencia ya es de minutos. El `static` hace que
toda la clase reaproveche el contenedor; Testcontainers además ofrece
*reuse* entre ejecuciones, configurable en `~/.testcontainers.properties`,
que elimina incluso el tiempo de arranque repetido durante el desarrollo.
:::

:::exercise level=3
Escribe `V2__agregar_category.sql` creando la tabla de categoría y la clave
foránea en `product`. Corre las pruebas y después responde: ¿qué pasa si
alguien edita el `V1` después de aplicado?

:::answer
Flyway guarda un *checksum* de cada archivo aplicado. Editar el `V1` hace
que la validación falle en el arranque con `Migration checksum mismatch`, y
eso es a propósito: un archivo ya aplicado en producción es historia, y la
historia no se edita. La corrección es siempre un `V3` nuevo.
:::
