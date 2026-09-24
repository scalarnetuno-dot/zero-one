---
title: "Enums e records"
number: 12
part: p2
kicker: "Dois recursos que apagam código: um para o conjunto fechado, outro para o dado puro."
goal: >-
  Substituir constantes de texto por `enum`, escrever um `record` em uma linha
  e explicar por que os dois deixam o compilador trabalhar mais.
---

Este capítulo tem um efeito colateral raro: ele **apaga** código que você
escreveu nos capítulos 5 e 10. Enum e record são recursos que resolvem dois
casos tão comuns que a linguagem decidiu tratá-los com sintaxe própria.

## O problema do `String` como categoria

```java title="O que dá errado com texto solto" numbered
String status = "ATIVO";

if (status.equals("ativo")) {     // não entra: caixa diferente
    ...
}
status = "ATVIO";                 // compila. e está errado.
```

Texto aceita qualquer valor, inclusive os errados. O compilador não tem como
ajudar porque, para ele, `"ATVIO"` é um texto perfeitamente válido.

## `enum`: o conjunto fechado

```java title="Status.java" numbered
public enum Status {
    ATIVO,
    INATIVO,
    ESGOTADO
}
```

```java
Status status = Status.ATIVO;

if (status == Status.ATIVO) {      // aqui == está correto!
    System.out.println("à venda");
}
```

Três ganhos imediatos. `Status.ATVIO` **não compila**. A comparação com `==`
volta a ser segura, porque existe exatamente uma instância de cada valor. E o
`switch` passa a ser exaustivo:

```java title="O compilador cobra os casos que faltam" numbered
String rotulo = switch (status) {
    case ATIVO -> "À venda";
    case INATIVO -> "Fora de linha";
    case ESGOTADO -> "Sem estoque";
};
```

Sem `default`. Se alguém acrescentar `PRE_VENDA` ao enum amanhã, este
`switch` deixa de compilar — e o compilador aponta o lugar exato onde falta
tratar o caso novo. Isso é um erro de compilação que você **quer** ter.

:::key
Toda vez que você escreve um `if` comparando texto com uma constante, existe
um enum esperando para nascer. O sinal é claro: se o conjunto de valores é
conhecido e não muda em tempo de execução, ele é um tipo, não um texto.
:::

:::story ATVIO
O status era um texto. `"ATIVO"`, `"INATIVO"`, `"ESGOTADO"` — combinado em
reunião, escrito na ata, seguido por todo mundo.

Até a terça em que alguém cadastrou quatrocentos produtos por planilha e a
coluna saiu com `"ATVIO"`.

Nada quebrou. Nenhuma exceção, nenhum log, nenhum alerta. Os quatrocentos
produtos simplesmente pararam de aparecer na loja, porque o filtro procurava
`"ATIVO"` e eles não eram nada.

Levou onze dias para alguém perceber. Quem percebeu foi Seu Antônio, que
ligou perguntando por que a marca de fone que ele sempre comprava tinha
"saído de linha".

Na retrospectiva, Roberto sugeriu uma validação a mais na importação da
planilha. Marina sugeriu outra coisa:

— Ou a gente para de deixar o computador aceitar qualquer palavra em um campo
que só tem três valores possíveis.
:::

## Enum com dados e comportamento

Aqui está o que quase ninguém ensina: um enum é uma classe completa.

```java title="PaymentMethod.java" numbered
public enum PaymentMethod {
    PIX("Pix", 0, 0),
    BOLETO("Boleto", 3, 0),
    CARTAO("Cartão", 0, 2.99);

    private final String rotulo;
    private final int prazoDias;
    private final double taxaPercentual;

    PaymentMethod(String rotulo, int prazoDias, double taxa) {
        this.rotulo = rotulo;
        this.prazoDias = prazoDias;
        this.taxaPercentual = taxa;
    }

    public double aplicarTaxa(double valor) {
        return valor * (1 + taxaPercentual / 100);
    }

    public String getRotulo() {
        return rotulo;
    }
}
```

```java
double cobrado = PaymentMethod.CARTAO.aplicarTaxa(100);   // 102.99
```

A tabela de taxas que viveria em um `switch` de vinte linhas agora mora ao
lado de cada valor. Acrescentar um meio de pagamento é acrescentar uma linha —
e o compilador garante que ninguém esqueceu de informar a taxa.

:::compare left="Escada de if" right="Enum com dados"
if (m.equals("PIX"))
  return v;
if (m.equals("BOLETO"))
  return v;
if (m.equals("CARTAO"))
  return v * 1.0299;
---
return m.aplicarTaxa(v);
:::

:::trivia
Enums chegaram no Java 5, em 2004. Antes disso o padrão era
`public static final int ATIVO = 1;` — e isso trazia um problema divertido:
qualquer `int` servia. Uma função que esperava um status aceitava `42` sem
reclamar. O padrão tinha até nome, *Typesafe Enum Pattern*, e ocupava trinta
linhas no livro de Joshua Bloch. A linguagem incorporou o padrão inteiro em
uma palavra-chave.
:::

## `record`: o dado puro

Lembra a classe `Product` imutável do capítulo 10, com construtor, getters,
`equals`, `hashCode` e `toString`? São quarenta linhas. Agora ela é esta:

```java title="ProductResponse.java" numbered
public record ProductResponse(
        Long id,
        String nome,
        double preco,
        int estoque) {
}
```

O compilador gera automaticamente: os atributos `private final`, o construtor
com todos os campos, um método de leitura por campo (`id()`, `nome()` — sem o
prefixo `get`), `equals` e `hashCode` por conteúdo, e um `toString` legível.

```java
var p = new ProductResponse(7L, "Teclado", 349.90, 12);
System.out.println(p.nome());    // Teclado
System.out.println(p);
// ProductResponse[id=7, nome=Teclado, preco=349.9, estoque=12]
```

:::anatomy title="O que o compilador escreve para você"
lang: java
code: |
  public record ProductResponse(Long id, String nome) {
      public ProductResponse {
          if (nome == null) {
              throw new IllegalArgumentException();
          }
      }
  }
notes:
  - { line: 1, text: "Os parâmetros do record **são** os atributos: `private final` por definição." }
  - { line: 1, text: "Leitura é `p.nome()`, sem `get` — e não existe `set`: record é imutável." }
  - { line: 2, text: "Construtor **compacto**: só a validação, sem repetir as atribuições." }
  - { line: 4, text: "Validar aqui garante o mesmo do capítulo 10: o objeto nunca nasce inválido." }
:::

## Quando usar record e quando usar classe

| Use `record` | Use `class` |
|---|---|
| dado que só transporta valor | objeto com comportamento e estado que muda |
| resposta e requisição de API | entidade de banco (o JPA precisa mutar) |
| chave composta, coordenada, par | qualquer coisa que precise herdar |

Tabela: Record é para dado; classe é para objeto. Um record não pode estender
nada — por construção.

:::pitfall
Record parece a solução para tudo e não serve para entidade JPA. O Hibernate
(capítulo 20) precisa de um construtor vazio e de setters para acompanhar
mudanças — um record não tem nenhum dos dois. Por isso o projeto vai usar
**classe** para `Product` (a entidade) e **record** para `ProductRequest` e
`ProductResponse` (os DTOs do capítulo 24).
:::

## Os dois juntos, como o projeto vai usar

```java title="Um recorte do capítulo 24" numbered
public record ProductResponse(
        Long id,
        String nome,
        double preco,
        Status status,
        PaymentMethod pagamentoPreferido) {
}
```

O JSON que o cliente recebe vai sair exatamente com esses campos — e o enum
vira texto na serialização, sem que você escreva uma linha de conversão. Este
é o formato da resposta que abriu o capítulo 1.

:::summary
- `enum` é conjunto fechado: erro de digitação não compila e `switch` fica
  exaustivo.
- Enum pode ter atributos, construtor e métodos: a tabela mora ao lado do
  valor.
- `record` gera construtor, leitores, `equals`, `hashCode` e `toString`.
- Record é imutável e não herda — perfeito para DTO, inadequado para entidade
  JPA.
:::

:::checkpoint
Você troca constantes de texto por enum, escreve um enum com dados e
comportamento, declara records e sabe quando não usá-los.
:::

:::milestone
O vocabulário do projeto está completo: `Product` (classe), `Status` e
`PaymentMethod` (enums), `ProductResponse` (record). Falta o que fazer quando
algo dá errado — o próximo capítulo.
:::

:::exercise level=1
Substitua a escada de notas do capítulo 5 por um `enum Conceito` com
`EXCELENTE`, `BOM`, `REGULAR` e `INSUFICIENTE`, e um método estático
`de(double nota)` que devolva o conceito.

:::answer
```java
public enum Conceito {
    EXCELENTE, BOM, REGULAR, INSUFICIENTE;

    public static Conceito de(double nota) {
        if (nota >= 9) return EXCELENTE;
        if (nota >= 7) return BOM;
        if (nota >= 5) return REGULAR;
        return INSUFICIENTE;
    }
}
```
A escada continua existindo, mas agora mora dentro do tipo que ela produz — e
só existe em um lugar do sistema.
:::

:::exercise level=2
Escreva `record Money(BigDecimal valor, String moeda)` com validação no
construtor compacto: valor não pode ser nulo nem negativo, e a moeda precisa
ter três letras.

:::answer
```java
public record Money(BigDecimal valor, String moeda) {
    public Money {
        if (valor == null || valor.signum() < 0) {
            throw new IllegalArgumentException("valor inválido");
        }
        if (moeda == null || moeda.length() != 3) {
            throw new IllegalArgumentException("moeda inválida");
        }
    }
}
```
:::

:::exercise level=3
Acrescente ao `enum PaymentMethod` um método `prazoEmDiasUteis()` e descubra
sozinho o que acontece se você chamar `values()` — e para que isso serve em
uma API.

:::answer
`PaymentMethod.values()` devolve um array com todos os valores, na ordem de
declaração. Em uma API isso permite responder `GET /payment-methods`
listando as opções disponíveis sem manter uma segunda lista em lugar
nenhum — a fonte da verdade é o próprio enum.
:::
