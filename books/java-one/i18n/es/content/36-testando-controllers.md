---
source_hash: 46329bbf1b5f
title: "Probando controladores"
number: 36
part: p8
kicker: "El contrato HTTP es la única parte del sistema de la que depende otra persona. Es la que más merece una prueba."
goal: >-
  Probar endpoints con MockMvc, verificar estado, cabecera y JSON, y simular
  un usuario autenticado sin iniciar sesión.
---

La prueba del capítulo 35 demostró que la regla funciona. No demuestra nada
sobre la ruta, el verbo, el estado o el formato del JSON, y eso es
exactamente lo que ve el cliente.

## MockMvc: HTTP sin red

```java title="ProductControllerTest.java" numbered
@WebMvcTest(ProductController.class)
class ProductControllerTest {

    @Autowired
    MockMvc mvc;

    @MockitoBean
    ProductService service;

    @Test
    void debeDevolver200YElProductoCuandoExiste() throws Exception {
        when(service.buscar(1L)).thenReturn(
                new ProductResponse(1L, "Teclado", null,
                        new BigDecimal("349.90"), 12,
                        Status.ACTIVO, Instant.now()));

        mvc.perform(get("/products/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.name").value("Teclado"))
                .andExpect(jsonPath("$.price").value(349.90));
    }
}
```

:::anatomy title="Lo que carga `@WebMvcTest`, y lo que deja afuera"
lang: java
code: |
  @WebMvcTest(ProductController.class)
  class ProductControllerTest {

      @Autowired
      MockMvc mvc;

      @MockitoBean
      ProductService service;
  }
notes:
  - { line: 1, text: "Levanta **solo** la capa web: controlador, conversores JSON, validación y seguridad." }
  - { line: 1, text: "No levanta servicio, repositorio ni base: por eso es rápido." }
  - { line: 4, text: "`MockMvc` ejecuta la petición dentro del proceso: no se abre ningún puerto." }
  - { line: 7, text: "`@MockitoBean` pone un doble del servicio en el contexto (era `@MockBean` hasta Spring Boot 3.4)." }
:::

:::key
Esta prueba verifica el **contrato**: ruta, verbo, estado, nombres de los
campos y formato de los valores. Si alguien renombra `name` a `title` en el
DTO, se rompe, y existe exactamente para eso.
:::

## Estado y cabecera

```java title="El 201 con Location del capítulo 17" numbered
@Test
void debeDevolver201YLocationAlCrear() throws Exception {
    when(service.crear(any())).thenReturn(
            new ProductResponse(7L, "Mouse", null,
                    new BigDecimal("89.90"), 5,
                    Status.ACTIVO, Instant.now()));

    mvc.perform(post("/products")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content("""
                             {"name":"Mouse","price":89.90,
                              "quantity":5}
                             """))
            .andExpect(status().isCreated())
            .andExpect(header().string("Location", "/products/7"))
            .andExpect(jsonPath("$.id").value(7));
}

@Test
void debeDevolver404CuandoNoExiste() throws Exception {
    when(service.buscar(99L))
            .thenThrow(new ProductNotFoundException(99L));

    mvc.perform(get("/products/99"))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.status").value(404))
            .andExpect(jsonPath("$.message").exists());
}
```

La segunda prueba es la que garantiza que el `@RestControllerAdvice` del
capítulo 26 está en el camino: verifica la traducción de la excepción, no el
servicio.

## Validación: la prueba que demuestra que el `400` es `400`

```java title="Entrada inválida" numbered
@Test
void debeDevolver400YElCampoCuandoElPrecioEsNegativo()
        throws Exception {
    mvc.perform(post("/products")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content("""
                             {"name":"X","price":-5,"quantity":1}
                             """))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.fields[0].field")
                    .value("price"));

    verify(service, never()).crear(any());
}
```

Dos verificaciones en una prueba, y las dos importan: el estado correcto
**y** la garantía de que no se llamó al servicio. Una validación que corre
después de la regla no es validación.

## Probando con un usuario autenticado

```java title="Sin iniciar sesión" numbered
@Test
@WithMockUser(roles = "ADMIN")
void adminDebeBorrar() throws Exception {
    mvc.perform(delete("/products/1").with(csrf()))
            .andExpect(status().isNoContent());
}

@Test
@WithMockUser(roles = "USER")
void usuarioComunNoDebeBorrar() throws Exception {
    mvc.perform(delete("/products/1").with(csrf()))
            .andExpect(status().isForbidden());

    verify(service, never()).borrar(any());
}
```

La segunda prueba es la del incidente del capítulo 33: las cuatro líneas que
habrían impedido que treinta y una personas pudieran borrar el catálogo.

:::pitfall
`@WebMvcTest` **carga** tu `SecurityConfig`. Si la prueba empieza a
devolver `401` donde esperas `200`, no es un bug de la prueba: es la
seguridad funcionando. Usa `@WithMockUser` o libera la ruta, y desconfía si
necesitas apagar la seguridad para que la prueba pase, porque eso significa
que no se está probando en ningún lado.
:::

## `jsonPath`: navegando la respuesta

```java title="Las formas que vas a usar" numbered
.andExpect(jsonPath("$.name").value("Teclado"))
.andExpect(jsonPath("$.content").isArray())
.andExpect(jsonPath("$.content.length()").value(3))
.andExpect(jsonPath("$.content[0].id").value(1))
.andExpect(jsonPath("$.totalElements").value(42))
.andExpect(jsonPath("$.password").doesNotExist())
```

La última línea es la más valiosa de todas: demuestra que un campo sensible
**no** está en la respuesta. Una prueba así en `UserController` es la red
que ataja el día en que alguien agregue un campo a la entidad sin pensar,
como en el capítulo 24.

## Cuándo levantar la aplicación entera

```java title="@SpringBootTest: la prueba de punta a punta" numbered
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
class ProductFlowTest {

    @Autowired MockMvc mvc;
    @Autowired ProductRepository repository;

    @Test
    @WithMockUser(roles = "ADMIN")
    void debeCrearYDespuesBuscar() throws Exception {
        mvc.perform(post("/products")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                 {"name":"Cable","price":19.90,
                                  "quantity":3}
                                 """)
                        .with(csrf()))
                .andExpect(status().isCreated());

        assertThat(repository.findByNameIgnoreCase("Cable"))
                .isPresent();
    }
}
```

| | `@WebMvcTest` | `@SpringBootTest` |
|---|---|---|
| Carga | solo la capa web | la aplicación entera |
| Velocidad | cientos de ms | segundos |
| Base | ninguna | de verdad |
| Úsalo para | el contrato de cada endpoint | uno o dos flujos completos |

Tabla: La proporción sana es una pirámide: muchas pruebas unitarias,
algunas de capa web, poquísimas de punta a punta.

:::story El contrato que se rompió sin que nadie lo notara
El cambio fue pequeño y bienintencionado: `ProductResponse` pasó a devolver
`price` como texto formateado —`"R$ 349,90"`— porque el equipo de front pidió
no tener que formatearlo.

Lo pidió el equipo de front del **sitio**. La aplicación móvil, hecha por un
socio, esperaba un número.

El deploy fue el martes. El miércoles, la pantalla del carrito de la
aplicación empezó a mostrar `NaN` en el total para todo el mundo. No hubo
error, no hubo `500`, no hubo alerta: la aplicación recibía un texto donde
esperaba un número, sumaba, y el resultado era "no es un número", en
silencio, en la pantalla del cliente.

Pasaron veintinueve horas hasta que alguien ató cabos.

La prueba que lo habría atrapado tenía una línea:

```java
.andExpect(jsonPath("$.price").value(349.90))
```

Existía. Alguien la había cambiado en el mismo commit, a `.value("R$
349,90")`, porque "la prueba se estaba rompiendo".
:::

:::summary
- `@WebMvcTest` levanta solo la capa web y prueba el contrato HTTP.
- Verifica estado, cabecera y campos del JSON, incluidos los que **no**
  deben existir.
- `@WithMockUser` simula un rol sin iniciar sesión; la prueba del `403` es
  obligatoria.
- La validación tiene que demostrar que no se llamó al servicio.
- Muchas pruebas unitarias, algunas web, poquísimas de punta a punta.
:::

:::checkpoint
Pruebas endpoints con MockMvc, verificas contrato y autorización, y sabes
elegir entre `@WebMvcTest` y `@SpringBootTest`.
:::

:::milestone
El contrato de la API está cubierto: ruta, estado, JSON y permiso. Falta la
capa que los dos capítulos anteriores evitaron a propósito: la base.
:::

:::exercise level=1
Escribe la prueba del `DELETE` verificando `204` y la llamada al servicio.

:::answer
No olvides `.with(csrf())` aun con CSRF apagado en producción:
`@WebMvcTest` usa la configuración de prueba por defecto de Spring
Security, que puede exigirlo. Es la causa número uno de `403` inexplicables
en pruebas de controlador.
:::

:::exercise level=2
Escribe una prueba que garantice que la respuesta de `GET /users/{id}`
**no** contiene el campo `password`.

:::answer
```java
.andExpect(jsonPath("$.password").doesNotExist())
```
Una prueba de cuatro palabras que protege contra una filtración. Las pruebas
negativas —demostrar que algo **no** pasa— son las más subestimadas del
repertorio.
:::

:::exercise level=3
Escribe una prueba de punta a punta que cree un producto, baje el stock
hasta cero y confirme que el estado pasó a `AGOTADO` en la respuesta de la
API.

:::answer
Esta prueba atraviesa controlador, servicio, entidad y base: es el único
tipo capaz de atrapar un error de integración, como un `@Transactional`
ausente o una columna con el nombre equivocado. Justamente por eso es lenta
y frágil: mantén dos o tres, para los flujos que valen dinero, y no más.
:::
