---
source_hash: f80894c60b72
title: "Base de datos"
number: 19
part: p4
kicker: "Un lugar donde el dato sobrevive al apagado de la máquina, y un lenguaje de cincuenta años que nadie ha logrado reemplazar."
goal: >-
  Levantar un PostgreSQL, crear tablas, escribir las cuatro instrucciones
  del CRUD en SQL y explicar la clave primaria, la clave foránea y el
  índice.
---

El `Map` del capítulo 17 tiene un defecto fatal: vive en la memoria del
proceso. Reiniciar la aplicación lo borra todo. Una base de datos resuelve
eso y, de paso, ofrece búsqueda rápida, integridad y acceso simultáneo.

## Levantando un PostgreSQL en dos minutos

```bash title="Con Docker: la forma más limpia"
docker run --name tienda-db \
  -e POSTGRES_PASSWORD=secreto \
  -e POSTGRES_DB=catalog \
  -p 5432:5432 \
  -d postgres:16
```

Un comando y tienes una base de datos corriendo, aislada, que puede borrarse
sin dejar rastro (`docker rm -f tienda-db`). Si prefieres instalarla
directamente en el sistema, funciona igual; solo es más difícil de
deshacer.

```bash title="Entrando en la base"
docker exec -it tienda-db psql -U postgres -d catalog
```

:::trivia
PostgreSQL nació en 1986 en Berkeley, como sucesor de Ingres: de ahí el
nombre *post-Ingres*. Lo mantiene una comunidad sin dueño desde hace casi
cuarenta años, no pertenece a ninguna empresa e implementa el estándar SQL
con más rigor que cualquier competidor comercial. Cuando no tienes un motivo
específico para elegir otra base relacional, la respuesta es esta.
:::

## SQL: cuatro instrucciones y nada más (por ahora)

```sql title="Creando la tabla" numbered
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

:::anatomy title="Cada declaración de la tabla es una regla que garantiza la base"
lang: sql
code: |
  CREATE TABLE product (
      id      BIGSERIAL PRIMARY KEY,
      name    VARCHAR(120) NOT NULL,
      price   NUMERIC(10,2) NOT NULL,
      status  VARCHAR(20) NOT NULL
  );
notes:
  - { line: 2, text: "`BIGSERIAL` crea la secuencia y el tipo de 64 bits: el `Long` del capítulo 18." }
  - { line: 2, text: "`PRIMARY KEY` garantiza la unicidad y crea un índice automáticamente." }
  - { line: 3, text: "`VARCHAR(120)` limita el tamaño: la base rechaza un texto más largo." }
  - { line: 3, text: "`NOT NULL` convierte un campo obligatorio en regla de la base, no solo del código." }
  - { line: 4, text: "`NUMERIC(10,2)` es un decimal exacto: el `BigDecimal` del capítulo 3." }
:::

| SQL | Equivalente en Java | Por qué |
|---|---|---|
| `BIGSERIAL` | `Long` | un id que crece solo |
| `VARCHAR(n)` | `String` | texto con límite |
| `NUMERIC(10,2)` | `BigDecimal` | decimal exacto, para dinero |
| `TIMESTAMPTZ` | `Instant` | momento con zona horaria |
| `BOOLEAN` | `Boolean` | verdadero o falso |

Tabla: El puente entre los dos mundos. El capítulo 20 hace esta traducción
automáticamente.

## Las cuatro operaciones

```sql title="Create, read, update, delete" numbered
-- create
INSERT INTO product (name, price, quantity, status)
VALUES ('Teclado mecánico', 349.90, 12, 'ACTIVO');

-- read
SELECT id, name, price FROM product WHERE price > 100;
SELECT * FROM product WHERE id = 1;
SELECT * FROM product ORDER BY name LIMIT 10 OFFSET 0;

-- update
UPDATE product SET price = 299.90 WHERE id = 1;

-- delete
DELETE FROM product WHERE id = 1;
```

Fíjate en el `WHERE` de las dos últimas. Sin él, `UPDATE` cambia **todas**
las filas y `DELETE` borra la tabla entera.

:::pitfall
`DELETE FROM product;` sin `WHERE` es la instrucción más destructiva de la
carrera de cualquier programador, y todos la ejecutamos una vez, siempre en
producción, siempre un viernes. El hábito que protege: escribe el `WHERE`
**primero**, después vuelve y escribe el `DELETE`.
:::

:::story El viernes en que faltó el WHERE
El ticket decía: "quitar los productos de prueba de homologación".

Carlos abrió la terminal de la base y escribió `DELETE FROM product`. Antes
de escribir el `WHERE`, el dedo rozó el Enter.

`DELETE 11482`

Leyó el número tres veces, como si leerlo cambiara algo. Después miró la
parte de arriba de la ventana, donde estaba el nombre de la conexión. No
decía `homologacion`.

Lo que salvó a Aurora Comércio ese viernes no fue Carlos, ni el proceso, ni
la revisión de código. Fue el *backup* automático de la noche anterior y una
hora y cuarenta de restauración, con Marina al lado, en silencio, tomando
café.

El lunes, sin alarde, agregó una línea a la configuración de la terminal de
la base de producción: un prompt rojo con la palabra PRODUCCIÓN en
mayúsculas.

—No es que confiemos menos en ti —dijo—. Es que nadie debería necesitar
prestar atención para no destruir una empresa.
:::

:::art caption="La instrucción más destructiva de una carrera cabe en tres palabras."
src="a-instrucao-mais-destrutiva-de-uma-carreira-cabe-em-tres-palavras.png"
Charge editorial minimalista: terminal de computador ocupando o centro da
composição, mostrando a linha "DELETE FROM product" e, abaixo, em destaque,
"DELETE 11482". Um dedo ainda pousado sobre a tecla Enter de um teclado. No
canto superior da janela, uma pequena aba com a palavra "PRODUÇÃO". Ao lado,
um desenvolvedor jovem petrificado, completamente sem expressão. Fundo
branco, poucos elementos, tensão silenciosa, estética editorial de
tecnologia.
:::

## Clave foránea: la integridad que exige la base

```sql title="La relación del capítulo 18, en SQL" numbered
CREATE TABLE category (
    id   BIGSERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE
);

ALTER TABLE product
    ADD COLUMN category_id BIGINT,
    ADD CONSTRAINT fk_product_category
        FOREIGN KEY (category_id) REFERENCES category (id);
```

Hecho eso, la base pasa a **rechazar** un producto que apunte a una
categoría que no existe, y a rechazar el borrado de una categoría que
todavía tiene productos. Esa garantía vale más que cualquier validación en
código, porque no depende de que el programa esté bien.

:::key
Toda regla que puedas expresar en la base (`NOT NULL`, `UNIQUE`,
`FOREIGN KEY`, `CHECK`) es una regla que sigue valiendo cuando alguien toca
los datos por fuera de tu aplicación: un script, un pasante, otro sistema.
Valida en los dos lugares.
:::

## Índice: por qué una búsqueda es rápida

```sql title="Dos búsquedas, rendimientos distintos" numbered
SELECT * FROM product WHERE id = 500000;      -- instantáneo
SELECT * FROM product WHERE name = 'Teclado'; -- recorre la tabla

CREATE INDEX idx_product_name ON product (name);
-- ahora la segunda también es instantánea
```

Un índice es una estructura ordenada aparte que la base consulta para no
tener que leer todas las filas. Acelera la lectura y **ralentiza la
escritura**: cada `INSERT` tiene que actualizar también el índice. Por eso
no se indexa todo: se indexa lo que se busca.

:::diagram type="flowchart" caption="Sin índice, la base lee todo. Con índice, consulta un atajo ordenado."
nodes:
  - { id: q,   type: io,       text: "WHERE name = 'Teclado'" }
  - { id: d,   type: decision, text: "¿hay índice?" }
  - { id: idx, type: process,  text: "consulta el índice: ~20 lecturas" }
  - { id: seq, type: process,  text: "recorre la tabla: 1.000.000 de lecturas" }
  - { id: r,   type: start,    text: "fila encontrada" }
edges:
  - { from: q,   to: d }
  - { from: d,   to: idx, label: "sí" }
  - { from: d,   to: seq, label: "no" }
  - { from: idx, to: r }
  - { from: seq, to: r }
:::

## Conectando la aplicación

```properties title="application.properties"
spring.datasource.url=jdbc:postgresql://localhost:5432/catalog
spring.datasource.username=postgres
spring.datasource.password=secreto

spring.jpa.hibernate.ddl-auto=validate
spring.jpa.show-sql=true
```

Y la dependencia en el `pom.xml`:

```xml title="pom.xml"
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
    <scope>runtime</scope>
</dependency>
```

:::pitfall
`spring.jpa.hibernate.ddl-auto=update` aparece en todo tutorial y **no debe
ir a producción**. Deja que Hibernate cambie el esquema por su cuenta:
renombrar un campo puede crear una columna nueva y dejar la vieja atrás con
los datos. En producción usa `validate` y haz los cambios con migraciones
versionadas (Flyway), tema del capítulo 42.
:::

## El SQL no se va a ir

El capítulo 20 trae JPA, que escribe SQL por ti. Eso no te exime de saber
SQL: te exime de **teclear** SQL. Cuando la consulta generada sea lenta,
cuando el log muestre mil consultas donde debería haber una (capítulo 30),
quien lee SQL lo resuelve en minutos y quien no lo lee cambia de framework.

:::term Transacción
Un conjunto de operaciones que ocurre entero o no ocurre. Si el `INSERT`
del pedido funciona y el del ítem falla, la transacción deshace los dos.
:::

:::summary
- Docker levanta un PostgreSQL descartable en un comando.
- `CREATE TABLE` declara reglas que la base garantiza: tipo, tamaño,
  obligatoriedad, unicidad.
- `INSERT`, `SELECT`, `UPDATE`, `DELETE` son el CRUD; `UPDATE` y `DELETE`
  sin `WHERE` son una catástrofe.
- La clave foránea garantiza la integridad incluso frente a cambios hechos
  fuera de la aplicación.
- El índice acelera la lectura y cuesta escritura: indexa lo que buscas.
:::

:::checkpoint
Levantas una base de datos, creas tablas con restricciones, escribes las
cuatro operaciones en SQL, creas un índice y conectas la aplicación Spring a
la base.
:::

:::milestone
El proyecto tiene dónde guardar: la tabla `product` existe y la aplicación
conoce la URL de la base. Falta traducir la clase Java en una fila de
tabla: el capítulo 20.
:::

:::exercise level=1
Crea la tabla `category` e inserta tres categorías. Después asocia dos
productos a categorías distintas con `UPDATE`.

:::answer
```sql
INSERT INTO category (name) VALUES ('Periféricos'), ('Monitores');
UPDATE product SET category_id = 1 WHERE id = 1;
```
Prueba ahora `UPDATE product SET category_id = 99 WHERE id = 1;` y lee el
error: `violates foreign key constraint`. La base acaba de impedir un dato
inconsistente que tu código Java ni sabía que estaba mal.
:::

:::exercise level=2
Escribe la consulta que devuelve el nombre de la categoría junto a cada
producto. Pista: `JOIN`.

:::answer
```sql
SELECT p.name AS producto, c.name AS categoria
FROM product p
JOIN category c ON c.id = p.category_id
ORDER BY c.name, p.name;
```
Un producto sin categoría **no aparece** en esa consulta. Para incluirlo,
usa `LEFT JOIN`, y esa diferencia de una palabra es el origen de la mitad de
los informes que "pierden" registros.
:::

:::exercise level=3
Descubre qué hace `EXPLAIN ANALYZE` y córrelo sobre la búsqueda por nombre
antes y después de crear el índice. Compara el tiempo y el tipo de
recorrido.

:::answer
Antes, el plan muestra `Seq Scan on product`: un recorrido secuencial.
Después, `Index Scan using idx_product_name`. En una tabla de un millón de
filas la diferencia suele ser de tres órdenes de magnitud. Saber leer un
plan de ejecución es la habilidad que separa a quien "optimiza a ojo" de
quien optimiza.
:::
