---
source_hash: 767c174d772f
title: "Tratamiento de errores"
number: 26
part: p5
kicker: "El error es parte del contrato. Una API que responde 500 para todo es una API que no cuenta qué pasó."
goal: >-
  Traducir excepciones de negocio en estados HTTP con `@ControllerAdvice`,
  armar una respuesta de error estandarizada y elegir entre `400`, `404`,
  `409` y `500` con criterio.
---

El capítulo 23 terminó con un problema: `GET /products/999` devuelve `500`.
El servicio lanzó `ProductNotFoundException` y nadie la tradujo. Este
capítulo escribe el traductor: una clase, y todos los errores de la API
pasan a tener forma.

## Un lugar para traducirlo todo

```java title="shared/exception/ApiExceptionHandler.java" numbered
package com.tienda.catalog.shared.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<ApiError> noEncontrado(
            ProductNotFoundException e, HttpServletRequest req) {
        return respuesta(HttpStatus.NOT_FOUND, e.getMessage(), req);
    }

    @ExceptionHandler(DuplicateProductException.class)
    public ResponseEntity<ApiError> conflicto(
            DuplicateProductException e, HttpServletRequest req) {
        return respuesta(HttpStatus.CONFLICT, e.getMessage(), req);
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ApiError> peticionMala(
            IllegalArgumentException e, HttpServletRequest req) {
        return respuesta(HttpStatus.BAD_REQUEST, e.getMessage(), req);
    }

    private ResponseEntity<ApiError> respuesta(
            HttpStatus status, String mensaje,
            HttpServletRequest req) {
        ApiError cuerpo = new ApiError(
                Instant.now(), status.value(),
                status.getReasonPhrase(), mensaje,
                req.getRequestURI(), List.of());
        return ResponseEntity.status(status).body(cuerpo);
    }
}
```

:::anatomy title="Cómo encuentra Spring el traductor correcto"
lang: java
code: |
  @RestControllerAdvice
  public class ApiExceptionHandler {

      @ExceptionHandler(ProductNotFoundException.class)
      public ResponseEntity<ApiError> noEncontrado(
              ProductNotFoundException e) {
          return ...;
      }
  }
notes:
  - { line: 1, text: "`@RestControllerAdvice` vale para **todos** los controladores de la aplicación." }
  - { line: 4, text: "`@ExceptionHandler` registra este método para ese tipo de excepción." }
  - { line: 4, text: "La búsqueda es por el tipo más específico: un handler de `RuntimeException` solo entra si no hay uno más cercano." }
  - { line: 6, text: "Spring inyecta la propia excepción como parámetro y, si lo pides, también la petición." }
:::

## La respuesta de error estandarizada

```java title="shared/exception/ApiError.java" numbered
public record ApiError(
        Instant timestamp,
        int status,
        String error,
        String message,
        String path,
        List<FieldError> fields) {

    public record FieldError(String field, String message) { }
}
```

:::http title="El mismo 404 de antes, ahora honesto"
GET /products/999
---
404 Not Found
Content-Type: application/json

{
  "timestamp": "2026-03-14T18:35:00Z",
  "status": 404,
  "error": "Not Found",
  "message": "producto no encontrado: 999",
  "path": "/products/999",
  "fields": []
}
:::

## El error de validación con el campo que falló

El capítulo 25 dejó el mensaje de validación en el formato del framework.
Ahora entra en el mismo molde:

```java title="ApiExceptionHandler.java (fragmento)" numbered
@ExceptionHandler(MethodArgumentNotValidException.class)
public ResponseEntity<ApiError> validacion(
        MethodArgumentNotValidException e,
        HttpServletRequest req) {

    List<ApiError.FieldError> campos = e.getBindingResult()
            .getFieldErrors().stream()
            .map(f -> new ApiError.FieldError(
                    f.getField(), f.getDefaultMessage()))
            .toList();

    ApiError cuerpo = new ApiError(
            Instant.now(), 400, "Bad Request",
            "datos inválidos", req.getRequestURI(), campos);

    return ResponseEntity.badRequest().body(cuerpo);
}
```

:::http title="Un error de validación con la dirección del problema"
POST /products
Content-Type: application/json

{ "name": "", "price": -50 }
---
400 Bad Request

{
  "status": 400,
  "message": "datos inválidos",
  "path": "/products",
  "fields": [
    { "field": "name",  "message": "el nombre es obligatorio" },
    { "field": "price", "message": "el precio debe ser positivo" }
  ]
}
:::

Esa respuesta la puede usar un cliente: la aplicación puede pintar de rojo
exactamente el campo `price` y mostrar el mensaje al lado. Es la diferencia
entre una API que rechaza y una API que enseña.

## Eligiendo el estado

| Estado | Significa | Ejemplo en el proyecto |
|---|---|---|
| `400` | petición malformada o inválida | precio negativo, JSON roto |
| `401` | no sé quién eres | token ausente (capítulo 32) |
| `403` | sé quién eres, y no puedes | usuario intentando borrar (capítulo 33) |
| `404` | no existe | id inexistente |
| `409` | conflicto con el estado actual | nombre duplicado, stock insuficiente |
| `422` | semánticamente inválido | opcional; muchos usan `400` |
| `500` | **yo** tengo un bug | cualquier cosa no prevista |

Tabla: La regla maestra: `4xx` es el cliente, `5xx` eres tú. Cambiarlos
rompe el monitoreo y la política de reintentos de los clientes.

:::key
`401` significa *no autenticado* aunque se llame `Unauthorized`; `403`
significa *no autorizado* (sin permiso). El nombre en el protocolo está
cambiado desde 1997 y no se va a corregir. Memorízalo.
:::

## La red de seguridad

```java title="El último handler, y el más importante" numbered
@ExceptionHandler(Exception.class)
public ResponseEntity<ApiError> inesperado(
        Exception e, HttpServletRequest req) {

    log.error("error no tratado en {}", req.getRequestURI(), e);

    ApiError cuerpo = new ApiError(
            Instant.now(), 500, "Internal Server Error",
            "error interno", req.getRequestURI(), List.of());

    return ResponseEntity.internalServerError().body(cuerpo);
}
```

Dos decisiones en ese método. **Registra** la excepción completa en el log,
con la traza: es la única copia de lo que pasó. Y le devuelve al cliente un
mensaje genérico, sin traza y sin detalle interno.

:::pitfall
Nunca le devuelvas al cliente el `e.getMessage()` de una excepción
inesperada. Los mensajes de excepción de la base llevan nombres de tabla, de
columna y, a veces, el SQL entero: información valiosa para quien esté
buscando una brecha. Registra todo en el log; muestra poco en la respuesta.
:::

## El problema del error genérico bienintencionado

:::compare left="Tragar y maquillar" right="Traducir con honestidad"
try {
  return service.buscar(id);
} catch (Exception e) {
  return null;
}
---
// sin try en el controller:
// el handler traduce
return service.buscar(id);
:::

La columna de la izquierda devuelve `200` con el cuerpo vacío: el cliente no
tiene cómo saber si el producto no existe o si el servidor falló. La de la
derecha no tiene ningún `try`: el controlador confía en el traductor
central.

:::trivia
Existe un patrón de respuesta de error publicado como norma: la RFC 9457,
*Problem Details for HTTP APIs*, con los campos `type`, `title`, `status`,
`detail` e `instance`. Spring 6 trae soporte nativo a través de
`ProblemDetail`. Si hoy empiezas un proyecto nuevo, vale la pena adoptar el
formato estandarizado en vez de inventar el tuyo; el `ApiError` de este
capítulo existe para mostrar la mecánica.
:::

:::summary
- `@RestControllerAdvice` centraliza la traducción de excepciones en
  respuestas HTTP.
- `@ExceptionHandler` coincide por el tipo más específico.
- Un error de validación debe decir **qué campo** falló.
- `4xx` es culpa del cliente, `5xx` es tuya; `401` es autenticación y `403`
  es permiso.
- Registra la excepción completa en el log y devuelve un mensaje genérico
  en el `500`.
:::

:::checkpoint
Traduces excepciones de negocio en los estados correctos, devuelves errores
de validación por campo, mantienes una red de seguridad para lo inesperado y
no filtras detalles internos.
:::

:::milestone
La API ahora falla bien: `404` para lo inexistente, `409` para el
conflicto, `400` con el campo problemático, `500` solo cuando la culpa es
tuya. Los cuatro defectos del capítulo 17 están resueltos.
:::

:::exercise level=1
Agrega un handler para `InsufficientStockException` que devuelva `409`.

:::answer
```java
@ExceptionHandler(InsufficientStockException.class)
public ResponseEntity<ApiError> stock(
        InsufficientStockException e, HttpServletRequest req) {
    return respuesta(HttpStatus.CONFLICT, e.getMessage(), req);
}
```
`409` y no `400`: la petición era correcta; es el **estado actual** del
recurso lo que impide la operación. Esa distinción ayuda al cliente a
decidir si vale la pena intentarlo de nuevo.
:::

:::exercise level=2
Haz que el handler del `500` incluya un identificador de rastreo en el
cuerpo y en el log (un `UUID` generado en el momento). Explica la ganancia.

:::answer
```java
String traceId = UUID.randomUUID().toString();
log.error("error {} en {}", traceId, req.getRequestURI(), e);
```
Con el identificador en la respuesta, el usuario puede informarlo al
soporte y tú encuentras la traza exacta en el log en segundos, sin tener que
exponer nada. Es una práctica estándar en una API de producción.
:::

:::exercise level=3
Descubre qué pasa con un `@ExceptionHandler(RuntimeException.class)`
declarado **junto** a los demás. Después explica por qué no importa el orden
de declaración.

:::answer
Solo se llama para una `RuntimeException` que no tenga un handler más
específico. Spring resuelve por **proximidad en la jerarquía de tipos**, no
por el orden en el archivo: `ProductNotFoundException` tiene handler
propio, así que gana. Eso permite tener un handler genérico sin miedo a que
secuestre los casos tratados.
:::
