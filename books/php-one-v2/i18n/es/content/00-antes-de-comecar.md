---
source_hash: 876fb3fad0f7
title: "Antes de empezar"
slug: antes-de-comecar
matter: front
numbered: false
kicker: "Veinticinco fines de semana hasta el 31 de marzo. Nonato los contó en el calendario de la pared, y la cuenta no cerró por uno."
---

El volumen 1 terminó un viernes, con la carpeta ordenada y una pregunta en
el cuaderno de Tainá. Este empieza el lunes.

## Lunes, nueve y diez

La primera tarea de la semana no tuvo nada de web. Dedé cambió la
contraseña de la base —la que había pasado por once archivos y por el
historial de Git— y pegó la nueva en el `.env`, que no va a ninguna parte.

—¿Cuál era la vieja? —preguntó Tainá.

—`contrasena`.

—¿Y la nueva?

—No es `contrasena`.

Nonato, desde la mesa de al lado, levantó la mano sin quitar los ojos de la
pantalla.

—Protesto. En 2009 la contraseña era `casaamarela2009`. Alguien la cambió a
`contrasena` después de mí.

A las nueve y cuarenta, don Juvenal entró en la sala de reuniones de
Vertexo con un paquete de pan de queso y un anuncio.

—Mi nieto, Kauã, hizo una aplicación. En un fin de semana. Para la
biblioteca. —Giró el celular hacia la mesa: una pantalla azul, el logotipo
de la Casa Amarela estirado a lo ancho y un botón *Renovar*—. Solo falta
conectarla al sistema.

—¿Conectarla cómo? —preguntó Márcia.

—Eso se lo dejo a ustedes. Él dijo que es solo una API.

Tainá abrió el cuaderno en la última página escrita. Debajo de *¿qué llega
del navegador hasta PHP?* apareció una segunda línea: *¿y de la aplicación
de Kauã?*

## El fin de semana de Nonato

La discusión empezó como empieza una discusión técnica en Vertexo: con
alguien diciendo que no hacía falta discutir.

—Lo hacemos en PHP puro —dijo Nonato—. Ustedes acaban de pasar un libro
entero aprendiendo PHP. Yo hice el Sistema en un fin de semana, y está en
producción hace quince años.

—Con `mysql_query` y contraseñas en MD5 —dijo Dedé.

—Con `mysql_query` y contraseñas en MD5, y ningún acervo perdido.

Dedé fue hasta la pizarra.

—Está bien. ¿Qué tiene que hacer la aplicación de Kauã?

—Ver los libros. Prestar. Renovar. Devolver.

Dedé escribió cuatro palabras —**libros, ejemplares, lectores,
préstamos**— y, al lado de cada una, las mismas cuatro letras.

—CRUD —dijo Tainá—. *Create, read, update, delete.*

—Cuatro tablas, cuatro operaciones. Dieciséis endpoints. Es la parte
fácil. —Hizo una raya debajo—. Ahora el resto.

Y escribió, una por línea: *rutas. leer JSON. responder JSON. validar cada
campo. contraseña del lector. token de la aplicación. quién puede qué.
errores en un solo formato. paginación. búsqueda. correo de aviso. cola,
para que el correo no trabe la pantalla. caché. log. migración de la base.
pruebas. documentación para Kauã. deploy.*

—Cada una de esas —dijo Nonato— es un fin de semana.

—Entonces cuenta.

Nonato contó las líneas en voz alta, sumando las que Dedé iba recordando
en el camino. Dieron veintiséis. Después se levantó, fue hasta el
calendario de la pared —un calendario de farmacia, con los meses en fila—
y contó los sábados hasta el 31 de marzo, con el dedo.

—Veinticinco.

—Falta uno —dijo Tainá.

—Falta el fin de semana en que sale mal —dijo Márcia—. Siempre está ese.

Nonato se sentó otra vez, despacio.

—En 2009 no había aplicaciones.

## El término medio que nadie pidió

—Laravel —dijo Dedé—. Todo lo que está en la pizarra viene listo, y probado
por más gente de la que vamos a conocer en la vida.

—Y entonces nadie aquí sabe qué corre por debajo —respondió Nonato—. Se
vuelve magia. Y la magia se rompe el viernes a la noche.

Fue Tainá quien desempató, sin darse cuenta de que estaba desempatando.

—¿Y si lo hacemos a mano primero? Pequeño. Solo para ver qué hace. Después
usamos el de verdad.

Dedé miró la pizarra. Nonato miró el calendario.

—¿Cuánto es pequeño? —preguntó Nonato.

—Cuarenta líneas.

—Cuarenta líneas las leo.

Vera, que había venido solo a entregar la lista de las once reglas y se
había quedado por el pan de queso, tomó la cartera.

—Háganlo como quieran. El lunes a las nueve yo abro. Con o sin
aplicación.

El plan quedó en la pizarra hasta el final del proyecto, con la letra de
Dedé y una flecha de Tainá al lado:

```text
1. entender lo que manda el navegador (y Kauã)   -> HTTP
2. diseñar la conversación antes del código      -> REST
3. escribir un framework pequeño, a mano         -> 40 líneas
4. usar el de verdad, sabiendo lo que hace       -> Laravel
```

Es el orden de este volumen.

## Lo que traes del volumen 1

Todo lo que Laravel va a suponer que sabes: tipos, arrays, funciones,
closures, SQL escrito a mano, PDO, Composer, clases, interfaces,
excepciones, tipado estricto, enums, fechas con zona horaria y errores que
avisan. Y un proyecto organizado como lo va a organizar el framework:

:::tree title="Lo que el volumen 1 dejó listo"
acervo/
  bin/                 importar-donaciones.php, atrasados.php
  config/app.php       zona, plazo, base, leídos del .env
  public/              vacía: es la puerta de la web, y la web empieza aquí
  src/
    Acervo/            Libro, Ejemplar, EstadoEjemplar
    Prestamos/         Dinero, PlazoDePrestamo, EstadoPrestamo
    Circulacion/       excepciones de dominio, CalendarioDeLaBiblioteca
    Importacion/       Csv, Importador
    Tiempo/            Reloj, RelojDelSistema, RelojDetenido
    Bitacora.php       log con contexto
    Servicios.php      contenedor de fábricas, escrito a mano
  var/log/
  bootstrap.php        config, errores que se vuelven excepción, servicios
  .env, .env.example
  composer.json        psr-4 CasaAmarela\, phpstan nivel 5
:::

Y la base `casa_amarela`, con `libros`, `ejemplares`, `lectores` y
`prestamos`, escrita en SQL puro. Cada pieza de Laravel se va a comparar
con algo de este árbol, y, en algunas comparaciones, el árbol gana.

Si llegaste directo a este volumen: la **Biblioteca Comunitaria Casa
Amarela** tiene cuatro mil títulos y un sistema en PHP de 2009, el
**Sistema**, que atiende el mostrador mientras **Vertexo Sistemas**
construye el reemplazo. El dinero viene de una convocatoria cultural, con
rendición de cuentas el **31 de marzo**: si se atrasa, el dinero se
devuelve. **Dedé** explica, **Tainá** pregunta y anota, **Vera** sabe las
reglas, **Márcia** cuida el plazo, **Nonato** escribió el Sistema,
**Cléber** responde "lo procesa" y **don Juvenal** trae el próximo pedido.

## Cómo está organizado este volumen

Los capítulos tienen numeración propia, a partir del 1. Cuando el texto
cite un capítulo del primer libro, la cita lo dice: "el capítulo 21 del
volumen 1". Sin esa indicación, el capítulo es de este volumen.

| Parte | Capítulos | Qué pasa |
|---|---|---|
| 1 · La web debajo del framework | 1–4 | HTTP, REST, cuarenta líneas y la elección del framework |
| 2 · Dentro de Laravel | 5–9 | proyecto, configuración, rutas, requests, Blade |
| 3 · Eloquent sobre el SQL | 10–12 | migrations, Eloquent, relaciones |
| 4 · La API de verdad | 13–17 | CRUD, validación, resources, paginación, errores |
| 5 · Arquitectura y seguridad | 18–22 | contenedor, services, middleware, Sanctum, Policies |
| 6 · Después de la respuesta | 23–24 | colas, caché, logs y medición |
| 7 · Probar y publicar | 25–28 | pruebas, documentación, Git, CI y deploy |
| 8 · El sistema en producción | 29–31 | subida, correo y notificaciones, colas en producción |

Tabla: Ocho partes, en el orden en que aparece el problema. El framework
recién entra en el capítulo 4, después de que escribiste a mano lo que
hace; la última parte empieza el día después del deploy.

:::practice
Ten PHP 8.3 y Composer instalados, comprobados con `php -v` y
`composer -V`. Si llegaste aquí por el volumen 1, ya tienes los dos. Si no,
los capítulos 2 y 16 del volumen 1 hacen esa instalación paso a paso.
:::

Faltan veinticinco fines de semana. El lunes a las nueve, Vera abre.
