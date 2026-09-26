---
source_hash: f80894c60b72
title: "Databases"
number: 19
part: p4
kicker: "A place where data survives the machine being turned off — and a fifty-year-old language nobody has managed to replace."
goal: >-
  Start a PostgreSQL instance, create tables, write the four CRUD statements
  in SQL and explain primary keys, foreign keys and indexes.
---

The `Map` from chapter 17 has a fatal flaw: it lives in the process's
memory. Restarting the application erases everything. A database solves
that and, along the way, offers fast search, integrity and simultaneous
access.

## Starting PostgreSQL in two minutes

```bash title="With Docker — the cleanest way"
docker run --name store-db \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=catalog \
  -p 5432:5432 \
  -d postgres:16
```

One command and you have a database running, isolated, that can be deleted
without a trace (`docker rm -f store-db`). If you prefer to install it
directly on your system, it works the same — it is just harder to undo.

```bash title="Getting into the database"
docker exec -it store-db psql -U postgres -d catalog
```

:::trivia
PostgreSQL was born in 1986 at Berkeley, as the successor to Ingres — hence
the name *post-Ingres*. It has been maintained by an ownerless community
for almost forty years, belongs to no company and implements the SQL
standard more rigorously than any commercial competitor. When you have no
specific reason to choose another relational database, the answer is this
one.
:::

## SQL: four statements and nothing more (for now)

```sql title="Creating the table" numbered
CREATE TABLE product (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(120) NOT NULL,
    description TEXT,
    price       NUMERIC(10,2) NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 0,
    status      VARCHAR(20) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

:::anatomy title="Each declaration in the table is a rule the database guarantees"
lang: sql
code: |
  CREATE TABLE product (
      id      BIGSERIAL PRIMARY KEY,
      name    VARCHAR(120) NOT NULL,
      price   NUMERIC(10,2) NOT NULL,
      status  VARCHAR(20) NOT NULL
  );
notes:
  - { line: 2, text: "`BIGSERIAL` creates the sequence and the 64-bit type: chapter 18's `Long`." }
  - { line: 2, text: "`PRIMARY KEY` guarantees uniqueness and creates an index automatically." }
  - { line: 3, text: "`VARCHAR(120)` limits the size — the database rejects a longer text." }
  - { line: 3, text: "`NOT NULL` turns a required field into a database rule, not just a code rule." }
  - { line: 4, text: "`NUMERIC(10,2)` is an exact decimal: chapter 3's `BigDecimal`." }
:::

| SQL | Java equivalent | Why |
|---|---|---|
| `BIGSERIAL` | `Long` | an id that grows on its own |
| `VARCHAR(n)` | `String` | text with a limit |
| `NUMERIC(10,2)` | `BigDecimal` | exact decimal, for money |
| `TIMESTAMPTZ` | `Instant` | a moment with a time zone |
| `BOOLEAN` | `Boolean` | true or false |

Table: The bridge between the two worlds. Chapter 20 does this translation
automatically.

## The four operations

```sql title="Create, read, update, delete" numbered
-- create
INSERT INTO product (name, price, quantity, status)
VALUES ('Mechanical keyboard', 349.90, 12, 'ACTIVE');

-- read
SELECT id, name, price FROM product WHERE price > 100;
SELECT * FROM product WHERE id = 1;
SELECT * FROM product ORDER BY name LIMIT 10 OFFSET 0;

-- update
UPDATE product SET price = 299.90 WHERE id = 1;

-- delete
DELETE FROM product WHERE id = 1;
```

Notice the `WHERE` in the last two. Without it, `UPDATE` changes **every**
row and `DELETE` deletes the whole table.

:::pitfall
`DELETE FROM product;` without a `WHERE` is the most destructive statement
of any programmer's career — and all of us run it once, always in
production, always on a Friday. The habit that protects you: write the
`WHERE` **first**, then go back and write the `DELETE`.
:::

:::story The Friday the WHERE was missing
The ticket said: "remove the test products from staging".

Carlos opened the database terminal and typed `DELETE FROM product`. Before
he wrote the `WHERE`, his finger brushed the Enter key.

`DELETE 11482`

He read the number three times, as if reading it would change anything.
Then he looked at the top of the window, where the connection name was. It
did not say `staging`.

What saved Aurora Comércio that Friday was not Carlos, nor the process, nor
the code review. It was the previous night's automatic *backup* and an hour
and forty minutes of restoring, with Marina beside him, in silence,
drinking coffee.

On Monday, without fuss, she added a line to the production database
terminal's configuration: a red prompt with the word PRODUCTION in
capitals.

"It's not that we trust you less," she said. "It's that nobody should need
to pay attention in order not to destroy a company."
:::

:::art caption="The most destructive statement of a career fits in three words."
src="a-instrucao-mais-destrutiva-de-uma-carreira-cabe-em-tres-palavras.png"
Charge editorial minimalista: terminal de computador ocupando o centro da
composição, mostrando a linha "DELETE FROM product" e, abaixo, em destaque,
"DELETE 11482". Um dedo ainda pousado sobre a tecla Enter de um teclado. No
canto superior da janela, uma pequena aba com a palavra "PRODUÇÃO". Ao lado,
um desenvolvedor jovem petrificado, completamente sem expressão. Fundo
branco, poucos elementos, tensão silenciosa, estética editorial de
tecnologia.
:::

## Foreign key: the integrity the database enforces

```sql title="Chapter 18's relationship, in SQL" numbered
CREATE TABLE category (
    id   BIGSERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE
);

ALTER TABLE product
    ADD COLUMN category_id BIGINT,
    ADD CONSTRAINT fk_product_category
        FOREIGN KEY (category_id) REFERENCES category (id);
```

Once that is done, the database starts **refusing** a product that points
to a category that does not exist, and refusing to delete a category that
still has products. That guarantee is worth more than any validation in
code, because it does not depend on the program being correct.

:::key
Every rule you can express in the database (`NOT NULL`, `UNIQUE`,
`FOREIGN KEY`, `CHECK`) is a rule that keeps holding when someone touches
the data from outside your application — a script, an intern, another
system. Validate in both places.
:::

## Index: why a search is fast

```sql title="Two searches, different performance" numbered
SELECT * FROM product WHERE id = 500000;       -- instant
SELECT * FROM product WHERE name = 'Keyboard'; -- scans the table

CREATE INDEX idx_product_name ON product (name);
-- now the second one is instant too
```

An index is a separate, sorted structure the database consults so it does
not have to read every row. It speeds up reading and **slows down
writing** — each `INSERT` has to update the index too. That is why you
don't index everything: you index what you search for.

:::diagram type="flowchart" caption="Without an index, the database reads everything. With one, it consults a sorted shortcut."
nodes:
  - { id: q,   type: io,       text: "WHERE name = 'Keyboard'" }
  - { id: d,   type: decision, text: "is there an index?" }
  - { id: idx, type: process,  text: "consults the index: ~20 reads" }
  - { id: seq, type: process,  text: "scans the table: 1,000,000 reads" }
  - { id: r,   type: start,    text: "row found" }
edges:
  - { from: q,   to: d }
  - { from: d,   to: idx, label: "yes" }
  - { from: d,   to: seq, label: "no" }
  - { from: idx, to: r }
  - { from: seq, to: r }
:::

## Connecting the application

```properties title="application.properties"
spring.datasource.url=jdbc:postgresql://localhost:5432/catalog
spring.datasource.username=postgres
spring.datasource.password=secret

spring.jpa.hibernate.ddl-auto=validate
spring.jpa.show-sql=true
```

And the dependency in the `pom.xml`:

```xml title="pom.xml"
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
    <scope>runtime</scope>
</dependency>
```

:::pitfall
`spring.jpa.hibernate.ddl-auto=update` shows up in every tutorial and
**must not go to production**. It lets Hibernate change the schema on its
own: renaming a field can create a new column and leave the old one behind
with the data. In production use `validate` and make changes through
versioned migrations (Flyway) — the subject of chapter 42.
:::

## SQL isn't going away

Chapter 20 brings JPA, which writes SQL for you. That does not make knowing
SQL unnecessary — it makes **typing** SQL unnecessary. When the generated
query is slow, when the log shows a thousand queries where there should be
one (chapter 30), whoever reads SQL solves it in minutes and whoever
doesn't switches frameworks.

:::term Transaction
A set of operations that happens entirely or not at all. If the order's
`INSERT` works and the item's fails, the transaction undoes both.
:::

:::summary
- Docker starts a disposable PostgreSQL in one command.
- `CREATE TABLE` declares rules the database guarantees: type, size,
  mandatoriness, uniqueness.
- `INSERT`, `SELECT`, `UPDATE`, `DELETE` are the CRUD; `UPDATE` and
  `DELETE` without `WHERE` are a catastrophe.
- A foreign key guarantees integrity even against changes made outside the
  application.
- An index speeds up reading and costs writing: index what you search for.
:::

:::checkpoint
You start a database, create tables with constraints, write the four
operations in SQL, create an index and connect the Spring application to
the database.
:::

:::milestone
The project has somewhere to store things: the `product` table exists and
the application knows the database URL. What is missing is translating the
Java class into a table row — chapter 20.
:::

:::exercise level=1
Create the `category` table and insert three categories. Then associate two
products with different categories using `UPDATE`.

:::answer
```sql
INSERT INTO category (name) VALUES ('Peripherals'), ('Monitors');
UPDATE product SET category_id = 1 WHERE id = 1;
```
Now try `UPDATE product SET category_id = 99 WHERE id = 1;` and read the
error: `violates foreign key constraint`. The database has just prevented
inconsistent data that your Java code didn't even know was wrong.
:::

:::exercise level=2
Write the query that returns the category name alongside each product.
Hint: `JOIN`.

:::answer
```sql
SELECT p.name AS product, c.name AS category
FROM product p
JOIN category c ON c.id = p.category_id
ORDER BY c.name, p.name;
```
A product without a category **does not show up** in that query. To include
it, use `LEFT JOIN` — and that one-word difference is the origin of half
the reports that "lose" records.
:::

:::exercise level=3
Find out what `EXPLAIN ANALYZE` does and run it on the name search before
and after creating the index. Compare the time and the type of scan.

:::answer
Before, the plan shows `Seq Scan on product` — a sequential scan. After,
`Index Scan using idx_product_name`. On a table with a million rows the
difference is usually three orders of magnitude. Knowing how to read an
execution plan is the skill that separates those who "optimize by guessing"
from those who optimize.
:::
