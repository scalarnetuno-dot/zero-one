---
source_hash: 7a1c5b285f5f
title: "Probando Java"
number: 34
part: p8
kicker: "Probar no se trata de demostrar que funciona. Se trata de poder tocar el código sin miedo el viernes."
goal: >-
  Escribir pruebas con JUnit 5 y AssertJ, nombrar una prueba de forma que
  documente la regla, y saber qué no vale la pena probar.
---

La API está lista y nadie la probó nunca de verdad. Toda validación hasta
aquí fue un `curl` tecleado a mano, mirando la respuesta y decidiendo, a
ojo, si estaba bien.

Eso funciona una vez. El problema es la segunda.

## Lo que compra una prueba

:::key
Una prueba no demuestra que el código esté bien: demuestra que sigue
haciendo lo que hacía cuando escribiste la prueba. El valor no está en
encontrar el bug de hoy: está en **avisarte mañana** que alguien rompió la
regla de anteayer.
:::

## La primera prueba

```java title="src/test/java/.../ProductTest.java" numbered
package com.tienda.catalog.product;

import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.*;

class ProductTest {

    @Test
    void noDebeAceptarPrecioNegativo() {
        assertThatThrownBy(() ->
                new Product("Teclado",
                        new BigDecimal("-10"), 5))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("precio");
    }

    @Test
    void debeDescontarStockYMarcarAgotado() {
        Product p = new Product("Teclado",
                new BigDecimal("349.90"), 3);

        p.descontarStock(3);

        assertThat(p.getQuantity()).isZero();
        assertThat(p.getStatus()).isEqualTo(Status.AGOTADO);
    }
}
```

```bash
./mvnw test
```

```text title="Salida"
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

:::anatomy title="La anatomía de una prueba, en tres actos"
lang: java
code: |
  @Test
  void debeDescontarStockYMarcarAgotado() {
      Product p = new Product("Teclado",
              new BigDecimal("349.90"), 3);

      p.descontarStock(3);

      assertThat(p.getStatus())
              .isEqualTo(Status.AGOTADO);
  }
notes:
  - { line: 1, text: "`@Test` marca el método. No necesita ser público desde JUnit 5." }
  - { line: 2, text: "El **nombre** es la documentación: describe la regla, no el método probado." }
  - { line: 3, text: "**Arrange**: arma el escenario. Solo lo que la prueba necesita, nada más." }
  - { line: 6, text: "**Act**: una línea. Si son tres, la prueba está verificando tres cosas." }
  - { line: 8, text: "**Assert**: lo que debería haber pasado, escrito como afirmación." }
:::

## AssertJ: la afirmación que se lee

```java title="La misma verificación, dos bibliotecas" numbered
// JUnit puro
assertEquals(Status.AGOTADO, p.getStatus());

// AssertJ
assertThat(p.getStatus()).isEqualTo(Status.AGOTADO);
```

La segunda forma tiene dos ventajas prácticas: se lee en el orden natural
("afirmo que el estado es igual a agotado") y el autocompletado del IDE
muestra todas las verificaciones posibles para ese tipo después del punto.
`spring-boot-starter-test` ya trae AssertJ: no hay nada que instalar.

```java title="Las afirmaciones que vas a usar" numbered
assertThat(valor).isEqualTo(esperado);
assertThat(lista).hasSize(3).contains(item);
assertThat(lista).isEmpty();
assertThat(texto).startsWith("Tec").containsIgnoringCase("MECÁNICO");
assertThat(numero).isPositive().isLessThan(100);
assertThat(optional).isPresent().get()
        .extracting(Product::getName).isEqualTo("Teclado");
assertThatThrownBy(() -> metodo())
        .isInstanceOf(IllegalStateException.class);
```

## El nombre de la prueba es la especificación

:::compare left="Un nombre que no ayuda" right="Un nombre que documenta"
@Test
void testDescontarStock() {
  ...
}

@Test
void test2() {
  ...
}
---
@Test
void debeRechazarDescuento
MayorQueElStock() {
  ...
}
:::

Cuando una prueba se rompe un viernes, lo único que aparece en la terminal
es su nombre. `test2 failed` te obliga a abrir el archivo;
`debeRechazarDescuentoMayorQueElStock failed` ya te contó lo que se perdió.

:::tip
Un patrón de nombres que envejece bien: **debe** + el comportamiento
esperado + **cuando** + la condición.
`debeMarcarAgotadoCuandoElStockLlegaACero`. Queda largo y no pasa nada: el
nombre de una prueba no se teclea dos veces.
:::

## Organizando: `@Nested` y `@DisplayName`

```java title="Pruebas agrupadas por comportamiento" numbered
@DisplayName("Producto")
class ProductTest {

    @Nested
    @DisplayName("al descontar stock")
    class DescontarStock {

        @Test
        @DisplayName("lo marca como agotado al llegar a cero")
        void agotado() { ... }

        @Test
        @DisplayName("rechaza una cantidad mayor que la disponible")
        void rechazaExceso() { ... }
    }
}
```

El informe pasa a leerse como una especificación:

```text
Producto
  al descontar stock
    ✔ lo marca como agotado al llegar a cero
    ✔ rechaza una cantidad mayor que la disponible
```

## Casos repetidos: `@ParameterizedTest`

```java title="Una prueba, cinco escenarios" numbered
@ParameterizedTest
@ValueSource(strings = {"", " ", "   "})
void noDebeAceptarNombreEnBlanco(String nombre) {
    assertThatThrownBy(() ->
            new Product(nombre, BigDecimal.TEN, 1))
            .isInstanceOf(IllegalArgumentException.class);
}

@ParameterizedTest
@CsvSource({
    "10, 3, 7",
    "3,  3, 0",
    "1,  1, 0"
})
void debeRestarDelStock(int inicial, int descuento, int esperado) {
    Product p = new Product("X", BigDecimal.TEN, inicial);
    p.descontarStock(descuento);
    assertThat(p.getQuantity()).isEqualTo(esperado);
}
```

## Lo que no hay que probar

:::pitfall
No pruebes getters, setters, constructores triviales ni el framework. Una
prueba que verifica si `getName()` devuelve el nombre no protege contra nada
y hay que mantenerla para siempre. Prueba **decisiones**: `if`, cálculo,
validación, transformación. Donde no hay decisión, no hay nada que romper.
:::

| Vale la pena probar | No vale la pena |
|---|---|
| reglas de negocio | getters y setters |
| cálculo y redondeo | mapeo trivial de DTO |
| validación y excepciones | configuración del framework |
| casos límite (cero, vacío, nulo) | bibliotecas de terceros |

Tabla: La pregunta es siempre la misma: *si esto se rompe, ¿alguien se da
cuenta?*

## Cobertura: un número que engaña

```bash
./mvnw verify   # con el plugin JaCoCo configurado
```

La cobertura mide las **líneas ejecutadas** por las pruebas, no las reglas
verificadas. Una prueba que llama al método y no afirma nada da 100% de
cobertura y cero garantía.

:::trivia
La meta del "80% de cobertura" es probablemente la métrica más distorsionada
de la ingeniería de software. Nació como observación empírica y se volvió
meta, y toda métrica que se vuelve meta deja de ser métrica. El síntoma
clásico: pruebas escritas para cubrir líneas, con `assertTrue(true)` al
final, aprobadas porque el número subió.
:::

:::story ¿Probar no atrasa?
—¿Cuánto tiempo lleva escribir estas pruebas? —preguntó Roberto.

—Un treinta por ciento más al principio.

Roberto lo anotó. Treinta por ciento más es, en su planilla, treinta por
ciento más.

Marina esperó un poco y le devolvió la pregunta en la moneda que él
entendía:

—¿Cuántas horas gastamos el mes pasado arreglando cosas que ya habían
funcionado antes?

Roberto no lo sabía. Fue a mirar. Volvió al día siguiente con un número que
él mismo había sumado a partir de los tickets: el sesenta y dos por ciento
del tiempo del equipo.

No se volvió regla de inmediato. Se volvió regla después del incidente del
capítulo 33, cuando una prueba de cuatro líneas habría impedido que treinta
y una personas pudieran borrar el catálogo.
:::

:::summary
- Una prueba protege el futuro, no el presente: te avisa cuando alguien
  rompe la regla.
- Arrange, act, assert, y el nombre del método es la documentación.
- AssertJ se lee en el orden natural y se descubre con el autocompletado.
- `@ParameterizedTest` cambia cinco pruebas iguales por una con cinco
  entradas.
- Prueba decisiones; no pruebes getters ni el framework. Una cobertura alta
  no es garantía.
:::

:::checkpoint
Escribes pruebas unitarias con JUnit y AssertJ, las nombras de forma que el
informe documente la regla, usas pruebas parametrizadas y sabes qué dejar
afuera.
:::

:::milestone
Las reglas de `Product` están cubiertas por pruebas que corren en
milisegundos, sin base de datos y sin Spring. El próximo capítulo prueba el
servicio, que tiene dependencias.
:::

:::exercise level=1
Escribe tres pruebas para `descontarStock`: éxito, cantidad cero y una
cantidad mayor que el stock.

:::answer
La tercera es la más valiosa: verifica que se lance la excepción correcta.
Probar el camino feliz demuestra que el código funciona; probar el camino
rechazado demuestra que **protege**.
:::

:::exercise level=2
Convierte las tres pruebas de arriba en un `@ParameterizedTest` con
`@CsvSource`. Después decide si quedó mejor o peor y justifícalo.

:::answer
Mejor para los casos de cálculo, que solo varían en los números. Peor para
los casos de excepción, que verifican tipos distintos: forzarlos en la misma
tabla exige una columna con el nombre de la excepción, y la prueba termina
con un `if`. Una prueba con un `if` adentro es una prueba que necesita una
prueba.
:::

:::exercise level=3
Escribe una prueba que falle a propósito y lee con atención la salida de
AssertJ. Después haz lo mismo con el `assertEquals` de JUnit y compara los
mensajes.

:::answer
AssertJ muestra lo esperado y lo obtenido en bloques separados, destacando
la diferencia; en las colecciones, señala los elementos que faltan y los que
sobran. La calidad del mensaje de falla es la razón práctica para
preferirlo, porque el mensaje se lee con prisa, casi siempre con el build en
rojo.
:::
