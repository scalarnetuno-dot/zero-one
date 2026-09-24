---
title: "Strings e símbolos"
number: 7
slug: strings-e-simbolos
part: p2
kicker: "O status era active dos dois lados. Um deles tinha dois-pontos na frente, e a comparação dava falso."
goal: >-
  Trabalhar com texto sem surpresa, saber quando uma string pode ser
  alterada no lugar, entender o que é um símbolo, e nunca mais comparar
  :active com "active" esperando verdadeiro.
---

:::story Dois-pontos
Na sexta, 13 de março, a Lívia corrigiu o relatório de ocupação com o
`&&` da véspera e, para deixar legível, tirou os status de dentro do `if`:

```ruby
OCUPAM = [:active, :reserved]

if OCUPAM.include?(c.status) && c.end_date >= hoje
```

Rodou contra o banco de homologação. Nenhuma plataforma ocupada. Nenhuma,
das quatrocentas e trinta.

— Tudo livre — disse ela. — Isso está errado.

O Caio olhou o `OCUPAM` e depois o console.

```text
>> c.status
=> "active"
```

— A tabela devolve texto. Você escreveu símbolo.

— É a mesma palavra.

— Para você.
:::

## String

Texto, no Ruby, é um objeto da classe `String`, e tem muitos métodos:

```text
irb(main):001> "  plataforma PT-118 ".strip
=> "plataforma PT-118"
irb(main):002> "pt-118".upcase
=> "PT-118"
irb(main):003> "PT-118".start_with?("PT")
=> true
irb(main):004> "Serra Azul, Contagem".include?("Contagem")
=> true
irb(main):005> "CT-2041".sub("CT-", "")
=> "2041"
```

`strip` tira os espaços das pontas — o que a planilha põe quando alguém
digita o patrimônio com espaço antes. `upcase` põe tudo em maiúsculas.
`sub` troca a primeira ocorrência; `gsub` trocaria todas. Nenhum desses
métodos altera o texto original: todos devolvem um texto novo.

```text
irb(main):006> patrimonio = "pt-118"
=> "pt-118"
irb(main):007> patrimonio.upcase
=> "PT-118"
irb(main):008> patrimonio
=> "pt-118"
```

## O `!` e a string que muda no lugar

Vários desses métodos têm um irmão com `!` no fim:

```text
irb(main):009> patrimonio = "pt-118"
=> "pt-118"
irb(main):010> patrimonio.upcase!
=> "PT-118"
irb(main):011> patrimonio
=> "PT-118"
```

`upcase!` altera **o próprio objeto**. Não cria um texto novo: muda o que
já existia. O `!` no nome, como o `?`, é convenção de leitura: avisa que o
método faz algo mais perigoso que o irmão sem `!` — aqui, mudar o objeto em
que foi chamado.

Mudar no lugar importa quando o mesmo texto está em dois nomes:

```text
irb(main):012> a = "pt-118"
=> "pt-118"
irb(main):013> b = a
=> "pt-118"
irb(main):014> b.upcase!
=> "PT-118"
irb(main):015> a
=> "PT-118"
```

`b = a` não copia o texto. Faz `b` apontar para o **mesmo** objeto. Quando
`b` muda o objeto, `a` vê a mudança, porque não há dois textos: há um, com
dois nomes.

O `<<` também muda no lugar. Serve para ir montando um texto:

```ruby
linha = "PT-118"
linha << " | Serra Azul"
linha << " | Contagem"
puts linha
```

```text
PT-118 | Serra Azul | Contagem
```

## O texto escrito entre aspas vai congelar

A partir do Ruby 3.4, um texto escrito diretamente no arquivo — um
*literal* — nasce "resfriado": ele ainda pode ser alterado, mas o Ruby
avisa que isso vai deixar de funcionar numa versão futura, quando os
literais passarem a nascer congelados. O aviso aparece com os avisos de
depreciação ligados:

```text
$ ruby -W:deprecated linha.rb
linha.rb:2: warning: literal string will be frozen in the future
```

Congelado quer dizer que o objeto não aceita mais alteração. Um texto
congelado recebendo `<<` levanta `FrozenError`.

É por isso que muitos arquivos Ruby começam com esta linha:

```ruby
# frozen_string_literal: true
```

É um comentário mágico: o Ruby lê essa primeira linha e passa a congelar
todos os literais do arquivo desde já. O `nortea` tem esse comentário em
parte dos arquivos, os escritos depois de 2021. A partir daqui, o código
novo da `patio` também tem.

Com ele, para montar um texto aos poucos, parte-se de um texto que não
seja literal:

```ruby title="linha.rb" numbered
# frozen_string_literal: true

linha = +"PT-118"
linha << " | Serra Azul"
puts linha
```

O `+` antes do literal devolve uma cópia que pode ser alterada. Na maioria
das vezes nem isso é preciso: a interpolação monta o texto inteiro de uma
vez, sem alterar nada.

```ruby
linha = "#{patrimonio} | #{cliente} | #{canteiro}"
```

## Símbolo

Um símbolo se escreve com dois-pontos na frente:

```text
irb(main):016> :active.class
=> Symbol
```

Ele parece um texto e é outra coisa. Um símbolo é um **nome**: não tem
métodos de texto para alterar, não muda, e existe uma única vez no
programa inteiro. Dois `:active` escritos em arquivos diferentes são o
mesmo objeto:

```text
irb(main):017> :active.object_id == :active.object_id
=> true
irb(main):018> "active".object_id == "active".object_id
=> false
```

`object_id` é o número que identifica o objeto. Os dois símbolos têm o
mesmo; os dois textos, não — cada aspa criou um objeto.

O símbolo aparece sempre que o valor é um **nome escolhido por quem
escreve o código**: a chave de um hash, o nome de um método, a opção de
uma configuração. O texto aparece quando o valor **vem de fora**: o que a
Helena digitou, o que a tabela guardou, o que a planilha trouxe.

:::term Símbolo
Um nome imutável e único, escrito `:nome`. Usado quando o valor é um
rótulo escolhido no código — chave, opção, nome de método —, não um dado
vindo de fora.

`:active` e `"active"` não são iguais. São objetos de classes diferentes.
:::

## `:active` não é `"active"`

```text
irb(main):019> :active == "active"
=> false
irb(main):020> [:active, :reserved].include?("active")
=> false
```

Foi o relatório da Lívia. A lista era de símbolos. A coluna devolvia
texto. `include?` compara cada item com `==`, e `:active == "active"` é
falso. Nenhum contrato entrou.

Não há erro, e isso é o que torna o defeito caro: o programa roda, devolve
um resultado plausível — "tudo livre" —, e só quem conhece o pátio percebe
que é impossível.

A correção é escolher **um** tipo na fronteira e converter ali:

```text
irb(main):021> "active".to_sym
=> :active
irb(main):022> :active.to_s
=> "active"
```

No relatório, os status vêm da tabela como texto. A lista passa a ser de
texto também:

```ruby
OCUPAM = ["active", "reserved"]
```

:::pitfall
Mais adiante, o Rails vai mostrar que a coluna `status` pode ser declarada
como uma lista fechada de valores, e aí os dois lados passam a combinar.
Até lá, a regra da casa: **status que vem da tabela é texto**. Símbolo é
para chave e opção. Se um mesmo valor aparecer ora como `:active`, ora como
`"active"` no mesmo arquivo, alguém vai comparar os dois.
:::

## O ponto de milhar

O capítulo @cap:objetos-e-tipos deixou "R$ 1819,80" sem o ponto. Com
métodos de texto, ele sai:

```ruby title="reais.rb" numbered
# frozen_string_literal: true

def reais(centavos)
  inteiro = (centavos / 100).to_s
  com_ponto = inteiro.reverse.scan(/\d{1,3}/).join(".").reverse
  format("R$ %s,%02d", com_ponto, centavos % 100)
end

puts reais(181_980)
puts reais(360_000_000)
```

```text
$ ruby reais.rb
R$ 1.819,80
R$ 3.600.000,00
```

`reverse` inverte o texto. `scan(/\d{1,3}/)` corta em pedaços de até três
dígitos, e `join(".")` junta com ponto. O segundo `reverse` desvira. O
`/\d{1,3}/` é uma expressão regular — um padrão de texto —; `\d` é "um
dígito", `{1,3}` é "de um a três". Os R$ 3,6 milhões do contrato da Serra
Azul saem com os dois pontos no lugar.

:::summary
- Métodos de `String` sem `!` devolvem texto novo; com `!`, alteram o
  próprio objeto. `<<` também altera.
- `b = a` não copia: os dois nomes apontam para o mesmo objeto.
- No Ruby 3.4 o literal avisa que vai congelar.
  `# frozen_string_literal: true` congela desde já; `+"..."` dá uma cópia
  alterável.
- Símbolo é nome único e imutável, para chave e opção. Texto é dado vindo
  de fora.
- `:active == "active"` é falso. Converta na fronteira com `to_sym` ou
  `to_s`, e escolha um tipo só.
:::

:::exercise level=1
Diga o valor de `a` no fim, sem rodar:

```ruby
a = "serra azul"
b = a
b = b.upcase
```

E se a última linha fosse `b.upcase!`?

:::answer
Com `b = b.upcase`, `a` continua `"serra azul"`. O `upcase` criou um texto
novo, e `b` passou a apontar para ele.

Com `b.upcase!`, `a` vale `"SERRA AZUL"`. O `!` alterou o objeto que os dois
nomes compartilhavam.
:::

:::exercise level=2
A planilha traz o patrimônio de vários jeitos: `" pt-118"`, `"PT118"`,
`"Pt-118 "`. Escreva `normalizar(patrimonio)` que devolve sempre
`"PT-118"`.

:::answer
```ruby
def normalizar(patrimonio)
  limpo = patrimonio.strip.upcase.delete("-")
  "#{limpo[0, 2]}-#{limpo[2..]}"
end
```

`strip` tira as pontas, `upcase` padroniza, `delete("-")` tira o hífen que
às vezes vem e às vezes não. `limpo[0, 2]` pega dois caracteres a partir do
início; `limpo[2..]` pega do terceiro até o fim. O hífen volta no lugar.

Nenhum `!`: o texto que veio da planilha não é alterado. Quem chama recebe
um texto novo.
:::

:::exercise level=3
A Lívia vai receber, da API da Serra Azul, status como `"ACTIVE"`, e da
tabela como `"active"`. O código novo tem um `case` com `when :active`.
Diga onde converter, para qual tipo, e por quê.

:::answer
Na fronteira de cada entrada, para o tipo que a tabela usa: texto em
minúsculas. A resposta da Serra Azul passa por `status.downcase` no ponto
em que entra no programa; a tabela já vem assim.

E o `case` troca `when :active` por `when "active"`. Com o símbolo, nenhum
dos dois lados combina — nem a API, nem a tabela —, e o `case` cai no
`else` para todo contrato, sem erro.

Converter para símbolo também funcionaria, se fosse feito em todas as
entradas. Mas a tabela é a origem que mais aparece, e escolher o tipo dela
é o que exige menos conversões espalhadas.
:::
