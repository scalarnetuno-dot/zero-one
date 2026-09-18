---
title: "Testando services"
number: 35
part: p8
kicker: "Para testar a regra, o banco precisa sair do caminho — e alguém precisa fingir ser ele."
goal: >-
  Isolar o serviço com Mockito, verificar chamadas com `verify`, e reconhecer
  quando um mock deixou de ajudar e passou a testar a si mesmo.
---

O `ProductService` do capítulo 22 depende do `ProductRepository`. Testá-lo
com banco de verdade é lento e frágil; testá-lo sem nada é impossível. A
saída é entregar a ele um repositório **falso**, que faz o que o teste mandar.

E isso só é possível por causa de uma decisão do capítulo 15: injeção por
construtor.

## O mock

```java title="ProductServiceTest.java" numbered
@ExtendWith(MockitoExtension.class)
class ProductServiceTest {

    @Mock
    ProductRepository repository;

    @InjectMocks
    ProductService service;

    @Test
    void deveLancarQuandoProdutoNaoExiste() {
        when(repository.findById(99L))
                .thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.buscar(99L))
                .isInstanceOf(ProductNotFoundException.class)
                .hasMessageContaining("99");
    }
}
```

:::anatomy title="As quatro peças de um teste com mock"
lang: java
code: |
  @ExtendWith(MockitoExtension.class)
  class ProductServiceTest {

      @Mock
      ProductRepository repository;

      @InjectMocks
      ProductService service;

      @Test
      void deveLancarQuandoNaoExiste() {
          when(repository.findById(99L))
                  .thenReturn(Optional.empty());
          ...
      }
  }
notes:
  - { line: 1, text: "A extensão do Mockito processa as anotações. Nenhum Spring é carregado." }
  - { line: 4, text: "`@Mock` cria um dublê: todo método devolve vazio ou nulo até você ensinar." }
  - { line: 7, text: "`@InjectMocks` monta o serviço com os mocks — pelo construtor." }
  - { line: 12, text: "`when(...).thenReturn(...)` ensina o dublê a responder naquele caso." }
:::

:::key
Note o que este teste **não** faz: não sobe o Spring, não abre conexão, não
toca em banco. Ele roda em milissegundos e testa exatamente uma coisa — que
o serviço transforma "não achei" em `ProductNotFoundException`.
:::

## Verificando o que foi chamado

```java title="Às vezes o que importa é o efeito" numbered
@Test
void deveSalvarProdutoNovo() {
    var dados = new ProductRequest("Teclado", null,
            new BigDecimal("349.90"), 12);

    when(repository.existsByNameIgnoreCase("Teclado"))
            .thenReturn(false);
    when(repository.save(any(Product.class)))
            .thenAnswer(inv -> inv.getArgument(0));

    service.criar(dados);

    ArgumentCaptor<Product> captor =
            ArgumentCaptor.forClass(Product.class);
    verify(repository).save(captor.capture());

    assertThat(captor.getValue().getName())
            .isEqualTo("Teclado");
    assertThat(captor.getValue().getStatus())
            .isEqualTo(Status.ATIVO);
}
```

O `ArgumentCaptor` guarda o objeto que o serviço passou ao repositório — é
como você verifica **o que** seria salvo sem salvar nada.

```java title="E o que não deve acontecer" numbered
@Test
void naoDeveSalvarQuandoNomeDuplicado() {
    when(repository.existsByNameIgnoreCase("Teclado"))
            .thenReturn(true);

    assertThatThrownBy(() -> service.criar(dados))
            .isInstanceOf(DuplicateProductException.class);

    verify(repository, never()).save(any());
}
```

`verify(..., never())` é frequentemente mais valioso que o `assert`: ele
prova que a operação foi **abortada antes** de tocar no banco.

## O vocabulário mínimo do Mockito

| Comando | Para quê |
|---|---|
| `when(x).thenReturn(y)` | ensina a resposta |
| `when(x).thenThrow(e)` | ensina a falhar |
| `verify(mock).metodo()` | confirma que foi chamado |
| `verify(mock, never())` | confirma que **não** foi |
| `verify(mock, times(2))` | confirma quantas vezes |
| `any()`, `eq(valor)` | casa argumentos |
| `ArgumentCaptor` | captura o que foi passado |

Tabela: Sete construções resolvem 95% dos testes de serviço.

:::pitfall
`when(repository.save(any()))` sem `thenReturn` devolve `null`. Se o serviço
usar o retorno (`return repository.save(p).getId()`), o teste falha com
`NullPointerException` — e a culpa não é do código, é do mock mal ensinado.
Quando o retorno importa, use
`thenAnswer(inv -> inv.getArgument(0))` para devolver o próprio objeto.
:::

## Quando o mock passa a atrapalhar

:::story O teste que testava o mock
O teste tinha noventa linhas e sete mocks.

Ele verificava que o serviço chamava o repositório, que chamava o mapeador,
que chamava o validador, que chamava o publicador de evento — cada um deles
ensinado a responder exatamente o que o serviço esperava.

Passava sempre. Passou inclusive na semana em que o cálculo do total do
pedido estava errado por um centavo, porque o mock do mapeador devolvia um
valor fixo que ninguém tinha atualizado.

— Esse teste não testa o serviço — disse Marina, na revisão. — Ele testa a
minha capacidade de prever o que o serviço vai chamar. Se eu mudar a ordem
das chamadas sem mudar o resultado, ele quebra. Se eu quebrar o resultado sem
mudar a ordem, ele passa.

Carlos perguntou o que fazer.

— Quando o teste tem mais mock do que asserção, o problema não é o teste. É a
classe, que depende de coisa demais.

O `OrderService` virou dois: um que calcula e não depende de nada, e um que
orquestra. O primeiro ganhou doze testes sem nenhum mock. O segundo ficou com
dois.
:::

:::art caption="Quando o teste tem mais dublês que atores, ele virou ensaio."
src="quando-o-teste-tem-mais-dubles-que-atores-ele-virou-ensaio.png"
Charge editorial minimalista: palco de teatro visto de frente, com um único
ator real no centro e sete manequins de madeira posicionados ao redor, cada
um com uma plaquinha pendurada no pescoço: "repositório", "mapeador",
"validador". Na plateia, uma única pessoa aplaude com cara de dúvida. Fundo
branco, poucos elementos, humor visual seco, estética editorial de
tecnologia.
:::

:::pitfall
Três sinais de que o mock virou problema: o teste tem mais linhas de `when`
do que de `assertThat`; o teste quebra quando você refatora sem mudar o
comportamento; o teste passa quando o resultado está errado. Qualquer um dos
três é um pedido para dividir a classe.
:::

## A alternativa: o dublê escrito à mão

```java title="Um repositório falso, de verdade" numbered
class InMemoryProductRepository implements ProductRepository {

    private final Map<Long, Product> dados = new HashMap<>();
    private long sequencia = 0;

    @Override
    public <S extends Product> S save(S p) {
        if (p.getId() == null) {
            p.setId(++sequencia);
        }
        dados.put(p.getId(), p);
        return p;
    }

    @Override
    public Optional<Product> findById(Long id) {
        return Optional.ofNullable(dados.get(id));
    }

    // ... o resto da interface
}
```

Este é exatamente o `Map` do capítulo 8, agora cumprindo um contrato. A
vantagem sobre o mock é que ele **se comporta**: salvar e depois buscar
devolve o que foi salvo, sem ninguém ensinar. A desvantagem é que
`JpaRepository` tem dezenas de métodos para implementar.

:::tip
O meio-termo prático: declare uma interface menor, só com os métodos que o
serviço usa (`ProductGateway`, com quatro métodos), e faça o
`ProductRepository` estendê-la. O teste implementa a interface pequena; a
produção usa o Spring Data. É a lição do capítulo 11 — dependa do contrato —
aplicada ao teste.
:::

:::summary
- Injeção por construtor é o que torna o serviço testável sem framework.
- `@Mock` + `@InjectMocks` montam o cenário; `when` ensina; `verify`
  confirma.
- `verify(never())` prova que a operação foi abortada antes do banco.
- Mock demais testa a previsão do autor, não o comportamento.
- Dublê escrito à mão se comporta; mock apenas responde.
:::

:::checkpoint
Você isola o serviço com Mockito, ensina respostas, captura argumentos,
verifica ausência de chamada e reconhece quando o excesso de mock é sintoma
de uma classe fazendo demais.
:::

:::milestone
A regra de negócio do projeto tem testes rápidos e independentes de
infraestrutura. Falta provar que o HTTP — caminho, status e JSON — continua
sendo o combinado.
:::

:::exercise level=1
Escreva o teste de `apagar` verificando que o repositório recebeu `delete`
com o produto correto.

:::answer
```java
when(repository.findById(1L))
        .thenReturn(Optional.of(produto));

service.apagar(1L);

verify(repository).delete(produto);
```
:::

:::exercise level=2
Teste `baixarEstoque` para o caso de estoque insuficiente. Verifique a
exceção **e** que nada foi salvo.

:::answer
A segunda verificação é a que importa: sem ela, o teste passaria mesmo que o
serviço lançasse a exceção **depois** de gravar a baixa. Exceção correta com
efeito colateral errado é um defeito que só aparece em produção.
:::

:::exercise level=3
Pegue um teste seu com quatro ou mais mocks e tente reescrevê-lo dividindo a
classe testada. Compare o antes e o depois.

:::answer
Na maioria dos casos aparece uma classe pura — de cálculo, de decisão, de
transformação — que não depende de nada e ganha testes triviais. O que sobra
na classe original é orquestração, e orquestração se testa com poucos
`verify`. A qualidade do teste é um termômetro do desenho do código: teste
difícil quase nunca é problema do teste.
:::
