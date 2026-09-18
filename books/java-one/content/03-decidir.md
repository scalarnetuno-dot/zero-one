---
title: "Decidir"
number: 3
kicker: "Escolher um caminho é assumir o outro — inclusive quando ele não está escrito."
---

Até agora o programa fazia sempre a mesma coisa. A partir daqui ele olha
para um valor e escolhe. É a menor unidade de inteligência que um programa
pode ter, e cabe em três linhas.

## `if` pede um `boolean`, não um número

```java title="Maioridade.java" numbered
int idade = 18;

if (idade >= 18) {
    System.out.println("Pode entrar");
} else {
    System.out.println("Não pode entrar");
}
```

A condição entre parênteses precisa resultar em `true` ou `false`. Em
linguagens onde `0` vale como falso, `if (idade)` compila; em Java, não.
O compilador exige que você diga o que está comparando.

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
simplesmente não faz nada. Ter consciência disso é o que separa um
programa correto de um programa que só parece correto.

## O erro que todo mundo comete uma vez

```java title="Isto não funciona como você espera"
String senha = "abc";

if (senha == "abc") {
    System.out.println("Liberado");
}
```

Pode imprimir nada. `==` compara **referências** — pergunta se os dois
nomes apontam para o mesmo objeto na memória. Para texto, a pergunta certa
é sobre conteúdo:

```java title="Isto funciona sempre"
if (senha.equals("abc")) {
    System.out.println("Liberado");
}
```

:::warning
Às vezes `==` funciona com `String` e isso é pior do que se nunca
funcionasse: o compilador otimiza literais iguais para o mesmo objeto, o
teste passa, e o defeito só aparece quando o texto vem de um arquivo ou do
teclado. Para texto, use sempre `equals`.
:::

:::tip Inverta a comparação com literais
`"abc".equals(senha)` faz o mesmo teste e não estoura se `senha` for
`null`. É um hábito de duas teclas que apaga uma classe inteira de erro.
:::

## Encadear sem virar escada

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

A ordem importa: o primeiro teste verdadeiro vence e os outros nem são
avaliados. Por isso a escada vai do valor mais alto para o mais baixo — na
ordem inversa, `nota >= 5` engoliria todos os casos.

:::practice
Rode o programa acima com `nota = 9`, `7`, `5` e `4.9`. Depois inverta a
ordem dos testes e rode de novo com os mesmos quatro valores. Guarde a
saída: é a demonstração mais curta de que ordem de condição é lógica, não
estilo.
:::

## E quando a condição tem duas partes

```java title="Duas condições"
boolean temIngresso = true;
int idade = 16;

if (temIngresso && idade >= 18) {
    System.out.println("Entrada liberada");
}
```

`&&` exige as duas; `||` aceita qualquer uma; `!` inverte. Java avalia
`&&` da esquerda para a direita e **para no primeiro falso** — o que
permite escrever `if (nome != null && nome.equals("Ana"))` sem risco.

:::summary
- `if` exige uma expressão `boolean`; número não vale como condição.
- Para texto, `equals` compara conteúdo; `==` compara identidade.
- Em uma escada de `else if`, o primeiro teste verdadeiro vence.
- `&&` e `||` param assim que o resultado está decidido.
:::

:::exercise level=1
Escreva um programa que receba uma `double temperatura` e imprima
`"Febre"` acima de 37.8 e `"Normal"` caso contrário.

:::answer
```java
double temperatura = 38.2;
if (temperatura > 37.8) {
    System.out.println("Febre");
} else {
    System.out.println("Normal");
}
```
:::

:::exercise level=2
Escreva um programa que decida a tarifa de um estacionamento: a primeira
hora custa R$ 8, cada hora seguinte custa R$ 5, e o valor máximo do dia é
R$ 40. Teste com 1, 3 e 12 horas.

:::answer
```java
int horas = 3;
double valor = 8 + (horas - 1) * 5;
if (valor > 40) {
    valor = 40;
}
System.out.println("R$ " + valor);
```
O teto entra depois do cálculo, como uma segunda decisão. Tentar resolver
o limite dentro da mesma expressão é o caminho mais curto para um erro
difícil de enxergar.
:::
