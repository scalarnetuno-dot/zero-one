---
source_hash: cf351d8098a6
title: "Errores y depuración"
number: 28
slug: erros-e-debug
part: p5
kicker: "La importación de la madrugada no importó nada y terminó con éxito. PHP había avisado tres veces, a nadie."
goal: >-
  Distinguir los niveles de error de PHP, hacer que el aviso que el
  programa ignora se vuelva una excepción que no puede ignorar, armar la
  configuración de errores de un script en un solo lugar, leer una pila de
  llamadas de abajo hacia arriba, y registrar errores con contexto
  suficiente para que alguien los arregle.
---

:::story Cero libros, código cero
La primera importación nocturna de las donaciones de don Juvenal corrió a
las 2 h. A la mañana, la tabla de libros tenía los mismos cuatro mil
títulos del día anterior.

—¿Dio error? —preguntó Márcia.

—No —dijo Tainá—. Terminó con éxito. Código de salida cero.

—Entonces importó.

—Importó cero.

Dedé abrió la configuración del programador de tareas del servidor.

```text
0 2 * * * php /srv/acervo/scripts/importar-donaciones.php \
    > /dev/null 2>&1
```

—Ese `> /dev/null 2>&1` al final —dijo— manda todo lo que imprime el
script a ninguna parte. Los mensajes normales y los de error.

—¿Y había error?

—Vamos a ver.

Ejecutó el script a mano, desde la raíz, como lo ejecutaba el programador
de tareas:

```text
Warning: fopen(donaciones.csv): Failed to open stream: No such
file or directory in /srv/acervo/scripts/importar-donaciones.php
on line 7
```

—PHP avisó —dijo Dedé—. Todas las noches. A `/dev/null`.
:::

:::art caption="PHP avisó todas las noches. El aviso iba a ninguna parte."
src="o-php-avisou-todas-as-noites-o-aviso-ia-para-lugar-nenhum.png"
Viñeta editorial minimalista sobre fondo blanco, composición dividida entre
noche y mañana. A la izquierda, de noche, un servidor pequeño sobre una
mesa, con un reloj que marca las 2 h; de él sale un globo de diálogo con la
palabra "Warning", que se desliza directo a un agujero redondo en el suelo
con un cartelito "/dev/null". Dentro del agujero, una pila de globos
iguales, uno por noche. A la derecha, de mañana, una pasante mira una
pantalla donde solo se lee "código de salida: 0" con un visto verde, y a su
lado una gerente con una planilla en la mano sonríe satisfecha. Pocos
elementos, humor seco, estética de revista de tecnología.
:::

## Los niveles de error

No todo lo que PHP llama error detiene el programa. El mismo archivo puede
mostrar tres problemas y llegar a la última línea:

```php title="niveles.php" numbered
<?php

declare(strict_types=1);

$libro = ['titulo' => 'Vidas Secas'];

echo $libro['autor'], "\n";
echo $total, "\n";
$archivo = fopen('/no/existe.csv', 'r');
var_dump($archivo);
echo "llegó al final\n";
```

```text
$ php niveles.php

Warning: Undefined array key "autor" in niveles.php on line 7

Warning: Undefined variable $total in niveles.php on line 8

Warning: fopen(/no/existe.csv): Failed to open stream: No
such file or directory in niveles.php on line 9
bool(false)
llegó al final
```

Tres avisos, y el programa sigue con `null` donde esperaba un autor, `null`
donde esperaba un total y `false` donde esperaba un archivo. Es el
comportamiento que PHP heredó de la época en que una página armada a medias
era mejor que ninguna.

| Nivel | Qué significa | El programa |
|---|---|---|
| `Deprecated` | esto va a dejar de funcionar en una versión futura | sigue |
| `Warning` | algo salió mal, y PHP improvisó un valor | sigue |
| `Fatal error` | no hay cómo continuar | se detiene |
| excepción no capturada | el capítulo @cap:excecoes | se detiene |

Tabla: Los niveles que vas a encontrar. Había un cuarto, `Notice`, que PHP
8 promovió casi entero a `Warning`.

El `Deprecated` aparece al usar un recurso con fecha de salida:

```text
$ php -r 'echo strlen(null);'

Deprecated: strlen(): Passing null to parameter #1 ($string)
of type string is deprecated in Command line code on line 1
0
```

Hoy funciona. En una versión futura de PHP, es un `TypeError`. Un
`Deprecated` en el log es una tarea con plazo, y el plazo es la próxima
actualización de versión, que, en la vida de un proyecto, suele llegar
antes de lo que parece.

:::key
**Un warning no es "todo bien, es solo un aviso".** Es PHP diciendo que no
pudo hacer lo que pediste y puso otro valor en su lugar. Un programa que
deja pasar un warning sigue corriendo con un valor que nadie eligió.
:::

## El aviso se vuelve excepción

El capítulo @cap:excecoes enseñó a tratar excepciones: detienen el
programa si nadie las captura, y llevan la pila de llamadas. El warning no
tiene ninguna de esas dos cualidades. La solución es convertir uno en el
otro.

```php title="bootstrap.php" numbered
<?php

declare(strict_types=1);

error_reporting(E_ALL);
ini_set('display_errors', '0');
ini_set('log_errors', '1');
ini_set('error_log', __DIR__ . '/var/log/php.log');

set_error_handler(
    function (int $nivel, string $msg, string $arch, int $ln): bool {
        if ($nivel === E_DEPRECATED || $nivel === E_USER_DEPRECATED) {
            error_log("deprecated: {$msg} en {$arch}:{$ln}");
            return true;
        }
        throw new ErrorException($msg, 0, $nivel, $arch, $ln);
    },
);

set_exception_handler(function (Throwable $e): void {
    error_log((string) $e);
    fwrite(STDERR, "falló: {$e->getMessage()}\n");
    exit(1);
});
```

Un archivo, cuatro decisiones, y todo script de la carpeta `scripts/`
empieza por él:

```php
require __DIR__ . '/../bootstrap.php';
```

**`error_reporting(E_ALL)`** activa todos los niveles. Un nivel apagado no
es un problema menos: es un problema que no ves.

**Las tres líneas de `ini_set`** son las del capítulo
@cap:primeiro-programa, ahora en el código: no mostrar errores en pantalla,
y grabar todo en un archivo que el equipo sabe dónde está. Escritas aquí,
valen incluso en un servidor cuyo `php.ini` nadie revisó.

**`set_error_handler`** registra una función que PHP llama en lugar de
imprimir el warning. Esta hace dos cosas: el `Deprecated` va al log y el
programa sigue —no está mal **hoy**, y una biblioteca de terceros con un
recurso antiguo no puede tumbar la importación—. Todo lo demás se vuelve
`ErrorException`, una excepción que PHP ya trae lista para eso, con el
nivel, el archivo y la línea del aviso original.

**`set_exception_handler`** es la última red del capítulo @cap:excecoes:
registrar todo, mostrar poco, salir con un código distinto de cero.

El mismo script de la historia, ahora con el `bootstrap.php`:

```text
$ php /srv/acervo/scripts/importar-donaciones.php > /dev/null
falló: fopen(donaciones.csv): Failed to open stream: No such
file or directory
$ echo $?
1
```

El mensaje va a la salida de error, que el `> /dev/null` solo no esconde, y
el código de salida 1 le dice al programador de tareas que la noche salió
mal. En el log, la historia entera:

```text
[26-Sep-2025 02:00:03 UTC] ErrorException: fopen(donaciones.csv):
Failed to open stream: No such file or directory in
/srv/acervo/scripts/importar-donaciones.php:7
Stack trace:
#0 [internal function]: {closure}(2, 'fopen(donacione...', ...)
#1 /srv/acervo/scripts/importar-donaciones.php(7):
   fopen('donaciones.csv', 'r')
#2 {main}
```

:::pitfall
El operador `@` delante de una llamada —`@fopen(...)`— silencia el aviso de
esa línea. Aparece mucho en código antiguo, siempre por el mismo motivo: el
aviso molestaba. Es el `catch` vacío del capítulo @cap:excecoes con un solo
carácter.

Si una llamada puede fallar de una forma esperada, revisa su retorno, como
el `if ($archivo === false)` del capítulo @cap:manipulacao-de-arquivos. Si
no puede, deja que el aviso se vuelva excepción.
:::

## La pila, leída de abajo hacia arriba

Con los avisos volviéndose excepciones, las fallas pasan a venir con una
**pila de llamadas**: el camino que hizo el programa hasta el error. En la
importación, una fila de la planilla tenía el año escrito en letras:

```text
Fatal error: Uncaught InvalidArgumentException: año inválido:
mil ochocientos in /srv/acervo/src/Importador.php:26
Stack trace:
#0 /srv/acervo/src/Importador.php(18):
   Importador->anio('mil ochocientos')
#1 /srv/acervo/src/Importador.php(11): Importador->grabar(Array)
#2 /srv/acervo/importar.php(12): Importador->importar(Array)
#3 {main}
  thrown in /srv/acervo/src/Importador.php on line 26
```

La primera línea dice **qué**: la excepción, el mensaje, y el archivo y la
línea en que se lanzó. La pila dice **por dónde**, y se lee mejor de abajo
hacia arriba, que es el orden en que ocurrieron las cosas:

1. `{main}`: el programa empezó;
2. `importar.php`, línea 12, llamó a `importar`;
3. `importar`, en la línea 11 del `Importador`, llamó a `grabar`;
4. `grabar`, en la línea 18, llamó a `anio` con `'mil ochocientos'`;
5. `anio` lanzó la excepción, en la línea 26.

El argumento entre paréntesis, `'mil ochocientos'`, muchas veces es la
respuesta entera. Cuando no lo es, la pregunta siguiente es: **¿cuál es la
primera línea, de abajo hacia arriba, que es código mío y que no esperaba
ver ahí?** En un proyecto con framework, la pila tiene sesenta líneas, y
cincuenta y cinco son del framework. Las cinco tuyas son las que importan.

:::key
El mensaje dice qué; la pila dice por dónde; los argumentos dicen con qué.
Lee los tres antes de abrir el código. La mitad de las veces el arreglo
aparece antes.
:::

## Investigar: `var_dump`, y un paso más

Cuando la pila no alcanza, el recurso más usado sigue siendo el del
capítulo @cap:variaveis-e-tipos: detener el programa y mirar.

```php
var_dump($fila);
exit;
```

Es rápido y funciona en cualquier servidor. El costo es que tienes que
saber dónde ponerlo, y quitarlo después: un `var_dump` olvidado en el
código que sube a producción es un clásico con víctimas.

Tres hábitos vuelven más eficiente esa forma:

- **Reduce el caso.** Si la fila 81.407 de la planilla se rompe, haz un
  archivo con la fila 81.407 y ninguna más. Un error que se repite en un
  segundo se investiga diez veces más rápido que uno que tarda cuatro
  minutos.
- **Una hipótesis a la vez.** "Creo que es el BOM": imprime las claves.
  ¿No era? Siguiente hipótesis. Cambiar tres cosas a la vez y ver que
  funciona no dice cuál de las tres lo arregló.
- **Escribe lo que descubriste.** En el cuaderno, en el pedido de revisión.
  La misma falla vuelve dentro de ocho meses, y quien la investigue puedes
  ser tú.

El paso más allá es un **depurador**: Xdebug, una extensión de PHP que se
conecta al editor y te deja detener el programa en una línea, ver todas las
variables y avanzar una línea a la vez. La instalación cambia con el
sistema y el editor, y queda para cuando el `var_dump` deje de alcanzar.
Cuando deje de alcanzar, vale la tarde.

## Registrar con contexto

`error_log` graba un texto. Un texto como "falla al importar" responde poco
a las 9 h del día siguiente: ¿qué libro? ¿qué fila? ¿qué archivo? El
registro que ayuda tiene el mensaje **y** los datos.

```php title="src/Bitacora.php" numbered
<?php

declare(strict_types=1);

final class Bitacora
{
    public function __construct(private string $archivo)
    {
    }

    public function info(string $mensaje, array $contexto = []): void
    {
        $this->grabar('info', $mensaje, $contexto);
    }

    public function error(string $mensaje, array $contexto = []): void
    {
        $this->grabar('error', $mensaje, $contexto);
    }

    private function grabar(
        string $nivel,
        string $msg,
        array $ctx,
    ): void
    {
        $linea = json_encode([
            'cuando' => date(DATE_ATOM),
            'nivel' => $nivel,
            'mensaje' => $msg,
            'contexto' => $ctx,
        ], JSON_UNESCAPED_UNICODE);

        file_put_contents(
            $this->archivo,
            $linea . "\n",
            FILE_APPEND | LOCK_EX,
        );
    }
}
```

Y la importación gana lo que pedía el ejercicio 3 del capítulo
@cap:manipulacao-de-arquivos: contar.

```php
$bitacora->error('fila descartada', [
    'fila' => $numero,
    'motivo' => $e->getMessage(),
]);

// ...al final del bucle:
$bitacora->info('importación terminada', [
    'leidas' => $leidas,
    'importadas' => $importadas,
    'descartadas' => $descartadas,
]);

if ($leidas > 0 && $importadas === 0) {
    exit(1);
}
```

```text
{"cuando":"2025-09-27T02:00:41+00:00","nivel":"error",
 "mensaje":"fila descartada","contexto":{"fila":81407,
 "motivo":"año inválido: mil ochocientos"}}
{"cuando":"2025-09-27T02:04:12+00:00","nivel":"info",
 "mensaje":"importación terminada","contexto":{"leidas":200000,
 "importadas":199312,"descartadas":688}}
```

Una línea de JSON por evento. `FILE_APPEND` agrega al final en lugar de
borrar el archivo, y `LOCK_EX` es el `flock` del capítulo
@cap:manipulacao-de-arquivos en una constante: dos scripts registrando al
mismo tiempo no mezclan las líneas.

:::term Registro con contexto
Una entrada de log con tres partes: el **nivel** (info, error...), un
**mensaje fijo**, que se puede buscar, y un **contexto** con los datos de
esa ocurrencia. "fila descartada" es igual en las 688 entradas; el número
de la fila y el motivo cambian.

La comunidad PHP estandarizó ese formato en la PSR-3, la interfaz
`LoggerInterface`, con un método por nivel y el `array $context` en todos.
:::

## Lo que el volumen 2 hace con los errores

Laravel hace todo esto antes de que corra tu primera línea. Registra un
manejador que convierte los warnings en `ErrorException` —el mismo
`set_error_handler` de este capítulo—, manda los `Deprecated` a un log
aparte, y tiene una última red que decide qué mostrar: la página detallada
con la pila para quien está desarrollando, y una respuesta corta, sin rutas
de archivos, para quien está usando.

El registro con contexto es el `Log::error('mensaje', [...])`, que
implementa la PSR-3. Y el `var_dump` seguido de `exit` tiene nombre propio
en el framework, `dd()`: *dump and die*, "muestra y detente".

:::note En tu carrera
El `> /dev/null 2>&1` de la historia no fue un descuido de quien lo
escribió. El programador de tareas manda por correo todo lo que imprime un
script, y alguien, un día, se cansó de recibir trescientos correos de aviso
por mes. Silenció la salida y resolvió el problema que tenía.

El arreglo de verdad es el de este capítulo: el script se queda callado
cuando sale bien, y cuando sale mal registra con detalle, sale con un código
distinto de cero y alguien se entera. Un sistema que avisa solo cuando hace
falta es escuchado. Uno que avisa todo el tiempo termina mandado a
`/dev/null`.
:::

:::tree title="Dónde estamos ahora"
acervo/
  bootstrap.php          # E_ALL, log, el warning se vuelve excepción
  src/
    Bitacora.php         # una línea JSON por evento
    Importador.php       # cuenta leídas, importadas, descartadas
  scripts/
    importar-donaciones.php  # require bootstrap; exit(1) si da cero
  var/
    log/                 # fuera de Git
:::

:::summary
- `Warning` y `Deprecated` no detienen el programa; `Fatal error` y la
  excepción no capturada sí.
- Un warning es PHP improvisando un valor. No lo dejes pasar.
- `set_error_handler` transforma los warnings en `ErrorException`; el
  `Deprecated` va al log.
- `bootstrap.php` junta en un lugar: `E_ALL`, `display_errors` apagado,
  log activado, manejador de errores, última red.
- La pila se lee de abajo hacia arriba; busca la primera línea que es tuya.
- `@` es el `catch` vacío de un carácter.
- Registra con nivel, mensaje fijo y contexto. La PSR-3 lo estandariza.
:::

:::checkpoint
Reconoces los niveles de error de PHP, haces que un warning detenga el
programa en lugar de dejarlo seguir con un valor improvisado, lees una pila
de llamadas hasta la línea que interesa, y dejas que un script de la
madrugada hable cuando sale mal, y solo cuando sale mal.
:::

:::exercise level=1
Para cada mensaje, di el nivel y si el programa continúa **sin** el
`bootstrap.php` de este capítulo:

1. `Undefined array key "isbn"`
2. `Passing null to parameter #1 ($string) of type string is deprecated`
3. `Uncaught TypeError: diasDeAtraso(): Argument #1 ($plazo) must be of
   type DateTimeImmutable, string given`
4. `file_get_contents(portada.jpg): Failed to open stream`

:::answer
1. `Warning`. Continúa, con `null` en lugar del ISBN.
2. `Deprecated`. Continúa.
3. Excepción (`TypeError`, un `Error`) no capturada. Se detiene.
4. `Warning`. Continúa, con `false` en lugar del contenido, y el `false`
   sigue hasta que alguien intenta usarlo como texto.

Con el `bootstrap.php`, los ítems 1 y 4 también se detienen, y el 2 va al
log.
:::

:::exercise level=2
Lee la pila y responde: ¿en qué función nació el error, con qué valor, y
cuál es la línea **de tu código** por donde empezarías a investigar?

```text
Fatal error: Uncaught ValueError: "prestado " is not a valid
backing value for enum EstadoEjemplar
Stack trace:
#0 /srv/acervo/src/Acervo/Ejemplar.php(41):
   EstadoEjemplar::from('prestado ')
#1 /srv/acervo/src/Acervo/RepositorioDeEjemplares.php(58):
   Ejemplar::deLaBase(Array)
#2 /srv/acervo/scripts/informe.php(19):
   RepositorioDeEjemplares->todos()
#3 {main}
```

:::answer
Nació en `EstadoEjemplar::from`, el método del enum del capítulo
@cap:enums-datas-e-valores, llamado con `'prestado '`, con un espacio al
final.

`from` hace bien en rechazarlo: el valor no es uno de los casos. La primera
línea que es código tuyo es `Ejemplar.php`, línea 41, pero la pregunta útil
va una línea más allá: **¿de dónde vino el espacio?** `deLaBase` recibe el
array del repositorio, que lo leyó de la base. El espacio está en una fila
de la tabla `ejemplares`, probablemente importada del Sistema antiguo.

Arreglo en dos partes: limpiar los datos
(`UPDATE ... SET condicion = TRIM(condicion)`) y decidir si `deLaBase` debe
aceptar suciedad. La respuesta de este libro es no: el error apareció, y es
bueno que haya aparecido.
:::

:::exercise level=3
Márcia quiere "un correo cuando la importación salga mal". Describe qué
cambiarías en el `bootstrap.php` y en el script de importación, y di por
qué **no** mandarías un correo por cada fila descartada.

:::answer
El correo entra en la última red, y solo en ella: el
`set_exception_handler` ya se llama exactamente cuando la importación
falló del todo. Después del `error_log`, llama al envío, con el mensaje y
el nombre del script, sin la pila, que queda en el log. La otra condición
de falla es la del final del script: leídas más que cero e importadas
cero. En lugar de `exit(1)` directo, lanza una excepción, y cae en la misma
red.

Una fila descartada no genera correo porque una importación de doscientas
mil filas con seiscientas descartadas mandaría seiscientos correos, y a la
tercera noche alguien crearía una regla para mandarlos a la papelera: el
`/dev/null` de la historia, ahora en la bandeja de entrada. Lo que le llega
a Márcia es el resumen: un correo por noche, con los tres conteos, y solo
cuando las descartadas pasen de un límite que ella elige.
:::
