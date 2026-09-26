---
source_hash: 4293094912bb
title: "Lambdas y streams"
number: 14
part: p2
kicker: "El bucle dice cómo recorrer. El stream dice lo que quieres. La segunda frase es más corta."
goal: >-
  Escribir una lambda, encadenar `filter`, `map`, `sorted` y `collect`, y
  reconocer cuándo un stream ayuda y cuándo estorba.
---

En 2014, Java 8 agregó funciones como valor. No fue maquillaje: cambió el
estilo del código Java y es la base de la mitad de las API modernas,
incluidas algunas que Spring te va a pedir en la Parte 4.

## Lambda: una función sin nombre

```java title="La misma idea, dos escrituras" numbered
// antes de Java 8: clase anónima
Comparator<String> porLargo = new Comparator<String>() {
    @Override
    public int compare(String a, String b) {
        return a.length() - b.length();
    }
};

// Java 8: lambda
Comparator<String> porLargo2 =
        (a, b) -> a.length() - b.length();
```

Ocho líneas se volvieron dos. La lambda es lo mismo: la implementación de
una interfaz que tiene **un único método abstracto**. Java lo llama
*interfaz funcional*, y por eso la lambda sabe qué método está
implementando.

:::anatomy title="La sintaxis de la lambda, en tres formas"
lang: java
code: |
  p -> p.getPrecio() > 100
  (a, b) -> a.length() - b.length()
  p -> {
      log(p);
      return p.getNombre();
  }
notes:
  - { line: 1, text: "Un parámetro, sin paréntesis; cuerpo de una expresión, sin `return`." }
  - { line: 2, text: "Dos parámetros exigen paréntesis. El tipo se infiere del contexto." }
  - { line: 3, text: "Un cuerpo con llaves necesita un `return` explícito." }
:::

## Referencia a método: la lambda que ya existe

```java title="Cuatro formas de la misma idea" numbered
productos.forEach(p -> System.out.println(p));  // lambda
productos.forEach(System.out::println);         // referencia

nombres.sort((a, b) -> a.compareTo(b));         // lambda
nombres.sort(String::compareTo);                // referencia
```

Cuando la lambda solo llama a un método existente, `::` lo dice más corto.
Vas a ver `Product::getNombre` en casi todo el código Java moderno.

## Stream: la secuencia de operaciones

```java title="El bucle del capítulo 6, reescrito" numbered
List<Product> caros = productos.stream()
        .filter(p -> p.getPrecio() > 100)
        .toList();
```

:::compare left="Bucle imperativo" right="Stream declarativo"
List<Product> caros =
    new ArrayList<>();
for (Product p : productos) {
  if (p.getPrecio() > 100) {
    caros.add(p);
  }
}
---
var caros = productos
    .stream()
    .filter(p ->
        p.getPrecio() > 100)
    .toList();
:::

La diferencia no es el tamaño, es lo que lees. A la izquierda reconstruyes
la intención a partir del mecanismo; a la derecha la intención está
escrita: *filtra los caros*.

## Las cinco operaciones que resuelven casi todo

```java title="Un pipeline completo" numbered
List<String> nombres = productos.stream()
        .filter(p -> p.getStock() > 0)            // selecciona
        .sorted(Comparator.comparing(Product::getPrecio))
        .map(Product::getNombre)                  // transforma
        .limit(10)                                // corta
        .toList();                                // materializa
```

| Operación | Qué hace | Devuelve |
|---|---|---|
| `filter` | mantiene a quien pasa la prueba | stream |
| `map` | transforma cada ítem | stream |
| `sorted` | ordena | stream |
| `limit` / `skip` | corta | stream |
| `toList` / `count` / `sum` | termina | resultado |

Tabla: Las cuatro primeras son **intermedias**: devuelven un stream y no
ejecutan nada. La última es **terminal**: es la que hace correr el
pipeline.

:::key
Un stream sin operación terminal **no se ejecuta**. Si tu `filter` parece no
haber corrido, busca el `toList` que falta. Esa evaluación diferida es lo
que le permite a Java recorrer la colección una sola vez, aplicando todos
los pasos ítem por ítem.
:::

## Reducir a un número

```java title="Suma, conteo, promedio" numbered
long activos = productos.stream()
        .filter(Product::isActivo)
        .count();

double total = productos.stream()
        .mapToDouble(Product::getPrecio)
        .sum();

OptionalDouble promedio = productos.stream()
        .mapToDouble(Product::getPrecio)
        .average();
```

`mapToDouble` cambia el stream de objetos por uno de números primitivos, que
trae `sum`, `average`, `max` y `min` listos. Y fíjate en el
`OptionalDouble`: el promedio de una lista vacía no existe, y la API es
honesta al respecto: la lección del capítulo 13 apareciendo de nuevo.

## Agrupar: el `Map` del capítulo 8 en una línea

```java title="Conteo por estado" numbered
Map<Status, Long> porStatus = productos.stream()
        .collect(Collectors.groupingBy(
                Product::getStatus,
                Collectors.counting()));
```

Compáralo con las cinco líneas de `getOrDefault` del capítulo 8. La misma
salida, otra escritura, y la versión con stream sigue siendo legible cuando
el agrupamiento tiene dos niveles.

:::trivia
Los streams se diseñaron con un segundo objetivo: el paralelismo. Cambiar
`.stream()` por `.parallelStream()` distribuye el trabajo entre los núcleos.
Parece una optimización gratis y casi nunca lo es: para colecciones
pequeñas, el costo de coordinar los hilos es mayor que la ganancia. La regla
empírica del propio equipo de Java es no considerar el paralelismo por
debajo de diez mil elementos.
:::

:::story El pull request de una línea
Carlos descubrió los streams un jueves y reescribió el informe entero el
viernes.

El método tenía dieciocho líneas. Se volvió una.

Una línea de cuatrocientos doce caracteres, con cuatro `filter`, dos `map`,
un `flatMap`, un `sorted` con comparador invertido y un `collect` agrupando
por dos claves. Abrió el *pull request* con el título "simplificación".

Marina respondió con un solo comentario, en la línea 1:

> "Explica en voz alta, sin leer, qué hace esta línea. Si puedes, lo
> apruebo."

Carlos lo intentó. Llegó hasta el tercer `filter`.

La versión aprobada tenía seis líneas y tres métodos con nombre:
`activos()`, `masVendidos()` y `porCategoria()`. Cada uno con un stream
corto adentro.

—El stream no es para escribir menos —dijo Marina—. Es para escribir lo que
quieres en vez de cómo recorrer.
:::

:::art caption="Una línea de cuatrocientos caracteres no es código conciso: es código comprimido."
src="uma-linha-com-quatrocentos-caracteres-nao-e-codigo-conciso-e-codigo-comprimido.png"
Charge editorial minimalista: tela de editor de código mostrando uma única
linha absurdamente longa que atravessa o monitor e continua por uma fita de
papel que sai da tela, cai no chão e se enrola pela sala. Um desenvolvedor
jovem, orgulhoso, segura a ponta da fita. Uma desenvolvedora sênior, ao lado,
segura uma tesoura pequena com expressão paciente. Fundo branco, poucos
elementos, humor visual seco, estética de revista de tecnologia.
:::

## Cuándo el bucle sigue siendo mejor

Los streams no reemplazan todo. El bucle sigue siendo más claro cuando:

- necesitas el **índice** de cada ítem;
- necesitas **salir a la mitad** sabiendo dónde te detuviste;
- el cuerpo tiene varias líneas con efectos secundarios (log, grabación,
  envío);
- estás depurando: ir paso a paso en un stream es incómodo.

:::pitfall
Un stream con un efecto secundario dentro del `map` es una trampa:
`.map(p -> { guardar(p); return p; })`. Funciona, y engaña a quien lee:
`map` dice "transformo", no "grabo en la base". Para actuar sobre cada ítem,
usa `forEach`: el nombre avisa que algo va a pasar.
:::

## El pipeline que va a usar el proyecto

```java title="Un recorte del capítulo 28" numbered
public List<ProductResponse> buscarPorNombre(String termino) {
    return repository.findAll().stream()
            .filter(p -> p.getNombre()
                    .toLowerCase()
                    .contains(termino.toLowerCase()))
            .map(ProductResponse::of)
            .toList();
}
```

Esta versión filtra **en memoria**, y justamente por eso el capítulo 28 la
va a reemplazar por una consulta que filtra en la base de datos. Guarda la
diferencia: el stream es excelente para transformar lo que ya tienes, y
pésimo para evitar traer lo que no necesitas.

:::summary
- Una lambda es la implementación de una interfaz con un único método
  abstracto.
- `::` hace referencia a un método que ya existe.
- Una operación intermedia devuelve un stream; solo la terminal ejecuta el
  pipeline.
- `groupingBy` resuelve en una línea lo que el `Map` hacía en cinco.
- El bucle todavía gana cuando hay índice, salida a la mitad o efecto
  secundario.
:::

:::checkpoint
Escribes lambdas, encadenas `filter`, `map`, `sorted` y `collect`, reduces
un stream a un número y sabes justificar cuándo prefieres un bucle.
:::

:::milestone
Fin de la Parte 2. El proyecto tiene vocabulario (`Product`, `Status`, DTO),
reglas con nombre, errores con tipo y un estilo de transformación de datos.
Es Java suficiente para Spring, y es exactamente donde empieza la Parte 3.
:::

:::exercise level=1
Dada una `List<Product>`, escribe un stream que devuelva los nombres de los
productos con stock cero, en orden alfabético.

:::answer
```java
List<String> sinStock = productos.stream()
        .filter(p -> p.getStock() == 0)
        .map(Product::getNombre)
        .sorted()
        .toList();
```
:::

:::exercise level=2
Calcula el valor total del stock (precio × cantidad de cada producto)
usando un stream. Compáralo con la versión con bucle del capítulo 9.

:::answer
```java
double total = productos.stream()
        .mapToDouble(p -> p.getPrecio() * p.getStock())
        .sum();
```
Cuatro líneas contra seis, y una diferencia más importante: la versión con
stream no tiene ninguna variable mutable. Sin acumulador, no hay cómo
olvidarse de inicializarlo.
:::

:::exercise level=3
Agrupa los productos por rango de precio (hasta 50, de 50 a 200, por encima
de 200) y devuelve un `Map<String, List<String>>` con los nombres de cada
rango.

:::answer
```java
Map<String, List<String>> rangos = productos.stream()
        .collect(Collectors.groupingBy(
                p -> p.getPrecio() <= 50 ? "barato"
                        : p.getPrecio() <= 200 ? "medio" : "caro",
                Collectors.mapping(Product::getNombre,
                        Collectors.toList())));
```
Ese ternario encadenado es el límite del buen gusto: en la práctica, merece
volverse un método `rangoDe(Product p)`, o mejor, un `enum Rango` con el
criterio dentro, como en el capítulo 12. Si lo pensaste antes de leerlo, la
Parte 2 cumplió su objetivo.
:::
