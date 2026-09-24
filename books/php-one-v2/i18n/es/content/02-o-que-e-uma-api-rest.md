---
source_hash: bcb494e6f209
title: "Qué es una API REST"
number: 2
slug: o-que-e-uma-api-rest
part: p1
kicker: "Don Juvenal quiere un botón que renueva todo. La pregunta difícil no es cómo hacerlo: es qué pasa cuando alguien lo aprieta dos veces."
goal: >-
  Diseñar las direcciones de una API a partir de los recursos, separar lo
  que es seguro de lo que es idempotente, elegir el status que ya responde
  la mitad de la pregunta, y saber qué puede y qué no puede cambiar después
  de que alguien empezó a consumirla.
---

:::story Renovar todo
—Una cosita —dijo don Juvenal—. Un botón que renueva todo de una vez. Doña
Marlene se lleva seis libros.

—Se puede —dijo Dedé.

—Perfecto.

—La pregunta es qué pasa cuando lo aprieta dos veces.

Don Juvenal pensó que era un chiste y esperó el resto.

—Hablando en serio: su teléfono es malo. Aprieta, la pantalla se queda
girando, aprieta otra vez. ¿Los seis libros se renuevan dos veces?

—¿Se renuevan veintiocho días?

—O el sistema rechaza la segunda y ella cree que no funcionó.

Tainá levantó los ojos del cuaderno.

—¿Y si cierra la aplicación en el medio?

—Ahí es mejor todavía: nadie sabe si se renovó.
:::

## La dirección nombra una cosa, no una acción

Una API se diseña listando **los sustantivos del dominio** y decidiendo
cuáles merecen una dirección propia. La Casa Amarela tiene cinco: libro,
ejemplar, lector, préstamo y reserva.

Cada sustantivo da dos direcciones:

| Dirección | Qué es |
|---|---|
| `/libros` | la colección entera |
| `/libros/12` | un ítem de ella |

Y cuando una cosa solo existe dentro de otra, se vuelve una dirección
anidada:

```text
/libros/12/ejemplares
```

Eso quiere decir "los ejemplares **de ese** libro", y es distinto de
`/ejemplares?libro_id=12`, que quiere decir "la colección de todos los
ejemplares, filtrada". Las dos formas funcionan; la primera dice que un
ejemplar no tiene sentido solo, y en el acervo de verdad no lo tiene.

:::pitfall
Un filtro no es un recurso. `/libros/infantiles` parece organizado y crea
un problema al día siguiente, cuando alguien quiere los infantiles de 2020
en adelante, o los infantiles prestados, o los infantiles de un autor.

Cada combinación se volvería una dirección nueva, y la lista crece como la
pizarra de clases del capítulo @cap:heranca-interfaces-e-traits. El filtro
vive en la consulta: `/libros?clasificacion=infantil&anio_minimo=2020`.

La regla: **si puedes imaginar la combinación con otro filtro, es un
filtro.**
:::

:::art caption="El botón que la persona aprieta dos veces es el único que importa."
src="o-botao-que-a-pessoa-aperta-duas-vezes-e-o-unico-que-importa.png"
Viñeta editorial minimalista sobre fondo blanco: una señora de setenta y
nueve años, de cárdigan y lentes, sostiene un celular antiguo muy cerca de
la cara y aprieta por segunda vez un botón grande que dice "RENOVAR TODO",
mientras un ícono de carga gira en la pantalla. Saliendo del celular, dos
flechas idénticas parten al mismo tiempo hacia una pila de seis libros, y
sobre la pila flotan dos calendarios, uno de "14 DÍAS" y otro de "28 DÍAS",
con un signo de interrogación entre ellos. Al lado, un señor entusiasmado
de gorra hace el gesto de aprobación, sin darse cuenta de nada. Pocos
elementos, humor seco, estética de revista de tecnología.
:::

## Seguro, idempotente, y ni lo uno ni lo otro

Aquí está la parte que casi nadie enseña y que decide el comportamiento de
tu API con una red mala.

:::term Seguro e idempotente
**Seguro** es el pedido que no cambia nada en el servidor. Se puede
repetir a voluntad, en cualquier orden, por cualquiera.

**Idempotente** es el pedido que se puede repetir sin cambiar el
resultado: hacerlo una vez y hacerlo cinco veces deja el sistema en el
mismo estado.

Todo pedido seguro es idempotente. Lo contrario no vale.
:::

| Verbo | Seguro | Idempotente |
|---|---|---|
| `GET` | sí | sí |
| `PUT` | no | sí |
| `DELETE` | no | sí |
| `POST` | no | **no** |
| `PATCH` | no | depende de lo que esté escrito |

Tabla: Esto no es una convención de estilo. Es lo que los navegadores, los
intermediarios de red y las bibliotecas de cliente suponen sobre tu API sin
preguntar.

`PUT /libros/12` es idempotente porque manda el libro entero: repetirlo
graba el mismo contenido. `DELETE /libros/12` es idempotente porque el
**estado** final es el mismo —el libro no existe—, aunque la segunda
llamada responda `404` en lugar de `204`.

`POST /prestamos` no es ninguna de las dos cosas, y ahí vive doña Marlene.

## El informe que corregía

El Sistema tiene una pantalla que ya conoces: el informe que, cuando
encuentra una línea rara, la arregla. Su dirección es esta:

```text
GET /informe.php?mes=02&accion=corregir
```

Un `GET` que modifica datos rompe una promesa que nadie escribió en el
código y de la que todos dependen:

- **el navegador puede pedirla antes de que hagas clic**, para que la
  página abra más rápido;
- **la red puede guardar la respuesta** y devolvérsela otra vez a otra
  persona;
- **el cliente puede repetirla solo** cuando se cae la conexión, porque
  repetir un `GET` es seguro por definición;
- **la dirección entera va al log**, con los parámetros, en cada máquina
  por la que pase.

El defecto clásico de esta familia es el sistema que perdió contenido
porque un robot de indexación siguió todos los enlaces de la pantalla de
administración, y los enlaces de borrar eran `GET`. Nadie había escrito
nada mal: todos habían escrito `<a href>`.

:::key
La pregunta que separa `GET` de todo lo demás no es "¿esto lee o escribe?".
Es: **¿algún intermediario puede repetir esto solo sin avisarme?**

Si la respuesta es sí, y repetirlo causa daño, el verbo está mal.
:::

## La repetición que no controlas

Vuelve al teléfono de doña Marlene, porque su problema no es que apriete
dos veces. Es peor.

```text
> POST /renovaciones
> (la conexión se cae antes de que llegue la respuesta)
```

La aplicación no sabe qué pasó. Puede que el pedido no haya llegado; puede
que haya llegado, se haya procesado y lo que se perdió sea la respuesta.
Las dos situaciones son idénticas vistas desde fuera.

Un cliente bien escrito vuelve a intentarlo. Y si tu API no está preparada,
el segundo intento crea la segunda renovación.

Hay dos salidas, y el orden importa.

**La primera es diseñar la operación para que sea idempotente.** "Renovar"
puede significar "sumar catorce días al plazo" —que se duplica cuando se
repite— o "fijar el plazo en catorce días a partir de hoy" —que da el
mismo resultado en las dos llamadas—. La segunda definición es la misma
regla de Vera, cuesta lo mismo y resuelve el problema sola.

**La segunda, cuando la operación no puede ser idempotente por
naturaleza**, es dejar que el cliente selle el intento:

```text
POST /prestamos
Idempotency-Key: 7f3a9c-intento-1
```

El servidor guarda la clave junto con la respuesta. Si vuelve la misma
clave, devuelve la respuesta guardada en lugar de crear de nuevo. Es el
mecanismo que usan las operadoras de pago, y por el mismo motivo: nadie
quiere cobrar dos veces porque el celular se trabó.

## Entonces qué es "renovar todo"

Ni `PUT /prestamos`, ni `GET`.

`PUT` sobre una colección significa "reemplaza la colección entera por lo
que estoy mandando", lo que, leído al pie de la letra, borraría todos los
préstamos que no estuvieran en el cuerpo. Nadie hace eso, y justamente por
eso el verbo no sirve: promete algo que no vas a cumplir.

La salida es recordar que **la renovación es una cosa**. Tiene fecha, tiene
autor, tiene cantidad, y Vera va a querer un informe de ella en algún
momento. Si es una cosa, tiene colección:

```text
POST /lectores/47/renovaciones
Content-Type: application/json

{"prestamos": [4471, 4472, 4473]}
```

```text
201 Created
Location: /lectores/47/renovaciones/91

{
  "id": 91,
  "renovados": [4471, 4472, 4473],
  "rechazados": []
}
```

Crear un recurso llamado renovación resuelve tres cosas de una vez: el
verbo queda honesto, la operación recibe un identificador que el cliente
puede consultar después de una conexión caída, y la respuesta puede decir
que dos libros se renovaron y uno no, lo que `PUT` no tendría cómo
expresar.

:::key
Cuando una acción no cabe en crear, leer, modificar o borrar, la pregunta
no es "¿qué verbo invento?". Es: **¿qué sustantivo está escondido aquí?**

Renovar esconde una renovación. Devolver esconde una devolución. Cancelar
esconde una cancelación. Casi siempre el sustantivo es algo que el negocio
ya cuenta, ya archiva y ya quiere en un informe.
:::

## El status ya responde la mitad

```text
201 Created
Location: /lectores/47/renovaciones/91
```

El `Location` en la respuesta de un `201` dice dónde fue a vivir la cosa
creada. Es lo que le permite al cliente consultarla después sin adivinar la
dirección, y es lo que hace recuperable la renovación perdida de doña
Marlene.

Dos elecciones de status suelen decidirse a ojo y merecen una regla:

**`409` contra `422`.** El `422` es sobre el **contenido del pedido**:
campo faltante, fecha con formato equivocado, cantidad negativa. El `409`
es sobre el **estado del sistema**: el pedido es impecable y la realidad no
lo permite: el ejemplar ya está prestado, el lector tiene una multa, la
reserva ya se canceló.

La diferencia es útil para quien consume: `422` le pide al usuario que
corrija lo que escribió; `409` le pide que mire la pantalla otra vez,
porque el mundo cambió.

**`200` con un error dentro.** No existe. Un cuerpo `{"exito": false}` con
status `200` obliga a todo cliente a abrir e interpretar cada respuesta
antes de saber si salió bien, y el primero que se olvide va a tratar un
error como éxito en silencio.

## El contrato con quien no controlas

El día en que la aplicación del lector esté publicada en la tienda, tu API
deja de ser tuya. Hay teléfonos por ahí con la versión vieja instalada, y
no se van a actualizar porque se lo pidas.

| Cambio | ¿Rompe? |
|---|---|
| agregar un campo en la respuesta | no |
| agregar un campo **opcional** en el pedido | no |
| agregar una dirección nueva | no |
| renombrar un campo | **sí** |
| quitar un campo | **sí** |
| cambiar el tipo de un campo | **sí** |
| volver obligatorio un campo que era opcional | **sí** |
| cambiar el status devuelto en un caso existente | **sí** |

Tabla: Lo que no rompe son todos agregados; lo que rompe son todos cambios
y eliminaciones. Es la regla entera, y cabe en una frase.

:::pitfall
El ítem más olvidado es el último. Cambiar un `200` por un `204` porque "de
todas formas no tenía cuerpo" parece orden y tumba a todo cliente que hacía
`if (status == 200)`.

Lo mismo vale para el formato de error. Si hoy el error sale como
`{"error": "texto"}` y mañana sale como `{"errores": [...]}`, no importa que
el segundo sea mejor: la aplicación publicada espera el primero.
:::

Cuando el cambio sea inevitable, el camino conocido es convivir con los dos
por un tiempo —dirección nueva en paralelo, o un número de versión en la
ruta— y apagar la vieja con fecha anunciada y medición de quién todavía la
usa.

## REST no es ley

REST es un estilo, no una especificación con inspector. Vale porque crea
una expectativa compartida: quien nunca vio tu API puede adivinar la mitad
de ella.

Donde no quepa, fuérzalo menos y documenta más. Una búsqueda con quince
filtros, una operación por lotes, un cálculo que no guarda nada: todas
existen, y ninguna mejora torcida hasta parecer un recurso.

El error grave no es salirse del estilo. Es salirse **en silencio**,
dejando que el cliente lo descubra probando.

## El diseño de la Casa Amarela

Escrito antes de la primera ruta, y eso es lo que lo vuelve un diseño:

| Verbo y dirección | Devuelve | Idempotente |
|---|---|---|
| `GET /libros` | `200` con la lista | sí |
| `GET /libros/12` | `200` o `404` | sí |
| `POST /libros` | `201` + `Location` | no |
| `PUT /libros/12` | `200` o `404` | sí |
| `DELETE /libros/12` | `204` o `404` | sí |
| `GET /libros/12/ejemplares` | `200` con la lista | sí |
| `POST /prestamos` | `201`, `409` o `422` | no |
| `POST /prestamos/7/devolucion` | `201` o `409` | no |
| `POST /lectores/47/renovaciones` | `201` o `409` | no |
| `GET /lectores/47/prestamos` | `200` con la lista | sí |

Tabla: Diez líneas cubren el sistema entero. Ninguna tiene un verbo en la
dirección, y las tres últimas operaciones de circulación son sustantivos
que Vera ya usa en el mostrador.

:::note En tu carrera
El diseño de la tabla de arriba lleva cuarenta minutos y ahorra semanas,
pero la razón no es técnica.

Una dirección escrita después del código carga las decisiones del código:
el nombre de la columna, el orden de los parámetros, lo que era fácil de
consultar ese día. Una dirección escrita antes carga las decisiones del
**negocio**, y por eso sobrevive al primer cambio de base de datos.

Cuando entres en un proyecto que ya tiene API, pide esa tabla. Si no
existe, armarla leyendo las rutas es la mejor primera semana que puedes
tener: nadie conoce el sistema tan rápido como quien escribió su índice.
:::

:::summary
- Un recurso es un sustantivo; la colección y el ítem son dos direcciones
  del mismo sustantivo.
- Anida cuando la cosa no existe sola; filtra en la consulta cuando la
  combinación es imaginable con otro filtro.
- Seguro es no cambiar nada; idempotente es poder repetir sin cambiar el
  resultado. `POST` no es ninguno de los dos.
- Un `GET` que modifica el estado rompe la suposición de quien repite solo,
  y alguien siempre repite solo.
- Una red que se cae después del pedido es indistinguible de un pedido no
  entregado: diseña la operación idempotente o acepta una clave de
  idempotencia.
- Una acción que no es CRUD esconde un sustantivo; crearlo resuelve el
  verbo, el identificador y el informe de una vez.
- `201` trae `Location`; `422` es contenido inválido; `409` es estado
  incompatible; `200` con un error dentro no existe.
- Agregar no rompe; renombrar, quitar, cambiar el tipo y cambiar el status
  rompen.
:::

:::checkpoint
Diseñas las direcciones de un dominio a partir de los sustantivos,
clasificas cada operación como segura, idempotente o ninguna de las dos,
eliges entre `409` y `422` con argumentos, y sabes decir qué cambios puedes
publicar sin avisarle a nadie.
:::

:::exercise level=1
Clasifica cada operación como segura, idempotente o ninguna de las dos:

1. `GET /libros/12`
2. `DELETE /reservas/88`
3. `POST /prestamos`
4. `PUT /lectores/47`
5. `POST /prestamos/7/renovacion`, definida como "el plazo pasa a ser hoy
   más catorce días"

:::answer
1. **Segura** (y por lo tanto idempotente).
2. **Idempotente**, no segura. La segunda llamada devuelve `404` y el
   estado sigue igual: la reserva no existe.
3. **Ninguna de las dos.** Cada llamada crea un préstamo nuevo.
4. **Idempotente**, no segura. Mandar el lector entero dos veces graba el
   mismo contenido.
5. **Idempotente**, no segura, y ese es el punto del enunciado. La
   operación es `POST`, que por defecto no es idempotente, pero la **regla
   elegida** la vuelve idempotente: fijar el plazo da el mismo resultado con
   cualquier número de repeticiones, mientras que sumar catorce días no lo
   daría.

El caso 5 muestra que la idempotencia no es una propiedad del verbo: es una
propiedad de la regla. El verbo solo dice qué puede suponer el cliente
cuando no conoce la regla.
:::

:::exercise level=2
Vera pide tres cosas nuevas. Diseña la dirección y el verbo de cada una, y
di el status de éxito y un status de rechazo posible.

1. Marcar un ejemplar como extraviado.
2. Listar los diez libros más prestados del mes.
3. Perdonar la multa de un préstamo.

:::answer
**1. Marcar como extraviado.**

```text
POST /ejemplares/2117/extravio      → 201, o 409
```

Es un acontecimiento con fecha y responsable, no la edición de un campo. El
`409` cubre el ejemplar que ya está marcado como extraviado.

La alternativa `PATCH /ejemplares/2117` con `{"condicion": "extraviado"}`
funciona y pierde dos cosas: la fecha del acontecimiento y la posibilidad
de rechazar transiciones inválidas con claridad.

**2. Los diez más prestados.**

```text
GET /libros?ordenar=prestamos&periodo=2026-02&limite=10   → 200
```

No es un recurso nuevo: es la colección de libros, ordenada y filtrada. Una
dirección `/libros/mas-prestados` sería la trampa del filtro que se vuelve
recurso: al mes siguiente alguien quiere los más prestados entre los
infantiles.

Sin status de rechazo obvio; un período mal formado devuelve `422`.

**3. Perdonar la multa.**

```text
POST /multas/312/perdon      → 201, o 409
```

El `409` es para la multa ya pagada: el pedido es correcto y el estado no
lo permite. El perdón es un acontecimiento que la rendición de cuentas de
la convocatoria va a querer listar aparte: un sustantivo más que el negocio
ya tenía y el código todavía no.
:::

:::exercise level=3
La API del acervo está publicada hace tres meses y tiene dos consumidores:
la aplicación del lector, en la tienda, y una planilla que la asociación
actualiza sola.

Llega el pedido: `GET /libros` hoy devuelve `anio` como número, y tiene que
pasar a devolver un objeto con `anio` y `edicion`.

Escribe el plan en cuatro pasos y di qué responderías a "¿no se puede
simplemente cambiar?".

:::answer
**Paso 1: agregar, no cambiar.** La respuesta pasa a traer `anio`
(inalterado) y un campo nuevo, `publicacion`, con el objeto. Nadie se
rompe, porque agregar un campo es el único cambio seguro.

**Paso 2: medir quién usa el campo viejo.** Registrar, por consumidor,
quién todavía lee `anio`. Sin ese número, el paso 4 se vuelve una discusión
de opiniones.

**Paso 3: anunciar con fecha.** Avisarles a los dos consumidores que `anio`
sale en una fecha específica, con al menos un ciclo de actualización de la
aplicación de margen. Marcar el campo como obsoleto en la documentación, no
solo en el correo.

**Paso 4: quitarlo después de que el número llegue a cero**, y no en la
fecha anunciada si no llegó a cero. La fecha es un compromiso con quien se
adaptó; el número es la realidad.

**"¿No se puede simplemente cambiar?"** Se puede, y el costo tiene
dirección: todo teléfono con la versión publicada hoy pasa a mostrar el año
en blanco, o a trabarse en la pantalla de detalle, según cómo la aplicación
maneje un campo que se volvió objeto. No se actualizan porque se lo
pidamos: se actualizan cuando la tienda empuja, y una parte de ellos nunca.

La planilla de la asociación es peor, porque nadie la mantiene: va a dejar
de funcionar un martes y Vera va a llamar el jueves.

El agregado cuesta un campo más en la respuesta durante algunos meses. El
cambio directo cuesta una ventana en la que el producto está roto para una
porción de usuarios que ni siquiera puedes contar.
:::
