---
title: "Operadores e expressões"
number: 4
part: p1
kicker: "O sinal de igual não significa igual, e o sinal de igual duplo engana com texto."
goal: >-
  Prever o resultado de qualquer expressão aritmética, lógica ou de
  comparação, e explicar por que `==` não serve para comparar texto em Java.
---

Operador é um símbolo que pega valores e devolve outro. Você já usou três no
capítulo passado sem pensar. Este capítulo é curto e denso de propósito:
quase todo defeito de lógica que você vai caçar mais tarde nasce de um
operador mal entendido.

## Aritméticos

```java title="Cinco símbolos" numbered
int soma = 7 + 2;      // 9
int sub = 7 - 2;       // 5
int mult = 7 * 2;      // 14
int div = 7 / 2;       // 3  ← inteiro, o resto some
int resto = 7 % 2;     // 1  ← o resto que sumiu
```

O `%` é o **módulo**: o resto da divisão. Parece inútil até você precisar
saber se um número é par (`n % 2 == 0`), paginar uma lista ou distribuir
itens em colunas — e então ele aparece toda semana.

:::trivia
`%` em Java pode devolver negativo: `-7 % 2` dá `-1`, não `1`. A linguagem
segue a regra do C, onde o sinal do resto acompanha o dividendo. Python
escolheu o contrário (`-7 % 2` dá `1`). Duas linguagens, duas matemáticas
defensáveis — e um bug garantido para quem troca de uma para a outra sem
reparar.
:::

## Atribuição e a forma curta

O `=` não pergunta se dois valores são iguais: ele **manda** o da direita
para o nome da esquerda. Ler `total = total + preco` como uma equação é o
caminho mais rápido para a confusão; leia como "o novo total passa a ser o
total anterior mais o preço".

```java
total = total + preco;
total += preco;          // idêntico, e mais curto
```

Existem `+=`, `-=`, `*=`, `/=` e `%=`. Todos fazem o mesmo: operam e
atribuem.

## Incremento: o `++` e a posição dele

```java title="A posição muda o valor da expressão" numbered
int i = 5;
System.out.println(i++);   // imprime 5, depois i vale 6
System.out.println(i);     // 6

int j = 5;
System.out.println(++j);   // imprime 6
```

`i++` devolve o valor **antes** de somar; `++i` soma e **depois** devolve. Em
um laço sozinho na linha (`i++;`) não faz diferença nenhuma. Dentro de uma
expressão maior, faz — e é por isso que código profissional evita misturar
incremento com outra coisa na mesma linha.

## Comparação

| Operador | Pergunta |
|---|---|
| `==` | são o mesmo? |
| `!=` | são diferentes? |
| `>` `<` | maior, menor |
| `>=` `<=` | maior ou igual, menor ou igual |

Tabela: Os seis comparadores. Todos devolvem `boolean` — nunca número.

E aqui mora a armadilha mais famosa da linguagem.

## `==` compara identidade, `.equals()` compara conteúdo

```java title="Isto pode não funcionar" numbered
String senha = new String("abc");

if (senha == "abc") {
    System.out.println("Liberado");
}
```

Não imprime nada. O `==` pergunta se os dois nomes apontam para **o mesmo
objeto na memória** — e não apontam: `new String` criou um objeto novo. A
pergunta certa é sobre conteúdo:

```java title="Isto funciona sempre"
if (senha.equals("abc")) {
    System.out.println("Liberado");
}
```

:::diagram type="cells" caption="Duas variáveis, dois objetos, o mesmo conteúdo: `==` diz não, `equals` diz sim."
items: ["senha →", "objeto A: \"abc\"", "literal →", "objeto B: \"abc\""]
orientation: horizontal
:::

:::pitfall
Às vezes `==` funciona com `String` — e isso é pior do que se nunca
funcionasse. O compilador guarda literais iguais em um mesmo lugar (o *string
pool*), então `String a = "abc"; String b = "abc";` faz `a == b` dar `true`.
O teste passa no seu computador e falha quando o texto vem do teclado, de um
arquivo ou de uma requisição HTTP. **Para texto, use sempre `equals`.**
:::

:::tip Inverta a comparação com literais
`"abc".equals(senha)` faz o mesmo teste e não estoura se `senha` for
`null`. É um hábito de duas teclas que apaga uma classe inteira de erro —
você vai reencontrá-lo no capítulo 13, quando o `NullPointerException`
virar assunto.
:::

Para primitivos (`int`, `double`, `boolean`, `char`), `==` é a ferramenta
certa: não há objeto nenhum, só o valor. A regra prática é curta: **primitivo
usa `==`, objeto usa `equals`.**

:::story O cupom que só funcionava na máquina do Carlos
O cupom era simples: digite PROMO10 e ganhe dez por cento.

Funcionou no teste do Carlos. Funcionou no teste do Carlos de novo.
Funcionou no teste do Carlos pela terceira vez, o que deveria ter servido de
alerta.

No dia seguinte, Seu Antônio ligou:

— Moço, esse cupom de vocês não funciona.

— O senhor digitou PROMO10, tudo maiúsculo?

— Digitei igualzinho está no papel.

Carlos passou quarenta minutos tentando reproduzir. Digitava o cupom,
funcionava. Marina se aproximou, leu a linha `if (cupom == "PROMO10")` e fez
uma única pergunta:

— No seu teste, de onde vem esse texto?

— Está escrito no código.

— E no caso do cliente?

— Vem do... teclado.

Marina não disse mais nada. Não precisava. Carlos já estava trocando o `==`
por `.equals`, com aquela sensação específica de estar consertando um erro
que o compilador tinha deixado passar de propósito.
:::

:::art caption="O teste passava porque o texto e o literal eram, por acidente, o mesmo objeto."
src="o-teste-passava-porque-o-texto-e-o-literal-eram-por-acidente-o-mesmo-objeto.png"
Charge editorial minimalista: dois balões de texto idênticos com a palavra
"PROMO10", ligados por uma seta com um grande sinal de igual duplo riscado
em vermelho. De um lado, um desenvolvedor jovem de expressão confusa diante
do monitor; do outro, um senhor de óculos segurando um papel com o cupom
escrito à mão, digitando em um celular. Entre os dois, uma lupa gigante
mostrando que as duas palavras, apesar de idênticas, estão em caixas
separadas. Composição limpa, poucos elementos, fundo branco, humor sutil,
estética editorial de tecnologia.
:::

## Lógicos

```java title="Três operadores e uma otimização importante" numbered
boolean temIngresso = true;
int idade = 16;

if (temIngresso && idade >= 18) { /* exige os dois */ }
if (temIngresso || idade >= 18) { /* basta um */ }
if (!temIngresso)               { /* inverte */ }
```

`&&` e `||` têm **curto-circuito**: a avaliação para assim que o resultado
está decidido. Se o lado esquerdo de um `&&` é falso, o direito nem é
executado. Isso não é detalhe de desempenho, é uma ferramenta:

```java
if (nome != null && nome.equals("Ana")) { ... }
```

Se `nome` for `null`, o segundo teste nunca roda e o programa não estoura. Na
ordem inversa, estoura sempre.

:::anatomy title="Como o compilador lê uma expressão composta"
lang: java
code: |
  boolean liberado = idade >= 18
          && (temIngresso || convidado)
          && !bloqueado;
notes:
  - { line: 1, text: "Primeiro os comparadores: `>=` roda antes de `&&`." }
  - { line: 2, text: "Parênteses primeiro: o `||` interno é resolvido antes do `&&` externo." }
  - { line: 3, text: "`!` tem precedência alta: inverte só `bloqueado`, não a expressão toda." }
:::

A tabela de precedência completa tem quinze níveis e ninguém a decora.
O conselho profissional é outro: **use parênteses** quando a expressão tem
mais de dois operadores. Eles não custam nada em desempenho e economizam
uma hora de depuração.

## O ternário

```java
String status = idade >= 18 ? "adulto" : "menor";
```

Leia como uma pergunta: *condição ? valor se sim : valor se não*. Serve para
escolher **um valor**. Não serve para executar dois blocos de código — para
isso existe o `if`, que é o capítulo seguinte.

:::summary
- `/` entre inteiros descarta o resto; `%` devolve o resto.
- `=` atribui, `==` compara. `i++` devolve antes de somar.
- Primitivo compara com `==`; objeto compara com `equals`.
- `&&` e `||` param assim que o resultado está decidido — use isso contra
  `null`.
- Parênteses são documentação executável.
:::

:::checkpoint
Você prevê o resultado de expressões aritméticas e lógicas, sabe por que
`==` falha com texto e usa curto-circuito para proteger uma chamada.
:::

:::milestone
Nada de novo no projeto, e é intencional: este capítulo é uma dívida que
está sendo paga adiantada. As regras daqui aparecem em todo `if` do resto do
livro.
:::

:::exercise level=1
Escreva um programa que receba um número como argumento e imprima `"par"` ou
`"ímpar"` usando `%` e o operador ternário.

:::answer
```java
int n = Integer.parseInt(args[0]);
System.out.println(n % 2 == 0 ? "par" : "ímpar");
```
:::

:::exercise level=2
Sem rodar, diga o que este trecho imprime. Depois rode e confira.

```java
int i = 3;
int total = i++ + ++i;
System.out.println(total + " " + i);
```

:::answer
Imprime `8 5`. O primeiro `i++` usa `3` e deixa `i` em `4`; o `++i` leva `i`
a `5` e usa `5`. Logo `3 + 5 = 8`. Se você errou, não se sinta mal: é
exatamente por isso que esse tipo de linha não passa em revisão de código.
:::

:::exercise level=2
Escreva a condição que libera a entrada se a pessoa tem ingresso **e** (é
maior de idade **ou** está acompanhada). Depois reescreva sem nenhum
parêntese e explique por que o significado muda.

:::answer
`temIngresso && (idade >= 18 || acompanhada)`. Sem parênteses,
`temIngresso && idade >= 18 || acompanhada` é lido como
`(temIngresso && idade >= 18) || acompanhada` — porque `&&` tem precedência
sobre `||`. Nessa versão, quem está acompanhada entra mesmo sem ingresso.
:::
