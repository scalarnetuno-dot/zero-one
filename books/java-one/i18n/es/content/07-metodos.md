---
source_hash: a3a5ad5e76a8
title: "Métodos"
number: 7
part: p2
kicker: "Ponerle nombre a un fragmento de código es la forma de documentación más barata que existe."
goal: >-
  Extraer un método con parámetros y retorno, entender qué es el alcance y
  reconocer cuándo una sobrecarga ayuda y cuándo confunde.
---

Hasta aquí todo el código vivió dentro del `main`. Funciona para veinte
líneas y se vuelve una pesadilla en doscientas. Un método es un fragmento de
código con nombre, entrada y salida, y el nombre es la parte más
importante.

## De la repetición al método

:::compare left="Antes: la cuenta desparramada" right="Después: la cuenta con nombre"
double t1 = p1 * 1.08;
double t2 = p2 * 1.08;
double t3 = p3 * 1.08;
---
double t1 = conImpuesto(p1);
double t2 = conImpuesto(p2);
double t3 = conImpuesto(p3);
:::

La versión de la derecha tiene dos ventajas que no son estéticas. Si la
alícuota cambia, modificas un solo lugar. Y quien lee `conImpuesto(p1)`
entiende la intención sin reconstruir la multiplicación.

```java title="El método" numbered
static double conImpuesto(double valor) {
    return valor * 1.08;
}
```

:::anatomy title="Cada parte de la declaración de un método"
lang: java
code: |
  static double conImpuesto(double valor) {
      return valor * 1.08;
  }
notes:
  - { line: 1, text: "`static` porque todavía lo llamamos desde el `main`, sin objeto. En el capítulo 9 esto cambia." }
  - { line: 1, text: "`double` es el **tipo de retorno**: la especie del valor que sale." }
  - { line: 1, text: "`conImpuesto` es el nombre. Verbo o sustantivo, siempre en camelCase." }
  - { line: 1, text: "`double valor` es el **parámetro**: el nombre que recibe el valor aquí dentro." }
  - { line: 2, text: "`return` devuelve y termina el método en la misma instrucción." }
:::

## `void` y `return`

Un método que no devuelve nada declara `void`. En él, `return` sin valor
sirve para salir antes:

```java title="Salir antes también vale para un método" numbered
static void imprimirEtiqueta(String nombre, double precio) {
    if (nombre == null || nombre.isBlank()) {
        return;                     // nada que imprimir
    }
    System.out.println(nombre + " — R$ " + precio);
}
```

:::key
Un método con más de un `return` no es un problema; un método con más de un
*motivo para existir* sí lo es. Si necesitas una "y" para explicar lo que
hace ("valida **y** guarda **y** notifica"), son tres métodos.
:::

:::story La alícuota que vivía en nueve lugares
El impuesto pasó del 8% al 8,5%. Una línea, dijo Roberto. Cinco minutos.

Carlos abrió el proyecto y usó la búsqueda: `1.08`. Nueve resultados.

Cambió los nueve. Lo corrió. Funcionó.

El miércoles, Cláudia avisó que el informe de cierre seguía con el valor
viejo. Carlos buscó de nuevo, ahora por `* 1.0`: apareció un décimo lugar,
escrito como `0.08 + 1`, que la búsqueda anterior no atrapaba.

Marina apareció con su taza e hizo la pregunta que no era sobre impuestos:

—¿Cuántas veces necesita existir esta cuenta?

—Una.

—¿Y cuántas veces existe?

—Diez. —Carlos lo pensó un poco—. Diez que yo encontré.
:::

## Alcance: dónde existe un nombre

```java title="Cada llave abre un mundo" numbered
static void ejemplo() {
    int a = 1;
    if (a == 1) {
        int b = 2;
        System.out.println(a + b);   // ok: a y b existen
    }
    // System.out.println(b);        // error: b murió en la llave
}
```

La regla es simple: un nombre existe desde la declaración hasta la llave
que la cierra. El compilador no te deja usar lo que ya no existe, y tampoco
te deja declarar dos variables con el mismo nombre en el mismo alcance.

:::pitfall
Un parámetro es una **copia**. Cambiar `valor` dentro del método no cambia
la variable de quien llamó. Para los primitivos esto es siempre verdad; para
los objetos, la copia es de la *referencia*: no puedes cambiar el objeto de
quien llamó, pero sí su contenido. Esa distinción vuelve en el capítulo 9 y
explica muchos bugs de listas compartidas.
:::

## Sobrecarga: mismo nombre, firmas distintas

```java title="Tres formas de llamar a la misma idea" numbered
static double total(double precio) {
    return total(precio, 1);
}

static double total(double precio, int cantidad) {
    return total(precio, cantidad, 0.08);
}

static double total(double precio, int cantidad, double tasa) {
    return precio * cantidad * (1 + tasa);
}
```

Java elige cuál llamar por el número y el tipo de los argumentos: la
**firma**. Fíjate en el encadenamiento: las dos primeras versiones solo
completan valores por defecto y delegan. Es un patrón común y saludable,
porque la regla vive en un solo lugar.

:::pitfall
Una sobrecarga que cambia el *significado* confunde. `guardar(String)`
escribiendo en un archivo y `guardar(int)` escribiendo en la base de datos
es una trampa para quien lee. Los nombres distintos cuestan tres teclas y
ahorran una hora.
:::

:::trivia
Java no tiene parámetros con valor por defecto, como Python o Kotlin. La
sobrecarga encadenada de arriba es el sustituto idiomático, y el motivo por
el que las bibliotecas Java antiguas tienen métodos con siete versiones. A
partir de la Parte 3 vas a ver a Spring resolverlo de otra forma: con
objetos de configuración.
:::

## Métodos que documentan reglas

Este es el ejercicio de traducción que sostiene el resto del libro: **toda
regla de negocio cabe en un método con nombre de regla**.

```java title="La regla tiene nombre" numbered
static boolean puedeVender(int stock, boolean activo) {
    return activo && stock > 0;
}
```

En el capítulo 22 esta misma función se vuelve un método de una clase
`ProductService` y pasa a ser llamada por un controlador HTTP. La forma
cambia; la idea es la misma: la regla vive en un lugar, tiene nombre y
puede probarse sola, que es exactamente lo que va a hacer con ella el
capítulo 34.

:::example Un programa entero, ahora organizado
```java
public class Tienda {
    public static void main(String[] args) {
        double[] precios = { 19.90, 4.50, 32.00 };
        System.out.println("Total: R$ " + sumar(precios));
        System.out.println("Promedio: R$ " + promedio(precios));
    }

    static double sumar(double[] valores) {
        double total = 0;
        for (double v : valores) {
            total += v;
        }
        return total;
    }

    static double promedio(double[] valores) {
        if (valores.length == 0) return 0;
        return sumar(valores) / valores.length;
    }
}
```
`promedio` usa `sumar` y trata el caso del array vacío. Sin ese `return 0`,
la división por cero devolvería `NaN`, y un `NaN` en un informe es peor que
un error, porque no llama la atención.
:::

:::summary
- Un método es código con nombre, parámetros y tipo de retorno.
- `void` no devuelve nada; un `return` solo sirve para salir antes.
- Un nombre existe hasta la llave que cierra su bloque.
- La sobrecarga es el mismo nombre con firmas distintas: úsala para valores
  por defecto, no para cambiar de significado.
- Una regla de negocio con nombre es una regla que se puede probar.
:::

:::checkpoint
Extraes un método a partir de código repetido, eliges entre `void` y
retorno, sabes dónde existe cada variable y usas la sobrecarga sin
confundir a quien lee.
:::

:::milestone
Las reglas del proyecto empiezan a tener nombre: `puedeVender`,
`conImpuesto`. Todavía son métodos estáticos en una clase suelta; en el
capítulo 9 ganan un dueño.
:::

:::exercise level=1
Extrae un método `mayorPrecio(double[] precios)` del ejercicio del capítulo
6 y llámalo desde el `main`.

:::answer
```java
static double mayorPrecio(double[] precios) {
    double mayor = precios[0];
    for (double p : precios) {
        if (p > mayor) {
            mayor = p;
        }
    }
    return mayor;
}
```
:::

:::exercise level=2
Escribe `aplicarDescuento(double precio, double porcentaje)` que rechace
porcentajes fuera de 0 a 100 devolviendo el precio original. Después
escribe la sobrecarga `aplicarDescuento(double precio)` con 10% de
descuento.

:::answer
```java
static double aplicarDescuento(double precio) {
    return aplicarDescuento(precio, 10);
}

static double aplicarDescuento(double precio, double porcentaje) {
    if (porcentaje < 0 || porcentaje > 100) {
        return precio;
    }
    return precio * (1 - porcentaje / 100);
}
```
Devolver el precio original en el caso inválido es una decisión discutible:
esconde el error. En el capítulo 13 vas a aprender la alternativa honesta:
lanzar una excepción.
:::

:::exercise level=3
Escribe `static String etiqueta(String nombre, double precio, int cantidad)`
que devuelva `"Teclado · R$ 349,90 · 12 un"`. Usa `String.format` y descubre
por tu cuenta cómo obtener la coma decimal en lugar del punto.

:::answer
```java
static String etiqueta(String nombre, double precio, int cantidad) {
    return String.format("%s · R$ %.2f · %d un",
            nombre, precio, cantidad);
}
```
La coma depende del *locale* de la máquina: `String.format` usa el del
sistema, así que en un sistema configurado en español o en portugués ya
sale `349,90`, y en uno en inglés, `349.90`. Para garantizarlo,
`String.format(Locale.of("es", "ES"), ...)`. El formato que depende del
entorno es una de las fuentes más irritantes de "funciona en mi máquina".
:::
