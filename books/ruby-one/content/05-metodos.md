---
title: "Métodos"
number: 5
slug: metodos
part: p2
kicker: "Um método de três linhas que ninguém chama. A busca no repositório discordava."
goal: >-
  Definir um método, entender o valor que ele devolve sem return, ler o ?
  no fim do nome, passar argumentos por posição e por nome, e saber que um
  método sem chamada no arquivo pode estar sendo chamado de outro lugar.
---

:::story Ninguém chama
Na quarta, 11 de março, a Lívia abriu `app/models/contract.rb` pela
primeira vez inteira. No meio das vinte e três colunas havia três linhas
soltas:

```ruby title="app/models/contract.rb"
def active?
  status == "active" && end_date >= Date.today
end
```

Ela procurou `active?` no próprio arquivo. Nada chamava.

— Posso apagar? — perguntou. — Ninguém chama.

O Caio não tirou os olhos da tela dele.

— Procura no repositório inteiro.

Ela procurou. Quatro resultados. Dois numa view, um num relatório e um
num arquivo de 2021 com o nome `exportar_patio.rb`.

— Ninguém neste arquivo — disse o Caio.
:::

## `def`

Um método é um trecho de código com nome. Ele é definido com `def`, e
termina em `end`:

```ruby title="ativo.rb" numbered
def saudacao
  "Bom dia, pátio"
end

puts saudacao
```

```text
$ ruby ativo.rb
Bom dia, pátio
```

`saudacao` foi chamado na linha 5 e devolveu o texto. Não há `return` no
corpo. No Ruby, **o método devolve o valor da última expressão que
executou**. A última linha do corpo é o texto, e o texto é o que volta.

`return` existe, e serve para sair antes do fim. Na última linha ele não
acrescenta nada, e o código da casa não o escreve ali.

## O método do contrato, fora do Rails

O `active?` do model depende de `status` e `end_date`, que o Rails lê da
tabela. Fora do Rails, dá para escrever a mesma pergunta recebendo os
dois valores de fora:

```ruby title="ativo.rb" numbered
require "date"

def ativo?(status, fim, hoje)
  status == "active" && fim >= hoje
end

hoje = Date.new(2026, 3, 11)

puts ativo?("active", Date.new(2026, 6, 30), hoje)
puts ativo?("cancelled", Date.new(2026, 6, 30), hoje)
puts ativo?("active", Date.new(2026, 3, 10), hoje)
```

```text
$ ruby ativo.rb
true
false
false
```

`require "date"` carrega a classe `Date`, que não vem ligada por padrão
num arquivo Ruby solto. `Date.new(2026, 3, 11)` é o dia 11 de março.
Datas se comparam com `>=`: a mais tarde é a maior.

`&&` é o "e". As duas condições precisam ser verdadeiras. O contrato
cancelado falha na primeira. O que venceu ontem falha na segunda.

:::anatomy title="As partes de um método"
lang: ruby
code: |
  def ativo?(status, fim, hoje)
    status == "active" && fim >= hoje
  end
notes:
  - { line: 1, text: "`def` abre a definição. `ativo?` é o nome, com o `?` que o próprio nome carrega." }
  - { line: 1, text: "Entre parênteses, os parâmetros: nomes locais que recebem os valores de quem chama." }
  - { line: 2, text: "A última expressão é o valor devolvido. Aqui, `true` ou `false`." }
  - { line: 3, text: "`end` fecha. Tudo entre `def` e `end` só roda quando o método é chamado." }
:::

## O `?` no nome

O `?` faz parte do nome. `ativo?` e `ativo` seriam dois métodos
diferentes. O computador não exige nada do `?`: é uma convenção de leitura.
Um método cujo nome termina em `?` responde sim ou não.

O Ruby segue a própria convenção. Já apareceram dois:

```text
irb(main):001> 480.even?
=> true
irb(main):002> nil.nil?
=> true
```

Quem lê `if contrato.active?` sabe, sem abrir o método, que ali volta
verdadeiro ou falso. Quem lê `if contrato.status` não sabe.

:::term Predicado
Um método que responde sim ou não. No Ruby, termina em `?` por convenção:
`active?`, `even?`, `empty?`.

O `?` é parte do nome. Não é operador, e não pode ser acrescentado na hora
de chamar um método que não o tem.
:::

## Parêntese opcional

A chamada pode dispensar os parênteses:

```ruby
puts ativo?("active", fim, hoje)
puts(ativo?("active", fim, hoje))
```

As duas linhas fazem o mesmo. `puts` é um método, e a primeira forma é a
que se lê em todo código Ruby. A convenção da Nortea: parêntese na
chamada que recebe argumentos, exceto em `puts`, `require` e nos métodos
que o Rails usa como declaração — que aparecem mais adiante.

Na definição, o parêntese em volta dos parâmetros também é opcional, e o
código da casa sempre o escreve. Sem parâmetros, nem na definição nem na
chamada: `saudacao`, não `saudacao()`.

## Valor padrão e argumento com nome

Um parâmetro pode ter valor padrão. Quem chama pode omiti-lo:

```ruby title="ativo.rb" numbered
def ativo?(status, fim, hoje = Date.today)
  status == "active" && fim >= hoje
end

puts ativo?("active", Date.new(2026, 6, 30))
```

Sem o terceiro argumento, `hoje` vale `Date.today`, calculado **na hora da
chamada**. O parâmetro com padrão vem depois dos obrigatórios.

Três argumentos por posição já pedem atenção: quem lê
`ativo?("active", a, b)` precisa lembrar qual data é o fim e qual é hoje.
O argumento com nome resolve:

```ruby title="ativo.rb" numbered
def ativo?(status:, fim:, hoje: Date.today)
  status == "active" && fim >= hoje
end

puts ativo?(status: "active", fim: Date.new(2026, 6, 30))
puts ativo?(fim: Date.new(2026, 6, 30), status: "cancelled")
```

Com o `:` depois do nome, o parâmetro passa a ser pedido pelo nome. A ordem
na chamada deixa de importar. `status:` sem valor padrão é obrigatório;
esquecê-lo dá erro que diz o nome:

```text
ativo.rb:1:in 'ativo?': missing keyword: :status (ArgumentError)
```

:::pitfall
`Date.today` como padrão é conveniente e é o que torna o método difícil de
conferir: rodado hoje responde uma coisa, amanhã outra. Para testar o
contrato que vence em 30 de junho, a data de hoje precisa poder vir de
fora. É por isso que `hoje` continua sendo parâmetro, com padrão, e não uma
linha dentro do método.
:::

## Ausência de chamada no arquivo

A Lívia procurou `active?` em `contract.rb` e não achou chamada. O Caio
mandou procurar no repositório:

```text
$ grep -rn "active?" app lib
app/models/contract.rb:41:  def active?
app/views/contracts/_linha.html.erb:3:  <% if contrato.active? %>
app/views/contracts/index.html.erb:12:  ...select(&:active?)
app/reports/ocupacao.rb:27:    next unless c.active?
lib/tasks/exportar_patio.rb:14:    c.public_send("#{campo}?")
```

Quatro chamadas, nenhuma no arquivo em que o método mora. É o normal: um
método de um contrato é chamado por quem tem um contrato na mão — a tela,
o relatório, a exportação.

A última linha é a que merece atenção. `public_send("#{campo}?")` monta o
nome do método num texto e o chama. Se `campo` valer `"active"`, a linha
chama `active?`. Nenhuma busca por `active?` a encontraria se o nome
estivesse inteiro dentro de uma variável.

:::key
Não achar a chamada num arquivo não prova que o método não é chamado. No
Ruby, um método pode ser chamado por um nome montado em tempo de execução.
Antes de apagar, procure no repositório inteiro, procure pelo pedaço do
nome, e pergunte a quem mantém o arquivo.
:::

:::summary
- `def nome ... end` define um método. Ele devolve o valor da última
  expressão; `return` serve para sair antes.
- O `?` é parte do nome e marca um predicado: responde sim ou não.
- Parêntese é opcional na chamada; a casa usa, exceto em `puts` e
  `require`.
- Parâmetro com padrão vem depois dos obrigatórios. Com `nome:`, o
  argumento é pedido pelo nome e a ordem deixa de importar.
- Um método sem chamada no próprio arquivo pode ser chamado de qualquer
  lugar, até por um nome montado num texto.
:::

:::exercise level=1
Escreva um método `vencido?(fim, hoje)` que responde se o contrato já
passou da data de fim. Chame com 30 de junho e hoje em 11 de março, e com
10 de março e hoje em 11 de março.

:::answer
```ruby
require "date"

def vencido?(fim, hoje)
  fim < hoje
end

hoje = Date.new(2026, 3, 11)
puts vencido?(Date.new(2026, 6, 30), hoje)
puts vencido?(Date.new(2026, 3, 10), hoje)
```

```text
false
true
```

O corpo é uma comparação, e a comparação já devolve `true` ou `false`. Não
há `if` nem `return`.
:::

:::exercise level=2
Reescreva `vencido?` com argumentos com nome, com `hoje` opcional. Depois
chame esquecendo o `fim:` e leia a mensagem de erro.

:::answer
```ruby
def vencido?(fim:, hoje: Date.today)
  fim < hoje
end

puts vencido?(fim: Date.new(2026, 3, 10), hoje: Date.new(2026, 3, 11))
puts vencido?(hoje: Date.new(2026, 3, 11))
```

A segunda chamada falha com `missing keyword: :fim (ArgumentError)`. A
mensagem diz o nome do argumento que faltou, e não uma posição.
:::

:::exercise level=3
A Lívia quer apagar um método `suspended?` do `contract.rb` porque
"ninguém chama". A busca por `suspended?` não devolve nada além da
definição. Que outras buscas você faria antes de concordar, e por quê?

:::answer
A busca pelo nome sem o `?` — `suspended` —, porque uma chamada pode montar
o nome num texto, como o `public_send("#{campo}?")` do `exportar_patio.rb`.

A busca por `public_send` e por `send(`, para achar todos os lugares que
chamam método por nome montado, e conferir que valores o nome pode ter.

E a busca fora de `app` e `lib`: a pasta de tarefas, os scripts de
relatório, a pasta de views. Se nenhuma encontrar, ainda vale perguntar ao
Sérgio de onde veio o método. O nome no histórico às vezes diz o
relatório que o usa.
:::
