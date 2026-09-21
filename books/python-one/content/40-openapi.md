---
title: "OpenAPI"
number: 40
slug: openapi
part: p9
kicker: "Documentação que não nasce do código começa a mentir no dia seguinte."
goal: >-
  Enriquecer a documentação gerada, descrever respostas de erro, versionar a
  API e usar o esquema para gerar clientes em outras linguagens.
---

Desde o capítulo @cap:o-que-vamos-construir existe um `/docs` funcionando
que ninguém escreveu. A tarefa agora é transformá-lo de "aceitável" em
"suficiente para alguém integrar sem perguntar nada".

E a razão de isso valer a pena é uma só: essa documentação **não
desatualiza**. Ela é gerada do mesmo código que atende a requisição. Um
documento à parte — num wiki, numa planilha, num PDF — começa correto e
diverge na primeira alteração que alguém esquecer de replicar.

## O que já vem de graça

| Vem de | Vira |
|---|---|
| tipo do parâmetro | tipo e validação na documentação |
| `response_model` | esquema da resposta |
| `status_code` | status de sucesso |
| `Enum` | lista fechada de opções |
| `Field(gt=0, ...)` | restrições visíveis |
| `tags` do router | agrupamento |

Tabela: Tudo isso é consequência de decisões que você já tomou por outros
motivos.

## Metadados da aplicação

```python title="app/main.py" numbered
app = FastAPI(
    title="Catálogo Sabiá",
    version="1.3.0",
    summary="Catálogo de produtos da Cooperativa Sabiá.",
    description=(
        "API REST do catálogo. Autenticação por token Bearer; "
        "peça o seu em `POST /auth/login`.\n\n"
        "Preços viajam como **texto** para preservar a "
        "precisão decimal."
    ),
    contact={
        "name": "Time de tecnologia",
        "email": "dev@sabia.coop",
    },
    license_info={"name": "Uso interno"},
    openapi_tags=[
        {
            "name": "produtos",
            "description": "Cadastro e consulta do catálogo.",
        },
        {
            "name": "auth",
            "description": "Login e renovação de token.",
        },
    ],
)
```

Aquela frase sobre preço como texto vale mais do que parece: é o tipo de
decisão que gera uma pergunta em toda integração nova. Escrita ali, ela é
respondida antes de ser feita.

## Documentando a rota

```python title="rota_documentada.py" numbered
@router.post(
    "",
    response_model=ProdutoLer,
    status_code=201,
    summary="Cadastra um produto",
    response_description="Produto criado, com identificador",
    responses={
        409: {
            "description": "Já existe produto com esse nome",
            "content": {
                "application/json": {
                    "example": {
                        "tipo": "produto_ja_existe",
                        "mensagem": "produto 'Tomate' já cadastrado",
                    }
                }
            },
        },
        422: {"description": "Campos inválidos"},
    },
)
def criar(dados: ProdutoCriar, servico: ServicoDep):
    """
    Cadastra um produto no catálogo.

    O nome é normalizado — espaços das pontas e espaços
    repetidos no meio são removidos — antes da verificação
    de duplicidade.
    """
    return servico.criar(dados)
```

A **docstring** vira a descrição longa do endpoint, com Markdown. É a
promessa que o capítulo @cap:funcoes fez: a documentação escrita junto da
função aparece na documentação da API, sem uma linha a mais.

:::key
O campo `responses` é o mais esquecido e o mais útil. Sem ele, a
documentação mostra só o caminho feliz, e quem integra descobre o `409`
quando ele acontecer em produção. Documentar os erros é documentar metade do
contrato.
:::

:::pitfall
Descrever em `responses` um erro que a rota **não** devolve é pior que não
descrever nada: quem integra escreve um tratamento para um caso impossível e
confia num contrato que não existe. Se a lista começar a divergir, o teste
do capítulo @cap:testando-a-api sobre o `/openapi.json` é o que a mantém
honesta.
:::

## Exemplos

```python title="exemplos.py" numbered
class ProdutoCriar(ProdutoBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nome": "Tomate italiano",
                    "preco": "8.90",
                    "estoque": 120,
                }
            ]
        }
    )
```

O botão **Try it out** passa a vir preenchido com um corpo válido. Em
integração, isso vale mais que um parágrafo de explicação: a pessoa clica,
executa e vê a resposta real.

## Marcando o que vai sair

```python
@router.get("/antigo", deprecated=True)
def rota_antiga():
    ...
```

A rota aparece riscada na documentação. É a etapa 2 do plano de
transição do capítulo @cap:schemas, agora visível para quem consome sem
precisar de um comunicado por e-mail.

## Versionar

```python title="versao.py" numbered
v1 = APIRouter(prefix="/v1")
v1.include_router(produtos.router)

app.include_router(v1)
```

Três formas de versionar convivem no mundo:

| Forma | Exemplo | Nota |
|---|---|---|
| no caminho | `/v1/produtos` | explícita, fácil de rotear, a mais comum |
| no cabeçalho | `Accept: ...;version=1` | "mais pura", difícil de testar no navegador |
| por data | `X-Api-Version: 2026-03-14` | ótima com muitos clientes, cara de manter |

Tabela: A primeira ganha por um motivo prático: dá para colar a URL num
navegador e ver o que ela devolve.

:::warning
Versão nova é uma superfície nova para manter: dois conjuntos de rotas, dois
de testes, duas documentações. Antes de criar a `/v2`, verifique se a
mudança cabe numa transição por campo — acrescentar, marcar como obsoleto,
medir, remover. Na maioria dos casos, cabe.
:::

## Gerar cliente

```text
$ curl http://localhost:8000/openapi.json > openapi.json
$ npx @hey-api/openapi-ts -i openapi.json -o src/api
```

O front-end passa a ter funções tipadas, geradas, que acompanham a API. Um
campo removido vira erro de compilação lá — antes de virar tela em branco no
celular de um produtor.

Isso funciona **na proporção do cuidado** que você teve até aqui: sem
`response_model`, o cliente gerado é `any`; sem `operation_id` estável, os
nomes das funções mudam a cada refatoração.

```python
@router.get("", operation_id="listarProdutos")
```

:::trivia
O OpenAPI se chamava Swagger e foi doado à Linux Foundation em 2015,
virando um padrão aberto. O nome antigo sobreviveu nas ferramentas: a página
interativa do FastAPI ainda é o *Swagger UI*. É por isso que você vai
encontrar os dois nomes na mesma frase, em documentação de todo mundo, sem
explicação.
:::

## A documentação em produção

```python title="producao.py" numbered
config = get_config()
interno = config.app_ambiente != "producao"

app = FastAPI(
    docs_url="/docs" if interno else None,
    redoc_url=None,
    openapi_url="/openapi.json" if interno else None,
)
```

Expor ou não a documentação de uma API interna é uma decisão de risco, não
de gosto. Ela entrega a lista completa de endpoints, parâmetros e formatos —
o que é exatamente o que se quer para uma API pública e exatamente o que não
se quer numa administrativa.

:::pitfall
Esconder o `/docs` **não** é segurança: as rotas continuam lá e respondem.
Isso é redução de superfície, não proteção. A proteção é a autenticação do
capítulo @cap:jwt. Esconder a documentação de uma API sem autenticação é
trancar a porta e deixar a janela aberta com a cortina fechada.
:::

:::summary
- A documentação gerada do código não desatualiza; a escrita à parte,
  sempre.
- `summary`, docstring e `responses` transformam o `/docs` em material de
  integração.
- Documentar o erro é documentar metade do contrato.
- `deprecated=True` comunica a transição sem depender de e-mail.
- Versão no caminho é a forma prática; versão nova é superfície a manter.
- Cliente gerado depende de `response_model` e `operation_id` estáveis.
- Esconder `/docs` reduz superfície e não substitui autenticação.
:::

:::exercise level=1
Acrescente `summary`, `response_description` e docstring à rota de busca de
produto.

:::answer
```python
@router.get(
    "/{produto_id}",
    response_model=ProdutoLer,
    summary="Busca um produto pelo identificador",
    response_description="O produto encontrado",
)
def buscar(produto_id: int, servico: ServicoDep):
    """Devolve um produto do catálogo.

    Responde `404` quando o identificador não existe.
    """
    return servico.buscar(produto_id)
```
:::

:::exercise level=1
Acrescente `operation_id` estável às cinco rotas de produtos e explique o
efeito no cliente gerado.

:::answer
```python
@router.get("", operation_id="listarProdutos")
@router.get("/{produto_id}", operation_id="buscarProduto")
@router.post("", operation_id="criarProduto")
@router.put("/{produto_id}", operation_id="atualizarProduto")
@router.delete("/{produto_id}", operation_id="apagarProduto")
```
Sem `operation_id`, o FastAPI gera o nome a partir do nome da função **e**
do caminho — algo como `listar_produtos__get`. Renomear a função, mover a
rota de arquivo ou mudar o prefixo altera esse nome, e o cliente gerado
ganha funções novas enquanto as antigas somem: um diff enorme, num projeto
que nem é o seu, causado por uma refatoração interna.
:::

:::exercise level=2
Documente as respostas `404` e `422` da rota de atualização, com exemplo de
corpo.

:::answer
```python
RESPOSTAS_PADRAO = {
    404: {
        "description": "Produto não encontrado",
        "content": {
            "application/json": {
                "example": {
                    "tipo": "produto_nao_encontrado",
                    "mensagem": "produto 999 não encontrado",
                    "recurso_id": 999,
                }
            }
        },
    },
    422: {"description": "Campos inválidos"},
}


@router.put("/{produto_id}", responses=RESPOSTAS_PADRAO)
def atualizar(...):
    ...
```
Extrair o dicionário para uma constante compartilhada é o que impede que as
dez rotas descrevam o mesmo `404` de dez jeitos diferentes.
:::

:::exercise level=3
A API tem quatro clientes e precisa mudar o formato de `preco` de texto para
objeto — `{"valor": "8.90", "moeda": "BRL"}`. Proponha o plano completo.

:::answer
Essa mudança **não** cabe numa transição por campo: o tipo de um campo
existente está mudando, e não há como um cliente antigo ler um objeto onde
esperava texto. Só há dois caminhos honestos.

**Caminho A — campo novo ao lado.** A resposta passa a ter `preco` (texto,
como sempre) e `preco_detalhado` (o objeto). Os clientes migram um por um;
quando o log mostrar que ninguém lê o antigo, ele é marcado como obsoleto e,
depois, removido. Custo: um campo redundante por alguns meses e um nome
provisório que vai ficar para sempre se ninguém concluir a transição.

**Caminho B — versão nova.** `/v2` com o formato novo, `/v1` congelado e com
data de encerramento anunciada. Custo: duas superfícies. O que torna isso
gerenciável é as duas chamarem o **mesmo** serviço, com esquemas de resposta
diferentes — o desenho em camadas do capítulo @cap:service paga
exatamente aqui: nenhuma regra é duplicada, só a tradução.

**Eu escolheria B**, por dois motivos: quatro clientes é pouco, e a mudança
tem cara de ser a primeira de várias — se a moeda está entrando, é porque a
cooperativa vai exportar, e outras coisas vão mudar junto.

**O plano:**

1. Anunciar por escrito, com a data de encerramento da `/v1`, antes de
   escrever código.
2. Publicar a `/v2` com o formato novo e o esquema `ProdutoLerV2`.
3. Instrumentar: registrar por cliente qual versão cada um usa. Sem essa
   medição, a etapa 5 vira um chute.
4. Marcar a `/v1` como obsoleta na documentação e acompanhar o log.
5. Encerrar a `/v1` na data anunciada — **não** antes, e não meses depois,
   porque uma data que não é cumprida ensina aos clientes que as próximas
   também não serão.

E uma decisão que precisa ficar explícita no anúncio: durante a transição, os
dois formatos leem do mesmo banco. Nada de manter duas colunas.
:::
