---
source_hash: 2927aad224a7
title: "Usuarios y permisos"
number: 33
part: p7
kicker: "Saber quién es la persona es la mitad del trabajo. La otra mitad es decidir qué puede hacer."
goal: >-
  Proteger rutas por rol con `@PreAuthorize` y por regla de dueño del
  recurso, y saber por qué la autorización también vive en el servicio.
---

El token del capítulo 32 lleva un rol: `USER` o `ADMIN`. Falta usarlo. Hoy,
cualquier persona autenticada todavía borra cualquier producto, lo que es
una mejora pequeña respecto de "cualquier persona".

## El mapa de permisos de Aurora

| Operación | USER | ADMIN |
|---|---|---|
| `GET /products` | público | público |
| `POST /products` | no | sí |
| `PUT /products/{id}` | no | sí |
| `DELETE /products/{id}` | no | sí |
| `GET /orders/mios` | solo los propios | todos |
| `GET /users` | no | sí |

Tabla: El contrato de autorización. Escribirlo antes de programar es lo que
evita descubrir una regla faltante en producción.

## Dos lugares para declarar la regla

```java title="1. En la cadena de filtros: por ruta" numbered
.authorizeHttpRequests(auth -> auth
    .requestMatchers(HttpMethod.GET, "/products/**").permitAll()
    .requestMatchers(HttpMethod.POST, "/products/**")
        .hasRole("ADMIN")
    .requestMatchers(HttpMethod.PUT, "/products/**")
        .hasRole("ADMIN")
    .requestMatchers(HttpMethod.DELETE, "/products/**")
        .hasRole("ADMIN")
    .anyRequest().authenticated())
```

```java title="2. En el método: por anotación" numbered
@PreAuthorize("hasRole('ADMIN')")
@DeleteMapping("/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
public void borrar(@PathVariable Long id) {
    service.borrar(id);
}
```

Para que la segunda forma funcione, una anotación en la configuración:

```java
@Configuration
@EnableMethodSecurity
public class SecurityConfig { ... }
```

:::key
Las dos formas conviven, y la elección no es de gusto. La regla **por ruta**
es un mapa: quien lee la configuración ve el sistema entero. La regla **por
método** queda cerca del código que protege y sobrevive a un cambio de URL.
En proyectos reales, usa la primera para el diseño general y la segunda
para las excepciones.
:::

:::pitfall
`hasRole("ADMIN")` busca la autoridad `ROLE_ADMIN`: el prefijo se agrega
automáticamente. `hasAuthority("ADMIN")` busca exactamente `ADMIN`.
Mezclarlas da un `403` a quien debería pasar, y el log no lo explica. Elige
un estilo y mantenlo.
:::

## La regla que el filtro no puede expresar

"Un usuario ve sus propios pedidos" no es una regla de ruta: depende del
**dato**, no del camino.

```java title="OrderService.java" numbered
@Transactional(readOnly = true)
public OrderResponse buscar(Long id, String emailLogueado) {
    Order order = repository.findById(id)
            .orElseThrow(() -> new OrderNotFoundException(id));

    boolean dueno = order.getCustomer()
            .getEmail().equals(emailLogueado);

    if (!dueno && !esAdmin()) {
        throw new AccessDeniedException("pedido de otro cliente");
    }
    return OrderResponse.of(order);
}
```

:::pitfall
Fíjate en lo que este método **no** hace: no devuelve `404` cuando el pedido
es de otra persona. Devolver `404` en vez de `403` esconde la existencia del
recurso —lo que es más seguro—, pero también impide que el cliente legítimo
distinga "no existe" de "no es tuyo". Para datos sensibles, prefiere `404`;
para el resto, `403` es más honesto. Es una decisión consciente, no un
descuido.
:::

## Quién está logueado, dentro del código

```java title="Tres formas de obtener el usuario actual" numbered
// 1. parámetro del controlador
@GetMapping("/mios")
public List<OrderResponse> mios(Authentication auth) {
    return service.delCliente(auth.getName());
}

// 2. anotación
@GetMapping("/mios")
public List<OrderResponse> mios(
        @AuthenticationPrincipal UserDetails user) {
    return service.delCliente(user.getUsername());
}

// 3. en cualquier lugar (incluido el servicio)
String email = SecurityContextHolder.getContext()
        .getAuthentication().getName();
```

La tercera funciona en cualquier capa porque el contexto vive en una
variable del hilo: el mismo hilo que atiende la petición. Es práctica y
tiene un precio: el servicio pasa a depender de Spring Security, lo que
dificulta probarlo en aislamiento. Preferir pasar el e-mail como parámetro
mantiene al servicio ignorante del framework.

## La autorización también es regla de negocio

:::diagram type="blocks" caption="Tres capas de autorización, y la de abajo es la única que conoce el dato."
rows:
  - [{ text: "Cadena de filtros", note: "por ruta y verbo: el mapa general" }]
  - [{ text: "@PreAuthorize", note: "por método: el rol exigido" }]
  - [{ text: "Service", note: "por dato: ¿es tuyo? ¿está en tu sector?" }]
:::

:::pitfall
Proteger solo en el controlador es proteger solo la puerta de entrada. El
día en que exista otro punto de entrada —una cola de mensajes, un
programador de tareas, un comando de terminal— la regla del controlador deja
de valer. Una regla que depende del dato pertenece al servicio.
:::

## Lo que recibe el cliente

:::http title="Autenticado, pero sin permiso"
DELETE /products/7
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
---
403 Forbidden

{
  "status": 403,
  "error": "Forbidden",
  "message": "acceso denegado",
  "path": "/products/7"
}
:::

Para que la respuesta salga en ese formato —el `ApiError` del capítulo 26—,
falta un handler:

```java title="ApiExceptionHandler.java (agregado)" numbered
@ExceptionHandler(AccessDeniedException.class)
public ResponseEntity<ApiError> denegado(
        AccessDeniedException e, HttpServletRequest req) {
    return respuesta(HttpStatus.FORBIDDEN,
            "acceso denegado", req);
}
```

:::story El pasante con ADMIN
La tabla de usuarios tenía una columna `role` y un valor por defecto:
`ADMIN`.

No fue una decisión. Fue el primer registro creado a mano durante el
desarrollo, copiado como modelo en el script de creación de usuarios, y el
script se quedó.

Todos los que entraron a Aurora en los cuatro meses siguientes entraron como
administradores del catálogo. El equipo de atención, el equipo de
marketing, dos pasantes y un consultor externo que estuvo tres semanas.

Nadie hizo nada malo. Ese es el punto: la seguridad no se probó porque
nunca se ejercitó.

El descubrimiento llegó por el lado más burocrático posible: una auditoría
de cumplimiento pidió la lista de quién podía borrar un producto. La
respuesta fue "treinta y una personas", en una empresa de cuarenta.

Marina agregó tres cosas ese mismo día: el valor por defecto de la columna
pasó a ser `USER`, el script pasó a exigir el rol explícitamente, y una
prueba automatizada pasó a verificar que un `USER` recibe `403` en el
`DELETE`.

La prueba es el capítulo 36. Es lo que impidió que volviera a pasar.
:::

:::summary
- La regla por ruta dibuja el mapa; `@PreAuthorize` protege el método; el
  servicio decide lo que depende del dato.
- `hasRole` agrega `ROLE_`; `hasAuthority` no.
- `401` es "no sé quién eres"; `403` es "lo sé, y no puedes".
- Devolver `404` en vez de `403` esconde la existencia del recurso: una
  decisión consciente.
- El valor por defecto de un permiso debe ser el menor posible.
:::

:::checkpoint
Proteges rutas por rol, escribes la autorización por dueño del recurso en
el servicio, obtienes el usuario logueado y devuelves `403` en el formato
estándar de la API.
:::

:::milestone
Fin de la Parte 7. La API sabe quién entra, qué puede hacer cada uno y
responde con el estado correcto cuando no puede. Tampoco se probó nunca con
nada más que un `curl` tecleado a mano, y eso es lo que resuelve la Parte 8.
:::

:::exercise level=1
Protege `POST`, `PUT` y `DELETE` de `/products` con `ADMIN` y prueba con un
token de `USER`. Confirma el `403`.

:::answer
Si viene `401` en vez de `403`, el token no llegó al filtro: probablemente
falta el prefijo `Bearer ` o el filtro no se registró en la cadena. Los dos
estados apuntan a problemas distintos, y confundirlos cuesta media hora.
:::

:::exercise level=2
Implementa `GET /orders/mios` devolviendo solo los pedidos del usuario
autenticado, sin recibir ningún id en la URL.

:::answer
```java
@GetMapping("/mios")
public List<OrderResponse> mios(Authentication auth) {
    return service.delCliente(auth.getName());
}
```
Fíjate en que el cliente **no puede** pedir los pedidos de otra persona: el
identificador no está en la URL. Diseñar el endpoint así elimina toda una
clase de fallas de autorización: la mejor protección es la que no depende
de una verificación.
:::

:::exercise level=3
Agrega el rol `MANAGER`, que puede crear y editar productos pero no
borrarlos. Después responde: ¿en qué punto una lista de roles deja de
escalar?

:::answer
Cuando las combinaciones crecen más rápido que los cargos: "puede editar el
precio pero no el stock", "puede borrar solo de su propia categoría". Ahí el
modelo deja de ser de roles y pasa a ser de **permisos**: el usuario tiene
un conjunto de autoridades granulares (`PRODUCT_WRITE`, `PRODUCT_DELETE`) y
los roles se vuelven meros atajos a conjuntos. Es el mismo giro del
capítulo 12: cuando la escalera de `if` crece demasiado, falta un tipo.
:::
