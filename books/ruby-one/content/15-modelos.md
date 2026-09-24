---
title: "Modelos"
number: 15
slug: modelos
part: p4
kicker: "Vinte e três colunas, três começos, e cada relatório da Nortea lendo um deles."
goal: >-
  Ler um model do Rails sabendo o que ele herda, entender por que ele não
  declara as colunas, consultar e ler registros no console, e descobrir o
  que cada uma das três colunas de começo quer dizer antes de mexer nelas.
---

:::story Três começos
Na quarta, 1º de abril, o Ruby 3.3 do servidor saiu da manutenção normal.
O Caio anotou no quadro da sala e ninguém comentou. A Lívia estava com o
`contract.rb` aberto:

```ruby title="app/models/contract.rb"
class Contract < ApplicationRecord
  belongs_to :customer
  belongs_to :equipment
  has_many :reservations

  def active?
    status == "active" && end_date >= Date.today
  end
end
```

Nove linhas. E, no `db/schema.rb`, a tabela `contracts` com vinte e três
colunas. Três delas diziam começo:

```ruby
t.date "start_date"
t.date "begin_date"
t.datetime "started_at"
```

— Qual é a data em que o contrato começa? — perguntou ela.

O Sérgio respondeu sem pensar:

— `start_date`.

A Marta, da mesa ao lado:

— A vigência é a `begin_date`. A Paula fez para o relatório do jurídico.

O Caio não respondeu. Abriu o console, digitou três linhas e virou a tela
para as duas.
:::

## `class Contract < ApplicationRecord`

O `<` é a herança que o capítulo @cap:excecoes usou para
`EquipamentoOcupado < StandardError`. `Contract` é um tipo de
`ApplicationRecord`, que por sua vez é um tipo de `ActiveRecord::Base`: a
classe do Rails que fala com o banco.

```ruby title="app/models/application_record.rb"
class ApplicationRecord < ActiveRecord::Base
  primary_abstract_class
end
```

`ApplicationRecord` existe para a Nortea ter um lugar onde pôr o que vale
para todos os models. Hoje está vazio.

Tudo que o `Contract` sabe fazer com o banco — buscar, gravar, apagar —
vem dessa herança. As nove linhas do `contract.rb` são só o que é
**diferente** num contrato.

:::term Active Record
O padrão em que um objeto representa uma linha da tabela e sabe se gravar.
O nome é do livro de Martin Fowler, de 2002; o Rails o implementou em 2004.

Um `Contract` é uma linha de `contracts`. Mudar um atributo do objeto não
muda o banco até alguém mandar gravar.
:::

## As colunas não estão no model

A classe `Contrato` do capítulo @cap:classes declarava cada campo com
`attr_reader` e cada valor no `initialize`. O `Contract` não declara
nenhum. Mesmo assim:

```text
$ bin/rails console
nortea(dev)> c = Contract.first
nortea(dev)> c.code
=> "CT-0001"
nortea(dev)> c.daily_rate_cents
=> 48000
```

O Rails lê a tabela quando a classe é carregada e cria um método para cada
coluna. As colunas estão num lugar só, o banco, e o `db/schema.rb` é a
fotografia delas:

```ruby title="db/schema.rb" numbered
create_table "contracts", force: :cascade do |t|
  t.string "code", null: false
  t.bigint "customer_id", null: false
  t.bigint "equipment_id", null: false
  t.string "site"
  t.string "status"
  t.date "start_date"
  t.date "end_date"
  t.integer "daily_rate_cents"
  t.integer "delivery_fee_cents"
  t.string "responsible"
  t.text "notes"
  t.string "purchase_order"
  t.date "begin_date"
  t.integer "billing_day"
  t.bigint "created_by"
  t.string "legacy_id"
  t.datetime "started_at"
  t.datetime "returned_at"
  t.datetime "cancelled_at"
  t.string "cancel_reason"
  t.datetime "created_at", null: false
  t.datetime "updated_at", null: false
end
```

Vinte e duas linhas, mais o `id`, que o Rails cria em toda tabela e não
escreve. A ordem é a ordem em que as colunas foram entrando ao longo de
dez anos: `begin_date` depois de `purchase_order`, `started_at` perto do
fim.

O tipo de cada coluna vira o tipo do valor em Ruby. `date` vira `Date`;
`datetime`, um instante com hora e fuso; `integer`, `Integer`. O
`daily_rate_cents` é inteiro em centavos — a decisão do capítulo
@cap:objetos-e-tipos já estava tomada em 2016.

:::pitfall
Uma coluna nova na tabela vira um método novo no model sem nenhuma linha
em `contract.rb`. Uma coluna apagada faz sumir o método, e todo código que
o chamava quebra com `NoMethodError`. O model de nove linhas depende de
vinte e três colunas que ele não mostra.
:::

## Buscar

Os métodos de busca são da classe:

```text
nortea(dev)> Contract.count
=> 3184
nortea(dev)> Contract.find(2041)
=> #<Contract id: 2041, code: "CT-2041", ...>
nortea(dev)> Contract.find_by(code: "CT-2041")
=> #<Contract id: 2041, code: "CT-2041", ...>
nortea(dev)> Contract.where(site: "contagem").count
=> 37
```

`find` busca pelo `id` e levanta `ActiveRecord::RecordNotFound` se não
achar. `find_by` busca pelo que você disser e devolve `nil` se não achar —
a diferença entre o `fetch` e o `[]` do capítulo @cap:arrays-e-hashes.
`where` devolve todos os que batem, numa coleção que se percorre com os
métodos do capítulo @cap:blocos-e-enumerables.

Cada uma dessas linhas vira SQL, a linguagem do banco. O console mostra:

```text
nortea(dev)> Contract.where(site: "contagem").count
  Contract Count (1.2ms)
  SELECT COUNT(*) FROM "contracts" WHERE "contracts"."site" = $1
  [["site", "contagem"]]
=> 37
```

Não é preciso escrever SQL para usar o model. É preciso saber que ele
existe, porque é ele que roda — e é ele que fica lento.

## A pluralização e a tabela de equipamentos

O `Contract` procura `contracts`. O `Equipment` procura `equipment`, sem
`s`, porque em inglês a palavra não tem plural. O Rails sabe disso. E o
`nortea` tem, mesmo assim, um arquivo de 2016 que o repete:

```ruby title="config/initializers/inflections.rb"
ActiveSupport::Inflector.inflections(:en) do |inflect|
  inflect.uncountable %w[equipment]
end
```

`uncountable` diz ao Rails que a palavra não muda no plural. A lista
padrão do Rails já inclui `equipment`. A linha não muda nada, e está lá
porque, em 2016, alguém viu o plural e não sabia que estava certo.

```text
nortea(dev)> "equipment".pluralize
=> "equipment"
nortea(dev)> Equipment.table_name
=> "equipment"
```

`table_name` diz qual tabela o model usa. Quando a convenção não basta — um
nome em português, uma tabela herdada de outro sistema —, o model declara:
`self.table_name = "equipamentos"`. O `nortea` não precisa.

## O que o Caio digitou

```text
nortea(dev)> c = Contract.find_by(code: "CT-2041")
nortea(dev)> [c.start_date, c.begin_date, c.started_at]
=> [Sun, 01 Mar 2026, Fri, 20 Feb 2026,
    Tue, 03 Mar 2026 06:12:00.000000000 -03 -03:00]
```

Três datas diferentes, para o mesmo contrato.

A Lívia procurou quem lia cada coluna, com a busca do capítulo
@cap:metodos:

| Coluna | Desde | Quem lê | O que é |
|---|---|---|---|
| `start_date` | 2016, Sérgio | faturamento | o primeiro dia cobrado |
| `begin_date` | 2019, Paula | relatório do jurídico | a assinatura, início da vigência |
| `started_at` | 2021, Sérgio | ocupação do pátio | a hora em que o caminhão saiu |

Tabela: Não são três respostas para a mesma pergunta. São três perguntas
com o mesmo nome em inglês.

A `start_date` é a data que o comercial combina: a partir de quando se
cobra. A `begin_date` é a data da assinatura — a Serra Azul assinou em 20
de fevereiro, e o contrato vigora a partir daí para efeito de cláusula. A
`started_at` é um fato do pátio, com hora: a PT-118 saiu às 6h12 do dia 3,
dois dias depois do primeiro dia cobrado, porque o canteiro não estava
liberado.

O commit do Sérgio de 2021 dizia `temporário`. Era a única coluna com
hora, e a única que a Helena teria reconhecido.

:::key
Antes de juntar, apagar ou "corrigir" colunas parecidas num model,
descubra quem lê cada uma e o que ela significa para essa pessoa. Três
colunas com o mesmo nome em inglês podem ser três fatos do negócio. Apagar
duas seria apagar dois relatórios.
:::

Para o módulo novo, a Marta decidiu na mesma tarde: a página da Serra Azul
mostra `started_at` — quando a máquina chegou ao canteiro — e, se ela
estiver vazia, "aguardando saída". As outras duas continuam onde estão.

:::summary
- `Contract < ApplicationRecord < ActiveRecord::Base`: o model herda do
  Rails tudo que fala com o banco.
- As colunas não estão no model. O Rails lê a tabela e cria os métodos; o
  `schema.rb` é a fotografia.
- `find` levanta se não achar; `find_by` devolve `nil`; `where` devolve uma
  coleção. Tudo vira SQL.
- `equipment` já é incontável para o Rails. `table_name` mostra a tabela;
  `self.table_name =` troca.
- Colunas parecidas podem ser fatos diferentes. Descubra quem lê cada uma
  antes de mexer.
:::

:::exercise level=1
No console, escreva a linha que responde cada pergunta:

1. Quantos contratos estão cancelados.
2. O contrato de código `CT-2050`, ou `nil`.
3. Os contratos da PT-118, pelo `equipment_id` 412.

:::answer
```ruby
Contract.where(status: "cancelled").count
Contract.find_by(code: "CT-2050")
Contract.where(equipment_id: 412)
```

A terceira devolve uma coleção, mesmo que haja um só contrato. Para o
primeiro dela, `.first`.
:::

:::exercise level=2
A Lívia quer um método no model que responda "quando a máquina chegou ao
canteiro", do jeito que a Marta decidiu. Escreva `chegada`, que devolve a
`started_at` ou o texto `"aguardando saída"`.

:::answer
```ruby
def chegada
  started_at || "aguardando saída"
end
```

`||` devolve o da esquerda se ele for verdadeiro, e o da direita se não
for. Como só `nil` e `false` são falsos, uma `started_at` preenchida volta
inteira.

Há um custo no desenho: o método devolve às vezes uma data, às vezes um
texto. Quem chamar `c.chegada.strftime` num contrato sem saída recebe
`NoMethodError`. Uma alternativa é deixar o método devolver data ou `nil`
e pôr o texto na view — que é onde texto de tela mora.
:::

:::exercise level=3
O Sérgio propõe, já que agora se sabe o que cada coluna é, renomear as
três para `billing_start`, `signed_on` e `left_yard_at`. Diga o que isso
exige além de mudar o `schema.rb`, e se você faria agora, a nove semanas
de 3 de junho.

:::answer
Exige uma migration para cada renomeação — o `schema.rb` não se edita à
mão —, e a troca de todo código que lê os nomes antigos: o faturamento, o
relatório do jurídico, o de ocupação, as views, o `exportar_patio.rb` que
monta nome de método num texto, os testes. E qualquer relatório fora do
repositório que leia o banco direto, que a busca no código não encontra.

Eu não faria agora. Os nomes estão ruins, mas estão entendidos e anotados.
A renomeação não muda nada que a Helena ou a Serra Azul confiram em 3 de
junho, e cada relatório tocado é um relatório que pode sair errado na
véspera. O que cabe agora é um comentário no model, em cima de cada
coluna, com a tabela deste capítulo. A renomeação vai para depois da
renovação, com calma.
:::
