---
source_hash: 7bea13b9a37f
title: "Encapsulamiento"
number: 19
slug: encapsulamento
part: p3
kicker: "El informe decía que tres ejemplares estaban prestados dos veces. Seis lugares distintos escribían en esa columna."
goal: >-
  Elegir qué queda público, escribir un objeto cuyo estado inválido sea
  imposible de alcanzar desde fuera, usar `readonly` para lo que no cambia y
  reconocer cuándo `static` se volvió una variable global con otro nombre.
---

:::story Seis lugares
El informe de circulación de febrero acusó tres ejemplares prestados dos
veces al mismo tiempo. Físicamente imposible: el libro estaba en el
estante, y Vera trajo uno de ellos a la reunión como prueba.

Dedé buscó en el Sistema quién escribía en la columna `status` de los
ejemplares.

```text
$ grep -rn "status *=" *.php | wc -l
6
```

—Seis —dijo.

—¿Seis funciones?

—Seis lugares. La pantalla de préstamo, la de devolución, la de
renovación, el importador, un script de corrección que alguien ejecutó en
2019 y dejó en la carpeta, y el informe.

Tainá tardó un momento con el último.

—¿El informe escribe?

—El informe corrige. Cuando encuentra una línea rara, la arregla.

—¿La arregla para qué?

—Para que salga bonito.
:::

## `public` es un permiso para siempre

El `Ejemplar` que el proyecto tiene hoy no impide nada:

```php title="src/Acervo/Ejemplar.php" numbered
<?php

namespace CasaAmarela\Acervo;

class Ejemplar
{
    public function __construct(
        public int $registro,
        public Libro $libro,
        public string $condicion = 'bueno',
    ) {}
}
```

Todas las propiedades son públicas, y público quiere decir que cualquier
línea de cualquier archivo puede escribir cualquier cosa:

```php
$ejemplar->condicion = 'prestadoo';
$ejemplar->condicion = 'qué sé yo';
$ejemplar->registro = -3;
```

Ningún aviso. Tres condiciones que no existen, un registro negativo, y el
objeto sigue circulando por el programa como si estuviera entero.

Es la misma enfermedad de la columna `status` del Sistema, un piso más
arriba. El problema nunca fue la escritura en sí: fue que hubiera seis
lugares con permiso para escribir, y ninguno con la obligación de revisar.

:::key
`public` no es "lo predeterminado". Es una decisión, y es casi
irreversible: el día que quieras cerrar la propiedad, vas a tener que
encontrar y corregir a todos los que aprendieron a escribir en ella.

Empieza cerrado. Abrir después cuesta una línea; cerrar después cuesta una
reunión.
:::

## `private`: el cartel que PHP fiscaliza

Cambia una palabra:

```php title="src/Acervo/Ejemplar.php" numbered
    public function __construct(
        public int $registro,
        public Libro $libro,
        private string $condicion = 'bueno',
    ) {}
```

Y los intentos desde fuera dejan de funcionar:

```php
$ejemplar->condicion = 'qué sé yo';
```

```text
Fatal error: Uncaught Error: Cannot access private property
CasaAmarela\Acervo\Ejemplar::$condicion
```

La lectura también se detiene: `private` cierra la puerta en los dos
sentidos.

Son tres niveles, y en el día a día usas dos:

| | Quién llega |
|---|---|
| `public` | cualquier código, desde cualquier lugar |
| `protected` | la propia clase y las que hereden de ella |
| `private` | solo la propia clase |

Tabla: `protected` es una elección para quien ya decidió que la clase va a
tener descendientes. Mientras no los tenga, `private` es la respuesta
correcta.

:::pitfall
La visibilidad de PHP la fiscaliza el lenguaje, y por eso funciona: es
distinta de la convención de otros lenguajes, en los que un guion bajo
delante del nombre pide amablemente que nadie lo toque.

Pero vale por **clase**, no por objeto. Un método de `Ejemplar` puede leer
la `condicion` privada de *otro* `Ejemplar` recibido como parámetro. Eso
sorprende a quien llega de fuera y es lo que permite escribir un
`equals()` honesto.
:::

## Invariante

Cerrar la propiedad no sirve de nada si el objeto puede nacer mal.

:::term Invariante
Una afirmación sobre el objeto que tiene que ser verdadera **desde el
nacimiento hasta el final**, pase lo que pase entre una cosa y otra.

No es validación de formulario, que ocurre una vez a la entrada. Es una
promesa permanente de la clase: si se cumple, ningún código que reciba ese
objeto necesita revisarlo de nuevo.
:::

El `Ejemplar` de la Casa Amarela tiene tres:

1. el registro es un número positivo;
2. la condición es una de las cinco que el acervo reconoce;
3. un ejemplar prestado no puede prestarse de nuevo.

Las dos primeras son sobre el nacimiento. La tercera es sobre el cambio.

## El constructor que rechaza

```php title="src/Acervo/Ejemplar.php" numbered
<?php

namespace CasaAmarela\Acervo;

class Ejemplar
{
    private const CONDICIONES = [
        'bueno', 'prestado', 'danado', 'restauracion', 'extraviado',
    ];

    public function __construct(
        public int $registro,
        public Libro $libro,
        private string $condicion = 'bueno',
    ) {
        if ($registro <= 0) {
            throw new \InvalidArgumentException(
                "Registro inválido: {$registro}"
            );
        }

        if (!in_array($condicion, self::CONDICIONES, true)) {
            throw new \InvalidArgumentException(
                "Condición desconocida: {$condicion}"
            );
        }
    }
}
```

Tres cosas nuevas en la misma pantalla, y las tres son cortas.

`private const CONDICIONES` es una **constante de clase**: un valor fijo
que pertenece a la clase en lugar de a cada objeto. Se escribe una vez y se
lee con `self::CONDICIONES`; `self` quiere decir "esta clase de aquí".

`throw` interrumpe el método en el acto y le entrega el problema a quien
llamó. Es el mismo mecanismo de `PDOException`, ahora partiendo de tu
código. `InvalidArgumentException` es el tipo que PHP ofrece para decir
"el argumento que pasaste está fuera de lo acordado".

La barra delante de `\InvalidArgumentException` es la misma de `\PDO`: la
clase vive en la raíz, y este archivo tiene namespace.

```php
$ejemplar = new Ejemplar(-3, $libro);
```

```text
Fatal error: Uncaught InvalidArgumentException: Registro inválido: -3
```

El objeto no existió. No existe, en ningún lugar del programa, un
`Ejemplar` con registro negativo, y esa es una afirmación sobre el sistema
entero que cabe en cuatro líneas.

## Getter y setter no son obligatorios

El reflejo de quien aprendió orientación a objetos en un curso es este:

```php
public function getCondicion(): string
{
    return $this->condicion;
}

public function setCondicion(string $c): void
{
    $this->condicion = $c;
}
```

Con esos dos métodos, la propiedad volvió a ser pública, con dos líneas
más, un nombre peor y la apariencia de estar protegida. El `setCondicion`
acepta `'qué sé yo'` exactamente como lo aceptaba el `public`.

Pregúntate dos cosas antes de escribir cada uno:

**¿El lado de fuera lo necesita?** Si nadie lo llama, no lo escribas. Un
método público que no se llama sigue siendo una promesa que alguien puede
cobrar mañana.

**¿El cambio tiene nombre?** A un ejemplar no "se le cambia la condición a
prestado". **Se presta**. El nombre del método es el nombre del
acontecimiento, y es ahí donde la regla encuentra dónde vivir.

## `readonly`: el dato que no cambia de idea

El registro no cambia. Una vez pegada la etiqueta en el libro, ese número
es de ese ejemplar hasta el final.

```php title="src/Acervo/Ejemplar.php" numbered
    public function __construct(
        public readonly int $registro,
        public readonly Libro $libro,
        private string $condicion = 'bueno',
    ) {
```

```php
$ejemplar->registro = 9;
```

```text
Fatal error: Uncaught Error: Cannot modify readonly property
CasaAmarela\Acervo\Ejemplar::$registro
```

`readonly` permite escribir una vez, desde dentro de la clase, y rechaza
todo lo demás. Con él, `public` deja de ser peligroso: leer no rompe nada,
y escribir ya no es posible.

Es la combinación que resuelve la mayoría de los casos: **público y
`readonly` para lo que no cambia, privado para lo que cambia**.

:::key
La pregunta que separa los dos es siempre la misma, y no es técnica: *en
el mundo real, ¿esto cambia?*

El registro no cambia. El libro de ese ejemplar no cambia. La condición
cambia todo el tiempo, y por eso es la única que necesita una puerta con
nombre.
:::

## Una puerta para cada cambio

Falta la tercera invariante, que es sobre el cambio y no sobre el
nacimiento.

```php title="src/Acervo/Ejemplar.php" numbered
    public function condicion(): string
    {
        return $this->condicion;
    }

    public function disponible(): bool
    {
        return $this->condicion === 'bueno';
    }

    public function prestar(): void
    {
        if ($this->condicion !== 'bueno') {
            throw new \RuntimeException(
                "Ejemplar {$this->registro} no sale: "
                . $this->condicion
            );
        }

        $this->condicion = 'prestado';
    }

    public function devolver(
        string $condicionAlVolver = 'bueno',
    ): void {
        if ($this->condicion !== 'prestado') {
            throw new \RuntimeException(
                "Ejemplar {$this->registro} no está prestado"
            );
        }

        if (!in_array($condicionAlVolver, self::CONDICIONES, true)) {
            throw new \InvalidArgumentException(
                "Condición desconocida: {$condicionAlVolver}"
            );
        }

        $this->condicion = $condicionAlVolver;
    }
```

Ahora la columna tiene una sola puerta, y la puerta revisa:

```php
$ejemplar->prestar();
$ejemplar->prestar();
```

```text
Fatal error: Uncaught RuntimeException:
Ejemplar 2117 no sale: prestado
```

Los tres ejemplares prestados dos veces del informe de febrero dejan de ser
posibles, no porque el equipo empezó a tener más cuidado, sino porque ya no
existe un camino que lleve hasta ahí.

Y fíjate en `devolver`: acepta la condición de vuelta, porque los libros
vuelven rotos. Lo que no acepta es cualquier texto, y no acepta devolver lo
que no salió.

:::note En tu carrera
"Seis lugares escriben en esa columna" es una frase que vas a decir, y la
respuesta casi siempre es "entonces suma uno". Una séptima pantalla
necesita cambiar la condición, nadie quiere tocar las seis existentes, y el
plazo es el martes.

El camino que suele funcionar no es pedir una refactorización: es escribir
la puerta, usarla en la pantalla nueva, y migrar uno de los seis cada vez
que alguien tenga que abrir ese archivo por otro motivo. La conversación
cambia cuando puedes decir "hoy son cuatro" en una reunión en la que, el
mes pasado, eran seis.

Guarda el número. Una deuda técnica sin número se vuelve opinión, y la
opinión pierde contra el plazo todas las veces.
:::

## `static`: herramienta o variable global disfrazada

Una propiedad `static` pertenece a la clase, no al objeto: existe una sola,
compartida por todos.

```php
class Ejemplar
{
    public static int $prestadosHoy = 0;
}
```

Eso no es un contador del acervo. Es una variable global con un nombre más
bonito: cualquier código puede sumar, nadie tiene que decir por qué, y el
valor no pertenece a ningún objeto en particular.

La prueba que separa el uso legítimo del disfraz es corta: **¿el valor
depende de quién está usando el sistema ahora?** Si depende, `static` es el
lugar equivocado.

Un `static` que guarda la cotización de la moneda del día es discutible.
Uno que guarda el usuario conectado es un defecto esperando un servidor que
atienda dos peticiones al mismo tiempo, y así es como, en producción, Vera
ve el nombre de Neide en la esquina de la pantalla.

Los métodos `static` tienen el mismo olor cuando guardan estado, y son
inofensivos cuando no lo guardan: una función de conversión que solo
depende de los argumentos puede ser `static` sin ningún problema.

## La superficie pública es una promesa

Todo lo público es una promesa a quien usa la clase: *esto va a seguir
existiendo, con este nombre y este comportamiento*.

El `Ejemplar` de ahora promete cinco cosas —`registro`, `libro`,
`condicion()`, `disponible()`, `prestar()`, `devolver()`— y esconde una:
que la condición es un `string`. Mañana puede volverse otra cosa sin que
cambie una línea de fuera, porque nadie de fuera tiene cómo saber qué es.

Eso es lo que compró el encapsulamiento. No es organización; es libertad
de cambiar de idea después.

Hay una palabra que hace la promesa opuesta. `final` delante de una clase
dice que nadie puede heredar de ella, y delante de un método, que nadie
puede cambiar su comportamiento. Reduce lo que prometes, y por eso aumenta
lo que puedes cambiar.

:::tree title="Dónde estamos ahora"
acervo/
  src/
    Acervo/
      Libro.php
      Ejemplar.php   # readonly + condición privada con puerta
    Lectores/
      Lector.php
    Legado/
      Libro.php
  conexion.php
  listar.php
  prestar.php
  recibo.php
:::

:::milestone
Fin de la Parte 3. El proyecto tiene nombre, dependencias declaradas,
clases con dirección y objetos que se niegan a nacer mal. Un archivo se
volvió treinta, y treinta archivos con contrato son otra cosa que treinta
archivos sueltos.
:::

:::summary
- `public` es un permiso permanente: empieza cerrado, abre cuando alguien
  lo necesite.
- `private` lo fiscaliza el lenguaje y vale por clase, no por objeto.
- Una invariante es lo que tiene que ser verdad desde el nacimiento hasta
  el final; el constructor es donde empieza a valer.
- `throw` en el constructor impide que el objeto inválido exista en
  cualquier lugar del programa.
- Getter y setter automáticos le devuelven la propiedad al público con más
  líneas.
- `readonly` vuelve seguro a `public` para lo que no cambia.
- Un cambio de estado pasa por un método con nombre de acontecimiento, y
  el método revisa antes.
- Un `static` que depende de quién está usando el sistema es una variable
  global disfrazada.
- Lo público es promesa; lo privado es libertad para cambiar después.
:::

:::checkpoint
Eliges la visibilidad con argumentos, escribes una clase cuyo estado
inválido no tiene camino, usas `readonly` en lo que no cambia, expones los
cambios con métodos con nombre de acontecimiento y reconoces un `static`
que está guardando estado de la petición.
:::

:::exercise level=1
La clase `Lector` tiene `nombre`, `documento` y `registradoEn`. Decide la
visibilidad de cada uno y justifícala en una frase.

Después responde: ¿cuál de los tres harías modificable, y con qué método?

:::answer
```php title="src/Lectores/Lector.php" numbered
<?php

namespace CasaAmarela\Lectores;

class Lector
{
    public function __construct(
        private string $nombre,
        public readonly string $documento,
        public readonly string $registradoEn,
    ) {}
}
```

`documento` es `readonly`: el CPF de una persona no cambia, y si se
escribió mal el caso es de corrección del registro, no de modificación de
un dato.

`registradoEn` es `readonly` por el mismo motivo, más fuerte: es un hecho
histórico. La fecha de algo que ya ocurrió no cambia.

`nombre` es el único que cambia de verdad: matrimonio, corrección de
ortografía, nombre social. Por eso queda privado y recibe una puerta con
nombre de acontecimiento, `corregirNombre()` o `renombrar()`, no
`setNombre()`. La puerta es el lugar para rechazar un nombre vacío.
:::

:::exercise level=2
Escribe la clase `Multa` con `centavos` y `diasDeAtraso`, que:

1. se niega a nacer con días negativos;
2. se niega a nacer con centavos negativos;
3. expone `valorFormateado()` devolviendo algo como `R$ 7,20`;
4. expone `perdonar()`, que deja el valor en cero y no se puede deshacer.

Después di qué invariante tiene que respetar `perdonar()`.

:::answer
```php title="src/Prestamos/Multa.php" numbered
<?php

namespace CasaAmarela\Prestamos;

class Multa
{
    public function __construct(
        private int $centavos,
        public readonly int $diasDeAtraso,
    ) {
        if ($diasDeAtraso < 0) {
            throw new \InvalidArgumentException(
                "Días de atraso negativos: {$diasDeAtraso}"
            );
        }

        if ($centavos < 0) {
            throw new \InvalidArgumentException(
                "Multa negativa: {$centavos}"
            );
        }
    }

    public function centavos(): int
    {
        return $this->centavos;
    }

    public function valorFormateado(): string
    {
        $reales = $this->centavos / 100;

        return 'R$ ' . number_format($reales, 2, ',', '.');
    }

    public function perdonar(): void
    {
        $this->centavos = 0;
    }
}
```

La invariante que tiene que respetar `perdonar()` es la misma del
constructor: **centavos nunca es negativo**. Dejarlo en cero la respeta.

Aquí vive el error más común de quien empieza a validar: escribir las
revisiones en el constructor y olvidar que todo método que cambia el estado
tiene que dejar el objeto tan válido como lo encontró. Un
`descontar(int $centavos)` escrito sin cuidado lleva la multa a menos
veinte, y el constructor no tiene cómo impedirlo: ya corrió.

`diasDeAtraso` es `readonly` porque es un hecho del préstamo, y perdonar la
multa no hace que el atraso deje de haber existido. Esa distinción aparece
en el informe de la Casa Amarela: Vera necesita saber cuántos atrasos hubo,
incluso los perdonados.
:::

:::exercise level=3
Este código corre e imprime un número equivocado. Di cuál, por qué, y
arréglalo sin quitar el contador.

```php title="contador.php" numbered
<?php

class Ejemplar
{
    public static int $prestados = 0;

    public function __construct(
        public readonly int $registro,
        private string $condicion = 'bueno',
    ) {}

    public function prestar(): void
    {
        $this->condicion = 'prestado';
        self::$prestados++;
    }
}

$a = new Ejemplar(2117);
$b = new Ejemplar(843);

$a->prestar();
$a->prestar();
$b->prestar();

echo Ejemplar::$prestados, "\n";
```

:::answer
Imprime `3`. El acervo prestó dos ejemplares.

Son dos defectos, y se esconden uno detrás del otro.

El primero es la falta de la puerta: `prestar()` no revisa la condición,
así que llamarlo dos veces en el mismo ejemplar pasa. Con la revisión del
capítulo, la segunda llamada se rechazaría y el contador se quedaría en 2,
por accidente.

El segundo es el contador en sí. `public static` significa que cualquier
línea de cualquier archivo puede sumar, restar o ponerlo en cero, y nada
obliga a ese número a tener relación con la realidad. Es un total paralelo,
que empieza correcto y diverge en el primer camino que alguien olvide
contar: exactamente la columna `cantidad` del capítulo
@cap:o-que-vamos-construir, ahora en memoria.

La corrección que mantiene el contador:

```php
    public function prestar(): void
    {
        if ($this->condicion !== 'bueno') {
            throw new \RuntimeException('Ejemplar no disponible');
        }

        $this->condicion = 'prestado';
        self::$prestados++;
    }
```

Y la corrección que resuelve de verdad es no guardar el total: contar las
filas de `prestamos` abiertas cuando alguien pregunte. Un número contado no
diverge de la realidad, y un `static` que desaparece con cada petición
nueva ni siquiera sirve de total, porque se pone en cero junto con el
proceso.
:::
