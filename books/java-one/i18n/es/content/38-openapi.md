---
source_hash: 7f29ca09590b
title: "Swagger y OpenAPI"
number: 38
part: p9
kicker: "Una API que nadie sabe usar no existe. Y la documentación escrita a mano envejece en una semana."
goal: >-
  Generar documentación OpenAPI a partir del código, enriquecerla con
  anotaciones y entender por qué la documentación separada del código
  siempre miente.
---

La API de Aurora Comércio tiene once endpoints, cuatro estados posibles por
ruta, tres filtros opcionales y dos roles de acceso. Nada de eso está
escrito en ningún lado, excepto en este libro.

## Una dependencia, y la documentación existe

```xml title="pom.xml"
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.6.0</version>
</dependency>
```

Reinicia y abre `http://localhost:8080/swagger-ui.html`. Está todo ahí: cada
endpoint, cada parámetro, cada campo de cada DTO, con tipo y
obligatoriedad.

Nadie escribió nada.

:::key
springdoc lee lo que ya existe —`@GetMapping`, `@RequestBody`, `@NotBlank`,
el tipo de retorno— y arma la especificación a partir de eso. Es
documentación **derivada del código**, y por eso no tiene forma de estar
desactualizada respecto del código.
:::

## OpenAPI, Swagger y la confusión de nombres

| Nombre | Qué es |
|---|---|
| **OpenAPI** | la especificación: un JSON que describe la API |
| **Swagger UI** | la página que lee ese JSON y dibuja la interfaz |
| **springdoc** | la biblioteca que genera el JSON a partir de tu código |

Tabla: Swagger fue el nombre del formato hasta 2016, cuando se donó y se
rebautizó como OpenAPI. El nombre viejo se quedó en la herramienta.

```text title="Dos direcciones que pasan a existir"
/swagger-ui.html          la interfaz
/v3/api-docs              el JSON de la especificación
```

La segunda es la que importa de verdad: con ella, un cliente genera código
automáticamente en cualquier lenguaje, una prueba de contrato verifica si la
API cambió y una herramienta de API *gateway* importa las rutas.

## Enriqueciendo lo que el código no dice

El código dice el formato. No dice el significado:

```java title="ProductController.java" numbered
@Tag(name = "Productos",
     description = "Catálogo de la tienda")
@RestController
@RequestMapping("/products")
public class ProductController {

    @Operation(
        summary = "Busca un producto por id",
        description = "Devuelve el producto activo o inactivo. "
                    + "No exige autenticación.")
    @ApiResponses({
        @ApiResponse(responseCode = "200",
                     description = "encontrado"),
        @ApiResponse(responseCode = "404",
                     description = "el id no existe",
                     content = @Content(schema =
                         @Schema(implementation = ApiError.class)))
    })
    @GetMapping("/{id}")
    public ProductResponse buscar(
            @Parameter(description = "id del producto", example = "7")
            @PathVariable Long id) {
        return service.buscar(id);
    }
}
```

:::pitfall
Anotar todos los endpoints con `@Operation`, `@ApiResponse` y `@Parameter`
duplica el tamaño del controlador y ahoga el código en metadatos. El
equilibrio práctico: deja que springdoc infiera lo común y anota solo lo que
**no tiene forma de saber**: el significado del recurso, el motivo de un
`409`, un valor de ejemplo.
:::

## Documentando el DTO, que es donde mira el cliente

```java title="dto/ProductRequest.java" numbered
@Schema(description = "Datos para registrar un producto")
public record ProductRequest(

        @Schema(description = "Nombre mostrado en el catálogo",
                example = "Teclado mecánico ABNT2")
        @NotBlank @Size(max = 120)
        String name,

        @Schema(description = "Precio de venta en reales",
                example = "349.90")
        @NotNull @Positive
        BigDecimal price,

        @Schema(description = "Unidades en stock", example = "12")
        @NotNull @PositiveOrZero
        Integer quantity) {
}
```

Las anotaciones de validación del capítulo 25 ya aparecían solas en la
documentación: `@NotBlank` se vuelve `required: true`, `@Size(max = 120)` se
vuelve `maxLength: 120`. El `@Schema` agrega lo que falta: el ejemplo y la
frase en español.

## El botón de autorizar

```java title="config/OpenApiConfig.java" numbered
@Configuration
public class OpenApiConfig {

    @Bean
    OpenAPI api() {
        return new OpenAPI()
            .info(new Info()
                .title("Aurora Comércio — Catálogo")
                .version("1.0")
                .description("API de productos, pedidos y clientes."))
            .addSecurityItem(
                new SecurityRequirement().addList("bearer"))
            .components(new Components()
                .addSecuritySchemes("bearer",
                    new SecurityScheme()
                        .type(SecurityScheme.Type.HTTP)
                        .scheme("bearer")
                        .bearerFormat("JWT")));
    }
}
```

Con eso, la interfaz gana un botón **Authorize**: se pega el token del
capítulo 32 y todas las llamadas de prueba pasan a enviarlo. Es lo que hace
que la página sea útil de verdad: se puede ejercitar la API entera sin
`curl`.

:::pitfall
`/swagger-ui.html` y `/v3/api-docs` son rutas como cualquier otra: con
Spring Security encendido, exigen autenticación y el navegador muestra un
`401` en blanco. Libéralas explícitamente y, en producción, considera apagar
la interfaz y mantener solo el JSON, o proteger las dos. Un mapa detallado
de tu API es útil para quien integra, y también para quien ataca.
:::

```java title="SecurityConfig.java (agregado)"
.requestMatchers("/swagger-ui/**", "/swagger-ui.html",
                 "/v3/api-docs/**").permitAll()
```

## Lo que la documentación generada no resuelve

Describe **qué** recibe y devuelve cada endpoint. No describe:

- en qué orden llamar las cosas (crear el cliente antes del pedido);
- qué significa cada estado de negocio;
- límites de uso, versionado, política de deprecación.

Eso sigue siendo texto escrito por personas, pero en un `README.md` en el
repositorio, versionado junto con el código, y no en un documento suelto que
nadie sabe dónde vive.

:::story La documentación en Word
Había un archivo. `API_Aurora_v3_FINAL_revisado_2.docx`, en una carpeta
compartida, con cuarenta y una páginas.

Lo escribió con cariño alguien que ya no trabaja en la empresa.

El socio que integraba el catálogo usaba ese archivo como referencia y
mandaba correos educados cada semana preguntando por qué el campo `stock` no
existía en la respuesta. Sí existía: se llamaba `quantity` desde el capítulo
24, y el documento nunca se enteró.

Cuando entró springdoc, Marina le mandó al socio el enlace de
`/swagger-ui.html` y borró el `.docx` de la carpeta compartida.

Roberto preguntó si no era arriesgado borrar la documentación.

—No borramos la documentación —dijo ella—. Borramos una ficción sobre el
sistema que treinta personas creían que era documentación.
:::

:::summary
- springdoc genera la especificación OpenAPI a partir del código y de las
  anotaciones de validación.
- Swagger UI es la interfaz; `/v3/api-docs` es lo que consumen las
  herramientas.
- Anota solo lo que el código no tiene forma de decir: significado,
  ejemplo, motivo del error.
- Configura el esquema `bearer` para poder probar autenticado en la propia
  página.
- Libera las rutas de la documentación en la seguridad, y piénsalo dos veces
  antes de exponerlas en producción.
:::

:::checkpoint
Generas la documentación automáticamente, enriqueces los puntos que
importan, liberas las rutas y puedes ejercitar la API entera desde el
navegador.
:::

:::milestone
La API se documenta sola. Cualquier persona con el enlace puede entender y
probar los once endpoints sin hablar contigo, que es la definición práctica
de una API lista para usarse.
:::

:::exercise level=1
Agrega springdoc, libera las rutas y abre la interfaz. Registra un producto
desde el navegador, sin `curl`.

:::answer
Fíjate en que el formulario ya nace con los campos correctos y rechaza el
envío si falta uno obligatorio: todo derivado de las anotaciones de
validación del capítulo 25. La documentación y la validación son la misma
verdad, escrita una vez.
:::

:::exercise level=2
Documenta el `409` de nombre duplicado con `@ApiResponse`, apuntando al
esquema `ApiError`. Después revisa el JSON en `/v3/api-docs`.

:::answer
La ganancia no está en la página bonita: está en el JSON. Un cliente que lee
la especificación pasa a saber, en código, que `409` devuelve un objeto con
`message` y `fields`, y puede tratarlo sin adivinar.
:::

:::exercise level=3
Descarga `/v3/api-docs` en un archivo y versiónalo en el repositorio.
Después escribe una prueba que compare el archivo con el generado en el
momento. ¿Qué protege esa prueba?

:::answer
Detecta un **cambio de contrato**: si alguien renombra un campo, cambia un
estado o quita un endpoint, el archivo generado deja de coincidir con el
versionado y el build falla. Es una prueba de contrato —la misma idea del
capítulo 36, elevada al nivel de la API entera— y la defensa más barata
contra el incidente del `NaN`.
:::
