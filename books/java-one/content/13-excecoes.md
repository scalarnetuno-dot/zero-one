---
title: "Exceções"
number: 13
part: p2
kicker: "Um erro tratado é um requisito. Um erro engolido é uma dívida com juros."
epigraph: "Eu chamo isso de erro de um bilhão de dólares. A invenção da referência nula, em 1965."
epigraph_by: "Tony Hoare, criador do Quicksort"
goal: >-
  Lançar e capturar exceções, escolher entre *checked* e *unchecked*, criar
  uma exceção própria e nunca mais escrever um `catch` vazio.
---

Programas dão errado por três motivos: o programador errou, o usuário mandou
lixo, ou o mundo lá fora falhou. Exceção é o mecanismo com que Java avisa que
algo saiu do trilho — e a forma como você a trata define a qualidade da sua
API.

## O erro mais famoso da plataforma

```java title="NullPointerException" numbered
String nome = null;
System.out.println(nome.length());
```

```text title="Terminal"
Exception in thread "main" java.lang.NullPointerException:
  Cannot invoke "String.length()" because "nome" is null
        at Loja.main(Loja.java:3)
```

Repare no detalhe: a mensagem diz **qual** variável era nula e **qual** método
você tentou chamar. Isso é conquista recente (Java 14, *helpful NullPointer
messages*); antes vinha só o número da linha, e quem tinha cinco chamadas
encadeadas na mesma linha ficava adivinhando.

:::history
Tony Hoare introduziu a referência nula em ALGOL W, em 1965, porque "era
fácil de implementar". Em 2009 ele pediu desculpas publicamente em uma
palestra, chamando-a de erro de um bilhão de dólares. Java herdou `null` do
C++, e a linguagem passou trinta anos criando remédios: `Optional` (Java 8),
mensagens detalhadas (Java 14) e anotações de nulidade nas bibliotecas.
:::

:::story O bug que só o Seu Antônio reproduz
— Dá erro quando eu clico — disse Seu Antônio.

— Erro em qual tela?

— Na tela.

Carlos pediu print. Veio uma foto do monitor, tirada de celular, na
diagonal, com o reflexo da janela cobrindo metade da mensagem. Dava para ler
três palavras: `NullPointerException`, `at` e `ProductService`.

Ele tentou reproduzir por duas horas. Cadastrou produto, editou, apagou,
clicou em tudo. Nada.

Marina perguntou a única coisa que faltava perguntar:

— Seu Antônio, o senhor preenche o campo "apelido do produto"?

— Não, moço, aquilo ali é opcional, né?

Era opcional. E era o único campo que o código lia sem verificar se existia.

Nenhum outro funcionário da empresa deixava aquele campo vazio, porque todo
mundo tinha aprendido, sem combinar, a preencher tudo. Seu Antônio não tinha
aprendido nada disso. Ele só usava o sistema como ele foi escrito.
:::

## `try`, `catch`, `finally`

```java title="A forma completa" numbered
try {
    int quantidade = Integer.parseInt(args[0]);
    System.out.println(100 / quantidade);
} catch (NumberFormatException e) {
    System.out.println("Isso não é um número: " + args[0]);
} catch (ArithmeticException e) {
    System.out.println("Não posso dividir por zero");
} finally {
    System.out.println("Isto roda sempre");
}
```

O `try` delimita o trecho de risco. Cada `catch` trata **um tipo** de
problema. O `finally` roda com ou sem erro — é onde se fecha arquivo, conexão,
qualquer recurso.

:::pitfall
O pecado capital:

```java
try {
    salvar(produto);
} catch (Exception e) {
    // depois eu vejo
}
```

Isso não trata o erro: apaga a evidência. O programa continua como se tivesse
funcionado, o dado não foi salvo e ninguém fica sabendo. Se você realmente não
pode tratar, **relance** ou pelo menos registre no log. Um `catch` vazio é a
única linha de código que eu reprovaria em qualquer revisão, sem discussão.
:::

## Duas famílias: *checked* e *unchecked*

:::diagram type="blocks" caption="A hierarquia que decide se o compilador vai te obrigar a tratar."
flow: false
rows:
  - [{ text: "Throwable", note: "tudo que pode ser lançado" }]
  - [{ text: "Error", note: "a JVM desistiu — não trate" }, { text: "Exception", note: "checked: o compilador cobra" }]
  - [{ text: "RuntimeException", note: "unchecked: o compilador não cobra" }]
:::

| | *Checked* | *Unchecked* |
|---|---|---|
| Exemplo | `IOException`, `SQLException` | `IllegalArgumentException`, `NPE` |
| Compilador | obriga `try` ou `throws` | não obriga nada |
| Significa | falha esperada do mundo externo | defeito de programação ou de uso |

Tabela: A regra prática: se quem chamou pode fazer algo a respeito, *checked*;
se é bug, *unchecked*.

```java title="Checked: o compilador exige uma decisão" numbered
// não compila sem tratar:
Files.readString(Path.of("config.txt"));

// opção 1: tratar aqui
try {
    Files.readString(Path.of("config.txt"));
} catch (IOException e) {
    System.out.println("não achei o arquivo");
}

// opção 2: declarar que não é meu problema
static String ler() throws IOException {
    return Files.readString(Path.of("config.txt"));
}
```

:::trivia
Exceções *checked* são uma ideia exclusiva de Java — nenhuma linguagem
popular depois dela repetiu o experimento. O motivo é o efeito colateral
observado em campo: para se livrar da obrigação, gerações de programadores
escreveram `catch (Exception e) {}`. O remédio criou a doença que queria
curar. Frameworks modernos, o Spring inclusive, convertem quase tudo para
*unchecked*.
:::

## `throw`: avisar em vez de mentir

```java title="Recusar é melhor que corrigir escondido" numbered
public void baixarEstoque(int quantidade) {
    if (quantidade <= 0) {
        throw new IllegalArgumentException(
                "quantidade deve ser positiva: " + quantidade);
    }
    if (quantidade > estoque) {
        throw new IllegalStateException(
                "estoque insuficiente: " + estoque);
    }
    this.estoque -= quantidade;
}
```

Duas exceções diferentes porque são dois problemas diferentes:
`IllegalArgumentException` é culpa de quem chamou; `IllegalStateException` é
uma situação do objeto. No capítulo 26 essa distinção vira a diferença entre
responder `400 Bad Request` e `409 Conflict`.

## Exceção própria: o nome que carrega o significado

```java title="ProductNotFoundException.java" numbered
public class ProductNotFoundException extends RuntimeException {
    private final Long id;

    public ProductNotFoundException(Long id) {
        super("produto não encontrado: " + id);
        this.id = id;
    }

    public Long getId() {
        return id;
    }
}
```

Três decisões nessas dez linhas. Estende `RuntimeException` (*unchecked*),
porque quem chamou não tem como "tratar" um id que não existe — quem trata é a
camada HTTP. A mensagem inclui o id, para o log servir de alguma coisa. E o id
fica guardado, para quem capturar poder montar a resposta.

:::key
O nome da exceção é a parte mais valiosa dela. `ProductNotFoundException` no
log diz o que aconteceu sem que ninguém precise ler a mensagem. `Exception` e
`RuntimeException` genéricas jogam esse valor no lixo.
:::

## `Optional`: a alternativa ao `null`

```java title="Dizer que pode não haver nada" numbered
Optional<Product> encontrado = repository.findById(7L);

if (encontrado.isPresent()) {
    System.out.println(encontrado.get().getNome());
}

// melhor: sem if
String nome = encontrado
        .map(Product::getNome)
        .orElse("desconhecido");

// ou lançando a exceção certa
Product p = encontrado
        .orElseThrow(() -> new ProductNotFoundException(7L));
```

`Optional` é uma caixa que pode estar vazia. A diferença em relação a `null`
não é técnica, é de comunicação: a assinatura do método **avisa** que o
resultado pode não existir, e o compilador te obriga a decidir o que fazer.

A última forma — `orElseThrow` — é a que o projeto vai usar do capítulo 22 ao
fim do livro. Guarde-a.

:::pitfall
`Optional` serve para **retorno** de método. Não use como parâmetro, nem como
atributo de entidade, nem em campo de record que vai virar JSON. O criador da
API, Brian Goetz, foi explícito sobre isso — e a internet passou dez anos
ignorando.
:::

## `try-with-resources`

```java title="Fecha sozinho, mesmo com erro" numbered
try (var reader = Files.newBufferedReader(Path.of("dados.csv"))) {
    System.out.println(reader.readLine());
} catch (IOException e) {
    System.out.println("falhou a leitura");
}
```

O que está entre parênteses é fechado automaticamente ao sair do bloco, com ou
sem exceção. Antes do Java 7 isso exigia um `finally` com outro `try` dentro —
o trecho de código mais feio que a linguagem já pediu.

:::summary
- `try/catch` trata por tipo; `finally` roda sempre.
- *Checked* obriga tratamento; *unchecked* sinaliza defeito de programação.
- Nunca escreva `catch` vazio: relance ou registre.
- Exceção própria com nome específico vale mais que mensagem longa.
- `Optional` comunica ausência no tipo de retorno; `orElseThrow` é o padrão do
  projeto.
:::

:::checkpoint
Você trata exceções por tipo, decide entre *checked* e *unchecked*, cria uma
exceção própria com contexto e usa `Optional` no retorno em vez de `null`.
:::

:::milestone
O projeto sabe recusar: preço inválido, estoque insuficiente, produto
inexistente. Falta traduzir essas recusas em respostas HTTP — e é o capítulo
26 que faz isso, usando exatamente as classes deste capítulo.
:::

:::exercise level=1
Escreva um programa que receba um número como argumento, divida 100 por ele e
trate os dois erros possíveis com mensagens distintas.

:::answer
```java
try {
    int n = Integer.parseInt(args[0]);
    System.out.println(100 / n);
} catch (NumberFormatException e) {
    System.out.println("argumento não é número");
} catch (ArithmeticException e) {
    System.out.println("divisão por zero");
}
```
Falta um terceiro caso: rodar sem argumento nenhum lança
`ArrayIndexOutOfBoundsException`, que não é capturada. Achou? Bom sinal.
:::

:::exercise level=2
Crie `InsufficientStockException` guardando o estoque disponível e a
quantidade pedida. Use-a em `baixarEstoque`.

:::answer
```java
public class InsufficientStockException extends RuntimeException {
    public InsufficientStockException(int disponivel, int pedido) {
        super("estoque " + disponivel + ", pedido " + pedido);
    }
}
```
Guardar os dois números na mensagem é o que transforma um log em
diagnóstico — sem eles, você sabe que falhou, mas não por quanto.
:::

:::exercise level=3
Escreva um método `Optional<Product> buscar(Long id)` sobre um
`Map<Long, Product>` e depois use-o de três formas: com `orElse`, com
`orElseThrow` e com `ifPresent`.

:::answer
```java
Optional<Product> buscar(Long id) {
    return Optional.ofNullable(mapa.get(id));
}
```
`Optional.ofNullable` é a ponte entre uma API antiga que devolve `null` e o
mundo do `Optional`. Nas três formas de uso, repare que nenhuma delas obriga
um `if` explícito — e que `orElseThrow` é a única que preserva a informação
de que algo deu errado.
:::
