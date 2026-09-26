---
source_hash: 5ae48da56ae3
title: "Arrays y colecciones"
number: 8
part: p2
kicker: "El array tiene tamaño. La lista tiene vida. El mapa tiene clave. Elegir mal sale caro."
goal: >-
  Elegir entre `List`, `Set` y `Map` según el problema, recorrer cada uno y
  explicar por qué se declara la interfaz y no la implementación.
---

El array resuelve el caso en que conoces el tamaño. Una API no lo conoce:
el cliente puede registrar tres productos hoy y trescientos mañana. Para eso
existe el *framework* de colecciones, la parte de la biblioteca estándar que
más vas a usar el resto de tu vida.

## Las tres preguntas

| Pregunta | Estructura | Característica |
|---|---|---|
| ¿En qué orden? | `List` | acepta repetidos, tiene índice |
| ¿Está aquí? | `Set` | no acepta repetidos, sin orden garantizado |
| ¿Cuál es el valor de? | `Map` | pares clave → valor |

Tabla: Elegir la colección es elegir la pregunta que vas a hacer mil veces
por segundo.

## `List`: orden y repetición

```java title="Una lista que crece" numbered
List<String> productos = new ArrayList<>();
productos.add("Teclado");
productos.add("Mouse");
productos.add("Teclado");       // repetido, y está todo bien

System.out.println(productos.size());     // 3
System.out.println(productos.get(0));     // Teclado
System.out.println(productos.contains("Mouse"));  // true

for (String p : productos) {
    System.out.println(p);
}
```

:::anatomy title="La línea más importante del capítulo"
lang: java
code: |
  List<String> productos = new ArrayList<>();
notes:
  - { line: 1, text: "`List` es la **interfaz**: el contrato, lo que se puede hacer." }
  - { line: 1, text: "`<String>` es el tipo genérico: el compilador pasa a rechazar cualquier cosa que no sea texto." }
  - { line: 1, text: "`ArrayList` es la **implementación**: cómo se hace en memoria." }
  - { line: 1, text: "El `<>` vacío (*diamond*) deduce el tipo del lado izquierdo, desde Java 7." }
:::

Declarar `List` a la izquierda y `ArrayList` a la derecha es una convención
con consecuencia práctica: si mañana necesitas cambiarla por `LinkedList`,
cambias una palabra y nada más se rompe. Es el primer encuentro con una idea
que Spring lleva al extremo en la Parte 3: **depende de la interfaz, no de
la implementación.**

:::trivia
Antes de Java 5 no había genéricos: una `List` guardaba `Object`, y tenías
que escribir `(String) lista.get(0)` para recuperar el texto. Un error de
tipo solo aparecía en producción, como un `ClassCastException`. Los
genéricos existen para convertir ese defecto de ejecución en error de
compilación: el mismo intercambio que este libro elogia desde el capítulo
3.
:::

## `Set`: pertenece o no

```java title="Sin repetición" numbered
Set<String> categorias = new HashSet<>();
categorias.add("periférico");
categorias.add("periférico");    // ignorado
System.out.println(categorias.size());   // 1
```

`Set` es la estructura correcta para "¿ya vi este?", "¿cuáles son los
distintos?", "¿el usuario tiene este permiso?", y es exactamente esa última
pregunta la que va a hacer el capítulo 33.

:::pitfall
`HashSet` no garantiza ningún orden, ni siquiera el de inserción. Si
imprimes un `HashSet` esperando el orden en que insertaste, te vas a llevar
un susto. Cuando el orden importa, usa `LinkedHashSet` (orden de inserción)
o `TreeSet` (orden natural).
:::

:::story El informe con orden propio
—El informe está saliendo en orden aleatorio —dijo Cláudia.

—No existe el orden aleatorio —respondió Carlos—. Debe ser el orden de
registro.

No lo era. Era un `HashSet`.

Lo corrieron de nuevo: otro orden. Lo corrieron una tercera vez: el mismo
orden de la primera, lo que confundió a todos durante veinte minutos más.

Roberto, que pasaba por ahí, oyó "orden impredecible" y tuvo una idea:

—¿No es buena señal? O sea, el sistema está eligiendo solo. Parece
inteligencia artificial.

Marina levantó la cabeza despacio y dijo, sin alterar la voz:

—Roberto, es una tabla de dispersión. No elige. No tiene opinión. Tiene el
resto de una división.
:::

## `Map`: clave y valor

```java title="Stock por producto" numbered
Map<String, Integer> stock = new HashMap<>();
stock.put("Teclado", 12);
stock.put("Mouse", 3);

System.out.println(stock.get("Teclado"));            // 12
System.out.println(stock.get("Monitor"));            // null
System.out.println(stock.getOrDefault("Monitor", 0));  // 0

for (Map.Entry<String, Integer> item : stock.entrySet()) {
    System.out.println(item.getKey() + ": " + item.getValue());
}
```

`get` de una clave inexistente devuelve `null`, y `null` es el origen del
error más famoso de la plataforma. `getOrDefault` existe precisamente para
que no tengas que pensar en eso.

:::diagram type="cells" caption="Un mapa es una tabla de dos columnas con búsqueda instantánea por la primera."
items: ["Teclado → 12", "Mouse → 3", "Cable → 41"]
orientation: vertical
notes:
  - { at: 0, text: "clave única" }
:::

## Listas inmutables: el atajo moderno

```java
List<String> fijos = List.of("PIX", "TARJETA", "BOLETO");
Map<String, Integer> plazos = Map.of("PIX", 0, "BOLETO", 3);
```

`List.of` y `Map.of` crean colecciones **inmutables**: `add` en ellas lanza
`UnsupportedOperationException`. Eso parece una limitación y es una
protección: una constante que nadie puede cambiar por accidente. Úsalas
para los valores fijos del sistema.

:::pitfall
`List.of("a", "b")` no es un `ArrayList`. Si recibes una lista de afuera y
necesitas cambiarla, cópiala: `new ArrayList<>(recibida)`. Modificar una
lista que vino de otro lugar es, además de un error en potencia, una falta
de modales de diseño.
:::

## Ordenar

```java title="Dos órdenes, una línea cada uno" numbered
List<String> nombres = new ArrayList<>(
        List.of("Mouse", "Cable", "Teclado"));

Collections.sort(nombres);                  // orden alfabético
nombres.sort(Comparator.reverseOrder());    // inverso
nombres.sort(Comparator.comparing(String::length));  // por tamaño
```

La última línea usa dos cosas del capítulo 14 (referencia a método y
comparador funcional). Guárdala: cuando llegues ahí, ya la habrás visto
funcionar.

## Recorrer: las tres formas y cuándo usar cada una

```java title="El mismo bucle, tres dialectos" numbered
for (String p : productos) { }          // estándar, casi siempre

for (int i = 0; i < productos.size(); i++) { }  // el índice importa

productos.forEach(System.out::println); // funcional (cap. 14)
```

:::pitfall
Quitar ítems durante un `for-each` lanza `ConcurrentModificationException`.
La colección detecta que cambió por debajo del bucle y se niega a seguir.
Para quitar, usa `productos.removeIf(p -> p.isBlank())`: una línea, sin
bucle, sin excepción.
:::

## Lo que va a usar el proyecto

Guarda este fragmento: es la versión en memoria de lo que el capítulo 21 va
a hacer con una base de datos de verdad.

```java title="Repositorio de juguete" numbered
Map<Long, String> productos = new HashMap<>();
long proximoId = 1;

productos.put(proximoId++, "Teclado");       // create
String nombre = productos.get(1L);           // read
productos.put(1L, "Teclado mecánico");       // update
productos.remove(1L);                        // delete
```

Cuatro operaciones, un mapa. Cuando Spring Data JPA entre en escena, va a
ofrecer exactamente estos cuatro métodos —`save`, `findById`, `save`,
`deleteById`— y la diferencia es que los datos sobreviven al apagado de la
máquina.

:::summary
- `List` para el orden, `Set` para la unicidad, `Map` para la asociación.
- Declara la interfaz (`List`), instancia la implementación (`ArrayList`).
- Los genéricos (`<String>`) convierten errores de ejecución en errores de
  compilación.
- `getOrDefault` evita el `null`; `List.of` crea una colección inmutable.
- No quites dentro de un `for-each`: usa `removeIf`.
:::

:::checkpoint
Eliges la colección correcta para el problema, recorres las tres, evitas el
`null` con `getOrDefault` y sabes por qué se declara la interfaz.
:::

:::milestone
El proyecto tiene una "base de datos" de mentira: un `Map` en memoria con
las cuatro operaciones del CRUD. Es el mismo diseño que va a sobrevivir al
cambio a PostgreSQL en el capítulo 19.
:::

:::exercise level=1
Crea una `List<String>` con cinco nombres de producto, ordénala
alfabéticamente e imprime cada uno en una línea.

:::answer
```java
List<String> nombres = new ArrayList<>(
        List.of("Mouse", "Cable", "Teclado", "Monitor", "Webcam"));
Collections.sort(nombres);
nombres.forEach(System.out::println);
```
:::

:::exercise level=2
Usa un `Map<String, Integer>` para contar cuántas veces aparece cada
palabra en un array de textos. Pista: `getOrDefault`.

:::answer
```java
Map<String, Integer> conteo = new HashMap<>();
for (String palabra : palabras) {
    conteo.put(palabra, conteo.getOrDefault(palabra, 0) + 1);
}
```
Este es probablemente el fragmento de código más reescrito de la historia de
Java. En el capítulo 14 se vuelve una línea con `Collectors.groupingBy`, y
te va a parecer bonito justamente porque escribiste primero la versión
larga.
:::

:::exercise level=3
Dado un `Map<String, Integer>` de stock, imprime solo los productos con
menos de cinco unidades, en orden alfabético de nombre.

:::answer
```java
new TreeMap<>(stock).forEach((nombre, cant) -> {
    if (cant < 5) {
        System.out.println(nombre + ": " + cant);
    }
});
```
`TreeMap` mantiene las claves ordenadas: pasar el mapa al constructor ya lo
ordena. Reconocer que la estructura de datos puede resolver el problema en
lugar del algoritmo es una de las marcas de quien programa desde hace un
tiempo.
:::
