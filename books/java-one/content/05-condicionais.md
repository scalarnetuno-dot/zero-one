---
title: "Condicionais"
number: 5
part: p1
kicker: "Escolher um caminho é assumir o outro — inclusive quando ele não está escrito."
goal: >-
  Escrever decisões com `if`, `else if` e `switch`, escolher entre eles com
  critério e reconhecer o caminho que você deixou implícito.
---

Até agora o programa fazia sempre a mesma coisa. A partir daqui ele olha para
um valor e escolhe. É a menor unidade de inteligência que um programa pode
ter, e cabe em três linhas.

## `if` exige um `boolean`

```java title="Maioridade.java" numbered
int idade = 18;

if (idade >= 18) {
    System.out.println("Pode entrar");
} else {
    System.out.println("Não pode entrar");
}
```

A condição entre parênteses precisa resultar em `true` ou `false`. Em
linguagens onde `0` vale como falso, `if (idade)` compila; em Java, não. O
compilador exige que você diga **o que** está comparando.

:::diagram type="flowchart" caption="Toda decisão tem dois caminhos, mesmo quando você escreve só um."
nodes:
  - { id: ini, type: start,    text: "Início" }
  - { id: d1,  type: decision, text: "idade >= 18?" }
  - { id: sim, type: process,  text: "Pode entrar" }
  - { id: nao, type: process,  text: "Não pode entrar" }
  - { id: fim, type: start,    text: "Fim" }
edges:
  - { from: ini, to: d1 }
  - { from: d1,  to: sim, label: "sim" }
  - { from: d1,  to: nao, label: "não" }
  - { from: sim, to: fim }
  - { from: nao, to: fim }
:::

Quando você omite o `else`, o caminho do "não" continua existindo: ele
simplesmente não faz nada. Ter consciência disso é o que separa um programa
correto de um que só parece correto — e no capítulo 26, quando uma API tiver
de responder `404`, esse caminho vazio vira o defeito mais visível que
existe.

:::key
Antes de escrever um `if`, responda em voz alta: *"e se não?"*. Se a resposta
for "não acontece nada", escreva o comentário dizendo isso. Se for "não sei",
você achou um requisito que ninguém definiu.
:::

:::story As trinta e sete combinações
Era para ser uma regra só.

— Se o cliente for premium, aplica dez por cento — disse Roberto.

Carlos escreveu o `if`. Levou quatro minutos.

— E se for funcionário? — perguntou Cláudia, na quinta-feira.

— Também dez.

Carlos escreveu o segundo `if`. Levou seis minutos, porque agora tinha um
`else if`.

— E se for premium **e** funcionário?

Silêncio.

— Acumula? — arriscou Carlos.

— Não sei — disse Roberto. — Pergunta pro financeiro.

O financeiro respondeu na terça seguinte: acumula, mas com teto de quinze por
cento, exceto em produto de fornecedor terceirizado, exceto se for o
aniversário do cliente, exceto na primeira compra.

Marina foi ao quadro branco e desenhou uma tabela com todas as combinações.
Eram trinta e sete.

— O problema não é Java — ela disse, tampando o marcador. — O problema é que
ninguém nunca escreveu essa regra inteira em lugar nenhum. A gente vai ser a
primeira pessoa da história da empresa a descobrir o que ela é.
:::

:::art caption="Toda escada de `else if` começa com uma regra só."
src="toda-escada-de-else-if-comeca-com-uma-regra-so.png"
Charge editorial minimalista: quadro branco corporativo inteiramente tomado
por uma tabela de condições "SE... E SE... MAS SE...", com dezenas de células
e setas se cruzando. Uma desenvolvedora sênior de pé ao lado do quadro,
marcador na mão, expressão resignada. Sentado, um desenvolvedor jovem abraça
o notebook contra o peito com olhar vazio. Um gerente, de costas, já saindo
pela porta com o celular no ouvido. Poucos elementos, fundo branco,
composição limpa, humor visual seco, estética de revista de tecnologia.
:::

## Chaves: o caso em que economizar custa caro

Java permite omitir as chaves quando o bloco tem uma linha só:

```java
if (idade >= 18)
    System.out.println("Pode entrar");
```

E permitir isso já custou muito dinheiro ao mundo. O código abaixo compila e
está errado:

:::compare left="O que parece" right="O que o compilador lê"
if (ok)
    libera();
    registra();
---
if (ok) {
    libera();
}
registra();
:::

`registra()` roda sempre, porque a indentação não significa nada para o
compilador. **Use chaves sempre**, inclusive em bloco de uma linha. É a
regra de estilo mais fácil de justificar em uma revisão de código.

:::history
Em fevereiro de 2014 a Apple corrigiu a falha apelidada de *goto fail*: um
`if` sem chaves, em C, com uma linha duplicada por acidente. O resultado era
que a verificação de certificado TLS sempre passava — qualquer pessoa na
mesma rede podia se passar por qualquer site. Duas chaves teriam impedido a
falha de segurança mais comentada daquele ano.
:::

## A escada de `else if`

```java title="Faixa.java" numbered
double nota = 7.5;

if (nota >= 9) {
    System.out.println("Excelente");
} else if (nota >= 7) {
    System.out.println("Bom");
} else if (nota >= 5) {
    System.out.println("Regular");
} else {
    System.out.println("Insuficiente");
}
```

A ordem importa: o primeiro teste verdadeiro vence e os demais nem são
avaliados. Por isso a escada vai do valor mais alto para o mais baixo — na
ordem inversa, `nota >= 5` engoliria todos os casos acima dele.

:::pitfall
Uma escada com mais de quatro degraus é sinal de que falta um conceito. No
capítulo 12 essa mesma faixa de notas vira um `enum`, e a escada desaparece.
Quando você se vê escrevendo o sexto `else if`, pare e pergunte que tipo
está faltando.
:::

## `switch`: quando a pergunta é "qual destes?"

Se todos os testes comparam a **mesma variável** com valores exatos, o
`switch` diz isso melhor:

```java title="Switch com seta (Java 14+)" numbered
String tipo = "PIX";

String prazo = switch (tipo) {
    case "PIX" -> "imediato";
    case "CARTAO" -> "2 dias";
    case "BOLETO" -> "3 dias úteis";
    default -> "desconhecido";
};

System.out.println(prazo);
```

Três coisas valem atenção aqui. A seta `->` substitui o `case:` com `break`.
O `switch` **devolve um valor** — ele é uma expressão, não só um desvio. E o
`default` é obrigatório quando você atribui o resultado a uma variável: o
compilador exige que todos os caminhos produzam algo.

:::compare left="switch antigo (até Java 13)" right="switch moderno (14+)"
switch (tipo) {
  case "PIX":
    prazo = "imediato";
    break;
  case "CARTAO":
    prazo = "2 dias";
    break;
  default:
    prazo = "?";
}
---
prazo = switch (tipo) {
  case "PIX" -> "imediato";
  case "CARTAO" -> "2 dias";
  default -> "?";
};
:::

:::trivia
Aquele `break` obrigatório da forma antiga existe por causa de uma
funcionalidade chamada *fall-through*: sem ele, a execução escorrega para o
`case` seguinte. Era proposital em C, para agrupar casos, e virou a fonte
número um de bugs em `switch`. A forma com seta não escorrega — e é por isso
que ela foi criada.
:::

## Qual usar

| Situação | Escolha |
|---|---|
| Uma condição com faixa (`>=`, `&&`) | `if` |
| Duas ou três faixas ordenadas | escada de `else if` |
| Muitos valores exatos da mesma variável | `switch` |
| Escolher **um valor** entre dois | ternário |
| Muitos valores exatos + comportamento | `enum` (capítulo 12) |

Tabela: Não é questão de gosto: cada forma comunica uma intenção diferente
para quem lê depois.

:::practice
Rode a escada de notas com `9`, `7`, `5` e `4.9`. Depois inverta a ordem dos
testes e rode de novo com os mesmos valores. Guarde as duas saídas: é a
demonstração mais curta de que ordem de condição é lógica, não estilo.
:::

:::story
Duas semanas depois, Marina apagou os trinta e sete `if` e deixou quatro
linhas no lugar. Carlos perguntou como.

— A regra não mudou — ela disse. — Só parou de morar em trinta e sete
lugares.

O como está no capítulo 12.
:::

## Um `if` que você vai escrever muito

O projeto do livro é uma API, e uma API passa o dia respondendo a uma
pergunta só: *isso existe?* A forma dessa decisão em Java moderno é esta:

```java title="O formato que reaparece no capítulo 22" numbered
Optional<Product> encontrado = repository.findById(id);

if (encontrado.isEmpty()) {
    throw new ProductNotFoundException(id);
}
return encontrado.get();
```

Você ainda não conhece `Optional`, nem `throw`, nem repositório. Guarde
apenas a forma: **trate o caso ruim primeiro e saia**. Esse padrão, chamado
*early return*, mantém o código raso — sem ele, uma API real acumula cinco
níveis de `if` aninhado.

:::summary
- `if` exige `boolean`; número não vale como condição.
- Use chaves sempre — a indentação não significa nada para o compilador.
- Em uma escada, o primeiro teste verdadeiro vence: ordene do mais restritivo
  ao mais geral.
- `switch` com seta devolve valor e não escorrega para o caso seguinte.
- Trate o caso ruim primeiro e saia: o código fica raso.
:::

:::checkpoint
Você escreve decisões simples e encadeadas, escolhe entre `if`, `switch` e
ternário por intenção, e reconhece o caminho implícito de um `if` sem `else`.
:::

:::milestone
O programa agora decide. Ainda não guarda nada nem responde a ninguém — mas
a lógica que vai recusar um preço negativo no capítulo 25 é exatamente esta.
:::

:::exercise level=1
Escreva um programa que receba uma temperatura como argumento e imprima
`"Febre"` acima de 37.8 e `"Normal"` caso contrário.

:::answer
```java
double temperatura = Double.parseDouble(args[0]);
if (temperatura > 37.8) {
    System.out.println("Febre");
} else {
    System.out.println("Normal");
}
```
:::

:::exercise level=2
Calcule a tarifa de um estacionamento: a primeira hora custa R$ 8, cada hora
seguinte custa R$ 5 e o valor máximo do dia é R$ 40. Teste com 1, 3 e 12
horas.

:::answer
```java
int horas = Integer.parseInt(args[0]);
double valor = 8 + (horas - 1) * 5;
if (valor > 40) {
    valor = 40;
}
System.out.println("R$ " + valor);
```
O teto entra **depois** do cálculo, como uma segunda decisão. Tentar resolver
o limite dentro da mesma expressão é o caminho mais curto para um erro
difícil de enxergar.
:::

:::exercise level=3
Reescreva a escada de notas usando `switch` com seta e o resultado inteiro da
divisão por 10 (`(int) nota / 10`). Depois decida qual das duas versões você
deixaria no projeto e justifique.

:::answer
```java
String conceito = switch ((int) nota / 10) {
    case 10, 9 -> "Excelente";
    case 8, 7 -> "Bom";
    case 6, 5 -> "Regular";
    default -> "Insuficiente";
};
```
Funciona e é mais curta. Mas a versão com `if` diz explicitamente
`nota >= 9`, enquanto esta exige que o leitor reconstrua a faixa a partir de
uma divisão. Para faixas, `if` comunica melhor; para valores exatos,
`switch`. A resposta certa é saber por quê.
:::
