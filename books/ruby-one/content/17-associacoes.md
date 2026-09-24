---
title: "Associações"
number: 17
slug: associacoes
part: p4
kicker: "O contrato da PT-121 foi cancelado na segunda. Na quarta, a plataforma ainda não aparecia entre as disponíveis."
goal: >-
  Ligar contrato e equipamento com belongs_to e has_many, entender que a
  associação devolve a coleção inteira, dar nome ao filtro de ativo com um
  escopo, e montar a lista de disponíveis sem esquecer o cancelamento.
---

:::story Nenhuma disponível
Na quarta, 8 de abril, a Helena ligou às 6h40 para o celular da Marta.

— Preciso de uma plataforma de doze metros para Betim. A tela diz que não
tem nenhuma disponível.

— E tem?

— A PT-121 está aqui na minha frente. O contrato dela foi cancelado na
segunda. Fui eu que cancelei.

A Marta encaminhou o áudio. Às 8h a Lívia estava com o
`equipment.rb` aberto:

```ruby title="app/models/equipment.rb"
class Equipment < ApplicationRecord
  has_many :contracts

  def self.available
    where.missing(:contracts)
  end
end
```

— Disponível é quem não tem contrato — leu ela.

— Nenhum contrato — disse o Caio. — Nunca. Nem cancelado.

— Então toda plataforma que já foi alugada uma vez...

— Só está disponível se nunca mais for.
:::

## `belongs_to` e `has_many`

Um contrato é de um equipamento. Um equipamento tem vários contratos ao
longo do tempo. No banco, a ligação é uma coluna: `contracts.equipment_id`
guarda o `id` do equipamento. No model, dois lados:

```ruby title="app/models/contract.rb"
class Contract < ApplicationRecord
  belongs_to :equipment
end
```

```ruby title="app/models/equipment.rb"
class Equipment < ApplicationRecord
  has_many :contracts
end
```

`belongs_to :equipment` diz: esta tabela tem a coluna `equipment_id`, e
ela aponta para `Equipment`. `has_many :contracts` diz o outro lado: a
tabela `contracts` tem uma coluna que aponta para mim.

Os nomes seguem a convenção do capítulo @cap:o-que-e-o-rails. `:equipment`
no singular procura `equipment_id` e a classe `Equipment`. `:contracts` no
plural procura a classe `Contract` e, nela, a coluna `equipment_id` — o
nome do model de quem declara, com `_id`.

:::term Associação
A declaração, no model, de uma ligação entre duas tabelas feita por uma
coluna `_id`. `belongs_to` fica em quem tem a coluna. `has_many` fica do
outro lado.

Cada associação cria métodos: `contrato.equipment` devolve um equipamento;
`equipamento.contracts` devolve uma coleção de contratos.
:::

## Navegar

```text
nortea(dev)> c = Contract.find_by(code: "CT-2033")
nortea(dev)> c.equipment.patrimony
=> "PT-121"
nortea(dev)> e = c.equipment
nortea(dev)> e.contracts.count
=> 14
```

`c.equipment` busca o equipamento cujo `id` é o `equipment_id` do
contrato. `e.contracts` busca todos os contratos cujo `equipment_id` é o
`id` do equipamento. Catorze: a PT-121 está na Nortea desde 2017.

**Todos.** A associação não sabe o que é um contrato ativo. Devolve a
coleção inteira: os encerrados de 2018, o cancelado de segunda, o que
ainda vai começar em maio.

```text
nortea(dev)> e.contracts.map(&:status).tally
=> {"closed"=>12, "cancelled"=>1, "reserved"=>1}
```

`tally` conta quantas vezes cada valor aparece. Nenhum ativo. Doze
encerrados, o cancelado de segunda e uma reserva para maio. A PT-121 está
livre hoje — e a regra de 2016, "disponível é quem não tem contrato",
dizia que não.

## Escopo: o filtro com nome

O filtro que faltava é "os contratos que ocupam a máquina agora". Um
**escopo** dá nome a um filtro no model:

```ruby title="app/models/contract.rb" numbered
class Contract < ApplicationRecord
  belongs_to :equipment

  scope :active, -> { where(status: "active") }
  scope :current, ->(hoje = Date.current) {
    active.where("end_date >= ?", hoje)
  }
end
```

`scope :active, -> { ... }` cria o método de classe `Contract.active`. O
`->` com o bloco é um *lambda*: um bloco guardado num objeto, a ideia de
1993 com outro nome, para o Rails chamar depois. `current` recebe a data,
com padrão, pelo mesmo motivo do `hoje` do capítulo @cap:metodos.

O `?` dentro do texto do `where` é um lugar reservado. O Rails põe o valor
de `hoje` ali, no formato certo e protegido — nunca interpolado com `#{}`.

E o escopo funciona **através da associação**:

```text
nortea(dev)> e.contracts.current
=> []
nortea(dev)> Contract.current.count
=> 381
```

`e.contracts.current` é "os contratos desta máquina que ocupam agora". A
associação dá a coleção; o escopo filtra; o Rails junta os dois numa
consulta só.

:::key
A associação devolve **todos** os registros ligados. Cancelado,
encerrado, futuro. O que a Helena chama de "ocupado" é um filtro, e esse
filtro precisa ter nome, estar num lugar só, e ser usado por quem pergunta
disponibilidade.
:::

## Os disponíveis, de novo

Com o escopo, a regra da Helena se escreve pelo que ela é: disponível é o
equipamento que **nenhum contrato atual** segura.

```ruby title="app/models/equipment.rb" numbered
class Equipment < ApplicationRecord
  has_many :contracts

  def self.available(hoje = Date.current)
    ocupados = Contract.current(hoje).select(:equipment_id)
    where.not(id: ocupados)
  end

  def available?(hoje = Date.current)
    contracts.current(hoje).none?
  end
end
```

```text
nortea(dev)> Equipment.available.where(kind: "plataforma_12m")
=> [#<Equipment id: 419, patrimony: "PT-121", ...>, ...]
```

`select(:equipment_id)` não traz os contratos: monta uma subconsulta com os
`equipment_id` ocupados. `where.not(id: ...)` pega os equipamentos fora
dela. O banco resolve tudo numa consulta.

A PT-121 voltou. A PT-118, que o CT-2041 segura, não aparece.

:::pitfall
`contracts.current(hoje).none?` responde uma máquina. Na lista da manhã,
chamado para quatrocentos e trinta equipamentos um por um, vira
quatrocentas e trinta consultas — uma por `available?`. Para uma lista, a
pergunta vai ao banco de uma vez, pelo método de classe. Para uma tela com
uma máquina só, o de instância basta.

O Rails tem uma ferramenta para carregar associações de muitos registros
de uma vez, `includes(:contracts)`. Ela resolve o número de consultas e
traz **todos** os contratos de cada máquina para a memória — os catorze da
PT-121, os encerrados de 2018. Para a pergunta "está livre?", a subconsulta
é menor.
:::

## E a reserva de maio

A PT-121 tem uma reserva que começa em maio. Ela não ocupa hoje, e o
escopo `current` não a pega, porque o status dela é `reserved`, não
`active`. A plataforma aparece disponível para Betim — o que é certo para
hoje e errado para quem quiser alugá-la até julho.

A Lívia levou a pergunta à Marta, que levou à Helena, que respondeu com um
áudio de oito segundos: "disponível é hoje. Se for mais que uma semana, eu
olho a agenda". A regra ficou como está, com um comentário no método. O
período entra na conta mais adiante, quando a validação precisar recusar
duas reservas na mesma data.

:::summary
- `belongs_to` fica em quem tem a coluna `_id`; `has_many`, do outro lado.
  Os nomes seguem a convenção.
- `contrato.equipment` devolve um registro; `equipamento.contracts`, a
  coleção **inteira**, sem filtro.
- `scope :nome, -> { where(...) }` dá nome a um filtro; o escopo funciona
  através da associação.
- `?` no `where` é um lugar reservado para o valor. Nunca `#{}`.
- Lista de muitos registros pergunta ao banco de uma vez; o método de
  instância é para um registro.
:::

:::exercise level=1
Escreva, no console, a linha para cada pergunta:

1. O patrimônio do equipamento do contrato `CT-2041`.
2. Quantos contratos a PT-118 já teve.
3. Os contratos atuais da PT-118.

:::answer
```ruby
Contract.find_by(code: "CT-2041").equipment.patrimony
Equipment.find_by(patrimony: "PT-118").contracts.count
Equipment.find_by(patrimony: "PT-118").contracts.current
```

A segunda conta todos os contratos, de qualquer status. A terceira usa o
escopo através da associação.
:::

:::exercise level=2
O `Customer` tem muitos contratos, e a Serra Azul é um `Customer`. Declare
os dois lados da associação e escreva a linha que devolve os patrimônios
que a Serra Azul ocupa hoje.

:::answer
```ruby
class Customer < ApplicationRecord
  has_many :contracts
end

class Contract < ApplicationRecord
  belongs_to :customer
end
```

```ruby
serra = Customer.find_by(name: "Construtora Serra Azul")
serra.contracts.current.includes(:equipment)
     .map { |c| c.equipment.patrimony }
```

O `includes(:equipment)` carrega os equipamentos desses contratos de uma
vez. Sem ele, o `map` faria uma consulta para cada contrato. Aqui ele é a
ferramenta certa: a lista precisa mesmo dos equipamentos, e são só os dos
contratos atuais.
:::

:::exercise level=3
O Diego pergunta o que acontece se alguém apagar um equipamento que tem
contratos, com `Equipment.find(419).destroy`. Descubra, diga o que você
quer que aconteça, e escreva a declaração.

:::answer
Sem nenhuma opção na associação, o Rails tenta apagar o equipamento, e o
banco recusa se houver chave estrangeira em `contracts.equipment_id` —
`ActiveRecord::InvalidForeignKey`. Sem chave estrangeira no banco, o
equipamento some e catorze contratos ficam apontando para um `id` que não
existe.

O que a Nortea quer: não apagar máquina com histórico. Contrato encerrado é
um fato de faturamento.

```ruby
has_many :contracts, dependent: :restrict_with_error
```

Com isso, o `destroy` não apaga, devolve `false` e deixa uma mensagem de
erro no equipamento, que a tela pode mostrar. Máquina vendida ou sucateada
vira um status, não uma linha apagada.
:::
