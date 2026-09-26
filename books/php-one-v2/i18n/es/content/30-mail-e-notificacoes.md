---
source_hash: 3aaf2e0591f4
title: "Mail y notificaciones"
number: 30
slug: mail-e-notificacoes
part: p8
kicker: "El primer e-mail de la Casa Amarela lo firmó un tal Laravel, desde hello@example.com. Doña Marlene lo imprimió y lo llevó al mostrador como prueba de la estafa."
goal: >-
  Separar el e-mail que es documento del aviso que es notificación,
  configurar quién firma lo que sale, llevar el mismo aviso por e-mail,
  WhatsApp e historial en la aplicación con una sola clase, poner cada canal
  en la cola sin que la falla de uno repita el otro, hablar el idioma del
  lector, llegar a la bandeja de entrada y probar sin mandar nada.
---

:::story Un tal Laravel
La cuenta del proveedor de WhatsApp llegó en abril: nueve centavos por
mensaje, trescientos mensajes por día. Márcia hizo la cuenta delante de
don Juvenal, que hizo la misma cuenta otra vez, más despacio.

—¿Y el e-mail es gratis? —preguntó él.

—Casi —dijo Dedé.

El lunes siguiente, el aviso de "tu libro vence mañana" empezó a salir
también por e-mail. El martes, a las nueve y cinco, doña Marlene estaba en
el mostrador con una hoja impresa, doblada en cuatro.

—Vera, mira esto. Mi nieto dice que es una estafa.

Vera desdobló la hoja. Arriba, en letras grandes: **Laravel**. Abajo,
*Hello!* Después, en portugués, el título del libro y un botón *Renovar*.
Al final: *Regards, Laravel*. Y el remitente: `hello@example.com`.

—¿Quién es Laravel? —preguntó doña Marlene.

—Es... —Vera buscó la palabra— ...el sistema.

—¿El sistema se llama Laravel?

—El sistema se llama Casa Amarela.

—¿Y entonces por qué firma Laravel?

Vera le sacó una foto a la hoja y se la mandó a Tainá, con una sola
palabra: *"¿Laravel?"*

Tainá abrió el `.env` de producción.

```text
APP_NAME=Laravel
MAIL_FROM_ADDRESS="hello@example.com"
MAIL_FROM_NAME="${APP_NAME}"
```

—Son los valores de fábrica —le dijo a Dedé—. Nunca los cambiamos. Nadie
había recibido nunca un e-mail nuestro.
:::

## Documento o aviso

Laravel tiene dos formas de mandar mensajes, y responden a preguntas
distintas.

Un **Mailable** es un e-mail. Tiene asunto, cuerpo y adjuntos, y va a una
dirección. Sirve para lo que es **documento**: el acta de donación firmada,
la constancia de no adeudo que el estudiante lleva a la escuela.

Una **notificación** es un hecho que tiene que llegarle a una **persona**,
por el canal que usa: e-mail, WhatsApp, la campanita de la aplicación. "Tu
libro vence mañana" es una notificación. Doña Marlene la quiere por
e-mail; don Juvenal, por WhatsApp; los dos quieren verla en la aplicación
de Kauã.

| Pregunta | Mailable | Notificación |
|---|---|---|
| ¿Qué es? | un e-mail | un hecho sobre alguien |
| ¿Para quién? | una dirección | un objeto que recibe avisos |
| ¿Por dónde? | e-mail | todos los canales que tenga la persona |
| Ejemplo | acta de donación en PDF | "vence mañana", "reserva disponible" |

Tabla: Cuando el texto solo tiene sentido como e-mail, Mailable. Cuando el
hecho tiene que llegar como sea, notificación.

:::art caption="El sistema se llama Casa Amarela. El e-mail lo firmaba Laravel."
src="o-sistema-se-chama-casa-amarela-o-e-mail-assinava-laravel.png"
Charge editorial minimalista em fundo branco: uma senhora de setenta e
nove anos, de cardigã, estende sobre um balcão de biblioteca uma folha
impressa, desdobrada em quatro, onde se lê no topo, em letras grandes,
"Laravel", e no rodapé "Regards, Laravel". Uma bibliotecária mais velha,
de óculos, olha a folha com as sobrancelhas erguidas, o celular na mão
pronto para fotografar. Atrás do balcão, uma casinha amarela desenhada
num cartaz na parede. Poucos elementos, humor seco, estética de revista de tecnologia.
:::

## Quién firma lo que sale

Antes de cualquier clase, el `.env`, que es donde estaba el problema de
doña Marlene:

```text title=".env (producción)"
APP_NAME="Biblioteca Casa Amarela"
APP_LOCALE=es

MAIL_MAILER=smtp
MAIL_HOST=smtp.proveedor.com.br
MAIL_PORT=587
MAIL_USERNAME=avisos@casaamarela.org.br
MAIL_PASSWORD=
MAIL_FROM_ADDRESS="avisos@casaamarela.org.br"
MAIL_FROM_NAME="${APP_NAME}"
```

El `APP_NAME` aparece en tres lugares del e-mail por defecto —el
encabezado, la firma y el pie de *copyright*— y en los tres se volvió
"Laravel". El `MAIL_FROM_ADDRESS` es el remitente; `example.com` es un
dominio reservado para ejemplos, y ningún proveedor serio entrega un
e-mail que dice venir de ahí.

En tu máquina, el e-mail no sale:

```text title=".env (local)"
MAIL_MAILER=log
```

El driver `log` escribe el e-mail entero en `storage/logs/laravel.log`, en
vez de mandarlo. Para ver el e-mail ya diseñado, una herramienta como
Mailpit finge ser un servidor de correo y lo muestra todo en una página
local.

:::warning
Nunca copies el `.env` de producción a tu máquina "para probar con los
datos de verdad". Con él viene el `MAIL_MAILER=smtp`, y el primer comando
programado que corras les avisa a mil lectores que su libro vence mañana,
un libro que devolvieron en marzo.
:::

## La notificación

```text
$ php artisan make:notification DevolucionManana
```

El lector pasa a recibir avisos con un trait:

```php title="app/Models/Lector.php" numbered
class Lector extends Model
{
    use Notifiable;

    // ...
}
```

`Notifiable` le da al model el método `notify()` y sabe, por defecto, que
la dirección de e-mail está en la columna `email`. Y la notificación dice
qué decir y por dónde:

```php title="app/Notifications/DevolucionManana.php" numbered
final class DevolucionManana extends Notification implements
    ShouldQueue
{
    use Queueable;

    public function __construct(
        public readonly Prestamo $prestamo,
    ) {
        $this->afterCommit();
    }

    public function via(Lector $lector): array
    {
        return array_values(array_filter([
            $lector->email !== null ? 'mail' : null,
            $lector->acepta_whatsapp ? CanalWhatsApp::class : null,
            'database',
        ]));
    }

    public function toMail(Lector $lector): MailMessage
    {
        $titulo = $this->prestamo->ejemplar->libro->titulo;

        return (new MailMessage)
            ->subject("\"{$titulo}\" vence mañana")
            ->greeting("¡Hola, {$lector->nombre}!")
            ->line("El plazo de \"{$titulo}\" termina mañana.")
            ->line('Si necesitas más tiempo, puedes renovarlo.')
            ->action('Renovar', $this->enlaceDeRenovacion());
    }

    public function toWhatsApp(Lector $lector): string
    {
        return sprintf(
            '"%s" vence mañana. Renuévalo en la aplicación.',
            $this->prestamo->ejemplar->libro->titulo,
        );
    }

    public function toArray(Lector $lector): array
    {
        return [
            'prestamo_id' => $this->prestamo->id,
            'devolver_hasta' => $this->prestamo->devolver_hasta
                ->toDateString(),
        ];
    }
}
```

Cuatro métodos, una responsabilidad cada uno.

**`via`** elige los canales **para esa persona**. Quien no tiene e-mail no
recibe e-mail; quien no aceptó WhatsApp —una columna booleana nueva en
`lectores`, `acepta_whatsapp`— no recibe WhatsApp; todo el mundo lo recibe
en el historial.

**`toMail`** arma el e-mail con un `MailMessage`: asunto, saludo, líneas y
un botón. Laravel dibuja el HTML, con la versión en texto plano al lado.

**`toWhatsApp`** es el texto que va a enviar el canal propio, un poco más
abajo.

**`toArray`** es lo que el canal `database` graba en la tabla
`notifications`, creada con `php artisan make:notifications-table`. La
aplicación de Kauã lista `$lector->notifications` y dibuja la campanita.

Y la programación del capítulo @cap:events-jobs-e-filas pasa a notificar en
vez de llamar directamente al enviador:

```php title="routes/console.php" numbered
Schedule::call(function () {
    Prestamo::abiertos()
        ->whereDate('devolver_hasta', today()->addDay())
        ->with('lector', 'ejemplar.libro')
        ->each(fn (Prestamo $p) => $p->lector->notify(
            new DevolucionManana($p),
        ));
})->dailyAt('09:00')->name('avisos-de-devolucion');
```

## Un canal que Laravel no tiene

El WhatsApp de la Casa Amarela ya existía: es el `EnviadorDeAviso` del
capítulo @cap:service-container, con el proveedor detrás de una interfaz.
Un canal propio es una clase con un método `send`:

```php title="app/Notifications/Canales/CanalWhatsApp.php" numbered
final class CanalWhatsApp
{
    public function __construct(
        private readonly EnviadorDeAviso $avisos,
    ) {}

    public function send(Lector $lector, Notification $aviso): void
    {
        $this->avisos->enviar($lector, $aviso->toWhatsApp($lector));
    }
}
```

`via` devuelve el nombre de la clase, y Laravel la construye con el
contenedor, con el `EnviadorDeAviso` que el `AvisoServiceProvider` ya
registra. Ninguna línea del enviador cambió: ganó un cliente más.

## Un job por canal

La notificación implementa `ShouldQueue`, y eso hace más de lo que parece.
Para doña Marlene, con e-mail, WhatsApp e historial, el `notify()` no crea
**un** job: crea **tres**, uno por canal.

Es la regla del capítulo @cap:events-jobs-e-filas —el job es la unidad más
pequeña que tiene sentido repetir— aplicada sin que escribas nada. Si se
cae el proveedor de WhatsApp, solo el job de WhatsApp vuelve a la cola. El
e-mail, que ya salió, no sale otra vez. Doña Iolanda, la de los mil
cuatrocientos mensajes, lo agradecería.

El `afterCommit()` en el constructor es el mismo cuidado de los eventos de
aquel capítulo: si la notificación se dispara dentro de una transacción,
solo entra en la cola después del `commit`. Un aviso de "reserva
disponible" no puede salir para una reserva que el `rollback` deshizo.

:::key
Una notificación en la cola se vuelve un job por canal. Escribe cada `toX`
como si pudiera correr sola, horas después, y más de una vez: busca lo que
necesites, verifica que el aviso todavía tenga sentido, y no dependas de lo
que hizo otro canal.
:::

## En el idioma del lector

Con el `APP_NAME` correcto, el e-mail todavía sale a medias en inglés. El
saludo es nuestro, pero el molde por defecto de Laravel trae tres frases
propias: la despedida, el pie y la instrucción para quien no puede pulsar
el botón.

Pasan por la función de traducción, y el `APP_LOCALE=es` manda a buscarlas
en `lang/es.json`:

```json title="lang/es.json"
{
    "Regards,": "Saludos,",
    "All rights reserved.": "Todos los derechos reservados.",
    "If you're having trouble clicking ...": "Si el botón ..."
}
```

La clave es el texto original **exacto**. Las dos primeras son cortas. La
tercera —abreviada arriba— es la frase entera del botón, con un salto de
línea `\n` en el medio, comillas escapadas y el marcador `:actionText`, que
Laravel cambia por la etiqueta del botón en los dos idiomas. Cópiala del
molde, en
`vendor/laravel/framework/src/Illuminate/Notifications/resources/views/email.blade.php`,
en vez de teclearla: una coma de menos en la clave, y la frase sigue en
inglés, sin ningún error.

Los mensajes de validación del capítulo @cap:upload-de-arquivos, *"The capa
field has invalid image dimensions"*, tienen la misma causa y el mismo
remedio, en `lang/es/validation.php`. Hay paquetes de la comunidad que
traen las dos traducciones listas; vale revisarlas antes del primer
e-mail, y no después de la primera doña Marlene.

## Llegar a la bandeja de entrada

El e-mail con el nombre correcto y en el idioma correcto todavía puede caer
en spam. Los proveedores de correo deciden según quién dice haberlo
mandado, y lo verifican en el DNS del dominio:

| Registro | Qué le dice al proveedor |
|---|---|
| SPF | qué servidores pueden mandar e-mail por `casaamarela.org.br` |
| DKIM | una firma que prueba que el mensaje no se alteró |
| DMARC | qué hacer con el e-mail que falla en los dos anteriores |

Tabla: Los tres registros vienen listos del proveedor de envío; alguien
con acceso al DNS del dominio tiene que pegarlos.

En la Casa Amarela, el acceso al DNS estaba en el papel doblado de Nonato.
Encontrar el login del registro del dominio tomó una semana, y pegar los
tres registros, diez minutos.

Y una regla de convivencia: el aviso de plazo es un mensaje de
**servicio**, y el lector puede apagarlo en la aplicación —la columna
`acepta_whatsapp` y una hermana para el e-mail—. Un mensaje de
**difusión** —el bazar de libros, el taller del sábado— solo va a quien
pidió recibirlo. Esa diferencia no es cortesía: es la LGPD, la ley de
protección de datos de Brasil.

## El documento, como Mailable

El acta de donación del capítulo @cap:upload-de-arquivos tiene que volver
firmada al donante. Eso es documento, y va como Mailable:

```text
$ php artisan make:mail ActaDeDonacionFirmada --markdown=mail.acta
```

```php title="app/Mail/ActaDeDonacionFirmada.php" numbered
final class ActaDeDonacionFirmada extends Mailable implements
    ShouldQueue
{
    use Queueable, SerializesModels;

    public function __construct(public readonly Donacion $donacion) {}

    public function envelope(): Envelope
    {
        return new Envelope(subject: 'Tu acta de donación');
    }

    public function content(): Content
    {
        return new Content(markdown: 'mail.acta');
    }

    public function attachments(): array
    {
        $acta = $this->donacion->acta;

        return [
            Attachment::fromStorageDisk('local', $acta)
                ->as('acta-de-donacion.pdf')
                ->withMime('application/pdf'),
        ];
    }
}
```

```php
Mail::to($donacion->donante_email)
    ->send(new ActaDeDonacionFirmada($donacion));
```

El `ShouldQueue` en la clase hace que el `send` vaya a la cola. El adjunto
sale del disco privado —el mismo desde donde lo sirve el
`ActaDeDonacionController`— sin pasar por ninguna carpeta pública.

## Probar sin mandar

```php title="tests/Feature/AvisoDeDevolucionTest.php" numbered
test('avisa por e-mail y WhatsApp si aceptó ambos', function () {
    Notification::fake();
    $prestamo = Prestamo::factory()
        ->venceManana()
        ->for(Lector::factory()->conEmail()->aceptaWhatsApp())
        ->create();

    $this->artisan('schedule:test', [
        '--name' => 'avisos-de-devolucion',
    ]);

    Notification::assertSentTo(
        $prestamo->lector,
        DevolucionManana::class,
        fn ($aviso, array $canales) => $canales === [
            'mail', CanalWhatsApp::class, 'database',
        ],
    );
});

test('e-mail en español, firmado por la Casa Amarela', function () {
    config(['app.name' => 'Biblioteca Casa Amarela']);
    app()->setLocale('es');
    $prestamo = Prestamo::factory()->venceManana()->create();

    $html = (string) (new DevolucionManana($prestamo))
        ->toMail($prestamo->lector)
        ->render();

    expect($html)
        ->toContain('Biblioteca Casa Amarela')
        ->toContain('Saludos')
        ->not->toContain('Laravel')
        ->not->toContain('Regards');
});
```

`Notification::fake()` intercepta el `notify()`: nada va a la cola, no se
llama a ningún canal, y la prueba pregunta después qué **se habría**
enviado, a quién y por dónde. La segunda prueba dibuja el e-mail de verdad
y verifica el texto: es la prueba que le habría ahorrado a doña Marlene un
viaje al mostrador.

`Mail::fake()` hace lo mismo con los Mailables, con `Mail::assertQueued`.

:::note En tu carrera
El e-mail es la única pieza del sistema que llega a la casa de las
personas, sin que ellas hayan abierto nada. Un error en la pantalla, el
lector la cierra. Un error en el e-mail, lo imprime y lo lleva al
mostrador.

Antes del primer envío en producción, mándate el e-mail a ti mismo, desde
el servidor de producción, y léelo entero en el celular: remitente,
asunto, encabezado, pie, el botón, y el texto en letra chica debajo de él.
Son cinco minutos, y es la única revisión que mira lo que va a mirar el
lector.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/
    Mail/ActaDeDonacionFirmada.php   # documento, con adjunto privado
    Notifications/
      DevolucionManana.php           # mail, WhatsApp, database
      Canales/CanalWhatsApp.php      # usa el EnviadorDeAviso
    Models/Lector.php                # Notifiable
  lang/es.json                       # el molde del e-mail traducido
  resources/views/mail/acta.blade.php
:::

:::summary
- El Mailable es documento; la notificación es un hecho que le llega a una
  persona por todos los canales que tenga.
- `APP_NAME`, `MAIL_FROM_ADDRESS` y `MAIL_FROM_NAME` firman el e-mail.
  Los valores de fábrica dicen "Laravel" y `hello@example.com`.
- En la máquina local, `MAIL_MAILER=log`. Nunca el `.env` de producción.
- `via()` elige los canales por persona; `toMail`, `toArray` y un `toX` por
  canal propio dicen qué mandar.
- Un canal propio es una clase con `send`, construida por el contenedor.
- Una notificación en la cola se vuelve un job por canal; `afterCommit()`
  espera a la transacción.
- El molde por defecto se traduce con `lang/es.json`, con la clave exacta.
- SPF, DKIM y DMARC en el DNS; el mensaje de servicio se puede apagar, la
  difusión solo con consentimiento.
- `Notification::fake()` y `Mail::fake()` prueban sin mandar.
:::

:::checkpoint
Eliges entre Mailable y notificación, configuras remitente e idioma antes
del primer envío, mandas el mismo aviso por varios canales con una clase,
escribes un canal propio sobre un servicio que ya existía, pones cada
canal en la cola sin repetir los demás, y pruebas lo que se enviaría sin
enviar nada.
:::

:::exercise level=1
¿Mailable o notificación?

1. "Tu reserva de *Capitanes de la arena* está disponible hasta el
   viernes."
2. El recibo mensual de donaciones, en PDF, para el contador de la
   asociación.
3. "Tu multa de R$ 4,80 fue perdonada."
4. La constancia de no adeudo que el estudiante pidió por la aplicación.

:::answer
1. Notificación. Es un hecho sobre el lector, y quiere enterarse por el
   canal que usa.
2. Mailable. Es un documento, con adjunto, para una dirección; el contador
   ni siquiera es lector.
3. Notificación: es la `MultaPerdonada` del último pedido de Vera, en el
   capítulo @cap:git-ci-e-deploy.
4. Mailable. El estudiante la va a imprimir o reenviar; lo que importa es
   el documento, no el aviso.
:::

:::exercise level=2
Escribe la notificación `ReservaDisponible`, con e-mail e historial, y un
`via` que **no** mande nada si la reserva se canceló entre el disparo y la
ejecución en la cola.

:::answer
```php
final class ReservaDisponible extends Notification implements
    ShouldQueue
{
    use Queueable;

    public function __construct(public readonly Reserva $reserva)
    {
        $this->afterCommit();
    }

    public function via(Lector $lector): array
    {
        if ($this->reserva->fresh()?->cancelada()) {
            return [];
        }
        return $lector->email !== null
            ? ['mail', 'database']
            : ['database'];
    }

    public function toMail(Lector $lector): MailMessage
    {
        return (new MailMessage)
            ->subject('Tu reserva está disponible')
            ->line(sprintf(
                '"%s" está apartado para ti hasta el %s.',
                $this->reserva->libro->titulo,
                $this->reserva->expira_en->format('d/m'),
            ));
    }

    public function toArray(Lector $lector): array
    {
        return ['reserva_id' => $this->reserva->id];
    }
}
```

Si `via` devuelve `[]`, la notificación no sale por ningún canal. El
`fresh()` vuelve a buscar la reserva en la base: el objeto que llegó en la
cola es una fotografía del momento del disparo.
:::

:::exercise level=3
Un mes después, Márcia recibe la factura del proveedor de e-mail: 9.000
envíos, para 1.200 lectores activos. La programación corre una vez al día.
Enumera tres causas posibles, en orden de investigación, y qué consultarías
para confirmar cada una.

:::answer
1. **La programación corre en más de un servidor.** Si la aplicación ganó
   un segundo servidor y los dos tienen el programador encendido, cada
   aviso sale dos veces. Confírmalo en el log: dos "avisos-de-devolucion"
   en el mismo minuto, desde máquinas distintas. Arreglo:
   `->onOneServer()` en la programación.
2. **Un canal que falla y reintenta el e-mail junto con él.** No debería
   pasar —son jobs separados—, pero una notificación escrita como un solo
   job que llama a los tres canales tendría ese efecto. Confírmalo en
   `failed_jobs` y en los reintentos del job de WhatsApp.
3. **La consulta agarra a más gente de la que debería.** Un `whereDate`
   con la zona horaria equivocada —el capítulo @cap:datas-e-horarios—
   puede incluir a los que vencen hoy y mañana. Confírmalo contando, para
   un día, cuántos préstamos devuelve la consulta y cuántos vencen de
   verdad al día siguiente.

Nueve mil para mil doscientos lectores en treinta días son trescientos por
día: exactamente el número de préstamos que vencen por día. Antes de las
tres hipótesis, vale la cuenta más simple: quizá no haya ningún defecto, y
la factura solo sea la primera.
:::
