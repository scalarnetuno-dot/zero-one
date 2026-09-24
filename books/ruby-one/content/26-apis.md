---
title: "APIs"
number: 26
slug: apis
part: p6
kicker: "A API devolvia status active. O sistema da Serra Azul comparava com ativo. Nenhum contrato da Nortea aparecia no painel deles."
goal: >-
  Escrever o contrato da API numa tabela curta antes do código, responder
  JSON com os nomes e os valores combinados, recusar com 422 o pedido que
  não faz sentido, e manter a API separada das telas.
---

:::story Ativo
Na segunda, 18 de maio, o Rômulo encaminhou o e-mail da TI da Serra Azul.
Eles tinham começado a consumir a API de homologação na sexta:

> A integração está funcionando, mas nenhum contrato aparece como vigente
> no nosso painel. Vocês podem verificar?

A Lívia chamou o endereço:

```text
$ curl -s https://homolog.nortea.com.br/api/contracts/3196
{"id":3196,"code":"CT-3196","status":"active","site":"nova_lima",
 "start_date":"2026-05-04","end_date":"2026-06-30", ...}
```

O Caio mandou uma pergunta para a TI da Serra Azul. A resposta veio em
dez minutos, com um trecho de código deles:

```text
if (contrato.status == "ativo") { ... }
```

— Eles escreveram em português — disse a Lívia.

— Ninguém disse a eles que era em inglês — disse o Renato. — Nem que
viriam as vinte e três colunas.

— O endpoint devolve o `to_json` do model?

— Devolve tudo. Inclusive `notes`. Que é onde a Helena escreve o que acha
do cliente.
:::

## API

Uma API, aqui, é uma parte do `nortea` que responde a **outro programa**,
não a uma pessoa. O pedido chega igual — verbo e caminho, o capítulo
@cap:rotas —, e a resposta, em vez de HTML para o navegador, é JSON: um
formato de texto que qualquer linguagem lê.

```json
{"code": "CT-3196", "status": "ativo", "fim": "2026-06-30"}
```

JSON tem objetos (entre chaves, com chaves de texto), listas (entre
colchetes), texto, número, `true`, `false` e `null`. É o hash e o array do
capítulo @cap:arrays-e-hashes, escritos para viajar.

A diferença que importa não é o formato. É quem lê. A Helena lê a tela e
pergunta quando não entende. O sistema da Serra Azul compara texto com
texto e não pergunta nada.

## O contrato antes do código

O endpoint de 2025, feito às pressas para uma demonstração, era isto:

```ruby
def show
  render json: Contract.find(params[:id])
end
```

`render json:` com um model chama o `to_json` dele: todas as colunas, com
os nomes do banco. A API passou a ser a tabela, e toda migration do
capítulo @cap:migrations passou a ser uma mudança na integração da Serra
Azul, sem ninguém saber.

A primeira coisa que a Lívia fez não foi código. Foi uma tabela, que a
Marta leu, o Rômulo aprovou e a TI da Serra Azul recebeu por e-mail:

| Campo | Tipo | Valores | Significado |
|---|---|---|---|
| `codigo` | texto | `CT-` e quatro dígitos | o número do contrato |
| `patrimonio` | texto | `PT-118` | a máquina |
| `canteiro` | texto | `contagem`, `betim`, ... | onde ela deve estar |
| `status` | texto | `ativo`, `reservado`, `cancelado`, `encerrado` | a situação |
| `chegada` | data e hora ou `null` | ISO 8601 | quando a máquina saiu do pátio |
| `fim` | data | `AAAA-MM-DD` | devolução prevista |

Tabela: Seis campos. Nenhum é o nome de uma coluna. Todos são o que a
Serra Azul confere.

`chegada` é a `started_at` do capítulo @cap:modelos — a coluna que a
Helena reconheceria. `notes`, `daily_rate_cents` e `created_by` não estão
na tabela, e por isso não estão na API.

:::key
A resposta de uma API é uma **lista de permissão**, campo a campo. O que
não está na tabela combinada não sai — inclusive a coluna que alguém criar
no mês que vem. `render json: model` é a lista de proibição vazia.
:::

## A resposta com nome

A tabela vira um método que monta o hash, com os nomes combinados:

```ruby title="app/models/contract.rb" numbered
API_STATUS = {
  "active" => "ativo",
  "reserved" => "reservado",
  "cancelled" => "cancelado",
  "closed" => "encerrado",
}.freeze

def as_api
  {
    codigo: code,
    patrimonio: equipment.patrimony,
    canteiro: site,
    status: API_STATUS.fetch(status),
    chegada: started_at&.iso8601,
    fim: end_date.iso8601,
  }
end
```

`API_STATUS.fetch(status)` traduz o status da tabela para o combinado. É
o `fetch` do capítulo @cap:arrays-e-hashes: um status novo no banco que
não estiver na tradução levanta `KeyError`, em vez de sair `null` para a
Serra Azul comparar com nada. `.freeze` congela o hash: ninguém o altera
em tempo de execução.

`started_at&.iso8601` usa o `&.`: se `started_at` for `nil`, o resultado é
`nil` — que vira `null` no JSON —, em vez de `NoMethodError`. `iso8601`
formata data no padrão internacional, que todo sistema lê igual.

## O controller da API

A API tem o próprio controller, num módulo que serve de sobrenome — o
capítulo @cap:modulos —, com a versão no nome:

```ruby title="config/routes.rb" numbered
namespace :api do
  namespace :v1 do
    resources :contracts, only: [:index, :show]
  end
end
```

```ruby title="app/controllers/api/v1/contracts_controller.rb" numbered
module Api
  module V1
    class ContractsController < ActionController::API
      def show
        contract = Contract.includes(:equipment)
                           .find_by!(code: params[:id])
        render json: contract.as_api
      end
    end
  end
end
```

```text
$ curl -s https://homolog.nortea.com.br/api/v1/contracts/CT-3196
{"codigo":"CT-3196","patrimonio":"CP-007","canteiro":"nova_lima",
 "status":"ativo","chegada":"2026-05-04T06:40:00-03:00",
 "fim":"2026-06-30"}
```

`ActionController::API` é uma versão menor do controller: sem cookies,
sem sessão, sem views. A API não precisa deles.

`/api/v1/` põe a versão no caminho. Quando a tabela mudar de um jeito que
quebra quem já usa, nasce a `v2` ao lado, e a Serra Azul migra quando
puder. O `/api/contracts` antigo fica respondendo até ela confirmar que
não o chama mais.

O endereço usa o **código**, não o `id`: a Serra Azul conhece `CT-3196`,
e o `id` é um detalhe do banco da Nortea.

## A lista, e o `422`

A Serra Azul também quer a lista dos contratos dela, filtrada por status:

```text
GET /api/v1/contracts?status=ativo
```

O filtro vem do outro sistema, na língua da tabela combinada. Pode vir
errado:

```ruby title="app/controllers/api/v1/contracts_controller.rb" numbered
def index
  status = Contract::API_STATUS.key(params.fetch(:status, "ativo"))

  if status.nil?
    return render json: {
      erro: "status inválido",
      aceitos: Contract::API_STATUS.values,
    }, status: :unprocessable_entity
  end

  contracts = Contract.includes(:equipment).where(status: status)
  render json: contracts.map(&:as_api)
end
```

`API_STATUS.key("ativo")` procura a chave cujo valor é `"ativo"` e
devolve `"active"`. Para um valor desconhecido, devolve `nil`.

```text
$ curl -s -w "\n%{http_code}\n" \
    ".../api/v1/contracts?status=active"
{"erro":"status inválido",
 "aceitos":["ativo","reservado","cancelado","encerrado"]}
422
```

`422` é o código do capítulo @cap:controllers: o pedido chegou, e o que
veio nele não faz sentido. O corpo diz o que falhou e o que é aceito. O
programa do outro lado lê o código; a pessoa que for depurar lê o corpo.

A alternativa — devolver a lista vazia para um status desconhecido — é o
`rescue` que devolve `[]` do capítulo @cap:excecoes, de novo: um "nenhum
contrato" plausível, e a Serra Azul achando que não tem nada alugado.

:::pitfall
Falta uma coisa importante nesta lista: ela devolve os contratos de
**todos** os clientes. Qualquer um com o endereço lê os contratos da
concorrente da Serra Azul. A API ainda não sabe quem está perguntando.
Esse é o capítulo seguinte, e a rota não vai para produção antes dele.
:::

:::summary
- API responde a outro programa, em JSON. O outro programa não pergunta.
- A tabela do contrato vem antes do código: campo, tipo, valores,
  significado. Nenhum nome de coluna.
- A resposta é uma lista de permissão: `as_api` monta o hash;
  `render json: model` vaza tudo.
- `ActionController::API`, `namespace :api` e `v1` separam a API das telas.
- Parâmetro inválido é `422`, com o que é aceito no corpo. Lista vazia para
  pedido errado é mentira plausível.
:::

:::exercise level=1
Diga o que a Serra Azul recebe em cada caso:

1. `GET /api/v1/contracts/CT-3196`, contrato ativo sem saída do pátio.
2. `GET /api/v1/contracts/CT-9999`, que não existe.
3. `GET /api/v1/contracts?status=encerrado`.

:::answer
1. O JSON com `"status":"ativo"` e `"chegada":null`.
2. `404`. O `find_by!` levanta `RecordNotFound`, e o Rails responde
   não encontrado.
3. `200` com a lista dos contratos `closed`, cada um no formato da tabela.

No 2, o corpo de erro padrão do Rails não segue o formato combinado. Vale
acrescentar à tabela como são os erros — e fazer o `404` responder
`{"erro": "contrato não encontrado"}`.
:::

:::exercise level=2
A Serra Azul pede um campo novo: o nome do responsável no canteiro. Diga
o que muda, na ordem, e se precisa de `v2`.

:::answer
Primeiro, a tabela: uma linha nova, `responsavel`, texto, com o
significado. A Marta confere se a Serra Azul pode ver esse nome — é gente
deles, então pode.

Depois, `as_api` ganha `responsavel: responsible`.

Não precisa de `v2`. Acrescentar um campo não quebra quem já usa: um
programa que não conhece `responsavel` o ignora. `v2` é para mudança que
quebra — renomear `fim`, trocar `status` de texto para número, remover um
campo.
:::

:::exercise level=3
O Sérgio propõe resolver o "ativo" de outro jeito: trocar os valores da
coluna `status` no banco para português, com uma migration, "e a API sai
certa sem tradução". Liste o que isso quebra e responda por que a
tradução na borda é melhor.

:::answer
Quebra: todos os escopos e comparações em inglês — `where(status:
"active")`, o `occupying?`, o `case` dos rótulos, o callback
`became_active?` —, o relatório de ocupação, a view, o `exportar_patio.rb`,
os testes e a factory. E qualquer leitor do banco fora do repositório.
É o `:active` e o `"active"` do capítulo @cap:strings-e-simbolos,
espalhado pelo sistema inteiro.

A tradução na borda é melhor porque a API é um contrato com **um**
cliente, escrito numa tabela. O banco é o contrato do sistema consigo
mesmo. Mudar um para agradar o outro amarra os dois: da próxima vez que
um terceiro cliente pedir `"active"`, não há como atender. Com a
tradução num lugar só, cada lado fala a sua língua.
:::
