---
source_hash: 7df1dd3c4dd5
title: "SQL: las cinco frases que resuelven el día"
number: 13
slug: sql-do-zero
part: p2
kicker: "Un UPDATE sin WHERE un viernes devolvió ocho mil libros que nadie había devuelto."
goal: >-
  Crear una tabla eligiendo el tipo de cada columna con criterio, insertar,
  consultar con filtro y orden, y cambiar exactamente las filas que quisiste
  cambiar.
---

:::story Nonato volvió
Nonato volvió de vacaciones un lunes, y a las 9:40 estaba en una sala con
cuatro personas y un proyector que mostraba la estructura de la base de
datos de la Casa Amarela.

La había escrito en 2009, en un fin de semana, a los veintitrés años, por
mil doscientos reales.

— Esta columna de aquí — dijo Tainá, señalando. — `devolvido`. ¿Es solo un
cero o un uno?

— Sí.

— ¿Y la fecha de devolución dónde queda?

Nonato miró la pantalla un rato.

— No queda.

— ¿Y si alguien pregunta cuándo volvió un libro?

— Nadie lo preguntó en quince años.

Márcia, sin levantar los ojos:

— La rendición de cuentas de la subvención pide el movimiento del acervo
por mes.

Nonato volvió a mirar la pantalla, más tiempo esta vez.

— Entonces ahora alguien lo preguntó.
:::

Un campo que guarda "sí o no" cuesta un byte y tira la fecha. Un campo que
guarda la fecha cuesta tres bytes y responde las dos preguntas: quien tiene
fecha devolvió; quien no la tiene, no devolvió.

Esa decisión de dos bytes es el tema de este capítulo. Se llama **elegir el
tipo de la columna**, ocurre una vez, y la Casa Amarela convivió quince años
con la versión equivocada.

## Diseñar la ficha antes de completarla

```sql
mysql> USE casa_amarela;
Database changed

mysql> CREATE TABLE libros (
    ->   id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    ->   titulo  VARCHAR(200) NOT NULL,
    ->   autor   VARCHAR(150) NOT NULL,
    ->   isbn    CHAR(13)     NULL,
    ->   tema    VARCHAR(40)  NOT NULL,
    ->   anio    SMALLINT     NULL,
    ->   PRIMARY KEY (id),
    ->   UNIQUE KEY uk_libros_isbn (isbn)
    -> ) ENGINE=InnoDB;
Query OK, 0 rows affected (0.04 sec)
```

Diez líneas que deciden muchas cosas. Vale la pena desarmarlas en cuatro
partes.

**El nombre y la lista de columnas.** `CREATE TABLE libros` crea el fajo de
fichas; cada línea dentro de los paréntesis es un campo impreso en la
ficha, con nombre y tipo.

**`NOT NULL` y `NULL`.** `NOT NULL` significa "esta columna nunca puede
quedar en blanco" — la base rechaza la grabación. `NULL` significa "puede
quedar en blanco", y es una afirmación sobre el negocio: no todo libro tiene
ISBN, porque el ISBN solo existe desde 1970 y la Casa Amarela tiene
ediciones anteriores.

**`PRIMARY KEY (id)`.** Una columna que identifica la fila, sin repetirse y
sin quedar vacía. Es el número de registro del papel, ascendido a regla de
la base de datos.

**`UNIQUE KEY`.** Dice que no puede haber dos filas con el mismo ISBN. Es
distinto de la clave primaria: una tabla tiene una clave primaria y puede
tener tantas restricciones de unicidad como quiera.

:::term DDL y DML
Los comandos SQL se dividen en dos familias. **DDL** (*Data Definition
Language*) toca la estructura: `CREATE`, `ALTER`, `DROP`. **DML** (*Data
Manipulation Language*) toca los datos: `INSERT`, `SELECT`, `UPDATE`,
`DELETE`.

La diferencia práctica es que el DDL es caro de deshacer y el DML no. Crear
una tabla equivocada cuesta una tarde; insertar una fila equivocada cuesta
un `DELETE`.
:::

El `AUTO_INCREMENT` hace que la base asigne sola el próximo número libre:
insertas un libro sin informar `id` y se vuelve 1, el próximo se vuelve 2.
Eso ahorra la pregunta "¿cuál fue el último?", que en un sistema con dos
encargadas es de nuevo la carrera del capítulo @cap:do-arquivo-ao-banco.

Y el `ENGINE=InnoDB` del final elige el motor de almacenamiento. Es el que
viene por defecto en MySQL 8 y es el que quieres: es el único que hace
transacciones y garantiza claves foráneas. Escribirlo explícitamente cuesta
doce caracteres y evita heredar el valor por defecto de un servidor viejo.

Para revisar lo que quedó grabado:

```sql
mysql> DESCRIBE libros;
+--------+--------------+------+-----+---------+----------------+
| Field  | Type         | Null | Key | Default | Extra          |
+--------+--------------+------+-----+---------+----------------+
| id     | int unsigned | NO   | PRI | NULL    | auto_increment |
| titulo | varchar(200) | NO   |     | NULL    |                |
| autor  | varchar(150) | NO   |     | NULL    |                |
| isbn   | char(13)     | YES  | UNI | NULL    |                |
| tema   | varchar(40)  | NO   |     | NULL    |                |
| anio   | smallint     | YES  |     | NULL    |                |
+--------+--------------+------+-----+---------+----------------+
6 rows in set (0.00 sec)
```

`DESCRIBE` muestra la estructura de una tabla. Es el primer comando que hay
que ejecutar cuando abres una base de datos que no conoces — antes de leer
cualquier código.

## El tipo es una decisión de negocio

La elección de cada tipo fue deliberada, y cada una responde una pregunta
sobre la Casa Amarela.

| Tipo | Guarda | Cuándo usarlo |
|---|---|---|
| `INT` | entero hasta ~2.100 millones | identificador, conteo, centavos |
| `SMALLINT` | entero hasta 32.767 | año, cantidad pequeña |
| `VARCHAR(n)` | texto de tamaño variable, hasta `n` | título, nombre, dirección |
| `CHAR(n)` | texto de tamaño **fijo** | ISBN, código de provincia, código de tamaño conocido |
| `TEXT` | texto largo, sin límite práctico | observación, descripción |
| `DATE` | solo la fecha | fecha de publicación, plazo |
| `DATETIME` | fecha y hora | cuándo ocurrió el préstamo |
| `DECIMAL(p,s)` | número exacto con decimales | valor monetario |
| `BOOLEAN` | verdadero o falso | alias de `TINYINT(1)` |

Tabla: No hay `FLOAT` en esta lista a propósito. Existe y sirve para medidas
físicas — peso, temperatura, coordenadas — y nunca para dinero, por el
motivo del capítulo @cap:conversao-automatica.

Cuatro de esas elecciones merecen explicación, porque es donde la gente se
equivoca.

**`VARCHAR(200)` y no `VARCHAR(255)`.** El número 255 se volvió costumbre
por un motivo histórico que ya no existe: hasta MySQL 5.0, un `VARCHAR` de
hasta 255 caracteres usaba un byte menos de control. Hoy eso no cambia nada
en disco, y el número que escribes pasó a ser lo que parece ser: una
**afirmación sobre el negocio**. `VARCHAR(200)` dice "un título de libro no
pasa de doscientos caracteres". Si pasa, la base lo rechaza — y está bien
que lo rechace, porque un título de ochocientos caracteres es casi siempre
un error de importación.

**`CHAR(13)` para el ISBN.** El ISBN tiene trece dígitos, siempre. `CHAR` es
para tamaño fijo y es ligeramente más eficiente en ese caso. Y fíjate en que
es texto, no número: un ISBN puede empezar con cero, y el cero a la
izquierda muere en una columna numérica.

**`DATETIME` y no `TIMESTAMP`.** Los dos guardan fecha y hora. La diferencia
es que `TIMESTAMP` convierte a UTC al grabar y vuelve a convertir al leer,
usando la zona horaria configurada en el servidor — lo que es excelente
para un sistema internacional y es una trampa cuando alguien cambia la
configuración del servidor y todas las fechas viejas cambian de valor.
`DATETIME` guarda lo que mandaste. Para una biblioteca de barrio,
`DATETIME` es más previsible.

**`DECIMAL(10,2)` para dinero, si usas dinero en la base.** Guarda el número
en base decimal, exacto, con diez dígitos en total y dos después de la coma.
Es la elección correcta cuando el valor vive en la base de datos.

:::pitfall
Hay un detalle de PHP que decide esta elección y casi nunca se menciona: una
columna `DECIMAL` **vuelve a PHP como string**. PHP no tiene un tipo decimal
exacto, así que el driver devuelve `"7.20"` en lugar de un número — porque
convertirlo a `float` desharía la exactitud que la columna garantizaba.

Eso significa que tienes que decidir qué hacer con ese string en cada lugar
donde aparece. La alternativa es guardar `INT` en centavos, que vuelve como
entero y cierra la cuenta de los dos lados. Es la elección de este libro, y
la columna se llama `multa_en_centavos`.

`DECIMAL` sigue siendo correcto — en un sistema financiero serio es lo que
se usa, con una clase que trata el string. La elección aquí es por
coherencia, no por superioridad.
:::

:::key
La regla que evita la mayor parte de los problemas de esquema: **`NOT NULL`
por defecto, `NULL` por excepción justificada.**

Toda columna empieza con prohibido quedar vacía. Cuando quieras permitirlo,
detente y escribe en una frase por qué ese dato puede no existir. "No todo
libro tiene ISBN" es una justificación. "Por si algún día falta" no lo es —
ese es el camino hacia una tabla en que la mitad de las columnas acepta nulo
y ninguna consulta puede confiar en nada.
:::

## Insertar

```sql
mysql> INSERT INTO libros (titulo, autor, isbn, tema, anio)
    -> VALUES ('O Cortiço', 'Aluísio Azevedo', '9788572326972',
    ->         'literatura', 1890);
Query OK, 1 row affected (0.01 sec)
```

La lista de columnas va primero, los valores después, en el mismo orden. El
`id` no se informó porque de eso se ocupa el `AUTO_INCREMENT`.

El texto va entre **comillas simples**. El número va sin comillas. Es la
única regla de formato que necesitas guardar ahora, y es la misma que va a
causar el problema de seguridad del próximo capítulo.

Varias filas a la vez:

```sql
mysql> INSERT INTO libros (titulo, autor, tema, anio) VALUES
    ->   ('Vidas Secas', 'Graciliano Ramos', 'literatura', 1938),
    ->   ('Grande Sertão', 'Guimarães Rosa', 'literatura', 1956),
    ->   ('O Pequeno Príncipe', 'Saint-Exupéry', 'infantil', 1943);
Query OK, 3 rows affected (0.01 sec)
Records: 3  Duplicates: 0  Warnings: 0
```

Tres filas en un solo comando. Fíjate en que se omitió `isbn`: como la
columna acepta `NULL`, la base graba nulo sin quejarse. Si omitieras
`titulo`, que es `NOT NULL`, la historia sería otra:

```sql
mysql> INSERT INTO libros (autor, tema) VALUES ('Alguien', 'general');
ERROR 1364 (HY000): Field 'titulo' doesn't have a default value
```

Ese rechazo es el trabajo del esquema a la vista. El error vino en el
momento de la grabación, con el nombre de la columna, y no seis meses
después en una pantalla que muestra un título en blanco.

## Consultar

```sql
mysql> SELECT id, titulo, anio FROM libros;
+----+--------------------+------+
| id | titulo             | anio |
+----+--------------------+------+
|  1 | O Cortiço          | 1890 |
|  2 | Vidas Secas        | 1938 |
|  3 | Grande Sertão      | 1956 |
|  4 | O Pequeno Príncipe | 1943 |
+----+--------------------+------+
4 rows in set (0.00 sec)
```

`SELECT` elige las columnas, `FROM` elige la tabla. Existe `SELECT *`, que
trae todas las columnas, y es cómodo en la terminal y malo en un programa:
cuando alguien agregue una columna `TEXT` de observaciones, tu programa
pasa a traerla en cada consulta sin usarla nunca.

Y existe el `WHERE`, que es donde la consulta empieza a valer algo:

```sql
mysql> SELECT titulo, anio FROM libros
    -> WHERE tema = 'literatura' AND anio > 1900;
+---------------+------+
| titulo        | anio |
+---------------+------+
| Vidas Secas   | 1938 |
| Grande Sertão | 1956 |
+---------------+------+
2 rows in set (0.00 sec)
```

El `WHERE` es la línea que decide qué filas entran. Acepta las
comparaciones de siempre — `=`, `<>`, `>`, `<`, `>=`, `<=` — y otras tres
que vale conocer:

```sql
mysql> SELECT titulo FROM libros WHERE titulo LIKE '%Sert%';
mysql> SELECT titulo FROM libros WHERE anio BETWEEN 1930 AND 1950;
mysql> SELECT titulo FROM libros
    -> WHERE tema IN ('infantil', 'juvenil');
mysql> SELECT titulo FROM libros WHERE isbn IS NULL;
```

`LIKE` busca un fragmento de texto, con `%` valiendo por "cualquier cosa".
`BETWEEN` es un atajo para dos comparadores. `IN` es un atajo para varios
`OR`.

Y la última es la que atrapa a todos: para comparar con nulo, **no** se usa
`= NULL`. Se usa `IS NULL`. El motivo es que, en SQL, `NULL` no es un valor
— es la ausencia de valor —, y la comparación `algo = NULL` no devuelve ni
verdadero ni falso: devuelve desconocido, y el `WHERE` descarta lo
desconocido junto con lo falso.

:::pitfall
Escribe `SELECT ... WHERE isbn = NULL` y MySQL no da ningún error. Devuelve
cero filas, callado, aunque haya tres libros sin ISBN.

Es el peor tipo de defecto: sintaxis válida, ejecución sin aviso, respuesta
equivocada. Cuando una consulta devuelva cero filas y estés seguro de que
debería devolver alguna, el `= NULL` es el primer sospechoso.
:::

Ordenar, contar y limitar:

```sql
mysql> SELECT titulo, anio FROM libros
    -> ORDER BY anio DESC
    -> LIMIT 2;
+--------------------+------+
| titulo             | anio |
+--------------------+------+
| Grande Sertão      | 1956 |
| O Pequeno Príncipe | 1943 |
+--------------------+------+
2 rows in set (0.00 sec)

mysql> SELECT COUNT(*) FROM libros WHERE tema = 'literatura';
+----------+
| COUNT(*) |
+----------+
|        3 |
+----------+
1 row in set (0.00 sec)
```

`ORDER BY` ordena — `ASC` es ascendente y es el valor por defecto, `DESC` es
descendente. `LIMIT` corta el resultado. `COUNT(*)` cuenta filas sin
traerlas, que es la diferencia entre preguntar "¿cuántos son?" y cargar
ocho mil registros para contarlos en PHP.

:::key
El orden en que se **escribe** el SQL no es el orden en que se **ejecuta**.
La base aplica primero el `FROM`, después el `WHERE`, después el `SELECT` de
las columnas, después el `ORDER BY` y por último el `LIMIT`.

Eso explica un comportamiento que confunde: el `WHERE` no ve los alias
creados en el `SELECT`, porque se ejecutó antes de que existieran. Y explica
por qué `LIMIT 10` en una tabla de un millón de filas puede ser lento —
corta al final, después de que la base ya encontró y ordenó todo lo que
alcanzó el filtro.
:::

## Cambiar y eliminar

:::story Viernes, 2013
— Yo ya lo hice — dijo Nonato, cuando el tema llegó a `UPDATE`.

Nadie había preguntado.

— Viernes, 2013. Vera pidió marcar como devuelto un préstamo que había
vuelto el sábado anterior y nadie había registrado.

Lo escribió en la pizarra, de memoria, con la letra de quien lo escribió
muchas veces desde entonces:

```text
UPDATE prestamos SET devolvido = 1
```

— ¿Qué faltó?

— El `WHERE` — dijo Tainá.

— Faltó el `WHERE`.

Ocho mil cuatrocientos préstamos quedaron devueltos a las 17:48 de un
viernes. Entre ellos, los mil doscientos que de verdad estaban abiertos.

— ¿Y entonces?

— Entonces la biblioteca no tenía backup.

Nonato borró la pizarra.

— Tiene desde el sábado.
:::

```sql
mysql> UPDATE libros SET tema = 'juvenil' WHERE id = 4;
Query OK, 1 row affected (0.01 sec)
Rows matched: 1  Changed: 1  Warnings: 0
```

`UPDATE` cambia, `SET` dice qué, `WHERE` dice dónde. Sin `WHERE`, cambia
**todas las filas de la tabla**, y MySQL no pregunta si estás seguro.

Fíjate en la segunda línea de la respuesta: `Rows matched: 1`. Ese número es
tu confirmación de que el `WHERE` alcanzó lo que querías. Cuando venga mucho
mayor de lo esperado, algo ya pasó.

```sql
mysql> DELETE FROM libros WHERE id = 4;
Query OK, 1 row affected (0.00 sec)
```

`DELETE` elimina filas. Sin `WHERE`, vacía la tabla.

:::art caption="Una línea sin `WHERE`, a las 17:48 de un viernes."
src="uma-linha-sem-where-as-17h48-de-uma-sexta-feira.png"
Viñeta editorial minimalista sobre fondo blanco: un desarrollador de unos
cuarenta años, con camisa a cuadros, frente a una pizarra donde escribió de
memoria, con letra firme, "UPDATE prestamos SET devolvido = 1" — y nada
después. En la pared, un reloj marca las 17:48 y una hojita de calendario
muestra "VIERNES". Al fondo, un fichero de préstamos con todas las fichas
saltando al mismo tiempo, cada una con un sello de "DEVUELTO". Sentada, una
pasante con el bolígrafo detenido en el aire sobre el cuaderno. Pocos
elementos, humor seco, estética de revista de tecnología.
:::

:::warning
Tres hábitos que evitan el viernes de Nonato, en orden de eficacia.

**Escribe el `WHERE` primero.** Empieza a teclear por el final:
`WHERE id = 4`, y solo después vuelve y escribe el `UPDATE ... SET`
delante. Parece una tontería y es el hábito que más funciona, porque elimina
la ventana en que el comando está sintácticamente completo y es peligroso.

**Ejecútalo como `SELECT` antes.** Cambia `UPDATE libros SET ...` por
`SELECT * FROM libros`, manteniendo el mismo `WHERE`. Lo que aparezca es
exactamente lo que se cambiaría. Revísalo, después cambia el principio.

**Activa la red de protección.** El cliente de MySQL acepta la opción
`--safe-updates` (o `-U`), que **rechaza** `UPDATE` y `DELETE` sin un
`WHERE` que use una clave:

```text
$ mysql -u root -p -U casa_amarela

mysql> DELETE FROM libros;
ERROR 1175 (HY000): You are using safe update mode and you
tried to update a table without a WHERE that uses a KEY column
```

Ponlo en tu archivo de configuración de MySQL y olvida que existe. El día en
que te salve, habrá valido por todos los días en que molestó.
:::

Y existe una cuarta protección, de otra naturaleza: **no borrar**. En lugar
de `DELETE`, muchas tablas ganan una columna `eliminado_en DATETIME NULL`, y
"eliminar" pasa a ser completar esa fecha. Nada desaparece, se puede
deshacer, y se puede responder "quién lo borró y cuándo". El costo es que
toda consulta pasa a necesitar `WHERE eliminado_en IS NULL`, y olvidarlo una
vez trae de vuelta a la pantalla los registros borrados.

:::note En tu carrera
La primera vez que tumbes datos de producción, va a existir una tentación
fuerte de arreglarlo en silencio antes de que alguien lo note. No lo hagas
— y no por moral, por matemática: el tiempo entre el error y el aviso es la
variable que más decide el tamaño del daño.

Lo que funciona, en orden: **deja de tocar**, avisa a quien responde por el
sistema, di lo que pasó en una frase y lo que ya sabes sobre el alcance
("un `UPDATE` sin `WHERE` en la tabla de préstamos, a las 17:48, 8.412
filas"). Solo entonces discute el arreglo.

Y fíjate en lo que Nonato hizo bien en 2013: empezó a contar la historia. Un
equipo en que el error grave lo cuenta quien lo cometió es un equipo donde
el próximo error aparece rápido.
:::

:::summary
- `CREATE TABLE` diseña la ficha; `DESCRIBE` muestra lo que quedó.
- El tipo de la columna es una decisión de negocio: `VARCHAR(200)` afirma
	un límite, `CHAR(13)` afirma un formato, `DATE` afirma que la hora no
	importa.
- `NOT NULL` por defecto; `NULL` solo con una justificación escrita.
- La clave primaria identifica la fila; `AUTO_INCREMENT` la completa sola;
	`UNIQUE` impide repeticiones en otra columna.
- Una columna `DECIMAL` vuelve a PHP como texto — de ahí la opción por
	`INT` en centavos.
- `WHERE` decide qué filas entran; el nulo se compara con `IS NULL`, nunca
	con `= NULL`.
- `COUNT(*)` cuenta sin traer; `ORDER BY` ordena; `LIMIT` corta al final.
- `UPDATE` y `DELETE` sin `WHERE` alcanzan la tabla entera, sin preguntar.
:::

:::milestone
El acervo de la Casa Amarela existe fuera de PHP. La tabla `libros` está
creada, con tipos elegidos y reglas que garantiza la base de datos, y
consultas y cambias lo que quieras desde la terminal.
:::

:::exercise level=1
Crea la tabla `lectores` con: identificador automático, nombre obligatorio
de hasta 120 caracteres, documento único de 11 caracteres, fecha de
registro, y teléfono opcional. Después inserta dos lectores y lístalos
ordenados por nombre.

:::answer
```sql
CREATE TABLE lectores (
  id             INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nombre         VARCHAR(120) NOT NULL,
  documento      CHAR(11)     NOT NULL,
  registrado_en  DATE         NOT NULL,
  telefono       VARCHAR(20)  NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_lectores_documento (documento)
) ENGINE=InnoDB;

INSERT INTO lectores (nombre, documento, registrado_en, telefono)
VALUES
  ('Marlene Coutinho', '11122233344', '2009-03-14', NULL),
  ('Juvenal Pereira',  '55566677788', '2011-08-02', '31 9999-1234');

SELECT id, nombre, registrado_en FROM lectores ORDER BY nombre;
```

```text
+----+------------------+---------------+
| id | nombre           | registrado_en |
+----+------------------+---------------+
|  2 | Juvenal Pereira  | 2011-08-02    |
|  1 | Marlene Coutinho | 2009-03-14    |
+----+------------------+---------------+
```

Tres decisiones que vale la pena defender: `CHAR(11)` porque el documento
tiene tamaño fijo y puede empezar con cero; `DATE` y no `DATETIME` porque la
hora del registro no le interesa a nadie; y el teléfono como `VARCHAR`
opcional, porque existe gente sin teléfono y porque un teléfono tiene
paréntesis, guiones y espacios — nunca es un número.
:::

:::exercise level=2
Sin ejecutarlos, di cuántas filas cambiaría cada comando de abajo en una
tabla `libros` con 4.000 registros, de los cuales 91 son de consulta y 12 no
tienen ISBN. Después di cuál no ejecutarías nunca.

```sql
UPDATE libros SET tema = 'referencia' WHERE tema = 'referência';
UPDATE libros SET anio = 2000 WHERE isbn = NULL;
UPDATE libros SET tema = 'general';
DELETE FROM libros WHERE id = 99999;
```

:::answer
**El primero:** cero o muchas, y nadie lo sabe sin mirar. Depende de cómo
se grabaron los 91 registros de consulta — con acento o sin él. Es un
comando de limpieza legítimo, y la forma correcta de ejecutarlo es
revisarlo antes con
`SELECT COUNT(*) FROM libros WHERE tema = 'referência';`.

**El segundo:** cero filas, siempre, aunque haya doce libros sin ISBN. El
`= NULL` no compara con nada. El comando corre, responde `Rows matched: 0` y
no hace nada — y quien lo escribió va a pasar media hora buscando el defecto
en otro lado. Lo correcto es `WHERE isbn IS NULL`.

**El tercero:** 4.000 filas. Todas. Es el comando de Nonato, con otro nombre
de columna.

**El cuarto:** cero filas, y sin ninguna consecuencia. Un `DELETE` con un
`WHERE` que no encuentra a nadie simplemente no borra nada.

**El que no ejecutaría nunca es el tercero** — y vale notar por qué es
distinto del segundo. El segundo es inofensivo por accidente: está mal y su
error lo vuelve inocuo. El tercero está sintácticamente perfecto y es
justamente por eso que destruye la tabla sin una sola pregunta.
:::

:::exercise level=3
La tabla de préstamos del Sistema, escrita en 2009, es esta:

```sql
CREATE TABLE prestamos (
  id          INT NOT NULL AUTO_INCREMENT,
  libro_id    INT NOT NULL,
  lector      VARCHAR(120) NOT NULL,
  fecha       VARCHAR(20) NOT NULL,
  devolvido   TINYINT(1) NOT NULL DEFAULT 0,
  multa       FLOAT NULL,
  PRIMARY KEY (id)
);
```

Señala cinco problemas y escribe la versión que propondrías. Para cada
cambio, di qué pregunta pasa a permitir.

:::answer
**1. `lector VARCHAR(120)` guarda el nombre, no el lector.** Dos lectores
homónimos son la misma persona para esta tabla, y un lector que cambia de
nombre desaparece de su propio historial. Se vuelve
`lector_id INT UNSIGNED NOT NULL`, apuntando a la tabla `lectores`.
*Pasa a permitir:* "¿qué préstamos son de esta persona?", con certeza.

**2. `fecha VARCHAR(20)` guarda la fecha como texto.** Ordenar por esa
columna ordena alfabéticamente: `10/03/2011` va antes que `09/04/2011`. Y
cabe cualquier cosa, incluso `ayer`. Se vuelve
`retirado_en DATETIME NOT NULL`.
*Pasa a permitir:* "¿cuántos préstamos en febrero?", que es literalmente lo
que pide la rendición de cuentas de la subvención.

**3. `devolvido TINYINT(1)` tira la fecha de la devolución.** Es la columna
de la escena de apertura. Se vuelve `devuelto_en DATETIME NULL` — quien
tiene fecha devolvió, quien no la tiene está abierto.
*Pasa a permitir:* "¿cuánto tiempo pasan afuera los libros, en promedio?" y
"¿cuántos días estuvo atrasado este?".

**4. `multa FLOAT` es dinero en coma flotante.** La suma acumula error y el
cierre del mes no cuadra por centavos — es el mismo defecto de las mil
multas de cincuenta centavos, ahora grabado en disco. Se vuelve
`multa_en_centavos INT UNSIGNED NULL`.
*Pasa a permitir:* sumar ocho mil multas y llegar al mismo número que la
caja.

**5. Falta la fecha prevista de devolución.** El plazo es de catorce días,
pero los catorce días cambian — en enero es otro, y el plazo de un préstamo
de 2011 era el de 2011. Calcularlo a partir de la fecha de retiro aplica la
regla de hoy al pasado. Se vuelve `devolver_hasta DATE NOT NULL`, grabado
en el momento del préstamo.
*Pasa a permitir:* "¿estaba atrasado?", respondido con la regla vigente en
ese momento.

```sql
CREATE TABLE prestamos (
  id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  ejemplar_id       INT UNSIGNED NOT NULL,
  lector_id         INT UNSIGNED NOT NULL,
  retirado_en       DATETIME     NOT NULL,
  devolver_hasta    DATE         NOT NULL,
  devuelto_en       DATETIME     NULL,
  multa_en_centavos INT UNSIGNED NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB;
```

Hay un sexto cambio escondido ahí, y es el mayor de todos: `libro_id` se
volvió `ejemplar_id`. Se presta el objeto físico, no el título — es la
distinción del capítulo @cap:o-que-vamos-construir llegando a la base de
datos, quince años después de que Vera describiera el problema en el
mostrador.

Y todavía le falta algo a esta versión: nada impide que `lector_id` apunte a
un lector que no existe. Eso es trabajo de una clave foránea.
:::
