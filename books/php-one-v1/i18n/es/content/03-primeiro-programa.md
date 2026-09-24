---
source_hash: a6f6540e699f
title: "El primer programa"
number: 3
slug: primeiro-programa
part: p1
kicker: "Dos líneas de PHP, tres instalaciones distintas en la misma máquina y una pantalla en blanco que no es ningún error."
goal: >-
  Escribir, guardar y ejecutar PHP desde la terminal y desde el navegador;
  comentar código; imprimir de cuatro formas distintas; y encontrar el
  mensaje de error que el servidor se tragó.
---

:::story El hosting del sobrino
— Conseguí el hosting — anunció Seu Juvenal, con la satisfacción de quien
resolvió el problema del mes antes de las diez de la mañana.

— Vertexo iba a contratar un servidor — dijo Márcia.

— Pero este es gratis. El sobrino de Dona Marlene. Tiene una empresa.

El panel se abrió en una ventana de 2011, con botones degradados y un ícono
de disquete en el menú. En una esquina, un campo:

```text
PHP Version: 5.6.40    [Cambiar]
```

Dedé hizo clic en **Cambiar**. Las opciones eran 5.4, 5.6 y 7.0.

— ¿Hay 8?

— El sobrino dijo que el 8 es inestable.

PHP 8 había salido hacía seis años. El 5.6 había dejado de recibir
correcciones de seguridad hacía nueve.

— ¿Y el acceso? ¿Hay SSH?

— Hay FTP.

Seu Juvenal entregó un papel doblado con el usuario, la contraseña y —
escrita a mano, en una esquina, con un bolígrafo de otro color — la nota
*"no tocar la carpeta vieja"*.

Márcia guardó el papel en la carpeta del proyecto.

— ¿Esto es un riesgo para marzo?

— Esto es un riesgo para hoy.
:::

Ejecutar PHP parece la parte más simple del trabajo, y es donde vive la
trampa que más tiempo consume a quien está empezando: **el PHP que corre en
tu terminal casi nunca es el mismo que corre en el servidor.**

## Dos PHP en la misma máquina

```text
$ which php
/usr/bin/php
$ php -v
PHP 8.3.14 (cli)
```

El `(cli)` al final de la primera línea es el detalle que importa. Dice que
este es el PHP de **línea de comandos** — el que responde cuando escribes
`php` en una terminal.

Existe otro, el que atiende al navegador. Puede ser una versión distinta,
con un archivo de configuración distinto y un conjunto de extensiones
distinto, en la misma máquina, al mismo tiempo.

:::term SAPI
*Server API*: la forma en que PHP está acoplado a quien lo llama. `cli` es
la terminal. `fpm` es el proceso que se queda esperando que Nginx le mande
trabajo. `apache2handler` es el PHP embebido dentro de Apache. El mismo
archivo `.php` puede comportarse distinto en cada uno, porque cada uno lee
su propio `php.ini`.
:::

:::pitfall
El síntoma clásico: instalas una extensión, `php -m` muestra que está ahí, y
la página en el navegador sigue diciendo que no existe.

Son dos PHP. La confirmación lleva diez segundos — crea un archivo con
`<?php phpinfo();` dentro, ábrelo **desde el navegador** y compara la versión
y la ruta del `php.ini` con lo que dijo `php -v` en la terminal. Después
borra el archivo: `phpinfo()` muestra la configuración entera del servidor,
y no es información para dejar pública.
:::

## Una etiqueta, una salida

```php title="hola.php" numbered
<?php

echo "Hola, Casa Amarela\n";
```

```text
$ php hola.php
Hola, Casa Amarela
```

Listo. Programaste.

Vale la pena desarmar las tres líneas, porque cada una tiene una decisión
adentro.

**`<?php`** abre el modo PHP. Todo lo que esté antes de esa etiqueta —
incluso un espacio en blanco o una línea vacía — se envía directo a quien
pidió la página, sin pasar por el intérprete. Eso parece irrelevante y va a
importar dentro de dos párrafos.

**`echo`** imprime. No es una función, es una construcción del lenguaje, y
por eso funciona sin paréntesis.

**`"\n"`** es un salto de línea. Dentro de comillas dobles, la barra
invertida activa el modo "el próximo carácter es especial": `\n` se vuelve
salto de línea, `\t` se vuelve tabulación. Dentro de comillas simples eso no
pasa — `'\n'` son dos caracteres, una barra y una ene.

Y el **punto y coma** del final cierra la instrucción. Olvidar uno es el
error número uno de quien empieza, y el mensaje que produce tiene una
particularidad que vale conocer antes de encontrarla.

## Comentar

Tres formas, y vas a usar dos:

```php title="comentarios.php" numbered
<?php

// una línea, la forma estándar

# una línea también, heredada del shell, hoy rara

/*
   varias líneas
   para cuando la explicación no entra en una
*/

echo "Casa Amarela\n"; // un comentario al final de la línea también vale
```

El `//` es el que se usa. El `#` funciona y aparece en código antiguo. El
bloque `/* */` sirve para explicaciones largas — y tiene una variante con
dos asteriscos en la apertura, `/** */`, que las herramientas de análisis
leen como documentación.

:::key
Un comentario que explica **qué** hace la línea es ruido: la línea ya lo
dice. Un comentario que explica **por qué** la decisión fue esa es lo más
valioso que se puede dejar en un archivo.

`// suma 1 al contador` no ayuda a nadie. `// Vera pidió que el domingo no
cuente como atraso; la biblioteca no abre` va a seguir prestando servicio
dentro de cinco años.
:::

## La etiqueta que no vas a cerrar

La etiqueta de cierre, `?>`, es **opcional al final del archivo**. Más que
opcional: en un archivo que solo tiene PHP, se evita por convención, y la
razón es concreta.

:::compare left="El archivo que va a dar problemas" right="La forma correcta" lang="php"
<?php
function multa(): int
{
    return 80;
}
?>
---
<?php
function multa(): int
{
    return 80;
}
:::

Fíjate en el salto de línea después del `?>` del lado izquierdo. Está fuera
del modo PHP, así que es contenido — y se envía al navegador como si fuera
parte de la página.

Meses después, cuando alguien intente redirigir al usuario o enviar
cualquier otra información de cabecera, va a recibir esto:

```text
Warning: Cannot modify header information - headers already
sent by (output started at /app/funciones.php:7) in
/app/index.php on line 3
```

El mensaje es generoso: dice el archivo y la línea exacta donde empezó la
salida. La causa es un espacio en blanco después de un `?>` que no hacía
falta.

:::key
Un archivo que contiene solo PHP no lleva `?>`. Es una de las pocas reglas
de estilo que se justifica por una consecuencia técnica, y no por gusto.
:::

## Cuatro formas de imprimir

```php title="salida.php" numbered
<?php

$titulo = "O Cortiço";
$ejemplares = 3;

echo "Tenemos ", $ejemplares, " ejemplares de ", $titulo, "\n";
echo "Tenemos {$ejemplares} ejemplares de {$titulo}\n";
printf("Tenemos %d ejemplares de %s\n", $ejemplares, $titulo);
```

```text
Tenemos 3 ejemplares de O Cortiço
Tenemos 3 ejemplares de O Cortiço
Tenemos 3 ejemplares de O Cortiço
```

La primera línea usa `echo` con varios pedazos separados por comas. Salen
pegados, en orden.

La segunda usa **interpolación**: dentro de comillas dobles, PHP cambia el
nombre de la variable por su valor. Las llaves en `{$titulo}` no son
obligatorias cuando el nombre termina claramente, pero sí lo son cuando no
— y usarlas siempre te ahorra la decisión.

La tercera usa `printf`, que recibe un molde y los valores para encajar en
él. El `%d` dice "aquí va un número entero" y el `%s` dice "aquí va un
texto". Los valores vienen después, en el orden de los marcadores. Es más
trabajo para una frase corta y es lo que vas a querer cuando necesites
alinear columnas o controlar decimales.

Existe además `print`, que hace casi lo mismo que `echo` y acepta un solo
valor. La diferencia práctica es irrelevante; usa `echo`.

Y existe una cuarta, que no es salida para el usuario — es para ti:

```text
$ php -r 'var_dump(3, "3", 3.0, true, null);'
int(3)
string(1) "3"
float(3)
bool(true)
NULL
```

`var_dump` imprime el **tipo** junto con el valor. Fíjate en la diferencia
entre `int(3)` y `string(1) "3"`: con `echo`, los dos saldrían como `3`, y
nunca sabrías cuál es cuál. Esta es la herramienta que responde en lugar de
que tengas que adivinar, y va a aparecer en casi todas las páginas de aquí
en adelante.

## De la terminal al navegador

PHP nació para la web, y la segunda forma de ejecutarlo es por HTTP. No hace
falta instalar Apache ni Nginx: el propio PHP trae un servidor pequeño.

```text
$ php -S localhost:8000
[Thu Nov 21 10:02:11 2026] PHP 8.3.14 Development Server
(http://localhost:8000) started
```

El comando se queda corriendo y ocupa la terminal — es así. Sirve los
archivos de la carpeta donde estabas cuando lo iniciaste. Abre
<http://localhost:8000/hola.php> y aparece la misma frase, ahora dentro de
una página. Para cerrarlo, `Ctrl+C`.

:::diagram type="flowchart" caption="Dos caminos, el mismo archivo: cambia quién llama y adónde va la salida."
nodes:
  - { id: arq, type: io,      text: "hola.php" }
  - { id: cli, type: process, text: "php hola.php (CLI)" }
  - { id: web, type: process, text: "php -S (servidor)" }
  - { id: t,   type: io,      text: "terminal" }
  - { id: n,   type: io,      text: "navegador" }
edges:
  - { from: arq, to: cli }
  - { from: arq, to: web }
  - { from: cli, to: t }
  - { from: web, to: n }
:::

:::warning
El nombre que imprime es literal: **Development Server**. Atiende una
petición a la vez, no tiene una reescritura de URL decente y no aguanta
carga ninguna. Para aprender e investigar, alcanza. Producción es otra
conversación — y ciertamente no es el hosting del sobrino de Dona Marlene.
:::

## El archivo correcto, en el servidor equivocado

:::story Dos servidores
Tainá editó el archivo, guardó, recargó. Nada cambió.

Guardó de nuevo. Recargó de nuevo. Nada.

Agregó un `echo "PRUEBA"` gigante arriba de todo, con treinta signos de
exclamación. Recargó. Nada.

Borró el archivo entero. Recargó. La página siguió ahí, funcionando
perfectamente, mostrando un contenido que técnicamente ya no existía.

Fue en ese punto que llamó a Dedé, ya dudando de la naturaleza de la
realidad.

Él pidió la URL y abrió el historial de la terminal de ella. Había dos
`php -S` corriendo: uno en el puerto 8000, abierto esa mañana, y otro en el
8080, olvidado abierto hacía dos semanas, sirviendo una copia vieja de la
carpeta.

El navegador estaba en el 8080.

— Va a volver a pasar — dijo él. — Cuando pase, la primera pregunta no es
"qué escribí mal". Es "qué está corriendo".

Tainá lo anotó en el cuaderno. Era la segunda línea de la lista.
:::

Media hora después, con el puerto correcto, vino el segundo problema:
página en blanco. Sin error, sin texto, sin nada. Código fuente vacío.

## El error apunta donde lo notó

Ella había escrito esto:

```php title="roto.php" numbered
<?php

$titulo = "O Cortiço"
echo $titulo;
```

Ejecutándolo desde la terminal, aparece el mensaje:

```text
PHP Parse error:  syntax error, unexpected token "echo",
expecting "," or ";" in /app/roto.php on line 4
```

El error apunta a la **línea 4**, y el problema está en la **3**: falta un
punto y coma. Eso no es un defecto del mensaje. El analizador estaba leyendo
la línea 3 y todavía podía continuar — nada impide que una expresión ocupe
varias líneas. Solo descubrió que faltaba algo cuando encontró, en la línea
siguiente, una palabra que no puede aparecer ahí.

:::key
Un error de sintaxis apunta donde el analizador lo **notó**, no donde tú te
**equivocaste**. Regla práctica: lee la línea señalada y la anterior. En
nueve de cada diez casos el problema está en la anterior — punto y coma,
paréntesis o llave.
:::

Un `Parse error` tiene una característica que asusta la primera vez: impide
que el archivo **entero** se ejecute. No sale nada, ni siquiera las líneas
anteriores al error, porque PHP analiza todo el archivo antes de ejecutar la
primera instrucción.

## Adónde fue a parar el mensaje

Pero Tainá no vio ningún mensaje. Vio una página en blanco.

```text
$ php -i | grep -E "display_errors|error_log"
display_errors => Off => Off
error_log => no value => no value
```

`display_errors` desactivado quiere decir "no muestres errores a quien pidió
la página". `error_log` sin valor quiere decir "y no los escribas en ningún
archivo". Juntas, las dos configuraciones hacen que el mensaje vaya a la
salida de error del proceso del servidor — que, en un PHP-FPM, termina en
`/var/log/php8.3-fpm.log`, y no donde ella estaba mirando.

La información existió. Se produjo, se formateó y se archivó en otro lugar.

**En desarrollo, activa todo:**

```text title="php.ini — solo en desarrollo"
display_errors = On
display_startup_errors = On
error_reporting = E_ALL
```

**En producción, lo contrario — y no es opcional:**

```text title="php.ini — producción"
display_errors = Off
error_log = /var/log/php/errores.log
error_reporting = E_ALL
```

:::warning
`display_errors = On` en producción es una falla de seguridad. El mensaje de
error de PHP entrega rutas absolutas de archivos, nombres de funciones, a
veces fragmentos de consultas a la base de datos y valores de variables. Es
información gratis para quien esté sondeando el sitio.

Fíjate en que `error_reporting` sigue en `E_ALL` en los dos casos. La
diferencia no es **registrar menos** — es **mostrárselo a quién**. En
producción el detalle queda en el log, para el equipo, y el visitante ve
una página corta.
:::

Y existe una verificación que no cuesta nada:

```text
$ php -l roto.php
PHP Parse error: syntax error, unexpected token "echo" ...
Errors parsing roto.php

$ php -l hola.php
No syntax errors detected in hola.php
```

El `-l` viene de *lint*: revisa la sintaxis sin ejecutar el archivo. Es la
verificación más barata que existe y corre en milisegundos.

### La pantalla en blanco, en cuatro hipótesis

La pantalla en blanco asusta porque parece ausencia de información. Casi
siempre es una de estas cuatro cosas:

| Causa | Cómo confirmarla |
|---|---|
| Error de sintaxis con `display_errors` off | `php -l archivo.php` |
| Error fatal en ejecución | leer el log de PHP o del servidor |
| Memoria o tiempo agotados | buscar `Allowed memory size` en el log |
| Salida realmente vacía, sin error | `var_dump` antes del punto sospechoso |

Tabla: Ninguna se resuelve recargando la página, que es exactamente lo que
todo el mundo hace durante los primeros cinco minutos.

:::practice
Crea un archivo que llame a una función que no existe — `descontar()`, por
ejemplo — y ejecútalo por los dos caminos: `php archivo.php` y desde el
navegador con `php -S`. Compara lo que aparece en cada uno.

Esa diferencia es la misma que va a existir entre tu máquina y el servidor
de producción, y verla una vez ahorra horas después.
:::

:::note En tu carrera
Antes de aceptar tocar un sistema que no conoces — freelance, proyecto
nuevo, empresa nueva —, cuatro preguntas valen más que cualquier lectura de
código:

1. **¿Qué versión de PHP corre en producción?** Define lo que puedes usar.
2. **¿Cómo subo un cambio?** Si la respuesta es "FTP", acabas de descubrir
	 el mayor riesgo del proyecto, y no es técnico: cualquier persona con ese
	 papel puede publicar cualquier cosa, y nadie va a saber quién fue.
3. **¿Dónde están los logs?** Si nadie lo sabe, vas a depurar a ciegas.
4. **¿Existe un entorno igual al de producción donde pueda equivocarme?**
	 Si no existe, el entorno de pruebas es producción — y alguien tiene que
	 saberlo por escrito, antes del primer incidente, no después.

Hacer estas preguntas no es desconfianza. Es el equivalente a que un
electricista pregunte dónde está el disyuntor.
:::

:::summary
- Hay dos PHP en tu máquina: el de la terminal y el del servidor. Cada uno
	lee su propio `php.ini`.
- Un archivo solo con PHP no lleva `?>` — un espacio después de él se
	vuelve salida, y rompe cabeceras meses después.
- Un buen comentario explica por qué, no qué.
- `echo` imprime; la interpolación cambia la variable por su valor dentro
	de comillas dobles; `printf` encaja valores en un molde; `var_dump`
	muestra el tipo.
- `php -S` levanta un servidor de desarrollo, y solo sirve para eso.
- Un error de sintaxis apunta donde el analizador lo notó: lee la línea
	anterior.
- Una página en blanco es un error escondido, no la ausencia de error.
:::

:::exercise level=1
Escribe un archivo que imprima el nombre de la biblioteca, la cantidad de
títulos del acervo y el horario de atención, usando interpolación de
variables. Después cambia la interpolación por `printf` y compara las dos
versiones.

:::answer
```php
<?php

$nombre = "Casa Amarela";
$titulos = 4000;
$horario = "de 9 a 18 h";

echo "{$nombre}: {$titulos} títulos, {$horario}\n";
printf("%s: %d títulos, %s\n", $nombre, $titulos, $horario);
```

```text
Casa Amarela: 4000 títulos, de 9 a 18 h
Casa Amarela: 4000 títulos, de 9 a 18 h
```

Para una frase corta, la interpolación es más legible. `printf` empieza a
ganar cuando importa el formato — decimales, ancho de columna, alineación.
:::

:::exercise level=2
Reproduce la pantalla en blanco a propósito: crea un archivo con un error
de sintaxis y sírvelo con los errores desactivados. Después encuentra el
mensaje sin volver a activar los errores.

:::answer
```text
$ php -S localhost:8000 -d display_errors=0
```

Abre el archivo roto en el navegador: página en blanco. Ahora, sin tocar
ninguna configuración:

```text
$ php -l roto.php
PHP Parse error: syntax error ... on line 4
```

El `-d` sobrescribe una directiva solo para esa ejecución, lo que es
práctico para reproducir el comportamiento de producción sin editar el
`php.ini`.

Fíjate también en que el servidor embebido escribe los errores en la propia
terminal donde se inició — en este caso, la información estuvo todo el
tiempo en la ventana de al lado. En un servidor de verdad, estaría en un
archivo de log.
:::

:::exercise level=2
Crea dos archivos: un `funciones.php` que termina con `?>` seguido de una
línea en blanco, y un `index.php` que hace `require 'funciones.php'` y
después llama a `header('Location: /panel')`. El `require` inserta el
contenido de un archivo dentro de otro; `header` envía una información de
cabecera HTTP — aquí, una redirección. Ejecútalo y lee el error.

:::answer
```text
Warning: Cannot modify header information - headers already
sent by (output started at /app/funciones.php:6) in
/app/index.php on line 4
```

El mensaje entrega al culpable con archivo y línea: `funciones.php:6` es la
línea en blanco después del `?>`. Borra las dos últimas líneas del archivo y
la redirección vuelve a funcionar.

Vale reproducirlo una vez porque el mensaje asusta y la causa es ridícula —
y porque, en un sistema legado con cuarenta `include`, descubrir qué archivo
tiene el espacio de más es exactamente ese número al final de la primera
línea.
:::

:::exercise level=3
El archivo de abajo funciona en tu terminal y devuelve una página en blanco
en el hosting de la Casa Amarela. Enumera cuatro hipótesis, en el orden en
que las verificarías, y di cómo confirmas cada una.

```php
<?php
require 'config.php';
$conexion = conectar();
echo "ok";
```

:::answer
**1. Versión distinta de PHP.** Tu terminal corre 8.3; el hosting corre
5.6. Cualquier sintaxis posterior a 5.6 es error de sintaxis allá y código
válido aquí. Lo confirmo con un `phpinfo()` servido **por el mismo camino
que la aplicación**, no por la terminal.

**2. Errores desactivados escondiendo un error fatal.** Es la hipótesis más
probable, porque el síntoma es exactamente ese. Lo confirmo leyendo el log;
si nadie sabe dónde está, el `phpinfo()` de la hipótesis 1 ya lo responde.

**3. `config.php` no encontrado.** El `require` con ruta relativa depende
del directorio de trabajo, que en el servidor no es el mismo que en la
terminal. Un `require` que falla es un error fatal — y, con los errores
desactivados, es una página en blanco. Lo confirmo con
`var_dump(getcwd())`, que imprime el directorio actual, y lo arreglo
cambiándolo por `require __DIR__ . '/config.php'`, donde `__DIR__` es la
carpeta del propio archivo.

**4. Extensión ausente.** La función `conectar()` probablemente habla con
una base de datos. Si la extensión correspondiente no está compilada en el
PHP del servidor, la función no existe. Lo confirmo buscando la extensión
en la salida de `phpinfo()`.

El orden es lo que vale del ejercicio. Las dos primeras hipótesis son
verificaciones de treinta segundos que revelan las otras dos: `phpinfo()`
responde versión, errores, ruta del log y extensiones de una sola vez.
Investigar el código antes de mirar esa página es el error de método más
común de quien empieza — la información ya existe, alguien solo tiene que
leerla.
:::

:::story Optimizada para 5.6
Dos semanas después, el sobrino de Dona Marlene respondió al pedido sobre
PHP 8.

> *"No lo recomendamos. Nuestra infraestructura está optimizada para 5.6,
> que es la versión más estable del mercado."*

Dedé se lo reenvió a Vera, sin ningún comentario.

La respuesta llegó en cuatro minutos:

> *"Él también cree que el Sistema está buenísimo."*

Se lo reenvió también a Márcia. Esa tardó más.

> *"Ponlo en el acta. Si cambiamos de hosting en marzo, quiero que esté
> escrito en enero que yo avisé."*
:::
