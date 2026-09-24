---
title: "Testando o banco"
number: 37
part: p8
kicker: "Testar contra um banco diferente do de produção é ensaiar a peça em outro teatro."
goal: >-
  Testar repositórios com `@DataJpaTest`, subir um PostgreSQL de verdade no
  teste com Testcontainers e entender por que o H2 engana.
---

O repositório é a única camada que os dois capítulos anteriores não tocaram —
e é onde mora o SQL, o mapeamento, a restrição de unicidade e a chave
estrangeira. Nada disso é exercitado por mock.

## `@DataJpaTest`

```java title="ProductRepositoryTest.java" numbered
@DataJpaTest
class ProductRepositoryTest {

    @Autowired ProductRepository repository;
    @Autowired TestEntityManager em;

    @Test
    void deveBuscarPorNomeIgnorandoCaixa() {
        em.persist(new Product("Teclado Mecânico",
                new BigDecimal("349.90"), 12));
        em.flush();

        var achados = repository
                .findByNameContainingIgnoreCase("mecânico",
                        Pageable.unpaged());

        assertThat(achados).hasSize(1);
    }

    @Test
    void naoDeveAceitarNomeDuplicado() {
        em.persist(new Product("Cabo", BigDecimal.TEN, 1));
        em.flush();

        assertThatThrownBy(() -> {
            em.persist(new Product("Cabo", BigDecimal.TEN, 1));
            em.flush();
        }).isInstanceOf(PersistenceException.class);
    }
}
```

:::anatomy title="O que `@DataJpaTest` faz por você"
lang: java
code: |
  @DataJpaTest
  class ProductRepositoryTest {

      @Autowired ProductRepository repository;
      @Autowired TestEntityManager em;
  }
notes:
  - { line: 1, text: "Sobe só JPA, Hibernate e os repositórios — sem controlador, sem serviço." }
  - { line: 1, text: "Cada teste roda em uma transação que é **desfeita** no fim: os testes não sujam uns aos outros." }
  - { line: 4, text: "`TestEntityManager` grava direto, sem passar pelo repositório que você está testando." }
:::

:::key
Preparar o cenário com `TestEntityManager` em vez de `repository.save()` não
é preciosismo: se o `save` estiver quebrado, o teste que usa `save` para
montar o cenário falha por um motivo e você procura por outro.
:::

## O problema do H2

Por padrão, `@DataJpaTest` substitui o seu banco por um em memória — o H2, se
ele estiver no classpath. É rápido, não exige nada instalado e mente.

| O que muda | H2 | PostgreSQL |
|---|---|---|
| `unaccent`, `pg_trgm` | não existem | existem |
| Tipo `jsonb`, array | não | sim |
| Comportamento de `LIKE` | outro | o seu |
| Palavra reservada | outra lista | a sua lista |
| Precisão de `NUMERIC` | diferente | a sua |

Tabela: Cada linha é um teste que passa no H2 e falha em produção.

:::pitfall
"No H2 passava" é uma frase que só aparece **depois** do deploy. O H2 é um
banco diferente, com dialeto diferente e comportamento diferente em
exatamente os pontos que costumam dar problema. Se você usa PostgreSQL em
produção, teste em PostgreSQL.
:::

## Testcontainers: o banco de verdade, descartável

```xml title="pom.xml"
<dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>postgresql</artifactId>
    <scope>test</scope>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-testcontainers</artifactId>
    <scope>test</scope>
</dependency>
```

```java title="Uma classe-base para os testes de dados" numbered
@DataJpaTest
@AutoConfigureTestDatabase(replace = Replace.NONE)
@Testcontainers
abstract class PostgresTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres =
            new PostgreSQLContainer<>("postgres:16-alpine");
}
```

```java title="E os testes só herdam" numbered
class ProductRepositoryTest extends PostgresTest {

    @Autowired ProductRepository repository;

    @Test
    void deveIgnorarAcentoNaBusca() {
        // agora unaccent existe de verdade
    }
}
```

Duas anotações fazem o trabalho pesado. `@AutoConfigureTestDatabase(replace =
NONE)` impede o Spring de trocar o banco pelo H2. `@ServiceConnection` pega a
URL, o usuário e a senha do contêiner e injeta na configuração — sem nenhuma
propriedade escrita à mão.

:::diagram type="flowchart" caption="O contêiner sobe uma vez, serve todos os testes e some no fim."
nodes:
  - { id: s,  type: start,   text: "mvn test" }
  - { id: c,  type: process, text: "Docker sobe postgres:16" }
  - { id: t,  type: process, text: "testes rodam contra ele" }
  - { id: r,  type: process, text: "cada teste desfaz a transação" }
  - { id: k,  type: start,   text: "contêiner é destruído" }
edges:
  - { from: s, to: c }
  - { from: c, to: t }
  - { from: t, to: r }
  - { from: r, to: t, label: "próximo" }
  - { from: t, to: k }
:::

:::trivia
O `static` no campo do contêiner não é detalhe de estilo: com ele, o
contêiner sobe **uma vez** para a classe inteira. Sem ele, o Docker levanta
um PostgreSQL novo a cada método de teste — e uma suíte de trinta testes
passa de vinte segundos para seis minutos. É a diferença entre uma prática
adotada e uma prática abandonada na segunda semana.
:::

:::pitfall
Testcontainers exige Docker rodando na máquina e no servidor de integração
contínua. É a única dependência de infraestrutura deste livro, e ela é real:
se a sua esteira não tem Docker, esses testes não rodam. A saída intermediária
é rodar os testes de repositório em um perfil separado
(`mvn test -Pintegration`) e mantê-los fora do build rápido do dia a dia.
:::

## Migração versionada: o teste que vale para produção

```xml title="pom.xml"
<dependency>
    <groupId>org.flywaydb</groupId>
    <artifactId>flyway-core</artifactId>
</dependency>
```

```sql title="src/main/resources/db/migration/V1__criar_product.sql"
CREATE TABLE product (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(120) NOT NULL,
    price       NUMERIC(10,2) NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 0,
    status      VARCHAR(20) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uk_product_name ON product (lower(name));
```

O Flyway roda os arquivos `V1__`, `V2__`, `V3__` em ordem, uma única vez
cada, e guarda em uma tabela o que já aplicou. Com ele:

- o teste sobe o esquema **exatamente** como a produção;
- `ddl-auto` pode ficar em `validate` para sempre;
- a evolução do banco fica no Git, revisável em *pull request*.

:::key
Migração versionada é a diferença entre "o banco de produção está em um
estado que ninguém sabe reproduzir" e "o banco é o resultado de rodar estes
dezessete arquivos, nesta ordem". Adote no primeiro dia: retroagir custa
caro.
:::

:::story No H2 passava
A busca ignorando acento foi entregue numa quarta, com teste.

O teste procurava por "cafe" e encontrava "Café". Verde. Passou na esteira,
passou na revisão, passou no *merge*.

Na sexta, Cláudia avisou que a busca por acento não funcionava em produção.

Carlos jurou que tinha testado. Tinha mesmo — no H2, que ignora acento por
padrão na comparação. O PostgreSQL não ignora, e a extensão `unaccent` nunca
tinha sido instalada no banco de produção porque o teste nunca precisou dela.

O teste não estava errado. Estava rodando em outro banco.

A migração para Testcontainers levou uma tarde. O primeiro teste a rodar
contra o PostgreSQL de verdade falhou imediatamente — e essa falha foi a
coisa mais útil que aconteceu naquela semana.
:::

:::summary
- `@DataJpaTest` sobe só a camada de dados e desfaz cada teste.
- Monte o cenário com `TestEntityManager`, não com o repositório testado.
- H2 é outro banco: tipos, dialeto e comportamento diferentes.
- Testcontainers sobe o PostgreSQL de verdade; `static` no contêiner é
  obrigatório para a suíte não demorar.
- Flyway versiona o esquema e faz o teste usar o mesmo banco da produção.
:::

:::checkpoint
Você testa repositórios contra um PostgreSQL real, versiona o esquema com
Flyway e sabe explicar por que "no H2 passava" não é defesa.
:::

:::milestone
Fim da Parte 8. Unidade, camada web e banco — as três camadas têm rede. A API
pode ser alterada sem que a alteração dependa de alguém lembrar de testar na
mão.
:::

:::exercise level=1
Escreva um teste de repositório que prove que dois produtos com o mesmo nome
não podem existir.

:::answer
O teste só passa se a restrição `UNIQUE` existir no banco — e é por isso que
ele vale: ele testa o **esquema**, não o Java. Se alguém remover o índice
único em uma migração futura, este teste quebra no mesmo dia.
:::

:::exercise level=2
Configure Testcontainers e rode a suíte. Depois remova o `static` do campo do
contêiner e cronometre a diferença.

:::answer
Em uma suíte pequena a diferença já é de minutos. O `static` faz o contêiner
ser reaproveitado por toda a classe; o Testcontainers ainda oferece
*reuse* entre execuções, configurável em `~/.testcontainers.properties`, que
elimina até o tempo de subida repetida durante o desenvolvimento.
:::

:::exercise level=3
Escreva `V2__adicionar_category.sql` criando a tabela de categoria e a chave
estrangeira em `product`. Rode os testes e depois responda: o que acontece se
alguém editar o `V1` depois de aplicado?

:::answer
O Flyway guarda um *checksum* de cada arquivo aplicado. Editar o `V1` faz a
validação falhar na partida com `Migration checksum mismatch` — e isso é
proposital: um arquivo já aplicado em produção é história, e história não se
edita. A correção é sempre um `V3` novo.
:::
