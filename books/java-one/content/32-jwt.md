---
title: "JWT"
number: 32
part: p7
kicker: "Um crachá assinado que o servidor não precisa guardar — e que ele também não consegue cancelar."
goal: >-
  Emitir e validar um token JWT, entender o que é assinatura e o que é
  criptografia, e escolher o tempo de expiração com consciência do que isso
  significa.
---

O capítulo 31 ensinou o servidor a reconhecer um usuário. Falta o
usuário **continuar** reconhecido na requisição seguinte — sem que o servidor
guarde nada sobre ele.

## O fluxo inteiro

:::diagram type="sequence" caption="Login uma vez, token em toda requisição seguinte."
actors:
  - { id: c, name: "Cliente" }
  - { id: a, name: "/auth/login" }
  - { id: f, name: "Filtro JWT" }
  - { id: r, name: "Controller" }
messages:
  - { from: c, to: a, text: "email + senha" }
  - { from: a, to: c, text: "token assinado", dashed: true }
  - { from: c, to: f, text: "Authorization: Bearer ..." }
  - { from: f, to: f, text: "valida assinatura" }
  - { from: f, to: r, text: "requisição autenticada" }
  - { from: r, to: c, text: "200 OK", dashed: true }
:::

:::http title="O login"
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

:::http title="E toda requisição seguinte"
GET /products
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbk...
---
200 OK

{ "content": [ ... ] }
:::

## O que é um JWT, exatamente

Três partes separadas por ponto, cada uma codificada em Base64:

```text title="header.payload.assinatura"
eyJhbGciOiJIUzI1NiJ9
.
eyJzdWIiOiJhZG1pbkBhdXJvcmEuY29tIiwicm9sZSI6IkFETUlOIn0
.
4pcPyMD09olPSyXnrXCjTwXyr4BsezdI1AVTmud2fU4
```

```json title="O que tem dentro, depois de decodificar"
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
Base64 **não é criptografia**: é codificação. Qualquer pessoa cola o token em
`jwt.io` e lê o conteúdo inteiro. A assinatura garante que ninguém
**alterou** o conteúdo — não que ninguém o leu. Nunca coloque dado sensível
no payload.
:::

:::pitfall
Um erro que aparece em código real: colocar o CPF, o telefone ou o saldo do
usuário no token "para economizar consulta". O token viaja em cada
requisição, fica no log do proxy, no histórico do navegador e no
`localStorage`. Coloque no payload apenas o que já é público e o que o
servidor precisa para decidir: identificador e papel.
:::

## Gerando e validando

```xml title="pom.xml"
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-api</artifactId>
    <version>0.12.6</version>
</dependency>
<!-- jjwt-impl e jjwt-jackson com scope runtime -->
```

```java title="security/JwtService.java" numbered
@Service
public class JwtService {

    private final SecretKey key;
    private final long expiracaoSegundos;

    public JwtService(
            @Value("${app.jwt.secret}") String secret,
            @Value("${app.jwt.expiration}") long expiracao) {
        this.key = Keys.hmacShaKeyFor(secret.getBytes());
        this.expiracaoSegundos = expiracao;
    }

    public String gerar(String email, Role role) {
        Instant agora = Instant.now();
        return Jwts.builder()
                .subject(email)
                .claim("role", role.name())
                .issuedAt(Date.from(agora))
                .expiration(Date.from(
                        agora.plusSeconds(expiracaoSegundos)))
                .signWith(key)
                .compact();
    }

    public String emailDo(String token) {
        return Jwts.parser()
                .verifyWith(key)
                .build()
                .parseSignedClaims(token)
                .getPayload()
                .getSubject();
    }
}
```

`parseSignedClaims` faz a validação inteira: confere a assinatura e a
expiração. Token adulterado lança `SignatureException`; token vencido lança
`ExpiredJwtException`. Você não precisa checar nada à mão.

```properties title="application.properties"
app.jwt.secret=${JWT_SECRET:troque-isto-em-producao-min-32-bytes}
app.jwt.expiration=3600
```

:::pitfall
O segredo **não** pode ir para o repositório. A sintaxe `${JWT_SECRET:padrão}`
lê a variável de ambiente e só usa o valor padrão se ela não existir — o
padrão serve para o desenvolvimento e nunca para produção. Um segredo HS256
precisa de pelo menos 32 bytes; a biblioteca recusa menos que isso, e essa
recusa é um favor.
:::

## O filtro que lê o cabeçalho

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
                String email = jwt.emailDo(header.substring(7));
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

E ele entra na cadeia antes do filtro padrão de usuário e senha:

```java title="SecurityConfig.java (acréscimo)"
.addFilterBefore(jwtFilter,
        UsernamePasswordAuthenticationFilter.class)
```

:::anatomy title="Três detalhes que mudam o comportamento do filtro"
lang: java
code: |
  if (header != null && header.startsWith("Bearer ")) {
      try {
          String email = jwt.emailDo(header.substring(7));
          ...
      } catch (JwtException e) {
          SecurityContextHolder.clearContext();
      }
  }
  chain.doFilter(req, res);
notes:
  - { line: 3, text: "`substring(7)` corta exatamente `Bearer ` — sete caracteres, com o espaço." }
  - { line: 6, text: "Token inválido não lança erro aqui: limpa o contexto e segue sem autenticar." }
  - { line: 9, text: "`chain.doFilter` **sempre** roda: quem decide o `401` é a cadeia, não este filtro." }
:::

## O endpoint de login

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
                jwt.gerar(user.getEmail(), user.getRole()), 3600);
    }
}
```

:::pitfall
A resposta de login errado tem de ser **igual** para "e-mail não existe" e
"senha errada". Um `404` no primeiro caso e `401` no segundo entrega uma
lista de e-mails cadastrados a quem quiser testar. `401` para os dois, com a
mesma mensagem.
:::

## O preço de não guardar nada

Um token assinado é verificável sem consultar o banco — é o que torna a API
escalável. E é também o que impede o cancelamento:

| Situação | Sessão no servidor | JWT |
|---|---|---|
| Validar | consulta o armazenamento | só confere a assinatura |
| Escalar | precisa compartilhar sessão | qualquer instância valida |
| Deslogar agora | apaga a sessão | **não dá** |
| Trocar permissão | vale na hora | vale no próximo token |

Tabela: A troca central do JWT. Ganha-se escala, perde-se controle imediato.

As saídas usuais: **expiração curta** (quinze minutos a uma hora) com um
*refresh token* de vida longa, e uma **lista de revogação** para os casos
graves — que, ironicamente, devolve o estado ao servidor.

:::story O token de dez anos
A expiração ficou em `315360000`.

Ninguém escolheu esse número conscientemente. Ele veio de um exemplo da
internet, copiado durante uma tarde apertada, e passou na revisão de código
porque estava entre duas dezenas de outras linhas.

São dez anos em segundos.

A descoberta veio junto com uma demissão. Um desenvolvedor saiu da empresa
numa sexta, os acessos foram revogados na segunda — o do e-mail, o do
repositório, o da nuvem — e alguém perguntou, quase por acaso, se o token da
API dele também tinha sido cancelado.

Não tinha. Não havia como cancelar. O token continuava tecnicamente válido,
assinado pela própria empresa, até 2035.

A correção foi trocar o segredo de assinatura, o que invalidou **todos** os
tokens de **todos** os usuários de uma vez. Foi a coisa certa a fazer e
derrubou o aplicativo de quatro mil pessoas por sete minutos.

Na semana seguinte, a expiração virou uma hora e a equipe passou a ter uma
lista de revogação. Roberto perguntou se aquilo não ia "deslogar o cliente o
tempo todo". Marina explicou o que é *refresh token*.

Foi uma boa reunião.
:::

:::art caption="Um token de dez anos é uma chave que continua abrindo a porta depois da demissão."
src="um-token-de-dez-anos-e-uma-chave-que-continua-abrindo-a-porta-depois-da-demissao.png"
Charge editorial minimalista: crachá corporativo pendurado em um cordão,
flutuando sozinho no ar, com a data "válido até 2035" impressa em destaque e
a foto substituída por uma silhueta cinza. Ao fundo, uma porta de escritório
com um leitor de cartão piscando verde. Ao lado, uma mesa vazia com uma caixa
de pertences. Fundo branco, poucos elementos, humor visual seco e levemente
sombrio, estética editorial de tecnologia.
:::

:::summary
- JWT é assinado, não criptografado: qualquer um lê o payload.
- A assinatura garante integridade; o segredo mora em variável de ambiente.
- O filtro lê `Authorization: Bearer`, valida e popula o contexto — e sempre
  segue a cadeia.
- Login errado responde sempre igual, independentemente do motivo.
- Token não se cancela: use expiração curta e trate revogação como exceção.
:::

:::checkpoint
Você emite um token no login, valida em um filtro, protege as rotas e sabe
explicar por que não é possível deslogar alguém imediatamente.
:::

:::milestone
A API autentica. Quem tem token é reconhecido em toda requisição e quem não
tem recebe `401`. Falta decidir o que cada um pode fazer — capítulo 33.
:::

:::exercise level=1
Faça login, copie o token, cole em `jwt.io` e leia o payload. Depois altere
uma letra do token e tente usá-lo.

:::answer
O payload é legível por qualquer pessoa — a lição principal do capítulo.
Alterar qualquer caractere invalida a assinatura e o filtro limpa o contexto,
resultando em `401`. O token é à prova de adulteração, não de leitura.
:::

:::exercise level=2
Mude a expiração para 10 segundos, faça login, espere e use o token.
Observe a exceção e escreva um handler que devolva `401` com mensagem clara.

:::answer
```java
@ExceptionHandler(ExpiredJwtException.class)
public ResponseEntity<ApiError> expirado(
        ExpiredJwtException e, HttpServletRequest req) {
    return resposta(HttpStatus.UNAUTHORIZED,
            "sessão expirada, faça login novamente", req);
}
```
Sem esse handler o cliente recebe um `401` genérico e não sabe se deve pedir
a senha de novo ou renovar o token. A mensagem é parte do contrato.
:::

:::exercise level=3
Implemente o *refresh token*: um segundo token, de vida longa, guardado no
banco, que permite emitir um novo token de acesso. Explique por que ele
precisa estar no banco.

:::answer
Porque é justamente o que devolve ao servidor o poder de cancelar. O token de
acesso continua *stateless* e de vida curta; o de renovação é uma linha em
uma tabela, que pode ser apagada em uma demissão. Você ganha escala nos 99%
das requisições e controle no 1% que importa — e essa é a resposta para o
dilema que fechou o capítulo.
:::
