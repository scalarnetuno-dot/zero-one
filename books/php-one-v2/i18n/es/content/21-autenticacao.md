---
source_hash: 02f09545a66c
title: "Autenticación con Sanctum"
number: 21
slug: autenticacao
part: p5
kicker: "El Sistema guardaba las contraseñas en MD5, sin sal. A la hora del almuerzo, en la máquina de un desarrollador, el sesenta por ciento cayó en cuatro minutos."
goal: >-
  Responder "quién eres" con seguridad: guardar la contraseña de la forma
  correcta, migrar las que están mal, emitir y revocar tokens con Sanctum, y
  escribir un inicio de sesión cuya respuesta de error no entregue nada: ni
  en el texto, ni en el tiempo.
---

:::story Cuatro minutos
Dedé había exportado la tabla `usuarios` del Sistema para planificar la
migración. Dos columnas interesaban: `email` y `contrasena`. La segunda
tenía treinta y dos caracteres hexadecimales en cada fila.

—MD5 —dijo.

—¿Eso es malo? —preguntó Tainá.

—Dame cuatro minutos.

Descargó una lista pública de contraseñas filtradas —algunos millones de
líneas, el tipo de archivo que circula hace una década—, escribió un bucle
de ocho líneas y lo ejecutó. El ventilador del portátil se aceleró.

```text
$ php romper.php usuarios.csv contrasenas-comunes.txt
probadas: 14.344.391
rotas: 1.047 de 1.731 (60,5%)
tiempo: 3min52s
```

Tainá miró la lista que iba apareciendo. `123456`. `casaamarela`.
`biblioteca`. `marmelada1994`. El nombre de un perro que conocía por una
foto en el mostrador.

—¿Puedes borrar eso ahora? —dijo.

—Ya lo estoy borrando.

—¿Y si alguien tiene esa tabla?

—El Sistema está en producción hace quince años, con el respaldo en un
disco en la sala del fondo y la contraseña del FTP en un papel —dijo Dedé—.
No sé quién tiene esa tabla.
:::

## La contraseña nunca se guarda

El Sistema cometió un error que parece técnico y es de principio. Guardaba
**algo derivado de la contraseña** que permitía descubrir la contraseña.

Lo que necesita un sistema de inicio de sesión no es saber la contraseña.
Es **comprobar** si la contraseña escrita ahora es la misma que se registró
antes. Para eso, basta con guardar algo que:

1. sea siempre igual para la misma contraseña;
2. no permita, en la práctica, volver a la contraseña original.

Una función con esas dos propiedades se llama *hash*. MD5 es una, y por eso
el Sistema creía que estaba protegido.

El problema está en la expresión "en la práctica". MD5 se diseñó para ser
**rápido**: comprobar la integridad de archivos grandes, millones de veces
por segundo. Una placa de video común calcula miles de millones de MD5 por
segundo. Con esa velocidad, no hace falta volver del hash a la contraseña:
basta con calcular el hash de todas las contraseñas probables y comparar.

Y sin **sal** —un valor aleatorio distinto para cada usuario, mezclado con
la contraseña antes del cálculo—, las personas con la misma contraseña
tienen el mismo hash. La lista de hashes de contraseñas comunes, calculada
una vez, sirve para todos los sistemas del mundo que usaron MD5 puro.

| Guardar | Quien filtra la tabla obtiene |
|---|---|
| la contraseña | todas las contraseñas, en el acto |
| MD5 sin sal | las contraseñas comunes, en minutos |
| SHA-256 sin sal | lo mismo, un poco más despacio |
| MD5 con sal | las comunes, una cuenta a la vez |
| `bcrypt` / `argon2` | muy poco, muy despacio |

Tabla: Lo que cambia de una línea a otra no es la matemática de la
función; es cuánto tiempo cuesta **cada intento**.

## `bcrypt`, `argon2` y el costo que es a propósito

Las funciones hechas para contraseñas hacen lo contrario de MD5: son
**lentas a propósito**, con la cantidad de lentitud ajustable por un factor
de costo.

```php
$hash = Hash::make('marmelada1994');
```

```text
$2y$12$Qm1S3pTjXe4K8b0vYzN1ZuQ4rW7pX2... (60 caracteres)
```

El hash ya trae dentro todo lo que hace falta para comprobarlo después: el
algoritmo (`2y` es `bcrypt`), el costo (`12`), la sal (los 22 caracteres
siguientes) y el resultado. Nada de eso es secreto, y nada de eso ayuda a
descubrir la contraseña.

```php
Hash::check('marmelada1994', $hash); // true
Hash::check('marmelada1995', $hash); // false
```

Con costo 12, cada comprobación tarda algo así como doscientos cincuenta
milisegundos en una máquina común. Para quien inicia sesión, es
imperceptible. Para quien prueba catorce millones de contraseñas, es la
diferencia entre cuatro minutos y **ciento once días**, por cuenta, porque
cada una tiene su sal.

Laravel usa `bcrypt` por defecto, con el costo configurado en el `.env`. El
`argon2id` es más moderno y resiste mejor a las placas de video; los dos
son elecciones correctas. La elección equivocada es cualquier cosa que no
se haya hecho para contraseñas.

:::key
El costo no es un defecto que optimizar. Si alguien del equipo "acelera el
inicio de sesión" bajando el factor de costo a 4, el inicio de sesión se
vuelve cincuenta veces más rápido para todo el mundo, incluido quien robó
la tabla.

El `Hash::needsRehash($hash)` dice si un hash se generó con un costo menor
que el configurado. Es lo que permite **subir** el costo con los años, a
medida que las máquinas se vuelven más rápidas.
:::

### Migrar las contraseñas del Sistema

Las 1.731 cuentas del Sistema no se pueden convertir de una vez: para
generar el `bcrypt` hace falta la contraseña, y la contraseña no la tiene
nadie. La salida es convertirla **en el próximo inicio de sesión de cada
persona**, cuando la contraseña pasa por la aplicación:

```php title="app/Auth/VerificadorDeContrasena.php" numbered
final class VerificadorDeContrasena
{
    public function verifica(Usuario $u, string $clave): bool
    {
        if ($this->esMd5Legado($u->contrasena)) {
            if (!hash_equals($u->contrasena, md5($clave))) {
                return false;
            }

            $u->forceFill(['contrasena' => Hash::make($clave)])
                ->save();

            return true;
        }

        if (!Hash::check($clave, $u->contrasena)) {
            return false;
        }

        if (Hash::needsRehash($u->contrasena)) {
            $u->forceFill(['contrasena' => Hash::make($clave)])
                ->save();
        }

        return true;
    }

    private function esMd5Legado(string $hash): bool
    {
        return (bool) preg_match('/^[a-f0-9]{32}$/', $hash);
    }
}
```

`hash_equals` compara dos strings tardando siempre el mismo tiempo,
independientemente de dónde difieran. La comparación con `===` se detiene
en el primer carácter distinto, y eso, medido millones de veces, filtra
información.

:::warning
La migración en el inicio de sesión protege las cuentas **de aquí en
adelante**. No protege lo que ya se filtró.

Las contraseñas del Sistema deben considerarse comprometidas: estuvo en
producción quince años con la tabla en MD5, y nadie sabe quién tuvo acceso
a los respaldos. La decisión correcta —y que Vera tiene que tomar con la
asociación, porque implica avisarles a todos— es **forzar el cambio de
contraseña** en el primer acceso al sistema nuevo. El
`VerificadorDeContrasena` sigue siendo útil: reconoce la contraseña vieja
una última vez, para permitir el cambio.

Y las cuentas que nunca más inicien sesión quedan con MD5 para siempre.
Después de un plazo, se borran —el hash, no la cuenta—, y el próximo acceso
pasa por la recuperación de contraseña.
:::

## Sesión y token: dos problemas distintos

Después de comprobar la contraseña, el servidor tiene que **recordar** que
la comprobó. HTTP no recuerda: el capítulo @cap:o-que-e-http mostró que cada
petición llega sola. Hay dos formas de resolverlo, y cada una sirve a un
tipo de cliente.

**Sesión con cookie.** El servidor guarda "el usuario 12 entró" en un
almacenamiento suyo, y le manda al navegador una cookie con un
identificador aleatorio. El navegador devuelve la cookie en cada petición,
solo. Es lo que usa el panel Blade.

**Token.** El servidor le entrega al cliente un string largo y aleatorio,
y el cliente lo manda en la cabecera `Authorization` de cada petición. Nada
es automático: el cliente lo guarda y lo manda. Es lo que usa la aplicación
del lector.

| | Sesión | Token |
|---|---|---|
| quién lo guarda | el navegador, solo | la aplicación, a propósito |
| cómo vuelve | cookie, automática | cabecera `Authorization` |
| sirve para | páginas en el mismo dominio | aplicaciones, integraciones |
| riesgo principal | CSRF | token filtrado |

Tabla: Que la cookie sea automática es la ventaja y el riesgo. El CSRF del
capítulo @cap:blade existe justamente porque el navegador manda la cookie
aunque la petición la haya disparado otro sitio.

## Sanctum

Sanctum es el paquete de Laravel que resuelve las dos cosas en el mismo
lugar: tokens para aplicaciones y autenticación por sesión para un
front-end en el mismo dominio. La Casa Amarela usa la primera mitad.

```text
$ php artisan install:api
```

El comando instala Sanctum, crea la tabla `personal_access_tokens` y el
archivo `routes/api.php`, si todavía no existe. El model de usuario recibe
un trait:

```php title="app/Models/Usuario.php" numbered
class Usuario extends Authenticatable
{
    use HasApiTokens;

    protected $table = 'usuarios';

    protected $authPasswordName = 'contrasena';

    protected $fillable = ['nombre', 'email'];

    protected $hidden = ['contrasena'];

    protected function casts(): array
    {
        return [
            'rol' => Rol::class,
            'contrasena' => 'hashed',
        ];
    }
}
```

El `$authPasswordName` le dice a Laravel que la columna se llama
`contrasena` y no `password`. El cast `hashed` hace el hash solo cuando
alguien asigna una contraseña en texto, y no lo hace otra vez si el valor
ya es un hash, lo que evita el hash de un hash.

`Rol` es un enum con tres casos, y el capítulo siguiente depende de él:

```php title="app/Auth/Rol.php" numbered
enum Rol: string
{
    case Lector = 'lector';
    case Encargado = 'encargado';
    case Admin = 'admin';
}
```

Un `Usuario` con rol `Lector` tiene un `lector_id` que apunta al registro
del lector. Los encargados y el admin no lo tienen: son el equipo.

## Inicio de sesión, cierre de sesión y `GET /yo`

```php title="app/Http/Controllers/Auth/LoginController.php" numbered
public function __invoke(
    LoginRequest $request,
    VerificadorDeContrasena $verificador,
) {
    $usuario = Usuario::where(
        'email',
        mb_strtolower($request->string('email')),
    )->first();

    $valido = $usuario !== null
        && $verificador->verifica($usuario, $request->contrasena);

    if (!$usuario) {
        Hash::check($request->contrasena, self::HASH_FALSO);
    }

    if (!$valido) {
        throw new CredencialesInvalidas();
    }

    $token = $usuario->createToken(
        name: $request->string('dispositivo', 'app'),
        abilities: $usuario->rol->habilidades(),
        expiresAt: now()->addDays(30),
    );

    return response()->json([
        'token' => $token->plainTextToken,
        'expira_en' => $token->accessToken->expires_at
            ->toIso8601String(),
        'usuario' => new UsuarioResource($usuario),
    ], 201);
}
```

`createToken` genera un string aleatorio, graba su **hash** en la tabla
`personal_access_tokens` y devuelve el texto original una sola vez. Después
de esta respuesta, ni el servidor sabe cuál es el token: solo puede
comprobarlo.

:::anatomy title="Las partes de un token de Sanctum"
lang: text
code: |
  Authorization: Bearer 7|kX9vQ2mT8pLr4wYz6nB1cD3fG5hJ0sA2eR7tU9iO
notes:
  - { line: 1, text: "`Bearer` es el esquema: \"quien porte esto está autorizado\". Por eso el token se trata como una contraseña." }
  - { line: 1, text: "`7` es el id de la fila en `personal_access_tokens`. Sirve para encontrar la fila sin recorrer la tabla." }
  - { line: 1, text: "El `|` separa el id del secreto." }
  - { line: 1, text: "El resto son 40 caracteres aleatorios. La base guarda solo su SHA-256, y usar SHA aquí es seguro: el valor es aleatorio, no una contraseña que alguien eligió." }
:::

Fíjate en la última nota. SHA-256 está mal para contraseñas y bien para
tokens, y la diferencia está en quién eligió el valor. Una contraseña la
elige una persona, y existe una lista de las probables. Un token de
cuarenta caracteres aleatorios no tiene lista: probarlos todos llevaría más
tiempo que la edad del universo, con cualquier velocidad de cálculo.

Las rutas protegidas usan el middleware del capítulo anterior:

```php title="routes/api.php" numbered
Route::post('auth/login', LoginController::class)
    ->middleware('throttle:login');

Route::middleware('auth:sanctum')->group(function () {
    Route::get('yo', YoController::class);
    Route::post('auth/logout', LogoutController::class);
    // ... el resto de la API del lector
});
```

```php title="app/Http/Controllers/YoController.php" numbered
public function __invoke(Request $request)
{
    return new UsuarioResource(
        $request->user()->load('lector'),
    );
}
```

`$request->user()` devuelve el usuario dueño del token que vino en la
cabecera. Es el `null` que el `LectorResource` del capítulo
@cap:api-resources esperaba que dejara de serlo.

## Revocar de verdad

```php title="app/Http/Controllers/Auth/LogoutController.php" numbered
public function __invoke(Request $request)
{
    $request->user()->currentAccessToken()->delete();

    return response()->noContent();
}
```

El cierre de sesión borra **la fila del token** en la base. En la próxima
petición con ese token, Sanctum busca por el id, no lo encuentra, y
responde `401`.

Es la ventaja de un token que vive en la base sobre un token
autocontenido, como el JWT, que lleva los datos dentro y se comprueba solo
por la firma: el JWT sigue siendo válido hasta que vence, y "salir" en la
aplicación borra la copia del celular sin invalidar las otras. Con
Sanctum, salir es salir.

Tres situaciones piden revocar **todos** los tokens de una persona:

```php
$usuario->tokens()->delete();
```

**La persona cambió la contraseña.** Si la cambió porque desconfió de
alguien, ese alguien no puede seguir con la sesión iniciada.

**El equipo bloqueó la cuenta.** El bloqueo que no tumba las sesiones
abiertas es un bloqueo que vale "en el próximo inicio de sesión".

**La persona lo pidió.** El botón "cerrar sesión en todos los dispositivos"
existe en toda aplicación seria por eso.

:::pitfall
Un token sin vencimiento es un token para siempre. El celular perdido en
2026 todavía accede a la cuenta en 2031.

El `expiresAt` en el `createToken` define la validez de cada token, y la
configuración `expiration` en `config/sanctum.php` es la red de seguridad
para los que se creen sin ella. Treinta días con renovación al usarlo es un
equilibrio común para una aplicación; para el panel del equipo, horas.

Los tokens vencidos siguen en la tabla hasta que alguien los borre.
Sanctum tiene un comando para eso, `sanctum:prune-expired`, y va a la
programación del capítulo @cap:configuracao-ambiente-e-artisan.
:::

## La respuesta que no dice si el correo existe

Volviendo al `LoginController`, hay dos líneas que parecen raras.

La primera es la excepción única. Tanto un correo inexistente como una
contraseña equivocada producen **la misma respuesta**:

```json
{
  "tipo": "credenciales-invalidas",
  "mensaje": "Correo o contraseña incorrectos."
}
```

La alternativa —"correo no registrado" en un caso, "contraseña incorrecta"
en el otro— es más amable y le entrega a quien está atacando una lista de
quiénes son lectores de la Casa Amarela. Para una biblioteca, eso parece
inofensivo. Para un servicio de salud, de citas o de apoyo psicológico,
confirmar que un correo tiene cuenta ya es la filtración.

La segunda es el `Hash::check` con `HASH_FALSO` cuando el usuario no
existe. Calcula un `bcrypt` entero y **descarta el resultado**.

El motivo es el tiempo. Sin esa línea, un intento con un correo inexistente
responde en cinco milisegundos: solo la consulta a la base. Un intento con
un correo existente y una contraseña equivocada responde en doscientos
cincuenta: la consulta más el `bcrypt`. El mensaje es idéntico, y el
cronómetro lo cuenta todo.

:::key
Una respuesta de inicio de sesión tiene que ser igual en **tres**
dimensiones: el status, el cuerpo y el tiempo.

Las dos primeras se revisan leyendo la respuesta. La tercera solo se
revisa midiendo, y por eso es la que suele quedar afuera.
:::

Y el HTTPS, que parece obvio y merece estar escrito: sin él, la contraseña
viaja en texto por la red del café donde está el lector. Y el token
también, en todas las peticiones siguientes. Nada de este capítulo
funciona sin HTTPS, y el capítulo @cap:git-ci-e-deploy lo pone en la lista
antes de publicar.

:::note En tu carrera
Vas a encontrar contraseñas en MD5, en SHA-1, en texto plano y en
"cifrado reversible para poder mandar la contraseña por correo". Las vas a
encontrar en sistemas de empresas grandes, hechos por gente competente,
hace años.

La conversación sobre eso rara vez es técnica. Es sobre avisarles a los
usuarios, forzar el cambio de contraseña y admitir, por escrito, que el
sistema viejo tenía un problema. Quien conduce bien esa conversación —con
el plan de migración listo, el texto del aviso en borrador y el riesgo
explicado sin alarmismo— es a quien la empresa llama la próxima vez que
aparece algo parecido.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/Auth/
    Rol.php                        # lector, encargado, admin
    VerificadorDeContrasena.php    # migra el MD5 en el inicio de sesión
    CredencialesInvalidas.php      # una excepción para los dos casos
  app/Models/
    Usuario.php                    # HasApiTokens, cast hashed
  app/Http/Controllers/
    Auth/LoginController.php       # token con validez
    Auth/LogoutController.php      # borra el token actual
    YoController.php
  config/sanctum.php               # expiration
:::

:::summary
- La contraseña no se guarda; se guarda un hash que permite comprobar y no
  permite volver.
- MD5 y SHA son rápidos a propósito; `bcrypt` y `argon2` son lentos a
  propósito, con sal por usuario.
- El costo del hash es protección; `needsRehash` permite subirlo con los
  años.
- Las contraseñas heredadas migran en el próximo inicio de sesión; las que
  se filtraron exigen un cambio forzado.
- La sesión es una cookie automática para páginas; el token es una
  cabecera explícita para aplicaciones.
- Sanctum guarda el hash del token en la base; el cierre de sesión borra la
  fila y vale en el acto.
- El cambio de contraseña, el bloqueo y "cerrar sesión en todos" revocan
  todos los tokens.
- Un token sin vencimiento vale para siempre; `expiresAt` y
  `sanctum:prune-expired` lo resuelven.
- El error de inicio de sesión es igual en el status, en el cuerpo y en el
  tiempo; `hash_equals` y el hash falso protegen el tercero.
:::

:::checkpoint
El inicio de sesión de la API emite un token con validez y habilidades, el
cierre de sesión lo revoca en el acto, las contraseñas del Sistema migran
en el primer acceso, y sabes explicar por qué la respuesta de error es
genérica, y por qué tarda el mismo tiempo cuando el correo no existe.
:::

:::exercise level=1
Di qué está mal en cada decisión y cuál es la corrección:

1. `contrasena` guardada con `hash('sha256', $clave . 'casaamarela')`.
2. Un token creado sin `expiresAt` "porque el lector se queja de tener que
   volver a entrar".
3. Al cambiar la contraseña, el sistema genera el hash nuevo y lo guarda.
4. El inicio de sesión responde `404` cuando el correo no existe.

:::answer
1. SHA-256 es rápido, y la "sal" es la misma para todos: es una constante,
   no una sal. Corrección: `Hash::make`.
2. Un token eterno. Corrección: validez de treinta días **renovada al
   usarlo**: el lector activo nunca tiene que volver a entrar, y el celular
   olvidado en un cajón pierde el acceso solo.
3. Faltó revocar los otros tokens. Corrección:
   `$usuario->tokens()->delete()` después de guardar, salvo, si se quiere,
   el token de la petición actual.
4. Confirma que el correo no tiene cuenta. Corrección: la misma respuesta
   `401` para los dos casos, con el mismo tiempo.
:::

:::exercise level=2
Escribe el endpoint `POST /yo/contrasena`, que cambia la contraseña del
usuario autenticado. Recibe la contraseña actual y la nueva (con
confirmación). Debe rechazarlo si la actual está mal, revocar todos los
**otros** tokens, y mantener el actual funcionando.

:::answer
```php title="app/Http/Controllers/CambioDeContrasenaController.php" numbered
public function __invoke(
    CambioDeContrasenaRequest $request,
    VerificadorDeContrasena $verificador,
) {
    $usuario = $request->user();

    if (!$verificador->verifica(
        $usuario, $request->contrasena_actual,
    )) {
        throw new CredencialesInvalidas();
    }

    $usuario->contrasena = $request->contrasena_nueva;
    $usuario->save();

    $actual = $usuario->currentAccessToken()->id;

    $usuario->tokens()
        ->where('id', '!=', $actual)
        ->delete();

    return response()->noContent();
}
```

```php title="app/Http/Requests/CambioDeContrasenaRequest.php" numbered
public function rules(): array
{
    return [
        'contrasena_actual' => ['required', 'string'],
        'contrasena_nueva' => [
            'required', 'confirmed',
            Password::min(10)->uncompromised(),
        ],
    ];
}
```

El cast `hashed` hace el hash de la `contrasena_nueva` en la asignación. El
`Password::uncompromised()` consulta un servicio público de contraseñas
filtradas —sin enviar la contraseña, solo los primeros caracteres de su
hash— y rechaza las que aparecen en la lista. Es la lista que usó Dedé,
puesta del lado correcto.

La ruta queda detrás del `throttle`, como el inicio de sesión: sin él, es
un segundo lugar para probar contraseñas.
:::

:::exercise level=3
El equipo de marketing de la asociación quiere que la aplicación muestre,
en la pantalla de inicio de sesión, el mensaje "Ese correo no está
registrado. ¿Quieres inscribirte?", porque muchas personas intentan entrar
sin tener cuenta y se rinden.

La necesidad es real. Propón una solución que atienda al marketing sin
volver a revelar qué correos tienen cuenta, y di lo que cuesta.

:::answer
**El problema real.** Las personas sin cuenta intentan entrar, reciben
"correo o contraseña incorrectos", creen que se equivocaron de contraseña,
y se rinden. El mensaje genérico protege a quien tiene cuenta y perjudica a
quien no la tiene.

**La solución: cambiar el flujo, no el mensaje.** La pantalla de inicio de
sesión pasa a tener dos etapas. En la primera, la persona escribe el
correo y toca "continuar". La respuesta es siempre la misma: "Te mandamos
un enlace a ese correo". Si el correo tiene cuenta, el enlace lleva al
inicio de sesión. Si no la tiene, el enlace lleva a la inscripción, con el
correo ya completado.

Quien está atacando recibe siempre "te mandamos un enlace", y no aprende
nada. Quien no tiene cuenta recibe, en su propio correo, la invitación a
inscribirse, que es exactamente lo que el marketing quería mostrar.

**Lo que cuesta.** Un paso más en el inicio de sesión, y la dependencia de
que el envío de correos funcione, lo que, con la cola del capítulo
@cap:events-jobs-e-filas, es manejable. Y la pantalla de inscripción
necesita la misma disciplina: "ese correo ya está registrado" en la
inscripción filtra el mismo dato por la otra puerta. La respuesta ahí
también es "te mandamos un enlace".

**La alternativa más barata, y peor:** mostrar "¿No tienes cuenta?
Inscríbete" **siempre**, destacado, debajo del mensaje de error. No revela
nada, y ayuda a una parte de las personas. Es lo que se puede hacer esta
semana, mientras el flujo en dos etapas no está listo.
:::
