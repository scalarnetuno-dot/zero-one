---
source_hash: 1a91b0c145c5
title: "Probando services"
number: 35
part: p8
kicker: "Para probar la regla, la base tiene que salir del camino, y alguien tiene que hacerse pasar por ella."
goal: >-
  Aislar el servicio con Mockito, verificar llamadas con `verify` y
  reconocer cuándo un mock dejó de ayudar y pasó a probarse a sí mismo.
---

El `ProductService` del capítulo 22 depende del `ProductRepository`.
Probarlo con una base de verdad es lento y frágil; probarlo sin nada es
imposible. La salida es entregarle un repositorio **falso**, que hace lo que
la prueba le mande.

Y eso solo es posible por una decisión del capítulo 15: la inyección por
constructor.

## El mock

```java title="ProductServiceTest.java" numbered
@ExtendWith(MockitoExtension.class)
class ProductServiceTest {

    @Mock
    ProductRepository repository;

    @InjectMocks
    ProductService service;

    @Test
    void debeLanzarCuandoElProductoNoExiste() {
        when(repository.findById(99L))
                .thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.buscar(99L))
                .isInstanceOf(ProductNotFoundException.class)
                .hasMessageContaining("99");
    }
}
```

:::anatomy title="Las cuatro piezas de una prueba con mock"
lang: java
code: |
  @ExtendWith(MockitoExtension.class)
  class ProductServiceTest {

      @Mock
      ProductRepository repository;

      @InjectMocks
      ProductService service;

      @Test
      void debeLanzarCuandoNoExiste() {
          when(repository.findById(99L))
                  .thenReturn(Optional.empty());
          ...
      }
  }
notes:
  - { line: 1, text: "La extensión de Mockito procesa las anotaciones. No se carga ningún Spring." }
  - { line: 4, text: "`@Mock` crea un doble: todo método devuelve vacío o nulo hasta que le enseñes." }
  - { line: 7, text: "`@InjectMocks` arma el servicio con los mocks, por el constructor." }
  - { line: 12, text: "`when(...).thenReturn(...)` le enseña al doble a responder en ese caso." }
:::

:::key
Fíjate en lo que esta prueba **no** hace: no levanta Spring, no abre una
conexión, no toca una base. Corre en milisegundos y prueba exactamente una
cosa: que el servicio convierte "no lo encontré" en
`ProductNotFoundException`.
:::

## Verificando lo que se llamó

```java title="A veces lo que importa es el efecto" numbered
@Test
void debeGuardarProductoNuevo() {
    var datos = new ProductRequest("Teclado", null,
            new BigDecimal("349.90"), 12);

    when(repository.existsByNameIgnoreCase("Teclado"))
            .thenReturn(false);
    when(repository.save(any(Product.class)))
            .thenAnswer(inv -> inv.getArgument(0));

    service.crear(datos);

    ArgumentCaptor<Product> captor =
            ArgumentCaptor.forClass(Product.class);
    verify(repository).save(captor.capture());

    assertThat(captor.getValue().getName())
            .isEqualTo("Teclado");
    assertThat(captor.getValue().getStatus())
            .isEqualTo(Status.ACTIVO);
}
```

El `ArgumentCaptor` guarda el objeto que el servicio le pasó al repositorio:
es cómo verificas **qué** se guardaría sin guardar nada.

```java title="Y lo que no debe pasar" numbered
@Test
void noDebeGuardarCuandoElNombreEstaDuplicado() {
    when(repository.existsByNameIgnoreCase("Teclado"))
            .thenReturn(true);

    assertThatThrownBy(() -> service.crear(datos))
            .isInstanceOf(DuplicateProductException.class);

    verify(repository, never()).save(any());
}
```

`verify(..., never())` suele valer más que el `assert`: demuestra que la
operación se **abortó antes** de tocar la base.

## El vocabulario mínimo de Mockito

| Comando | Para qué |
|---|---|
| `when(x).thenReturn(y)` | enseña la respuesta |
| `when(x).thenThrow(e)` | enseña a fallar |
| `verify(mock).metodo()` | confirma que se llamó |
| `verify(mock, never())` | confirma que **no** se llamó |
| `verify(mock, times(2))` | confirma cuántas veces |
| `any()`, `eq(valor)` | hace coincidir argumentos |
| `ArgumentCaptor` | captura lo que se pasó |

Tabla: Siete construcciones resuelven el 95% de las pruebas de servicio.

:::pitfall
`when(repository.save(any()))` sin `thenReturn` devuelve `null`. Si el
servicio usa el retorno (`return repository.save(p).getId()`), la prueba
falla con `NullPointerException`, y la culpa no es del código, es del mock
mal enseñado. Cuando el retorno importa, usa
`thenAnswer(inv -> inv.getArgument(0))` para devolver el propio objeto.
:::

## Cuándo el mock empieza a estorbar

:::story La prueba que probaba el mock
La prueba tenía noventa líneas y siete mocks.

Verificaba que el servicio llamaba al repositorio, que llamaba al mapeador,
que llamaba al validador, que llamaba al publicador de eventos, cada uno
enseñado a responder exactamente lo que el servicio esperaba.

Pasaba siempre. Pasó incluso la semana en que el cálculo del total del
pedido estaba mal por un centavo, porque el mock del mapeador devolvía un
valor fijo que nadie había actualizado.

—Esta prueba no prueba el servicio —dijo Marina, en la revisión—. Prueba mi
capacidad de prever lo que el servicio va a llamar. Si cambio el orden de las
llamadas sin cambiar el resultado, se rompe. Si rompo el resultado sin
cambiar el orden, pasa.

Carlos preguntó qué hacer.

—Cuando la prueba tiene más mocks que afirmaciones, el problema no es la
prueba. Es la clase, que depende de demasiadas cosas.

El `OrderService` se volvió dos: uno que calcula y no depende de nada, y
otro que orquesta. El primero ganó doce pruebas sin ningún mock. El segundo
se quedó con dos.
:::

:::art caption="Cuando la prueba tiene más dobles que actores, se volvió un ensayo."
src="quando-o-teste-tem-mais-dubles-que-atores-ele-virou-ensaio.png"
Charge editorial minimalista: palco de teatro visto de frente, com um único
ator real no centro e sete manequins de madeira posicionados ao redor, cada
um com uma plaquinha pendurada no pescoço: "repositório", "mapeador",
"validador". Na plateia, uma única pessoa aplaude com cara de dúvida. Fundo
branco, poucos elementos, humor visual seco, estética editorial de
tecnologia.
:::

:::pitfall
Tres señales de que el mock se volvió el problema: la prueba tiene más
líneas de `when` que de `assertThat`; la prueba se rompe cuando refactorizas
sin cambiar el comportamiento; la prueba pasa cuando el resultado está mal.
Cualquiera de las tres es un pedido para dividir la clase.
:::

## La alternativa: el doble escrito a mano

```java title="Un repositorio falso, de verdad" numbered
class InMemoryProductRepository implements ProductRepository {

    private final Map<Long, Product> datos = new HashMap<>();
    private long secuencia = 0;

    @Override
    public <S extends Product> S save(S p) {
        if (p.getId() == null) {
            p.setId(++secuencia);
        }
        datos.put(p.getId(), p);
        return p;
    }

    @Override
    public Optional<Product> findById(Long id) {
        return Optional.ofNullable(datos.get(id));
    }

    // ... el resto de la interfaz
}
```

Este es exactamente el `Map` del capítulo 8, ahora cumpliendo un contrato.
Su ventaja sobre el mock es que **se comporta**: guardar y después buscar
devuelve lo que se guardó, sin que nadie se lo enseñe. La desventaja es que
`JpaRepository` tiene decenas de métodos para implementar.

:::tip
El término medio práctico: declara una interfaz más pequeña, solo con los
métodos que usa el servicio (`ProductGateway`, con cuatro métodos), y haz que
`ProductRepository` la extienda. La prueba implementa la interfaz pequeña;
producción usa Spring Data. Es la lección del capítulo 11 —depende del
contrato— aplicada a la prueba.
:::

:::summary
- La inyección por constructor es lo que hace que el servicio se pueda
  probar sin framework.
- `@Mock` + `@InjectMocks` arman el escenario; `when` enseña; `verify`
  confirma.
- `verify(never())` demuestra que la operación se abortó antes de la base.
- Demasiados mocks prueban la previsión del autor, no el comportamiento.
- Un doble escrito a mano se comporta; un mock solo responde.
:::

:::checkpoint
Aíslas el servicio con Mockito, enseñas respuestas, capturas argumentos,
verificas la ausencia de una llamada y reconoces cuándo el exceso de mocks
es síntoma de una clase que hace demasiado.
:::

:::milestone
Las reglas de negocio del proyecto tienen pruebas rápidas e independientes
de la infraestructura. Falta demostrar que el HTTP —ruta, estado y JSON—
sigue siendo lo acordado.
:::

:::exercise level=1
Escribe la prueba de `borrar` verificando que el repositorio recibió
`delete` con el producto correcto.

:::answer
```java
when(repository.findById(1L))
        .thenReturn(Optional.of(producto));

service.borrar(1L);

verify(repository).delete(producto);
```
:::

:::exercise level=2
Prueba `descontarStock` para el caso de stock insuficiente. Verifica la
excepción **y** que no se guardó nada.

:::answer
La segunda verificación es la que importa: sin ella, la prueba pasaría aun
si el servicio lanzara la excepción **después** de grabar el descuento. La
excepción correcta con el efecto secundario equivocado es un defecto que
solo aparece en producción.
:::

:::exercise level=3
Toma una prueba tuya con cuatro o más mocks e intenta reescribirla
dividiendo la clase probada. Compara el antes y el después.

:::answer
En la mayoría de los casos aparece una clase pura —de cálculo, de decisión,
de transformación— que no depende de nada y gana pruebas triviales. Lo que
queda en la clase original es orquestación, y la orquestación se prueba con
pocos `verify`. La calidad de la prueba es un termómetro del diseño del
código: una prueba difícil casi nunca es un problema de la prueba.
:::
