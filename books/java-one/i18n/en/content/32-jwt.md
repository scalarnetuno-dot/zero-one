---
source_hash: c3eaf6cf80c7
title: "JWT"
number: 32
part: p7
kicker: "A signed badge the server doesn't need to keep — and that it also can't cancel."
goal: >-
  Issue and validate a JWT token, understand what a signature is and what
  encryption is, and choose the expiration time aware of what it means.
---

Chapter 31 taught the server to recognize a user. What's missing is for
the user to **stay** recognized on the next request — without the server
keeping anything about them.

## The whole flow

:::diagram type="sequence" caption="Log in once, token on every following request."
actors:
  - { id: c, name: "Client" }
  - { id: a, name: "/auth/login" }
  - { id: f, name: "JWT filter" }
  - { id: r, name: "Controller" }
messages:
  - { from: c, to: a, text: "email + password" }
  - { from: a, to: c, text: "signed token", dashed: true }
  - { from: c, to: f, text: "Authorization: Bearer ..." }
  - { from: f, to: f, text: "validates the signature" }
  - { from: f, to: r, text: "authenticated request" }
  - { from: r, to: c, text: "200 OK", dashed: true }
:::

:::http title="The login"
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

:::http title="And every following request"
GET /products
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbk...
---
200 OK

{ "content": [ ... ] }
:::

## What a JWT is, exactly

Three parts separated by dots, each one Base64-encoded:

```text title="header.payload.signature"
eyJhbGciOiJIUzI1NiJ9
.
eyJzdWIiOiJhZG1pbkBhdXJvcmEuY29tIiwicm9sZSI6IkFETUlOIn0
.
4pcPyMD09olPSyXnrXCjTwXyr4BsezdI1AVTmud2fU4
```

```json title="What's inside, after decoding"
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
Base64 **is not encryption**: it is encoding. Anyone can paste the token
into `jwt.io` and read its entire contents. The signature guarantees that
nobody **changed** the content — not that nobody read it. Never put
sensitive data in the payload.
:::

:::pitfall
A mistake that shows up in real code: putting the user's tax ID, phone
number or balance in the token "to save a query". The token travels on
every request, ends up in the proxy log, the browser history and
`localStorage`. Put in the payload only what is already public and what the
server needs to decide: the identifier and the role.
:::

## Generating and validating

```xml title="pom.xml"
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-api</artifactId>
    <version>0.12.6</version>
</dependency>
<!-- jjwt-impl and jjwt-jackson with runtime scope -->
```

```java title="security/JwtService.java" numbered
@Service
public class JwtService {

    private final SecretKey key;
    private final long expirationSeconds;

    public JwtService(
            @Value("${app.jwt.secret}") String secret,
            @Value("${app.jwt.expiration}") long expiration) {
        this.key = Keys.hmacShaKeyFor(secret.getBytes());
        this.expirationSeconds = expiration;
    }

    public String generate(String email, Role role) {
        Instant now = Instant.now();
        return Jwts.builder()
                .subject(email)
                .claim("role", role.name())
                .issuedAt(Date.from(now))
                .expiration(Date.from(
                        now.plusSeconds(expirationSeconds)))
                .signWith(key)
                .compact();
    }

    public String emailOf(String token) {
        return Jwts.parser()
                .verifyWith(key)
                .build()
                .parseSignedClaims(token)
                .getPayload()
                .getSubject();
    }
}
```

`parseSignedClaims` does the whole validation: it checks the signature and
the expiration. A tampered token throws `SignatureException`; an expired
token throws `ExpiredJwtException`. You don't need to check anything by
hand.

```properties title="application.properties"
app.jwt.secret=${JWT_SECRET:change-this-in-production-min-32-bytes}
app.jwt.expiration=3600
```

:::pitfall
The secret **cannot** go into the repository. The `${JWT_SECRET:default}`
syntax reads the environment variable and only uses the default value if it
doesn't exist — the default is for development and never for production.
An HS256 secret needs at least 32 bytes; the library refuses anything less,
and that refusal is a favor.
:::

## The filter that reads the header

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
                String email = jwt.emailOf(header.substring(7));
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

And it enters the chain before the default username-and-password filter:

```java title="SecurityConfig.java (addition)"
.addFilterBefore(jwtFilter,
        UsernamePasswordAuthenticationFilter.class)
```

:::anatomy title="Three details that change the filter's behavior"
lang: java
code: |
  if (header != null && header.startsWith("Bearer ")) {
      try {
          String email = jwt.emailOf(header.substring(7));
          ...
      } catch (JwtException e) {
          SecurityContextHolder.clearContext();
      }
  }
  chain.doFilter(req, res);
notes:
  - { line: 3, text: "`substring(7)` cuts exactly `Bearer ` — seven characters, space included." }
  - { line: 6, text: "An invalid token doesn't throw an error here: it clears the context and moves on unauthenticated." }
  - { line: 9, text: "`chain.doFilter` **always** runs: the chain decides the `401`, not this filter." }
:::

## The login endpoint

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
                jwt.generate(user.getEmail(), user.getRole()), 3600);
    }
}
```

:::pitfall
The response to a failed login has to be **the same** for "e-mail doesn't
exist" and "wrong password". A `404` in the first case and a `401` in the
second hands a list of registered e-mails to anyone who wants to test. `401`
for both, with the same message.
:::

## The price of keeping nothing

A signed token can be verified without querying the database — that is
what makes the API scalable. And it is also what prevents cancellation:

| Situation | Server-side session | JWT |
|---|---|---|
| Validate | queries the storage | only checks the signature |
| Scale | needs to share sessions | any instance validates |
| Log out now | deletes the session | **can't** |
| Change permission | applies immediately | applies on the next token |

Table: JWT's central trade-off. You gain scale, you lose immediate
control.

The usual ways out: a **short expiration** (fifteen minutes to an hour)
with a long-lived *refresh token*, and a **revocation list** for serious
cases — which, ironically, brings state back to the server.

:::story The ten-year token
The expiration was set to `315360000`.

Nobody chose that number consciously. It came from an example on the
internet, copied during a tight afternoon, and it got through code review
because it sat among two dozen other lines.

It is ten years in seconds.

The discovery came along with a dismissal. A developer left the company on
a Friday, their access was revoked on Monday — e-mail, repository, cloud —
and someone asked, almost by chance, whether their API token had also been
canceled.

It hadn't. There was no way to cancel it. The token was still technically
valid, signed by the company itself, until 2035.

The fix was to change the signing secret, which invalidated **every** token
of **every** user at once. It was the right thing to do and it took down
the app for four thousand people for seven minutes.

The following week, the expiration became one hour and the team got a
revocation list. Roberto asked whether that wasn't going to "log the
customer out all the time". Marina explained what a *refresh token* is.

It was a good meeting.
:::

:::art caption="A ten-year token is a key that keeps opening the door after the dismissal."
src="um-token-de-dez-anos-e-uma-chave-que-continua-abrindo-a-porta-depois-da-demissao.png"
Charge editorial minimalista: crachá corporativo pendurado em um cordão,
flutuando sozinho no ar, com a data "válido até 2035" impressa em destaque e
a foto substituída por uma silhueta cinza. Ao fundo, uma porta de escritório
com um leitor de cartão piscando verde. Ao lado, uma mesa vazia com uma caixa
de pertences. Fundo branco, poucos elementos, humor visual seco e levemente
sombrio, estética editorial de tecnologia.
:::

:::summary
- A JWT is signed, not encrypted: anyone can read the payload.
- The signature guarantees integrity; the secret lives in an environment
  variable.
- The filter reads `Authorization: Bearer`, validates and populates the
  context — and always continues the chain.
- A failed login always answers the same, whatever the reason.
- A token can't be canceled: use a short expiration and treat revocation as
  an exception.
:::

:::checkpoint
You issue a token at login, validate it in a filter, protect the routes and
can explain why it isn't possible to log someone out immediately.
:::

:::milestone
The API authenticates. Whoever has a token is recognized on every request
and whoever doesn't gets a `401`. What's left is deciding what each one can
do — chapter 33.
:::

:::exercise level=1
Log in, copy the token, paste it into `jwt.io` and read the payload. Then
change one letter of the token and try to use it.

:::answer
The payload is readable by anyone — the chapter's main lesson. Changing any
character invalidates the signature and the filter clears the context,
resulting in a `401`. The token is tamper-proof, not read-proof.
:::

:::exercise level=2
Change the expiration to 10 seconds, log in, wait and use the token.
Observe the exception and write a handler that returns `401` with a clear
message.

:::answer
```java
@ExceptionHandler(ExpiredJwtException.class)
public ResponseEntity<ApiError> expired(
        ExpiredJwtException e, HttpServletRequest req) {
    return response(HttpStatus.UNAUTHORIZED,
            "session expired, please log in again", req);
}
```
Without that handler the client gets a generic `401` and doesn't know
whether to ask for the password again or renew the token. The message is
part of the contract.
:::

:::exercise level=3
Implement the *refresh token*: a second, long-lived token, stored in the
database, that allows issuing a new access token. Explain why it needs to
be in the database.

:::answer
Because that is precisely what gives the server back the power to cancel.
The access token stays *stateless* and short-lived; the refresh token is a
row in a table, which can be deleted upon a dismissal. You gain scale on
99% of requests and control on the 1% that matters — and that is the
answer to the dilemma that closed the chapter.
:::
