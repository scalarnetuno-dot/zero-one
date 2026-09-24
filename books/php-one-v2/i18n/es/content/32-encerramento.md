---
source_hash: f52afc5d3a05
title: "Cierre"
slug: encerramento
matter: back
numbered: false
kicker: "El calendario de farmacia sigue en la pared de Vertexo, con veinticinco sábados tachados y uno encerrado en un círculo."
---

:::story El sábado del círculo
En junio, Vertexo se mudó de piso, y alguien tuvo que decidir qué hacer
con el calendario de farmacia de la sala de reuniones.

Estaba como lo había dejado Nonato en octubre: los sábados hasta el 31 de
marzo tachados uno por uno, con bolígrafo azul. Uno de ellos, de marzo,
estaba encerrado en un círculo rojo, con una anotación con la letra de
Márcia: *1.412*.

—El fin de semana que sale mal —dijo Tainá.

—Siempre hay uno —dijo Márcia.

Nonato descolgó el calendario, lo enrolló y se lo puso bajo el brazo,
junto con el papel doblado de la contraseña del FTP, que había pedido
guardar y que nadie se había animado a negarle.

—Veinticinco fines de semana —dijo—. Dije que era uno por punto.

—Dijiste que eran veintiséis puntos —dijo Dedé.

—Y lo fueron. El vigésimo sexto fue Laravel. —Se acomodó el calendario
bajo el brazo—. Se llevó los otros veinticinco.

Dedé tardó un poco en entender que eso era un elogio.
:::

:::story Cinco estrellas
La aplicación de Kauã entró en la tienda en mayo, con el logotipo de la
Casa Amarela por fin en la proporción correcta. Tenía cuarenta y dos
reseñas, promedio 4,6. La más corta era de doña Marlene:

*"Ahora el e-mail viene firmado por la biblioteca. Cinco estrellas."*

La más larga era de don Juvenal, y terminaba con una sugerencia de
funcionalidad.

Un sábado de junio, Vera llegó a las ocho y cuarenta, como todos los días
de los últimos treinta y un años. Abrió el panel y revisó el resumen del
día: cuatro devoluciones en el buzón, ningún atrasado nuevo, dos reservas
esperando, y las trescientas portadas que había fotografiado, todas
paradas.

Tainá llegó a las nueve, con el cuaderno. Estaba en la última página.

—¿Se terminó? —preguntó Vera.

—¿El cuaderno? Se terminó. Compré otro.

—¿Y qué dice la última línea?

Tainá leyó:

—"Preguntarle a quien hace el trabajo antes de escribir el código."

Vera lo pensó un poco.

—Eso debería estar en la primera.

La puerta se abrió. Don Juvenal entró con una bolsa de plantines de
lechuga.

—Buen día, buen día. Los chicos de la huerta vieron la aplicación y se
entusiasmaron. Quieren una cosita. Para controlar los canteros, quién
planta qué, quién riega qué día. —Puso la bolsa en el mostrador—. ¿Cuánto
se tarda en hacer un sistemita de esos?

Tainá abrió el cuaderno nuevo en la primera página.

—¿Cuántos canteros son?
:::

:::art caption="Todo sistema termina con alguien pidiendo una cosita."
src="todo-sistema-termina-com-alguem-pedindo-uma-coisinha.png"
Ilustração editorial minimalista em fundo branco, tom leve de despedida:
o balcão de uma pequena biblioteca de bairro numa manhã de sábado. Atrás
dele, uma bibliotecária mais velha, de óculos, confere um monitor onde
aparecem miniaturas de capas de livro, todas em pé. Uma estagiária abre um
caderno novo na primeira página, caneta na mão. Do outro lado, um senhor
de boné acaba de pôr no balcão uma sacola de mudas de alface, com as mãos
abertas no gesto de quem vai pedir "só uma coisinha". Poucos elementos,
humor sutil, estética de revista de tecnologia.
:::

## El camino de los dos volúmenes

Dos libros, sesenta capítulos, una biblioteca de barrio. Mirando hacia
atrás, cada cosa que Laravel hace por ti tiene un lugar donde primero la
hiciste a mano:

| El problema | A mano, en el volumen 1 | En el framework, en este volumen |
|---|---|---|
| guardar datos | SQL, PDO, transacción | migrations, Eloquent |
| organizar el código | Composer, namespaces | `app/`, autoload, service providers |
| armar objetos | el `Servicios` de closures | el contenedor que lee el constructor |
| configurar | `.env` y `config/` | `.env` y `config/`, con caché |
| decir que algo salió mal | excepciones de dominio | handler, `422`, `409`, formato único |
| el tiempo | `Reloj` inyectado | `now()` congelado en las pruebas |
| archivo grande | generador, `fgetcsv` | `LazyCollection`, lote en la cola |
| archivo subido | `rename` al final | `Storage`, disco privado y público |
| avisar | `Bitacora` con contexto | `Log`, notificaciones por canal |
| trabajo lento | el script de la madrugada | colas, workers, lotes, ritmo |

Tabla: La misma lista, de los dos lados. El framework no trajo ideas
nuevas a este proyecto; trajo las mismas ideas, listas, probadas por más
gente.

Por eso existe el volumen 1. Quien solo conoce la columna de la derecha
usa Laravel. Quien conoce las dos puede decir por qué hace lo que hace, y
qué hacer el día en que no lo haga.

## Lo que este libro no cubre, y dónde buscarlo

Algunas herramientas quedaron afuera a propósito. Cada una resuelve un
problema real, y ninguna es necesaria para una API como la de la Casa
Amarela.

**Livewire** e **Inertia** construyen interfaces interactivas sin separar
front-end y back-end; la documentación oficial de cada uno es el punto de
partida.

**Vue** y **React** son el camino cuando el panel de Vera se vuelva una
aplicación de verdad en el navegador; la API de este libro es exactamente
lo que consumen.

**Octane** mantiene la aplicación cargada en memoria entre peticiones, y
vuelve el `singleton` del capítulo @cap:service-container —y las variables
`static` del capítulo @cap:escopo-e-referencias— todavía más peligrosos;
la documentación de Laravel tiene una sección entera sobre lo que cambia.

**Horizon** y **Redis** son el siguiente paso de la cola del capítulo
@cap:queues-na-pratica, el día en que la tabla `jobs` deje de bastar.

**Multitenancy** —varias bibliotecas en el mismo sistema, con los datos
separados— es un problema de diseño antes que de paquete; empieza por los
artículos sobre base compartida × base por cliente. La segunda biblioteca,
la del barrio de al lado, va a hacer esa pregunta.

**GraphQL** es una alternativa a REST para clientes que necesitan armar
sus propias consultas; el paquete Lighthouse es la referencia en Laravel.

**Microservicios** y **Kubernetes** resuelven problemas de organizaciones
con decenas de equipos; para una biblioteca con tres conceptos y una
computadora, la respuesta es la del cuaderno de Tainá.

## Una última cosa

El Sistema de 2009 estuvo quince años en línea sin perder un acervo. Lo
escribió en un fin de semana alguien de veintitrés años, con las
herramientas que había. El sistema nuevo va a seguir en línea mientras
alguien sepa tocarlo, y ese alguien, a partir de ahora, puedes ser tú.

Cuando llegue tu don Juvenal, con la bolsa de plantines y la cosita que
lleva un fin de semana, empieza por la pregunta de Tainá. ¿Cuántos
canteros son? ¿Quién riega? ¿Qué pasa cuando dos chicos riegan el mismo
cantero el mismo día?

El código viene después. Siempre vino después.

:::milestone
Fin de PHP One. La Casa Amarela tiene una API en producción, una
aplicación en la tienda, portadas paradas, e-mails firmados por la
biblioteca y una cola que manda el aviso de las nueve a las nueve. Tiene
también una carpeta con el Sistema de 2009, en dos copias, que nadie
borró.

Y, en el mostrador, un cuaderno nuevo, con una pregunta en la primera
página.
:::
