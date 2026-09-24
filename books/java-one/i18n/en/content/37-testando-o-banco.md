---
source_hash: 6aa85e209e8a
title: "Testing the database"
number: 37
part: p8
kicker: "Testing against a database other than production's is rehearsing the play in a different theater."
goal: >-
  Test repositories with `@DataJpaTest`, start a real PostgreSQL in the test
  with Testcontainers, and understand why H2 misleads.
---

The repository is the only layer the two previous chapters didn't touch —
and it is where the SQL, the mapping, the uniqueness constraint and the
foreign key live. None of that is exercised by a mock.

## `@DataJpaTest`

```java title="ProductRepositoryTest.java" numbered
@DataJpaTest
class ProductRepositoryTest {

    @Autowired ProductRepository repository;
    @Autowired TestEntityManager em;

    @Test
    void shouldFindByNameIgnoringCase() {
        em.persist(new Product("Mechanical Keyboard",
                new BigDecimal("349.90"), 12));
        em.flush();

        var found = repository
                .findByNameContainingIgnoreCase("mechanical",
                        Pageable.unpaged());

        assertThat(found).hasSize(1);
    }

    @Test
    void shouldNotAcceptDuplicateName() {
        em.persist(new Product("Cable", BigDecimal.TEN, 1));
        em.flush();

        assertThatThrownBy(() -> {
            em.persist(new Product("Cable", BigDecimal.TEN, 1));
            em.flush();
        }).isInstanceOf(PersistenceException.class);
    }
}
```

:::anatomy title="What `@DataJpaTest` does for you"
lang: java
code: |
  @DataJpaTest
  class ProductRepositoryTest {

      @Autowired ProductRepository repository;
      @Autowired TestEntityManager em;
  }
notes:
  - { line: 1, text: "Starts only JPA, Hibernate and the repositories — no controller, no service." }
  - { line: 1, text: "Each test runs in a transaction that is **rolled back** at the end: tests don't dirty each other." }
  - { line: 4, text: "`TestEntityManager` writes directly, without going through the repository you're testing." }
:::

:::key
Setting up the scenario with `TestEntityManager` instead of
`repository.save()` isn't fussiness: if `save` is broken, the test that
uses `save` to build the scenario fails for one reason and you go looking
for another.
:::

## The H2 problem

By default, `@DataJpaTest` replaces your database with an in-memory one —
H2, if it's on the classpath. It's fast, requires nothing installed, and
lies.

| What changes | H2 | PostgreSQL |
|---|---|---|
| `unaccent`, `pg_trgm` | don't exist | exist |
| `jsonb` type, arrays | no | yes |
| `LIKE` behavior | different | yours |
| Reserved words | a different list | your list |
| `NUMERIC` precision | different | yours |

Table: Each row is a test that passes on H2 and fails in production.

:::pitfall
"It passed on H2" is a sentence that only shows up **after** the deploy.
H2 is a different database, with a different dialect and different
behavior in exactly the spots that tend to cause trouble. If you use
PostgreSQL in production, test on PostgreSQL.
:::

## Testcontainers: the real database, disposable

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

```java title="A base class for data tests" numbered
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

```java title="And the tests just inherit" numbered
class ProductRepositoryTest extends PostgresTest {

    @Autowired ProductRepository repository;

    @Test
    void shouldIgnoreAccentsInSearch() {
        // now unaccent really exists
    }
}
```

Two annotations do the heavy lifting. `@AutoConfigureTestDatabase(replace =
NONE)` stops Spring from swapping the database for H2. `@ServiceConnection`
takes the container's URL, user and password and injects them into the
configuration — without a single property written by hand.

:::diagram type="flowchart" caption="The container starts once, serves every test and disappears at the end."
nodes:
  - { id: s,  type: start,   text: "mvn test" }
  - { id: c,  type: process, text: "Docker starts postgres:16" }
  - { id: t,  type: process, text: "tests run against it" }
  - { id: r,  type: process, text: "each test rolls back its transaction" }
  - { id: k,  type: start,   text: "container is destroyed" }
edges:
  - { from: s, to: c }
  - { from: c, to: t }
  - { from: t, to: r }
  - { from: r, to: t, label: "next" }
  - { from: t, to: k }
:::

:::trivia
The `static` on the container field isn't a style detail: with it, the
container starts **once** for the whole class. Without it, Docker brings up
a new PostgreSQL for every test method — and a thirty-test suite goes from
twenty seconds to six minutes. It's the difference between a practice that
gets adopted and one abandoned in the second week.
:::

:::pitfall
Testcontainers requires Docker running on your machine and on the
continuous integration server. It is the only infrastructure dependency in
this book, and it is real: if your pipeline has no Docker, these tests
don't run. The middle ground is to run the repository tests in a separate
profile (`mvn test -Pintegration`) and keep them out of the fast everyday
build.
:::

## Versioned migrations: the test that holds for production

```xml title="pom.xml"
<dependency>
    <groupId>org.flywaydb</groupId>
    <artifactId>flyway-core</artifactId>
</dependency>
```

```sql title="src/main/resources/db/migration/V1__create_product.sql"
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

Flyway runs the `V1__`, `V2__`, `V3__` files in order, exactly once each,
and records in a table what it has already applied. With it:

- the test builds the schema **exactly** like production;
- `ddl-auto` can stay on `validate` forever;
- the database's evolution lives in Git, reviewable in a *pull request*.

:::key
Versioned migrations are the difference between "the production database
is in a state nobody knows how to reproduce" and "the database is the
result of running these seventeen files, in this order". Adopt them on day
one: retrofitting is expensive.
:::

:::story It passed on H2
Accent-insensitive search was delivered on a Wednesday, with a test.

The test searched for "cafe" and found "Café". Green. It passed the
pipeline, passed review, passed the *merge*.

On Friday, Cláudia reported that accent search didn't work in production.

Carlos swore he had tested it. He really had — on H2, which ignores accents
by default when comparing. PostgreSQL doesn't, and the `unaccent` extension
had never been installed on the production database because the test never
needed it.

The test wasn't wrong. It was running on a different database.

The move to Testcontainers took an afternoon. The first test to run against
a real PostgreSQL failed immediately — and that failure was the most useful
thing that happened that week.
:::

:::summary
- `@DataJpaTest` starts only the data layer and rolls back each test.
- Build the scenario with `TestEntityManager`, not with the repository
  under test.
- H2 is another database: different types, dialect and behavior.
- Testcontainers starts a real PostgreSQL; `static` on the container is
  mandatory so the suite doesn't drag.
- Flyway versions the schema and makes the test use the same database as
  production.
:::

:::checkpoint
You test repositories against a real PostgreSQL, version the schema with
Flyway and can explain why "it passed on H2" is no defense.
:::

:::milestone
End of Part 8. Unit, web layer and database — all three layers have a
safety net. The API can be changed without the change depending on someone
remembering to test by hand.
:::

:::exercise level=1
Write a repository test proving that two products with the same name
cannot exist.

:::answer
The test only passes if the `UNIQUE` constraint exists in the database —
and that's why it's worth it: it tests the **schema**, not the Java. If
someone removes the unique index in a future migration, this test breaks
the same day.
:::

:::exercise level=2
Set up Testcontainers and run the suite. Then remove the `static` from the
container field and time the difference.

:::answer
In a small suite the difference is already minutes. `static` makes the
container be reused by the whole class; Testcontainers also offers *reuse*
across runs, configurable in `~/.testcontainers.properties`, which removes
even the repeated startup time during development.
:::

:::exercise level=3
Write `V2__add_category.sql` creating the category table and the foreign
key in `product`. Run the tests and then answer: what happens if someone
edits `V1` after it has been applied?

:::answer
Flyway keeps a *checksum* of each applied file. Editing `V1` makes
validation fail at startup with `Migration checksum mismatch` — and that's
on purpose: a file already applied in production is history, and history
isn't edited. The fix is always a new `V3`.
:::
