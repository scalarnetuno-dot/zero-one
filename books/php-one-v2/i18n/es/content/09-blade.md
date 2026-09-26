---
source_hash: 5f8758badba3
title: "Blade, cuando la pantalla todavía es la respuesta"
number: 9
slug: blade
part: p2
kicker: "Vera no quiere una aplicación. Quiere un campo de búsqueda y un botón, como el del Sistema, que funcionaba."
goal: >-
  Entregar el panel que usa la bibliotecaria en el mostrador —listado,
  formulario y acción— entendiendo el escape automático, el token del
  formulario y dónde queda el límite entre Blade y un front-end de verdad.
---

:::story Un campo y un botón
El Dr. Aurélio presentó la aplicación del lector en la reunión del martes,
con las pantallas en el proyector, y le preguntó a Vera qué le parecía.

—Linda. ¿Dónde presto?

—El préstamo está aquí, mire. El lector la abre en su celular y...

—No. Yo. En el mostrador. Con la persona delante y el libro en la mano.

Silencio de quien no había pensado en eso.

—Podemos hacer una pantalla.

—Es la que uso hoy —dijo Vera—. Un campo, escribo el número de registro,
aprieto el botón, presto. Tarda cuatro segundos.

—¿La del Sistema?

—La del Sistema. Esa funcionaba.
:::

## No todo es API

Una aplicación tiene sentido para quien consulta el acervo desde el sofá.
No tiene ninguno para quien está de pie, detrás de un mostrador, con fila.

El panel de Vera tiene tres pantallas, y el resto del libro sigue siendo
API. Esta es la única parte web, y existe porque el cliente real del
sistema trabaja en una computadora que ya está encendida sobre la mesa.

:::key
La pregunta que decide entre pantalla y API no es "¿qué es más moderno?".
Es: **¿quién usa esto, en qué situación?**

Fila en el mostrador, cuatro segundos por atención y teclado piden un
formulario. El lector en el colectivo, que quiere saber si el libro
volvió, pide una aplicación. El mismo sistema atiende a los dos, y ninguno
de los dos atiende a los dos.
:::

:::art caption="La aplicación era linda. Vera quería un campo y un botón."
src="o-aplicativo-era-bonito-a-vera-queria-um-campo-e-um-botao.png"
Viñeta editorial minimalista sobre fondo blanco: en una sala de reuniones,
un proyector muestra en la pared una aplicación de celular gigante y
colorida, llena de íconos, tarjetas y degradados. Un director de traje
señala la proyección con orgullo. En primer plano, de espaldas a la pared,
una bibliotecaria mayor, con lentes, está detrás de un mostrador de madera
con un libro en la mano y un lector esperando delante, mirando un monitor
antiguo que muestra solo un campo de texto y un botón. Pocos elementos,
humor seco, estética de revista de tecnología.
:::

## Blade es PHP con menos ceremonia

Una vista es un archivo en `resources/views/` con la extensión
`.blade.php`. El controller arma los datos y elige la vista:

```php title="app/Http/Controllers/PanelController.php" numbered
public function index(Request $request)
{
    $prestamos = Prestamo::abiertos()
        ->conLibroYLector()
        ->orderBy('devolver_hasta')
        ->get();

    return view('panel.index', [
        'prestamos' => $prestamos,
        'hoy' => now(),
    ]);
}
```

```blade title="resources/views/panel/index.blade.php" numbered
<h1>Préstamos abiertos</h1>

<table>
    @forelse ($prestamos as $prestamo)
        <tr>
            <td>{{ $prestamo->ejemplar->registro }}</td>
            <td>{{ $prestamo->ejemplar->libro->titulo }}</td>
            <td>{{ $prestamo->lector->nombre }}</td>
            <td>{{ $prestamo->devolver_hasta->format('d/m/Y') }}</td>
        </tr>
    @empty
        <tr><td colspan="4">Nada prestado ahora.</td></tr>
    @endforelse
</table>
```

`@forelse` es un `foreach` con un caso menos para olvidar: ya trae el
`@empty` para la lista vacía. Sin él, la pantalla de una biblioteca sin
préstamos sería una tabla sin ninguna fila y sin ninguna explicación.

Las directivas que cubren casi todo:

| Blade | PHP |
|---|---|
| `{{ $x }}` | `echo e($x)` |
| `@if` / `@else` / `@endif` | `if` / `else` |
| `@foreach` / `@endforeach` | `foreach` |
| `@forelse` / `@empty` | `foreach` con prueba de vacío |
| `@php ... @endphp` | un bloque de PHP puro |

Tabla: El último existe, es legítimo en casos raros y suele ser la señal de
que la cuenta debería haberse hecho en el controller.

## `{{ }}` escapa, y ese es el recurso

Supón que alguien registra un libro con este título:

```text
<script>alert('hola')</script>
```

```blade
<td>{{ $libro->titulo }}</td>
```

```text
<td>&lt;script&gt;alert('hola')&lt;/script&gt;</td>
```

El navegador muestra el texto y no ejecuta nada. `{{ }}` convierte los
caracteres que tendrían significado en HTML antes de imprimir: es lo que
impide que el campo de un formulario se vuelva código en la pantalla de
otra persona.

Y existe la otra forma:

```blade
<td>{!! $libro->titulo !!}</td>
```

```text
<td><script>alert('hola')</script></td>
```

:::pitfall
`{!! !!}` no es "la versión que no rompe el HTML". Es una decisión de
seguridad, y la pregunta que obliga a hacer es una sola: **¿quién escribió
ese contenido?**

Si la respuesta incluye "un usuario", la respuesta correcta es `{{ }}`. Si
de verdad hace falta imprimir HTML que viene de fuera —un editor de texto
enriquecido, por ejemplo—, el contenido tiene que pasar antes por una
limpieza que quite lo que no está permitido, y eso es una biblioteca, no
una decisión de llaves.

El ataque tiene nombre, XSS, y su formato más común es exactamente este: un
campo de registro que nadie miró, impreso en una pantalla que abre otra
persona.
:::

## Layout y componente

Tres pantallas ya repiten cabecera, pie y menú. La forma moderna de
resolverlo en Blade es un componente de layout:

```blade title="resources/views/components/layout.blade.php" numbered
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>{{ $titulo ?? 'Casa Amarela' }}</title>
</head>
<body>
    <header>
        <strong>Biblioteca Casa Amarela</strong>
        <nav>
            <a href="{{ route('panel.index') }}">Préstamos</a>
            <a href="{{ route('panel.acervo') }}">Acervo</a>
        </nav>
    </header>

    <main>
        {{ $slot }}
    </main>
</body>
</html>
```

```blade title="resources/views/panel/index.blade.php" numbered
<x-layout titulo="Préstamos abiertos">
    <h1>Préstamos abiertos</h1>

    <table>
        ...
    </table>
</x-layout>
```

El archivo en `components/` se vuelve la etiqueta `<x-layout>`. Lo que
esté dentro de la etiqueta llega en `$slot`; lo que se escriba como
atributo llega como variable.

:::key
Existe también el `@include('parciales.menu')`, más antiguo, y envejece
mal por un motivo específico: el archivo incluido ve **todas** las
variables de quien lo incluyó.

Eso funciona hasta el día en que dos pantallas incluyen el mismo parcial y
una de ellas no tiene la variable que usa el parcial. El error aparece en
la pantalla, y la causa está en otro archivo.

El componente declara lo que recibe. Es la misma diferencia entre el array
y la clase del capítulo @cap:classes-e-objetos, ahora en HTML.
:::

## El formulario y el token que no ves

La pantalla que pidió Vera:

```blade title="resources/views/panel/prestar.blade.php" numbered
<x-layout titulo="Prestar">
    <form method="POST" action="{{ route('panel.prestar') }}">
        @csrf

        <label for="registro">Registro</label>
        <input id="registro" name="registro"
               value="{{ old('registro') }}" autofocus>

        @error('registro')
            <p class="error">{{ $message }}</p>
        @enderror

        <label for="documento">Documento del lector</label>
        <input id="documento" name="documento"
               value="{{ old('documento') }}">

        @error('documento')
            <p class="error">{{ $message }}</p>
        @enderror

        <button>Prestar</button>
    </form>
</x-layout>
```

Tres directivas hacen el trabajo aburrido.

**`@csrf`** inserta un campo oculto con un token. Cuando el formulario
vuelve, Laravel revisa si el token coincide con el de la sesión, y lo
rechaza si no coincide.

:::term CSRF
*Cross-Site Request Forgery*: un sitio cualquiera, abierto en otra pestaña,
arma un formulario que apunta a **tu** sistema y hace que el navegador lo
envíe. Como el navegador manda las cookies de sesión junto, el pedido
llega autenticado.

El token lo resuelve porque el sitio de afuera no tiene cómo saber cuál es.
Por eso existe en `web.php` y no existe en `api.php`: sin sesión en una
cookie, no hay nada que falsificar.
:::

**`old('registro')`** devuelve lo que la persona había escrito antes de que
se rechazara el formulario. Sin eso, un error de validación borra lo
completado, y Vera escribe todo de nuevo, con la fila esperando.

**`@error('registro')`** solo imprime cuando hay un error en ese campo.

Y el controller del otro lado:

```php title="app/Http/Controllers/PanelController.php" numbered
public function prestar(
    Request $request,
    RegistroDePrestamo $prestamos,
) {
    $datos = $request->validate([
        'registro' => ['required', 'integer'],
        'documento' => ['required', 'string'],
    ]);

    try {
        $prestamos->registrarPorRegistro(
            $datos['registro'],
            $datos['documento'],
        );
    } catch (EjemplarNoDisponible $e) {
        return back()
            ->withInput()
            ->withErrors(['registro' => $e->getMessage()]);
    }

    return redirect()
        ->route('panel.prestar')
        ->with('exito', 'Prestado.');
}
```

`back()->withInput()` devuelve a la persona al formulario con lo que
escribió, y es lo que alimenta el `old()`. El `redirect()` en el camino del
éxito existe para que recargar la página no preste el mismo libro otra vez:
el navegador reenviaría el `POST`.

:::key
Esa dupla —redirigir después de grabar, devolver con los datos después de
rechazar— es la base de toda pantalla de formulario. Resuelve el "recargar
la página duplicó el registro" sin ninguna astucia.

Es la pariente pobre de la idempotencia del capítulo
@cap:o-que-e-uma-api-rest, y resuelve el mismo problema: alguien apretó dos
veces.
:::

## Cuándo detenerse

Blade entrega pantallas renderizadas en el servidor. Eso cubre listados,
formularios, filtros e informes: lo que es casi todo panel administrativo.

Deja de ser la herramienta correcta cuando la pantalla tiene que cambiar
**sin recargar**: arrastrar ítems, actualizarse sola, editar en varias
pestañas al mismo tiempo.

| La pantalla necesita | Blade lo resuelve |
|---|---|
| listar, filtrar, paginar | sí |
| formulario con validación | sí |
| informe e impresión | sí |
| un fragmento que se actualiza solo | con ayuda |
| una interfaz que no recarga | no |

Tabla: La columna del medio tiene una franja gris, y ahí vive la decisión
de arquitectura de la mayoría de los proyectos.

:::pitfall
El peor lugar donde estar es el medio: un Blade lleno de JavaScript que
arma pedazos de la pantalla y conversa con la API, pero que no es una
aplicación de front-end ni una pantalla del servidor.

Terminas con dos lugares que saben armar la misma lista, dos copias de la
regla de visualización y ninguna de las ventajas de los dos lados.

La decisión honesta es elegir por pantalla: esta la sirve el servidor,
aquella es una aplicación de front-end que consume la API. Las dos
conviven en el mismo proyecto sin problema; lo que no convive es la mezcla
dentro de una.
:::

:::note En tu carrera
Vera no pidió una pantalla por conservadurismo. La pidió porque mide su
trabajo en segundos por atención, y nadie en el proyecto tenía esa unidad
en la cabeza.

Vale la pena llevar eso a cualquier relevamiento de requisitos: **pregunta
cuántas veces por día hace eso la persona**. La respuesta cambia la
decisión técnica más que cualquier preferencia de arquitectura: una
operación hecha seiscientas veces por día justifica una pantalla dedicada,
y una hecha tres veces por mes no justifica ni un botón.

Es también el argumento que funciona cuando tengas que defender la elección
en una reunión en la que alguien quiere todo en la aplicación.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  resources/views/
    components/
      layout.blade.php      # <x-layout>
    panel/
      index.blade.php       # préstamos abiertos
      prestar.blade.php     # el campo y el botón
      acervo.blade.php
  routes/
    web.php                 # el panel, con sesión y CSRF
    api.php                 # la aplicación del lector
:::

:::milestone
Fin de la Parte 2. Laravel está funcionando, configurado, con las rutas
diseñadas registradas, controllers que traducen en lugar de decidir, y la
pantalla que la bibliotecaria va a usar en el mostrador. Lo que falta ahora
es lo que está detrás de ella: los datos.
:::

:::summary
- Pantalla y API atienden situaciones distintas; la pregunta es quién usa y
  en qué situación.
- Una vista es un archivo `.blade.php`; el controller arma los datos y
  elige.
- `@forelse` trae junto el caso de la lista vacía.
- `{{ }}` escapa el contenido y es lo que impide el XSS; `{!! !!}` es una
  decisión de seguridad, no de formato.
- El componente declara lo que recibe; `@include` ve todo de quien lo
  incluyó.
- `@csrf` protege el formulario de sesión; en una API no tiene sentido
  porque no hay cookie que falsificar.
- `old()` y `@error` devuelven el formulario completado después de un
  rechazo.
- Redirigir después de grabar impide que recargar la página repita la
  operación.
- Blade cubre listados, formularios e informes; una interfaz que no recarga
  es otro trabajo, y mezclar los dos es lo peor de ambos mundos.
:::

:::checkpoint
Entregas una pantalla funcional con listado y formulario, explicas qué hace
`{{ }}` y por qué `{!! !!}` es una decisión, sabes por qué el token del
formulario existe en el panel y no en la API, y puedes defender por qué el
resto del libro sigue siendo API.
:::

:::exercise level=1
Di qué está mal en cada línea de Blade:

```blade
<td>{!! $lector->nombre !!}</td>
```

```blade
<form method="POST" action="/panel/prestar">
    <input name="registro">
    <button>Prestar</button>
</form>
```

```blade
@php
    $total = 0;
    foreach ($prestamos as $p) {
        $total += $p->multa->centavos();
    }
@endphp
```

:::answer
**La primera** imprime sin escapar un dato registrado por una persona. El
nombre de un lector puede contener `<` y `>` por error, o a propósito. Es
`{{ }}`.

**La segunda** no tiene `@csrf`. El formulario va a ser rechazado con
`419`, y —peor que no funcionar— si alguien desactiva la protección para
"resolverlo", la ruta queda abierta a envíos de afuera.

También vale cambiar la ruta fija por `{{ route('panel.prestar') }}`, por
el motivo del capítulo anterior.

**La tercera** es una cuenta en la vista. Funciona y vive en el lugar
equivocado: no tiene prueba, no la puede reutilizar la API y obliga a quien
toque el cálculo de la multa a acordarse de un archivo `.blade.php`.

El total viene listo del controller, o del propio objeto que ya sabe sumar
`Dinero`.
:::

:::exercise level=2
Escribe la pantalla de devolución: un campo para el registro, un selector
con los estados posibles del ejemplar y un botón.

El selector debe armarse a partir del enum `EstadoEjemplar`, sin repetir la
lista en el HTML.

:::answer
```blade title="resources/views/panel/devolver.blade.php" numbered
<x-layout titulo="Devolver">
    <form method="POST" action="{{ route('panel.devolver') }}">
        @csrf

        <label for="registro">Registro</label>
        <input id="registro" name="registro"
               value="{{ old('registro') }}" autofocus>

        @error('registro')
            <p class="error">{{ $message }}</p>
        @enderror

        <label for="estado">Estado al volver</label>
        <select id="estado" name="estado">
            @foreach ($estados as $estado)
                <option value="{{ $estado->value }}"
                    @selected(old('estado') === $estado->value)>
                    {{ $estado->etiqueta() }}
                </option>
            @endforeach
        </select>

        <button>Devolver</button>
    </form>
</x-layout>
```

```php
return view('panel.devolver', [
    'estados' => EstadoEjemplar::devolucion(),
]);
```

Tres decisiones.

El `value` del `<option>` es `$estado->value` y el texto es
`$estado->etiqueta()`: exactamente la separación del capítulo
@cap:enums-datas-e-valores entre lo que va al sistema y lo que lee la
persona.

El `@selected` es azúcar para el atributo `selected`; existe para que el
`old()` funcione también en el selector, y no solo en los campos de texto.

Y la lista no es `EstadoEjemplar::cases()`: es un método que devuelve solo
los estados que tienen sentido en una devolución. `prestado` no es uno de
ellos, y dejar el `cases()` crudo le ofrecería a Vera una opción que el
servicio va a rechazar.
:::

:::exercise level=3
El panel creció: siete pantallas, y cada una tiene el mismo bloque de
búsqueda por registro arriba. El código se copió siete veces.

Recibes dos propuestas: convertir el bloque en un `@include`, o en un
componente. Elige, escribe la implementación y explica qué le pasaría a la
otra opción dentro de seis meses.

:::answer
**Componente**, y el archivo es anónimo: no necesita clase.

```blade title="resources/views/components/busqueda-por-registro.blade.php"
@props(['accion', 'etiqueta' => 'Registro', 'valor' => null])

<form method="GET" action="{{ $accion }}" class="busqueda">
    <label for="registro">{{ $etiqueta }}</label>
    <input id="registro" name="registro"
           value="{{ $valor ?? request('registro') }}" autofocus>
    <button>Buscar</button>
</form>
```

```blade
<x-busqueda-por-registro :accion="route('panel.acervo')" />

<x-busqueda-por-registro :accion="route('panel.prestar')"
                         etiqueta="Registro para prestar" />
```

`@props` declara lo que acepta el componente y el valor predeterminado de
cada cosa. Es su firma, y Blade avisa cuando falta lo obligatorio.

**Lo que le pasaría al `@include`.** Funcionaría hoy, porque las siete
pantallas por casualidad tienen las variables correctas en el ámbito. El
problema llega en la octava.

Alguien crea una pantalla nueva, incluye el parcial, y este usa `$accion`,
que en esa pantalla no existe. El error aparece en el renderizado,
señalando el archivo del parcial, y quien investigue va a mirar un archivo
que está correcto hace seis meses.

Después de eso, el camino común es que el parcial reciba un `?? ''` para no
romperse, y ahí el formulario pasa a apuntar a ninguna parte en silencio.
Es el mismo recorrido del `function_exists` del capítulo
@cap:do-include-ao-composer: el parche borra el aviso y mantiene el
defecto.
:::
