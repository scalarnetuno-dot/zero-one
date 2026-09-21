---
title: "O que vamos construir"
number: 1
slug: o-que-vamos-construir
part: p1
kicker: "Antes da primeira linha, o destino — porque quem não sabe onde a viagem termina aceita qualquer atalho."
epigraph: "Eu queria uma linguagem em que a coisa óbvia de escrever fosse também a coisa certa de escrever."
epigraph_by: "Guido van Rossum, criador do Python"
goal: >-
  Saber o que é uma API REST, o que é um CRUD e qual a diferença entre
  Python, FastAPI e Uvicorn — e ter o ambiente instalado, isolado e testado.
---

No fim deste livro existe um programa rodando. Ele não tem tela, não tem
botão e não tem cor. Fica parado em uma porta do seu computador esperando
que alguém pergunte alguma coisa, e quando a pergunta chega ele responde
com texto — texto num formato que outro programa entende.

Isso é uma API. E é o tipo de programa que sustenta quase tudo que você usa
no celular: o aplicativo é a vitrine, a API é a loja.

## O projeto: o catálogo da Cooperativa Sabiá

A Cooperativa Sabiá reúne duzentos produtores de hortifrúti no interior.
Ela tem um catálogo — quais produtos existem, de que produtor vêm, quanto
custam, quanto há em estoque — e esse catálogo mora hoje em uma planilha
compartilhada com trinta e uma abas.

O programa que vamos construir substitui a planilha. Ele vai saber fazer
quatro coisas com um produto:

| Operação | O que faz | Nome técnico |
|---|---|---|
| Criar | cadastra um produto novo | `Create` |
| Ler | lista todos ou busca um | `Read` |
| Atualizar | muda preço, estoque, nome | `Update` |
| Apagar | tira do catálogo | `Delete` |

Tabela: As quatro operações que aparecem em praticamente todo sistema de
informação já construído.

As iniciais formam **CRUD**, e essa palavra vai aparecer tantas vezes neste
livro que convém se acostumar com ela agora. Um CRUD é a coisa mais comum
que um programador faz. Fazer um CRUD é fácil. Fazer um CRUD que não
estraga o dado de ninguém é o assunto de uns vinte capítulos daqui.

:::story A planilha com trinta e uma abas
— Ela funciona — disse Dona Neuza, de braços cruzados.

Bia não discordou. A planilha funcionava mesmo. Desde 2019.

— Funciona até duas pessoas abrirem ao mesmo tempo — disse Elias, sem tirar
os olhos da tela. — Aí uma das duas perde o trabalho da manhã e ninguém
descobre qual.

— Isso acontece uma vez por mês.

— Isso acontece uma vez por mês **que a gente percebe**.

Dona Neuza descruzou os braços. Trinta e um anos de armazém, e ela entendeu
na hora o que aquela frase significava: alguém já tinha perdido dado sem
jamais ter sabido.

— E o que vocês querem no lugar?

— Um programa — disse Bia. — Que guarde tudo num lugar só e responda a quem
perguntar.

— Isso demora quanto?

— Depende do que a senhora chamar de "tudo" — disse Elias.

Dona Neuza riu pela primeira vez na reunião.
:::

:::art caption="Toda planilha compartilhada é um banco de dados sem as regras que fazem um banco de dados funcionar."
Charge editorial minimalista em fundo branco: uma planilha gigante projetada
na parede de uma sala de reunião, com dezenas de abas coloridas na parte de
baixo e células de cores conflitantes. Três pessoas olham para ela: uma
coordenadora de armazém mais velha, de braços cruzados, com a expressão de
quem defende o próprio território; uma analista jovem com um caderno na mão;
e um desenvolvedor sentado de lado, olhando para o próprio notebook em vez
da parede. Poucos elementos, humor seco, estética de revista de tecnologia.
:::

## O que é uma API REST

Uma **API** é um contrato entre dois programas: um sabe fazer alguma coisa,
o outro precisa que ela seja feita, e existe um jeito combinado de pedir.
Nada mais.

O **REST** é um estilo de combinar. Ele diz que cada coisa que o sistema
conhece — um produto, um produtor, um pedido — é um **recurso** com um
endereço, e que o verbo da requisição diz o que fazer com ele.

:::anatomy title="Uma requisição HTTP, por partes"
lang: http
code: |
  POST /produtos HTTP/1.1
  Content-Type: application/json

  {"nome": "Tomate italiano", "preco": 8.90}
notes:
  - { line: 1, text: "**Verbo**: a intenção. `POST` cria, `GET` lê, `PUT` substitui, `DELETE` apaga." }
  - { line: 1, text: "**Caminho**: o recurso. Substantivo no plural, sem verbo dentro." }
  - { line: 2, text: "**Cabeçalho**: metadado — formato, autenticação, idioma." }
  - { line: 4, text: "**Corpo**: os dados. Só existe em `POST`, `PUT` e `PATCH`." }
:::

Repare no caminho: `/produtos`, e não `/criarProduto`. O verbo já está do
lado de fora. Um dos erros mais comuns de API iniciante é colocar o verbo no
endereço e acabar com `/criarProduto`, `/atualizarProduto` e
`/apagarProduto` — três endereços para um recurso só, e nenhum deles
combinável com nada.

Toda resposta traz um número de três dígitos que resume o destino da
requisição:

| Faixa | Significado | Os que você vai usar |
|---|---|---|
| `2xx` | deu certo | `200`, `201`, `204` |
| `4xx` | quem pediu errou | `400`, `401`, `403`, `404`, `422` |
| `5xx` | quem respondeu errou | `500` — e o objetivo é nunca |

Tabela: O código de status é a primeira coisa que outro programa lê. Errar
nele é mentir para quem confia em você.

:::diagram type="blocks" caption="O caminho de uma requisição: cada camada resolve um problema e passa adiante."
rows:
  - [{ text: "Cliente", note: "navegador, app, curl" }]
  - [{ text: "Rota FastAPI", note: "traduz HTTP em chamada de função" }]
  - [{ text: "Service", note: "as regras da cooperativa" }]
  - [{ text: "Repository", note: "conversa com o banco" }]
  - [{ text: "PostgreSQL", note: "onde o dado fica quando ninguém olha" }]
:::

Esse desenho é o sistema que a Cooperativa precisa: cada faixa resolve uma
pergunta diferente. A rota não deve conhecer a consulta ao banco; o banco
não deve decidir uma regra de negócio; e a documentação precisa continuar
verdadeira quando o código mudar.

## Python, FastAPI, Uvicorn: quem é quem

Três nomes aparecem juntos o tempo todo e são coisas diferentes.

**Python** é a linguagem. É o que você escreve. Ela sozinha não sabe o que é
HTTP.

**FastAPI** é uma biblioteca que ensina Python a atender requisições. Ela lê
as anotações de tipo que você escreve nas funções e, a partir delas, valida
a entrada, converte o JSON e gera a documentação sozinha. Esse é o truque
central do framework: tipos escritos para o programa também descrevem o
contrato para quem o consome.

**Uvicorn** é o servidor. É quem de fato abre a porta do computador, escuta
a rede e entrega a requisição pronta para o FastAPI. Sem ele, o FastAPI é um
livro de regras que ninguém leu.

:::key
Python é a linguagem. FastAPI é o framework. Uvicorn é o servidor. Quando
alguma coisa não sobe, a primeira pergunta útil é *qual dos três reclamou* —
e a resposta está na primeira linha do erro.
:::

## Instalando

Baixe o Python em <https://python.org>. No Windows, marque **Add python.exe
to PATH** na primeira tela. No macOS e no Linux quase sempre já existe um
Python instalado, mas ele pode ser velho — confira antes de confiar.

Abra o terminal e digite:

```text
$ python --version
Python 3.12.4
```

Se aparecer `3.12` ou mais alto, está pronto. Se o comando não for
encontrado, tente `python3` em vez de `python`; em macOS e Linux é o nome
usual.

:::pitfall
`python` e `python3` podem ser programas diferentes na mesma máquina, com
versões diferentes e pacotes diferentes. Descubra qual é o seu agora e use
sempre o mesmo. Metade dos "mas eu instalei essa biblioteca" da vida real é
esta confusão.
:::

## O ambiente virtual, antes de qualquer biblioteca

Aqui vem a primeira decisão que separa um script de um projeto.

Quando você instala uma biblioteca com `pip install`, por padrão ela vai
para o Python do sistema inteiro. Dois projetos na mesma máquina passam a
dividir as mesmas versões — e no dia em que um precisa da versão nova e o
outro só funciona com a antiga, um dos dois quebra.

A solução é um **ambiente virtual**: uma cópia isolada do Python, dentro da
pasta do projeto, com as bibliotecas só dele.

```text
$ mkdir catalogo && cd catalogo
$ python -m venv .venv
```

Isso cria uma pasta `.venv`. Agora **ative**:

| Sistema | Comando |
|---|---|
| Linux / macOS | `source .venv/bin/activate` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (cmd) | `.venv\Scripts\activate.bat` |

Tabela: Ativar é o passo que todo mundo esquece — e o esquecimento sempre se
manifesta como "módulo não encontrado".

O terminal passa a mostrar `(.venv)` no começo da linha. Esse prefixo é a
sua confirmação visual de que o `pip` vai instalar no lugar certo.

:::warning O PowerShell recusando o script
No Windows, o PowerShell pode responder que a execução de scripts está
desabilitada. O conserto, uma vez por máquina:

```text
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
:::

:::practice
Com o ambiente ativo, rode `pip list`. A lista deve ter dois ou três itens,
não trinta. Se vier longa, você não ativou o ambiente — feche o terminal e
comece de novo. Vale a pena ver essa lista curta uma vez, para reconhecer
depois quando ela estiver errada.
:::

## O teste que prova que está tudo de pé

Instale o FastAPI e o servidor:

```text
$ pip install "fastapi[standard]"
```

Crie um arquivo `main.py` com oito linhas:

```python title="main.py" numbered
from fastapi import FastAPI

app = FastAPI()


@app.get("/saude")
def saude():
    return {"status": "de pé"}
```

E suba:

```text
$ fastapi dev main.py
INFO  Uvicorn running on http://127.0.0.1:8000
```

Abra <http://127.0.0.1:8000/saude> no navegador. Se aparecer
`{"status":"de pé"}`, o ambiente está completo: linguagem, framework e
servidor funcionando juntos.

Agora abra <http://127.0.0.1:8000/docs>.

:::key
Essa página de documentação que apareceu sozinha, sem você escrever uma
linha para ela, é o melhor argumento de venda do FastAPI. Ela foi gerada a
partir do código — e vai continuar correta enquanto o código mudar, porque
não existe uma segunda fonte para desatualizar.
:::

Você ainda não precisa entender todas as oito linhas do `main.py`. O `@` na
frente de `app.get` é um decorador: uma função que recebe outra função e a
registra na tabela de rotas. Por enquanto, guarde o resultado concreto: oito
linhas já colocam uma API no ar.

:::summary
- O projeto do livro é uma API REST de catálogo, com CRUD completo.
- REST trata cada coisa como um recurso com endereço; o verbo diz o que
  fazer com ele.
- O código de status é a primeira coisa que outro programa lê.
- Python é a linguagem, FastAPI é o framework, Uvicorn é o servidor.
- Todo projeto Python começa com um ambiente virtual — antes da primeira
  biblioteca, não depois.
:::

:::milestone
Você tem Python instalado, um ambiente isolado e uma rota respondendo. É
pouco código e já é o esqueleto inteiro: a partir daqui, só cresce.
:::

:::exercise level=1
Mude a rota `/saude` para devolver também a versão da API, num campo
`versao` com o valor `"0.1.0"`. Recarregue a página e confira.

:::answer
```python
@app.get("/saude")
def saude():
    return {"status": "de pé", "versao": "0.1.0"}
```
O servidor em modo `dev` recarrega sozinho ao salvar o arquivo. Se a
resposta não mudar, confira se você salvou — é sempre isso.
:::

:::exercise level=2
Sem olhar a tabela, escreva o verbo e o caminho de cada operação do CRUD de
produtos. Depois compare com o que o livro vai usar do capítulo
@cap:primeira-api em diante.

:::answer
```text
POST   /produtos       cria
GET    /produtos       lista
GET    /produtos/1     busca um
PUT    /produtos/1     substitui
DELETE /produtos/1     apaga
```
Os dois `GET` diferentes são o ponto: o mesmo verbo, no plural e no
singular, significa coisas diferentes. Isso não é acaso do REST, é a ideia
inteira dele.
:::

:::exercise level=3
A Cooperativa pediu um endereço `/produtos/baratos`, que devolva os produtos
com preço abaixo de dez reais. Você aceitaria esse endereço? Justifique em
três linhas.

:::answer
Não, porque `baratos` não é um recurso — é um filtro sobre o recurso
`produtos`. Na hora em que aparecerem `/produtos/caros`,
`/produtos/em-falta` e `/produtos/organicos`, serão quatro endereços que não
se combinam: não há como pedir "baratos **e** orgânicos".

A forma que combina é `GET /produtos?preco_max=10`: o caminho identifica *o
que*, a query descreve *quais*.
:::
