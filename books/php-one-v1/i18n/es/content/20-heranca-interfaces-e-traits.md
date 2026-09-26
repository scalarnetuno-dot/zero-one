---
source_hash: b2dc06b01945
title: "Herencia, interfaces y traits"
number: 20
slug: heranca-interfaces-e-traits
part: p4
kicker: "La pizarra tenía tres cajas cuando llegó Vera. Tenía diez cuando se fue, y ella no dibujó ninguna."
goal: >-
  Elegir entre herencia, interfaz, trait y composición con un criterio que
  puedas defender, y reconocer, antes de dibujar la tercera caja, cuándo la
  jerarquía va a explotar.
---

:::story Y el infantil didáctico importado
En la pizarra había una caja que decía `Libro` y tres flechas saliendo de
ella: `LibroInfantil`, `LibroDidactico`, `LibroDeReferencia`.

—El infantil no sale por catorce días, sale por siete —explicó Dedé—. El
de referencia no sale.

Vera estaba ahí por otro motivo, esperando a Tainá para revisar una lista,
y miró la pizarra como se mira una señal de tránsito nueva.

—¿Y el infantil didáctico?

Dedé dibujó una cuarta caja.

—¿Y el importado? El importado no sale, sea lo que sea.

La cuarta caja recibió una quinta al lado.

—Y el infantil didáctico importado —dijo Vera, sin entonación de pregunta.

Tainá contó las cajas.

—Ocho.

—Diez —dijo Vera—. Te olvidaste de los de referencia.
:::

:::art caption="Toda jerarquía de clases cabe en la pizarra hasta que llega la bibliotecaria."
src="toda-hierarquia-de-classes-cabe-no-quadro-ate-a-bibliotecaria-chegar.png"
Viñeta editorial minimalista sobre fondo blanco: una pizarra blanca donde
empieza un diagrama limpio —una caja "Libro" con tres flechas hacia
"Infantil", "Didáctico" y "Referencia"— que, en la mitad derecha, degenera
en cajas cada vez más pequeñas y apretadas: "InfantilDidáctico",
"InfantilImportado", "InfantilDidácticoImportado", con flechas cruzadas
escapándose por el borde. El desarrollador, marcador en mano, ya no tiene
espacio y escribe en el marco. Apoyada en el marco de la puerta, una
bibliotecaria mayor, con lentes y brazos cruzados, dicta la siguiente
combinación sin cambiar de expresión. Una pasante cuenta las cajas con los
dedos. Pocos elementos, humor seco, estética de revista de tecnología.
:::

## `extends` es un parentesco que no deshaces

La herencia es el mecanismo más antiguo de los tres y el más fácil de
escribir:

```php title="src/Acervo/LibroInfantil.php" numbered
<?php

namespace CasaAmarela\Acervo;

class LibroInfantil extends Libro
{
    public function plazoEnDias(): int
    {
        return 7;
    }
}
```

`extends` dice: esta clase empieza con todo lo que tiene la de arriba
—propiedades, métodos, constructor— y agrega o cambia lo que quiera.

El problema no aparece en la primera caja. Aparece en la tercera.

Infantil, didáctico e importado son tres características
**independientes**: un libro puede tener cualquier combinación de ellas.
Como cada clase solo puede extender a otra —PHP no tiene herencia múltiple,
y `extends` acepta un solo nombre—, cubrir todas las combinaciones exige una
clase por combinación.

| Características | Clases necesarias |
|---|---|
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 16 |

Tabla: Cada característica nueva **duplica** la pizarra. Es lo que hizo
Vera en cuarenta segundos sin saber qué era una clase.

:::key
La herencia sirve bien para la variación en **un solo eje**, cuando las
opciones son excluyentes: o es una, o es otra, nunca las dos.

Si dos características pueden aparecer juntas, no son subclases. Son
datos.
:::

## Lo que promete una subclase

Hay una regla más importante que el conteo de cajas, y es fácil de
enunciar: **donde se acepta al padre, el hijo tiene que servir**.

Si una función recibe un `Libro` y el programa le pasa un
`LibroDeReferencia`, la función no puede romperse. No sabe, y no debería
necesitar saber, cuál de los dos llegó.

Mira lo que pasa cuando se rompe la regla:

```php title="src/Acervo/LibroDeReferencia.php" numbered
<?php

namespace CasaAmarela\Acervo;

class LibroDeReferencia extends Libro
{
    public function plazoEnDias(): int
    {
        throw new \RuntimeException('La referencia no sale de aquí');
    }
}
```

Parece razonable: la referencia de verdad no sale. Pero ahora toda función
que recibía un `Libro` y preguntaba el plazo ganó una forma nueva de morir,
y la única manera de protegerse es revisar el tipo antes:

```php
if ($libro instanceof LibroDeReferencia) {
    continue;
}
```

Ese `if` va a aparecer en cinco lugares, y el sexto va a faltar. La
herencia que prometía eliminar condicionales acaba de esparcir una.

:::pitfall
La prueba de "**es un**" es la que se enseña primero y la que más falla.
Un libro de referencia *es un* libro, en el lenguaje común, y aun así no
sirve como uno.

La prueba que funciona es otra: *si cambio al padre por el hijo, ¿algo que
funcionaba deja de funcionar?* Si la respuesta es sí, la herencia está
mintiendo, y la mentira se va a cobrar en un `if` que alguien olvidó.
:::

## Interfaz: el contrato sin el parentesco

No todo lo que se comporta igual necesita ser pariente.

Durante la migración, la Casa Amarela tiene dos acervos funcionando al
mismo tiempo: el del Sistema, que sigue atendiendo el mostrador, y el
nuevo. El informe de circulación necesita contar ejemplares de los dos.

Las dos clases no tienen nada en común por dentro —una lee `registro` y la
otra lee `cod_ejemplar`— y tienen que responder a las mismas tres
preguntas.

```php title="src/Circulacion/Prestable.php" numbered
<?php

namespace CasaAmarela\Circulacion;

interface Prestable
{
    public function identificacion(): string;

    public function disponible(): bool;

    public function plazoEnDias(): int;
}
```

Una interfaz es una lista de firmas sin ningún cuerpo. No dice cómo se
hace; dice qué tiene que existir.

```php title="src/Acervo/Ejemplar.php" numbered
<?php

namespace CasaAmarela\Acervo;

use CasaAmarela\Circulacion\Prestable;

class Ejemplar implements Prestable
{
    // ... constructor del capítulo anterior

    public function identificacion(): string
    {
        return "registro {$this->registro}";
    }

    public function disponible(): bool
    {
        return $this->condicion === 'bueno';
    }

    public function plazoEnDias(): int
    {
        return $this->libro->clasificacion->plazoEnDias();
    }
}
```

PHP cobra el contrato entero, en el momento de cargar la clase:

```text
Fatal error: Class Ejemplar contains 1 abstract method and must
therefore be declared abstract or implement the remaining methods
(Prestable::plazoEnDias)
```

Y el código que la usa no necesita saber de qué acervo vino el ítem:

```php title="informe.php" numbered
<?php

use CasaAmarela\Circulacion\Prestable;

function contarDisponibles(array $items): int
{
    $total = 0;

    foreach ($items as $item) {
        if ($item instanceof Prestable && $item->disponible()) {
            $total++;
        }
    }

    return $total;
}
```

:::key
La interfaz es el mecanismo que Laravel va a usar para casi todo, y el
motivo es este: te deja escribir código contra **lo que una cosa hace** en
lugar de contra **lo que es**.

Una clase puede implementar tantas interfaces como quiera. El límite de una
sola vale para `extends`.
:::

## Clase abstracta: contrato con parte del cómo

Una interfaz no guarda código. Cuando las implementaciones comparten un
pedazo de verdad, existe el término medio:

```php title="src/Circulacion/ItemDeAcervo.php" numbered
<?php

namespace CasaAmarela\Circulacion;

abstract class ItemDeAcervo implements Prestable
{
    abstract public function plazoEnDias(): int;

    public function plazoDescrito(): string
    {
        $dias = $this->plazoEnDias();

        return $dias === 1 ? '1 día' : "{$dias} días";
    }
}
```

Una `abstract class` no se puede instanciar: `new ItemDeAcervo()` es un
error. Una `abstract public function` no tiene cuerpo: quien herede está
obligado a escribirlo.

La diferencia cabe en una línea: **la interfaz dice el qué; la clase
abstracta dice el qué y un pedazo del cómo**. Y la clase abstracta gasta tu
único `extends`, lo que es un precio real.

## Trait: el copiar y pegar que hace el compilador

El tercer mecanismo es el más literal de los tres. Un `trait` es un bloque
de código que se **copia dentro** de las clases que lo usan.

```php title="src/Circulacion/RegistraHistorial.php" numbered
<?php

namespace CasaAmarela\Circulacion;

trait RegistraHistorial
{
    private array $historial = [];

    public function registrar(string $evento): void
    {
        $this->historial[] = date('Y-m-d H:i:s') . ' ' . $evento;
    }

    public function historial(): array
    {
        return $this->historial;
    }
}
```

```php title="src/Acervo/Ejemplar.php" numbered
class Ejemplar implements Prestable
{
    use \CasaAmarela\Circulacion\RegistraHistorial;
```

:::pitfall
Este `use` **no es** el `use` del principio del archivo.

Al principio, fuera de cualquier clase, `use` importa un nombre: es un
alias y no carga nada. Dentro del cuerpo de una clase, `use` copia un trait
dentro de ella.

La misma palabra, dos trabajos sin ninguna relación. Es la elección de
vocabulario más desafortunada del PHP moderno, y vas a leer código de los
dos tipos en el mismo archivo.
:::

Cuando dos traits traen un método con el mismo nombre, PHP no elige por ti:

```text
Fatal error: Trait method RegistraAuditoria::registrar has not been
applied as Ejemplar::registrar, because of collision with
RegistraHistorial::registrar
```

La salida es declarar quién gana y, opcionalmente, darle un alias al que
pierde:

```php
    use RegistraHistorial, RegistraAuditoria {
        RegistraHistorial::registrar insteadof RegistraAuditoria;
        RegistraAuditoria::registrar as registrarAuditoria;
    }
```

Funciona. Y es el mejor aviso que PHP puede dar de que los dos traits
querían ser la misma cosa, o de que la clase está haciendo dos trabajos.

:::key
El trait del ejemplo trajo una propiedad consigo: `$historial`. Pasa a ser
una propiedad de la clase, como cualquier otra, y no aparece en el cuerpo
de la clase, donde alguien la buscaría.

Un trait con estado es la forma más fácil de que una clase gane
propiedades que nadie recuerda haber declarado. Prefiere traits sin
estado; cuando necesites estado compartido, el mecanismo correcto es el de
la sección siguiente.
:::

## Composición: "tiene un" en lugar de "es un"

La pizarra de Vera tenía diez cajas porque tres características se
volvieron tipos. No son tipos. Son datos:

```php title="src/Acervo/Clasificacion.php" numbered
<?php

namespace CasaAmarela\Acervo;

final class Clasificacion
{
    public function __construct(
        public readonly bool $infantil = false,
        public readonly bool $didactico = false,
        public readonly bool $referencia = false,
        public readonly bool $importado = false,
    ) {}

    public function prestable(): bool
    {
        return !$this->referencia && !$this->importado;
    }

    public function plazoEnDias(): int
    {
        return $this->infantil ? 7 : 14;
    }
}
```

Y el `Libro` **tiene una** clasificación:

```php title="src/Acervo/Libro.php" numbered
<?php

namespace CasaAmarela\Acervo;

class Libro
{
    public function __construct(
        public readonly string $titulo,
        public readonly int $anio,
        public readonly Clasificacion $clasificacion,
    ) {}
}
```

```php
$vidasSecas = new Libro('Vidas Secas', 1938, new Clasificacion(
    didactico: true,
));

echo $vidasSecas->clasificacion->plazoEnDias(), "\n";
```

```text
14
```

Diez cajas se volvieron una clase y cuatro campos. Y cuando don Juvenal
llegue con los audiolibros —que salen por veintiún días, porque doña
Marlene tarda—, el costo es **una línea**, no duplicar la pizarra.

:::term Composición
Armar un comportamiento juntando objetos, en lugar de heredando de ellos.
"El libro tiene una clasificación" en lugar de "el libro es un libro
infantil".

El intercambio es siempre el mismo: escribes una línea más para delegar, y
ganas el derecho a cambiar de idea sin tocar el árbol.
:::

Cuatro booleanos no son la última palabra en modelado: el día que la Casa
Amarela tenga quince marcas, esto se vuelve una lista. Lo que ya está bien
es la dirección: crecer sumando campos, no sumando clases.

## Cómo elegir

| Quieres | Usa |
|---|---|
| que clases sin parentesco respondan a las mismas llamadas | interfaz |
| contrato más un pedazo de implementación común | clase abstracta |
| repetir un bloque de código sin estado en clases distintas | trait |
| variar el comportamiento en más de un eje | composición |
| variar en un solo eje, con opciones excluyentes | herencia |

Tabla: En la duda entre herencia y composición, empieza por composición.
Cambiar composición por herencia después es una tarde; el camino inverso es
un mes.

:::note En tu carrera
En una entrevista, "¿cuál es la diferencia entre clase abstracta e
interfaz?" es una pregunta para memorizar. La versión que separa a quien
entendió es la siguiente, y puedes hacértela a ti mismo antes de dibujar
cualquier jerarquía:

*Si mañana aparece una combinación que no previ, ¿agrego un campo o agrego
una clase?*

Quien responde "un campo" está componiendo. Quien responde "una clase" está
en un árbol que se va a duplicar, y vale la pena decirlo en la reunión
**antes** de la tercera caja, porque después de la octava la conversación
ya no es técnica, es sobre plazos.
:::

:::tree title="Dónde estamos ahora"
acervo/
  src/
    Acervo/
      Libro.php            # tiene una Clasificacion
      Clasificacion.php    # final, readonly
      Ejemplar.php         # implements Prestable, use RegistraHistorial
    Circulacion/
      Prestable.php        # interfaz
      RegistraHistorial.php  # trait
    Lectores/
      Lector.php
    Prestamos/
      Multa.php
    Legado/
      Libro.php
  informe.php
:::

:::summary
- `extends` copia todo de la clase de arriba y gasta el único parentesco
  que tiene la clase.
- Las características independientes duplican el árbol: tres se vuelven
  ocho clases.
- La regla de la subclase es servir en lugar del padre; si lanza donde el
  padre respondía, la herencia está mintiendo.
- La interfaz es contrato sin código; una clase implementa tantas como
  quiera.
- La clase abstracta es contrato con parte de la implementación, y cuesta
  el `extends`.
- El trait es código copiado dentro de la clase; un conflicto de nombres es
  error fatal, resuelto con `insteadof`.
- El `use` del principio del archivo importa un nombre; el `use` dentro de
  la clase copia un trait.
- La composición cambia "es un" por "tiene un", y crece sumando campos en
  lugar de clases.
:::

:::checkpoint
Sabes decir por qué la pizarra de Vera llegó a diez cajas, declaras e
implementas una interfaz, reconoces un trait que trajo estado escondido, y
puedes justificar por escrito —en dos frases— cuándo heredas, cuándo
compones y cuándo declaras un contrato.
:::

:::exercise level=1
La Casa Amarela presta, además de libros, tres lectores de pantalla donados
por una ONG. Tienen número de patrimonio en lugar de registro, salen por
treinta días y no se pueden renovar.

Decide: `LectorDePantalla extends Ejemplar`, `LectorDePantalla implements
Prestable`, ¿o ninguna de las dos? Justifícalo en dos frases.

:::answer
`implements Prestable`.

Un lector de pantalla no es un ejemplar de libro: no tiene registro, no
tiene un `Libro` dentro, no tiene condición de conservación del papel.
Heredar de `Ejemplar` traería todo eso consigo y obligaría a la clase a
fingir que tiene un libro.

Lo que tiene en común con un ejemplar es el **comportamiento**: se
identifica, está disponible o no, tiene plazo. Es exactamente lo que
describe la interfaz, y por eso el informe de circulación puede contar los
dos sin saber la diferencia.
:::

:::exercise level=2
Escribe la `Clasificacion` con un quinto caso: audiolibro, que sale por
veintiún días.

La regla de la Casa Amarela es: la referencia y el importado no salen;
entre los que salen, vale el plazo más largo aplicable —audiolibro (21)
antes que común (14), e infantil (7) solo cuando el libro no sea
audiolibro.

Escribe `plazoEnDias()` y explica por qué importa el orden de las
condiciones.

:::answer
```php title="src/Acervo/Clasificacion.php" numbered
    public function plazoEnDias(): int
    {
        if ($this->audiolibro) {
            return 21;
        }

        if ($this->infantil) {
            return 7;
        }

        return 14;
    }
```

El orden importa porque las condiciones **no son excluyentes**: un
audiolibro infantil cumple las dos. Quien escribiera `infantil` primero le
devolvería 7, contrariando la regla de Vera.

Es la misma trampa de la jerarquía de clases, ahora dentro de un método, y
por eso es preferible aquí: una regla ambigua en un `if` es una línea para
corregir, y la misma ambigüedad en un árbol de clases es una clase
`LibroInfantilAudiolibro` para borrar, con todo lo que ya dependía de ella.

Un detalle que vale la pena escribir en un comentario o en una prueba: la
regla "vale el plazo más largo" y el orden de las condiciones tienen que
estar de acuerdo. Si mañana alguien agrega un caso de 30 días al final de
la fila, nunca se va a alcanzar.
:::

:::exercise level=3
Recibes este código para revisar. Funciona, tiene las pruebas pasando y lo
escribió alguien con experiencia.

```php
abstract class Informe
{
    use ConectaBase;
    use FormateaMoneda;
    use EnviaCorreo;
    use GeneraPdf;

    abstract public function consultar(): array;

    public function ejecutar(): void
    {
        $filas = $this->consultar();
        $pdf = $this->generarPdf($filas);
        $this->enviar($pdf);
    }
}

class InformeDeCirculacion extends Informe { /* ... */ }
class InformeDeMultas extends Informe { /* ... */ }
```

Señala los dos problemas estructurales y propón el cambio mínimo que mejora
sin reescribir todo.

:::answer
**Primer problema: la clase abstracta se volvió un depósito.** Hace cuatro
cosas sin relación —habla con la base, formatea dinero, manda correos y
genera PDF— y todo informe hereda las cuatro, las use o no. Un informe que
solo imprime en pantalla carga el envío de correo consigo, y nadie puede
probar la consulta sin arrastrar el resto.

**Segundo problema: los traits esconden dependencias.** Mirando
`InformeDeCirculacion`, no hay nada que diga que necesita una conexión a la
base y un servidor de correo configurado. Eso está tres archivos más
arriba, dentro de traits, y solo aparece cuando se rompe.

**El cambio mínimo** no es borrar la jerarquía. Es quitar los dos traits
más pesados —`EnviaCorreo` y `ConectaBase`— y pasar lo que hacen como
objetos recibidos en el constructor:

```php
abstract class Informe
{
    use FormateaMoneda;

    public function __construct(
        private readonly BaseDeDatos $base,
        private readonly Correo $correo,
    ) {}

    abstract public function consultar(): array;
}
```

Lo que se gana es visible en la primera línea: ahora la clase **declara**
de qué depende. Lo que se pierde es la comodidad de no pasar nada, y esa
comodidad era lo que hacía que la prueba necesitara una base de verdad.

`FormateaMoneda` puede quedarse: es un trait sin estado, sin dependencia
externa, y su costo es cero. No todo trait es un problema; el problema es
el trait que trae el mundo consigo.
:::
