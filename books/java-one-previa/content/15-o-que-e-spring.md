---
title: "O que é Spring"
number: 15
part: p3
kicker: "Você para de criar objetos com new. Em troca, alguém cria por você — e é preciso entender quem."
epigraph: "Um framework é uma biblioteca que chama o seu código, em vez de ser chamada por ele."
epigraph_by: "Martin Fowler, sobre inversão de controle"
goal: >-
  Explicar inversão de controle e injeção de dependência com um exemplo de
  código, e dizer o que é um *bean* e o que é o contêiner.
---

Até o capítulo 14 você criou todos os objetos do programa. A partir daqui,
quem cria é o framework. Essa inversão tem nome, tem motivo e tem um preço —
e este capítulo é sobre os três. Não vamos instalar nada ainda: primeiro a
ideia.

## O problema que o Spring resolve

Considere a estrutura que você montou no capítulo 11:

```java title="Quem monta essas peças?" numbered
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }
}
```

Alguém precisa escrever:

```java title="A montagem manual" numbered
var dataSource = new PostgresDataSource(url, user, pass);
var repository = new JdbcProductRepository(dataSource);
var service = new ProductService(repository);
var controller = new ProductController(service);
```

Com quatro classes é aceitável. Uma API real tem quarenta: serviço de e-mail,
cliente HTTP, cache, transação, autenticação, e cada um depende de outros
três. Essa montagem passa a ser um arquivo de trezentas linhas que ninguém
quer abrir — e que precisa ser refeito em cada teste.

:::key
O Spring não faz nada que você não poderia fazer à mão. Ele faz a **montagem**
por você, sempre do mesmo jeito, e cuida da ordem. É um construtor de grafos
de objetos, não um poder mágico.
:::

:::story A palavra framework
Roberto voltou de um evento com uma palavra nova e uma certeza.

— A gente precisa de um framework.

— Para quê? — perguntou Marina.

— Para acelerar. O cara do painel disse que reduz em 70% o tempo de
desenvolvimento.

— Reduz o tempo de escrever o encanamento. A gente ainda não escreveu nem o
encanamento nem o resto.

Roberto anotou "70%" no caderno e circulou. Duas semanas depois, aquele
número apareceu em um slide, sem contexto, ao lado do prazo de entrega.

Marina fez o que fazia sempre: abriu o projeto e mostrou a Carlos as quatro
linhas de montagem manual que existiam no `main`.

— Isso aqui é o que o framework vai fazer por nós. Não é pouco. Mas também
não é 70% de nada.
:::

## Inversão de controle

A expressão descreve exatamente a troca:

:::compare left="Controle no seu código" right="Controle invertido"
class ProductService {
  private Repo repo =
      new JdbcRepo();
}
---
class ProductService {
  private final Repo repo;

  ProductService(Repo repo) {
    this.repo = repo;
  }
}
:::

À esquerda, a classe decide qual implementação usar — e fica presa a ela para
sempre. À direita, a classe **declara o que precisa** e recebe de fora. Quem
decide passa a ser quem monta.

Essa segunda forma tem nome próprio: **injeção de dependência por
construtor**. Ela é a única que este livro usa, e a recomendada oficialmente
pelo Spring, por três razões: o objeto nasce completo, o atributo pode ser
`final`, e a classe continua testável sem framework nenhum.

## O contêiner e os *beans*

```java title="O que o Spring lê" numbered
@Service
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }
}
```

Uma anotação, e o acordo muda. `@Service` diz ao Spring: *"esta classe é
minha, crie uma instância dela e guarde"*. Essa instância guardada é um
**bean**, e o lugar onde ela fica é o **contêiner** (formalmente,
*application context*).

:::diagram type="blocks" caption="O contêiner monta o grafo na partida, olhando as anotações e os construtores."
rows:
  - [{ text: "@SpringBootApplication", note: "varre o pacote em busca de anotações" }]
  - [{ text: "ApplicationContext", note: "o contêiner: cria, guarda e liga os beans" }]
  - [{ text: "@Controller", note: "recebe HTTP" }, { text: "@Service", note: "regra" }, { text: "@Repository", note: "banco" }]
:::

Na partida, o Spring varre o pacote, encontra as classes anotadas, olha os
construtores, descobre em que ordem criar cada uma e monta tudo. Se faltar
uma peça, ele falha **na partida** — não na requisição do cliente.

:::anatomy title="Como o Spring decide o que injetar"
lang: java
code: |
  @Service
  public class ProductService {
      private final ProductRepository repo;

      public ProductService(ProductRepository repo) {
          this.repo = repo;
      }
  }
notes:
  - { line: 1, text: "A anotação marca a classe como candidata a bean." }
  - { line: 3, text: "`final` garante que a dependência não muda depois de montada." }
  - { line: 5, text: "Um único construtor: o Spring nem precisa de `@Autowired` desde a versão 4.3." }
  - { line: 5, text: "O **tipo** do parâmetro é a chave da busca: ele procura um bean que sirva como `ProductRepository`." }
:::

## Quatro anotações que dizem a mesma coisa

| Anotação | Camada | Diferença real |
|---|---|---|
| `@Component` | qualquer | a forma genérica |
| `@Service` | regra de negócio | nenhuma técnica; comunica intenção |
| `@Repository` | acesso a dados | traduz exceções do banco |
| `@Controller` | entrada HTTP | habilita o mapeamento de rotas |

Tabela: Todas criam um bean. Escolher a certa é documentação — e, em dois
casos, também comportamento.

:::pitfall
`@Autowired` em atributo (*field injection*) ainda aparece em muito tutorial:

```java
@Autowired
private ProductRepository repository;   // evite
```

Funciona e cobra caro: o atributo não pode ser `final`, a classe mente sobre
suas dependências (o construtor não as declara) e o teste unitário precisa de
reflexão para preencher o campo. Use o construtor. Sempre.
:::

## Escopo: quantos objetos existem

Por padrão, um bean é **singleton**: existe **um** para a aplicação inteira, e
todas as requisições usam o mesmo objeto. Isso tem uma consequência que
assusta quem descobre tarde:

:::pitfall
Um bean singleton **não pode guardar estado de requisição**. Se o
`ProductService` tiver um atributo `private Product atual`, duas requisições
simultâneas vão sobrescrever uma à outra — e o cliente A receberá o dado do
cliente B. A regra é simples: **os atributos de um bean são só as suas
dependências**. Dado de requisição vive em parâmetro e variável local.
:::

## O que exatamente o Spring Boot acrescenta

O Spring Framework resolve a montagem. O Spring Boot resolve a configuração:

- **servidor embutido**: o Tomcat vem dentro do JAR; não há servidor para
  instalar;
- **autoconfiguração**: viu o PostgreSQL no classpath? configura a conexão;
  viu o Jackson? configura JSON;
- **`application.properties`**: um arquivo, chaves com nome previsível;
- **arranque único**: `java -jar app.jar` e está no ar.

:::history
Em 2003, escrever a mesma aplicação exigia um arquivo `web.xml`, dois
descritores `ejb-jar.xml`, um servidor de aplicação instalado à parte e um
ciclo de *build-deploy* de vários minutos. O Spring Boot é de 2014 e a
proposta era cortar isso: convenção em vez de configuração. A comunidade
chamou de "opinionated" — o framework tem opinião, e você só discute quando
precisa.
:::

## Onde a mágica cobra o preço

Vale dizer isto agora, antes de o encantamento começar:

- o erro vira longo. Uma pilha de exceção do Spring tem sessenta linhas, e as
  três que importam estão no meio;
- a ordem de criação é implícita. Quando duas classes dependem uma da outra, o
  erro é `circular reference` e a solução é repensar o desenho;
- a anotação esconde comportamento. `@Transactional` muda o que acontece em
  volta do método sem aparecer no corpo dele — e o capítulo 30 mostra o que
  isso significa na prática.

Nada disso é motivo para não usar. É motivo para saber o que está acontecendo,
que é a diferença entre usar o framework e ser usado por ele.

:::term Bean
Um objeto cujo ciclo de vida é controlado pelo Spring: ele cria, injeta as
dependências, guarda e destrói.
:::

:::term Contêiner (ApplicationContext)
O registro de todos os beans da aplicação. Monta o grafo na partida e entrega
a instância a quem pedir pelo tipo.
:::

:::summary
- Inversão de controle: a classe declara o que precisa; outro decide o que
  entregar.
- Injeção por construtor é a única forma recomendada — atributo `final`,
  objeto completo, teste sem framework.
- `@Service`, `@Repository`, `@Controller` e `@Component` criam beans.
- Bean é singleton por padrão: não guarde estado de requisição nele.
- Spring monta; Spring Boot configura.
:::

:::checkpoint
Você explica inversão de controle com um exemplo, sabe por que injeção por
construtor vence, reconhece as quatro anotações e sabe por que um bean não
pode guardar estado de requisição.
:::

:::milestone
Nenhuma linha nova de projeto, mas a estrutura do capítulo 11 acabou de
ganhar sentido: `ProductService` recebendo `ProductRepository` é exatamente o
formato que o Spring espera encontrar. O capítulo 16 instala o framework.
:::

:::exercise level=1
Reescreva a montagem manual de quatro linhas deste capítulo explicando, em uma
frase por linha, qual dependência cada objeto recebe.

:::answer
O `DataSource` recebe a configuração de conexão; o repositório recebe o
`DataSource`; o serviço recebe o repositório; o controlador recebe o serviço.
Cada camada conhece **apenas a de baixo** — e é essa cadeia que o Spring vai
montar sozinho.
:::

:::exercise level=2
Escreva duas classes, `EmailSender` (interface), `SmtpEmailSender` e
`FakeEmailSender`, e uma `OrderService` que receba a interface no construtor.
Monte as duas combinações à mão, sem framework.

:::answer
```java
var real = new OrderService(new SmtpEmailSender());
var teste = new OrderService(new FakeEmailSender());
```
Duas linhas, duas configurações do mesmo sistema. Você acabou de fazer, à
mão, exatamente o que o `@MockBean` do capítulo 36 faz — e é por isso que
injeção por construtor torna o teste trivial.
:::

:::exercise level=3
Explique, sem usar a palavra "mágica", o que acontece entre `java -jar
app.jar` e a primeira requisição atendida.

:::answer
A JVM carrega a classe principal; o Spring Boot cria o `ApplicationContext`;
o contêiner varre os pacotes procurando anotações; para cada classe
encontrada, resolve as dependências do construtor (criando-as antes, se
necessário) e guarda o bean; a autoconfiguração sobe o Tomcat embutido e
registra as rotas dos controladores; a porta abre. Nada disso é mágica: é um
grafo sendo montado em ordem topológica.
:::
