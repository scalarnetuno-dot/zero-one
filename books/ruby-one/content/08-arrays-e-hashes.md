---
title: "Arrays e hashes"
number: 8
slug: arrays-e-hashes
part: p2
kicker: "A planilha chama de Contrato o que o banco chama de code. O mesmo contrato, dois hashes, nenhuma chave em comum."
goal: >-
  Guardar a lista da manhã num array, guardar um contrato num hash, ler uma
  chave que pode não existir sem receber nil em silêncio, e levar o
  contrato da planilha e o do banco para a mesma forma.
---

:::story Contrato e code
Na segunda, 16 de março, a Marta pediu a primeira coisa concreta:

— Quero saber, de manhã, quais linhas da planilha não batem com o
sistema. Só isso. Uma lista.

O Sérgio mandou o arquivo que ele usava para exportar a planilha em
formato que o Ruby lia. A Lívia abriu uma linha:

```text
{"Patrimônio" => "PT-118", "Contrato" => "CT-2041",
 "Canteiro" => "Serra Azul - Contagem", "Saída" => "03/03/2026"}
```

E uma linha do banco, no console de homologação:

```text
{:code=>"CT-2041", :equipment=>"PT-118", :site=>"contagem",
 :start_date=>Tue, 03 Mar 2026}
```

— São o mesmo contrato — disse ela.

— Nenhuma chave igual — disse o Caio. — Nem o canteiro está escrito do
mesmo jeito.

A Marta olhou as duas telas.

— E qual das duas está certa?

— As duas — disse o Caio. — Cada uma do jeito dela.
:::

## Array: a lista da manhã

Um array é uma lista em ordem. Se escreve entre colchetes:

```ruby
manha = ["PT-118", "PT-121", "BT-044", "GR-310"]
```

Cada item tem uma posição, a partir de zero:

```text
irb(main):001> manha = ["PT-118", "PT-121", "BT-044", "GR-310"]
irb(main):002> manha[0]
=> "PT-118"
irb(main):003> manha[-1]
=> "GR-310"
irb(main):004> manha.size
=> 4
irb(main):005> manha.include?("BT-044")
=> true
irb(main):006> manha[10]
=> nil
```

`[-1]` é o último; `[-2]`, o penúltimo. Uma posição que não existe devolve
`nil`, sem erro — é o primeiro lugar em que a ausência entra calada.

Para acrescentar ao fim, `<<`. Para tirar, `delete`:

```ruby
manha << "CP-007"
manha.delete("PT-121")
```

Os dois alteram o próprio array, como o `<<` da string.

## Hash: o contrato

Um hash guarda pares de chave e valor. A chave é o nome do campo; o valor,
o dado:

```ruby
contrato = {
  code: "CT-2041",
  equipment: "PT-118",
  site: "contagem",
}
```

`code:` com os dois-pontos depois é uma chave **símbolo** — a forma que o
capítulo @cap:strings-e-simbolos recomendou para nomes escolhidos no
código. A vírgula depois do último par é permitida e evita ruído quando
alguém acrescenta uma linha.

```text
irb(main):007> contrato[:code]
=> "CT-2041"
irb(main):008> contrato[:site] = "betim"
=> "betim"
irb(main):009> contrato
=> {code: "CT-2041", equipment: "PT-118", site: "betim"}
```

A linha da planilha também é um hash, mas com chaves **texto**, porque
vieram do cabeçalho de uma coluna:

```ruby
linha = { "Patrimônio" => "PT-118", "Contrato" => "CT-2041" }
```

A seta `=>` é a forma geral: aceita qualquer objeto como chave. A forma
`code:` é o atalho para chave símbolo. As duas formas convivem, e o mesmo
hash pode ter chaves dos dois tipos — o que é quase sempre um erro.

:::pitfall
`contrato[:code]` e `contrato["code"]` são chaves diferentes. Um hash com
chaves símbolo, lido com texto, devolve `nil`:

```text
irb(main):010> contrato["code"]
=> nil
```

É o `:active` e o `"active"` do capítulo anterior, agora dentro de um
hash. Nenhum erro, só um `nil` que vai aparecer três métodos depois.
:::

## `fetch`: a chave que tem de existir

O colchete devolve `nil` para chave ausente. Quando a chave é obrigatória,
`fetch` diz que ela faltou:

```text
irb(main):011> linha.fetch("Contrato")
=> "CT-2041"
irb(main):012> linha.fetch("Canteiro")
(irb):12:in 'Hash#fetch': key not found: "Canteiro" (KeyError)
```

`KeyError`, com o nome da chave. Na linha da planilha em que alguém apagou
a coluna do canteiro, o `[]` seguiria com `nil` e o `fetch` para ali, onde
o problema está.

`fetch` aceita um valor padrão, para chave que pode faltar de propósito:

```ruby
observacao = linha.fetch("Obs", "")
```

:::key
`[]` para chave opcional. `fetch` para chave sem a qual o dado não faz
sentido. Na leitura de dado externo — planilha, API —, a maioria das
chaves é obrigatória.
:::

## Aninhado, e o `dig`

O contrato do banco traz o equipamento como outro hash:

```ruby
contrato = {
  code: "CT-2041",
  equipment: { patrimony: "PT-118", kind: "plataforma" },
}

contrato[:equipment][:patrimony]   # => "PT-118"
```

Se `equipment` não existir, `contrato[:equipment]` é `nil`, e
`nil[:patrimony]` quebra com `NoMethodError`. O `dig` desce e para no
primeiro `nil`:

```ruby
contrato.dig(:equipment, :patrimony)   # => "PT-118" ou nil
```

Serve para ler dado aninhado que pode estar incompleto. Não serve para
esconder um dado obrigatório que sumiu — para isso, `fetch` em cada nível.

## Dois contratos, uma forma

A lista da Marta compara a planilha com o banco. Antes de comparar, os dois
precisam falar a mesma língua. A casa decide: **chaves símbolo, nomes do
banco, valores normalizados**.

```ruby title="normalizar.rb" numbered
# frozen_string_literal: true

require "date"

CANTEIROS = {
  "Serra Azul - Contagem" => "contagem",
  "Serra Azul - Betim" => "betim",
}

def da_planilha(linha)
  {
    code: linha.fetch("Contrato").strip,
    equipment: linha.fetch("Patrimônio").strip.upcase,
    site: CANTEIROS.fetch(linha.fetch("Canteiro")),
    start_date: Date.strptime(linha.fetch("Saída"), "%d/%m/%Y"),
  }
end

def do_banco(registro)
  {
    code: registro.fetch(:code),
    equipment: registro.fetch(:equipment),
    site: registro.fetch(:site),
    start_date: registro.fetch(:start_date),
  }
end

planilha = {
  "Patrimônio" => "PT-118", "Contrato" => "CT-2041",
  "Canteiro" => "Serra Azul - Contagem", "Saída" => "03/03/2026",
}
banco = {
  code: "CT-2041", equipment: "PT-118", site: "contagem",
  start_date: Date.new(2026, 3, 3), responsible: "Helena",
}

puts da_planilha(planilha) == do_banco(banco)
```

```text
$ ruby normalizar.rb
true
```

`CANTEIROS` começa com maiúscula: é uma **constante**, um nome que o
arquivo não pretende reatribuir. O Ruby avisa se alguém reatribuir.

`Date.strptime` lê a data no formato que a planilha escreve: `%d/%m/%Y` é
dia, mês e ano com quatro dígitos. Sem ela, `"03/03/2026"` é só um texto,
e texto não se compara com data.

`do_banco` descarta o `responsible`, porque a planilha não tem essa coluna.
Dois hashes são iguais com `==` quando têm as mesmas chaves com os mesmos
valores. O que sobra de um lado faz a comparação dar falso — e é por isso
que os dois lados passam pela mesma forma, com o mesmo conjunto de chaves.

:::pitfall
O canteiro da planilha que não estiver em `CANTEIROS` levanta `KeyError`
no `fetch`. É de propósito. A alternativa, `CANTEIROS[...]`, devolveria
`nil`, e o contrato de um canteiro novo apareceria como divergente todo
dia, sem ninguém saber por quê. O erro diz o nome do canteiro que falta na
tabela de tradução.
:::

:::summary
- Array é lista em ordem, a partir de zero. `[-1]` é o último; posição
  inexistente devolve `nil`.
- Hash guarda chave e valor. `code:` é chave símbolo; `"Contrato" =>` é
  chave texto. Símbolo e texto são chaves diferentes.
- `[]` devolve `nil` para chave ausente; `fetch` levanta `KeyError` com o
  nome da chave.
- `dig` desce em hash aninhado e para no primeiro `nil`.
- Antes de comparar dado de duas origens, leve os dois para a mesma forma:
  mesmas chaves, mesmos tipos, mesmos valores.
:::

:::exercise level=1
Diga o que cada linha devolve:

```ruby
c = { code: "CT-2041", site: "contagem" }
c[:code]
c["code"]
c.fetch(:site)
c.fetch(:equipment, "sem equipamento")
```

:::answer
`"CT-2041"`, `nil`, `"contagem"` e `"sem equipamento"`.

A segunda devolve `nil` porque a chave é o símbolo `:code`, e foi lida com
o texto `"code"`. A última não quebra porque `fetch` recebeu um valor
padrão.
:::

:::exercise level=2
A planilha de amanhã traz uma linha com o canteiro `"Serra Azul -
Nova Lima"`. O que o `normalizar.rb` faz com ela, e o que você muda para
que ele passe a aceitar?

:::answer
O `CANTEIROS.fetch` levanta `KeyError: key not found: "Serra Azul - Nova
Lima"`. O programa para nessa linha.

A mudança é acrescentar o par na tabela de tradução, com o nome que o
banco usa:

```ruby
"Serra Azul - Nova Lima" => "nova_lima",
```

E conferir com quem cadastra o canteiro no sistema qual é esse nome. Não
se inventa um valor para o banco a partir da planilha.
:::

:::exercise level=3
A Marta quer a lista de divergências. Escreva `diverge?(linha, registro)`
que devolve verdadeiro quando o contrato da planilha e o do banco não
batem, e diga por que o `responsible` do banco não pode entrar na
comparação.

:::answer
```ruby
def diverge?(linha, registro)
  da_planilha(linha) != do_banco(registro)
end
```

`!=` é o contrário de `==`. As duas funções já levam os dois lados para a
mesma forma.

O `responsible` não entra porque a planilha não tem essa coluna. Se o hash
do banco o carregasse, **todo** contrato seria divergente: um lado teria
uma chave que o outro não tem. A comparação só vale sobre o que as duas
origens sabem dizer.
:::
