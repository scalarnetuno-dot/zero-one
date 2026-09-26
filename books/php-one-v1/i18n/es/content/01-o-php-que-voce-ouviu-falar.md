---
source_hash: 63fdb25c80ae
title: "El PHP del que te hablaron"
number: 1
slug: o-php-que-voce-ouviu-falar
part: p1
kicker: "Un lenguaje hecho para contar visitas en un currículum, que hoy atiende una parte enorme de la web — con tipos, enums y una versión nueva cada noviembre."
epigraph: "No sabía cómo parar. No tenía idea de cómo escribir un lenguaje de programación. Solo fui añadiendo el siguiente paso lógico en el camino."
epigraph_by: "Rasmus Lerdorf, creador de PHP"
goal: >-
  Saber de dónde viene PHP, qué causó su fama antigua y cuándo se eliminó
  cada causa, qué tiene el lenguaje hoy, qué resuelve bien, quién lo usa y
  por qué no va a morir pronto.
---

:::story ¿No se podía hacer en Node?
El Dr. Aurélio había visto una charla el jueves y volvió con una pregunta
el viernes.

— Este proyecto de la biblioteca. ¿Por qué PHP?

— El sistema actual es PHP — dijo Dedé. — El hosting es PHP. Vera usa PHP
desde 2009.

— ¿Pero no íbamos a modernizar?

— Vamos a hacerlo. De PHP 5.4 a PHP 8.

El Dr. Aurélio hizo el gesto de quien se aparta algo de la cara.

— ¿No se podía hacer en Node?

— Se podía.

— ¿Entonces?

— Entonces reescribimos todo, tiramos quince años de reglas de negocio que
no están documentadas en ninguna parte, y entregamos el 31 de marzo.

Pausa.

— Es que PHP es medio... — buscó la palabra — ...viejo.

— La versión actual salió en noviembre.

Márcia habló sin levantar los ojos de la planilla.

— ¿La nómina de Vertexo corre en qué?

Cléber carraspeó.

— PHP.

— ¿Qué versión?

— Cinco punto seis.
:::

Esta conversación ocurre en algún lugar del mundo todos los días, y el
malentendido es siempre el mismo: la fama de PHP describe, con precisión,
un lenguaje que dejó de existir hace más de diez años.

Los defectos que la generaron fueron reales, tenían nombre y tenían fecha —
y todos fueron eliminados, uno por uno, entre 2012 y 2021. El PHP que vas a
aprender aquí no es aquel lleno de parches: es un lenguaje tipado, rápido y
previsible, con calendario público de versiones y una década de
correcciones hechas.

Vale la pena dedicar un capítulo a entender esa diferencia por dos motivos.
El primero es que explica las decisiones extrañas que vas a encontrar en
código antiguo — y lo vas a encontrar, porque quince años de PHP siguen en
producción. El segundo es que es el argumento que querrás tener a mano
cuando alguien repita el chiste en una reunión.

## Un currículum, en 1994

Rasmus Lerdorf era un programador danés-canadiense que quería saber cuántas
personas visitaban su currículum en internet. Escribió, en C, un puñado de
programitas que hacían eso y llamó al conjunto **Personal Home Page
Tools**.

No era un lenguaje. Era una utilidad personal, publicada en 1995 porque
otras personas la pidieron.

Lo que pasó después es lo más importante de la historia de PHP: **creció
por demanda, no por diseño**. Alguien necesitaba hablar con una base de
datos, entonces apareció una función. Alguien necesitaba procesar un
formulario, entonces apareció una forma. Cada pedido se convirtió en una
función nueva, con el nombre que pareció razonable ese día, en el orden de
argumentos que pareció razonable ese día.

Veinticinco años después, por eso `strlen($texto)` recibe el texto primero
e `in_array($aguja, $pajar)` recibe la aguja primero. Nadie lo decidió.
Simplemente ocurrió.

:::trivia
El nombre es un acrónimo recursivo: **PHP: Hypertext Preprocessor**.
Empieza con una sigla que se refiere a sí misma, un chiste de programador
de los años noventa, y reemplazó el nombre original — *Personal Home Page*
— cuando quedó claro que la cosa había ido más allá del currículum de
Rasmus.
:::

En 1997, dos estudiantes en Haifa, Andi Gutmans y Zeev Suraski, decidieron
reescribir el intérprete porque querían usar PHP en un trabajo de la
universidad y no aguantaba. De esa reescritura salió PHP 3, y de la empresa
que ambos fundaron salió el motor que ejecuta el lenguaje hasta hoy.

## Los hitos que todavía afectan a tu código

:::diagram type="timeline" caption="Por qué el lenguaje es así: los hitos que vas a encontrar en código real."
width: 112
events:
  - { year: "1995", text: "Rasmus Lerdorf publica PHP Tools: contar visitas en un currículum" }
  - { year: "1998", text: "PHP 3, reescrito por Gutmans y Suraski — el lenguaje empieza aquí", mark: true }
  - { year: "2004", text: "PHP 5: objetos de verdad, excepciones y PDO" }
  - { year: "2009", text: "PHP 5.3 trae namespaces y closures, diez años tarde", mark: true }
  - { year: "2010", text: "PHP 6 se abandona sin llegar a existir; el número se salta" }
  - { year: "2012", text: "Composer: dependencias resueltas por una herramienta, no por FTP", mark: true }
  - { year: "2015", text: "PHP 7: cerca del doble de rápido, y tipos en parámetros", mark: true }
  - { year: "2020", text: "PHP 8: match, enums en camino, argumentos con nombre, JIT", mark: true }
  - { year: "2021", text: "PHP 8.1: enums y readonly — el lenguaje se vuelve tipado de verdad" }
  - { year: "2024", text: "PHP 8.4: property hooks; una versión nueva por año, cada noviembre" }
:::

Fíjate en dos fechas.

**2009** es cuando PHP ganó namespaces — la forma de organizar código en
paquetes sin que dos archivos se peleen por el mismo nombre. Hasta entonces,
la salida era escribir clases llamadas `Zend_Db_Table_Row_Abstract`. Todo el
código PHP anterior a esa fecha tiene esa cara, y todavía está corriendo en
algún lugar.

**2015** es cuando el lenguaje se volvió rápido. PHP 7 trajo un motor nuevo
y cerca del doble del rendimiento de la versión anterior, sin que nadie
tuviera que cambiar una línea. Fue la mayor actualización gratuita de la
historia de la web, y buena parte del ahorro en servidores de esa década
salió de ahí.

:::trivia
**PHP 6** existió durante cinco años en forma de intento: una reescritura
para tratar el texto en Unicode de punta a punta. Resultó demasiado grande
y se abandonó alrededor de 2010.

Cuando la versión siguiente estuvo lista, la comunidad votó saltarse el
número 6 y llamarla 7 — porque ya existían libros publicados sobre "PHP 6"
que describían un lenguaje que nunca salió. Es el único lenguaje popular
que se saltó una versión entera para no confundir a quien había comprado el
libro equivocado.
:::

## De dónde vino la fama, y qué pasó con cada cosa

La reputación antigua no fue prejuicio: tuvo cuatro causas concretas, y las
cuatro eran ciertas. Están aquí por dos motivos prácticos — para que las
reconozcas cuando abras un sistema de 2009, y para que sepas, de cada una,
en qué versión dejó de existir.

**`register_globals`.** Hasta PHP 4.2, activado por defecto: cualquier
parámetro que llegara en la URL se convertía automáticamente en una
variable dentro de tu programa. Una página que comprobaba `if ($admin)` se
podía abrir con `?admin=1`. Se eliminó recién en PHP 5.4, en 2012.

**`magic_quotes`.** PHP escapaba por su cuenta todo lo que venía de un
formulario, con la esperanza de evitar ataques de inyección. El efecto real
fue producir una generación de programadores que creía estar protegida sin
estarlo, y una base de datos llena de `O\'Brien`. Eliminado en la misma
versión.

**Las funciones `mysql_*`.** La forma antigua de hablar con la base de
datos era armar la consulta pegando texto. Eso funciona e invita al mayor
agujero de seguridad de la historia de la web. Se desaconsejaron en 2013 y
se eliminaron en 2015 — veinte años después de haberle enseñado el hábito a
todo el mundo.

**El fallo silencioso de la biblioteca estándar.** Las funciones internas
devolvían `false` cuando algo salía mal, en lugar de quejarse — y un
programa que no revisaba el retorno seguía adelante con un valor inválido en
la mano. Eso terminó en PHP 8.0, en 2020: esas funciones pasaron a lanzar
excepciones, y el error dejó de poder ignorarse.

Quedó la parte cosmética de esta historia — `strlen($texto)` recibe el
texto primero e `in_array($aguja, $pajar)` recibe la aguja primero. Los
nombres y los órdenes siguen como están porque cambiarlos rompería millones
de sitios que funcionan, y esa es la decisión correcta. En la práctica, es
un detalle que el editor de código resuelve mientras escribes.

| La causa | Cuándo dejó de existir |
|---|---|
| `register_globals` | PHP 5.4, en 2012 |
| `magic_quotes` | PHP 5.4, en 2012 |
| funciones `mysql_*` | PHP 7.0, en 2015 |
| fallo silencioso en las funciones internas | PHP 8.0, en 2020 |
| ausencia de tipos declarados | PHP 7.0 en 2015; enums y `readonly` en 2021 |

Tabla: Ningún elemento de esta lista describe el PHP que vas a instalar.
Todos describen código que todavía puede estar corriendo en algún servidor.

En 2012, un texto llamado *"PHP: a Fractal of Bad Design"* catalogó todo
esto y se convirtió en la referencia de quien quiere atacar el lenguaje. Es
largo, detallado y tenía razón cuando se escribió.

Lo que rara vez se menciona es lo que pasó después: la comunidad lo leyó,
estuvo de acuerdo con buena parte y pasó una década arreglando, punto por
punto, en el orden en que aparecían en la crítica. Hoy el texto es un
documento histórico — y la línea de tiempo de la tabla de arriba es la
respuesta.

## Lo que cambió de verdad

Cuatro cosas, y solo la primera es de sintaxis.

**El lenguaje se volvió tipado.** Puedes declarar el tipo de cada
parámetro, de cada retorno y de cada propiedad, y pedirle a PHP que rechace
lo que no encaje. Existen `enum`, `readonly`, `match` y tipos que combinan
otros tipos. No es Java, y ya no es la tierra sin ley de 2009.

**Apareció una forma de instalar código ajeno.** Antes de 2012, usar una
biblioteca significaba bajar un `.zip`, copiarlo en una carpeta y cruzar
los dedos. Composer trajo lo que Ruby, Python y Node ya tenían: un archivo
que declara lo que usa el proyecto, y un comando que resuelve el resto.

**Aparecieron convenciones compartidas.** Un grupo de mantenedores de
proyectos grandes empezó a publicar estándares — las PSR — que dicen cómo
nombrar archivos, cómo cargarlos, cómo registrar logs, cómo representar una
petición HTTP. Suena burocrático y es la razón por la que bibliotecas de
autores distintos hoy funcionan juntas.

**Aparecieron herramientas que leen tu código.** Analizadores estáticos
como PHPStan y Psalm encuentran, sin ejecutar nada, el error de tipeo que
antes solo aparecía en producción a las tres de la mañana.

Vale detenerse un segundo en lo que significa esta lista, porque es el
argumento más fuerte a favor del lenguaje y casi nunca se plantea.

Un lenguaje con treinta años de vida acumula malas decisiones — todos lo
hacen. Lo que distingue a una herramienta en la que vale la pena invertir
una carrera no es no haberse equivocado nunca: es lo que hace con el error
una vez descubierto.

PHP eliminó sus propias funciones peligrosas, en versiones numeradas, con
fecha y aviso previo. Cambió el motor entero y entregó el doble de
rendimiento sin cobrar una reescritura. Adoptó gestor de paquetes, tipos,
estándares de interoperabilidad y análisis estático — cada uno después de
una discusión pública, con votación registrada.

Es una década de deuda técnica pagada al contado, en público, por un
proyecto que podría haber elegido simplemente no tocar nada. Muchos
lenguajes que hoy se citan como "la elección segura" nunca tuvieron que
hacerlo, y nadie sabe cómo se comportarían si les tocara.

:::key
Elegir una tecnología es apostar por lo que va a ser dentro de cinco años,
no por lo que fue hace quince.

Las señales que importan en esa apuesta son tres, y PHP tiene las tres:
**versión nueva en calendario fijo**, **proceso de decisión público** e
**historial de arreglar lo que estaba mal en vez de defenderlo**.
:::

## Lo que PHP resuelve bien

Vale ser específico, porque "es bueno para la web" no explica nada.

**Cada petición empieza de cero.** Cuando alguien pide una página, PHP arma
todo, responde y lo tira todo. Nada sobrevive para la petición siguiente.

Parece un desperdicio y es una ventaja enorme: no hay fuga de memoria que
se acumule durante una semana, no hay estado compartido entre usuarios, no
hay variable global contaminada por la petición anterior. Una categoría
entera de defectos difíciles simplemente no tiene dónde ocurrir. Quien ya
persiguió una fuga en un proceso que lleva treinta días corriendo sabe
exactamente el tamaño de este regalo.

**Publicar es copiar archivos.** No hay compilación obligatoria, no hay
proceso que reiniciar, no hay servidor de aplicaciones que configurar. Un
proyecto moderno añade etapas por buenas razones, pero el mínimo sigue
siendo el mínimo — y por eso existe hosting de PHP por quince reales al mes
en cualquier lugar del mundo.

**Viene con pilas para la web.** Sesión, subida de archivos, fechas, texto,
JSON, cliente HTTP, drivers de base de datos: está todo en la caja, sin
instalar nada.

**Es suficientemente rápido.** La pregunta relevante en una aplicación web
casi nunca es la velocidad del lenguaje — es cuánto tarda la base de datos.
PHP 8 con caché de código compilado atiende bien a la aplastante mayoría de
los sistemas que alguien va a escribir.

:::term OPcache
PHP lee tu archivo `.php` y lo convierte en instrucciones internas antes de
ejecutarlo. OPcache guarda esa conversión en memoria, para que no ocurra de
nuevo en cada petición. Viene con PHP y está activado por defecto desde la
versión 5.5 — y es buena parte de la razón por la que el lenguaje es rápido
hoy.
:::

## Y lo que no resuelve

La misma lista, al revés, y es corta y honesta.

**Procesos que se quedan vivos.** WebSocket, conexiones abiertas durante
horas, miles de conexiones simultáneas esperando: eso va contra el modelo
de "empieza de cero y muere". Hay proyectos que lo resuelven, y todos están
remando contra la corriente.

**Cálculo pesado.** Procesamiento numérico, entrenamiento de modelos,
transformación de video. La respuesta correcta es otro lenguaje, llamado
desde PHP.

**Estado compartido en memoria.** Como nada sobrevive entre peticiones,
todo lo que hay que recordar va afuera — base de datos, Redis, archivo. Es
trabajo extra, y es el precio directo de la ventaja del punto anterior.

Ninguno de estos puntos es un defecto. Son el contorno de la herramienta, y
saber por dónde pasa es lo que separa elegir de repetir.

## Quién lo usa

**Wikipedia** corre en MediaWiki, que es PHP. **WordPress**, que sostiene
una porción enorme de los sitios del mundo, es PHP. **Etsy**, **Tumblr**,
**Mailchimp** y **Vimeo** tienen PHP en el núcleo — el equipo de Vimeo, por
cierto, escribió uno de los analizadores estáticos más usados del lenguaje.

**Facebook** se escribió en PHP y creció en él hasta el punto de mantener
su propio dialecto, Hack, que corre en un motor propio. **Slack** siguió el
mismo camino. Suele citarse como prueba de que PHP no escala; la lectura
más honesta es que dos de las mayores aplicaciones web del mundo se
construyeron en PHP y solo necesitaron otra cosa después de superar un
tamaño que tu sistema probablemente no va a tener.

En Europa, buena parte de los sistemas corporativos en PHP se hace sobre
Symfony — desde compañías ferroviarias hasta plataformas de viajes
compartidos. En Brasil, PHP está donde está el dinero del mercado
intermedio: agencias, comercio electrónico, ERP de tamaño medio, sistemas de
gestión, edtechs y el mostrador de miles de empresas que nunca van a
aparecer en una conferencia.

:::key
Vas a ver la estadística de que "cerca de tres cuartos de los sitios de la
web usan PHP". Es real y viene de relevamientos de tecnología de servidor,
y merece una salvedad honesta: cuenta **sitios**, no facturación ni
tráfico, y está fuertemente empujada por WordPress.

Eso no la vuelve inútil — solo cambia lo que prueba. Ninguna estadística de
adopción prueba calidad técnica, de ningún lenguaje. Lo que esta prueba es
mercado: hay una cantidad gigantesca de PHP en producción, y alguien tiene
que mantenerlo, evolucionarlo y reemplazarlo por sistemas nuevos.

La calidad técnica se argumenta por lo que el lenguaje tiene hoy — tipos,
enums, inmutabilidad, análisis estático, uno de los ecosistemas de
frameworks más maduros de la web —, y por eso ocupa un capítulo entero en
lugar de un porcentaje.
:::

## PHP no se muere

Anunciar la muerte de PHP se volvió un género literario. Sale al menos un
texto por año, con epitafio y sucesor designado, y el primero es más viejo
que buena parte de la gente que trabaja con el lenguaje hoy.

Lo mismo pasa con Java, con C y con COBOL, por un motivo que no es técnico:
un lenguaje que nadie usa no da para un artículo. En la práctica, el
anuncio de muerte funciona como indicador de uso.

Tres motivos concretos sostienen la relevancia de PHP, y ninguno es
nostalgia.

**El primero es el stock.** El software en producción no se reescribe; se
mantiene. Los sistemas que funcionan y dan ganancias no se detienen cinco
meses para cambiar de lenguaje, y la mayor parte de las vacantes de
cualquier tecnología existe por lo que ya se escribió, no por lo que se va a
escribir.

**El segundo es que todavía se empiezan proyectos nuevos en él.** Laravel
es uno de los frameworks web más usados del mundo, con un ecosistema
comercial alrededor que sostiene a gente que paga sus cuentas. No es
nostalgia: es gente eligiendo hoy.

**El tercero es la cadencia.** Desde 2015 sale una versión por año, cada
noviembre, con dos años de corrección activa y uno más de corrección de
seguridad. El lenguaje tiene plan, tiene calendario y tiene un proceso de
decisión público.

Y la delimitación honesta, porque forma parte del cuadro: PHP no es el
lenguaje de moda. Eso es distinto de estar en declive — la moda mide lo que
se dice en las conferencias; la producción mide lo que corre el martes. Si
tu objetivo es trabajar con aprendizaje automático, con sistemas de bajo
nivel o con aplicaciones nativas, este es el libro equivocado y la
herramienta equivocada, y no por un defecto suyo.

Si tu objetivo es construir y mantener sistemas que atienden empresas de
verdad, y cobrar por ello, elegiste bien. El lenguaje está más sólido que
en cualquier momento de su historia, la comunidad demostró que arregla lo
que se rompe, y el chiste de veinte años vale exactamente lo que valen los
chistes de veinte años.

:::practice
Dos verificaciones de cinco minutos, para traer este capítulo al mundo
real.

**La primera:** busca "PHP supported versions" y mira el calendario
oficial. Muestra, por versión, hasta cuándo hay corrección de defectos y
hasta cuándo hay corrección de seguridad. Anota la fecha de la versión que
acabas de instalar — y, si algún día heredas un sistema, esa es la primera
página que hay que abrir.

**La segunda:** piensa en tres sitios que usas cada semana y descubre en
qué tecnología corre cada uno. Hay extensiones de navegador que lo hacen en
un clic. El resultado suele sorprender en al menos uno de los tres.
:::

:::summary
- PHP nació en 1994 como utilidad personal y creció por demanda, no por
	diseño — de ahí los nombres de funciones inconsistentes, que se quedaron
	por compatibilidad y hoy son un detalle del editor.
- La fama antigua tiene causas con fecha, y todas se eliminaron:
	`register_globals` y `magic_quotes` en 2012, `mysql_*` en 2015, el fallo
	silencioso en 2020.
- PHP 7 duplicó el rendimiento en 2015 sin cobrar una reescritura; el 8
	trajo tipos, `match` y enums.
- Una década de deuda técnica pagada en público, con votación registrada,
	es la mejor señal disponible sobre lo que el lenguaje va a ser dentro de
	cinco años.
- Cada petición empieza de cero y muere al final: desaparece una categoría
	entera de defectos, y desaparece también el estado compartido en memoria.
- Resuelve bien sistemas web de datos y reglas de negocio; resuelve mal
	procesos largos y cálculo pesado.
- Wikipedia, WordPress, Etsy, Tumblr, Mailchimp y Vimeo corren PHP;
	Facebook y Slack corren un dialecto suyo.
- La relevancia viene del stock en producción, de proyectos nuevos que
	todavía empiezan en él, y de una versión por año con calendario público.
:::

:::exercise level=1
Ejecuta `php -v` y escribe, en una frase, qué significa cada parte de la
primera línea. Después averigua si tu versión todavía recibe correcciones
de seguridad.

:::answer
```text
$ php -v
PHP 8.3.14 (cli) (built: Nov 21 2026 09:42:15) (NTS)
```

`8.3.14` es la versión: familia 8, edición 3, corrección 14. El `(cli)` dice
que este es el PHP de línea de comandos, y no el que atiende al navegador —
esa distinción le va a costar tiempo a alguien en el próximo capítulo. La
fecha entre paréntesis es de cuándo se compiló ese ejecutable, no de cuándo
salió la versión. `NTS` quiere decir *non thread safe*, que es la variante
normal en Linux.

El calendario oficial de versiones dice hasta cuándo cada familia recibe
correcciones. La regla práctica: una versión tiene dos años de corrección de
defectos y uno más de corrección de seguridad. Correr una versión fuera de
esa ventana es una decisión — y tiene que estar escrita en algún lugar como
decisión, no como olvido.
:::

:::exercise level=2
La Casa Amarela corre PHP 5.6. Escribe, en cinco líneas, el argumento que le
presentarías a Seu Juvenal — que no es técnico y paga el hosting — para
justificar la actualización. Después escribe el mismo argumento para el Dr.
Aurélio, que es lo bastante técnico como para preguntar "¿y el riesgo?".

:::answer
**Para Seu Juvenal**, el argumento es riesgo y dinero, sin jerga:

> La versión que usa la biblioteca dejó de recibir correcciones de
> seguridad en 2018. Cualquier falla descubierta desde entonces sigue
> abierta en nuestro sistema, y el registro tiene nombre, documento y
> dirección de mil doscientas personas del barrio. La actualización entra en
> el presupuesto de la subvención; un incidente con datos de vecinos, no.

**Para el Dr. Aurélio**, el argumento es el riesgo del propio cambio,
porque eso es lo que va a preguntar:

> La actualización rompe el código que usa funciones eliminadas en PHP 7 —
> en nuestro caso, todo el acceso a la base de datos. Por eso no vamos a
> actualizar el sistema viejo: vamos a construir el nuevo ya en 8.3 y
> mantener el viejo en línea hasta el cambio. El riesgo queda aislado en lo
> que estamos escribiendo, y la fecha de apagar el viejo se vuelve una
> decisión, no un accidente.

Fíjate en lo que cambia entre los dos: no es el nivel de detalle técnico,
es **qué riesgo le toca evaluar a cada persona**. Una responde por el dinero
y por los vecinos; la otra, por la entrega. Mandarle el segundo texto a Seu
Juvenal sería hablar solo.
:::
