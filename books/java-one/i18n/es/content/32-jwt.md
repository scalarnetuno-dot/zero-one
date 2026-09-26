---
source_hash: c3eaf6cf80c7
title: "JWT"
number: 32
part: p7
kicker: "Una credencial firmada que el servidor no necesita guardar, y que tampoco puede cancelar."
goal: >-
  Emitir y validar un token JWT, entender qué es una firma y qué es el
  cifrado, y elegir el tiempo de expiración siendo consciente de lo que
  significa.
---

El capítulo 31 le enseñó al servidor a reconocer a un usuario. Falta que el
usuario **siga** siendo reconocido en la petición siguiente, sin que el
servidor guarde nada sobre él.

## El flujo entero

:::diagram type="sequence" caption="Login una vez, token en cada petición siguiente."
actors:
  - { id: c, name: "Cliente" }
  - { id: a, name: "/auth/login" }
  - { id: f, name: "Filtro JWT" }
  - { id: r, name: "Controller" }
messages:
  - { from: c, to: a, text: "email + contraseña" }
  - { from: a, to: c, text: "token firmado", dashed: true }
  - { from: c, to: f, text: "Authorization: Bearer ..." }
  - { from: f, to: f, text: "valida la firma" }
  - { from: f, to: r, text: "petición autenticada" }
  - { from: r, to: c, text: "200 OK", dashed: true }
:::

:::http title="El login"
POST /auth/login
Content-Type: application/json

{ "email": "admin@aurora.com", "password": "admin123" }
---
200 OK

{
  "token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbkBhdXJvcmEu...",
  "expiresIn": 3600
}
:::

:::http title="Y cada petición siguiente"
GET /products
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbk...
---
200 OK

{ "content": [ ... ] }
:::

## Qué es un JWT, exactamente

Tres partes separadas por puntos, cada una codificada en Base64:

```text title="header.payload.firma"
eyJhbGciOiJIUzI1NiJ9
.
eyJzdWIiOiJhZG1pbkBhdXJvcmEuY29tIiwicm9sZSI6IkFETUlOIn0
.
4pcPyMD09olPSyXnrXCjTwXyr4BsezdI1AVTmud2fU4
```

```json title="Lo que hay adentro, después de decodificarlo"
// header
{ "alg": "HS256", "typ": "JWT" }

// payload
{
  "sub": "admin@aurora.com",
  "role": "ADMIN",
  "iat": 1773504000,
  "exp": 1773507600
}
```

:::key
Base64 **no es cifrado**: es codificación. Cualquier persona pega el token
en `jwt.io` y lee todo su contenido. La firma garantiza que nadie **cambió**
el contenido, no que nadie lo leyó. Nunca pongas datos sensibles en el
payload.
:::

:::pitfall
Un error que aparece en código real: poner el documento, el teléfono o el
saldo del usuario en el token "para ahorrar una consulta". El token viaja en
cada petición, queda en el log del proxy, en el historial del navegador y en
el `localStorage`. Pon en el payload solo lo que ya es público y lo que el
servidor necesita para decidir: el identificador y el rol.
:::

## Generando y validando

```xml title="pom.xml"
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-api</artifactId>
    <version>0.12.6</version>
</dependency>
<!-- jjwt-impl y jjwt-jackson con scope runtime -->
```

```java title="security/JwtService.java" numbered
@Service
public class JwtService {

    private final SecretKey key;
    private final long segundosDeExpiracion;

    public JwtService(
            @Value("${app.jwt.secret}") String secret,
            @Value("${app.jwt.expiration}") long expiracion) {
        this.key = Keys.hmacShaKeyFor(secret.getBytes());
        this.segundosDeExpiracion = expiracion;
    }

    public String generar(String email, Role role) {
        Instant ahora = Instant.now();
        return Jwts.builder()
                .subject(email)
                .claim("role", role.name())
                .issuedAt(Date.from(ahora))
                .expiration(Date.from(
                        ahora.plusSeconds(segundosDeExpiracion)))
                .signWith(key)
                .compact();
    }

    public String emailDe(String token) {
        return Jwts.parser()
                .verifyWith(key)
                .build()
                .parseSignedClaims(token)
                .getPayload()
                .getSubject();
    }
}
```

`parseSignedClaims` hace la validación entera: verifica la firma y la
expiración. Un token adulterado lanza `SignatureException`; un token vencido
lanza `ExpiredJwtException`. No necesitas verificar nada a mano.

```properties title="application.properties"
app.jwt.secret=${JWT_SECRET:cambia-esto-en-produccion-min-32-bytes}
app.jwt.expiration=3600
```

:::pitfall
El secreto **no** puede ir al repositorio. La sintaxis
`${JWT_SECRET:por-defecto}` lee la variable de entorno y solo usa el valor
por defecto si no existe: el valor por defecto sirve para el desarrollo y
nunca para producción. Un secreto HS256 necesita al menos 32 bytes; la
biblioteca rechaza menos que eso, y ese rechazo es un favor.
:::

## El filtro que lee el encabezado

```java title="security/JwtFilter.java" numbered
@Component
public class JwtFilter extends OncePerRequestFilter {

    private final JwtService jwt;
    private final UserDetailsService users;

    @Override
    protected void doFilterInternal(
            HttpServletRequest req, HttpServletResponse res,
            FilterChain chain) throws ServletException, IOException {

        String header = req.getHeader("Authorization");

        if (header != null && header.startsWith("Bearer ")) {
            try {
                String email = jwt.emailDe(header.substring(7));
                UserDetails user =
                        users.loadUserByUsername(email);

                var auth = new UsernamePasswordAuthenticationToken(
                        user, null, user.getAuthorities());
                SecurityContextHolder.getContext()
                        .setAuthentication(auth);
            } catch (JwtException e) {
                SecurityContextHolder.clearContext();
            }
        }
        chain.doFilter(req, res);
    }
}
```

Y entra en la cadena antes del filtro estándar de usuario y contraseña:

```java title="SecurityConfig.java (agregado)"
.addFilterBefore(jwtFilter,
        UsernamePasswordAuthenticationFilter.class)
```

:::anatomy title="Tres detalles que cambian el comportamiento del filtro"
lang: java
code: |
  if (header != null && header.startsWith("Bearer ")) {
      try {
          String email = jwt.emailDe(header.substring(7));
          ...
      } catch (JwtException e) {
          SecurityContextHolder.clearContext();
      }
  }
  chain.doFilter(req, res);
notes:
  - { line: 3, text: "`substring(7)` corta exactamente `Bearer `: siete caracteres, con el espacio." }
  - { line: 6, text: "Un token inválido no lanza un error aquí: limpia el contexto y sigue sin autenticar." }
  - { line: 9, text: "`chain.doFilter` corre **siempre**: quien decide el `401` es la cadena, no este filtro." }
:::

## El endpoint de login

```java title="AuthController.java" numbered
@RestController
@RequestMapping("/auth")
public class AuthController {

    private final AuthenticationManager manager;
    private final JwtService jwt;
    private final UserRepository users;

    @PostMapping("/login")
    public LoginResponse login(@Valid @RequestBody LoginRequest req) {
        manager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        req.email(), req.password()));

        User user = users.findByEmail(req.email()).orElseThrow();
        return new LoginResponse(
                jwt.generar(user.getEmail(), user.getRole()), 3600);
    }
}
```

:::pitfall
La respuesta a un login fallido tiene que ser **igual** para "el e-mail no
existe" y "contraseña equivocada". Un `404` en el primer caso y un `401` en
el segundo le entrega una lista de e-mails registrados a quien quiera
probar. `401` para los dos, con el mismo mensaje.
:::

## El precio de no guardar nada

Un token firmado se puede verificar sin consultar la base: eso es lo que
vuelve escalable la API. Y es también lo que impide cancelarlo:

| Situación | Sesión en el servidor | JWT |
|---|---|---|
| Validar | consulta el almacenamiento | solo verifica la firma |
| Escalar | necesita compartir la sesión | cualquier instancia valida |
| Cerrar sesión ahora | borra la sesión | **no se puede** |
| Cambiar un permiso | vale en el acto | vale en el próximo token |

Tabla: El intercambio central del JWT. Se gana escala, se pierde control
inmediato.

Las salidas habituales: **expiración corta** (de quince minutos a una hora)
con un *refresh token* de vida larga, y una **lista de revocación** para los
casos graves, que, irónicamente, le devuelve el estado al servidor.

:::story El token de diez años
La expiración quedó en `315360000`.

Nadie eligió ese número conscientemente. Vino de un ejemplo de internet,
copiado durante una tarde apretada, y pasó la revisión de código porque
estaba entre dos docenas de otras líneas.

Son diez años en segundos.

El descubrimiento llegó junto con un despido. Un desarrollador dejó la
empresa un viernes, sus accesos se revocaron el lunes —el del e-mail, el del
repositorio, el de la nube— y alguien preguntó, casi por casualidad, si su
token de la API también se había cancelado.

No. No había cómo cancelarlo. El token seguía siendo técnicamente válido,
firmado por la propia empresa, hasta 2035.

La corrección fue cambiar el secreto de firma, lo que invalidó **todos** los
tokens de **todos** los usuarios de una vez. Fue lo correcto y tumbó la
aplicación de cuatro mil personas durante siete minutos.

La semana siguiente, la expiración pasó a ser de una hora y el equipo pasó a
tener una lista de revocación. Roberto preguntó si eso no iba a "cerrarle la
sesión al cliente todo el tiempo". Marina le explicó qué es un *refresh
token*.

Fue una buena reunión.
:::

:::art caption="Un token de diez años es una llave que sigue abriendo la puerta después del despido."
src="um-token-de-dez-anos-e-uma-chave-que-continua-abrindo-a-porta-depois-da-demissao.png"
Charge editorial minimalista: crachá corporativo pendurado em um cordão,
flutuando sozinho no ar, com a data "válido até 2035" impressa em destaque e
a foto substituída por uma silhueta cinza. Ao fundo, uma porta de escritório
com um leitor de cartão piscando verde. Ao lado, uma mesa vazia com uma caixa
de pertences. Fundo branco, poucos elementos, humor visual seco e levemente
sombrio, estética editorial de tecnologia.
:::

:::summary
- Un JWT está firmado, no cifrado: cualquiera puede leer el payload.
- La firma garantiza la integridad; el secreto vive en una variable de
  entorno.
- El filtro lee `Authorization: Bearer`, valida y completa el contexto, y
  siempre sigue la cadena.
- Un login fallido responde siempre igual, sin importar el motivo.
- Un token no se cancela: usa una expiración corta y trata la revocación
  como excepción.
:::

:::checkpoint
Emites un token en el login, lo validas en un filtro, proteges las rutas y
sabes explicar por qué no es posible cerrarle la sesión a alguien de
inmediato.
:::

:::milestone
La API autentica. Quien tiene token es reconocido en cada petición y quien
no lo tiene recibe `401`. Falta decidir qué puede hacer cada uno: el
capítulo 33.
:::

:::exercise level=1
Haz login, copia el token, pégalo en `jwt.io` y lee el payload. Después
cambia una letra del token e intenta usarlo.

:::answer
El payload lo puede leer cualquiera: la lección principal del capítulo.
Cambiar cualquier carácter invalida la firma y el filtro limpia el contexto,
lo que resulta en un `401`. El token es a prueba de adulteración, no de
lectura.
:::

:::exercise level=2
Cambia la expiración a 10 segundos, haz login, espera y usa el token.
Observa la excepción y escribe un handler que devuelva `401` con un mensaje
claro.

:::answer
```java
@ExceptionHandler(ExpiredJwtException.class)
public ResponseEntity<ApiError> expirado(
        ExpiredJwtException e, HttpServletRequest req) {
    return respuesta(HttpStatus.UNAUTHORIZED,
            "sesión expirada, vuelve a iniciar sesión", req);
}
```
Sin ese handler el cliente recibe un `401` genérico y no sabe si debe pedir
la contraseña otra vez o renovar el token. El mensaje es parte del
contrato.
:::

:::exercise level=3
Implementa el *refresh token*: un segundo token, de vida larga, guardado en
la base, que permite emitir un nuevo token de acceso. Explica por qué tiene
que estar en la base.

:::answer
Porque es justamente lo que le devuelve al servidor el poder de cancelar. El
token de acceso sigue siendo *stateless* y de vida corta; el de renovación
es una fila en una tabla, que puede borrarse ante un despido. Ganas escala
en el 99% de las peticiones y control en el 1% que importa, y esa es la
respuesta al dilema que cerró el capítulo.
:::
