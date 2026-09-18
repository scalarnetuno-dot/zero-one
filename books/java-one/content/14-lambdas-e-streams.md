---
title: "Lambdas e streams"
number: 14
part: p2
kicker: "O laço diz como percorrer. O stream diz o que você quer. A segunda frase é mais curta."
goal: >-
  Escrever uma lambda, encadear `filter`, `map`, `sorted` e `collect`, e
  reconhecer quando um stream ajuda e quando ele atrapalha.
---

Em 2014 o Java 8 acrescentou funções como valor. Não foi maquiagem: mudou o
estilo do código Java e é a base de metade das APIs modernas — inclusive de
algumas que o Spring vai pedir a você na Parte 4.

## Lambda: uma função sem nome

```java title="A mesma ideia, duas escritas" numbered
// antes do Java 8: classe anônima
Comparator<String> porTamanho = new Comparator<String>() {
    @Override
    public int compare(String a, String b) {
        return a.length() - b.length();
    }
};

// Java 8: lambda
Comparator<String> porTamanho2 =
        (a, b) -> a.length() - b.length();
```

Oito linhas viraram duas. A lambda é a mesma coisa: a implementação de uma
interface que tem **um único método abstrato**. Java chama isso de *interface
funcional*, e é por isso que a lambda sabe qual método ela está
implementando.

:::anatomy title="A sintaxe da lambda, em três formas"
lang: java
code: |
  p -> p.getPreco() > 100
  (a, b) -> a.length() - b.length()
  p -> {
      log(p);
      return p.getNome();
  }
notes:
  - { line: 1, text: "Um parâmetro, sem parênteses; corpo de uma expressão, sem `return`." }
  - { line: 2, text: "Dois parâmetros exigem parênteses. O tipo é inferido do contexto." }
  - { line: 3, text: "Corpo com chaves precisa de `return` explícito." }
:::

## Referência de método: a lambda que já existe

```java title="Quatro formas da mesma ideia" numbered
produtos.forEach(p -> System.out.println(p));   // lambda
produtos.forEach(System.out::println);          // referência

nomes.sort((a, b) -> a.compareTo(b));           // lambda
nomes.sort(String::compareTo);                  // referência
```

Quando a lambda só chama um método existente, `::` diz isso mais curto. Você
vai ver `Product::getNome` em quase todo código Java moderno.

## Stream: a sequência de operações

```java title="O laço do capítulo 6, reescrito" numbered
List<Product> caros = produtos.stream()
        .filter(p -> p.getPreco() > 100)
        .toList();
```

:::compare left="Laço imperativo" right="Stream declarativo"
List<Product> caros =
    new ArrayList<>();
for (Product p : produtos) {
  if (p.getPreco() > 100) {
    caros.add(p);
  }
}
---
var caros = produtos.stream()
    .filter(p ->
        p.getPreco() > 100)
    .toList();
:::

A diferença não é o tamanho, é o que você lê. À esquerda você reconstrói a
intenção a partir do mecanismo; à direita a intenção está escrita: *filtre os
caros*.

## As cinco operações que resolvem quase tudo

```java title="Um pipeline completo" numbered
List<String> nomes = produtos.stream()
        .filter(p -> p.getEstoque() > 0)          // seleciona
        .sorted(Comparator.comparing(Product::getPreco))
        .map(Product::getNome)                    // transforma
        .limit(10)                                // corta
        .toList();                                // materializa
```

| Operação | O que faz | Devolve |
|---|---|---|
| `filter` | mantém quem passa no teste | stream |
| `map` | transforma cada item | stream |
| `sorted` | ordena | stream |
| `limit` / `skip` | corta | stream |
| `toList` / `count` / `sum` | encerra | resultado |

Tabela: As quatro primeiras são **intermediárias** — devolvem stream e não
executam nada. A última é **terminal**: é ela que faz o pipeline rodar.

:::key
Um stream sem operação terminal **não executa**. Se o seu `filter` parece não
ter rodado, procure o `toList` que falta. Essa avaliação tardia é o que
permite ao Java percorrer a coleção uma única vez, aplicando todos os passos
item a item.
:::

## Reduzir a um número

```java title="Soma, contagem, média" numbered
long ativos = produtos.stream()
        .filter(Product::isAtivo)
        .count();

double total = produtos.stream()
        .mapToDouble(Product::getPreco)
        .sum();

OptionalDouble media = produtos.stream()
        .mapToDouble(Product::getPreco)
        .average();
```

`mapToDouble` troca o stream de objetos por um de números primitivos, que tem
`sum`, `average`, `max` e `min` prontos. E repare no `OptionalDouble`: a média
de uma lista vazia não existe, e a API é honesta sobre isso — a lição do
capítulo 13 aparecendo de novo.

## Agrupar: o `Map` do capítulo 8 em uma linha

```java title="Contagem por status" numbered
Map<Status, Long> porStatus = produtos.stream()
        .collect(Collectors.groupingBy(
                Product::getStatus,
                Collectors.counting()));
```

Compare com as cinco linhas de `getOrDefault` do capítulo 8. Mesma saída,
outra escrita — e a versão com stream continua legível quando o agrupamento
tem dois níveis.

:::trivia
Streams foram desenhados com um segundo objetivo: paralelismo. Trocar
`.stream()` por `.parallelStream()` distribui o trabalho entre os núcleos.
Parece uma otimização grátis e quase nunca é: para coleções pequenas, o custo
de coordenar as threads é maior que o ganho. A regra empírica do próprio time
do Java é não considerar paralelismo abaixo de dez mil elementos.
:::

:::story O pull request de uma linha
Carlos descobriu streams numa quinta-feira e reescreveu o relatório inteiro
na sexta.

O método tinha dezoito linhas. Virou uma.

Uma linha de quatrocentos e doze caracteres, com quatro `filter`, dois `map`,
um `flatMap`, um `sorted` com comparador invertido e um `collect` agrupando
por duas chaves. Ele abriu o *pull request* com o título "simplificação".

Marina respondeu com um único comentário, na linha 1:

> "Explica em voz alta, sem ler, o que esta linha faz. Se você conseguir, eu
> aprovo."

Carlos tentou. Chegou até o terceiro `filter`.

A versão aprovada tinha seis linhas e três métodos com nome:
`ativos()`, `maisVendidos()` e `porCategoria()`. Cada um com um stream curto
dentro.

— Stream não é para escrever menos — disse Marina. — É para escrever o que
você quer em vez de como percorrer.
:::

:::art caption="Uma linha com quatrocentos caracteres não é código conciso: é código comprimido."
src="uma-linha-com-quatrocentos-caracteres-nao-e-codigo-conciso-e-codigo-comprimido.png"
Charge editorial minimalista: tela de editor de código mostrando uma única
linha absurdamente longa que atravessa o monitor e continua por uma fita de
papel que sai da tela, cai no chão e se enrola pela sala. Um desenvolvedor
jovem, orgulhoso, segura a ponta da fita. Uma desenvolvedora sênior, ao lado,
segura uma tesoura pequena com expressão paciente. Fundo branco, poucos
elementos, humor visual seco, estética de revista de tecnologia.
:::

## Quando o laço ainda é melhor

Streams não substituem tudo. O laço continua mais claro quando:

- você precisa do **índice** de cada item;
- precisa **sair no meio** com informação de onde parou;
- o corpo tem várias linhas com efeitos colaterais (log, gravação, envio);
- você está depurando — passo a passo em stream é desconfortável.

:::pitfall
Stream com efeito colateral dentro do `map` é armadilha:
`.map(p -> { salvar(p); return p; })`. Funciona, e engana quem lê: `map` diz
"transformo", não "gravo no banco". Para agir sobre cada item, use `forEach` —
o nome avisa que algo vai acontecer.
:::

## O pipeline que o projeto vai usar

```java title="Um recorte do capítulo 28" numbered
public List<ProductResponse> buscarPorNome(String termo) {
    return repository.findAll().stream()
            .filter(p -> p.getNome()
                    .toLowerCase()
                    .contains(termo.toLowerCase()))
            .map(ProductResponse::of)
            .toList();
}
```

Esta versão filtra **em memória** — e é exatamente por isso que o capítulo 28
vai substituí-la por uma consulta que filtra no banco. Guarde a diferença:
stream é ótimo para transformar o que você já tem, e péssimo para evitar
trazer o que você não precisa.

:::summary
- Lambda é a implementação de uma interface com um único método abstrato.
- `::` referencia um método que já existe.
- Operação intermediária devolve stream; só a terminal executa o pipeline.
- `groupingBy` resolve em uma linha o que o `Map` fazia em cinco.
- Laço ainda ganha quando há índice, saída no meio ou efeito colateral.
:::

:::checkpoint
Você escreve lambdas, encadeia `filter`, `map`, `sorted` e `collect`, reduz um
stream a um número e sabe justificar quando prefere um laço.
:::

:::milestone
Fim da Parte 2. O projeto tem vocabulário (`Product`, `Status`, DTOs),
regras com nome, erros com tipo e um estilo de transformação de dados. É Java
suficiente para o Spring — e é exatamente onde a Parte 3 começa.
:::

:::exercise level=1
Dada uma `List<Product>`, escreva um stream que devolva os nomes dos produtos
com estoque zero, em ordem alfabética.

:::answer
```java
List<String> semEstoque = produtos.stream()
        .filter(p -> p.getEstoque() == 0)
        .map(Product::getNome)
        .sorted()
        .toList();
```
:::

:::exercise level=2
Calcule o valor total do estoque (preço × quantidade de cada produto) usando
stream. Compare com a versão em laço do capítulo 9.

:::answer
```java
double total = produtos.stream()
        .mapToDouble(p -> p.getPreco() * p.getEstoque())
        .sum();
```
Quatro linhas contra seis, e uma diferença mais importante: a versão com
stream não tem variável mutável nenhuma. Sem acumulador, não há como esquecer
de inicializá-lo.
:::

:::exercise level=3
Agrupe os produtos por faixa de preço (até 50, de 50 a 200, acima de 200) e
devolva um `Map<String, List<String>>` com os nomes de cada faixa.

:::answer
```java
Map<String, List<String>> faixas = produtos.stream()
        .collect(Collectors.groupingBy(
                p -> p.getPreco() <= 50 ? "barato"
                        : p.getPreco() <= 200 ? "médio" : "caro",
                Collectors.mapping(Product::getNome,
                        Collectors.toList())));
```
Aquele ternário encadeado é o limite do bom gosto — na prática, ele merece
virar um método `faixaDe(Product p)`, ou melhor, um `enum Faixa` com o
critério dentro, como no capítulo 12. Se você pensou isso antes de ler,
a Parte 2 cumpriu o objetivo.
:::
