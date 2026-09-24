---
source_hash: 432000fd71a5
title: "Git, CI y el día del deploy"
number: 28
slug: git-ci-e-deploy
part: p7
kicker: "El 31 de marzo, a las siete de la mañana, el papel doblado con la contraseña del FTP salió de la carpeta del proyecto por última vez."
goal: >-
  Salir del "funciona en mi máquina": un historial que se pueda leer, una
  cadena que rechaza lo que no pasa, un deploy en orden con migration, caché
  y worker en su lugar, una verificación de salud honesta y, al final, un
  requisito nuevo implementado de punta a punta, por tu cuenta.
---

## `.gitignore` antes del primer `git add`

El proyecto `casa-amarela/` está en un repositorio desde el capítulo
@cap:primeiro-projeto-laravel, y Laravel ya vino con un `.gitignore`.
Merece leerse una vez, línea por línea, porque cada línea es un incidente
que alguien ya tuvo:

```text title=".gitignore"
/vendor
/node_modules
/public/build
/public/storage
/storage/*.key
.env
.env.backup
.env.production
.phpunit.result.cache
```

**`/vendor`** lo recrea `composer install` a partir del `composer.lock`: la
lección del capítulo @cap:do-include-ao-composer.

**`.env`** tiene la contraseña de la base, la clave de la aplicación, el
token del proveedor de mensajes. Es el archivo más importante de la lista.

**`.env.backup`** y **`.env.production`** existen porque alguien, en algún
proyecto, hizo una copia del `.env` con otro nombre "solo para guardarla",
y la copia fue a parar al repositorio.

Lo que **entra** en el repositorio es el `.env.example`, con todas las
claves y ningún valor de verdad. Es la documentación de qué variables
necesita la aplicación, y es lo que la persona nueva copia el primer día.

## Un secreto en el historial se resuelve cambiando el secreto

La regla existe y, en algún momento, alguien la va a romper. El `.env` va a
entrar en un commit, por un `git add .` hecho con prisa, antes de que el
`.gitignore` esté bien.

La reacción instintiva es borrar el archivo y hacer otro commit. No
resuelve nada: Git guarda **todo el historial**, y el `.env` sigue en el
commit anterior, legible para cualquier persona con acceso al repositorio,
y para cualquier copia que ya se haya hecho.

Hay herramientas para reescribir el historial y borrar el archivo de todos
los commits. Son útiles y **no son la solución**, porque no alcanzan los
clones que ya existen, los *forks*, la caché del servicio de hospedaje, la
máquina de la persona que bajó el repositorio ayer.

:::key
Un secreto que entró en el historial está filtrado. La única corrección es
**cambiar el secreto**: generar una contraseña nueva para la base, una
clave nueva para el proveedor, revocar el token.

Reescribir el historial es limpieza. Cambiar el secreto es la corrección.
En el orden correcto: primero se cambia, después se limpia.
:::

Es la misma respuesta del capítulo @cap:middleware para las contraseñas
que fueron al log, y del capítulo @cap:autenticacao para las contraseñas
del Sistema. Se repite porque el principio es uno solo: un secreto que otra
persona puede haber visto dejó de ser secreto.

## Un commit que cuenta una historia

El historial de un proyecto se lee muchas más veces de las que se escribe,
y casi siempre lo lee alguien buscando **por qué** una línea es como es.

```text
$ git log --oneline
a3f9c21 ajustes
7be4d02 wip
c01e8f5 corrige
9d2a6b7 más ajustes
e44f1a0 ahora sí
```

Cinco commits, ninguna información. Compara:

```text
$ git log --oneline
a3f9c21 La devolución por el buzón usa PlazoDePrestamo
7be4d02 Prueba reproduce multa en devolución adelantada
c01e8f5 El listado de préstamos desempata por id
9d2a6b7 El último ejemplar exige autorización, no rechaza
e44f1a0 Límite de 5 préstamos en enero
```

Cada línea dice qué cambió, en imperativo o como hecho, en menos de
setenta caracteres. Quien busque por qué cambió la devolución del buzón en
febrero lo encuentra en segundos, y el commit de justo abajo muestra que la
prueba vino antes de la corrección, como pidió el capítulo @cap:testes.

Para los cambios que necesitan explicación, el cuerpo del commit, después
de una línea en blanco, cuenta el porqué:

```text
El último ejemplar exige autorización, no rechaza

La regla se anotó como "solo c/ autoriz." y se implementó
como rechazo. Corregida con Vera el 18/02. La Autorizacion
registra quién autorizó y el motivo, y cubre también los
casos que antes se resolvían de memoria en el mostrador.
```

:::note
Las ramas y la revisión entran aquí en una frase, porque son asunto del
equipo más que del código: cada cambio nace en una rama, se vuelve un
*pull request*, y alguien lo lee antes de que entre en la rama principal.
La rama principal siempre se puede publicar. La revisión no es para
encontrar errores de tipeo —eso lo hace la cadena— sino para preguntar
"¿por qué así?", que solo lo pregunta una persona.
:::

## La cadena: Pint, PHPStan, pruebas

La cadena de integración continua es un conjunto de verificaciones que
corre sola en cada *push*, en una máquina limpia, y dice si el código puede
entrar. Para la Casa Amarela, cuatro:

```yaml title=".github/workflows/cadena.yml" numbered
name: cadena

on: [push, pull_request]

jobs:
  verificar:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_DATABASE: casa_amarela_prueba
          MYSQL_ROOT_PASSWORD: prueba
        ports: ['3306:3306']
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=5s --health-retries=10

    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.3'
          coverage: none

      - run: composer install --no-interaction --prefer-dist

      - name: Estilo
        run: vendor/bin/pint --test

      - name: Análisis estático
        run: vendor/bin/phpstan analyse --no-progress

      - name: Ningún dd() olvidado
        run: "! grep -rnE '\\b(dd|dump|var_dump)\\(' app/"

      - name: Pruebas
        run: php artisan test --parallel
        env:
          DB_HOST: 127.0.0.1
          DB_PASSWORD: prueba
```

**Pint** verifica el estilo del código: espaciado, orden de los `use`,
llaves. Con `--test`, solo señala, sin cambiar nada. La discusión sobre
estilo sale de la revisión de código y va a una herramienta, donde no
ofende a nadie.

**PHPStan**, en el nivel 5 del capítulo @cap:tipagem-estrita, lee el código
sin correrlo y señala lo que no cierra: un método que no existe, un tipo
que no coincide, un `null` donde no puede haberlo. Para proyectos Laravel,
la extensión Larastan le enseña a PHPStan a entender los models y las
*facades*.

**La búsqueda de `dd(`** es la regla del capítulo
@cap:cache-logs-e-medicao, en una línea.

**Las pruebas** corren en el **mismo MySQL** de producción —el servicio
declarado arriba—, por el motivo del capítulo
@cap:testes-de-feature-http-e-banco.

La cadena en rojo bloquea el *merge*. No es una recomendación: es
configuración del repositorio. La rama principal solo recibe lo que pasó.

## La migration en producción es un paso aparte

El deploy de una aplicación Laravel tiene un orden, y el orden existe
porque cada paso depende del anterior:

```bash title="deploy.sh" numbered
#!/usr/bin/env bash
set -euo pipefail

cd /var/www/casa-amarela

git fetch --tags
git checkout "$1"

composer install --no-dev --optimize-autoloader

php artisan down --retry=15

php artisan migrate --force

php artisan config:cache
php artisan route:cache
php artisan view:cache

php artisan queue:restart

php artisan up
```

El `set -euo pipefail` hace que el script **se detenga en el primer
error**. Sin él, una migration que falla va seguida de `config:cache` y
`up`, y la aplicación vuelve a estar en línea con la base a medias.

El `$1` es la versión: un *tag* de Git, como `v1.0.0`. El deploy publica
una versión con nombre, no "lo que haya en la rama principal ahora".
Volver atrás es correr el mismo script con el *tag* anterior.

El `--no-dev` no instala Telescope, Pest ni Debugbar. El
`--optimize-autoloader` genera el mapa de clases del capítulo
@cap:namespaces-e-autoload, que el autoload de producción usa en vez de
buscar el archivo en cada clase.

La migration es un paso **aparte y único**: corre una vez, en un solo
lugar. Cuando la aplicación crece y pasa a correr en cinco servidores, la
tentación es poner el `migrate` al arranque de cada uno, y las cinco
máquinas intentan cambiar la misma tabla al mismo tiempo. El `--isolated`
de `migrate` bloquea la ejecución para que corra solo una, y la regla sigue
valiendo: migrar es un paso del deploy, no del arranque de cada máquina.

:::pitfall
El `--force` existe porque Laravel, en producción, **pregunta antes de
migrar**, y un script no responde preguntas. Es necesario en el script y es
peligroso fuera de él: escrito a mano, en la terminal equivocada, con el
`.env` equivocado, es el `migrate:fresh` del jueves del capítulo
@cap:migrations-seeders-e-factories con otro nombre.

El deploy es un script, versionado, revisado. Nadie corre una migration de
producción tecleándola.
:::

## `down`, la caché y el worker que hay que reiniciar

`artisan down` pone la aplicación en mantenimiento: toda petición recibe un
`503` con el encabezado `Retry-After`, y la aplicación del lector muestra
"en mantenimiento, vuelve en unos minutos". Existe para que nadie haga un
préstamo **durante** la migration, con la mitad de las columnas en el
formato viejo.

Las tres `cache` van **después** de la migration y del código nuevo,
porque congelan lo que exista en ese momento; el capítulo
@cap:cache-logs-e-medicao explicó lo que pasa cuando corren antes. Y van
**antes** del `up`, para que la primera petición ya encuentre todo listo.

El `queue:restart` es el paso que más se olvida y el que el capítulo
@cap:events-jobs-e-filas pidió no olvidar: sin él, el worker sigue con el
código de ayer en memoria, y los avisos salen con el texto viejo, o se
rompen, buscando la columna que la migration de hoy renombró.

:::note
El deploy **sin** sacar la aplicación de línea existe, y tiene nombre:
*zero downtime*. La técnica más común es preparar la versión nueva en una
carpeta al lado, con todo listo, y cambiar un enlace de una a otra en un
instante.

Lo que exige es que **las dos versiones funcionen con la misma base** al
mismo tiempo, lo que obliga a las migrations a seguir la expansión y
contracción del capítulo @cap:migrations-seeders-e-factories: agregar
antes, quitar en un deploy siguiente. Es más trabajo en cada migration.
Para una biblioteca que abre a las nueve, un minuto de mantenimiento a las
siete de la mañana es la elección honesta.
:::

## Health check: vivo no es lo mismo que listo

El capítulo @cap:primeiro-projeto-laravel presentó la `/up`, que Laravel
trae lista. Responde `200` si la aplicación puede atender una petición. Es
una pregunta útil —**¿el proceso está vivo?**— y no es la única.

La aplicación puede estar viva y sin base. Viva y con el disco lleno. Viva
y con la cola detenida hace seis horas. La `/up` responde `200` en los tres
casos.

```php title="app/Http/Controllers/ListoController.php" numbered
public function __invoke(): JsonResponse
{
    $chequeos = [
        'base' => $this->intenta(fn () => DB::select('SELECT 1')),
        'cache' => $this->intenta(fn () => Cache::put('listo', 1, 5)),
        'cola' => $this->intenta(fn () => $this->colaAndando()),
        'disco' => $this->intenta(fn () => $this->discoConHolgura()),
    ];

    $ok = !in_array(false, $chequeos, true);

    return response()->json(
        ['listo' => $ok, 'chequeos' => $chequeos],
        $ok ? 200 : 503,
    );
}

private function colaAndando(): bool
{
    $masViejo = DB::table('jobs')->min('created_at');

    return $masViejo === null
        || now()->diffInMinutes($masViejo) < 15;
}
```

| Ruta | Pregunta | Quién la consulta |
|---|---|---|
| `/up` | ¿el proceso responde? | el balanceador, cada pocos segundos |
| `/listo` | ¿puede hacer el trabajo? | el monitoreo, cada minuto |

Tabla: La primera debe ser barata y no depender de nada. La segunda puede
consultar la base, y por eso no se llama cada dos segundos.

La `/listo` no le dice **qué** se rompió a quien no debe saberlo: queda
detrás de un token del monitoreo, o responde solo `200` y `503` al mundo y
el detalle a quien se autentica. La lección del capítulo
@cap:erros-padronizados vale para ella también.

## La lista antes de publicar

Una lista corta, revisada la víspera, por una persona con la lista en la
mano, y no de memoria:

- `APP_ENV=production` y `APP_DEBUG=false`.
- `APP_KEY` generada **en el servidor**, distinta de la de desarrollo.
- HTTPS con certificado válido, y HTTP redirigiendo a HTTPS.
- `.env` del servidor fuera del repositorio, legible solo por el usuario
  de la aplicación.
- Permisos de `storage/` y `bootstrap/cache/` como en el capítulo
  @cap:primeiro-projeto-laravel.
- Worker bajo supervisor, reiniciándose en el deploy.
- Programador en el `cron`: `* * * * * php artisan schedule:run`.
- Log en JSON, con rotación, y ningún campo sensible, verificado con una
  búsqueda.
- `/listo` consultada por el monitoreo, con alerta para alguien.
- Backup diario de la base **y una restauración probada**.

El último punto es el único que merece explicación, porque es el que más
se salta. Un backup que nunca se restauró es una hipótesis. El archivo
puede estar corrupto, incompleto, cifrado con una clave que nadie tiene, o
ser el backup de otra base. La única forma de saberlo es restaurarlo en una
máquina aparte y abrir el acervo.

Nonato hizo un `UPDATE` sin `WHERE` un viernes de 2013, en el capítulo
@cap:sql-do-zero, y por eso existe el backup diario desde entonces. Lo que
nadie había hecho, en trece años, era restaurar uno.

:::warning
Docker entra en esta lista solo donde aporta. Para la Casa Amarela —una
aplicación, una base, un worker, un servidor—, un servidor con PHP, MySQL y
supervisor instalados es más simple de entender, de mantener y de arreglar
a las siete de la mañana. Docker tiene sentido cuando hay muchas
aplicaciones en la misma máquina, entornos difíciles de reproducir, o un
equipo que ya lo opera todo así. Adoptarlo "porque es profesional" es el
error del capítulo @cap:primeiro-projeto-laravel, con más piezas.
:::

:::story El papel doblado
A las siete de la mañana del 31, Márcia sacó de la carpeta del proyecto el
papel doblado que don Juvenal le había entregado en octubre. Usuario,
contraseña, y en una esquina, con tinta de otro color: *"no tocar la
carpeta vieja"*.

Servía para lo último que quedaba por hacer en el hospedaje viejo: sacar
una copia final del Sistema y cambiar la página de inicio por un aviso con
la dirección nueva.

Nonato tomó el papel, lo leyó, y se quedó quieto un rato.

—Esta letra es mía. Lo escribí en 2011. La carpeta vieja era la versión de
2009, que dejé ahí por si la nueva daba problemas. Nunca me animé a
borrarla.

Dedé corrió el script de deploy. `down`, `migrate`, tres `cache`,
`queue:restart`, `up`. Cuatro minutos. La `/listo` respondió `200` con
cuatro `true`.

El celular de Dedé vibró. Rejane: *"¡¡¡Felicitaciones por el ownership en
este go-live!!! Tu promoción quedó aprobada para el ciclo de abril."* Lo
leyó dos veces y guardó el celular sin responder.

Nonato bajó por FTP las dos carpetas, comparó el tamaño de los archivos dos
veces y cambió el `index.php` por una página con una frase y una
dirección.

—Listo. Quince años.

—Medio millón de préstamos —dijo Tainá—. Los conté. Ningún acervo perdido.

Nonato volvió a doblar el papel, por los mismos dobleces.

—¿Me lo puedo quedar?

—La contraseña todavía funciona —dijo Márcia.

—Entonces cambien la contraseña —dijo Dedé—. Después se lo queda.
:::

:::art caption="Quince años, medio millón de préstamos y un papel doblado."
src="quinze-anos-meio-milhao-de-emprestimos-e-um-papel-dobrado.png"
Ilustração editorial minimalista em fundo branco, tom mais contido: um
dev de uns quarenta anos, de camisa xadrez, segura com cuidado um papel
dobrado em quatro, com uma anotação à mão num canto em caneta de outra
cor. Atrás dele, um monitor de tubo antigo mostra uma tela cinza com
formulário, e ao lado um monitor novo mostra uma tela limpa com um visto
verde. Em volta, de pé, uma gerente com uma pasta, um desenvolvedor mais
novo que guarda o celular no bolso sem olhar, e uma estagiária de caderno
aberto, todos olhando para o papel. Poucos elementos, humor sutil e
afetuoso, estética de revista de tecnologia.
:::

## El primer pedido después de salir al aire

El sistema está en línea. Y, como todo sistema en línea, recibe el primer
pedido nuevo esa misma semana: el primero de una fila que la Parte 8
empieza a atender.

Vera quiere poder **perdonar una multa**. Hay casos —una inundación, una
enfermedad, un libro devuelto mojado por la lluvia de diciembre— en que
ella decide que la persona no debe pagar. Hoy lo anota en el cuaderno y no
lo cobra, y el informe de fin de mes muestra una deuda que no existe.

Este pedido es tuyo. Atraviesa casi todo lo que construyó este libro, y el
guion de abajo dice **dónde** vive cada parte, no **cómo** escribirla:

| Capa | Qué decidir | Capítulo |
|---|---|---|
| ruta | `POST /multas/{multa}/perdon`, y por qué no `DELETE` | @cap:o-que-e-uma-api-rest |
| Form Request | el `motivo` es obligatorio, con largo mínimo | @cap:validation-e-form-requests |
| policy | quién puede perdonar, y si el encargado puede | @cap:autorizacao |
| service | una multa ya pagada o ya perdonada no se perdona | @cap:services |
| excepción | el `tipo` del `409` | @cap:erros-padronizados |
| evento | `MultaPerdonada`, después del commit | @cap:events-jobs-e-filas |
| cola | avisar al lector, una sola vez | @cap:events-jobs-e-filas |
| resource | ¿la multa muestra que fue perdonada, y por quién? | @cap:api-resources |
| pruebas | la regla en la unitaria, el `403` en la feature | @cap:testes |
| documentación | el `tipo` nuevo en la tabla de errores | @cap:documentacao-da-api |

Tabla: Diez decisiones, y ninguna es de tecleo. El código de cada capa
tiene entre cinco y treinta líneas.

Dos preguntas no tienen respuesta técnica, y hay que hacérselas a Vera
antes de la primera línea. **¿El lector debe ver el motivo del perdón?**
"Inundación" quizá sí, "situación económica" quizá no. **¿Existe un monto a
partir del cual solo el admin perdona?** La respuesta va a cambiar la
policy, y es el tipo de regla que solo aparece cuando alguien pregunta.

:::milestone
Fin de la Parte 7. La Casa Amarela está en línea: acervo con búsqueda,
filtro y paginación; préstamos con las once reglas de Vera en un service
que ella puede leer; autenticación y autorización por recurso; errores en
un solo formato; avisos por la cola, sin repetir; caché donde no miente;
pruebas que demuestran la regla y el contrato; documentación generada del
código; y un deploy que es un script.

El Sistema de 2009 está en una carpeta, con dos copias, y nadie la borró. Y
el sistema nuevo acaba de conocer lo que ningún entorno de pruebas simula:
gente de verdad usándolo.
:::

:::summary
- El `.gitignore` es una lista de incidentes; el `.env.example` entra, el
  `.env` nunca.
- Un secreto en el historial está filtrado: primero se cambia, después se
  limpia.
- El commit dice qué cambió en una línea y el porqué en el cuerpo.
- La cadena verifica estilo, análisis estático, `dd()` olvidados y pruebas
  en el MySQL de producción, y bloquea el *merge*.
- El deploy es un script que se detiene en el primer error, publica un
  *tag*, y sigue el orden: código, `down`, `migrate`, cachés,
  `queue:restart`, `up`.
- La migration corre una vez, en un solo lugar, y nunca tecleada a mano.
- `/up` dice que el proceso está vivo; `/listo`, que puede trabajar.
- La lista antes de publicar se revisa con la lista en la mano; el backup
  solo cuenta después de restaurarlo.
- Un requisito nuevo atraviesa ruta, validación, policy, service,
  excepción, evento, cola, resource, pruebas y documentación, y empieza con
  dos preguntas a quien hace el trabajo.
:::

:::checkpoint
La aplicación está en línea con la lista cumplida, la cadena bloquea lo que
no pasa, el deploy es un script versionado que puedes explicar paso a paso,
y el perdón de multas está implementado de punta a punta, por ti, por tu
cuenta, con una prueba para cada decisión.
:::

:::exercise level=1
Pon los pasos del deploy en el orden correcto y di qué sale mal si el paso
señalado va fuera de lugar:

`queue:restart` · `migrate --force` · `up` · `config:cache` ·
`composer install --no-dev` · `down` · `git checkout v1.4.0`

:::answer
1. `git checkout v1.4.0`
2. `composer install --no-dev`
3. `down`
4. `migrate --force`
5. `config:cache` (y las otras dos cachés)
6. `queue:restart`
7. `up`

**`config:cache` antes del `checkout`:** congela la configuración de la
versión anterior; la clave nueva del `.env` o de `config/` no entra.

**`migrate` antes del `down`:** durante la migración, la aplicación atiende
con la base a medias; un préstamo hecho en ese minuto puede grabarse en el
formato viejo o fallar.

**`queue:restart` olvidado:** el worker corre el código de ayer hasta que
alguien lo reinicie, o hasta que expire el `--max-time`.

**`up` antes de las cachés:** las primeras peticiones encuentran la caché
vieja o ninguna, y quedan lentas o equivocadas durante unos segundos.
:::

:::exercise level=2
La persona nueva del equipo hizo `git add .` y un `push` con el `.env` de
producción. El repositorio es privado, con seis personas con acceso.
Escribe, en orden, qué hacer en la próxima hora.

:::answer
1. **Cambiar los secretos**, empezando por los que dan más acceso: la
   contraseña del usuario de la base, la clave del proveedor de mensajes,
   cualquier token de servicio externo. Actualizar el `.env` del servidor y
   correr `config:cache`.
2. **Cambiar la `APP_KEY`**, con cuidado: cifra sesiones y cookies, y
   cambiarla desconecta a quien esté logueado en el panel. En una
   biblioteca, a las siete de la mañana, es aceptable; en otros sistemas,
   pide un plan.
3. **Quitar el archivo** del repositorio en un commit nuevo, y agregarlo al
   `.gitignore` si no estaba.
4. **Reescribir el historial**, si el equipo lo decide, avisando a las seis
   personas para que vuelvan a clonar.
5. **Revisar el `.gitignore`** y la configuración del editor de la persona,
   para entender cómo pasó el archivo.

Y un sexto, que no es técnico: tratarlo como accidente, no como culpa. La
persona que esconde el próximo error porque la expusieron en este es el
riesgo mayor. El paso 5 es sobre el proceso que lo dejó pasar, no sobre
quien lo tecleó.
:::

:::exercise level=3
Implementa el perdón de multas descrito en la sección "El primer pedido
después de salir al aire". Usa la tabla de capas como guion y las dos
preguntas a Vera como punto de partida: decide las respuestas y escríbelas
en un comentario al inicio del service.

Al terminar, responde: ¿cuál de las diez decisiones cambiarías si Vera
respondiera distinto a la segunda pregunta, y cuántos archivos tocaría ese
cambio?

:::answer
No hay una respuesta única, y una solución completa tiene entre ocho y
doce archivos. Los puntos que una buena solución acierta:

**Ruta:** `POST /multas/{multa}/perdon`, y no `DELETE /multas/{multa}`: la
multa no deja de existir; gana un desenlace. El historial tiene que
mostrar que hubo multa y que se perdonó. Es la misma razón del
`POST /prestamos/{id}/devolucion` del capítulo @cap:o-que-e-uma-api-rest.

**Service:** `MultaService::perdonar(int $multaId, Autorizacion $a)`, con
transacción y bloqueo, lanzando `MultaYaSaldada` si ya está pagada o
perdonada. La `Autorizacion` del capítulo @cap:services vuelve: el perdón
es un juicio, y los juicios se registran.

**Policy:** `MultaPolicy::perdonar`, preguntando por un permiso
`PerdonarMulta`, no por el rol.

**Evento y cola:** `MultaPerdonada` con `ShouldDispatchAfterCommit`, y un
listener que avisa al lector con registro `unique` en `avisos_enviados`.

**Pruebas:** la regla de "no se perdona dos veces" en la unitaria; el `403`
para el lector y el `201` para quien tiene el permiso en la feature; el job
ejecutado dos veces con un solo mensaje.

**Sobre la pregunta final.** Si Vera responde que las multas de más de, por
ejemplo, R$ 50 solo las perdona el admin, el cambio vive **en un lugar**:
`MultaPolicy::perdonar` pasa a recibir la multa y comparar el monto. Un
archivo de código y un caso nuevo en el dataset de la prueba de feature.

Si tu respuesta tocó más archivos que eso —si el límite apareció en el
service **y** en la policy, o en el Form Request—, vale la pena volver y
preguntar dónde vive la regla. Es la pregunta que hizo el libro entero,
capítulo tras capítulo, y es la que vas a hacer, a partir de ahora, sin
él.
:::
