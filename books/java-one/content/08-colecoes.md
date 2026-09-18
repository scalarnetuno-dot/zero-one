---
title: "Arrays e coleções"
number: 8
part: p2
kicker: "Array tem tamanho. Lista tem vida. Mapa tem chave. Escolher errado custa caro."
goal: >-
  Escolher entre `List`, `Set` e `Map` pelo problema, percorrer cada um deles
  e explicar por que se declara a interface e não a implementação.
---

Array resolve o caso em que você sabe o tamanho. Uma API não sabe: o cliente
pode cadastrar três produtos hoje e trezentos amanhã. Para isso existe o
*framework* de coleções — a parte da biblioteca padrão que você mais vai usar
no resto da vida.

## As três perguntas

| Pergunta | Estrutura | Característica |
|---|---|---|
| Em que ordem? | `List` | aceita repetido, tem índice |
| Está aqui? | `Set` | não aceita repetido, sem ordem garantida |
| Qual é o valor de? | `Map` | pares chave → valor |

Tabela: Escolher a coleção é escolher a pergunta que você vai fazer mil vezes
por segundo.

## `List`: ordem e repetição

```java title="Uma lista que cresce" numbered
List<String> produtos = new ArrayList<>();
produtos.add("Teclado");
produtos.add("Mouse");
produtos.add("Teclado");        // repetido, e está tudo bem

System.out.println(produtos.size());     // 3
System.out.println(produtos.get(0));     // Teclado
System.out.println(produtos.contains("Mouse"));  // true

for (String p : produtos) {
    System.out.println(p);
}
```

:::anatomy title="A linha mais importante do capítulo"
lang: java
code: |
  List<String> produtos = new ArrayList<>();
notes:
  - { line: 1, text: "`List` é a **interface**: o contrato, o que se pode fazer." }
  - { line: 1, text: "`<String>` é o tipo genérico: o compilador passa a recusar qualquer coisa que não seja texto." }
  - { line: 1, text: "`ArrayList` é a **implementação**: como isso é feito na memória." }
  - { line: 1, text: "`<>` vazio (*diamond*) deduz o tipo do lado esquerdo — desde o Java 7." }
:::

Declarar `List` à esquerda e `ArrayList` à direita é uma convenção com
consequência prática: se amanhã você precisar trocar por `LinkedList`, muda
uma palavra e nada mais quebra. É o primeiro encontro com uma ideia que o
Spring leva ao extremo na Parte 3 — **dependa da interface, não da
implementação.**

:::trivia
Antes do Java 5 não havia genéricos: uma `List` guardava `Object`, e você
precisava escrever `(String) lista.get(0)` para recuperar o texto. Um erro de
tipo só aparecia em produção, como um `ClassCastException`. Os genéricos
existem para transformar aquele defeito de execução em erro de compilação —
a mesma troca que este livro elogia desde o capítulo 3.
:::

## `Set`: pertence ou não

```java title="Sem repetição" numbered
Set<String> categorias = new HashSet<>();
categorias.add("periférico");
categorias.add("periférico");    // ignorado
System.out.println(categorias.size());   // 1
```

`Set` é a estrutura certa para "já vi este?", "quais são os distintos?", "o
usuário tem esta permissão?" — e é exatamente essa última pergunta que o
capítulo 33 vai fazer.

:::pitfall
`HashSet` não garante ordem nenhuma — nem a de inserção. Se você imprimir um
`HashSet` esperando a ordem em que inseriu, vai levar um susto. Quando a
ordem importa, use `LinkedHashSet` (ordem de inserção) ou `TreeSet` (ordem
natural).
:::

:::story O relatório com ordem própria
— O relatório está saindo em ordem aleatória — disse Cláudia.

— Não existe ordem aleatória — respondeu Carlos. — Deve ser ordem de
cadastro.

Não era. Era `HashSet`.

Rodaram de novo: outra ordem. Rodaram uma terceira vez: a mesma ordem da
primeira, o que confundiu todo mundo por mais vinte minutos.

Roberto, que passava por ali, ouviu "ordem imprevisível" e teve uma ideia:

— Isso não é um bom sinal? Tipo, o sistema está escolhendo sozinho. Parece
inteligência artificial.

Marina levantou a cabeça devagar e disse, sem alterar a voz:

— Roberto, é uma tabela de espalhamento. Ela não escolhe. Ela não tem
opinião. Ela tem um resto de divisão.
:::

## `Map`: chave e valor

```java title="Estoque por produto" numbered
Map<String, Integer> estoque = new HashMap<>();
estoque.put("Teclado", 12);
estoque.put("Mouse", 3);

System.out.println(estoque.get("Teclado"));          // 12
System.out.println(estoque.get("Monitor"));          // null
System.out.println(estoque.getOrDefault("Monitor", 0));  // 0

for (Map.Entry<String, Integer> item : estoque.entrySet()) {
    System.out.println(item.getKey() + ": " + item.getValue());
}
```

`get` de uma chave inexistente devolve `null` — e `null` é a origem do erro
mais famoso da plataforma. `getOrDefault` existe exatamente para você não
precisar pensar nisso.

:::diagram type="cells" caption="Um mapa é uma tabela de duas colunas com busca instantânea pela primeira."
items: ["Teclado → 12", "Mouse → 3", "Cabo → 41"]
orientation: vertical
notes:
  - { at: 0, text: "chave única" }
:::

## Listas imutáveis: o atalho moderno

```java
List<String> fixos = List.of("PIX", "CARTAO", "BOLETO");
Map<String, Integer> prazos = Map.of("PIX", 0, "BOLETO", 3);
```

`List.of` e `Map.of` criam coleções **imutáveis**: `add` nelas lança
`UnsupportedOperationException`. Isso parece limitação e é proteção — uma
constante que ninguém pode alterar por acidente. Use para valores fixos do
sistema.

:::pitfall
`List.of("a", "b")` não é um `ArrayList`. Se você recebe uma lista de fora e
precisa alterá-la, copie: `new ArrayList<>(recebida)`. Modificar uma lista
que veio de outro lugar é, além de erro em potencial, má educação de projeto.
:::

## Ordenar

```java title="Duas ordens, uma linha cada" numbered
List<String> nomes = new ArrayList<>(
        List.of("Mouse", "Cabo", "Teclado"));

Collections.sort(nomes);                    // ordem alfabética
nomes.sort(Comparator.reverseOrder());      // inversa
nomes.sort(Comparator.comparing(String::length));  // por tamanho
```

A última linha usa duas coisas do capítulo 14 (referência de método e
comparador funcional). Deixe-a guardada: quando chegar lá, você já terá visto
funcionar.

## Percorrer: as três formas e quando usar cada uma

```java title="O mesmo laço, três dialetos" numbered
for (String p : produtos) { }          // padrão, quase sempre

for (int i = 0; i < produtos.size(); i++) { }  // índice importa

produtos.forEach(System.out::println); // funcional (cap. 14)
```

:::pitfall
Remover itens durante um `for-each` lança
`ConcurrentModificationException`. A coleção detecta que mudou por baixo do
laço e se recusa a continuar. Para remover, use
`produtos.removeIf(p -> p.isBlank())` — uma linha, sem laço, sem exceção.
:::

## O que o projeto vai usar

Guarde este trecho: ele é a versão em memória do que o capítulo 21 fará com
um banco de dados de verdade.

```java title="Repositório de brinquedo" numbered
Map<Long, String> produtos = new HashMap<>();
long proximoId = 1;

produtos.put(proximoId++, "Teclado");        // create
String nome = produtos.get(1L);              // read
produtos.put(1L, "Teclado mecânico");        // update
produtos.remove(1L);                         // delete
```

Quatro operações, um mapa. Quando o Spring Data JPA entrar em cena, ele vai
oferecer exatamente estes quatro métodos — `save`, `findById`, `save`,
`deleteById` — e a diferença é que os dados sobrevivem ao desligamento da
máquina.

:::summary
- `List` para ordem, `Set` para unicidade, `Map` para associação.
- Declare a interface (`List`), instancie a implementação (`ArrayList`).
- Genéricos (`<String>`) transformam erro de execução em erro de compilação.
- `getOrDefault` evita `null`; `List.of` cria coleção imutável.
- Não remova dentro de um `for-each`: use `removeIf`.
:::

:::checkpoint
Você escolhe a coleção certa para o problema, percorre as três, evita `null`
com `getOrDefault` e sabe por que se declara a interface.
:::

:::milestone
O projeto tem um "banco de dados" de mentira: um `Map` na memória com as
quatro operações do CRUD. É o mesmo desenho que vai sobreviver à troca por
PostgreSQL no capítulo 19.
:::

:::exercise level=1
Crie uma `List<String>` com cinco nomes de produto, ordene em ordem
alfabética e imprima cada um em uma linha.

:::answer
```java
List<String> nomes = new ArrayList<>(
        List.of("Mouse", "Cabo", "Teclado", "Monitor", "Webcam"));
Collections.sort(nomes);
nomes.forEach(System.out::println);
```
:::

:::exercise level=2
Use um `Map<String, Integer>` para contar quantas vezes cada palavra aparece
em um array de textos. Dica: `getOrDefault`.

:::answer
```java
Map<String, Integer> contagem = new HashMap<>();
for (String palavra : palavras) {
    contagem.put(palavra, contagem.getOrDefault(palavra, 0) + 1);
}
```
Este é provavelmente o trecho de código mais reescrito da história do Java.
No capítulo 14 ele vira uma linha com `Collectors.groupingBy` — e você vai
achar bonito exatamente porque escreveu a versão longa primeiro.
:::

:::exercise level=3
Dado um `Map<String, Integer>` de estoque, imprima apenas os produtos com
menos de cinco unidades, em ordem alfabética de nome.

:::answer
```java
new TreeMap<>(estoque).forEach((nome, qtd) -> {
    if (qtd < 5) {
        System.out.println(nome + ": " + qtd);
    }
});
```
`TreeMap` mantém as chaves ordenadas — passar o mapa no construtor já ordena.
Reconhecer que a estrutura de dados pode resolver o problema no lugar do
algoritmo é uma das marcas de quem programa há algum tempo.
:::
