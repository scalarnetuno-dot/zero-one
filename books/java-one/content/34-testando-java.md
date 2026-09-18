---
title: "Testando Java"
number: 34
part: p8
kicker: "Teste não é sobre provar que funciona. É sobre poder mexer no código sem medo na sexta-feira."
goal: >-
  Escrever testes com JUnit 5 e AssertJ, nomear um teste de forma que ele
  documente a regra, e saber o que não vale a pena testar.
---

A API está pronta e ninguém nunca a testou de verdade. Toda validação até
aqui foi um `curl` digitado à mão, olhando a resposta e decidindo, no olho,
se estava certa.

Isso funciona uma vez. O problema é a segunda.

## O que um teste compra

:::key
Teste não prova que o código está certo — prova que ele continua fazendo o
que fazia quando você escreveu o teste. O valor não está em achar o bug de
hoje: está em **avisar amanhã** que alguém quebrou a regra de anteontem.
:::

## O primeiro teste

```java title="src/test/java/.../ProductTest.java" numbered
package com.loja.catalog.product;

import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.*;

class ProductTest {

    @Test
    void naoDeveAceitarPrecoNegativo() {
        assertThatThrownBy(() ->
                new Product("Teclado",
                        new BigDecimal("-10"), 5))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("preço");
    }

    @Test
    void deveBaixarEstoqueEMarcarEsgotado() {
        Product p = new Product("Teclado",
                new BigDecimal("349.90"), 3);

        p.baixarEstoque(3);

        assertThat(p.getQuantity()).isZero();
        assertThat(p.getStatus()).isEqualTo(Status.ESGOTADO);
    }
}
```

```bash
./mvnw test
```

```text title="Saída"
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

:::anatomy title="A anatomia de um teste, em três atos"
lang: java
code: |
  @Test
  void deveBaixarEstoqueEMarcarEsgotado() {
      Product p = new Product("Teclado",
              new BigDecimal("349.90"), 3);

      p.baixarEstoque(3);

      assertThat(p.getStatus())
              .isEqualTo(Status.ESGOTADO);
  }
notes:
  - { line: 1, text: "`@Test` marca o método. Ele não precisa ser público desde o JUnit 5." }
  - { line: 2, text: "O **nome** é a documentação: descreve a regra, não o método testado." }
  - { line: 3, text: "**Arrange**: monta o cenário. Só o que o teste precisa, nada além." }
  - { line: 6, text: "**Act**: uma linha. Se forem três, o teste está verificando três coisas." }
  - { line: 8, text: "**Assert**: o que deveria ter acontecido, escrito como afirmação." }
:::

## AssertJ: a afirmação que se lê

```java title="A mesma verificação, duas bibliotecas" numbered
// JUnit puro
assertEquals(Status.ESGOTADO, p.getStatus());

// AssertJ
assertThat(p.getStatus()).isEqualTo(Status.ESGOTADO);
```

A segunda forma tem duas vantagens práticas: lê-se na ordem natural
("afirmo que o status é igual a esgotado") e o autocompletar da IDE mostra
todas as verificações possíveis para aquele tipo depois do ponto. O
`spring-boot-starter-test` já traz AssertJ — não há o que instalar.

```java title="As afirmações que você vai usar" numbered
assertThat(valor).isEqualTo(esperado);
assertThat(lista).hasSize(3).contains(item);
assertThat(lista).isEmpty();
assertThat(texto).startsWith("Tec").containsIgnoringCase("MECÂNICO");
assertThat(numero).isPositive().isLessThan(100);
assertThat(optional).isPresent().get()
        .extracting(Product::getName).isEqualTo("Teclado");
assertThatThrownBy(() -> metodo())
        .isInstanceOf(IllegalStateException.class);
```

## O nome do teste é a especificação

:::compare left="Nome que não ajuda" right="Nome que documenta"
@Test
void testBaixarEstoque() {
  ...
}

@Test
void test2() {
  ...
}
---
@Test
void deveRecusarBaixaMaior
QueOEstoque() {
  ...
}
:::

Quando um teste quebra em uma sexta-feira, a única coisa que aparece no
terminal é o nome dele. `test2 failed` obriga você a abrir o arquivo;
`deveRecusarBaixaMaiorQueOEstoque failed` já contou o que se perdeu.

:::tip
Um padrão de nomes que envelhece bem: **deve** + o comportamento esperado +
**quando** + a condição. `deveMarcarEsgotadoQuandoEstoqueChegaAZero`. Fica
longo e não tem problema: nome de teste não é digitado duas vezes.
:::

## Organizando: `@Nested` e `@DisplayName`

```java title="Testes agrupados por comportamento" numbered
@DisplayName("Produto")
class ProductTest {

    @Nested
    @DisplayName("ao baixar estoque")
    class BaixarEstoque {

        @Test
        @DisplayName("marca como esgotado ao chegar a zero")
        void esgotado() { ... }

        @Test
        @DisplayName("recusa quantidade maior que o disponível")
        void recusaExcesso() { ... }
    }
}
```

O relatório passa a se ler como uma especificação:

```text
Produto
  ao baixar estoque
    ✔ marca como esgotado ao chegar a zero
    ✔ recusa quantidade maior que o disponível
```

## Casos repetidos: `@ParameterizedTest`

```java title="Um teste, cinco cenários" numbered
@ParameterizedTest
@ValueSource(strings = {"", " ", "   "})
void naoDeveAceitarNomeEmBranco(String nome) {
    assertThatThrownBy(() ->
            new Product(nome, BigDecimal.TEN, 1))
            .isInstanceOf(IllegalArgumentException.class);
}

@ParameterizedTest
@CsvSource({
    "10, 3, 7",
    "3,  3, 0",
    "1,  1, 0"
})
void deveSubtrairDoEstoque(int inicial, int baixa, int esperado) {
    Product p = new Product("X", BigDecimal.TEN, inicial);
    p.baixarEstoque(baixa);
    assertThat(p.getQuantity()).isEqualTo(esperado);
}
```

## O que não testar

:::pitfall
Não teste getter, setter, construtor trivial nem framework. Um teste que
verifica se `getName()` devolve o nome não protege contra nada e precisa ser
mantido para sempre. Teste **decisão**: `if`, cálculo, validação,
transformação. Onde não há decisão, não há o que quebrar.
:::

| Vale testar | Não vale |
|---|---|
| regra de negócio | getter e setter |
| cálculo e arredondamento | mapeamento de DTO trivial |
| validação e exceção | configuração do framework |
| caso-limite (zero, vazio, nulo) | biblioteca de terceiros |

Tabela: A pergunta é sempre a mesma: *se isto quebrar, alguém percebe?*

## Cobertura: um número que engana

```bash
./mvnw verify   # com o plugin JaCoCo configurado
```

Cobertura mede **linhas executadas** pelos testes, não regras verificadas. Um
teste que chama o método e não afirma nada dá 100% de cobertura e zero de
garantia.

:::trivia
A meta de "80% de cobertura" é provavelmente a métrica mais distorcida da
engenharia de software. Ela nasceu como observação empírica e virou meta — e
toda métrica que vira meta deixa de ser métrica. O sintoma clássico: testes
escritos para cobrir linhas, com `assertTrue(true)` no fim, aprovados porque
o número subiu.
:::

:::story Testar não atrasa?
— Quanto tempo leva escrever esses testes? — perguntou Roberto.

— Uns trinta por cento a mais no começo.

Roberto anotou. Trinta por cento a mais é, na planilha dele, trinta por cento
a mais.

Marina esperou um pouco e devolveu a pergunta na moeda que ele entendia:

— Quantas horas a gente gastou no mês passado corrigindo coisa que já tinha
funcionado antes?

Roberto não sabia. Foi olhar. Voltou no dia seguinte com um número que ele
mesmo tinha somado dos chamados: sessenta e dois por cento do tempo da
equipe.

Não virou regra imediatamente. Virou depois do incidente do capítulo 33 —
quando um teste de quatro linhas teria impedido trinta e uma pessoas de
poderem apagar o catálogo.
:::

:::art caption="O tempo que o teste custa é sempre menor que o tempo que ele evita."
src="o-tempo-que-o-teste-custa-e-sempre-menor-que-o-tempo-que-ele-evita.png"
Charge editorial minimalista: balança de dois pratos. No prato esquerdo, uma
pequena pilha de folhas rotulada "escrever testes". No prato direito, uma
montanha enorme de papéis de chamado, um telefone tocando e um pequeno
incêndio. A balança pende dramaticamente para a direita. Ao lado, um gerente
de camisa social observa a balança com uma planilha na mão. Fundo branco,
poucos elementos, humor visual seco, estética editorial de tecnologia.
:::

:::summary
- Teste protege o futuro, não o presente: ele avisa quando alguém quebra a
  regra.
- Arrange, act, assert — e o nome do método é a documentação.
- AssertJ lê-se na ordem natural e descobre-se pelo autocompletar.
- `@ParameterizedTest` troca cinco testes iguais por um com cinco entradas.
- Teste decisão; não teste getter nem framework. Cobertura alta não é
  garantia.
:::

:::checkpoint
Você escreve testes de unidade com JUnit e AssertJ, nomeia de forma que o
relatório documente a regra, usa testes parametrizados e sabe o que deixar de
fora.
:::

:::milestone
As regras de `Product` estão cobertas por testes que rodam em milissegundos,
sem banco e sem Spring. O próximo capítulo testa o serviço — que tem
dependências.
:::

:::exercise level=1
Escreva três testes para `baixarEstoque`: sucesso, quantidade zero e
quantidade maior que o estoque.

:::answer
O terceiro é o mais valioso: ele verifica que a exceção certa é lançada.
Testar o caminho feliz prova que o código funciona; testar o caminho
recusado prova que ele **protege**.
:::

:::exercise level=2
Converta os três testes acima em um `@ParameterizedTest` com `@CsvSource`.
Depois decida se ficou melhor ou pior e justifique.

:::answer
Melhor para os casos de cálculo, que variam só nos números. Pior para os
casos de exceção, que verificam tipos diferentes — forçá-los na mesma tabela
exige uma coluna com o nome da exceção, e o teste passa a ter um `if`. Teste
com `if` dentro é um teste que precisa de teste.
:::

:::exercise level=3
Escreva um teste que falhe de propósito e leia a saída do AssertJ com
atenção. Depois faça o mesmo com `assertEquals` do JUnit e compare as
mensagens.

:::answer
O AssertJ mostra o esperado e o obtido em blocos separados, com destaque para
a diferença; em coleções, aponta os elementos faltantes e sobrando. A
qualidade da mensagem de falha é a razão prática de preferi-lo — porque a
mensagem é lida em um momento de pressa, quase sempre com o build vermelho.
:::
