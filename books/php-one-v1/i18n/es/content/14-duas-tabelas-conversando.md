---
source_hash: 9277a9c032ff
title: "Dos tablas conversando"
number: 14
slug: duas-tabelas-conversando
part: p2
kicker: "Cuatro millones de filas leídas para devolver tres resultados. Desde 2011."
goal: >-
  Unir tablas con claves foráneas, responder preguntas que cruzan más de una
  con `JOIN` y `GROUP BY`, descubrir por qué una consulta es lenta con
  `EXPLAIN`, y grabar dos cosas o ninguna.
---

La tabla `prestamos` del capítulo anterior tiene una columna `lector_id` y
ninguna garantía de que el número guardado ahí corresponda a un lector que
exista. Nada impide grabar `lector_id = 99999` en una biblioteca con mil
doscientos lectores.

Y, una vez grabado, nadie lo descubre — hasta el día en que un informe
muestra un préstamo sin nombre.

## La unión que garantiza la base de datos

```sql
mysql> CREATE TABLE ejemplares (
    ->   id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
    ->   libro_id  INT UNSIGNED NOT NULL,
    ->   registro  INT UNSIGNED NOT NULL,
    ->   condicion VARCHAR(20)  NOT NULL DEFAULT 'bueno',
    ->   PRIMARY KEY (id),
    ->   UNIQUE KEY uk_ejemplares_registro (registro),
    ->   CONSTRAINT fk_ejemplares_libro
    ->     FOREIGN KEY (libro_id) REFERENCES libros (id)
    -> ) ENGINE=InnoDB;
Query OK, 0 rows affected (0.05 sec)
```

Las tres últimas líneas antes del paréntesis de cierre son la novedad.
Dicen: *la columna `libro_id` de esta tabla apunta a la columna `id` de la
tabla `libros`, y la base de datos se encarga de que eso siga siendo
verdad.*

Pruébalo:

```sql
mysql> INSERT INTO ejemplares (libro_id, registro)
    -> VALUES (99999, 5000);
ERROR 1452 (23000): Cannot add or update a child row: a foreign
key constraint fails (`casa_amarela`.`ejemplares`, CONSTRAINT
`fk_ejemplares_libro` FOREIGN KEY (`libro_id`) REFERENCES
`libros` (`id`))
```

La base lo rechazó. No hubo aviso, no hubo una fila grabada a medias, no
hubo un dato malo esperando ser descubierto en 2029.

Y la protección vale para los dos lados:

```sql
mysql> DELETE FROM libros WHERE id = 1;
ERROR 1451 (23000): Cannot delete or update a parent row: a
foreign key constraint fails
```

No se puede borrar un libro que tiene ejemplares. La base protege la unión
sin importar qué programa la esté tocando — incluido tú, en la terminal, a
las seis de la tarde.

:::term Integridad referencial
La garantía de que toda referencia apunta a algo que existe. Es lo que
separa una base de datos de un conjunto de planillas: la regla es de la
base, no del programa, y por eso vale para todos los programas a la vez —
incluido el script de importación que alguien escribió apurado.
:::

Se puede elegir qué pasa cuando se elimina el lado al que se apunta:

| Cláusula | Qué hace |
|---|---|
| `ON DELETE RESTRICT` | rechaza la eliminación (es el valor por defecto) |
| `ON DELETE CASCADE` | borra en cascada las filas que apuntaban |
| `ON DELETE SET NULL` | pone la columna en nulo, si acepta nulo |

Tabla: `CASCADE` resuelve un problema y crea otro mayor — borrar un libro
por error pasa a borrar en silencio todos sus ejemplares y todos sus
préstamos.

:::key
Usa `RESTRICT` por defecto, que es el valor por defecto. `CASCADE` solo
cuando la fila apuntada **no existe sin** la fila que apunta: el ítem de un
pedido no existe sin el pedido, y borrar el pedido puede llevárselo.

Un ejemplar no es de ese tipo. Es un objeto físico que sigue en el estante
aunque alguien borre el registro del título.
:::

:::pitfall
Una diferencia entre bases de datos que sale cara cuando se cambia de una a
otra: **en MySQL con InnoDB, crear una clave foránea crea automáticamente un
índice en la columna**, si todavía no lo hay. En PostgreSQL, no — y allí la
ausencia de ese índice es una de las causas más comunes de `DELETE` lentos,
porque cada eliminación tiene que recorrer la tabla hija entera buscando
referencias.

Si vienes de una y vas a la otra, revísalo.
:::

## El esquema entero

Con esto, el dominio de la Casa Amarela cabe en cuatro tablas:

```sql title="esquema.sql"
CREATE TABLE libros (
  id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
  titulo  VARCHAR(200) NOT NULL,
  autor   VARCHAR(150) NOT NULL,
  isbn    CHAR(13)     NULL,
  tema    VARCHAR(40)  NOT NULL,
  anio    SMALLINT     NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_libros_isbn (isbn)
) ENGINE=InnoDB;

CREATE TABLE ejemplares (
  id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
  libro_id  INT UNSIGNED NOT NULL,
  registro  INT UNSIGNED NOT NULL,
  condicion VARCHAR(20)  NOT NULL DEFAULT 'bueno',
  PRIMARY KEY (id),
  UNIQUE KEY uk_ejemplares_registro (registro),
  FOREIGN KEY (libro_id) REFERENCES libros (id)
) ENGINE=InnoDB;

CREATE TABLE lectores (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nombre        VARCHAR(120) NOT NULL,
  documento     CHAR(11)     NOT NULL,
  registrado_en DATE         NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_lectores_documento (documento)
) ENGINE=InnoDB;

CREATE TABLE prestamos (
  id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  ejemplar_id       INT UNSIGNED NOT NULL,
  lector_id         INT UNSIGNED NOT NULL,
  retirado_en       DATETIME     NOT NULL,
  devolver_hasta    DATE         NOT NULL,
  devuelto_en       DATETIME     NULL,
  multa_en_centavos INT UNSIGNED NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (ejemplar_id) REFERENCES ejemplares (id),
  FOREIGN KEY (lector_id) REFERENCES lectores (id)
) ENGINE=InnoDB;
```

Fíjate en lo que **no** existe aquí: no hay una columna `cantidad` en
`libros`, ni una columna `disponible` en `ejemplares`. Las dos se pueden
calcular a partir de `prestamos`, y un número calculado no diverge de la
realidad.

:::key
La regla de orden que sigue el esquema de arriba tiene un nombre pomposo —
*normalización* — y tres preguntas prácticas:

1. **¿Cada columna guarda una sola cosa?** Un campo `autor` con
	 `"Machado de Assis; Aluísio Azevedo"` guarda dos, y ninguna consulta va a
	 poder separarlos de forma confiable.
2. **¿Cada tabla habla de un solo tema?** Si `prestamos` tuviera
	 `lector_nombre`, el nombre pasaría a existir en dos lugares y
	 divergirían con la primera corrección de ortografía.
3. **¿Nada de lo guardado se puede calcular?** `cantidad` se puede. Fuera.

Responder que sí a las tres cubre la aplastante mayoría de los casos. El
resto de la teoría existe y rara vez cambia una decisión práctica.
:::

## La pregunta que involucra dos tablas

El esquema está ordenado y creó un problema: el título del libro ya no está
en la misma tabla que el ejemplar. Para listar ejemplares con título, hay
que juntar las dos.

```sql
mysql> SELECT e.registro, l.titulo
    -> FROM ejemplares e
    -> JOIN libros l ON l.id = e.libro_id;
+----------+---------------+
| registro | titulo        |
+----------+---------------+
|      812 | O Cortiço     |
|      907 | O Cortiço     |
|      344 | Vidas Secas   |
|     1120 | Grande Sertão |
+----------+---------------+
4 rows in set (0.00 sec)
```

Léelo desde el `FROM`: *empieza por los ejemplares, y para cada uno
encuentra el libro cuyo `id` sea igual al `libro_id` del ejemplar.*

La `e` y la `l` después de los nombres de tabla son **alias**. Existen para
que `e.registro` y `l.titulo` digan de qué tabla vino cada columna — lo que
deja de ser una comodidad y pasa a ser una obligación cuando dos tablas
tienen columnas con el mismo nombre, como `id`.

El `ON` es la condición de la unión, y es la parte que nadie puede olvidar:

:::pitfall
Un `JOIN` sin `ON` — o con un `ON` que no une nada — produce el **producto
cartesiano**: cada fila de un lado combinada con cada fila del otro.

Con 8.000 ejemplares y 4.000 libros, eso son 32 millones de filas. El
comando no da error. Empieza a devolver resultados, y la máquina se
detiene.

Cuando una consulta que debería traer decenas traiga millones, mira el `ON`
antes que cualquier otra cosa.
:::

Tres tablas siguen la misma forma:

```sql
mysql> SELECT l.titulo, le.nombre, pr.devolver_hasta
    -> FROM prestamos pr
    -> JOIN ejemplares e ON e.id = pr.ejemplar_id
    -> JOIN libros l ON l.id = e.libro_id
    -> JOIN lectores le ON le.id = pr.lector_id
    -> WHERE pr.devuelto_en IS NULL
    -> ORDER BY pr.devolver_hasta;
+---------------+------------------+----------------+
| titulo        | nombre           | devolver_hasta |
+---------------+------------------+----------------+
| O Cortiço     | Marlene Coutinho | 2027-02-18     |
| Grande Sertão | Juvenal Pereira  | 2027-02-24     |
+---------------+------------------+----------------+
2 rows in set (0.00 sec)
```

Esa es la lista de pendientes de Vera, en una sola consulta, sin ningún
bucle. Es literalmente el informe que tardaba cuatro décimas de segundo
recorriendo listas en memoria, ahora hecho por la base de datos — que fue
construida para eso y no se vuelve más lenta cuando la biblioteca crezca.

## La fila que no tiene par

```sql
mysql> SELECT l.titulo, COUNT(e.id) AS ejemplares
    -> FROM libros l
    -> JOIN ejemplares e ON e.libro_id = l.id
    -> GROUP BY l.id, l.titulo;
```

Esta consulta tiene un defecto silencioso: los libros **sin ningún
ejemplar** no aparecen. El `JOIN` solo devuelve filas que encontraron par
de los dos lados, y un libro recién registrado, cuyos ejemplares todavía no
llegaron, simplemente desaparece del informe.

El arreglo es una palabra:

```sql
mysql> SELECT l.titulo, COUNT(e.id) AS ejemplares
    -> FROM libros l
    -> LEFT JOIN ejemplares e ON e.libro_id = l.id
    -> GROUP BY l.id, l.titulo
    -> ORDER BY ejemplares DESC;
+--------------------+------------+
| titulo             | ejemplares |
+--------------------+------------+
| O Cortiço          |          2 |
| Vidas Secas        |          1 |
| Grande Sertão      |          1 |
| O Pequeno Príncipe |          0 |
+--------------------+------------+
4 rows in set (0.00 sec)
```

`LEFT JOIN` trae **todas** las filas de la tabla de la izquierda, tengan
par o no. Cuando no lo tienen, las columnas del lado derecho vienen nulas.

:::key
La diferencia entre `JOIN` y `LEFT JOIN` no es técnica, es de pregunta.

`JOIN` responde *"¿qué pares existen?"*. `LEFT JOIN` responde *"¿qué tiene
la tabla de la izquierda, con lo que haya de la derecha?"*.

El error clásico es usar `JOIN` cuando la pregunta era la segunda — y el
síntoma es un informe al que le faltan exactamente las filas más
interesantes: el libro sin ejemplares, el lector que nunca se llevó nada, el
mes sin movimiento.
:::

Fíjate en el `COUNT(e.id)` y no `COUNT(*)`. En un `LEFT JOIN`, la fila del
libro sin ejemplares existe, así que `COUNT(*)` contaría `1`. `COUNT(e.id)`
ignora los nulos y devuelve `0`, que es la respuesta correcta.

## Agrupar para contar

```sql
mysql> SELECT l.tema,
    ->        COUNT(*) AS prestamos
    -> FROM prestamos pr
    -> JOIN ejemplares e ON e.id = pr.ejemplar_id
    -> JOIN libros l ON l.id = e.libro_id
    -> WHERE pr.retirado_en >= '2027-02-01'
    ->   AND pr.retirado_en <  '2027-03-01'
    -> GROUP BY l.tema
    -> ORDER BY prestamos DESC;
+------------+-----------+
| tema       | prestamos |
+------------+-----------+
| infantil   |       214 |
| literatura |       188 |
| referencia |        12 |
+------------+-----------+
3 rows in set (0.01 sec)
```

`GROUP BY` junta las filas que tienen el mismo valor en la columna indicada
y produce **una fila por grupo**. Las funciones de agregación — `COUNT`,
`SUM`, `AVG`, `MIN`, `MAX` — operan dentro de cada grupo.

Esa es la respuesta que pide la rendición de cuentas de la subvención, y
reemplaza el programa PHP de tres bucles anidados del capítulo
@cap:repeticoes por nueve líneas que la base de datos resuelve en centésimas
de segundo.

Fíjate también en el filtro de fechas: `>= '2027-02-01' AND < '2027-03-01'`,
en lugar de `BETWEEN '2027-02-01' AND '2027-02-28'`. La segunda forma pierde
los préstamos del día 28 después de las 00:00, porque la columna es
`DATETIME` y `'2027-02-28'` significa medianoche en punto. El intervalo
semiabierto — incluye el inicio, excluye el final — no tiene ese problema y
ni siquiera necesita saber cuántos días tiene el mes.

:::pitfall
Para filtrar **después** de agrupar, el `WHERE` no sirve: se ejecuta antes
del `GROUP BY` y no ve el resultado del conteo. Para eso existe `HAVING`:

```sql
GROUP BY l.tema
HAVING COUNT(*) > 50
```

La regla: `WHERE` filtra filas, `HAVING` filtra grupos. Poner
`COUNT(*) > 50` en el `WHERE` da error; poner `tema = 'infantil'` en el
`HAVING` funciona y es más lento, porque la base agrupa todo para después
tirarlo.
:::

## Cuatro millones de filas

:::story La búsqueda de 2011
— ¿Cuánto tarda la búsqueda del Sistema? — preguntó Márcia.

— Depende — dijo Vera.

— ¿De qué?

— De la hora. A la mañana es rápida. Después del almuerzo se traba.

Dedé pidió la consulta. Nonato la recordaba de memoria:

```sql
SELECT * FROM libros WHERE titulo LIKE '%sertao%'
```

La ejecutó con una palabra delante:

```text
mysql> EXPLAIN SELECT * FROM libros
    -> WHERE titulo LIKE '%sertao%';
+------+------+------+-------------+
| type | key  | rows | Extra       |
+------+------+------+-------------+
| ALL  | NULL | 4000 | Using where |
+------+------+------+-------------+
```

— `type: ALL` — dijo. — Lee la tabla entera.

— ¿Cuatro mil filas es mucho?

— Para un libro, no. El problema es `ejemplares`, que hace lo mismo con ocho
mil, y `prestamos`, con cuatrocientos mil desde 2009. Cada búsqueda suma.

Márcia lo anotó.

— ¿Y después del almuerzo?

— Después del almuerzo hay quince personas usándolo al mismo tiempo.
:::

`EXPLAIN` delante de cualquier `SELECT` muestra el plan de ejecución: lo que
la base pretende hacer antes de hacerlo. La salida real tiene doce columnas;
las cuatro de arriba son las que deciden casi todo.

| Columna | Qué significa |
|---|---|
| `type` | cómo se alcanzan las filas. `ALL` es un recorrido completo |
| `key` | qué índice se usó. `NULL` es ninguno |
| `rows` | cuántas filas estima la base que va a **leer** |
| `Extra` | avisos, entre ellos `Using filesort` y `Using temporary` |

Tabla: La lectura rápida: `type: ALL` con `rows` alto es una consulta que
va a empeorar sola a medida que la tabla crezca.

Un **índice** es una estructura aparte que la base mantiene ordenada, para
no tener que recorrerlo todo. Es la diferencia entre buscar una palabra
hojeando el libro entero y buscarla en el índice alfabético del final.

```sql
mysql> CREATE INDEX idx_prestamos_lector
    -> ON prestamos (lector_id);
Query OK, 0 rows affected (0.09 sec)

mysql> EXPLAIN SELECT * FROM prestamos WHERE lector_id = 47;
+------+----------------------+------+
| type | key                  | rows |
+------+----------------------+------+
| ref  | idx_prestamos_lector |    7 |
+------+----------------------+------+
```

De 400.000 filas leídas a 7. El `type` pasó de `ALL` a `ref`, y la consulta
pasó a costar lo mismo con cuatrocientos mil o con cuatro millones de
préstamos.

Pero fíjate en lo que el índice **no** arregla: la búsqueda de Nonato sigue
leyéndolo todo.

```sql
mysql> CREATE INDEX idx_libros_titulo ON libros (titulo);

mysql> EXPLAIN SELECT * FROM libros WHERE titulo LIKE '%sertao%';
+------+------+------+
| type | key  | rows |
+------+------+------+
| ALL  | NULL | 4000 |
+------+------+------+
```

El índice existe y no se usó. El motivo es la posición del `%`: un índice
guarda los valores **ordenados**, y el orden solo ayuda a quien sabe el
principio de la palabra. `LIKE 'sertao%'` usa el índice; `LIKE '%sertao%'`
no puede usarlo, porque el fragmento buscado puede estar en cualquier
posición.

:::key
Un índice acelera la lectura y **cuesta en la escritura**: cada `INSERT`,
`UPDATE` y `DELETE` tiene que actualizar todos los índices de la tabla. Una
tabla con ocho índices graba sensiblemente más despacio que la misma tabla
con dos.

La regla práctica: crea índices para las columnas que aparecen en `WHERE`,
en `JOIN` y en `ORDER BY` de consultas que se ejecutan mucho. No los crees
por precaución. Y comprueba con `EXPLAIN` si se está usando — un índice
creado e ignorado es lo peor de los dos mundos: cuesta en la escritura y no
paga en la lectura.
:::

Para buscar un fragmento en medio del texto, el camino en MySQL es otro: un
índice `FULLTEXT`, que indexa palabras en lugar de valores enteros. Es la
salida para la búsqueda de Vera, y combina con la clave de búsqueda
normalizada del capítulo @cap:strings — el índice encuentra la palabra, la
normalización garantiza que "SERTAO" y "Sertão" sean la misma palabra.

## Todo o nada

Registrar un préstamo son dos grabaciones: la fila en `prestamos` y el
cambio de condición del ejemplar. Si la primera funciona y la segunda
falla, el sistema queda con un préstamo cuyo ejemplar sigue marcado como
disponible — y alguien presta el mismo libro dos veces.

```sql
mysql> START TRANSACTION;
Query OK, 0 rows affected (0.00 sec)

mysql> INSERT INTO prestamos
    ->   (ejemplar_id, lector_id, retirado_en, devolver_hasta)
    -> VALUES (1, 1, NOW(), '2027-02-18');
Query OK, 1 row affected (0.00 sec)

mysql> UPDATE ejemplares SET condicion = 'prestado' WHERE id = 1;
Query OK, 1 row affected (0.00 sec)

mysql> COMMIT;
Query OK, 0 rows affected (0.01 sec)
```

Entre el `START TRANSACTION` y el `COMMIT`, nada de lo hecho existe para los
otros programas. En el `COMMIT`, todo pasa a existir de una vez. Y si algo
sale mal en el medio:

```sql
mysql> ROLLBACK;
```

La base deshace todo lo que ocurrió desde el `START TRANSACTION`, como si no
se hubiera tecleado nada.

:::term Transacción
Un conjunto de operaciones tratado como una sola: o pasan todas, o no pasa
ninguna. Es lo que impide que una falla en medio de una secuencia deje la
base en un estado que la regla de negocio prohíbe.

Es también la respuesta definitiva a la carrera del capítulo
@cap:do-arquivo-ao-banco: mientras una transacción toca una fila, las otras
esperan por esa fila — y no por el archivo entero.
:::

:::warning
MySQL, por defecto, corre en *autocommit*: cada comando es una transacción
por sí solo, confirmada en el momento. Eso significa que, sin
`START TRANSACTION`, el `UPDATE` sin `WHERE` del viernes de Nonato **ya
estaba confirmado** en el instante en que apretó Enter. No había nada que
deshacer.

Con una transacción abierta, lo habría habido — y `ROLLBACK` habría salvado
el viernes. Vale como argumento práctico para abrir una transacción en
cualquier cambio manual que hagas en producción, aunque sea de una sola
línea.
:::

:::note En tu carrera
"Depende de la hora" es el tipo de reporte que suele descartarse como
impresión, y casi siempre es la información más valiosa del pedido.

Vera no sabía decir "la consulta hace un recorrido completo y la contención
aparece con concurrencia". Sabía decir que a la mañana era rápido y después
del almuerzo se trababa — que es exactamente la misma frase, en el lenguaje
de quien lo usa.

Cuando alguien describa un problema por **cuándo** ocurre, en lugar de por
**qué** ocurre, anota el cuándo. Horario, día del mes, fin de semana,
cierre: esos patrones apuntan a carga, a tareas programadas o a volumen
acumulado, y son la mitad del diagnóstico que no está en el código.
:::

:::summary
- Una clave foránea hace que la base garantice que toda referencia apunta a
	algo que existe — para todos los programas, no solo el tuyo.
- `RESTRICT` por defecto; `CASCADE` solo cuando el hijo no existe sin el
	padre.
- `JOIN` trae los pares; `LEFT JOIN` trae todo lo de la izquierda, con nulo
	donde no haya par.
- `JOIN` sin `ON` produce un producto cartesiano, sin ningún error.
- `GROUP BY` produce una fila por grupo; `WHERE` filtra filas, `HAVING`
	filtra grupos.
- Un intervalo de fechas semiabierto (`>=` y `<`) evita perder el último
	día.
- `EXPLAIN` muestra el plan: `type: ALL` con `rows` alto es un recorrido
	completo.
- Un índice acelera la lectura y cuesta en la escritura; `LIKE '%termino%'`
	no usa un índice común.
- Una transacción vuelve una sola dos grabaciones; sin ella, MySQL confirma
	todo en el momento.
:::

:::milestone
El dominio de la Casa Amarela existe en cuatro tablas unidas, con las reglas
garantizadas por la base de datos. Las cinco preguntas que hizo Vera en el
mostrador pasaron a tener una respuesta de una línea cada una.
:::

:::exercise level=1
Escribe la consulta que lista, para cada ejemplar, el número de registro, el
título del libro y la condición — ordenada por título. Después cámbiala para
mostrar solo los ejemplares en restauración.

:::answer
```sql
SELECT e.registro, l.titulo, e.condicion
FROM ejemplares e
JOIN libros l ON l.id = e.libro_id
ORDER BY l.titulo;

SELECT e.registro, l.titulo, e.condicion
FROM ejemplares e
JOIN libros l ON l.id = e.libro_id
WHERE e.condicion = 'restauracion'
ORDER BY l.titulo;
```

El `JOIN` es el correcto aquí, y no el `LEFT JOIN`: todo ejemplar tiene un
libro, y la clave foránea lo garantiza. Donde la unión es obligatoria, los
dos devuelven el mismo resultado — y el `JOIN` le dice a quien lee que la
obligatoriedad existe.
:::

:::exercise level=2
Las cinco preguntas que Vera hizo en el mostrador eran: qué ejemplar tiene
Dona Marlene, cuál está roto, cuál desapareció, cuántos están libres, y
cuáles fueron los más prestados del mes. Escribe las cinco consultas.

:::answer
```sql
-- 1. qué ejemplar tiene Dona Marlene
SELECT e.registro, l.titulo, pr.devolver_hasta
FROM prestamos pr
JOIN ejemplares e ON e.id = pr.ejemplar_id
JOIN libros l ON l.id = e.libro_id
JOIN lectores le ON le.id = pr.lector_id
WHERE le.nombre = 'Marlene Coutinho'
  AND pr.devuelto_en IS NULL;

-- 2. cuáles están rotos
SELECT e.registro, l.titulo
FROM ejemplares e
JOIN libros l ON l.id = e.libro_id
WHERE e.condicion = 'danado';

-- 3. cuáles desaparecieron
SELECT e.registro, l.titulo
FROM ejemplares e
JOIN libros l ON l.id = e.libro_id
WHERE e.condicion = 'extraviado';

-- 4. cuántos ejemplares de este libro están libres
SELECT COUNT(*) AS libres
FROM ejemplares e
LEFT JOIN prestamos pr
  ON pr.ejemplar_id = e.id AND pr.devuelto_en IS NULL
WHERE e.libro_id = 1
  AND e.condicion = 'bueno'
  AND pr.id IS NULL;

-- 5. los más prestados del mes
SELECT l.titulo, COUNT(*) AS veces
FROM prestamos pr
JOIN ejemplares e ON e.id = pr.ejemplar_id
JOIN libros l ON l.id = e.libro_id
WHERE pr.retirado_en >= '2027-02-01'
  AND pr.retirado_en <  '2027-03-01'
GROUP BY l.id, l.titulo
ORDER BY veces DESC
LIMIT 10;
```

La cuarta es la más interesante, y merece atención.

Usa `LEFT JOIN` con la condición de "abierto" **dentro del `ON`**, y
después filtra `pr.id IS NULL` en el `WHERE`. Ese es el idioma para "trae lo
que **no** tiene par": el `LEFT JOIN` trae todos los ejemplares, con el
préstamo abierto cuando lo haya, y el `IS NULL` se queda solo con los que no
tienen ninguno.

Si la condición `devuelto_en IS NULL` fuera al `WHERE` en lugar del `ON`,
eliminaría justamente las filas sin par — y la consulta devolvería cero
siempre.

Y fíjate en que la quinta responde la pregunta del capítulo
@cap:o-que-vamos-construir: cuenta por **libro**, agrupando los préstamos de
todos los ejemplares de ese título. Contar por ejemplar sería
`GROUP BY e.id`, y respondería otra cosa.
:::

:::exercise level=3
La operación de devolución hace tres cosas: graba la fecha en `prestamos`,
calcula la multa, y cambia la condición del ejemplar a disponible.
Escríbela como transacción y responde: ¿qué pasa si la conexión se cae
entre la segunda y la tercera? ¿Y qué pasaría sin la transacción?

:::answer
```sql
START TRANSACTION;

UPDATE prestamos
SET devuelto_en = NOW(),
    multa_en_centavos = 720
WHERE id = 3315
  AND devuelto_en IS NULL;

UPDATE ejemplares
SET condicion = 'bueno'
WHERE id = (SELECT ejemplar_id FROM prestamos WHERE id = 3315);

COMMIT;
```

**Si la conexión se cae antes del `COMMIT`**, la base lo deshace todo sola.
No existe un estado intermedio: el préstamo sigue abierto, el ejemplar sigue
prestado, y la devolución se puede rehacer desde el principio. La atención
repite la operación y nadie se entera.

**Sin la transacción**, cada `UPDATE` se confirma en el instante en que
corre. La caída entre los dos deja la base en un estado que la regla de
negocio prohíbe: préstamo devuelto, ejemplar marcado como prestado. El libro
vuelve al estante y el sistema se niega a prestarlo de nuevo, para siempre,
hasta que alguien lo descubra y lo corrija a mano.

Ese estado es peor que la falla entera, por un motivo que vale la pena
guardar: **la falla avisa, el estado inconsistente no.** La operación que
se cae en el medio muestra un error en pantalla y alguien la repite. La que
graba a medias termina diciendo "devuelto con éxito".

Dos observaciones sobre la consulta.

El `AND devuelto_en IS NULL` del primer `UPDATE` no es decoración: impide
que una devolución registrada dos veces sobrescriba la fecha original y
recalcule la multa. Cuando `Rows matched` venga en `0`, es porque alguien ya
la devolvió.

Y la multa aparece aquí como un número ya calculado, lo que es una
simplificación: depende de `devolver_hasta`, de la fecha de hoy y de la
regla vigente. Calcular reglas de negocio dentro del SQL es posible y casi
siempre indeseable — el cálculo vive en PHP, que es donde se puede
verificar línea por línea.
:::
