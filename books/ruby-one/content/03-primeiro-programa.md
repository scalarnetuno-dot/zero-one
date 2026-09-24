---
title: "O primeiro programa"
number: 3
slug: primeiro-programa
part: p1
kicker: "Dois Rubys na mesma manhã, e só um deles abre o pátio às 6h."
goal: >-
  Escrever, salvar e rodar um programa Ruby; interpolar um nome dentro do
  texto; ler o nil que o irb mostra; e reconhecer as três falhas da
  primeira hora.
---

:::story Não mexe no três ponto três
A Lívia rodou o comando na pasta dela.

```text
$ ruby -v
ruby 3.4.0 (2024-12-25) [x64-mingw-ucrt]
```

No servidor, a mesma pergunta respondia 3.3.

— Aqui está rodando — disse ela.

O Sérgio não levantou os olhos do `Gemfile`.

— O pátio abre com o três ponto três. Não mexe nele. O seu fica do lado, e
antes de rodar qualquer coisa você descobre qual dos dois o terminal está
chamando.
:::

O programa desta página roda no seu Ruby, o 3.4. O sistema de produção
continua no 3.3, e ninguém desta página vai publicá-lo hoje.

O menor programa útil tem duas linhas. Salve isto num arquivo chamado
`contrato.rb`, dentro da pasta `patio`:

```ruby title="contrato.rb" numbered
codigo = "CT-2041"
puts "Contrato #{codigo}"
```

Abra o terminal nessa pasta e rode:

```text
$ ruby contrato.rb
Contrato CT-2041
```

`codigo` começa com minúscula. No Ruby, isso é uma variável local: um nome
deste arquivo, criado no `=` e visível daqui até o fim do arquivo. O valor
é o texto entre aspas. `puts` escreve o valor e pula a linha.

As aspas desta linha são duplas. Dentro delas, `#{codigo}` não é texto. É
uma interpolação: o Ruby lê o nome e coloca o valor no lugar. Com aspas
simples, `'Contrato #{codigo}'`, as chaves sairiam escritas.

:::anatomy title="As partes da interpolação"
lang: ruby
code: |
  puts "Contrato #{codigo}"
notes:
  - { line: 1, text: "Aspas duplas ligam a interpolação. Aspas simples tratam `#{codigo}` como texto." }
  - { line: 1, text: "`#{codigo}` troca o nome pelo valor. Dentro das chaves vale uma expressão." }
  - { line: 1, text: "O que está fora das chaves, inclusive o espaço, é texto fixo." }
:::

O Ruby leu o arquivo e executou. Você não dispara um segundo comando para
compilar. Quem lê o texto, no 3.4, é o Prism. Quem executa é o YARV, o
executor que entrou no Ruby 1.9. Os dois ficam dentro do comando `ruby`.

:::diagram type="flowchart" caption="Do arquivo à linha no terminal. Você dispara um comando. A leitura e a execução ficam dentro dele."
nodes:
  - { id: src, type: io, text: "contrato.rb" }
  - { id: ruby, type: process, text: "ruby contrato.rb" }
  - { id: y, type: process, text: "Prism lê, YARV executa" }
  - { id: out, type: io, text: "Contrato CT-2041" }
edges:
  - { from: src, to: ruby }
  - { from: ruby, to: y }
  - { from: y, to: out }
:::

## O irb

O `irb` é o Ruby esperando uma linha, sem arquivo. Serve para perguntar.
Não serve para ser o programa: o que você digita some quando a sessão
fecha.

```text
$ irb
irb(main):001> puts "Contrato CT-2041"
Contrato CT-2041
=> nil
```

A primeira linha depois do comando é o que o `puts` escreveu. A linha
`=> nil` é outra coisa: o valor que o `puts` devolveu. Escrever na tela é
efeito do método. O valor devolvido é `nil`.

:::term nil
O objeto que significa ausência de valor. É um objeto: tem métodos, como
qualquer outro no Ruby.

`puts` devolve `nil` porque o trabalho dele foi escrever, não calcular um
resultado para quem chamou. O `irb` mostra esse retorno depois de `=>`.
No `ruby contrato.rb`, o `nil` não aparece: o programa termina, e só o que
foi escrito com `puts` fica no terminal.
:::

Para sair do `irb`, digite `exit` e confirme.

## Trocar o valor

Uma variável local aceita outra atribuição. A primeira ligação deixa de
valer.

```ruby title="contrato.rb" numbered
codigo = "CT-2041"
codigo = "CT-2042"
puts "Contrato #{codigo}"
```

```text
$ ruby contrato.rb
Contrato CT-2042
```

O nome `codigo` aponta para um texto, depois para outro. Não há, no Ruby,
um modo de criar esse nome já proibindo a segunda linha. Se o código do
contrato não deve mudar no meio do arquivo, a disciplina é não atribuir de
novo. A linguagem não impede.

## Três falhas da primeira hora

**O arquivo não está onde você chamou.**

```text
ruby: No such file or directory -- contrato.rb (LoadError)
```

`LoadError` aqui é o Ruby procurando o arquivo e não achando. Quase sempre
o terminal está em outra pasta, ou o editor gravou `contrato.rb.txt`.
Confira o nome na pasta em que o comando rodou.

**Faltou fechar a aspa.**

```ruby title="quebra.rb" numbered
puts "Contrato CT-2041
```

```text
quebra.rb:1: syntax error, unexpected end-of-input
quebra.rb:1: unterminated string meets end of file
```

`syntax error` é texto que nem chegou a rodar. `unterminated string` diz
que a aspa abriu e não fechou. O Ruby para nesse furo.

**O nome não existe.**

```ruby title="nome.rb" numbered
puts "Contrato #{codigo}"
```

```text
nome.rb:1:in `<main>':
undefined local variable or method `codigo' (NameError)
```

O Ruby escreve o arquivo e o `NameError` na mesma linha. O nome que
faltou é `codigo`.

`NameError` é um nome usado sem ter sido criado. `codigo` não apareceu à
esquerda de um `=` neste arquivo. `` `<main>' `` é o programa solto, fora
de uma classe: o arquivo que você acabou de rodar. O Ruby chama isso de
`main`.

:::pitfall
Aspas simples não interpolam. `'Contrato #{codigo}'` imprime as chaves e o
nome, mesmo que `codigo` exista.

E o nome dentro de `#{ }` precisa existir antes. A ordem é de cima para
baixo. Uma linha não enxerga o `codigo` que só vai ser criado na linha
seguinte.
:::

## Comentário

```ruby title="contrato.rb" numbered
# número do contrato, como a Helena dita no rádio
codigo = "CT-2041"
puts "Contrato #{codigo}"
```

Tudo depois de `#`, na mesma linha, é comentário. O Ruby ignora. O
comentário não repete o que a linha já diz. Diz de onde vem o valor.

:::summary
- `ruby contrato.rb` lê o arquivo e executa. Prism e YARV ficam dentro
  desse comando.
- Aspas duplas interpolam `#{nome}`. Aspas simples não.
- Variável local começa com minúscula e aceita outra atribuição.
- Arquivo ausente, aspa aberta e nome inexistente são três falhas:
  `LoadError`, `syntax error`, `NameError`. O `irb` ainda mostra o `nil`
  que o `puts` devolve.
:::

:::exercise level=1
Na pasta `patio`, altere `contrato.rb` para a saída sair exatamente assim:

```text
Contrato CT-2041: plataforma PT-118
```

O patrimônio da plataforma deve ser outro nome, não um pedaço cravado na
frase.

:::answer
```ruby title="contrato.rb"
codigo = "CT-2041"
patrimonio = "PT-118"
puts "Contrato #{codigo}: plataforma #{patrimonio}"
```

```text
$ ruby contrato.rb
Contrato CT-2041: plataforma PT-118
```

Os dois-pontos e a palavra "plataforma" estão fora das chaves: são texto.
:::

:::exercise level=2
O arquivo abaixo vai falhar. Diga o tipo da falha e a linha, sem rodar.
Depois rode e confira.

```ruby title="contrato.rb"
codigo = "CT-2041"
puts "Contrato #{patrimonio}"
```

:::answer
`NameError` na linha 2. `codigo` existe. `patrimonio` não foi criado.

A mensagem diz `undefined local variable or method`. O Ruby não separa, na
falha, "variável" de "método": um nome desconhecido pode ser qualquer um
dos dois, e ele avisa os dois.
:::

:::exercise level=3
A Lívia precisa que `codigo` comece em `"CT-2041"` e passe a `"CT-2042"`
antes do `puts`. Mostre o arquivo que imprime `Contrato CT-2042`, e diga
o que aconteceu com o primeiro texto.

:::answer
```ruby title="contrato.rb"
codigo = "CT-2041"
codigo = "CT-2042"
puts "Contrato #{codigo}"
```

```text
$ ruby contrato.rb
Contrato CT-2042
```

A segunda atribuição faz o nome apontar para o outro texto. `"CT-2041"`
deixa de estar ligado a `codigo`. O `puts` só vê o valor que o nome tem
naquela linha.
:::
