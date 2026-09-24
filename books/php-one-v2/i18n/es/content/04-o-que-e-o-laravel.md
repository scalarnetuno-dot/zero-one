---
source_hash: 1720405ffbbc
title: "Qué es Laravel"
number: 4
slug: o-que-e-o-laravel
part: p1
kicker: "La respuesta a la pregunta de la pasante tiene dos partes: lo que el framework hace por ti, y lo que decide sin preguntar."
goal: >-
  Describir el ciclo de una petición Laravel señalando, en cada etapa, el
  equivalente en el micro-framework del capítulo anterior, y saber nombrar
  lo que la convención cobra a cambio de lo que entrega.
---

*"¿Por qué no usamos este y listo?"*

Porque el archivo de cien líneas atiende tres rutas y no valida la
entrada, no trata errores, no habla con la base, no autentica a nadie, no
estandariza respuestas, no tiene pruebas y no tiene documentación.
Completar esa lista es el trabajo de un año, y el resultado sería un
framework con un solo mantenedor.

La respuesta larga es este capítulo, y no empieza en "Laravel es
excelente". Empieza en qué es, exactamente, un framework.

## Un framework es código que llama al tuyo

Una **biblioteca** es código que tú llamas. Decides cuándo, pasas los
argumentos y recibes el resultado. `symfony/var-dumper` es una biblioteca:
escribes `dump()` donde quieras.

Un **framework** es lo contrario: él es el programa, y tu código son los
pedazos que él llama. No escribes el bucle principal, no tratas la
petición, no decides el orden de las etapas. Llenas huecos que alguien ya
numeró.

:::term Inversión de control
El nombre de eso. Con una biblioteca, el control es tuyo y pides ayuda;
con un framework, el control es suyo y él pide tu código.

No es una cuestión de tamaño. Hay frameworks pequeños y bibliotecas
enormes. La diferencia es quién llama a quién.
:::

Eso tiene una consecuencia práctica que aparece el primer día: **no eliges
la estructura de carpetas, el nombre de los archivos ni el formato de las
clases.** El framework eligió, y el precio de discrepar es mayor que el de
aceptar.

## Las piezas

Laravel no se escribió desde cero en 2011. Es un montaje, y buena parte de
las piezas de abajo vienen de Symfony:

| Pieza | Origen | Trabajo |
|---|---|---|
| `Illuminate\Http\Request` | extiende la de Symfony | la petición como objeto |
| `Illuminate\Http\Response` | extiende la de Symfony | la respuesta como objeto |
| `Illuminate\Console\Command` | extiende la de Symfony | los comandos de terminal |
| `Illuminate\Container` | propio | resuelve dependencias |
| `Illuminate\Routing` | propio | la tabla de rutas |
| Eloquent | propio | objetos que hablan con la base |
| Blade | propio | generar HTML |

Tabla: `Illuminate` es el nombre del conjunto de componentes de Laravel.
Cada uno se puede instalar solo, fuera del framework.

Es una información útil y rara vez dicha: cuando lees `Request` en el
código de un proyecto Laravel, estás mirando una clase que hereda de una
pieza de Symfony con más de quince años de uso. La parte "mágica" del
framework es más delgada de lo que parece, y la parte probada, más gruesa.

## El ciclo de una petición

Aquí está el capítulo entero en una tabla. A la izquierda, lo que
escribiste a mano; a la derecha, quién hace el mismo trabajo en Laravel.

| En tu `mini.php` | En Laravel |
|---|---|
| el archivo entero | `public/index.php` |
| — | `bootstrap/app.php` arma la aplicación |
| — | los *service providers* registran e inician |
| `Contenedor::obtener` | `Illuminate\Container\Container` |
| el `array_reduce` de las capas | `Illuminate\Pipeline\Pipeline` |
| `$rutas`, el array | `routes/api.php` y `routes/web.php` |
| `Enrutador::despachar` | `Illuminate\Routing\Router` |
| la función de la ruta | tu controller |
| `Respuesta` | `Illuminate\Http\Response` |
| `enviar()` | `$response->send()` |

Tabla: Dos líneas no tienen equivalente en tu archivo, y son justamente
las dos que hacen que un framework crezca sin volverse un desorden.

**`bootstrap/app.php`** es el lugar donde se arma la aplicación antes de
que llegue cualquier petición: qué archivos de rutas existen, qué capas
corren en cada grupo, qué hacer con una excepción no tratada. En tu
archivo, eso estaba mezclado con las rutas porque eran tres.

**Service provider** es la pieza que todavía no tienes y vas a querer.
Cada parte del framework —base, cola, caché, sesión— tiene un archivo que
le dice al contenedor cómo construirla. Corren en dos fases: primero todos
*registran* lo que saben hacer, después todos *inician*.

:::key
La separación en dos fases existe por un motivo que reconoces del
contenedor del capítulo anterior: al iniciar, un proveedor puede necesitar
algo que registró otro.

Registrar es barato y no depende de nadie. Iniciar puede depender de todo
el mundo. Hacer las dos cosas en una sola pasada crearía un orden de carga,
y el orden de carga es el problema del `funciones2_NUEVO_final.php`, en un
edificio más grande.
:::

Y las **facades**, en una frase, porque confunden a quien llega:
`Cache::get()` no es un método estático de verdad: es un atajo que le
pregunta al contenedor qué objeto responde por "cache" y llama al método en
él. Comodidad de escritura, con el objeto real debajo.

## Convención sobre configuración, y lo que cuesta

Laravel decide muchas cosas por ti. Dónde viven los controllers, cómo se
llaman las clases, qué tabla usa un model, en qué orden corren las capas,
cómo un error se vuelve respuesta.

Cada una de esas decisiones es tiempo que no gastas, y una libertad que no
tienes.

| Lo que entrega la convención | Lo que cobra |
|---|---|
| ninguna decisión de estructura el día 1 | la estructura no se discute el día 300 |
| cualquier persona de la comunidad lee el proyecto | el proyecto se parece a todos los demás |
| actualización de versión con camino listo | salirse del camino encarece la actualización |
| respuesta lista para el problema común | el problema poco común pelea contra el estándar |

Tabla: El intercambio es bueno en la mayoría de los proyectos, y es un
intercambio. Quien lo llama "pura ventaja" todavía no tuvo un requisito
que pelee con el estándar.

:::pitfall
El error que sale caro no es elegir la convención. Es **rechazarla a
medias**: mantener el framework y reescribir la parte que no te gustó.

El resultado es un proyecto que ni sigue el manual ni tiene un manual
propio, y en el que cada persona nueva tiene que aprender dos veces: cómo
lo hace Laravel y cómo lo hacemos aquí.

Si la convención no sirve, el camino honesto es discutirlo antes de elegir
el framework, y no seis meses después con el plazo encima.
:::

## Lo que decide por ti, y cómo discrepar

No todo es impuesto. Vale la pena saber dónde hay espacio:

**No se puede cambiar sin dolor:** la estructura de carpetas de primer
nivel, el ciclo de la petición, el contenedor y el formato del archivo de
rutas.

**Se puede cambiar, y es común:** la capa de base —se puede usar
Eloquent, una consulta escrita a mano o las dos—; la capa de respuesta; la
organización interna de `app/`, que el framework no fiscaliza.

**Es solo un estándar, y a nadie le importa:** los nombres de carpetas
dentro de `app/`, el formato de los controllers, cuántos archivos de rutas
existen.

La regla: **cuanto más cerca del ciclo de la petición, menos negociable.**
Cuanto más cerca de tu regla de negocio, más.

## Laravel, Symfony o ninguno de los dos

Los tres son respuestas legítimas.

**Laravel** entrega más cosas listas y decide más por ti. Cola, correo,
autenticación, programación de tareas y subida de archivos vienen
configurados, y el camino de cada uno está documentado en el mismo lugar.
El costo es que salirse de los rieles da trabajo.

**Symfony** entrega piezas más sueltas y una configuración más explícita.
Pide más decisiones al principio y cobra menos por decisiones raras
después. Es la elección frecuente de las empresas grandes con equipo de
plataforma.

**Ninguno de los dos** es la respuesta correcta en dos situaciones reales:
un servicio con una sola ruta, en el que el framework sería más código que
el servicio; y un proyecto cuyo problema es tan específico que ninguna
convención ayuda, lo que es raro, y casi siempre se alega antes de que sea
verdad.

Para la Casa Amarela, la decisión cabe en una línea: un CRUD con reglas de
negocio, autenticación simple, informes, cola de recordatorios y una
pantalla administrativa es exactamente el formato para el que se diseñó
Laravel.

:::note En tu carrera
"¿Qué framework es mejor?" es la pregunta de quien todavía no eligió
ninguno. La pregunta de quien ya entregó es otra: **¿qué fricción voy a
tener, y es una fricción que sé pagar?**

Toda elección de tecnología tiene un lugar donde duele. Saber nombrar ese
lugar antes de empezar es la diferencia entre una decisión y una apuesta, y
es la respuesta que impresiona en una entrevista técnica, porque muestra
que llevaste un proyecto hasta el punto en que apareció el dolor.

Cuando alguien defienda una elección y no pueda decir lo que cuesta,
todavía no es una defensa. Es entusiasmo, y el entusiasmo tiene fecha de
vencimiento corta.
:::

:::milestone
Fin de la Parte 1. Leíste una petición en el cable, diseñaste las
direcciones de la API antes de la primera ruta, escribiste las cuatro
piezas que tiene todo framework PHP y viste dónde vive cada una en un
framework de verdad. A partir de aquí entra Laravel, y ninguna parte de él
debería parecer magia.
:::

:::summary
- Una biblioteca es código que llamas; un framework es código que llama al
  tuyo.
- `Illuminate` es el conjunto de componentes de Laravel, y las piezas de
  HTTP y consola heredan de Symfony.
- El ciclo es el mismo del micro-framework, con dos piezas más:
  `bootstrap/app.php` y los service providers.
- Los providers registran en una fase e inician en otra, para no depender
  del orden de carga.
- Una facade es un atajo a un objeto que vive en el contenedor, no un
  método estático de verdad.
- La convención entrega velocidad el día 1 y cobra libertad el día 300.
- Rechazar la convención a medias es peor que aceptarla o que no usar el
  framework.
- Cuanto más cerca del ciclo de la petición, menos negociable; cuanto más
  cerca de la regla de negocio, más.
:::

:::checkpoint
Describes el ciclo de una petición Laravel desde el `index.php` hasta la
respuesta, señalas el equivalente de cada etapa en el archivo que
escribiste a mano, explicas qué es una facade sin usar la palabra magia, y
puedes decir lo que cuesta la convención del framework.
:::

:::exercise level=1
Para cada ítem, di si es biblioteca o framework, y por qué:

1. `symfony/var-dumper`
2. Laravel
3. PHPStan
4. Eloquent, usado solo, fuera de Laravel

:::answer
1. **Biblioteca.** Llamas a `dump()` donde quieras; no llama a nada tuyo.
2. **Framework.** Corre el ciclo y llama a tu controller.
3. **Herramienta**, y vale la pena separar la categoría: a PHPStan no lo
   llama tu programa ni él llama a tu programa: **lee** tu programa, y corre
   fuera de la ejecución. Analizador, formateador y pruebas son de esa
   familia.
4. **Biblioteca.** Fuera del framework, Eloquent es un paquete que
   instalas, configuras y llamas. Se vuelve parte de un framework cuando el
   framework es quien decide cuándo llamarlo.

El caso 4 es el interesante: la misma clase es biblioteca o parte de un
framework según quién esté al mando. La distinción no está en el código:
está en la dirección de la llamada.
:::

:::exercise level=2
Toma el `mini.php` del capítulo anterior y escribe, para cada pieza, una
frase que diga qué hace Laravel **de más** en el mismo punto.

Cubre: front controller, enrutador, contenedor y middleware.

:::answer
**Front controller.** Tu `mini.php` lee el verbo y la ruta y despacha. El
`public/index.php` de Laravel primero arma la aplicación, corre los service
providers, resuelve el entorno y la configuración, y recién entonces
entrega la petición; y al final trata la excepción que nadie atrapó,
transformándola en una respuesta con el formato correcto.

**Enrutador.** El tuyo hace coincidir una expresión regular por ruta, en
orden. El de Laravel compila las rutas, las agrupa por método, aplica las
restricciones declaradas, resuelve el nombre de una ruta a una URL, y
además busca el registro en la base cuando el parámetro es un model.

**Contenedor.** El tuyo resuelve parámetros que son clases y guarda lo que
construyó. El de Laravel hace eso y más: acepta instrucciones explícitas
para lo que no se puede adivinar, sabe atar una interfaz a una
implementación, distingue lo que es único de lo que es nuevo en cada
resolución, y puede construir el mismo objeto de formas distintas según el
contexto.

**Middleware.** El tuyo es una cadena. El de Laravel es una cadena por
grupo de rutas, con parámetros por ruta, orden declarado y la posibilidad
de correr trabajo **después** de que la respuesta ya se envió.

El patrón de las cuatro respuestas es el mismo, y es el punto del
capítulo: ninguna es una idea nueva. Todas son la misma idea con los casos
difíciles tratados.
:::

:::exercise level=3
Una empresa va a empezar un sistema nuevo y el equipo está dividido entre
Laravel y "sin framework, solo las bibliotecas que necesitemos".

Escribe los tres argumentos más fuertes de cada lado —los de verdad, no
los de internet— y di qué información sobre el proyecto decidiría la
cuestión.

:::answer
**A favor de Laravel.**

El primero es el costo de lo que no es tu problema: autenticación, cola,
correo, programación de tareas y subida de archivos ya existen, probados
por mucha gente, y ninguno diferencia tu producto.

El segundo es la contratación y la continuidad: hay gente que ya conoce la
estructura, y quien entre al proyecto dentro de dos años va a reconocer el
diseño sin un mes de lectura.

El tercero es el mantenimiento de seguridad. Cuando aparece una falla en
una pieza común, la corrige quien mantiene el framework, y tú actualizas
una dependencia. Sin framework, cada pieza es tuya.

**A favor de no usarlo.**

El primero es el tamaño de lo que cargas: un servicio con dos rutas corre
más rápido, arranca más rápido y tiene menos superficie de ataque sin
cincuenta paquetes que no usa.

El segundo es la libertad de diseño. Si el proyecto tiene una restricción
poco común —latencia muy baja, formato de mensaje propio, un modelo de
concurrencia distinto—, la convención se vuelve una pelea diaria.

El tercero es la claridad: sin framework, lo que pasa está escrito en tu
repositorio, y el camino de la petición cabe en la cabeza de una persona.

**La información que decide.** Cuántas de estas cosas va a necesitar el
sistema en los próximos dos años: usuario con sesión, permisos por perfil,
envío de correo, trabajo en segundo plano, pantalla administrativa,
informes, subida de archivos.

Si la respuesta es "casi todas", el framework ya ganó, porque la
alternativa no es "sin framework": es "con un framework peor, escrito aquí
adentro, sin documentación". Si la respuesta es "ninguna, es un servicio
que recibe JSON y devuelve JSON", el equipo que quiere quedarse sin
framework tiene razón.
:::
