---
title: "Validações"
number: 18
slug: validacoes
part: p4
kicker: "O formulário gravava contrato sem responsável. O motorista chegava ao canteiro sem ninguém para assinar a entrega, e a máquina voltava no mesmo caminhão."
goal: >-
  Recusar no model o contrato que o pátio não aceitaria: presença,
  período coerente, sem duas reservas da mesma máquina ao mesmo tempo; ler
  os erros que a validação produz; e saber quais caminhos passam por cima
  dela.
---

:::story Ninguém para assinar
Na segunda, 13 de abril, o motorista do compactador CP-007 ligou da
portaria do canteiro de Nova Lima.

— Não tem ninguém da Serra Azul aqui com o nome da ordem. A ordem está sem
nome.

A Helena mandou voltar. Duas horas de caminhão, ida e volta, e um dia de
diária que a Serra Azul não ia pagar.

O Diego abriu o contrato no sistema. O campo `responsible` estava vazio.

— O formulário deixa gravar sem — disse ele. — Eu testei agora. Salva.

— O banco não recusa? — perguntou a Lívia.

— A coluna aceita nulo — disse o Caio. — E ninguém disse ao model que não
pode.
:::

## `validates`

Uma validação é uma regra que o model confere **antes de gravar**. Se a
regra falhar, ele não grava.

```ruby title="app/models/contract.rb" numbered
class Contract < ApplicationRecord
  belongs_to :customer
  belongs_to :equipment

  validates :responsible, presence: true
  validates :start_date, :end_date, presence: true
end
```

`validates :responsible, presence: true` diz que `responsible` precisa
estar presente: não `nil`, não texto vazio, não só espaços. Uma linha pode
validar vários campos com a mesma regra.

`belongs_to` já valida sozinho, desde o Rails 5: o contrato sem
`equipment` ou sem `customer` não grava. Não precisa de linha a mais.

## `valid?`, `errors`, e o `save` que devolve falso

```text
nortea(dev)> c = Contract.new(code: "CT-2071", responsible: "")
nortea(dev)> c.valid?
=> false
nortea(dev)> c.errors.full_messages
=> ["Customer must exist", "Equipment must exist",
    "Responsible can't be blank", "Start date can't be blank",
    "End date can't be blank"]
```

`valid?` roda todas as validações e responde. `errors` guarda o que
falhou, por campo. `full_messages` junta o nome do campo com a mensagem.

E o `save`:

```text
nortea(dev)> c.save
=> false
```

`save` devolve `false` e não grava. Não levanta exceção. Quem chamou
precisa olhar o retorno. Existe o irmão com `!`:

```text
nortea(dev)> c.save!
ActiveRecord::RecordInvalid: Validation failed: Customer must
exist, Equipment must exist, Responsible can't be blank, ...
```

`save!` levanta `ActiveRecord::RecordInvalid`. O mesmo par existe para
criar — `create` devolve o objeto não gravado, `create!` levanta.

| Método | Se a validação falha |
|---|---|
| `save`, `create`, `update` | devolve `false` (ou o objeto não gravado) |
| `save!`, `create!`, `update!` | levanta `ActiveRecord::RecordInvalid` |

Tabela: O formulário usa o primeiro par e mostra os erros. O script e o
teste usam o segundo, e deixam a falha subir — a régua do capítulo
@cap:excecoes.

:::pitfall
`c.save` numa linha solta, sem olhar o retorno, é o jeito mais comum de um
contrato não ser gravado e ninguém saber. O script de importação de 2019
tinha dezenas assim. Fora de um formulário, use `save!`.
:::

## Em português

As mensagens estão em inglês porque o Rails vem em inglês. A tela da
Helena é em português. O `nortea` tem o arquivo de tradução:

```yaml title="config/locales/pt-BR.yml"
pt-BR:
  activerecord:
    models:
      contract: Contrato
    attributes:
      contract:
        responsible: Responsável no canteiro
        start_date: Início da cobrança
        end_date: Devolução prevista
        equipment: Equipamento
  errors:
    messages:
      blank: não pode ficar em branco
      required: é obrigatório
```

Com o idioma padrão em `pt-BR`, as mesmas validações dizem:

```text
=> ["Equipamento é obrigatório",
    "Responsável no canteiro não pode ficar em branco", ...]
```

O nome da coluna em inglês nunca chega à Helena. É o lugar onde a clareza
do capítulo @cap:o-que-e-o-rails mora: o código fala inglês, a tela fala
a língua de quem a usa.

## O período

Presença não basta. Um contrato que termina antes de começar passa em
todas as validações de presença. A regra do período é da Nortea, e o
Rails não a tem pronta. Um método resolve:

```ruby title="app/models/contract.rb" numbered
class Contract < ApplicationRecord
  validates :responsible, :start_date, :end_date, presence: true
  validate :fim_depois_do_inicio

  private

  def fim_depois_do_inicio
    return if start_date.blank? || end_date.blank?

    if end_date < start_date
      errors.add(:end_date,
                 "não pode ser antes do início da cobrança")
    end
  end
end
```

`validate` no singular recebe o nome de um método. O método roda junto com
as outras validações, e reprova o registro acrescentando um erro com
`errors.add`: o campo e a mensagem.

O `return if ... blank?` no começo evita repetir o que a presença já diz:
se uma das datas faltou, o erro de presença já está lá, e comparar `nil`
com data levantaria `NoMethodError`. `blank?` é do Rails: verdadeiro para
`nil`, texto vazio, texto só com espaço.

`private` separa os métodos que só a própria classe chama. O
`fim_depois_do_inicio` não é para ser chamado de fora; o Rails o chama por
dentro.

## A mesma máquina, duas vezes

O capítulo @cap:associacoes deixou uma pergunta: duas reservas da mesma
plataforma no mesmo período. É o caso da PT-118 em Contagem e Betim, no
capítulo @cap:o-que-vamos-construir.

Dois períodos se sobrepõem quando cada um começa antes de o outro
terminar:

```ruby title="app/models/contract.rb" numbered
validate :equipamento_livre_no_periodo

def equipamento_livre_no_periodo
  return if equipment_id.blank? || start_date.blank? ||
            end_date.blank?

  conflito = Contract
    .where(equipment_id: equipment_id)
    .where(status: %w[active reserved])
    .where.not(id: id)
    .where("start_date <= ? AND end_date >= ?", end_date, start_date)
    .first

  return unless conflito

  errors.add(:equipment,
             "já está no contrato #{conflito.code} nesse período")
end
```

`%w[active reserved]` é um atalho para `["active", "reserved"]`: uma lista
de palavras sem aspas. `where.not(id: id)` tira o próprio contrato da
busca — sem ele, editar um contrato daria conflito com ele mesmo.

```text
nortea(dev)> c = Contract.new(equipment: pt118, customer: serra,
               responsible: "Rogério", site: "betim",
               start_date: "2026-04-20", end_date: "2026-05-10")
nortea(dev)> c.valid?
=> false
nortea(dev)> c.errors[:equipment]
=> ["já está no contrato CT-2041 nesse período"]
```

A mensagem diz o código do contrato que segura a máquina. A Helena sabe
para quem ligar.

:::key
Validação protege o formulário, o console e o script — todo caminho que
passa por `save`. Ela não protege dois pedidos que chegam no mesmo
segundo: os dois conferem, os dois veem a máquina livre, os dois gravam.
Para isso a regra precisa estar também no banco. Para a Nortea, com três
pessoas cadastrando contrato, o segundo exato é raro. Não é impossível, e
está anotado.
:::

## Os caminhos que passam por cima

Alguns métodos gravam **sem validar**:

```ruby
c.update_column(:responsible, nil)
Contract.where(site: "betim").update_all(responsible: nil)
c.save(validate: false)
```

`update_column` e `update_all` escrevem direto no banco. `save(validate:
false)` pula as validações de propósito. Os três existem para migração de
dados e correção em massa, e cada um é uma forma de gravar um contrato que
o formulário recusaria.

A coluna `responsible` continua aceitando nulo no banco. Os contratos
antigos sem responsável — são 94 — ainda não têm um nome para pôr ali. A
validação vale para contrato novo e para quem editar um antigo: ao salvar,
vai ter de preencher. A regra no banco, `null: false`, vem depois que os
94 forem preenchidos, na ordem que o capítulo @cap:migrations ensinou.

:::summary
- `validates :campo, presence: true` recusa vazio antes de gravar.
  `belongs_to` já valida a presença do associado.
- `valid?` roda as regras; `errors` diz o que falhou. `save` devolve
  `false`; `save!` levanta `RecordInvalid`.
- As mensagens e os nomes de campo se traduzem em `config/locales`.
- `validate :metodo` roda uma regra da casa; `errors.add` reprova.
- `update_column`, `update_all` e `save(validate: false)` passam por cima.
  Validação não substitui regra no banco para pedidos simultâneos.
:::

:::exercise level=1
Diga o que cada linha devolve, para um contrato novo sem responsável:

```ruby
c.valid?
c.save
c.persisted?
c.errors[:responsible]
```

:::answer
`false`, `false`, `false` e `["não pode ficar em branco"]`.

`persisted?` pergunta se o registro está no banco. Não está: o `save`
recusou. A mensagem sai em português por causa do arquivo de tradução.
:::

:::exercise level=2
A Marta pede que o código do contrato seja único e siga o formato `CT-`
seguido de quatro dígitos. Escreva as validações.

:::answer
```ruby
validates :code, presence: true,
                 uniqueness: true,
                 format: { with: /\ACT-\d{4}\z/,
                           message: "deve ser CT- e quatro dígitos" }
```

`\A` e `\z` marcam o começo e o fim do texto. Sem eles, `"XCT-2041Y"`
passaria, porque o padrão apareceria no meio.

`uniqueness` confere no banco se outro contrato já tem o código. Ela sofre
do mesmo problema da sobreposição: dois pedidos no mesmo segundo passam.
Para o código, a proteção completa é um índice único no banco, que uma
migration cria.
:::

:::exercise level=3
O Diego traz a combinação: editar um contrato da PT-118 **cancelado** em
março, com período de abril a junho, só para corrigir o nome do
responsável. O `save` falha com "Equipamento já está no contrato CT-2041
nesse período". O cancelado não ocupa nada. Onde
está o defeito e qual é a correção?

:::answer
A validação de sobreposição roda para todo contrato, inclusive o que está
sendo salvo cancelado. Ela busca conflitos entre os outros contratos
ativos e reservados, acha o CT-2041 no mesmo período, e reprova. Mas um
contrato cancelado não disputa a máquina com ninguém: ele não deveria
estar sendo conferido.

A correção é dizer quando a regra vale:

```ruby
validate :equipamento_livre_no_periodo,
         if: -> { status.in?(%w[active reserved]) }
```

`if:` recebe uma condição; a validação só roda quando ela é verdadeira.
`in?` é do Rails: pergunta se o valor está na lista.

O defeito tem a forma do capítulo @cap:associacoes: a regra olhou para os
outros contratos filtrando o cancelamento, e esqueceu de filtrar o
próprio.
:::
