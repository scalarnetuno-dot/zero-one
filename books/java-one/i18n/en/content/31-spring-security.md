---
source_hash: b73c62f55d19
title: "Spring Security"
number: 31
part: p7
kicker: "The API has been live for three chapters and anyone with the URL can delete any product."
goal: >-
  Add Spring Security to the project, understand the filter chain,
  configure which routes are public and store passwords the right way.
---

So far every one of Aurora Comércio's endpoints is public. `DELETE
/products/7` works for anyone who knows how to type. This chapter doesn't
solve that entirely — it builds the structure chapter 32 is going to use.

## Two words that are not synonyms

| | Question | Status when it fails |
|---|---|---|
| **Authentication** | who are you? | `401 Unauthorized` |
| **Authorization** | are you allowed to do this? | `403 Forbidden` |

Table: Authenticating is identifying; authorizing is allowing. A system can
know exactly who you are and still refuse.

## Adding the dependency (and the fright)

```xml title="pom.xml"
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
</dependency>
```

Restart and try `GET /products`:

:::http title="One dependency, and everything closes"
GET /products
---
401 Unauthorized
WWW-Authenticate: Basic realm="Realm"
:::

```text title="In the startup log"
Using generated security password: 8f3c1a92-...
```

Spring Security has an aggressive and correct default: **everything
protected until you say otherwise**. The random password in the log exists
so development doesn't stop — and it disappears the moment you configure
anything.

:::key
That default is the philosophy of the whole component: deny by omission.
It is the opposite of what most tools do, and it is why Spring Security is
annoying to configure and hard to leave insecure by carelessness.
:::

## The filter chain

```java title="config/SecurityConfig.java" numbered
package com.store.catalog.config;

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

:::anatomy title="Every line of the configuration is a security decision"
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
  - { line: 2, text: "CSRF protects forms with a browser session; an API with a token doesn't use a session." }
  - { line: 3, text: "`STATELESS`: the server keeps nothing between requests — which is what chapter 32 requires." }
  - { line: 5, text: "Order matters: the first rule that matches the request wins." }
  - { line: 8, text: "`anyRequest().authenticated()` closes everything not allowed above — the safety net." }
:::

:::pitfall
`csrf.disable()` shows up in every tutorial and is **not** a neutral
decision. It is only safe because the API is *stateless* and authenticates
through the `Authorization` header, not a cookie. If one day you add
session login with a cookie, that line becomes a real vulnerability. The
rule: CSRF turned off requires a token in the header.
:::

:::pitfall
The rules are evaluated top to bottom and the **first one that matches
wins**. Putting `.anyRequest().authenticated()` before the permits closes
everything — and the error is silent, because the configuration compiles
and starts normally. The symptom is a `401` on a route that should be
public.
:::

## A password is never stored

```java title="What goes to the database" numbered
PasswordEncoder encoder = new BCryptPasswordEncoder();

String hash = encoder.encode("secret123");
// $2a$10$N9qo8uLOickgx2ZMRZoMye...

encoder.matches("secret123", hash);   // true
encoder.matches("secret124", hash);   // false
```

What stays in the database is the **hash**, not the password. A hash is
one-way: you can verify, you can't go back. And BCrypt adds two things an
ordinary hash doesn't have:

- **salt** — a random value built in, which makes the same password
  generate different hashes for different users;
- **cost** — it is deliberately slow (tens of milliseconds), which doesn't
  bother a login and makes testing billions of combinations unfeasible.

:::trivia
In 2012 LinkedIn leaked 6.5 million passwords stored with unsalted SHA-1.
Within days, more than 90% had been cracked — not by breaking the
algorithm, but by comparing the hashes against ready-made tables. SHA-1 is
fast, and for passwords that is a defect. In 2016 it came out that the real
leak had been 117 million accounts.
:::

:::pitfall
Don't invent password cryptography. Don't use MD5, SHA-1 or plain SHA-256.
Don't store a reversible password "so it can be e-mailed when the user
forgets" — if your system can show the password, whoever breaks in can
too. Use `BCryptPasswordEncoder` and move on.
:::

## The user as an entity

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
    private String password;      // the hash, never the password

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Role role = Role.USER;

    protected User() { }
}
```

```java title="Role.java"
public enum Role { USER, ADMIN }
```

`users` in the plural for the same reason as chapter 29's `orders`: `USER`
is a reserved word in PostgreSQL.

## Teaching Spring to find the user

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

One interface, one method. Spring Security knows nothing about your
database — it knows how to ask for a user by identifier, and this class is
the translation.

:::story The DELETE nobody protected
The discovery was an accident, and the accident was Mr. Antônio.

He was showing the store to his grandson, who is nineteen and studies
computer science. The grandson opened the browser's developer panel, saw
the page's requests and noticed that the API answered anyone.

Out of curiosity, he typed a `DELETE` on a random product. He got
`204 No Content`.

The product vanished from the store.

He called Aurora the same day, which was an immense piece of luck. The
call reached Roberto, who called Marina, who opened the project and
confirmed it in fifteen seconds: there was no authentication anywhere.
There never had been.

"But nobody knows the URL," Roberto argued.

"The app knows it. Anyone with a phone and ten minutes knows it."

The endpoint stayed disabled for two days, by hand, with a commented-out
line. It was all there was time to do until security came in for real.
:::

:::summary
- Authentication identifies (`401`); authorization allows (`403`).
- Spring Security closes everything by default: you open things up
  explicitly.
- The order of the rules matters — the first one that matches wins.
- A password becomes a hash with BCrypt: salted and deliberately slow.
- `UserDetailsService` is the bridge between your database and the
  framework.
:::

:::checkpoint
You configure the filter chain, open public routes with judgment, store
passwords with BCrypt and connect Spring Security to your users table.
:::

:::milestone
The API has users and a security configuration. What's missing is the
mechanism that turns "I know the password" into "I'm still me on the next
request" — and that is the next chapter.
:::

:::exercise level=1
Leave `GET /products` public and everything else authenticated. Test both
cases with `curl` and check the statuses.

:::answer
`GET` returns `200`; `POST` without credentials returns `401`. If the
`POST` returns `403`, you probably forgot `csrf.disable()` — Spring
Security is blocking for lack of the CSRF token, not for lack of
authentication. The two statuses tell different stories.
:::

:::exercise level=2
Create the administrator user at startup with a `CommandLineRunner`, with
the password encoded.

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
The `if` is not a detail: without it, every restart tries to create the
same user and runs into the `UNIQUE` constraint.
:::

:::exercise level=3
Find out how long `BCryptPasswordEncoder` takes to encode a password with
cost 10 and with cost 14. Explain why the default isn't 14.

:::answer
Cost 10 takes tens of milliseconds; 14 takes almost a second. The cost is
exponential — each point doubles the work. One second per login is
tolerable for the user and disastrous for a server with a thousand logins
per minute. The default of 10 is a balance between the cost of the attack
and the cost of legitimate use, and it is worth revisiting every few years,
because the attacker's hardware improves.
:::
