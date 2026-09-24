---
title: "JWT"
number: 35
slug: jwt
part: p7
kicker: "Um crachá que o servidor emite, assina e não guarda — e é o \"não guarda\" que custa caro."
goal: >-
  Emitir e verificar tokens assinados, escolher o conteúdo e a validade,
  implementar renovação, e entender por que revogar um JWT é difícil.
---

O login do capítulo @cap:autenticacao confirma quem é a pessoa. Agora é
preciso que a requisição seguinte também saiba — sem pedir a senha de novo e
sem o servidor guardar nada.

O JWT — *JSON Web Token* — resolve isso com uma ideia simples: o servidor
escreve um bilhete, assina, e entrega. Quem apresentar o bilhete com a
assinatura válida é quem o bilhete diz ser.

## A anatomia

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
.eyJzdWIiOiI0MiIsImV4cCI6MTc5MDAwMDAwMH0
.mV3qKZ8fHc7xQyR1nL9vTt2bWuX0aY5cE8dG
```

Três partes separadas por ponto:

:::anatomy title="As três partes de um JWT"
lang: json
code: |
  {"alg": "HS256", "typ": "JWT"}
  {"sub": "42", "exp": 1790000000, "papel": "admin"}
  assinatura
notes:
  - { line: 1, text: "**Cabeçalho**: qual algoritmo assinou. Codificado, não cifrado." }
  - { line: 2, text: "**Carga**: as afirmações. Qualquer pessoa consegue ler." }
  - { line: 2, text: "`sub` é o sujeito; `exp` é o instante de expiração." }
  - { line: 3, text: "**Assinatura**: prova que as duas partes acima não foram alteradas." }
:::

:::warning
As duas primeiras partes são **Base64, não criptografia**. Qualquer pessoa
com o token lê o conteúdo inteiro — basta colar em <https://jwt.io> ou rodar
um decodificador de três linhas. Nunca coloque senha, CPF, endereço ou
qualquer dado sensível dentro de um JWT. A assinatura garante que ninguém
**alterou**; ela não esconde nada.
:::

## Emitir

```text
$ pip install pyjwt
```

```python title="app/security.py" numbered
from datetime import datetime, timedelta, timezone

import jwt

ALGORITMO = "HS256"


def criar_token(usuario_id: int, minutos: int = 30) -> str:
    agora = datetime.now(timezone.utc)
    carga = {
        "sub": str(usuario_id),
        "iat": agora,
        "exp": agora + timedelta(minutes=minutos),
        "typ": "acesso",
    }
    return jwt.encode(
        carga, get_config().secret_key, algorithm=ALGORITMO
    )
```

:::pitfall
`sub` precisa ser **texto**, mesmo quando o identificador é um número. A
especificação exige, e várias bibliotecas recusam o token com um erro que
não menciona isso. `str(usuario_id)` na emissão e `int(...)` na leitura.
:::

## Verificar

```python title="app/security.py" numbered
class TokenInvalido(Exception):
    pass


def ler_token(token: str) -> int:
    try:
        carga = jwt.decode(
            token,
            get_config().secret_key,
            algorithms=[ALGORITMO],
        )
    except jwt.ExpiredSignatureError as erro:
        raise TokenInvalido("token expirado") from erro
    except jwt.InvalidTokenError as erro:
        raise TokenInvalido("token inválido") from erro

    if carga.get("typ") != "acesso":
        raise TokenInvalido("tipo de token incorreto")

    return int(carga["sub"])
```

:::warning
`algorithms=[ALGORITMO]` é obrigatório e é uma **lista fechada**. Houve uma
época em que bibliotecas aceitavam o algoritmo declarado no cabeçalho do
próprio token — incluindo `"alg": "none"`, que significa "sem assinatura".
Um atacante trocava a carga, apagava a assinatura, declarava `none` e era
aceito. As bibliotecas atuais recusam isso, e a lista explícita é o que
garante que nenhuma configuração futura reabra a porta.
:::

## A dependência que identifica

```python title="app/dependencies.py" numbered
from fastapi.security import OAuth2PasswordBearer

oauth2 = OAuth2PasswordBearer(tokenUrl="auth/login")


def usuario_atual(
    token: Annotated[str, Depends(oauth2)],
    servico: UsuarioServicoDep,
) -> Usuario:
    credenciais_invalidas = HTTPException(
        status_code=401,
        detail="credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        usuario_id = ler_token(token)
    except TokenInvalido as erro:
        raise credenciais_invalidas from erro

    usuario = servico.buscar(usuario_id)
    if usuario is None or not usuario.ativo:
        raise credenciais_invalidas

    return usuario


UsuarioDep = Annotated[Usuario, Depends(usuario_atual)]
```

```python title="uso.py" numbered
@router.post("", response_model=ProdutoLer, status_code=201)
def criar(
    dados: ProdutoCriar,
    servico: ServicoDep,
    usuario: UsuarioDep,
):
    return servico.criar(dados, criado_por=usuario.id)
```

Declarar `usuario: UsuarioDep` é tudo: a rota passa a exigir token, e o
`/docs` ganha o botão **Authorize**, porque `OAuth2PasswordBearer` descreve
o esquema de segurança no OpenAPI.

Repare que `usuario_atual` **consulta o banco**. Isso custa uma consulta por
requisição e compra duas coisas: o usuário desativado deixa de entrar na
hora, e os dados vêm atualizados. A alternativa — confiar só no que está no
token — é mais rápida e transforma cada token válido numa autorização de
trinta minutos que nada cancela.

:::diagram type="sequence" caption="Login uma vez, token em toda requisição seguinte."
actors:
  - { id: c, name: "Cliente" }
  - { id: a, name: "API" }
  - { id: d, name: "Banco" }
messages:
  - { from: c, to: a, text: "POST /auth/login (e-mail, senha)" }
  - { from: a, to: d, text: "busca usuário" }
  - { from: a, to: c, text: "token (30 min)", dashed: true }
  - { from: c, to: a, text: "GET /produtos + Bearer token" }
  - { from: a, to: a, text: "verifica assinatura e exp" }
  - { from: a, to: c, text: "200 OK", dashed: true }
:::

## O problema da revogação

Um JWT válido continua válido até expirar. O servidor não o guardou, não
tem lista do que emitiu, e não consegue invalidá-lo.

Três consequências práticas:

- Demitir alguém não derruba a sessão dele.
- Trocar a senha não invalida os tokens antigos.
- Um token vazado funciona até o fim da validade, em qualquer lugar do
  mundo.

:::key
Por isso a validade do token de acesso é **curta** — quinze a trinta
minutos. A janela de estrago de um token vazado é exatamente o tempo que
falta para ele expirar. Token de acesso com validade de dias é a decisão que
transforma um vazamento pequeno num incidente grande.
:::

## Renovação

Token curto exigiria login a cada trinta minutos. O par de tokens resolve:

```python title="renovacao.py" numbered
import hashlib


def hash_refresh(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def criar_par(
    usuario_id: int, servico: UsuarioServicoDep
) -> dict[str, str]:
    refresh = criar_refresh(usuario_id, dias=14)
    servico.guardar_refresh(
        usuario_id=usuario_id,
        hash_token=hash_refresh(refresh),
    )
    return {
        "access_token": criar_token(usuario_id, minutos=30),
        "refresh_token": refresh,
        "token_type": "bearer",
    }


@router.post("/renovar")
def renovar(dados: RenovarEntrada, servico: UsuarioServicoDep):
    usuario_id = ler_refresh(dados.refresh_token)
    sessao = servico.consumir_refresh(
        usuario_id, hash_refresh(dados.refresh_token)
    )
    if sessao is None:
        raise HTTPException(401, "sessão encerrada")
    # Consumir invalida o token anterior antes de emitir o próximo.
    return criar_par(usuario_id, servico)
```

`guardar_refresh` armazena apenas o hash. `consumir_refresh` precisa fazer a
busca e a revogação na mesma transação; assim, duas requisições simultâneas
não conseguem renovar a mesma sessão. Se o token antigo aparecer de novo,
trate isso como possível replay e encerre a família de tokens, em vez de
emitir outro par silenciosamente.

| | Acesso | Renovação |
|---|---|---|
| Validade | 15–30 min | 7–30 dias |
| Vai em toda requisição | sim | não |
| Guardado no servidor | não | **sim**, para poder revogar |

Tabela: O token de renovação é guardado justamente para ter o que o de
acesso não tem: a possibilidade de encerrar a sessão.

Guardar o hash dos tokens de renovação emitidos é o que permite o botão
"sair de todos os dispositivos" — e é a resposta honesta ao problema da
revogação: **ela não é resolvida pelo JWT, é resolvida por um estado que
você decidiu manter**.

:::pitfall
Uma alternativa mais barata, e frequentemente suficiente: guardar no usuário
um campo `tokens_validos_apos`. Ao trocar a senha ou desativar a conta, ele
recebe a hora atual, e a verificação compara com o `iat` do token. Um campo,
uma comparação, e todos os tokens anteriores morrem juntos — sem lista de
tokens, sem armazenamento extra.
:::

## Onde o cliente guarda

| Lugar | Risco |
|---|---|
| `localStorage` | qualquer script na página lê (XSS) |
| cookie `HttpOnly` + `Secure` + `SameSite` | protegido de XSS; exige cuidado com CSRF |
| memória da aplicação | mais seguro; perde-se ao recarregar |

Tabela: Para aplicação web em navegador, cookie `HttpOnly` é a recomendação
atual. Para aplicativo móvel, o armazenamento seguro do sistema.

## A chave secreta

```text title=".env"
SECRET_KEY=8f3c1d...  # 32 bytes aleatórios, gerados uma vez
```

```text
$ python -c "import secrets; print(secrets.token_hex(32))"
```

:::warning
Quem tem a chave emite tokens válidos para qualquer usuário, inclusive
administradores. Ela não vai para o repositório, não vai para o log, e não
tem valor padrão que funcione — a aplicação deve **recusar subir** sem ela,
como o capítulo @cap:modulos-e-ambiente mostrou com `os.environ["X"]`.

Trocar a chave invalida todos os tokens de uma vez. Isso é um incômodo e,
num incidente, é exatamente a ferramenta que você quer ter.
:::

:::summary
- O JWT é assinado, não cifrado: qualquer pessoa lê a carga.
- `algorithms=[...]` explícito na verificação, sempre.
- `sub` é texto; `exp` é obrigatório e curto.
- A dependência que identifica também consulta o banco — e é o que faz um
  usuário desativado cair na hora.
- Revogação não é resolvida pelo JWT: é resolvida por estado que você
  mantém.
- Par de tokens: acesso curto, renovação longa e guardada.
- Sem a chave secreta, a aplicação não sobe.
:::

:::checkpoint
Você emite e verifica tokens, protege rotas com uma dependência, sabe
explicar por que um JWT não se revoga e implementa a alternativa que resolve
o caso real.
:::

:::exercise level=1
Proteja as rotas de criação, atualização e remoção de produtos exigindo
usuário autenticado, deixando as de leitura públicas.

:::answer
```python
@router.post("", response_model=ProdutoLer, status_code=201)
def criar(
    dados: ProdutoCriar, servico: ServicoDep, usuario: UsuarioDep
):
    return servico.criar(dados)
```
Ou, para o grupo inteiro, um segundo router com
`dependencies=[Depends(usuario_atual)]` — a forma do capítulo
@cap:dependency-injection, que evita repetir o parâmetro em cada rota.
:::

:::exercise level=2
Implemente o campo `tokens_validos_apos` no usuário e faça a troca de senha
invalidar todos os tokens anteriores.

:::answer
```python
class Usuario(Base):
    tokens_validos_apos: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


def trocar_senha(self, usuario: Usuario, nova: str) -> None:
    usuario.senha_hash = gerar_hash(nova)
    usuario.tokens_validos_apos = datetime.now(timezone.utc)
    self.session.commit()


# na dependência, depois de carregar o usuário
emitido = datetime.fromtimestamp(carga["iat"], timezone.utc)
if emitido < usuario.tokens_validos_apos:
    raise credenciais_invalidas
```
Repare que isso só funciona porque a dependência já consultava o banco. Se
ela confiasse apenas no token, não haveria onde comparar.
:::

:::exercise level=3
Um colega sugere colocar no token o nome, o e-mail, a lista de permissões e
o nome da cooperativa, "para evitar a consulta ao banco em toda
requisição". Avalie.

:::answer
A economia é real: uma consulta a menos por requisição, numa API que pode
fazer milhares por minuto. E os três problemas também são reais.

**O primeiro é a obsolescência.** O token vale trinta minutos. Se uma
permissão for revogada aos cinco, a pessoa continua com ela por vinte e
cinco minutos. Para uma permissão administrativa, isso não é aceitável.

**O segundo é o vazamento.** Nome e e-mail dentro do token significam nome e
e-mail no `localStorage` do navegador, no log do proxy que registrou a URL
com o token, e na tela de quem colou o token num depurador online para
entender um erro. A carga não é cifrada.

**O terceiro é o tamanho.** O token vai em **toda** requisição, em um
cabeçalho. Uma lista de permissões grande produz tokens de vários
kilobytes, e alguns servidores rejeitam cabeçalhos acima de 8 KB — com um
erro que não menciona o token.

O desenho que eu defenderia é intermediário. No token: `sub`, `exp`, `iat` e
no máximo um papel de granularidade grossa (`admin`, `operador`), que muda
raramente e cujo atraso de trinta minutos é tolerável. No banco: tudo o
mais, buscado pela dependência.

E, se a consulta por requisição for medida como gargalo — medida, não
suposta —, a resposta não é inchar o token: é um cache de usuário com
validade de segundos, que dá a mesma economia e mantém a revogação quase
imediata.
:::
