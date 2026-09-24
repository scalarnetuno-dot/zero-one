---
title: "Módulos"
number: 11
slug: modulos
part: p3
kicker: "O mesmo módulo, incluído em dois models. Um deles redefiniu o total e esqueceu o super. A taxa de entrega sumiu da reserva."
goal: >-
  Compartilhar comportamento entre classes com um módulo, entender em que
  ordem o Ruby procura um método, usar super para estender em vez de
  substituir, e usar módulo como sobrenome para agrupar nomes.
---

:::story Sem o super
A Marta trouxe a conta na segunda, 23 de março. Duas reservas de
compactador para a Serra Azul, Nova Lima. O orçamento que a Nortea mandou
somava diárias e a taxa de entrega de R$ 350. O valor que o sistema gravou
na reserva não tinha a taxa.

— Setecentos reais a menos, nas duas — disse ela. — A Serra Azul não vai
reclamar.

O Sérgio sabia onde procurar.

— O `Billable`. Eu escrevi em 2020 para o contrato e copiei para a
reserva.

A Lívia abriu `app/models/reservation.rb`:

```ruby title="app/models/reservation.rb"
class Reservation < ApplicationRecord
  include Billable

  def total
    daily_rate_cents * days
  end
end
```

— A reserva tem o próprio `total` — disse ela.

— Tem — disse o Sérgio. — Alguém precisou mudar o cálculo das diárias só
para reserva. Em 2022.

— E a taxa?

O Sérgio abriu o `Billable`, leu, e fechou.

— A taxa estava no `total` do módulo.
:::

## Um comportamento, duas classes

O contrato e a reserva têm diária, dias e taxa de entrega. A conta é a
mesma. Copiar o método para as duas classes é o caminho do capítulo
@cap:metodos: uma regra em dois lugares muda em um.

Um **módulo** guarda métodos para serem incluídos em classes:

```ruby title="billable.rb" numbered
# frozen_string_literal: true

module Billable
  TAXA_DE_ENTREGA = 35_000

  def total
    diaria * dias + TAXA_DE_ENTREGA
  end
end
```

```ruby title="contrato.rb" numbered
class Contrato
  include Billable

  attr_reader :diaria, :dias

  def initialize(diaria:, dias:)
    @diaria = diaria
    @dias = dias
  end
end

puts Contrato.new(diaria: 48_000, dias: 3).total
```

```text
$ ruby contrato.rb
179000
```

`module Billable ... end` define o módulo. O nome segue a regra da classe:
maiúscula, sem sublinhado. `include Billable` dentro da classe faz os
métodos do módulo passarem a responder nas instâncias dela. `total` não está
escrito em `Contrato` e responde assim mesmo.

Dentro do `total` do módulo, `diaria` e `dias` são chamadas a métodos que o
módulo **espera** que a classe tenha. O módulo não os define. Quem inclui o
`Billable` assume o compromisso de ter os dois.

:::term Módulo
Um conjunto de métodos e constantes com nome, que não cria instâncias. Não
existe `Billable.new`.

Incluído numa classe com `include`, ele empresta os métodos às instâncias
dela. É o *mixin*: comportamento misturado à classe, sem herança.
:::

## Um módulo que o Ruby já inclui

O Ruby usa o mesmo mecanismo nas próprias classes. O `Comparable` é um
módulo: quem o inclui e define um único método, `<=>`, ganha `<`, `>`,
`between?` e `clamp`.

```ruby title="contrato.rb" numbered
class Contrato
  include Comparable

  attr_reader :fim

  def initialize(fim:)
    @fim = fim
  end

  def <=>(outro)
    fim <=> outro.fim
  end
end

a = Contrato.new(fim: Date.new(2026, 6, 30))
b = Contrato.new(fim: Date.new(2026, 4, 15))
puts a > b
```

```text
true
```

`<=>` compara e devolve -1, 0 ou 1. O `Comparable` constrói o resto em cima
dele. É o mesmo trato do `Billable`: o módulo espera um método, e entrega
vários.

## Onde o Ruby procura um método

Quando a reserva recebe `total`, o Ruby procura o método numa ordem fixa.
A lista está pronta, em `ancestors`:

```text
irb> Reserva.ancestors
=> [Reserva, Billable, Object, Kernel, BasicObject]
```

Primeiro a própria classe. Depois os módulos que ela incluiu, do último
incluído para o primeiro. Depois a classe de cima. O primeiro lugar em que
o nome aparece ganha, e a busca para ali.

É por isso que a reserva de 2022 perdeu a taxa:

```ruby title="reserva.rb" numbered
class Reserva
  include Billable

  attr_reader :diaria, :dias

  def initialize(diaria:, dias:)
    @diaria = diaria
    @dias = dias
  end

  def total
    diaria * dias
  end
end

puts Reserva.new(diaria: 21_000, dias: 4).total
```

```text
84000
```

`Reserva#total` vem antes de `Billable#total` na lista. O do módulo nunca
roda. A taxa de R$ 350 estava lá, e nenhuma reserva chegou até ela.

:::diagram type="flowchart" caption="A reserva recebe total. O Ruby procura de cima para baixo e para no primeiro que encontra."
nodes:
  - { id: r, type: process, text: "Reserva#total" }
  - { id: b, type: process, text: "Billable#total" }
  - { id: o, type: process, text: "Object" }
edges:
  - { from: r, to: b }
  - { from: b, to: o }
:::

## `super`: estender em vez de substituir

`super`, dentro de um método, chama o método de mesmo nome **no próximo
lugar da lista**. Na reserva, o próximo lugar é o `Billable`: um `total`
que começasse com `super` receberia o total do módulo, com a taxa, e
poderia ajustar a partir dele.

Mas o que o Sérgio precisava em 2022 era outro cálculo **das diárias** —
dez por cento a menos na reserva —, não outro total. O jeito que não
esquece a taxa é quebrar o módulo em partes e deixar a classe trocar só a
parte que muda:

```ruby title="billable.rb" numbered
module Billable
  TAXA_DE_ENTREGA = 35_000

  def total
    valor_das_diarias + TAXA_DE_ENTREGA
  end

  def valor_das_diarias
    diaria * dias
  end
end
```

```ruby title="reserva.rb" numbered
class Reserva
  include Billable

  # ... attr_reader e initialize

  def valor_das_diarias
    super * 9 / 10
  end
end

puts Reserva.new(diaria: 21_000, dias: 4).total
```

```text
110600
```

A reserva troca só `valor_das_diarias`, e ainda chama o do módulo com
`super` para não reescrever a conta. `total` continua vindo do módulo, com
a taxa. Diárias com dez por cento de desconto, em inteiros: R$ 756 mais
R$ 350.

:::key
Ao redefinir um método que veio de um módulo, a pergunta é: estou
**substituindo** a regra ou **acrescentando** a ela? Se estiver
acrescentando, o método começa ou termina com `super`. Sem ele, tudo que o
módulo fazia naquele método deixa de acontecer, calado.
:::

:::pitfall
`super` sem parênteses repassa **os mesmos argumentos** que o método
recebeu. `super()` com parênteses vazios não repassa nenhum. Num método sem
parâmetros a diferença não aparece. Num método com parâmetros, `super()`
chama o do módulo com menos argumentos do que ele espera, e o erro vem de
dentro do módulo, longe de quem escreveu a linha.
:::

## Módulo como sobrenome

Um módulo também serve para agrupar nomes. A `patio` começa a ter
`Contrato`, `Reserva`, `Equipamento`. Dentro de um módulo, eles ganham um
sobrenome:

```ruby title="patio.rb" numbered
module Patio
  class Contrato
    # ...
  end

  class Reserva
    # ...
  end
end

c = Patio::Contrato.new(diaria: 48_000, dias: 3)
```

`Patio::Contrato` é o nome completo. O `::` desce do módulo para o que está
dentro dele. Uma biblioteca de terceiros com uma classe `Contrato` não
esbarra na da Nortea. O Rails usa essa forma o tempo todo:
`ActiveRecord::Base`, `ActionController::Base`.

:::summary
- Módulo guarda métodos e constantes; não tem `new`. `include` mistura os
  métodos nas instâncias da classe.
- O módulo pode depender de métodos que a classe precisa ter.
- `ancestors` mostra a ordem de busca: classe, módulos incluídos, classe
  de cima. O primeiro nome encontrado ganha.
- Redefinir um método do módulo sem `super` substitui tudo que ele fazia.
  `super` estende. `super` repassa os argumentos; `super()` não.
- `Modulo::Classe` agrupa nomes e evita colisão.
:::

:::exercise level=1
Diga o que `Contrato.ancestors` devolve, e qual `to_s` responde:

```ruby
module Rotulado
  def to_s = "contrato"
end

class Contrato
  include Rotulado
  include Comparable
end
```

:::answer
`[Contrato, Comparable, Rotulado, Object, Kernel, BasicObject]`. O último
módulo incluído vem primeiro.

`to_s` responde `"contrato"`. `Contrato` não define `to_s`, `Comparable`
também não, e `Rotulado` sim. A busca para ali, antes de chegar ao `to_s`
de `Object`.

`def to_s = "contrato"` é a forma de uma linha de um método, sem `end`.
:::

:::exercise level=2
Escreva um módulo `Atrasavel` com `atrasado?(hoje)` e `dias_de_atraso(hoje)`,
que espera da classe um método `fim`. Inclua em `Contrato` e confira com
um contrato vencido em 15 de março, consultado em 23 de março.

:::answer
```ruby
module Atrasavel
  def atrasado?(hoje)
    fim < hoje
  end

  def dias_de_atraso(hoje)
    atrasado?(hoje) ? (hoje - fim).to_i : 0
  end
end

class Contrato
  include Atrasavel
  attr_reader :fim

  def initialize(fim:) = @fim = fim
end

c = Contrato.new(fim: Date.new(2026, 3, 15))
puts c.atrasado?(Date.new(2026, 3, 23))
puts c.dias_de_atraso(Date.new(2026, 3, 23))
```

```text
true
8
```

O `? :` é a forma curta do `if`: condição, valor se verdadeiro, valor se
falso. O `0` para quem não está atrasado evita o número negativo.
:::

:::exercise level=3
O Diego encontra um terceiro model, `Orcamento`, que também inclui
`Billable` e redefine `total` assim:

```ruby
def total
  super + TAXA_DE_URGENCIA
end
```

Ele funciona. Seis meses depois alguém muda `Billable#total` para receber
um argumento, `total(desconto)`. O que acontece com o `Orcamento`, e que
forma de `super` teria evitado o problema?

:::answer
`Orcamento#total` não recebe argumento. O `super` sem parênteses repassa os
argumentos que o método recebeu — nenhum. `Billable#total(desconto)`
recebe zero argumentos e levanta `ArgumentError: wrong number of arguments
(given 0, expected 1)`, de dentro do módulo.

Nenhuma forma de `super` sozinha evita, porque o `Orcamento` precisa
receber o desconto para repassá-lo. O que evita é redefinir com a mesma
assinatura:

```ruby
def total(desconto)
  super + TAXA_DE_URGENCIA
end
```

Aí o `super` sem parênteses repassa o `desconto`. É por isso que a casa
prefere o `super` sem parênteses: ele acompanha a assinatura de quem o
chama. E é por isso que mudar a assinatura de um método de módulo exige
procurar todos os lugares que o redefinem.
:::
