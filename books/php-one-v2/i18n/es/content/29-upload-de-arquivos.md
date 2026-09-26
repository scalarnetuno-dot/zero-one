---
source_hash: 9f28e7c33628
title: "Subida de archivos"
number: 29
slug: upload-de-arquivos
part: p8
kicker: "Vera fotografió trescientas portadas con el celular nuevo. La mitad no subió. La otra mitad subió acostada."
goal: >-
  Recibir archivos grandes sin que te frene un límite que no configuraste,
  validar la imagen por el contenido y por las dimensiones, elegir entre
  disco privado y público, procesar la imagen fuera de la petición,
  cambiar un archivo sin dejar huérfanos, y probarlo todo sin tocar el
  disco.
---

:::story Acostadas
La primera semana de abril, Vera recibió de la asociación un celular nuevo
y decidió que el acervo tendría portadas. Pasó tres tardes en el depósito,
fotografiando libro por libro sobre una cartulina blanca.

El jueves abrió el panel y empezó a subirlas. De la primera a la
nonagésima, todas dieron el mismo mensaje:

```text
The capa failed to upload.
```

—En inglés —le dijo a Tainá, por teléfono—. Y ni sé qué es *failed*.

El viernes, Tainá pasó las fotos por la computadora, que las achicó, y las
portadas subieron. Todas. Acostadas.

—¿Acostadas cómo?

—Acostadas. *Vidas secas* con el título de arriba abajo. *El conventillo*
mirando a la izquierda. En el celular están paradas.

Dedé abrió una de las fotos originales.

—Doce megabytes —dijo—. El servidor acepta dos. Y el celular no gira la
foto: la graba acostada y anota en un rincón del archivo "muéstrala
parada". El navegador lee la nota. Nuestro código, no.

Vera suspiró.

—Saqué trescientas.
:::

## Tres límites antes de tu código

El capítulo @cap:requests-e-responses trató la seguridad de la subida:
nombre y extensión generados de este lado, contenido verificado, carpeta
fuera de `public/`. Todo eso pasa dentro de Laravel. La foto de doce
megabytes de Vera no llegó hasta ahí.

Entre el celular y el controller hay tres porteros, y cada uno rechaza de
una manera distinta:

| Dónde | Configuración | Valor común | Lo que ve el cliente |
|---|---|---|---|
| servidor web | `client_max_body_size` (nginx) | 1 MB | `413` en HTML, antes de PHP |
| PHP | `upload_max_filesize` | 2 MB | el archivo llega con error: *failed to upload* |
| PHP | `post_max_size` | 8 MB | se descarta el cuerpo entero: `413` de Laravel |

Tabla: Tres límites, tres síntomas. El de Vera fue el segundo: PHP recibió
el pedido, descartó el archivo y le avisó a Laravel.

El segundo y el tercero viven en el `php.ini`. El `post_max_size` tiene que
ser **mayor** que el `upload_max_filesize`, porque el cuerpo de la petición
lleva el archivo y los demás campos juntos:

```ini title="/etc/php/8.3/fpm/conf.d/99-casa-amarela.ini"
upload_max_filesize = 12M
post_max_size = 14M
```

Y nginx tiene que estar de acuerdo con los dos:

```text title="/etc/nginx/sites-available/casa-amarela"
client_max_body_size 14m;
```

Esos números abren la puerta. Quien decide lo que entra es la validación,
que devuelve `422` con un mensaje que la aplicación sabe mostrar, en vez
de un `413` que nadie sabe leer.

:::key
Configura los tres porteros con **holgura**, y pon el límite de verdad en
la validación. El portero frena con una página de error genérica; la
validación frena con una frase en el campo correcto, en el idioma del
cliente.
:::

## Validar la imagen por lo que es

El `'image'` del capítulo @cap:requests-e-responses verifica que el archivo
sea una imagen. Para la portada de un libro, la Casa Amarela necesita más:
un formato que el navegador muestre, un tamaño máximo, y una resolución
mínima; una portada de 100×150 píxeles se vuelve una mancha en la
pantalla.

```php title="app/Http/Requests/PortadaRequest.php" numbered
public function rules(): array
{
    return [
        'capa' => [
            'required',
            File::image()
                ->types(['jpg', 'png', 'webp'])
                ->max('10mb')
                ->dimensions(
                    Rule::dimensions()->minWidth(300)->minHeight(400),
                ),
        ],
    ];
}
```

`File` es la regla fluida de archivos de Laravel, en
`Illuminate\Validation\Rules\File`. Cada método agrega una condición, y la
respuesta trae un mensaje por cada una que falle:

```text
{"capa":["The capa field has invalid image dimensions."]}

{"capa":["The capa field must not be greater than 10000
kilobytes."]}
```

Fíjate en el "10000". El `'10mb'` se cuenta en múltiplos de mil: diez mil
kilobytes, no 10.240. La diferencia es pequeña y aparece justo en el
archivo de 10,1 MB que alguien jura que pesa menos de diez.

El campo se sigue llamando `capa` porque ese es el contrato con la
aplicación. Los mensajes están en inglés porque el proyecto todavía no
tiene traducción. El capítulo @cap:mail-e-notificacoes se ocupa de eso, y
de la misma causa en otro lugar.

:::pitfall
La foto del iPhone llega, a veces, en HEIC, un formato que el `types()` de
arriba rechaza y que la extensión de imágenes de PHP no lee. El navegador
del propio iPhone suele convertirla a JPEG al subirla; la aplicación, no
necesariamente. Acuérdalo con Kauã: la aplicación convierte antes de
enviar, y la API acepta solo lo que sabe procesar.
:::

## Disco privado, disco público

Laravel guarda archivos en **discos**, declarados en
`config/filesystems.php`. Un proyecto nuevo trae tres:

| Disco | Dónde graba | Quién lee |
|---|---|---|
| `local` | `storage/app/private` | solo el código |
| `public` | `storage/app/public` | el navegador, por un enlace |
| `s3` | un servicio de archivos en la nube | depende de la configuración |

Tabla: El disco por defecto es el `local`, y es privado a propósito.

El `public` queda visible en la web por un atajo que un comando crea una
vez por servidor:

```text
$ php artisan storage:link
```

Enlaza `public/storage` con `storage/app/public`. Una portada grabada en
`portadas/x.webp` en el disco `public` pasa a responder en
`/storage/portadas/x.webp`, y es el `url()` del disco el que arma esa
dirección:

```php title="app/Http/Resources/LibroResource.php" numbered
'portada_url' => $this->portada
    ? Storage::disk('public')->url($this->portada)
    : null,
```

La decisión es simple de enunciar: **lo que es para que cualquiera lo vea
va al `public`; el resto, al `local`**. La portada de *Vidas secas* es
pública. La foto original de Vera, de doce megabytes, no necesita serlo, y
el acta de donación firmada por don Juvenal, con CPF, no puede serlo.

Un archivo privado sale por una ruta, después de la policy:

```php title="app/Http/Controllers/ActaDeDonacionController.php" numbered
public function __invoke(Donacion $donacion)
{
    $this->authorize('view', $donacion);

    return Storage::disk('local')->download(
        $donacion->acta,
        "acta-{$donacion->id}.pdf",
    );
}
```

Cambiar de disco es una línea del `.env`. Cuando el acervo de portadas
crezca más allá del disco del servidor, `FILESYSTEM_DISK` y las
credenciales del `s3` cambian, y el código de arriba sigue igual: es
`Storage` haciendo por la subida lo que `DB` hizo por la base.

## Procesar después de responder

La foto de Vera necesita tres cosas antes de volverse portada: ponerse
derecha, achicarse y pasar a un formato liviano. Ninguna tiene que ocurrir
mientras el celular espera.

El controller guarda el original en el disco privado y le entrega el resto
a la cola:

```php title="app/Http/Controllers/PortadaController.php" numbered
public function __invoke(PortadaRequest $request, Libro $libro)
{
    $original = $request->file('capa')
        ->store('portadas/originales', 'local');

    PrepararPortada::dispatch($libro->id, $original);

    return response()->json(['situacion' => 'procesando'], 202);
}
```

`202 Accepted` es el status del capítulo @cap:o-que-e-uma-api-rest para
"lo recibí y todavía no terminé". La aplicación muestra la portada cuando
el `portada_url` del libro deja de ser `null`.

Y el job hace el trabajo con la extensión GD, que viene con la mayoría de
las instalaciones de PHP:

```php title="app/Jobs/PrepararPortada.php" numbered
public function handle(): void
{
    $libro = Libro::find($this->libroId);
    if ($libro === null) {
        return;
    }

    $ruta = Storage::disk('local')->path($this->original);

    $imagen = imagecreatefromstring(file_get_contents($ruta));
    $imagen = $this->enderezar($imagen, $ruta);
    $imagen = imagescale($imagen, 600);

    $destino = 'portadas/' . Str::uuid() . '.webp';
    Storage::disk('public')->put($destino, $this->enWebp($imagen));

    $this->cambiarPortada($libro, $destino);
    Storage::disk('local')->delete($this->original);
}
```

`imagescale($imagen, 600)` reduce el ancho a 600 píxeles y calcula el alto
en proporción. Una foto de 3000×4000 queda en 600×800, y doce megabytes se
vuelven unos sesenta kilobytes en WebP.

La nota "muéstrala parada" se llama **EXIF**: datos que la cámara graba
dentro del JPEG, entre ellos la orientación. Leerla y aplicarla:

```php title="app/Jobs/PrepararPortada.php (continuación)" numbered
private function enderezar(GdImage $imagen, string $ruta): GdImage
{
    if (mime_content_type($ruta) !== 'image/jpeg') {
        return $imagen;
    }

    $exif = exif_read_data($ruta) ?: [];
    $grados = match ($exif['Orientation'] ?? 1) {
        3 => 180,
        6 => -90,
        8 => 90,
        default => 0,
    };

    return $grados === 0 ? $imagen : imagerotate($imagen, $grados, 0);
}

private function enWebp(GdImage $imagen): string
{
    ob_start();
    imagewebp($imagen, null, 80);
    return (string) ob_get_clean();
}
```

El `if` del principio no es adorno. PNG y WebP no tienen EXIF, y
`exif_read_data` en un PNG emite un *warning* que, en Laravel, se vuelve
excepción, como hacía el `bootstrap.php` del capítulo @cap:erros-e-debug.
Sin el `if`, toda portada en PNG fallaría en la cola.

`imagewebp` escribe directo en la salida; `ob_start` y `ob_get_clean`
capturan esa salida en un string, que `Storage` graba donde diga el disco.

:::note
En proyectos con muchas imágenes, una biblioteca como Intervention Image
esconde GD detrás de una interfaz más corta, y resuelve la orientación con
un método. Para una portada por libro, las veinte líneas de arriba bastan,
y sabes qué hace cada una.
:::

## Cambiar sin dejar huérfanos

Cuando Vera vuelve a sacar la foto de *El conventillo*, la portada nueva
entra y la vieja tiene que salir. El orden importa, porque la base y el
disco no participan de la misma transacción:

```php title="app/Jobs/PrepararPortada.php (continuación)" numbered
private function cambiarPortada(Libro $libro, string $nueva): void
{
    $vieja = $libro->portada;

    try {
        $libro->update(['portada' => $nueva]);
    } catch (Throwable $e) {
        Storage::disk('public')->delete($nueva);
        throw $e;
    }

    if ($vieja !== null) {
        Storage::disk('public')->delete($vieja);
    }
}
```

**Primero el archivo nuevo, después la base, por último el archivo
viejo.** Si el `update` falla, el archivo nuevo se borra y el libro sigue
con la portada vieja, entera. Si falla el `delete` de la vieja, sobra un
archivo sin dueño: un desperdicio de espacio, y no un libro sin portada.

Es el "graba en un temporal y renombra al final" del capítulo
@cap:manipulacao-de-arquivos, ahora con una base en medio: en ningún
instante el sistema muestra una portada a medias ni apunta a un archivo que
no existe.

:::key
Cuando una operación toca la base y el disco, ordena los pasos para que la
falla en cualquiera de ellos deje **sobrante**, nunca **faltante**. Lo que
sobra se limpia después, con un comando programado que compara el disco
con la tabla. Lo que falta es la portada rota en la pantalla del lector.
:::

## Probar sin disco y sin cola

`Storage::fake` cambia un disco por una carpeta temporal, que desaparece al
final de la prueba. `UploadedFile::fake()->image()` fabrica una imagen de
verdad, con las dimensiones pedidas:

```php title="tests/Feature/PortadaTest.php" numbered
test('acepta la portada y deja el trabajo a la cola', function () {
    Storage::fake('local');
    Queue::fake();
    $libro = Libro::factory()->create();

    $this->actingAs(Usuario::factory()->encargado()->create())
        ->postJson("/api/libros/{$libro->id}/portada", [
            'capa' => UploadedFile::fake()
                ->image('capa.jpg', 800, 1200),
        ])
        ->assertStatus(202);

    Queue::assertPushed(PrepararPortada::class);
    expect(Storage::disk('local')->allFiles('portadas/originales'))
        ->toHaveCount(1);
});

test('prepara la portada en webp con 600 de ancho', function () {
    Storage::fake('local');
    Storage::fake('public');
    $libro = Libro::factory()->create();
    $original = UploadedFile::fake()->image('capa.jpg', 800, 1200)
        ->store('portadas/originales', 'local');

    (new PrepararPortada($libro->id, $original))->handle();

    $portada = Storage::disk('public')->get($libro->fresh()->portada);
    [$ancho, $alto] = getimagesizefromstring($portada);

    expect([$ancho, $alto])->toBe([600, 900]);
    Storage::disk('local')->assertMissing($original);
});
```

La primera prueba demuestra el contrato: `202`, original guardado, job en
la cola. La segunda llama al `handle` directamente y demuestra el trabajo:
ancho 600, alto en proporción, original borrado. Ninguna de las dos graba
nada en el disco de verdad, y las dos corren en menos de un segundo.

`UploadedFile::fake()->image()` necesita la extensión GD en el PHP que
corre las pruebas, la misma que usa el job. Si la cadena del capítulo
@cap:git-ci-e-deploy no la tiene, la prueba falla con un mensaje que lo
dice.

:::note En tu carrera
El archivo que sube un usuario es el dato que más crece y el que menos
gente se acuerda de copiar. El backup de la base corre todas las noches;
la carpeta `storage/app` queda afuera porque "son solo imágenes".

El día en que muera el disco del servidor, las cuatro mil portadas de Vera
desaparecen, y cada una costó una foto sobre una cartulina. Pregunta, el
mismo día en que la primera subida vaya a producción: **¿quién copia
`storage/`, y adónde?** Si la respuesta es el `s3`, la pregunta pasa a ser
"¿quién copia el `s3`?".
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/
    Http/Controllers/
      PortadaController.php          # 202: guarda y encola
      ActaDeDonacionController.php   # descarga privada, con policy
    Http/Requests/PortadaRequest.php # tipo, tamaño, dimensiones
    Jobs/PrepararPortada.php         # EXIF, 600px, WebP, cambio
  storage/app/
    private/portadas/originales/     # lo que envió Vera
    public/portadas/                 # lo que ve el lector
:::

:::summary
- El servidor web, `upload_max_filesize` y `post_max_size` frenan antes de
  Laravel. Configúralos con holgura; el límite real va en la validación.
- `File::image()->types()->max()->dimensions()` valida por el contenido;
  `'10mb'` son diez mil kilobytes.
- El disco `local` es privado; el `public` aparece en la web por el
  `storage:link`. Un archivo sensible sale por una ruta, después de la
  policy.
- Guarda el original, responde `202` y procesa en la cola.
- La foto de celular trae la orientación en el EXIF; aplícala antes de
  achicar.
- Cambia archivos en el orden nuevo → base → viejo: la falla deja
  sobrantes, nunca faltantes.
- `Storage::fake` y `UploadedFile::fake()->image()` prueban sin disco.
:::

:::checkpoint
Configuras los límites de subida del servidor a Laravel, validas la imagen
por tipo, tamaño y dimensión, eliges entre disco privado y público,
procesas la imagen en una cola, cambias archivos sin dejar un libro sin
portada, y pruebas el camino entero sin tocar el disco.
:::

:::exercise level=1
Para cada síntoma, di qué portero frenó y qué cambiar:

1. La aplicación recibe una página HTML con "413 Request Entity Too
   Large".
2. La API responde `422` con *"The capa failed to upload."*.
3. La API responde `413` en JSON, y los demás campos del formulario
   también desaparecieron.

:::answer
1. nginx, con `client_max_body_size`. PHP ni vio el pedido.
2. PHP, con `upload_max_filesize`. El cuerpo llegó, el archivo se
   descartó, y Laravel avisó que no subió.
3. PHP, con `post_max_size`. Se descartó el cuerpo entero —por eso
   desaparecieron los demás campos—, y Laravel respondió con
   `PostTooLargeException`.
:::

:::exercise level=2
El acta de donación es un PDF de hasta 5 MB. Escribe la regla de
validación y di en qué disco queda y por qué. Después, escribe la prueba
que demuestra que un lector común recibe `403` al intentar descargarla.

:::answer
```php
'acta' => ['required', File::types(['pdf'])->max('5mb')],
```

Disco `local`: el acta tiene nombre, dirección y CPF. Sale solo por la
ruta del `ActaDeDonacionController`, después de la policy.

```php
test('un lector común no descarga el acta de donación', function () {
    Storage::fake('local');
    $donacion = Donacion::factory()->create([
        'acta' => UploadedFile::fake()
            ->create('acta.pdf', 100, 'application/pdf')
            ->store('actas', 'local'),
    ]);

    $this->actingAs(Usuario::factory()->lector()->create())
        ->get("/api/donaciones/{$donacion->id}/acta")
        ->assertForbidden();
});
```
:::

:::exercise level=3
Seis meses después, el disco del servidor está ocupado al 70%, y la
carpeta `storage/app/public/portadas` tiene 11.000 archivos para 4.000
libros. Explica de dónde vinieron los 7.000 de más, y diseña el comando
programado que los limpia sin ningún riesgo de borrar una portada en uso.

:::answer
Vinieron de los sobrantes que acepta el orden nuevo → base → viejo: un
`delete` del archivo viejo que falló, jobs que grabaron la portada y se
cayeron antes del `update`, portadas cambiadas varias veces durante las
pruebas de Vera.

El comando, `portadas:limpiar`, programado una vez por semana:

1. Lista los archivos de `portadas/` en el disco `public`.
2. Lista los valores de la columna `portada` de `libros`.
3. Borra los archivos que están en el primer conjunto y no en el segundo,
   y **solo los modificados hace más de un día**, para no borrar la
   portada que un job acaba de grabar y todavía no registró en la base.
4. Registra en el log cuántos borró.

La regla del paso 3 es lo que hace seguro el comando: nunca compite con un
`PrepararPortada` en curso. Antes de correrlo de verdad, una opción
`--simular` que solo lista lo que se borraría es el tipo de cuidado que
Vera nunca va a saber que existió.
:::
