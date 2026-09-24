---
title: "Condicionais"
number: 6
slug: condicionais
part: p2
kicker: "O contrato estava cancelado desde segunda. O relatório dizia que a plataforma continuava ocupada, e estava certo segundo o próprio código."
goal: >-
  Escrever decisões com if, elsif, unless e case; saber o que o Ruby
  considera falso; e reconhecer dois ifs independentes onde deveria haver
  uma escolha só.
---

:::story Cancelado e ocupado
O Diego chegou na quinta, 12 de março, com o celular na mão e uma captura
do relatório de ocupação.

— O CT-2033 foi cancelado na segunda. A Helena cancelou na tela. O
relatório diz que a PT-121 continua ocupada por ele.

— O cancelamento gravou? — perguntou a Lívia.

— Gravou. `status` está `cancelled`.

O Caio abriu `app/reports/ocupacao.rb` e rolou até o trecho:

```ruby title="app/reports/ocupacao.rb"
situacao = "livre"
if c.status == "active"
  situacao = "ocupado"
end
if c.end_date >= hoje
  situacao = "ocupado"
end
```

A Lívia leu duas vezes.

— O segundo `if` não sabe do primeiro.

— Ninguém disse para ele — disse o Caio.
:::

## `if`, `elsif`, `else`

A forma completa:

```ruby title="situacao.rb" numbered
status = "cancelled"

if status == "active"
  puts "ocupado"
elsif status == "reserved"
  puts "reservado"
else
  puts "livre"
end
```

```text
$ ruby situacao.rb
livre
```

O Ruby testa de cima para baixo e executa **só o primeiro ramo** cuja
condição é verdadeira. Os outros são pulados. `elsif` se escreve assim,
sem o segundo `e` de "else" — `elseif` e `else if` são erros de quem vem de
outra linguagem. `end` fecha o bloco inteiro, uma vez.

## Dois `if` não são uma escolha

O relatório de ocupação tinha dois `if` separados. Cada um é uma decisão
independente, e o segundo roda **sempre**, tenha o primeiro rodado ou não:

```ruby title="ocupacao.rb" numbered
require "date"

status = "cancelled"
fim = Date.new(2026, 6, 30)
hoje = Date.new(2026, 3, 12)

situacao = "livre"
if status == "active"
  situacao = "ocupado"
end
if fim >= hoje
  situacao = "ocupado"
end

puts situacao
```

```text
$ ruby ocupacao.rb
ocupado
```

O contrato cancelado tem data de fim em 30 de junho. O primeiro `if`
falha, o segundo acerta, e a plataforma aparece ocupada. O código faz
exatamente o que está escrito: "se estiver ativo, ocupado; e também, se
não tiver vencido, ocupado".

A regra da Helena é outra. Ocupado é **ativo e ainda não vencido**, as duas
coisas ao mesmo tempo:

```ruby title="ocupacao.rb" numbered
situacao =
  if status == "active" && fim >= hoje
    "ocupado"
  else
    "livre"
  end

puts situacao
```

```text
$ ruby ocupacao.rb
livre
```

Uma condição, dois ramos. E repare que o `if` inteiro está à direita do
`=`. No Ruby, `if` é uma expressão: devolve o valor do ramo que rodou. A
variável recebe esse valor, e não existe um momento em que ela vale
"livre" por engano antes de o segundo teste mudar de ideia.

:::key
Dois `if` seguidos, que atribuem à mesma variável, quase sempre são uma
escolha escrita como duas. Pergunte: os dois podem ser verdadeiros ao
mesmo tempo? Se podem, e só um deveria valer, é um `if` com `elsif`, ou uma
condição com `&&`.
:::

## O que é falso

No Ruby, só dois valores são falsos numa condição: `false` e `nil`. Todo o
resto é verdadeiro — inclusive o zero e o texto vazio.

```text
irb(main):001> puts "sim" if 0
sim
=> nil
irb(main):002> puts "sim" if ""
sim
=> nil
irb(main):003> puts "sim" if nil
=> nil
```

Quem vem de PHP, JavaScript ou Python espera que `0` e `""` sejam falsos.
No Ruby não são. A consequência na Nortea é concreta: uma multa de zero
centavos é verdadeira num `if`.

```ruby
multa = 0
puts "cobrar" if multa      # imprime "cobrar"
puts "cobrar" if multa > 0  # não imprime
```

:::term Verdadeiro e falso
Numa condição, `false` e `nil` são falsos. Qualquer outro objeto é
verdadeiro: `0`, `""`, a lista vazia.

Para perguntar se um número é zero, compare — `multa > 0`, `multa.zero?`.
Para perguntar se um texto está vazio, pergunte — `nome.empty?`.
:::

## `unless`, e o `if` no fim da linha

`unless` é o `if` ao contrário: executa quando a condição é falsa.

```ruby
unless responsavel
  puts "contrato sem responsável"
end
```

Lê-se "a menos que haja responsável". Para uma condição simples, lê bem.
Com `else`, ou com `&&` e `||` dentro, fica difícil de ler em voz alta, e a
casa troca por um `if` com a condição invertida.

As duas formas têm uma versão de uma linha, com a condição no fim:

```ruby
puts "contrato sem responsável" unless responsavel
puts "cobrar multa" if multa > 0
```

É o modificador. O controller de 2021 da Nortea usa muito:

```ruby title="app/controllers/contracts_controller.rb"
flash[:alerta] = "Sem responsável" unless @contract.responsible
```

A linha começa pela ação e termina na condição. Para um aviso ou uma saída
antecipada, é o jeito mais curto de dizer. Para uma ação que muda dado, a
casa prefere o `if` de bloco: quem lê a linha pelo começo vê a gravação
antes de ver que ela é condicional.

## `case`

Quando a mesma variável é comparada com vários valores, o `case` diz isso
de uma vez:

```ruby title="situacao.rb" numbered
status = "reserved"

rotulo =
  case status
  when "active" then "Em uso"
  when "reserved" then "Reservado"
  when "cancelled", "closed" then "Encerrado"
  else "Desconhecido"
  end

puts rotulo
```

```text
$ ruby situacao.rb
Reservado
```

Cada `when` compara com o valor do `case`. Um `when` aceita vários
valores separados por vírgula. O `else` pega o que sobrar — e na Nortea ele
nunca fica vazio, porque o `status` que ninguém previu é justamente o que
o Diego vai trazer.

O `when` também aceita um intervalo:

```ruby
dias_de_atraso = 4

multa =
  case dias_de_atraso
  when 0 then 0
  when 1..3 then 180_000
  else 180_000 * dias_de_atraso
  end
```

`1..3` é o intervalo de 1 a 3, inclusive. O `when` pergunta se o número
está dentro dele.

:::pitfall
O `case` compara com `===`, não com `==`. Para texto e número, o efeito é o
mesmo. Para intervalo, `===` pergunta "está dentro?", e é por isso que
`when 1..3` funciona. O `case` sem valor depois dele — só `case` e os
`when` com condições completas — existe, e é um `if` com `elsif` escrito
de outro jeito. A casa usa o `if`.
:::

:::summary
- `if` / `elsif` / `else` executa só o primeiro ramo verdadeiro. `elsif`
  sem o `e`.
- Dois `if` que atribuem à mesma variável são duas decisões. Se só uma deve
  valer, é uma condição com `&&` ou um `elsif`.
- `if` é expressão: devolve o valor do ramo.
- Só `false` e `nil` são falsos. Zero e texto vazio são verdadeiros.
- `unless` é o `if` negado; o modificador no fim da linha serve para
  avisos. `case` / `when` compara um valor com vários, e aceita intervalo.
:::

:::exercise level=1
Diga o que cada linha imprime:

```ruby
puts "a" if 0
puts "b" if nil
puts "c" unless false
puts "d" if "".empty?
```

:::answer
`a`, `c` e `d`. Zero é verdadeiro. `nil` é falso. `unless false` executa.
`"".empty?` pergunta se o texto está vazio, e está.
:::

:::exercise level=2
Reescreva o trecho com um `case`, e acrescente o ramo para um status que
ninguém previu:

```ruby
if status == "active"
  cor = "verde"
elsif status == "reserved"
  cor = "amarelo"
elsif status == "cancelled"
  cor = "cinza"
end
```

:::answer
```ruby
cor =
  case status
  when "active" then "verde"
  when "reserved" then "amarelo"
  when "cancelled" then "cinza"
  else "vermelho"
  end
```

Na versão original, um status desconhecido deixava `cor` sem valor — ou com
o valor de uma volta anterior, se a variável já existisse. O `else` dá uma
cor que chama atenção para o caso que ninguém previu.
:::

:::exercise level=3
O Diego traz outro caso: um contrato `active` com data de fim em 11 de
março, consultado em 12 de março. O relatório corrigido diz "livre". A
Helena diz que a plataforma ainda está no canteiro, esperando o caminhão de
volta. Quem está certo, e o que falta na regra?

:::answer
Os dois descrevem coisas diferentes. O relatório diz que o **contrato**
não segura mais a plataforma. A Helena diz onde a **plataforma** está.

Falta na regra a devolução: um contrato vencido e ainda não devolvido não
libera a máquina para outro contrato. A condição de ocupado passa a ser
"ativo e não vencido, **ou** vencido e sem data de devolução". A regra
nova não cabe num `if` escrito por quem só olha a tabela. Ela é da Helena,
e alguém precisa perguntar a ela antes de escrever o `||`.
:::
