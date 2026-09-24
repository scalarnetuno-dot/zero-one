---
title: "Autenticação"
number: 34
slug: autenticacao
part: p7
kicker: "Guardar senha é a única parte do sistema em que improvisar é indefensável."
goal: >-
  Guardar senhas com hash lento, escrever o cadastro e o login, entender a
  diferença entre sessão e token, e reconhecer os erros clássicos de quem
  implementa autenticação pela primeira vez.
---

Até aqui, qualquer pessoa com o endereço da API pode apagar o catálogo
inteiro. A primeira metade do problema é *quem é
você?* — e o capítulo @cap:usuarios-e-permissoes resolve a segunda — *o que
você pode?*

:::key
Uma API sem autenticação não é privada. Ela é apenas desconhecida — e
"desconhecida" é uma propriedade que dura até o primeiro varredor de portas
ou o primeiro endereço colado num chat.
:::

## Senha nunca é guardada

A regra é absoluta e não tem exceção: o banco **não** guarda a senha. Ele
guarda um resumo criptográfico que permite conferir a senha e não permite
recuperá-la.

| Forma | Serve? |
|---|---|
| texto puro | não |
| criptografia reversível | não — quem tem a chave tem as senhas |
| MD5, SHA-1, SHA-256 | não — rápidos demais |
| bcrypt, scrypt, Argon2 | **sim** |

Tabela: SHA-256 é um bom algoritmo de resumo e uma péssima escolha para
senha, pelo mesmo motivo que o torna bom em outros usos: a velocidade.

Uma placa de vídeo comum calcula bilhões de SHA-256 por segundo. Contra uma
lista de senhas comuns, isso quebra a maioria das contas em minutos. Os
algoritmos próprios de senha são **deliberadamente lentos** e têm um
parâmetro de custo, ajustável conforme o hardware melhora.

:::term Sal
Um valor aleatório, diferente para cada usuário, misturado à senha antes do
resumo. Ele impede que duas pessoas com a mesma senha tenham o mesmo hash e
inutiliza tabelas pré-calculadas. As bibliotecas modernas geram e guardam o
sal dentro do próprio hash — você não precisa gerenciá-lo.
:::

## Gerando e conferindo

```text
$ pip install "pwdlib[argon2]"
```

```python title="app/security.py" numbered
from pwdlib import PasswordHash

hasher = PasswordHash.recommended()


def gerar_hash(senha: str) -> str:
    return hasher.hash(senha)


def conferir_senha(senha: str, hash_guardado: str) -> bool:
    return hasher.verify(senha, hash_guardado)
```

```text
>>> gerar_hash("segredo123")
'$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ...'
```

Esse texto guarda tudo: o algoritmo, os parâmetros de custo, o sal e o
resumo. É por isso que `verify` precisa apenas da senha e dele — e é por
isso que trocar os parâmetros no futuro não invalida os hashes antigos.

:::warning
Nunca escreva a sua própria comparação. `if hash(senha) == guardado:` parece
equivalente e não é: a comparação de textos em Python para no primeiro
caractere diferente, e o tempo que ela leva vaza informação sobre o
conteúdo. As bibliotecas usam comparação de tempo constante.
:::

## O modelo de usuário

```python title="app/models/usuario.py" numbered
class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(160), unique=True, index=True
    )
    senha_hash: Mapped[str] = mapped_column(String(255))
    nome: Mapped[str] = mapped_column(String(120))
    ativo: Mapped[bool] = mapped_column(default=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

O campo se chama `senha_hash`, e não `senha`. O nome importa: ele é a
documentação que impede alguém de atribuir texto puro ali por distração.

`String(255)` porque o hash do Argon2 passa de cem caracteres e cresce se
os parâmetros mudarem. Dimensionar apertado é criar uma migração futura.

## O esquema: a senha só entra

```python title="app/schemas/usuario.py" numbered
class UsuarioCriar(BaseModel):
    nome: Annotated[str, Field(min_length=2, max_length=120)]
    email: EmailStr
    senha: Annotated[str, Field(min_length=8, max_length=128)]


class UsuarioLer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    ativo: bool
```

Aqui a separação de esquemas do capítulo @cap:schemas deixa de ser questão
de organização e vira segurança: `UsuarioLer` **não tem** `senha` nem
`senha_hash`. Não existe caminho pelo qual eles saiam numa resposta.

:::pitfall
O `max_length=128` na senha não é capricho. Algumas implementações de hash
têm limite de entrada — o bcrypt trunca em 72 bytes, silenciosamente — e
senhas de megabytes já foram usadas para negação de serviço, porque o hash
lento fica lento demais. Limite mínimo **e** máximo.
:::

## Cadastro

```python title="app/services/usuario.py" numbered
def criar(self, dados: UsuarioCriar) -> Usuario:
    email = dados.email.strip().lower()

    if self.repo.buscar_por_email(email):
        raise EmailJaCadastrado(email)

    usuario = Usuario(
        nome=dados.nome.strip(),
        email=email,
        senha_hash=gerar_hash(dados.senha),
    )
    self.repo.criar(usuario)
    self.session.commit()
    return usuario
```

:::warning
Esse `EmailJaCadastrado` com `409` revela que o e-mail existe no sistema —
e isso é um vazamento real em serviços onde ser usuário é informação
sensível. A alternativa é responder sempre `202` e enviar um e-mail
diferente conforme o caso: "confirme seu cadastro" ou "você já tem conta". O
preço é uma experiência pior no caso comum. Para o catálogo de uma
cooperativa, o `409` é aceitável; para um serviço de saúde, não é.
:::

## Login

```python title="app/routers/auth.py" numbered
from fastapi.security import OAuth2PasswordRequestForm


@router.post("/login")
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    servico: UsuarioServicoDep,
):
    usuario = servico.autenticar(form.username, form.password)
    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="e-mail ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"acesso": "ok", "usuario_id": usuario.id}
```

```python title="app/services/usuario.py" numbered
def autenticar(self, email: str, senha: str) -> Usuario | None:
    usuario = self.repo.buscar_por_email(email.strip().lower())

    if usuario is None:
        gerar_hash(senha)      # gasta o mesmo tempo
        return None

    if not conferir_senha(senha, usuario.senha_hash):
        return None

    if not usuario.ativo:
        return None

    return usuario
```

Três decisões aqui merecem nome.

A mensagem é **"e-mail ou senha inválidos"**, sem dizer qual. Dizer "usuário
não encontrado" entrega ao atacante a lista de quem tem conta.

O `gerar_hash(senha)` no caminho do usuário inexistente parece desperdício e
é proposital: sem ele, a resposta para um e-mail que não existe volta em
microssegundos e a de uma senha errada volta em centenas de milissegundos. A
diferença de tempo diz exatamente o que a mensagem tentou esconder.

E o usuário inativo recebe a mesma resposta genérica — a distinção entre
"não existe", "senha errada" e "desativado" é informação interna.

:::story Os três segundos de diferença
Elias abriu o painel de latência e apontou para duas faixas.

— Login com e-mail que existe: 340 milissegundos. Com e-mail que não existe:
4 milissegundos.

— E daí? — perguntou Rafa. — A resposta é a mesma.

— A resposta é a mesma. O tempo não é. — Ele rodou um laço que tentava mil
e-mails, cronometrando. Em dois minutos tinha a lista de quem era cliente da
cooperativa. — Não precisei de senha nenhuma. Eu só precisei de um relógio.
:::

## Sessão ou token

Confirmada a identidade, é preciso mantê-la nas requisições seguintes. Há
dois caminhos:

| | Sessão no servidor | Token assinado |
|---|---|---|
| Onde mora o estado | no servidor | no próprio token |
| Revogar na hora | fácil | difícil |
| Vários servidores | precisa de armazenamento comum | não precisa |
| Cliente natural | navegador, com cookie | app, outro serviço |

Tabela: Não há vencedor. Há um custo em cada coluna, e quem diz que um dos
dois é sempre melhor está vendendo alguma coisa.

O capítulo @cap:jwt implementa o segundo, que é o formato usual de API REST
consumida por aplicativos — e trata com honestidade do preço da revogação.

:::pitfall
Autenticação sem HTTPS é teatro. A senha viaja em texto pela rede, e o token
também. Isso vale inclusive para "só dentro da rede da empresa" — a rede da
empresa é o lugar onde a maioria dos incidentes começa. Em produção, TLS não
é uma etapa posterior.
:::

:::summary
- A senha nunca é guardada; guarda-se um hash lento, com sal.
- SHA-256 é rápido demais; use Argon2, bcrypt ou scrypt.
- O campo se chama `senha_hash`, e o esquema de saída não o tem.
- Limite mínimo **e** máximo de tamanho de senha.
- A resposta de login não distingue e-mail inexistente de senha errada — nem
  na mensagem, nem no tempo.
- Sessão e token têm custos diferentes; revogação é o ponto de decisão.
- Sem HTTPS, nada disso vale.
:::

:::exercise level=1
Implemente o endpoint `POST /usuarios` que cadastre um usuário e devolva
`UsuarioLer`, sem nunca expor a senha.

:::answer
```python
@router.post(
    "/usuarios", response_model=UsuarioLer, status_code=201
)
def criar(dados: UsuarioCriar, servico: UsuarioServicoDep):
    return servico.criar(dados)
```
O `response_model` filtra: mesmo que o serviço devolva o objeto completo com
`senha_hash`, ele não atravessa.
:::

:::exercise level=2
Acrescente ao `UsuarioCriar` a exigência de que a senha tenha ao menos uma
letra e um dígito, com mensagem clara.

:::answer
```python
@field_validator("senha")
@classmethod
def senha_forte(cls, v: str) -> str:
    if not any(c.isalpha() for c in v):
        raise ValueError("a senha precisa ter ao menos uma letra")
    if not any(c.isdigit() for c in v):
        raise ValueError("a senha precisa ter ao menos um dígito")
    return v
```
Vale saber que as recomendações atuais do NIST desaconselham regras de
composição como esta: elas produzem `Senha123!` em vez de senhas boas. O que
funciona melhor é exigir **comprimento** e comparar com uma lista de senhas
vazadas. Se você for implementar só uma coisa, implemente o comprimento
mínimo maior.
:::

:::exercise level=3
Sua equipe precisa migrar um sistema antigo com dez mil senhas guardadas em
MD5. Descreva a migração sem pedir a senha de ninguém e sem manter o MD5.

:::answer
Não é possível converter um MD5 em Argon2: o hash não é reversível, e você
não tem as senhas. A migração é **gradual, no login**.

```python
def autenticar(self, email, senha):
    usuario = self.repo.buscar_por_email(email)
    if usuario is None:
        gerar_hash(senha)
        return None

    if usuario.senha_hash.startswith("$argon2"):
        if not conferir_senha(senha, usuario.senha_hash):
            return None
    else:
        legado = hashlib.md5(senha.encode()).hexdigest()
        if not secrets.compare_digest(legado, usuario.senha_hash):
            return None
        usuario.senha_hash = gerar_hash(senha)
        self.session.commit()

    return usuario
```

No momento do login, você tem a senha em texto por um instante — e é o único
momento em que a tem. Aproveite-o: confira pelo formato antigo e regrave no
formato novo.

**O plano completo**, porque o código sozinho não resolve:

1. Implantar o código acima e medir quantos usuários ainda têm hash antigo.
2. Depois de um período — três meses é comum —, forçar a redefinição de
   senha dos que sobraram, por e-mail, e desativar o caminho legado.
3. Remover o código do MD5 e a dependência.

E uma decisão que precisa ser tomada logo no dia 1: os hashes MD5 **já estão
comprometidos**, porque se o banco vazou uma vez, vazou com eles. Se houver
qualquer indício de vazamento, o passo 2 não espera três meses — ele é
imediato, e todo mundo redefine.
:::
