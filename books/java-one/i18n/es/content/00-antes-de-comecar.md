---
source_hash: 41c088731d81
title: "Antes de empezar"
matter: front
numbered: false
kicker: "Un libro corto sobre un lenguaje que suele enseñarse demasiado largo."
---

Hay dos maneras de enseñar Java. La primera presenta el lenguaje entero
—treinta años de recursos, cuatro tipos de bucle, ocho modificadores, la
jerarquía de colecciones en un diagrama del tamaño de una pared— y promete
que un día todo eso se vuelve un programa. La segunda elige un programa y
enseña solo el Java que ese programa exige, cuando lo exige.

Este libro es del segundo tipo. Tiene un proyecto: una API REST de catálogo
de productos, con base de datos, validación, autenticación, pruebas y
documentación. Vas a construirla. Cada concepto del lenguaje aparece en el
capítulo en que el proyecto lo necesita, y no antes.

:::key
El libro no es una referencia de Java. Es un camino hasta una API
funcionando. Si después quieres la referencia completa, cabe en un sitio
web; lo difícil de encontrar es el camino.
:::

## Cómo funciona este libro

El proyecto crece en línea recta. En el capítulo 2 imprimes una línea en la
terminal; en el 17 respondes una petición HTTP; en el 23 tienes un CRUD
completo; en el 32 proteges ese CRUD con un token; en el 42 lo subes todo en
un contenedor. Cada capítulo cierra con el estado del proyecto en ese
punto:

:::milestone
Tienes: nada todavía. Una terminal abierta, un JDK instalado y una carpeta
vacía. Es exactamente de aquí de donde empieza todo software.
:::

El camino no es limpio, a propósito. Vas a escribir código que se rompe,
leer el mensaje de error entero y arreglarlo. Así se aprende a programar de
verdad, y es la parte que los tutoriales recortan en la edición.

## Lo que necesitas

Un JDK 21 o más nuevo, un editor de texto y una terminal. Una base
PostgreSQL aparece en la Parte 4, y el capítulo 19 explica cómo levantar
una en dos minutos. Nada más.

```bash title="Confirma que todo está en su lugar"
java -version
javac -version
```

Si los dos responden con un número de versión, estás listo.

:::pitfall
Que `java -version` responda y `javac -version` no es el síntoma clásico de
haber instalado un JRE en vez de un JDK. El JRE solo ejecuta; el JDK
compila. Necesitas el segundo.
:::

## El elenco

Entre una explicación y otra, vas a encontrar escenas de una empresa. Se
llama Aurora Comércio, vende de todo por internet y acaba de decidir que
necesita una API, de preferencia para ayer.

Las escenas no son adorno: existen porque un concepto abstracto se pega
mejor cuando viene unido a una situación que reconoces. Cuando el libro
explique `NullPointerException`, te vas a acordar de don Antônio.

:::story Los cinco que vas a conocer
**Carlos** entró hace tres semanas. Sabe lógica, no sabe Java, y le
asignaron "ese proyectito de la API". Él eres tú.

**Marina** es la desarrolladora sénior. Ya vio esta película, sabe cómo
termina y aun así insiste en revisar cada *pull request* línea por línea.

**Roberto** es el gerente. No escribe código, escribe plazos. Para él,
cualquier pedido cabe en la frase "es solo un cambiecito".

**Cláudia** se ocupa del producto. Trae requisitos nuevos con la
naturalidad de quien trae café, incluso la víspera de la entrega.

**Don Antônio**, 68 años, es el primer cliente de la tienda. En dos minutos
de uso encuentra errores que el equipo no reproduce en dos semanas.
:::

:::art caption="El equipo de Aurora Comércio el primer día del proyecto." src="o-time-da-aurora-comercio-no-primeiro-dia-do-projeto.png"
Ilustração editorial minimalista em traço limpo: cinco personagens de corpo
inteiro lado a lado, como um retrato de elenco, sobre fundo branco. Carlos,
jovem desenvolvedor segurando um notebook novo demais e uma expressão de
otimismo ingênuo. Marina, desenvolvedora sênior de braços cruzados, caneca
de café, olhar de quem já sabe o que vem. Roberto, gerente de camisa social,
apontando para um cronograma impresso onde se lê apenas "3 SEMANAS".
Cláudia, product owner com um caderno cheio de post-its coloridos
transbordando. Seu Antônio, senhor de 68 anos com óculos na ponta do nariz,
segurando um celular na horizontal e apertando a tela com o dedo indicador.
Humor sutil, poucos elementos, sem cenário elaborado, estética de revista de
tecnologia, personagens expressivos, sem estética infantil.
:::

## Convenciones

Fragmentos como `System.out.println` aparecen en fuente de código cuando se
citan en medio de la frase. Los bloques más grandes vienen con el nombre
del archivo arriba: en Java ese nombre importa más que en casi cualquier
otro lenguaje, y el capítulo 2 explica por qué.

Cinco marcas aparecen en los márgenes del texto, y vale la pena
reconocerlas de antemano:

:::trivia
**¿Sabías que?** trae la curiosidad, la historia, la decisión de diseño que
se quedó. Se puede saltar sin perjuicio, pero es lo que te permite contar
la historia en la mesa de un bar.
:::

:::pitfall
**Error común** muestra la trampa antes de que caigas en ella. Casi siempre
es un error que yo cometí.
:::

:::history
**Tras bambalinas** cuenta por qué el lenguaje es así. Java tiene muchas
decisiones extrañas, y casi todas tienen un motivo con fecha.
:::

:::checkpoint
**Punto de control** cierra el capítulo enumerando lo que ya sabes hacer: no
lo que leíste, lo que *sabes hacer*.
:::

Y **El proyecto ahora** es el hito del capítulo: una frase sobre dónde está
la API. Si abres el libro por la mitad, es lo primero que debes buscar.
