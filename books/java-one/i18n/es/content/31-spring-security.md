---
source_hash: b73c62f55d19
title: "Spring Security"
number: 31
part: p7
kicker: "La API está en línea hace tres capítulos y cualquier persona con la URL borra cualquier producto."
goal: >-
  Agregar Spring Security al proyecto, entender la cadena de filtros,
  configurar qué rutas son públicas y guardar las contraseñas de la forma
  correcta.
---

Hasta ahora todos los endpoints de Aurora Comércio son públicos. `DELETE
/products/7` funciona para cualquiera que sepa escribir. Este capítulo no lo
resuelve del todo: arma la estructura que va a usar el capítulo 32.

## Dos palabras que no son sinónimos

| | Pregunta | Estado cuando falla |
|---|---|---|
| **Autenticación** | ¿quién eres? | `401 Unauthorized` |
| **Autorización** | ¿puedes hacer esto? | `403 Forbidden` |

Tabla: Autenticar es identificar; autorizar es permitir. Un sistema puede
saber exactamente quién eres y aun así rechazarte.

## Agregando la dependencia (y el susto)

```xml title="pom.xml"
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
</dependency>
```

Reinicia y prueba el `GET /products`:

:::http title="Una dependencia, y todo se cierra"
GET /products
---
401 Unauthorized
WWW-Authenticate: Basic realm="Realm"
:::

```text title="En el log del arranque"
Using generated security password: 8f3c1a92-...
```

Spring Security tiene un valor por defecto agresivo y correcto: **todo
protegido hasta que digas lo contrario**. La contraseña aleatoria en el log
existe para que el desarrollo no se detenga, y desaparece en el instante en
que configuras cualquier cosa.

:::key
Ese valor por defecto es la filosofía del componente entero: negar por
omisión. Es lo contrario de lo que hace la mayoría de las herramientas, y
es el motivo por el que Spring Security es molesto de configurar y difícil
de dejar inseguro por descuido.
:::

## La cadena de filtros

```java title="config/SecurityConfig.java" numbered
package com.tienda.catalog.config;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http)
            throws Exception {
        return http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(s -> s.sessionCreationPolicy(
                    SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(HttpMethod.GET, "/products/**")
                    .permitAll()
                .requestMatchers("/auth/**").permitAll()
                .anyRequest().authenticated())
            .build();
    }

    @Bean
    PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

:::anatomy title="Cada línea de la configuración es una decisión de seguridad"
lang: java
code: |
  return http
      .csrf(csrf -> csrf.disable())
      .sessionManagement(s -> s.sessionCreationPolicy(
              SessionCreationPolicy.STATELESS))
      .authorizeHttpRequests(auth -> auth
          .requestMatchers(HttpMethod.GET, "/products/**")
              .permitAll()
          .anyRequest().authenticated())
      .build();
notes:
  - { line: 2, text: "CSRF protege formularios con sesión en el navegador; una API con token no usa sesión." }
  - { line: 3, text: "`STATELESS`: el servidor no guarda nada entre peticiones, que es lo que exige el capítulo 32." }
  - { line: 5, text: "El orden importa: la primera regla que coincide con la petición gana." }
  - { line: 8, text: "`anyRequest().authenticated()` cierra todo lo que no se liberó arriba: la red de seguridad." }
:::

:::pitfall
`csrf.disable()` aparece en todo tutorial y **no** es una decisión neutra.
Solo es seguro porque la API es *stateless* y autentica por el encabezado
`Authorization`, no por cookie. Si un día agregas login por sesión con
cookie, esa línea se vuelve una vulnerabilidad real. La regla: CSRF
desactivado exige un token en el encabezado.
:::

:::pitfall
Las reglas se evalúan de arriba abajo y **gana la primera que coincide**.
Poner `.anyRequest().authenticated()` antes de las liberaciones lo cierra
todo, y el error es silencioso, porque la configuración compila y arranca
normalmente. El síntoma es un `401` en una ruta que debería ser pública.
:::

## La contraseña nunca se guarda

```java title="Lo que va a la base" numbered
PasswordEncoder encoder = new BCryptPasswordEncoder();

String hash = encoder.encode("clave123");
// $2a$10$N9qo8uLOickgx2ZMRZoMye...

encoder.matches("clave123", hash);   // true
encoder.matches("clave124", hash);   // false
```

Lo que queda en la base es el **hash**, no la contraseña. Un hash es de un
solo sentido: se puede verificar, no se puede volver atrás. Y BCrypt agrega
dos cosas que un hash común no tiene:

- **sal**: un valor aleatorio incorporado, que hace que la misma contraseña
  genere hashes distintos para usuarios distintos;
- **costo**: es deliberadamente lento (decenas de milisegundos), lo que no
  molesta a un login y hace inviable probar miles de millones de
  combinaciones.

:::trivia
En 2012 LinkedIn filtró 6,5 millones de contraseñas guardadas con SHA-1 sin
sal. En pocos días, más del 90% habían sido descubiertas, no rompiendo el
algoritmo, sino comparando los hashes con tablas ya preparadas. SHA-1 es
rápido, y para contraseñas eso es un defecto. En 2016 se supo que la
filtración real había sido de 117 millones de cuentas.
:::

:::pitfall
No inventes criptografía de contraseñas. No uses MD5, SHA-1 ni SHA-256 a
secas. No guardes la contraseña de forma reversible "para poder mandarla por
e-mail cuando el usuario se la olvide": si tu sistema puede mostrar la
contraseña, quien lo invada también puede. Usa `BCryptPasswordEncoder` y
sigue adelante.
:::

## El usuario como entidad

```java title="User.java" numbered
@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 120)
    private String email;

    @Column(nullable = false)
    private String password;      // el hash, nunca la contraseña

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Role role = Role.USER;

    protected User() { }
}
```

```java title="Role.java"
public enum Role { USER, ADMIN }
```

`users` en plural por el mismo motivo que `orders` en el capítulo 29:
`USER` es palabra reservada en PostgreSQL.

## Enseñándole a Spring a encontrar al usuario

```java title="AppUserDetailsService.java" numbered
@Service
public class AppUserDetailsService implements UserDetailsService {

    private final UserRepository repository;

    public AppUserDetailsService(UserRepository repository) {
        this.repository = repository;
    }

    @Override
    public UserDetails loadUserByUsername(String email) {
        User user = repository.findByEmail(email)
                .orElseThrow(() ->
                        new UsernameNotFoundException(email));

        return org.springframework.security.core.userdetails
                .User.builder()
                .username(user.getEmail())
                .password(user.getPassword())
                .roles(user.getRole().name())
                .build();
    }
}
```

Una interfaz, un método. Spring Security no sabe nada de tu base: sabe
pedir un usuario por su identificador, y esta clase es la traducción.

:::story El DELETE que nadie protegía
El descubrimiento fue por accidente, y el accidente fue don Antônio.

Le estaba mostrando la tienda a su nieto, que tiene diecinueve años y
estudia informática. El nieto abrió el panel del navegador, vio las
peticiones de la página y se dio cuenta de que la API le respondía a
cualquiera.

Por curiosidad, escribió un `DELETE` sobre un producto cualquiera. Recibió
`204 No Content`.

El producto desapareció de la tienda.

Llamó a Aurora ese mismo día, lo que fue una suerte inmensa. La llamada le
llegó a Roberto, que llamó a Marina, que abrió el proyecto y lo confirmó en
quince segundos: no había autenticación en ningún lugar. Nunca la había
habido.

—Pero nadie sabe la URL —argumentó Roberto.

—La aplicación la sabe. Cualquier persona con un celular y diez minutos la
sabe.

El endpoint quedó desactivado dos días, a mano, con una línea comentada. Fue
lo único que dio tiempo de hacer hasta que la seguridad entrara de verdad.
:::

:::summary
- La autenticación identifica (`401`); la autorización permite (`403`).
- Spring Security lo cierra todo por defecto: tú liberas explícitamente.
- El orden de las reglas importa: gana la primera que coincide.
- La contraseña se vuelve hash con BCrypt: con sal y deliberadamente lento.
- `UserDetailsService` es el puente entre tu base y el framework.
:::

:::checkpoint
Configuras la cadena de filtros, liberas rutas públicas con criterio,
guardas contraseñas con BCrypt y conectas Spring Security a tu tabla de
usuarios.
:::

:::milestone
La API tiene usuarios y una configuración de seguridad. Falta el mecanismo
que convierte "sé la contraseña" en "sigo siendo yo en la próxima petición",
y ese es el próximo capítulo.
:::

:::exercise level=1
Deja `GET /products` público y todo lo demás autenticado. Prueba los dos
casos con `curl` y revisa los estados.

:::answer
`GET` devuelve `200`; `POST` sin credenciales devuelve `401`. Si el `POST`
devuelve `403`, probablemente olvidaste `csrf.disable()`: Spring Security
está bloqueando por falta del token CSRF, no por falta de autenticación.
Los dos estados cuentan historias distintas.
:::

:::exercise level=2
Crea el usuario administrador al arrancar con un `CommandLineRunner`, con la
contraseña codificada.

:::answer
```java
@Bean
CommandLineRunner seed(UserRepository repo,
                       PasswordEncoder encoder) {
    return args -> {
        if (repo.findByEmail("admin@aurora.com").isEmpty()) {
            repo.save(new User("admin@aurora.com",
                    encoder.encode("admin123"), Role.ADMIN));
        }
    };
}
```
El `if` no es un detalle: sin él, cada reinicio intenta crear el mismo
usuario y choca con la restricción `UNIQUE`.
:::

:::exercise level=3
Descubre cuánto tarda `BCryptPasswordEncoder` en codificar una contraseña
con costo 10 y con costo 14. Explica por qué el valor por defecto no es 14.

:::answer
El costo 10 tarda decenas de milisegundos; el 14 tarda casi un segundo. El
costo es exponencial: cada punto duplica el trabajo. Un segundo por login es
tolerable para el usuario y desastroso para un servidor con mil logins por
minuto. El valor 10 es un equilibrio entre el costo del ataque y el costo
del uso legítimo, y vale la pena revisarlo cada pocos años, porque el
hardware del atacante mejora.
:::
