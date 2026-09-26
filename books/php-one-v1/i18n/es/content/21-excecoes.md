---
source_hash: 9b07f231629f
title: "Excepciones"
number: 21
slug: excecoes
part: p4
kicker: "La importación nocturna nunca daba error. Perdía doscientas catorce filas por noche, en silencio, desde hacía tres meses."
goal: >-
  Entender la diferencia entre `Error` y `Exception`, capturar por tipo en
  lugar de capturar el mundo entero, crear el vocabulario de errores del
  dominio con datos adjuntos y conservar la causa original de una falla.
---

:::story Nunca dio error
El Sistema importaba, cada madrugada, el archivo que la editorial asociada
mandaba con las novedades del mes. Cinco años funcionando, ningún ticket
abierto.

Tainá fue a revisar un libro que Vera juraba haber registrado y no lo
encontró. Fue a revisar el archivo de la editorial: estaba ahí.

Contó las filas del archivo de octubre. Después contó las filas que habían
entrado en la base.

—Faltan doscientas catorce.

Dedé abrió el `importa_editorial.php` y buscó el bucle. Todo estaba bien
escrito, indentado, con nombres de variables en portugués.

```php
    } catch (Exception $e) {
        continue;
    }
```

—¿Cuánto tiempo tiene esto?

Tainá buscó en el historial del archivo. La línea se había agregado un
viernes de 2019, en un *commit* llamado *"corrige error de la
importación"*.

—Tres años.

—¿Y el error?

—Corregido.
:::

## `Error`, `Exception` y el `Throwable` que cubre a los dos

PHP tiene dos familias de problemas, y cuentan cosas distintas.

:::tree title="La jerarquía, simplificada"
Throwable            # la interfaz que entiende el catch
  Error              # defecto del programa
    TypeError
    ArgumentCountError
    DivisionByZeroError
  Exception          # condición del mundo
    LogicException   # tu API se usó mal
      InvalidArgumentException
      DomainException
    RuntimeException # solo se sabe al ejecutar
      PDOException
      UnexpectedValueException
:::

`Error` es lo que pasa cuando el **programa** está mal: llamaste un método
sobre `null`, pasaste texto donde iba un entero, dividiste por cero. No es
una condición del mundo, es un defecto, y un defecto no se trata: se
arregla.

`Exception` es lo que pasa cuando el **mundo** no colabora: la base se
cayó, el archivo no llegó, el ejemplar ya está prestado. El programa está
bien; la situación es la adversa.

Esa separación tiene una consecuencia práctica que atrapa a casi todos una
vez:

```php title="protegido.php" numbered
<?php

try {
    $ejemplar = null;
    $ejemplar->prestar();
} catch (Exception $e) {
    echo "lo traté\n";
}
```

```text
Fatal error: Uncaught Error:
Call to a member function prestar() on null
```

El `catch` no atrapó nada. `Error` no es `Exception`: las dos solo se
encuentran allá arriba, en `Throwable`.

:::key
`catch (Exception $e)` trata problemas del mundo y deja pasar los
defectos. Ese es el comportamiento correcto en la mayor parte del código:
quieres saber cuándo llamaste un método sobre `null`, no quieres tragártelo.
:::

## El `catch` que borra al testigo

El bloque del `importa_editorial.php` tiene cuatro líneas y tres defectos.

```php
    } catch (Exception $e) {
        continue;
    }
```

**El primero es el silencio.** La variable `$e` se capturó y se descartó.
Quien lo escribió tenía en la mano el archivo, la línea, el mensaje de la
base y la pila entera de llamadas, y lo tiró todo.

**El segundo es el alcance.** Trata cualquier `Exception`: el ISBN
duplicado, que es esperado, y la conexión a la base caída, que no lo es.
Una noche en que MySQL no arranca produce un archivo importado con cero
filas y ninguna queja.

**El tercero es el resultado.** Al final, el programa termina con éxito. El
código de salida es cero, el programador de tareas marca verde, y nadie
tiene motivo para mirar.

La versión que dice la verdad no es más complicada:

```php title="importar.php" numbered
<?php

$grabadas = 0;
$rechazadas = [];

foreach ($filas as $numero => $fila) {
    try {
        grabar($pdo, $fila);
        $grabadas++;
    } catch (FilaInvalida $e) {
        $rechazadas[] = "fila {$numero}: {$e->getMessage()}";
    }
}

echo "grabadas: {$grabadas}\n";
echo 'rechazadas: ' . count($rechazadas) . "\n";

foreach ($rechazadas as $motivo) {
    echo "  {$motivo}\n";
}

exit($rechazadas === [] ? 0 : 1);
```

```text
grabadas: 1786
rechazadas: 214
  fila 12: ISBN 9788525406958 ya existe
  fila 19: falta el año
  ...
```

Dos cambios hicieron el trabajo. El `catch` pasó a nombrar **un tipo
específico**: solo se tolera la fila inválida; cualquier otra cosa sube y
tumba el programa, que es lo que se quiere cuando la base se cayó. Y el
resumen salió del silencio: alguien, en algún momento, lee "214
rechazadas" y abre un ticket.

:::pitfall
`catch (\Throwable $e) { return false; }` es la forma más completa de ese
defecto, porque se traga hasta los `Error`. Un `TypeError` en una línea
tuya se vuelve "dio falso", y el programa sigue como si fuera una condición
normal del negocio.

Cuando encuentres uno de esos en una revisión, la pregunta no es "¿por qué
está capturando?". Es: **¿qué harías si supieras cuál fue el error?** Si la
respuesta es "abriría un ticket", el `catch` está en el lugar equivocado.
:::

## El vocabulario de errores del dominio

`RuntimeException('Ejemplar no disponible')` funciona, y tiene un problema:
quien la captura no puede hacer nada con ella además de mostrar el texto.

Para reaccionar, el código de arriba tendría que leer la frase, y las
frases cambian, ganan tildes, pasan al plural, se traducen.

Una excepción es una clase. Puede llevar datos:

```php title="src/Circulacion/EjemplarNoDisponible.php" numbered
<?php

namespace CasaAmarela\Circulacion;

class EjemplarNoDisponible extends \RuntimeException
{
    public function __construct(
        public readonly int $registro,
        public readonly string $condicion,
    ) {
        parent::__construct(
            "Ejemplar {$registro} no disponible: {$condicion}"
        );
    }
}
```

`parent::__construct(...)` llama al constructor de la clase de arriba
—aquí, el de `RuntimeException`, que es quien guarda el mensaje—. Las dos
propiedades promovidas son un agregado tuyo.

La Casa Amarela necesita tres:

| Excepción | Lleva | Quién reacciona |
|---|---|---|
| `EjemplarNoDisponible` | registro, condicion | la pantalla ofrece la reserva |
| `LimiteDePrestamosAlcanzado` | limite, abiertos | la pantalla lista qué devolver |
| `LectorConPendiente` | lectorId, multaEnCentavos | la pantalla muestra el monto |

Tabla: Tres situaciones previsibles, tres tipos, y en ninguna de ellas
quien captura necesita leer el mensaje para decidir qué hacer.

Y el uso queda directo:

```php title="prestar.php" numbered
try {
    prestar($pdo, $registro, $lectorId);
} catch (LectorConPendiente $e) {
    $valor = number_format($e->multaEnCentavos / 100, 2, ',', '.');
    echo "Regulariza R$ {$valor} antes de llevar otro libro.\n";
} catch (EjemplarNoDisponible $e) {
    echo "El {$e->registro} está {$e->condicion}. ¿Lo reservas?\n";
}
```

:::key
El orden de los `catch` importa: PHP usa el **primero que sirve**. El tipo
más específico primero, el más genérico después.

Un `catch (\RuntimeException $e)` escrito antes de los tres nunca dejaría
que se alcanzara ninguno de ellos, y PHP no avisa, porque no hay nada
ilegal en eso.
:::

## `previous`: no perder la causa en el camino

Una falla suele atravesar capas. La base rechaza, el repositorio traduce,
la pantalla muestra, y en cada traducción existe el riesgo de que la
información original desaparezca.

El tercer argumento del constructor de cualquier excepción es la
**causa**:

```php title="prestar.php" numbered
try {
    $c->execute([$ejemplarId, $lectorId]);
} catch (\PDOException $e) {
    throw new \RuntimeException(
        'Falla al registrar el préstamo',
        0,
        $e,
    );
}
```

Si nadie la trata, PHP imprime las dos, en el orden en que ocurrieron:

```text
Fatal error: Uncaught PDOException: SQLSTATE[HY000]: conexión negada
in /app/prestar.php:8
Stack trace:
#0 /app/prestar.php(14): prestar()
#1 {main}

Next RuntimeException: Falla al registrar el préstamo
in /app/prestar.php:10
Stack trace:
#0 /app/prestar.php(14): prestar()
#1 {main}
```

La primera es la causa; el `Next` es la traducción. Sin el tercer
argumento, el log tendría solo la segunda, y "falla al registrar el
préstamo" no dice si la base se cayó, si la tabla desapareció o si cambió
la contraseña.

`getPrevious()` recupera la causa en código, y devuelve `null` cuando no
la hubo.

## `finally`: lo que hay que devolver

Existe un bloque que corre **siempre**: cuando el `try` termina bien,
cuando sube una excepción y hasta cuando hay un `return` en el medio.

```php title="prestar.php" numbered
function prestar(PDO $pdo, int $ejemplarId, int $lectorId): int
{
    $pdo->beginTransaction();

    try {
        // ... el SELECT FOR UPDATE, el INSERT y el UPDATE

        $pdo->commit();

        return $id;
    } catch (\PDOException $e) {
        $pdo->rollBack();

        throw new \RuntimeException('Falla en el préstamo', 0, $e);
    } finally {
        $pdo->exec('SET SESSION wait_timeout = DEFAULT');
    }
}
```

`finally` es el lugar para devolver lo que se tomó prestado: un archivo
abierto, un bloqueo, una configuración de sesión modificada. No es el
lugar para tratar el error: es el lugar para limpiar la mesa, pase lo que
pase.

:::pitfall
Un `return` dentro del `finally` **reemplaza** lo que el `try` iba a
devolver, y descarta hasta una excepción que estaba subiendo.

```php
function cuanto(): int
{
    try {
        throw new \RuntimeException('me rompí');
    } finally {
        return 0;
    }
}
```

Esa función devuelve cero y la excepción se evapora. Es el `catch` vacío
otra vez, disfrazado de orden.
:::

## Cuándo no capturar

Capturar es la excepción, no la regla. Tres casos en los que lo correcto es
dejarla subir.

**Cuando no vas a hacer nada además de reenviarla.** Un `catch` que solo
escribe en el log y vuelve a hacer `throw` agregó ruido y ninguna
información.

**Cuando el problema es un defecto.** `TypeError`, `ArgumentCountError`,
método llamado sobre `null`: tratar eso es esconder un error que hay que
arreglar en el código.

**Cuando la situación es previsible y frecuente.** Una excepción es cara y
ruidosa. "El lector no existe" en una búsqueda no es una falla: es una
respuesta posible, y su lugar es un `null` o una lista vacía.

:::key
La regla: excepción para lo que **interrumpe** lo que se estaba haciendo;
retorno normal para lo que es **una de las respuestas** posibles.

"No encontré al lector 913" es una respuesta. "La base no respondió" es
una interrupción.
:::

## La última red

En un programa que atiende personas, una excepción que llega hasta arriba
no puede volverse un volcado de la pila en la pantalla: muestra rutas de
archivos, nombres de tablas y a veces credenciales.

```php title="importar.php" numbered
set_exception_handler(function (\Throwable $e): void {
    error_log((string) $e);

    fwrite(STDERR, "La importación falló. Busca al soporte.\n");

    exit(1);
});
```

`set_exception_handler` registra qué hacer con lo que nadie trató. Las
tres líneas del cuerpo son el patrón: **registra todo** donde el equipo
busca, **muestra poco** a quien está frente a la pantalla, y **termina con
un código distinto de cero**, para que el programador de tareas sepa que
salió mal.

:::note En tu carrera
El `catch (Exception $e) { continue; }` de la madrugada no fue pereza.
Alguien tenía una importación rompiéndose a las tres de la mañana, un
ticket abierto y un viernes. La línea resolvió el ticket.

Es la forma más común de deuda técnica: la corrección que funciona contra
el síntoma exacto que se informó. Pasa la revisión porque el informe decía
"la importación se está rompiendo" y la importación dejó de romperse.

Lo que habría detectado esto en treinta segundos es una pregunta de
revisión que cuesta poco y que puedes hacer siempre: **¿cómo vamos a saber
si esto vuelve a pasar?** Si la respuesta es "no va a dar error", la
corrección borró el aviso, no la causa.
:::

:::tree title="Dónde estamos ahora"
acervo/
  src/
    Circulacion/
      Prestable.php
      RegistraHistorial.php
      EjemplarNoDisponible.php        # con registro y condicion
      LimiteDePrestamosAlcanzado.php  # con limite y abiertos
      LectorConPendiente.php          # con lectorId y multa
    Acervo/
      Libro.php
      Clasificacion.php
      Ejemplar.php
    Lectores/
      Lector.php
    Prestamos/
      Multa.php
  importar.php
  prestar.php
:::

:::summary
- `Error` es un defecto del programa; `Exception` es una condición del
  mundo; las dos son `Throwable`.
- `catch (Exception)` no atrapa `Error`, y eso juega a favor.
- Un `catch` vacío borra al único testigo de la falla y hace que el
  programa termine con éxito.
- Captura el tipo específico; deja subir el resto.
- Una excepción es una clase: adjunta los datos que necesita quien la
  captura, en lugar de obligarlo a leer el mensaje.
- El orden de los `catch` va del más específico al más genérico.
- El tercer argumento del constructor guarda la causa, y aparece en el log
  como `Next`.
- `finally` devuelve recursos y nunca debe contener `return`.
- Excepción para lo que interrumpe; retorno normal para lo que es una de
  las respuestas posibles.
:::

:::checkpoint
Distingues `Error` de `Exception`, reconoces en una revisión de código el
`catch` que borra información, escribes una familia de excepciones de
dominio con datos adjuntos, encadenas la causa original y sabes señalar
tres situaciones en las que lo correcto es no capturar.
:::

:::exercise level=1
Di, para cada situación, si merece una excepción o un retorno normal, y,
cuando sea excepción, de cuál de las dos familias.

1. El lector escribió un documento que no existe en el registro.
2. El archivo de configuración no se encontró al arrancar.
3. `prestar()` recibió un registro negativo.
4. La consulta de libros por tema no encontró ninguno.
5. MySQL rechazó la conexión.

:::answer
1. **Retorno normal**: `null`. No encontrar es una de las respuestas
   posibles de una búsqueda.
2. **Excepción**, familia `Exception` (`RuntimeException`). El programa
   está bien; el mundo es el que no tiene el archivo, y no hay cómo
   continuar.
3. **Excepción**, familia `Exception` (`InvalidArgumentException`). Es un
   uso equivocado de tu función, detectable en la frontera. Fíjate que si
   se violara el tipo —texto donde va `int`— entonces sería `TypeError`,
   familia `Error`, y no eres tú quien la lanza.
4. **Retorno normal**: lista vacía. Cero resultados es un resultado, y el
   `count()` de un array vacío es cero, lo que ya resuelve la pantalla.
5. **Excepción**, familia `Exception` (`PDOException`, que ya viene
   lista).

El patrón que aparece en los cinco: la búsqueda que no encuentra devuelve
vacío; lo que impide que el trabajo continúe lanza.
:::

:::exercise level=2
Escribe `LimiteDePrestamosAlcanzado` con los datos adjuntos y ajusta la
función de préstamo para que la lance.

La regla de Vera: tres libros por lector, cinco en enero.

Después escribe el `catch` que produce el mensaje final para el mostrador,
usando los datos de la excepción y no su mensaje.

:::answer
```php title="src/Circulacion/LimiteDePrestamosAlcanzado.php" numbered
<?php

namespace CasaAmarela\Circulacion;

class LimiteDePrestamosAlcanzado extends \RuntimeException
{
    public function __construct(
        public readonly int $lectorId,
        public readonly int $limite,
        public readonly int $abiertos,
    ) {
        parent::__construct(
            "Lector {$lectorId} tiene {$abiertos} de {$limite}"
        );
    }
}
```

```php title="prestar.php" numbered
$limite = (int) date('n') === 1 ? 5 : 3;

$abiertos = (int) $pdo->query(
    'SELECT COUNT(*) FROM prestamos
     WHERE lector_id = ' . $lectorId . ' AND devuelto_en IS NULL'
)->fetchColumn();

if ($abiertos >= $limite) {
    throw new LimiteDePrestamosAlcanzado(
        $lectorId,
        $limite,
        $abiertos,
    );
}
```

```php
} catch (LimiteDePrestamosAlcanzado $e) {
    echo "Límite de {$e->limite} libros alcanzado. ";
    echo "Devuelve 1 de los {$e->abiertos} para llevar otro.\n";
}
```

Una observación sobre la consulta: está concatenando `$lectorId`. Como el
valor vino de un `(int)`, es seguro, pero seguro por accidente, y el
accidente no es una política. La consulta preparada es la forma de que la
seguridad no dependa de que alguien se acuerde del `(int)` en el próximo
cambio.

Y fíjate en lo que el mensaje del mostrador **no** usa:
`$e->getMessage()`. La frase "Lector 913 tiene 3 de 3" sirve para el log.
Para la persona en la fila, la pantalla arma su propia frase, con los
mismos números.
:::

:::exercise level=3
Este código corre cada madrugada y nunca se quejó. Encuentra los cuatro
problemas y reescríbelo.

```php title="sincroniza.php" numbered
<?php

$archivo = fopen('/tmp/editorial.csv', 'r');

try {
    while (($fila = fgetcsv($archivo)) !== false) {
        try {
            grabar($pdo, $fila);
        } catch (Throwable $e) {
            file_put_contents(
                '/tmp/errores.log',
                $e->getMessage(),
                FILE_APPEND,
            );
        }
    }
} catch (Exception $e) {
    echo "error\n";
}

fclose($archivo);
```

:::answer
**Uno: el `catch (Throwable)` de adentro se traga los defectos.** Si
`grabar()` tiene un `TypeError`, todas las filas fallan de la misma forma
y el programa termina bien. El tipo capturado tiene que ser el de la fila
inválida, y solo ese.

**Dos: el log guarda solo el mensaje.** `$e->getMessage()` descarta el
tipo, el archivo, la línea y la causa encadenada. `(string) $e` guarda
todo, y `error_log()` lo manda adonde el equipo ya busca, en lugar de a un
archivo en `/tmp` que nadie abre.

**Tres: nada cuenta.** No hay total de grabadas, total de rechazadas ni
código de salida. Sin números, la diferencia entre una noche perfecta y una
noche que perdió doscientas filas es invisible.

**Cuatro: el `fclose` no ocurre siempre.** Si el `while` lanza algo que el
`catch (Exception)` no atrapa —un `Error`, por ejemplo—, el programa muere
con el archivo abierto. El lugar del `fclose` es un `finally`.

```php title="sincroniza.php" numbered
<?php

$archivo = fopen('/tmp/editorial.csv', 'r');

if ($archivo === false) {
    throw new RuntimeException('El CSV de la editorial no llegó');
}

$grabadas = 0;
$rechazadas = [];

try {
    while (($fila = fgetcsv($archivo)) !== false) {
        try {
            grabar($pdo, $fila);
            $grabadas++;
        } catch (FilaInvalida $e) {
            $rechazadas[] = $e->getMessage();
            error_log((string) $e);
        }
    }
} finally {
    fclose($archivo);
}

echo "grabadas: {$grabadas}, rechazadas: ", count($rechazadas), "\n";

exit($rechazadas === [] ? 0 : 1);
```

El `catch (Exception)` de afuera desapareció entero, y es la mejor parte
del cambio: no había nada útil que hacer ahí. Cualquier falla que no sea
una fila inválida ahora tumba el programa con el mensaje completo, que es
exactamente lo que se quiere a las tres de la mañana.
:::
