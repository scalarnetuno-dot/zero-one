---
title: "Objetos e tipos"
number: 4
slug: objetos-e-tipos
part: p2
kicker: "Três diárias de R$ 480 somadas pela planilha davam R$ 480.480.480. O boleto não saiu, e ninguém achou estranho a tempo."
goal: >-
  Perguntar a qualquer valor que tipo ele é, separar número de texto antes
  de somar, e guardar dinheiro da locação em centavos, inteiros, em vez de
  confiar em ponto flutuante.
---

:::story Quatrocentos e oitenta mil
A Marta encaminhou o print na terça, 10 de março, com uma linha só: "isso
é nosso?".

Era um rascunho de boleto da Serra Azul, gerado por um script que o Sérgio
tinha escrito em 2019 para juntar a planilha com o sistema. Três diárias de
betoneira. Total: `R$ 480480480`.

— Não saiu — disse o Sérgio. — O banco recusou. Valor acima do limite.

— E se não recusasse? — perguntou a Lívia.

O Sérgio pensou.

— Aí a Serra Azul ligava.

O Caio abriu o script e apontou uma linha.

```ruby
total = diaria + diaria + diaria
```

— A diária veio da planilha — disse ele. — Da planilha vem texto.
:::

## Tudo é objeto

O capítulo @cap:fevereiro-de-1993 disse que no Ruby tudo é objeto, inclusive
o número e o `nil`. No `irb` dá para ver. Todo objeto responde ao método
`class`, que diz de que classe ele é:

```text
$ irb
irb(main):001> 480.class
=> Integer
irb(main):002> "480".class
=> String
irb(main):003> 480.0.class
=> Float
irb(main):004> nil.class
=> NilClass
irb(main):005> true.class
=> TrueClass
```

`480` e `"480"` parecem a mesma coisa para quem lê. Para o Ruby são objetos
de classes diferentes, com métodos diferentes. O inteiro sabe dizer se é
par. O texto sabe dizer quantos caracteres tem:

```text
irb(main):006> 480.even?
=> true
irb(main):007> "480".length
=> 3
irb(main):008> "480".even?
(irb):8:in '<main>': undefined method 'even?' for an instance
of String (NoMethodError)
```

`NoMethodError` é a mensagem enviada a um objeto que não tem aquele
método. O Ruby não converte o texto em número para tentar ajudar. Diz a
classe que recebeu a mensagem — `String` — e o nome do método que faltou.

:::term Classe
O tipo de um objeto. Diz quais métodos ele tem. `480.class` responde
`Integer`; `"480".class` responde `String`.

No Ruby o tipo mora no valor, não no nome. A variável `diaria` pode apontar
para um inteiro numa linha e para um texto na seguinte. Quem sabe o tipo é
o objeto para o qual ela aponta agora.
:::

## Texto somado com texto

O `+` também é um método. Cada classe decide o que ele faz. No inteiro,
soma. No texto, junta:

```text
irb(main):009> 480 + 480
=> 960
irb(main):010> "480" + "480"
=> "480480"
```

Foi o que o script de 2019 fez. A coluna da planilha chegava como texto,
três textos foram juntados, e o resultado foi `"480480480"` — que o resto
do script tratou como valor.

Somar texto com número não junta nem soma. Quebra:

```text
irb(main):011> "480" + 480
(irb):11:in 'String#+': no implicit conversion of Integer
into String (TypeError)
```

`TypeError` é o objeto certo recebendo um argumento do tipo errado. O `+`
do texto aceita outro texto. Recebeu um inteiro e parou.

A conversão existe, mas é pedida em voz alta:

```text
irb(main):012> "480".to_i + 480
=> 960
irb(main):013> 480.to_s + "480"
=> "480480"
```

`to_i` pede ao texto o inteiro que ele representa. `to_s` pede ao inteiro
o texto. A regra é converter **na entrada**: o valor que vem da planilha
vira número uma vez, no ponto em que entra, e não em cada soma.

:::pitfall
`to_i` não reclama. Texto que não é número vira zero, e o que vier depois
de um número é descartado:

```text
irb(main):014> "R$ 480".to_i
=> 0
irb(main):015> "480,50".to_i
=> 480
```

A diária com cifrão vira zero. A diária com centavos perde os centavos. Os
dois sem erro nenhum. Quando o texto precisa ser um número e não é,
`Integer("R$ 480")` levanta `ArgumentError` em vez de devolver zero — e é
isso que se quer na entrada de dinheiro.
:::

## Dinheiro não é `Float`

A diária da betoneira é R$ 480. A do gerador pequeno é R$ 189,90. Número
com vírgula, no Ruby, se escreve com ponto e é um `Float`:

```text
irb(main):016> 189.90.class
=> Float
```

`Float` é um número em ponto flutuante: o computador guarda uma
aproximação binária. Para medir a altura de uma plataforma, basta. Para
somar dinheiro, não:

```text
irb(main):017> 1.10 + 2.20
=> 3.3000000000000003
irb(main):018> 1.10 + 2.20 == 3.30
=> false
```

R$ 1,10 de taxa de combustível mais R$ 2,20 de taxa de limpeza não é, para
o computador, R$ 3,30. A diferença é pequena, e é suficiente para uma
comparação dar falso e um boleto não fechar com o contrato.

A Nortea resolve do jeito que banco resolve: **dinheiro em centavos,
inteiro**.

```text
irb(main):019> 110 + 220
=> 330
irb(main):020> 110 + 220 == 330
=> true
```

A diária de R$ 480 é `48_000`. A de R$ 189,90 é `18_990`. O sublinhado
dentro do número é só para ler: o Ruby ignora.

```ruby title="diarias.rb" numbered
diaria_betoneira = 48_000
diaria_gerador = 18_990

total = diaria_betoneira * 3 + diaria_gerador * 2
puts total
```

```text
$ ruby diarias.rb
181980
```

Três diárias de betoneira e duas de gerador: R$ 1.819,80, guardado como
`181980`. Nenhuma aproximação no caminho.

:::key
Dinheiro entra como centavos inteiros e só vira "R$ 1.819,80" na hora de
mostrar. Entre a entrada e a tela, toda conta é entre inteiros.
:::

## Divisão entre inteiros

Inteiro dividido por inteiro dá inteiro, e o resto é descartado:

```text
irb(main):021> 48_000 / 3
=> 16000
irb(main):022> 100 / 3
=> 33
irb(main):023> 100 % 3
=> 1
```

`/` entre inteiros corta a parte decimal. `%` devolve o resto. Numa
diária proporcional — uma plataforma que ficou oito horas de um dia de
vinte e quatro —, o centavo que sobra precisa de dono. A Nortea arredonda
para cima, a favor da locadora, e isso está escrito no contrato:

```ruby title="proporcional.rb" numbered
diaria = 48_000
horas = 8

valor = (diaria * horas + 23) / 24
puts valor
```

```text
$ ruby proporcional.rb
16000
```

O `+ 23` antes de dividir por 24 faz a divisão inteira arredondar para
cima. Com oito horas o resultado é exato. Com sete, seriam `14_000`
exatos. Com cinco, `10_000`. A conta nunca passa por `Float`.

## Mostrar em reais

Para a tela, o inteiro vira texto com `format`:

```ruby title="diarias.rb" numbered
total = 181_980

reais = total / 100
centavos = total % 100
puts format("R$ %d,%02d", reais, centavos)
```

```text
$ ruby diarias.rb
R$ 1819,80
```

`%d` é um inteiro. `%02d` é um inteiro com duas casas, completando com
zero: cinco centavos saem `05`, não `5`. O ponto de milhar fica para
quando o capítulo de strings chegar. A conta já está certa.

:::summary
- Tudo é objeto. `class` diz o tipo: `Integer`, `String`, `Float`,
  `NilClass`.
- O `+` é um método. No inteiro soma, no texto junta. Misturar os dois dá
  `TypeError`.
- Converta na entrada. `to_i` devolve zero para texto inválido;
  `Integer("...")` levanta erro.
- `Float` é aproximação. Dinheiro é centavo inteiro: R$ 480 é `48_000`.
- `/` entre inteiros corta o decimal; `%` é o resto. `format` monta o texto
  em reais só na saída.
:::

:::exercise level=1
Diga a classe e o resultado de cada linha, sem rodar. Depois confira no
`irb`.

```ruby
"48000".class
48_000 / 100
"480" + "20"
480 + "20".to_i
```

:::answer
- `"48000".class` é `String`. As aspas fazem dele texto.
- `48_000 / 100` é `480`, um `Integer`.
- `"480" + "20"` é `"48020"`, um `String`: dois textos juntados.
- `480 + "20".to_i` é `500`, um `Integer`: o texto virou número antes da
  soma.
:::

:::exercise level=2
A planilha traz a diária da plataforma PT-118 como `"R$ 320,00"`. Escreva
o trecho que transforma esse texto em centavos inteiros — `32000` — e
explique por que `"R$ 320,00".to_i` não serve.

:::answer
```ruby
texto = "R$ 320,00"
limpo = texto.delete("R$ .").delete(",")
centavos = Integer(limpo)
```

`delete` remove todos os caracteres listados. Sobram `"32000"`, e o
`Integer` converte. Se a planilha trouxer algo que não seja número, o
`Integer` levanta `ArgumentError` e o problema aparece na entrada.

`"R$ 320,00".to_i` devolve `0`: o texto começa com `R`, e o `to_i` para no
primeiro caractere que não é dígito. Diária zero, sem aviso.
:::

:::exercise level=3
Um contrato cobra 17 diárias de R$ 189,90 e uma taxa única de R$ 45,50. O
script de 2019 fazia a conta com `Float`. Escreva a versão em centavos,
mostre o total em reais com `format`, e diga em que linha o `Float` poderia
ter produzido um valor que não fecha.

:::answer
```ruby
diaria = 18_990
taxa = 4_550

total = diaria * 17 + taxa
puts format("R$ %d,%02d", total / 100, total % 100)
```

```text
R$ 3273,80
```

Com `Float`, `189.90 * 17 + 45.50` passa por dois números que o computador
não guarda exatos. O resultado pode sair com uma cauda como `...00000004`,
e a comparação com o valor do contrato dá falso. Em centavos, as três
contas são entre inteiros e o total é exato.
:::
