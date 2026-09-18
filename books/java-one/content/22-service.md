---
title: "Service"
number: 22
part: p4
kicker: "A camada onde mora a regra. Se ela estiver vazia, a regra está espalhada em outro lugar — e você vai encontrá-la do jeito difícil."
goal: >-
  Mover a regra de negócio do controlador para um serviço, injetar o
  repositório por construtor e usar `@Transactional` sabendo o que ele faz.
---

O controlador do capítulo 17 sabia HTTP **e** sabia regras. Enquanto a regra é
"guarde no mapa", isso passa. Quando ela vira "não deixe cadastrar dois
produtos com o mesmo nome, e ao baixar o estoque marque como esgotado se
chegar a zero", o controlador deixa de ser um tradutor e passa a ser o sistema
inteiro.

## As três responsabilidades, separadas

:::diagram type="blocks" caption="Cada camada só conhece a de baixo — e só faz uma coisa."
rows:
  - [{ text: "Controller", note: "HTTP: caminho, status, JSON" }]
  - [{ text: "Service", note: "regra de negócio e transação" }]
  - [{ text: "Repository", note: "consulta e gravação" }]
:::

| Camada | Sabe | Não sabe |
|---|---|---|
| Controller | verbo, caminho, status | regra, banco |
| Service | regra, ordem das operações | HTTP, JSON |
| Repository | SQL, entidade | regra, HTTP |

Tabela: O teste de cheiro: se o `Service` importa algo de `http`, a separação
foi rompida.

:::key
O `Service` não deve ter nenhum `import` de `org.springframework.http` nem de
`jakarta.servlet`. Se tiver, a regra de negócio passou a depender do protocolo
— e testá-la vai exigir subir um servidor.
:::

## O serviço

```java title="ProductService.java" numbered
package com.loja.catalog.product;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ProductService {

    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }

    @Transactional(readOnly = true)
    public List<Product> listar() {
        return repository.findAll();
    }

    @Transactional(readOnly = true)
    public Product buscar(Long id) {
        return repository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException(id));
    }

    @Transactional
    public Product criar(Product novo) {
        if (repository.existsByNameIgnoreCase(novo.getName())) {
            throw new DuplicateProductException(novo.getName());
        }
        return repository.save(novo);
    }

    @Transactional
    public Product atualizar(Long id, Product dados) {
        Product atual = buscar(id);
        atual.setName(dados.getName());
        atual.setDescription(dados.getDescription());
        atual.setPrice(dados.getPrice());
        atual.setQuantity(dados.getQuantity());
        return atual;          // sem save: entidade gerenciada
    }

    @Transactional
    public void apagar(Long id) {
        Product atual = buscar(id);
        repository.delete(atual);
    }
}
```

Cinco métodos e quatro decisões que valem explicação.

:::anatomy title="As decisões escondidas em cinco métodos"
lang: java
code: |
  @Transactional(readOnly = true)
  public Product buscar(Long id) {
      return repository.findById(id)
              .orElseThrow(() ->
                  new ProductNotFoundException(id));
  }

  @Transactional
  public Product atualizar(Long id, Product dados) {
      Product atual = buscar(id);
      atual.setPrice(dados.getPrice());
      return atual;
  }
notes:
  - { line: 1, text: "`readOnly = true` avisa o banco que não haverá escrita: permite otimização." }
  - { line: 4, text: "`orElseThrow` transforma ausência em exceção com nome — o capítulo 26 a converte em `404`." }
  - { line: 10, text: "Reusa `buscar`: a regra do \"não existe\" vive em um lugar só." }
  - { line: 12, text: "Sem `save`: a entidade está gerenciada e o `UPDATE` sai no fim da transação." }
:::

## `@Transactional`: o que essa anotação realmente faz

Ela envolve o método em uma transação de banco: abre antes, confirma
(`commit`) se terminar bem, desfaz (`rollback`) se escapar uma exceção.

:::diagram type="sequence" caption="O Spring intercepta a chamada e cuida do começo e do fim."
actors:
  - { id: c, name: "Controller" }
  - { id: p, name: "Proxy" }
  - { id: s, name: "Service" }
  - { id: d, name: "Banco" }
messages:
  - { from: c, to: p, text: "criar(produto)" }
  - { from: p, to: d, text: "BEGIN" }
  - { from: p, to: s, text: "criar(produto)" }
  - { from: s, to: d, text: "INSERT" }
  - { from: s, to: p, text: "retorna", dashed: true }
  - { from: p, to: d, text: "COMMIT" }
  - { from: p, to: c, text: "produto salvo", dashed: true }
:::

Repare no **proxy**. O Spring não modifica o seu método: ele cria um objeto
que envolve o seu serviço e intercepta a chamada. Isso explica as duas
pegadinhas mais comuns da anotação.

:::pitfall
**Chamada interna não passa pelo proxy.** Se `criar()` chama `this.validar()`
e só `validar()` tem `@Transactional`, a anotação é ignorada — a chamada não
saiu do objeto, então o proxy não viu nada. A solução é colocar a transação no
método público que inicia a operação.
:::

:::pitfall
**Só exceção *unchecked* desfaz a transação, por padrão.** Uma `IOException`
(checked) escapando de um método `@Transactional` faz o Spring confirmar a
transação de qualquer jeito. Para mudar:
`@Transactional(rollbackFor = Exception.class)`.
:::

:::story A transação que não existia
A baixa de estoque funcionava. Menos quando não funcionava.

Uma vez a cada duzentas, o produto saía do estoque e o pedido não era
gravado. O cliente pagava, o item sumia da prateleira e o pedido não existia
em lugar nenhum.

Carlos tinha colocado `@Transactional` no método. Estava lá, escrito,
visível, com a importação correta.

Marina abriu o arquivo e apontou a linha 61: o método público chamava
`this.baixarEProcessar()`, um método privado da mesma classe — que era onde
a anotação estava.

— A anotação não é uma promessa que o método faz — ela disse. — É uma
promessa que alguém faz *em volta* dele. Se a chamada não sai do objeto,
não existe ninguém em volta.

Carlos passou o resto do dia entendendo o que é um proxy. Foi a tarde mais
útil daquele mês.
:::

:::art caption="A anotação não altera o método: ela altera quem chama o método."
src="a-anotacao-nao-altera-o-metodo-ela-altera-quem-chama-o-metodo.png"
Charge editorial minimalista: dois bonecos geométricos representando objetos.
Um deles está dentro de uma bolha transparente rotulada "PROXY"; uma seta
vinda de fora atravessa a bolha e é interceptada por ela, ganhando um pequeno
carimbo. Outra seta, que nasce dentro do próprio boneco e volta para ele
mesmo, passa por dentro sem tocar a bolha e sem carimbo. Ao lado, um
desenvolvedor jovem observa com expressão de quem acabou de entender algo.
Fundo branco, poucos elementos, composição limpa, estética editorial de
tecnologia.
:::

## As exceções de negócio

```java title="ProductNotFoundException.java" numbered
package com.loja.catalog.product;

public class ProductNotFoundException extends RuntimeException {
    public ProductNotFoundException(Long id) {
        super("produto não encontrado: " + id);
    }
}
```

```java title="DuplicateProductException.java" numbered
public class DuplicateProductException extends RuntimeException {
    public DuplicateProductException(String name) {
        super("já existe produto com o nome: " + name);
    }
}
```

Duas classes de cinco linhas. Elas não sabem nada de HTTP — e é exatamente por
isso que o serviço pode lançá-las. No capítulo 26, um tradutor central
converte a primeira em `404` e a segunda em `409`.

## A regra de negócio de verdade

Até aqui o serviço só orquestra. A regra aparece quando o negócio tem uma
decisão:

```java title="Uma operação com regra" numbered
@Transactional
public Product baixarEstoque(Long id, int quantidade) {
    Product produto = buscar(id);

    if (quantidade <= 0) {
        throw new IllegalArgumentException("quantidade inválida");
    }
    if (produto.getQuantity() < quantidade) {
        throw new InsufficientStockException(
                produto.getQuantity(), quantidade);
    }

    produto.setQuantity(produto.getQuantity() - quantidade);
    if (produto.getQuantity() == 0) {
        produto.setStatus(Status.ESGOTADO);
    }
    return produto;
}
```

Essa é a camada que justifica a arquitetura. Repare que a regra "estoque zero
vira esgotado" existe em **um** lugar. Se ela morasse no controlador, cada
endpoint novo que baixasse estoque precisaria repeti-la — e um deles
esqueceria.

:::tip
Um serviço bem escrito lê como a descrição do negócio: buscar, validar,
alterar, decidir. Se ao ler em voz alta você ouve "pega a requisição, extrai o
parâmetro, monta o JSON", o código está na camada errada.
:::

## O controlador, agora magro

```java title="ProductController.java (só o que é dele)" numbered
@RestController
@RequestMapping("/products")
public class ProductController {

    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @GetMapping("/{id}")
    public Product buscar(@PathVariable Long id) {
        return service.buscar(id);
    }
}
```

Quatro linhas úteis por endpoint. O controlador virou o que deveria ser: um
tradutor entre HTTP e chamada de método.

:::compare left="Antes (cap. 17)" right="Depois"
@GetMapping("/{id}")
Product buscar(
    @PathVariable Long id) {
  Product p =
      banco.get(id);
  if (p == null) {
    return null;
  }
  return p;
}
---
@GetMapping("/{id}")
Product buscar(
    @PathVariable Long id) {
  return service.buscar(id);
}
:::

:::summary
- Controller traduz HTTP; Service decide; Repository persiste.
- O serviço não importa nada de HTTP — é isso que o mantém testável.
- `@Transactional` abre e fecha transação por meio de um proxy: chamada
  interna não conta.
- Exceção *checked* escapando não desfaz a transação por padrão.
- Dentro da transação, alterar entidade gerenciada dispensa `save`.
:::

:::checkpoint
Você move a regra para o serviço, injeta o repositório por construtor, usa
`@Transactional` sabendo o que ele faz e lança exceções de negócio sem
mencionar HTTP.
:::

:::milestone
O defeito número dois do capítulo 17 está resolvido: a regra saiu do
controlador. A API tem três camadas e uma regra de estoque que vive em um
lugar só.
:::

:::exercise level=1
Escreva `CategoryService` com `listar`, `buscar` e `criar`, recusando nome
duplicado.

:::answer
```java
@Service
public class CategoryService {
    private final CategoryRepository repository;

    public CategoryService(CategoryRepository repository) {
        this.repository = repository;
    }

    @Transactional
    public Category criar(Category nova) {
        repository.findByNameIgnoreCase(nova.getName())
                .ifPresent(c -> {
                    throw new DuplicateCategoryException(c.getName());
                });
        return repository.save(nova);
    }
}
```
:::

:::exercise level=2
Acrescente `reajustar(Long id, BigDecimal percentual)` ao `ProductService`,
recusando reajuste que leve o preço a zero ou menos.

:::answer
```java
@Transactional
public Product reajustar(Long id, BigDecimal percentual) {
    Product p = buscar(id);
    BigDecimal fator = BigDecimal.ONE
            .add(percentual.divide(new BigDecimal("100")));
    BigDecimal novo = p.getPrice().multiply(fator);
    if (novo.signum() <= 0) {
        throw new IllegalArgumentException("reajuste inválido");
    }
    p.setPrice(novo.setScale(2, RoundingMode.HALF_UP));
    return p;
}
```
Aquele `setScale` com `HALF_UP` no fim não é detalhe: sem ele, o resultado da
multiplicação carrega casas decimais que o banco vai truncar do jeito dele.
Arredondamento é decisão de negócio, não do driver.
:::

:::exercise level=3
Imagine que criar um produto deva também registrar um evento em uma tabela de
auditoria. Escreva o método e explique o que acontece se a gravação da
auditoria falhar.

:::answer
```java
@Transactional
public Product criar(Product novo) {
    Product salvo = repository.save(novo);
    auditoria.registrar("CREATE", salvo.getId());
    return salvo;
}
```
Se a auditoria lançar uma exceção *unchecked*, a transação desfaz **as duas**
operações: o produto não é criado. Isso pode ser o comportamento desejado ou
um desastre (perder a venda porque o log falhou). É uma decisão de negócio, e
a forma de separá-las é publicar um evento e tratá-lo em outra transação —
assunto que este livro deixa como próximo passo.
:::
