---
title: "Spring Security"
number: 31
part: p7
kicker: "A API está no ar há três capítulos e qualquer pessoa com a URL apaga qualquer produto."
goal: >-
  Adicionar Spring Security ao projeto, entender a cadeia de filtros,
  configurar quais rotas são públicas e guardar senha do jeito certo.
---

Até agora todo endpoint da Aurora Comércio é público. `DELETE
/products/7` funciona para qualquer um que saiba digitar. Este capítulo
não resolve isso inteiro — ele monta a estrutura que o capítulo 32 vai
usar.

## Duas palavras que não são sinônimas

| | Pergunta | Status quando falha |
|---|---|---|
| **Autenticação** | quem é você? | `401 Unauthorized` |
| **Autorização** | você pode isso? | `403 Forbidden` |

Tabela: Autenticar é identificar; autorizar é permitir. Um sistema pode saber
exatamente quem você é e ainda assim recusar.

## Adicionando a dependência (e o susto)

```xml title="pom.xml"
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
</dependency>
```

Reinicie e tente o `GET /products`:

:::http title="Uma dependência, e tudo fecha"
GET /products
---
401 Unauthorized
WWW-Authenticate: Basic realm="Realm"
:::

```text title="No log da partida"
Using generated security password: 8f3c1a92-...
```

O Spring Security tem um padrão agressivo e correto: **tudo protegido até
você dizer o contrário**. A senha aleatória no log existe para o
desenvolvimento não parar — e some no instante em que você configura
qualquer coisa.

:::key
Esse padrão é a filosofia do componente inteiro: negar por omissão. É o
oposto do que a maioria das ferramentas faz, e é o motivo de o Spring
Security ser chato de configurar e difícil de deixar inseguro por descuido.
:::

## A cadeia de filtros

```java title="config/SecurityConfig.java" numbered
package com.loja.catalog.config;

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

:::anatomy title="Cada linha da configuração é uma decisão de segurança"
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
  - { line: 2, text: "CSRF protege formulário com sessão em navegador; uma API com token não usa sessão." }
  - { line: 3, text: "`STATELESS`: o servidor não guarda nada entre requisições — é o que o capítulo 32 exige." }
  - { line: 5, text: "A ordem importa: a primeira regra que casar com a requisição vence." }
  - { line: 8, text: "`anyRequest().authenticated()` fecha tudo que não foi liberado acima — a rede de segurança." }
:::

:::pitfall
`csrf.disable()` aparece em todo tutorial e **não** é uma decisão neutra. Ele
só é seguro porque a API é *stateless* e autentica por cabeçalho `Authorization`,
não por cookie. Se um dia você acrescentar login por sessão com cookie, essa
linha vira uma vulnerabilidade real. A regra: CSRF desligado exige token no
cabeçalho.
:::

:::pitfall
A ordem das regras é de cima para baixo e a **primeira que casa vence**.
Colocar `.anyRequest().authenticated()` antes das liberações fecha tudo — e o
erro é silencioso, porque a configuração compila e sobe normalmente. O
sintoma é `401` em uma rota que deveria ser pública.
:::

## Senha nunca é guardada

```java title="O que vai para o banco" numbered
PasswordEncoder encoder = new BCryptPasswordEncoder();

String hash = encoder.encode("senha123");
// $2a$10$N9qo8uLOickgx2ZMRZoMye...

encoder.matches("senha123", hash);   // true
encoder.matches("senha124", hash);   // false
```

O que fica no banco é o **hash**, não a senha. Hash é de mão única: dá para
verificar, não dá para voltar. E o BCrypt acrescenta duas coisas que um hash
comum não tem:

- **sal** — um valor aleatório embutido, que faz a mesma senha gerar hashes
  diferentes para usuários diferentes;
- **custo** — ele é deliberadamente lento (dezenas de milissegundos), o que
  não incomoda um login e inviabiliza testar bilhões de combinações.

:::trivia
Em 2012 o LinkedIn vazou 6,5 milhões de senhas guardadas com SHA-1 sem sal.
Em dias, mais de 90% tinham sido descobertas — não por quebrar o algoritmo,
mas por comparar os hashes com tabelas prontas. SHA-1 é rápido, e para senha
isso é um defeito. Em 2016 descobriu-se que o vazamento real tinha sido de
117 milhões de contas.
:::

:::pitfall
Não invente criptografia de senha. Não use MD5, SHA-1 nem SHA-256 puro. Não
guarde senha reversível "para poder mandar por e-mail quando o usuário
esquecer" — se o seu sistema consegue mostrar a senha, quem invadir também
consegue. Use `BCryptPasswordEncoder` e siga a vida.
:::

## O usuário como entidade

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
    private String password;      // hash, nunca a senha

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Role role = Role.USER;

    protected User() { }
}
```

```java title="Role.java"
public enum Role { USER, ADMIN }
```

`users` no plural pelo mesmo motivo de `orders` no capítulo 29: `USER` é
palavra reservada no PostgreSQL.

## Ensinando o Spring a encontrar o usuário

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

Uma interface, um método. O Spring Security não sabe nada do seu banco — ele
sabe pedir um usuário pelo identificador, e essa classe é a tradução.

:::story O DELETE que ninguém protegia
A descoberta foi por acidente, e o acidente foi o Seu Antônio.

Ele estava mostrando a loja para o neto, que tem dezenove anos e faz
faculdade de computação. O neto abriu o painel do navegador, viu as
requisições da página e reparou que a API respondia a qualquer um.

Digitou, por curiosidade, um `DELETE` em um produto qualquer. Recebeu `204
No Content`.

O produto sumiu da loja.

Ele ligou para a Aurora no mesmo dia, o que foi uma sorte imensa. A ligação
chegou ao Roberto, que ligou para a Marina, que abriu o projeto e confirmou
em quinze segundos: não havia autenticação em lugar nenhum. Nunca tinha
havido.

— Mas ninguém sabe a URL — argumentou Roberto.

— O aplicativo sabe. Qualquer pessoa com um celular e dez minutos sabe.

O endpoint ficou desligado por dois dias, na unha, com uma linha comentada.
Foi o que deu tempo de fazer até a segurança entrar de verdade.
:::

:::art caption="Uma API sem autenticação não é privada: é apenas desconhecida."
src="uma-api-sem-autenticacao-nao-e-privada-e-apenas-desconhecida.png"
Charge editorial minimalista: porta de casa aberta com uma pequena placa
escrita "API", sem maçaneta e sem fechadura; ao lado, um capacho onde se lê
"ninguém sabe que estamos aqui". Um jovem de mochila nas costas, do lado de
fora, olha para dentro com curiosidade e um celular na mão. Fundo branco,
poucos elementos, humor visual seco, estética editorial de tecnologia.
:::

:::summary
- Autenticação identifica (`401`); autorização permite (`403`).
- O Spring Security fecha tudo por padrão: você libera explicitamente.
- A ordem das regras importa — a primeira que casa vence.
- Senha vira hash com BCrypt: com sal e deliberadamente lento.
- `UserDetailsService` é a ponte entre o seu banco e o framework.
:::

:::checkpoint
Você configura a cadeia de filtros, libera rotas públicas com critério,
guarda senha com BCrypt e conecta o Spring Security à sua tabela de usuários.
:::

:::milestone
A API tem usuários e uma configuração de segurança. Falta o mecanismo que
transforma "eu sei a senha" em "eu continuo sendo eu na próxima
requisição" — e é o próximo capítulo.
:::

:::exercise level=1
Deixe `GET /products` público e todo o resto autenticado. Teste os dois casos
com `curl` e confira os status.

:::answer
`GET` devolve `200`; `POST` sem credencial devolve `401`. Se o `POST`
devolver `403`, você provavelmente esqueceu `csrf.disable()` — o Spring
Security está barrando por falta do token CSRF, não por falta de
autenticação. Os dois status contam histórias diferentes.
:::

:::exercise level=2
Crie o usuário administrador na partida com um `CommandLineRunner`, com a
senha codificada.

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
O `if` não é detalhe: sem ele, cada reinício tenta criar o mesmo usuário e
esbarra na restrição `UNIQUE`.
:::

:::exercise level=3
Descubra quanto tempo o `BCryptPasswordEncoder` leva para codificar uma
senha com custo 10 e com custo 14. Explique por que o padrão não é 14.

:::answer
Custo 10 leva dezenas de milissegundos; 14 leva quase um segundo. O custo é
exponencial — cada ponto dobra o trabalho. Um segundo por login é tolerável
para o usuário e desastroso para um servidor com mil logins por minuto. O
padrão 10 é um equilíbrio entre o custo do ataque e o custo do uso legítimo,
e vale revisá-lo a cada poucos anos, porque o hardware do atacante melhora.
:::
