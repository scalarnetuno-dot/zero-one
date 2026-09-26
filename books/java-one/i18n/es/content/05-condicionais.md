---
source_hash: d78f4a5a5b69
title: "Condicionales"
number: 5
part: p1
kicker: "Elegir un camino es hacerse cargo del otro, incluso cuando no está escrito."
goal: >-
  Escribir decisiones con `if`, `else if` y `switch`, elegir entre ellos con
  criterio y reconocer el camino que dejaste implícito.
---

Hasta ahora el programa hacía siempre lo mismo. A partir de aquí mira un
valor y elige. Es la unidad de inteligencia más pequeña que puede tener un
programa, y cabe en tres líneas.

## `if` exige un `boolean`

```java title="MayoriaDeEdad.java" numbered
int edad = 18;

if (edad >= 18) {
    System.out.println("Puede entrar");
} else {
    System.out.println("No puede entrar");
}
```

La condición entre paréntesis tiene que dar `true` o `false`. En lenguajes
donde `0` vale como falso, `if (edad)` compila; en Java, no. El compilador
exige que digas **qué** estás comparando.

:::diagram type="flowchart" caption="Toda decisión tiene dos caminos, incluso cuando escribes solo uno."
nodes:
  - { id: ini, type: start,    text: "Inicio" }
  - { id: d1,  type: decision, text: "¿edad >= 18?" }
  - { id: sim, type: process,  text: "Puede entrar" }
  - { id: nao, type: process,  text: "No puede entrar" }
  - { id: fim, type: start,    text: "Fin" }
edges:
  - { from: ini, to: d1 }
  - { from: d1,  to: sim, label: "sí" }
  - { from: d1,  to: nao, label: "no" }
  - { from: sim, to: fim }
  - { from: nao, to: fim }
:::

Cuando omites el `else`, el camino del "no" sigue existiendo: simplemente no
hace nada. Tener conciencia de eso es lo que separa un programa correcto de
uno que solo parece correcto, y en el capítulo 26, cuando una API tenga que
responder `404`, ese camino vacío se vuelve el defecto más visible que
existe.

:::key
Antes de escribir un `if`, responde en voz alta: *"¿y si no?"*. Si la
respuesta es "no pasa nada", escribe el comentario que lo diga. Si es "no
sé", encontraste un requisito que nadie definió.
:::

:::story Las treinta y siete combinaciones
Iba a ser una sola regla.

—Si el cliente es premium, aplica diez por ciento —dijo Roberto.

Carlos escribió el `if`. Le tomó cuatro minutos.

—¿Y si es empleado? —preguntó Cláudia, el jueves.

—También diez.

Carlos escribió el segundo `if`. Le tomó seis minutos, porque ahora había
un `else if`.

—¿Y si es premium **y** empleado?

Silencio.

—¿Se acumulan? —se arriesgó Carlos.

—No sé —dijo Roberto—. Pregúntale a finanzas.

Finanzas respondió el martes siguiente: se acumulan, pero con un tope de
quince por ciento, excepto en productos de proveedores tercerizados,
excepto si es el cumpleaños del cliente, excepto en la primera compra.

Marina fue a la pizarra y dibujó una tabla con todas las combinaciones.
Eran treinta y siete.

—El problema no es Java —dijo, tapando el marcador—. El problema es que
nadie escribió nunca esta regla entera en ningún lugar. Vamos a ser las
primeras personas en la historia de la empresa en descubrir cuál es.
:::

:::art caption="Toda escalera de `else if` empieza con una sola regla."
src="toda-escada-de-else-if-comeca-com-uma-regra-so.png"
Charge editorial minimalista: quadro branco corporativo inteiramente tomado
por uma tabela de condições "SE... E SE... MAS SE...", com dezenas de células
e setas se cruzando. Uma desenvolvedora sênior de pé ao lado do quadro,
marcador na mão, expressão resignada. Sentado, um desenvolvedor jovem abraça
o notebook contra o peito com olhar vazio. Um gerente, de costas, já saindo
pela porta com o celular no ouvido. Poucos elementos, fundo branco,
composição limpa, humor visual seco, estética de revista de tecnologia.
:::

## Llaves: el caso en que ahorrar sale caro

Java permite omitir las llaves cuando el bloque tiene una sola línea:

```java
if (edad >= 18)
    System.out.println("Puede entrar");
```

Y permitirlo ya le costó mucho dinero al mundo. El código de abajo compila y
está mal:

:::compare left="Lo que parece" right="Lo que lee el compilador"
if (ok)
    permite();
    registra();
---
if (ok) {
    permite();
}
registra();
:::

`registra()` corre siempre, porque la sangría no significa nada para el
compilador. **Usa llaves siempre**, incluso en bloques de una línea. Es la
regla de estilo más fácil de justificar en una revisión de código.

:::history
En febrero de 2014 Apple corrigió la falla apodada *goto fail*: un `if` sin
llaves, en C, con una línea duplicada por accidente. El resultado era que la
verificación del certificado TLS siempre pasaba: cualquier persona en la
misma red podía hacerse pasar por cualquier sitio. Dos llaves habrían
impedido la falla de seguridad más comentada de ese año.
:::

## La escalera de `else if`

```java title="Rango.java" numbered
double nota = 7.5;

if (nota >= 9) {
    System.out.println("Excelente");
} else if (nota >= 7) {
    System.out.println("Bueno");
} else if (nota >= 5) {
    System.out.println("Regular");
} else {
    System.out.println("Insuficiente");
}
```

El orden importa: la primera prueba verdadera gana y las demás ni siquiera
se evalúan. Por eso la escalera va del valor más alto al más bajo: en el
orden inverso, `nota >= 5` se tragaría todos los casos por encima de él.

:::pitfall
Una escalera con más de cuatro escalones es señal de que falta un concepto.
En el capítulo 12 este mismo rango de notas se vuelve un `enum`, y la
escalera desaparece. Cuando te encuentres escribiendo el sexto `else if`,
detente y pregunta qué tipo está faltando.
:::

## `switch`: cuando la pregunta es "¿cuál de estos?"

Si todas las pruebas comparan la **misma variable** con valores exactos, el
`switch` lo dice mejor:

```java title="Switch con flecha (Java 14+)" numbered
String tipo = "PIX";

String plazo = switch (tipo) {
    case "PIX" -> "inmediato";
    case "TARJETA" -> "2 días";
    case "BOLETO" -> "3 días hábiles";
    default -> "desconocido";
};

System.out.println(plazo);
```

Tres cosas merecen atención aquí. La flecha `->` reemplaza al `case:` con
`break`. El `switch` **devuelve un valor**: es una expresión, no solo un
desvío. Y el `default` es obligatorio cuando asignas el resultado a una
variable: el compilador exige que todos los caminos produzcan algo.

:::compare left="switch antiguo (hasta Java 13)" right="switch moderno (14+)"
switch (tipo) {
  case "PIX":
    plazo = "inmediato";
    break;
  case "TARJETA":
    plazo = "2 días";
    break;
  default:
    plazo = "?";
}
---
plazo = switch (tipo) {
  case "PIX" -> "inmediato";
  case "TARJETA" -> "2 días";
  default -> "?";
};
:::

:::trivia
Ese `break` obligatorio de la forma antigua existe por una funcionalidad
llamada *fall-through*: sin él, la ejecución se desliza al `case`
siguiente. Era intencional en C, para agrupar casos, y se volvió la fuente
número uno de bugs en `switch`. La forma con flecha no se desliza, y por eso
se creó.
:::

## Cuál usar

| Situación | Elección |
|---|---|
| Una condición con rango (`>=`, `&&`) | `if` |
| Dos o tres rangos ordenados | escalera de `else if` |
| Muchos valores exactos de la misma variable | `switch` |
| Elegir **un valor** entre dos | ternario |
| Muchos valores exactos + comportamiento | `enum` (capítulo 12) |

Tabla: No es cuestión de gusto: cada forma comunica una intención distinta a
quien lea después.

:::practice
Corre la escalera de notas con `9`, `7`, `5` y `4.9`. Después invierte el
orden de las pruebas y córrela de nuevo con los mismos valores. Guarda las
dos salidas: es la demostración más corta de que el orden de las condiciones
es lógica, no estilo.
:::

:::story
Dos semanas después, Marina borró los treinta y siete `if` y dejó cuatro
líneas en su lugar. Carlos preguntó cómo.

—La regla no cambió —dijo ella—. Solo dejó de vivir en treinta y siete
lugares.

El cómo está en el capítulo 12.
:::

## Un `if` que vas a escribir mucho

El proyecto del libro es una API, y una API pasa el día respondiendo una
sola pregunta: *¿esto existe?* La forma de esa decisión en Java moderno es
esta:

```java title="El formato que reaparece en el capítulo 22" numbered
Optional<Product> encontrado = repository.findById(id);

if (encontrado.isEmpty()) {
    throw new ProductNotFoundException(id);
}
return encontrado.get();
```

Todavía no conoces `Optional`, ni `throw`, ni repositorio. Guarda solo la
forma: **trata primero el caso malo y sal**. Ese patrón, llamado *early
return*, mantiene el código poco profundo: sin él, una API real acumula
cinco niveles de `if` anidados.

:::summary
- `if` exige `boolean`; un número no vale como condición.
- Usa llaves siempre: la sangría no significa nada para el compilador.
- En una escalera, la primera prueba verdadera gana: ordena de la más
  restrictiva a la más general.
- El `switch` con flecha devuelve un valor y no se desliza al caso
  siguiente.
- Trata primero el caso malo y sal: el código queda poco profundo.
:::

:::checkpoint
Escribes decisiones simples y encadenadas, eliges entre `if`, `switch` y
ternario por intención, y reconoces el camino implícito de un `if` sin
`else`.
:::

:::milestone
El programa ahora decide. Todavía no guarda nada ni le responde a nadie,
pero la lógica que va a rechazar un precio negativo en el capítulo 25 es
exactamente esta.
:::

:::exercise level=1
Escribe un programa que reciba una temperatura como argumento e imprima
`"Fiebre"` por encima de 37.8 y `"Normal"` en caso contrario.

:::answer
```java
double temperatura = Double.parseDouble(args[0]);
if (temperatura > 37.8) {
    System.out.println("Fiebre");
} else {
    System.out.println("Normal");
}
```
:::

:::exercise level=2
Calcula la tarifa de un estacionamiento: la primera hora cuesta R$ 8, cada
hora siguiente cuesta R$ 5 y el valor máximo del día es R$ 40. Prueba con 1,
3 y 12 horas.

:::answer
```java
int horas = Integer.parseInt(args[0]);
double valor = 8 + (horas - 1) * 5;
if (valor > 40) {
    valor = 40;
}
System.out.println("R$ " + valor);
```
El tope entra **después** del cálculo, como una segunda decisión. Intentar
resolver el límite dentro de la misma expresión es el camino más corto a un
error difícil de ver.
:::

:::exercise level=3
Reescribe la escalera de notas usando `switch` con flecha y el resultado
entero de la división por 10 (`(int) nota / 10`). Después decide cuál de las
dos versiones dejarías en el proyecto y justifícalo.

:::answer
```java
String calificacion = switch ((int) nota / 10) {
    case 10, 9 -> "Excelente";
    case 8, 7 -> "Bueno";
    case 6, 5 -> "Regular";
    default -> "Insuficiente";
};
```
Funciona y es más corta. Pero la versión con `if` dice explícitamente
`nota >= 9`, mientras que esta exige que el lector reconstruya el rango a
partir de una división. Para rangos, `if` comunica mejor; para valores
exactos, `switch`. La respuesta correcta es saber por qué.
:::
