---
title: "Git"
number: 42
slug: git
part: p9
kicker: "Um projeto sem histórico não tem volta — e a volta é a única coisa que se quer quando algo dá errado."
goal: >-
  Versionar o projeto com um histórico legível, trabalhar em ramos, proteger
  o repositório de segredos e automatizar a conferência antes do commit.
---

O projeto tem quarenta arquivos, quatro camadas, migrações e testes. Ele
ainda mora numa pasta sem memória: qualquer alteração sobrescreve a anterior,
e "como estava na semana passada" é uma pergunta sem resposta.

## O começo

```text
$ git init
$ git add .
$ git commit -m "primeiro commit: catálogo da Cooperativa Sabiá"
```

Antes do `git add .`, porém, existe um arquivo que precisa existir.

## `.gitignore`, antes de tudo

```text title=".gitignore"
# ambiente
.venv/
__pycache__/
*.py[cod]

# configuração local — NUNCA versionar
.env
*.pem
*.key

# ferramentas
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# editor e sistema
.idea/
.vscode/
.DS_Store
```

:::warning
`.env` no `.gitignore` é a linha mais importante aqui. Um segredo
que entrou no histórico **não sai** apagando o arquivo: ele continua em
todos os commits anteriores, em todos os clones, em todos os forks e na
cópia que a plataforma manteve. A resposta a uma chave vazada não é apagar o
commit — é **trocar a chave**, imediatamente, antes de qualquer outra coisa.
:::

O `.env.example` do capítulo @cap:primeiro-projeto-fastapi entra no
repositório justamente porque não tem valor real: ele documenta quais
variáveis existem sem revelar nenhuma.

## Commits que contam uma história

```text
$ git add app/services/produto.py tests/test_servico_produto.py
$ git commit
```

```text
Recusa venda acima do estoque disponível

A rotina de ajuste em lote subtraía do estoque sem conferir,
e quatro produtos ficaram negativos no fechamento de novembro.

A verificação passa para o serviço, junto com um CHECK no
banco — o serviço dá a mensagem, o banco dá a garantia.

Refs #214
```

A primeira linha é um **resumo no imperativo**, até cinquenta caracteres,
sem ponto final. Ela aparece sozinha em `git log --oneline`, na lista de
commits da plataforma e na busca — e é a única linha que muita gente vai
ler.

O corpo explica **por quê**. O "o quê" está no diff; o "por quê" só existe na
cabeça de quem escreveu, e some em duas semanas.

:::pitfall
`git commit -m "ajustes"` é o commit que não ajuda ninguém. Seis meses
depois, procurando quando um comportamento mudou, você vai encontrar quinze
deles em sequência e vai precisar abrir os quinze. O custo de escrever uma
linha boa é de trinta segundos; o de não escrever é pago por outra pessoa,
com juros.
:::

Um bom tamanho de commit é **uma mudança com um motivo**. Consertar um
defeito e reformatar o arquivo são dois motivos, e dois commits — senão a
correção de três linhas fica escondida numa mudança de trezentas.

## Ramos

```text
$ git switch -c 214-estoque-negativo
$ ...trabalho...
$ git switch main
$ git merge 214-estoque-negativo
$ git branch -d 214-estoque-negativo
```

:::diagram type="flowchart" caption="Um ramo por funcionalidade, revisão antes de entrar."
nodes:
  - { id: m,  type: start,   text: "main" }
  - { id: b,  type: process, text: "ramo da funcionalidade" }
  - { id: c,  type: process, text: "commits" }
  - { id: p,  type: decision, text: "revisado e testes verdes?" }
  - { id: mg, type: process, text: "merge em main" }
edges:
  - { from: m,  to: b }
  - { from: b,  to: c }
  - { from: c,  to: p }
  - { from: p,  to: mg, label: "sim" }
  - { from: p,  to: c,  label: "não" }
:::

A `main` é o que pode ir para produção a qualquer momento. Tudo o mais
acontece em ramo.

## Conflito

```text
<<<<<<< HEAD
    limite = max(1, min(limite, 100))
=======
    limite = min(limite, 200)
>>>>>>> 214-estoque-negativo
```

Entre `<<<<<<<` e `=======` está a versão de quem estava lá; entre `=======`
e `>>>>>>>`, a sua. Resolver é escolher, combinar ou reescrever — e **apagar
as três linhas de marcação**.

:::pitfall
Deixar um `<<<<<<<` no arquivo produz um `SyntaxError` que costuma aparecer
só em produção, porque ninguém rodou aquele módulo depois do merge. Uma
busca por `<<<<<<<` em todo o projeto, antes de confirmar, leva um segundo —
e o gancho de pré-commit da próxima seção faz isso por você.
:::

## Ganchos de pré-commit

```text
$ pip install pre-commit
```

```text title=".pre-commit-config.yaml"
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-merge-conflict
      - id: check-added-large-files
      - id: detect-private-key
      - id: end-of-file-fixer
```

```text
$ pre-commit install
```

A partir daí, todo `git commit` roda essas conferências e recusa o commit se
alguma falhar. O `detect-private-key` e o `check-merge-conflict` sozinhos já
pagam a instalação.

:::key
Formatação automática encerra uma categoria inteira de discussão. Com o
`ruff-format` no gancho, ninguém revisa espaçamento, ninguém debate aspas
simples contra duplas, e nenhum diff vem poluído por reformatação. A
ferramenta decide, e o time discute o que importa.
:::

## Integração contínua

```text title=".github/workflows/ci.yml"
name: CI
on: [push, pull_request]

jobs:
  testes:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: catalogo
          POSTGRES_PASSWORD: senha
          POSTGRES_DB: catalogo_test
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -r requirements.txt
      - run: ruff check app tests
      - run: mypy app
      - run: pytest -q
```

Os testes do capítulo @cap:testando-o-banco rodam a cada envio, num
PostgreSQL de verdade, na máquina de outra pessoa. É o que transforma "passa
na minha máquina" em uma afirmação verificável.

:::story Funciona na minha máquina
A esteira ficou vermelha por três dias seguidos, sempre no mesmo teste, e na
máquina de todo mundo ele passava.

Rafa acabou encontrando: o teste dependia da ordem em que o banco devolvia
os produtos. Localmente, com quatro registros, o PostgreSQL devolvia na
ordem de inserção. Na esteira, com o banco recém-criado e estatísticas
diferentes, ele escolhia outro plano.

— Então o teste estava errado.

— O teste estava **incompleto** — disse Bia. — Faltava o `ORDER BY`. E o
código que ele testava também.

Era a mesma ausência do capítulo da paginação, escondida num lugar onde
ninguém tinha olhado.
:::

## Comandos que salvam

| Comando | Para quê |
|---|---|
| `git log --oneline -20` | os últimos vinte commits |
| `git log -p arquivo.py` | o histórico de um arquivo |
| `git blame arquivo.py` | quem escreveu cada linha, e quando |
| `git diff` | o que mudou e ainda não foi adicionado |
| `git restore arquivo.py` | desfazer alteração não adicionada |
| `git revert <hash>` | desfazer um commit criando outro |

Tabela: `git blame` não serve para achar culpado. Serve para achar o commit
— e, nele, a explicação de por que aquela linha existe.

:::warning
`git push --force` reescreve o histórico do servidor. Em ramo pessoal, é
aceitável. Em ramo compartilhado, apaga o trabalho de quem tinha baixado.
Se precisar mesmo, `--force-with-lease` recusa a operação caso alguém tenha
enviado algo desde a sua última atualização.
:::

:::summary
- `.gitignore` antes do primeiro `git add`; `.env` nunca entra.
- Segredo que entrou no histórico se resolve trocando o segredo.
- Resumo no imperativo, corpo explicando o porquê.
- Um commit é uma mudança com um motivo.
- Ganchos de pré-commit pegam conflito, chave privada e formatação.
- A esteira transforma "funciona na minha máquina" em algo verificável.
- `--force` em ramo compartilhado apaga o trabalho dos outros.
:::

:::exercise level=1
Escreva o `.gitignore` do projeto e faça o primeiro commit, conferindo com
`git status` que o `.env` não entrou.

:::answer
```text
$ git init
$ printf '.venv/\n__pycache__/\n.env\n' > .gitignore
$ git add .
$ git status --short
```
Se `.env` aparecer na lista, ele já estava rastreado — o `.gitignore` só vale
para arquivos ainda não versionados. O conserto é
`git rm --cached .env` antes do commit.
:::

:::exercise level=2
Escreva a mensagem de commit para a correção de um `PATCH` que apagava campos
não enviados.

:::answer
```text
Corrige PATCH que apagava campos não enviados

model_dump() sem exclude_unset devolvia None para todo campo
ausente, e o serviço gravava esses None por cima dos valores
existentes. Um PATCH só com o preço apagava o nome do produto.

Passa a usar exclude_unset=True e acrescenta teste com um
único campo no corpo.

Refs #241
```
A segunda linha em branco entre resumo e corpo não é estética: o Git usa
exatamente essa separação para distinguir os dois.
:::

:::exercise level=3
Você descobre que uma chave de API de um fornecedor foi commitada há três
meses, no repositório privado da empresa, e já passou por dois forks
internos. Descreva o que fazer, em ordem.

:::answer
**1. Revogar a chave.** Agora, antes de qualquer coisa relacionada ao Git.
Enquanto a chave for válida, tudo o mais é secundário — e limpar o histórico
sem revogar é gastar horas numa tarefa que não resolve o problema.

**2. Emitir uma chave nova** e colocá-la onde ela deveria estar desde o
início: variável de ambiente, ou um cofre de segredos.

**3. Verificar o uso.** O fornecedor tem log de chamadas: veja se houve uso
fora dos seus endereços e horários habituais. Essa é a diferença entre "chave
exposta" e "chave usada", e ela muda o que precisa ser comunicado.

**4. Comunicar.** Segurança da empresa e o fornecedor. Um repositório
privado com dois forks internos não é um incidente público, e continua sendo
um incidente.

**5. Só então, o histórico.** `git filter-repo` ou o BFG reescrevem os
commits antigos, e isso exige que **todo mundo** apague os clones e baixe de
novo — inclusive os forks. É trabalhoso, quebra todas as referências de
commit e, com a chave já revogada, o benefício é modesto: evitar que o valor
antigo apareça numa auditoria futura. Em repositório privado com poucos
clones, muita gente decide, com razão, não reescrever.

**6. Impedir a repetição.** `detect-secrets` ou `gitleaks` no gancho de
pré-commit e na esteira. Esse passo é o único que muda alguma coisa para o
próximo trimestre — os cinco anteriores tratam deste incidente; só o sexto
trata do próximo.
:::
