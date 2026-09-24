---
title: "Blocos e enumerables"
number: 9
slug: blocos-e-enumerables
part: p2
kicker: "A lista da Helena tinha quatro plataformas. O select devolveu três. A quarta tinha status nil desde uma importação de 2019."
goal: >-
  Entregar um trecho de código a um método, percorrer, transformar e
  filtrar a lista da manhã com each, map, select e find, e saber o que um
  filtro faz com o valor que ninguém previu.
---

:::story A quarta plataforma
A lista de divergências saiu na terça, 17 de março, às 7h. A Helena
respondeu às 7h20, por mensagem para a Marta, que encaminhou sem
comentário:

> Serra Azul Contagem tem QUATRO plataformas. A lista diz três. Falta a
> PT-133. Ela está lá, eu vi o caminhão sair.

A Lívia rodou de novo. Três. Procurou a PT-133 no banco de homologação.

```text
{:code=>"CT-1987", :equipment=>"PT-133", :site=>"contagem",
 :status=>nil}
```

— `status` nulo — disse ela.

O Sérgio olhou por cima do ombro dela.

— Importação de 2019. Os contratos que vieram da planilha antiga entraram
sem status. A tela mostra como ativo porque a view testa se é cancelado.

— E o meu filtro testa se é ativo.

— Então para a tela ela existe, e para o seu filtro não.
:::

## O bloco

O capítulo @cap:fevereiro-de-1993 apresentou o bloco como a ideia que o
Matz trouxe de Smalltalk: um trecho de código entregue a um método, que
decide quando chamá-lo. A sintaxe é um par de chaves — ou `do` e `end` —
depois da chamada:

```ruby
3.times { puts "carregando" }

3.times do
  puts "carregando"
end
```

As duas formas fazem o mesmo. `times` é um método do inteiro. Ele chama o
bloco três vezes. A convenção da casa: chaves para bloco de uma linha,
`do ... end` para bloco de várias.

O bloco pode receber valores de quem o chama. Os nomes ficam entre barras,
logo no começo:

```ruby
3.times { |i| puts "volta #{i}" }
```

```text
volta 0
volta 1
volta 2
```

`|i|` é o parâmetro do bloco. O `times` passa 0, depois 1, depois 2.

:::term Bloco
Um trecho de código entre `{ }` ou `do ... end`, entregue a um método na
chamada. O método decide quando executá-lo e com quais valores. Os
parâmetros vêm entre `| |`.

Um método recebe no máximo um bloco, e o bloco não é um argumento entre
os parênteses: vem depois deles.
:::

## `yield`: o lado de quem recebe

Um método seu também pode receber bloco. `yield` chama o bloco que veio:

```ruby title="bloco.rb" numbered
def para_cada_turno
  yield "6h"
  yield "13h"
end

para_cada_turno { |hora| puts "carga das #{hora}" }
```

```text
$ ruby bloco.rb
carga das 6h
carga das 13h
```

O método não sabe o que o bloco faz. Sabe quando chamá-lo e com o quê. É a
divisão de trabalho do desenho de 1993: percorrer é do método; o que fazer
com cada item é de quem chama.

## `each`: percorrer

Todo array tem `each`, que chama o bloco uma vez para cada item:

```ruby title="manha.rb" numbered
# frozen_string_literal: true

contratos = [
  { code: "CT-2041", equipment: "PT-118", status: "active" },
  { code: "CT-2033", equipment: "PT-121", status: "cancelled" },
  { code: "CT-2050", equipment: "PT-140", status: "reserved" },
  { code: "CT-1987", equipment: "PT-133", status: nil },
]

contratos.each do |c|
  puts "#{c[:equipment]}: #{c[:status]}"
end
```

```text
$ ruby manha.rb
PT-118: active
PT-121: cancelled
PT-140: reserved
PT-133: 
```

O `nil` interpolado vira texto vazio. A linha da PT-133 sai sem status, e
sem erro.

O hash também tem `each`, que passa chave e valor:

```ruby
{ code: "CT-2041", site: "contagem" }.each do |chave, valor|
  puts "#{chave} = #{valor}"
end
```

## `map`, `select`, `reject`, `find`

`each` percorre e devolve a própria lista: serve para efeito, como
escrever na tela. Para **produzir** alguma coisa a partir da lista, há
métodos que usam o valor que o bloco devolve.

**`map` transforma.** Devolve uma lista nova, com o valor do bloco para
cada item:

```text
irb> contratos.map { |c| c[:equipment] }
=> ["PT-118", "PT-121", "PT-140", "PT-133"]
```

**`select` filtra.** Devolve os itens para os quais o bloco é verdadeiro:

```text
irb> contratos.select { |c| c[:status] == "active" }
=> [{code: "CT-2041", equipment: "PT-118", status: "active"}]
```

**`reject` filtra ao contrário.** Devolve os itens para os quais o bloco é
falso.

**`find` acha o primeiro.** Devolve o primeiro item para o qual o bloco é
verdadeiro, ou `nil`:

```text
irb> contratos.find { |c| c[:equipment] == "PT-140" }
=> {code: "CT-2050", equipment: "PT-140", status: "reserved"}
```

Nenhum desses métodos altera `contratos`. Todos devolvem algo novo.

:::anatomy title="As partes de uma chamada com bloco"
lang: ruby
code: |
  ocupam = contratos.select { |c| c[:status] == "active" }
notes:
  - { line: 1, text: "`contratos.select` é a chamada. O método percorre a lista." }
  - { line: 1, text: "`{ |c| ... }` é o bloco. `c` recebe cada contrato, um por vez." }
  - { line: 1, text: "O valor da última expressão do bloco é a resposta. `select` guarda o item quando ela é verdadeira." }
  - { line: 1, text: "O resultado é uma lista nova. `contratos` não muda." }
:::

## Atalhos: `&:` e `it`

Quando o bloco só chama um método no item, há uma forma curta:

```ruby
patrimonios = ["pt-118", "pt-121"]
patrimonios.map { |p| p.upcase }
patrimonios.map(&:upcase)
```

As duas linhas devolvem `["PT-118", "PT-121"]`. `&:upcase` é "chame
`upcase` em cada um". É a forma que apareceu no `select(&:active?)` que a
busca do capítulo @cap:metodos encontrou numa view.

O Ruby 3.4 trouxe outra: `it`, o nome do item quando o bloco tem um
parâmetro só e ninguém o declarou:

```ruby
contratos.map { it[:equipment] }
```

O servidor da Nortea está no 3.3, que não tem `it`. Código que vai para o
`nortea` usa `|c|`.

## Somar, contar, ordenar, agrupar

```ruby
diarias = [48_000, 18_990, 32_000]

diarias.sum                              # => 98990
contratos.count { |c| c[:status] == "active" }   # => 1
contratos.sort_by { |c| c[:equipment] }
contratos.group_by { |c| c[:status] }
```

`sum` soma. `count` com bloco conta os verdadeiros. `sort_by` ordena pelo
valor que o bloco devolve. `group_by` devolve um hash: a chave é o valor do
bloco, o valor é a lista dos itens que deram aquela chave.

```text
irb> contratos.group_by { |c| c[:status] }.keys
=> ["active", "cancelled", "reserved", nil]
```

`nil` aparece como grupo. O `group_by` não esconde o que ninguém previu.

## O filtro e o `nil`

A lista de divergências da Lívia filtrava assim:

```ruby
ocupam = contratos.select do |c|
  ["active", "reserved"].include?(c[:status])
end
```

Três itens. A PT-133, com `status: nil`, não está na lista de status, o
bloco devolve falso, e o `select` a descarta.

A view do sistema de 2016 testava o contrário:

```ruby
visiveis = contratos.reject { |c| c[:status] == "cancelled" }
```

Quatro itens. O `nil` não é igual a `"cancelled"`, então fica.

As duas linhas parecem dizer o mesmo — "os que ocupam" — e divergem
exatamente no valor que nenhuma delas previu. Filtrar pelo que entra
("active ou reserved") descarta o desconhecido. Filtrar pelo que sai ("não
cancelado") mantém.

:::key
Um filtro é uma decisão sobre o valor que você não previu. `select` pelo
que é permitido descarta o desconhecido; `reject` pelo que é proibido o
deixa passar. Escolha sabendo qual dos dois o pátio aceita — e procure o
desconhecido antes de escolher.
:::

A correção não é trocar um filtro pelo outro. É descobrir o desconhecido
e decidir sobre ele:

```ruby
sem_status = contratos.select { |c| c[:status].nil? }
puts "#{sem_status.size} contrato(s) sem status"
```

```text
1 contrato(s) sem status
```

Na homologação, o número real foi 212. Todos da importação de 2019. A
Marta levou a lista à Helena, que confirmou quais ainda estavam no pátio.
O status deles vai ser preenchido por uma migração de dados, quando o
livro chegar às tabelas. Até lá, a lista da manhã os mostra à parte, com
o aviso.

:::milestone
Fim da Parte 2. Na pasta `patio` há Ruby sem Rails: diária em centavos, um
predicado `ativo?`, o relatório de ocupação com uma condição só, o
contrato da planilha e o do banco na mesma forma, e a lista da manhã
filtrada sem perder a PT-133. É o pedaço da linguagem que o `nortea` usa
em todo arquivo.
:::

:::summary
- Bloco é código entre `{ }` ou `do ... end`, entregue a um método. `yield`
  o chama de dentro do método.
- `each` percorre, para efeito. `map` transforma, `select` e `reject`
  filtram, `find` acha o primeiro. Nenhum altera a lista.
- `&:metodo` chama o método em cada item. `it` é do 3.4, e o servidor está
  no 3.3.
- `sum`, `count`, `sort_by` e `group_by` resolvem a maioria das contas da
  manhã.
- Filtrar pelo permitido descarta o desconhecido; filtrar pelo proibido o
  mantém. Procure o `nil` antes de escolher.
:::

:::exercise level=1
Com a lista `contratos` do capítulo, escreva uma linha para cada pedido:

1. Os patrimônios, em maiúsculas.
2. Os contratos cancelados.
3. O contrato da PT-118.
4. Quantos contratos não têm status.

:::answer
```ruby
contratos.map { |c| c[:equipment].upcase }
contratos.select { |c| c[:status] == "cancelled" }
contratos.find { |c| c[:equipment] == "PT-118" }
contratos.count { |c| c[:status].nil? }
```

A terceira devolve o hash, ou `nil` se a PT-118 não estiver na lista.
:::

:::exercise level=2
Escreva um método `por_canteiro(contratos)` que devolve um hash com o
canteiro como chave e a lista de patrimônios como valor. Use `group_by` e
`map`.

:::answer
```ruby
def por_canteiro(contratos)
  contratos
    .group_by { |c| c[:site] }
    .transform_values { |lista| lista.map { |c| c[:equipment] } }
end
```

`group_by` agrupa os hashes por canteiro. `transform_values` troca cada
valor — a lista de hashes — pelo que o bloco devolve: a lista de
patrimônios. As chaves não mudam.

Um contrato com `site: nil` vira um grupo com chave `nil`. É o mesmo aviso
do capítulo: o desconhecido aparece em vez de sumir.
:::

:::exercise level=3
O Sérgio propõe resolver a PT-133 trocando o `select` da Lívia por
`reject { |c| c[:status] == "cancelled" }`, "igual à tela". Diga o que isso
resolve, o que passa a entrar errado, e o que você faria.

:::answer
Resolve a PT-133: o `nil` deixa de ser descartado.

O que passa a entrar errado é qualquer outro status desconhecido. Um
`"closed"`, um `"suspended"`, um `"Active"` com maiúscula vindo de outra
importação — todos contam como ocupando, porque não são `"cancelled"`. O
defeito muda de lado: em vez de a lista esconder plataforma, ela passa a
prender plataforma livre.

O que faria: manter o filtro pelo permitido, e tratar o desconhecido à
parte, visível — a contagem de contratos sem status, e a lista deles para
a Helena conferir. O desconhecido não é decidido por um filtro. É decidido
por quem sabe onde a plataforma está.
:::
