---
title: "Banco de dados"
number: 19
part: p4
kicker: "Um lugar onde o dado sobrevive ao desligamento da máquina — e uma linguagem de cinquenta anos que ninguém conseguiu substituir."
goal: >-
  Subir um PostgreSQL, criar tabelas, escrever as quatro instruções do CRUD em
  SQL e explicar chave primária, chave estrangeira e índice.
---

O `Map` do capítulo 17 tem um defeito fatal: ele mora na memória do processo.
Reiniciar a aplicação apaga tudo. Um banco de dados resolve isso e, no
caminho, oferece busca rápida, integridade e acesso simultâneo.

## Subindo um PostgreSQL em dois minutos

```bash title="Com Docker — a forma mais limpa"
docker run --name loja-db \
  -e POSTGRES_PASSWORD=senha \
  -e POSTGRES_DB=catalog \
  -p 5432:5432 \
  -d postgres:16
```

Um comando e você tem um banco rodando, isolado, que pode ser apagado sem
deixar rastro (`docker rm -f loja-db`). Se preferir instalar direto no
sistema, funciona igual — só é mais difícil de desfazer.

```bash title="Entrando no banco"
docker exec -it loja-db psql -U postgres -d catalog
```

:::trivia
O PostgreSQL nasceu em 1986 em Berkeley, como sucessor do Ingres — daí o nome
*post-Ingres*. É mantido por uma comunidade sem dono há quase quarenta anos,
não pertence a nenhuma empresa e implementa o padrão SQL com mais rigor que
qualquer concorrente comercial. Quando você não tem um motivo específico para
escolher outro banco relacional, a resposta é este.
:::

## SQL: quatro instruções e nada mais (por enquanto)

```sql title="Criando a tabela" numbered
CREATE TABLE product (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(120) NOT NULL,
    description TEXT,
    price       NUMERIC(10,2) NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 0,
    status      VARCHAR(20) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

:::anatomy title="Cada declaração da tabela é uma regra que o banco garante"
lang: sql
code: |
  CREATE TABLE product (
      id      BIGSERIAL PRIMARY KEY,
      name    VARCHAR(120) NOT NULL,
      price   NUMERIC(10,2) NOT NULL,
      status  VARCHAR(20) NOT NULL
  );
notes:
  - { line: 2, text: "`BIGSERIAL` cria a sequência e o tipo de 64 bits: o `Long` do capítulo 18." }
  - { line: 2, text: "`PRIMARY KEY` garante unicidade e cria um índice automaticamente." }
  - { line: 3, text: "`VARCHAR(120)` limita o tamanho — o banco recusa o texto maior." }
  - { line: 3, text: "`NOT NULL` transforma campo obrigatório em regra do banco, não só do código." }
  - { line: 4, text: "`NUMERIC(10,2)` é decimal exato: o `BigDecimal` do capítulo 3." }
:::

| SQL | Java equivalente | Por quê |
|---|---|---|
| `BIGSERIAL` | `Long` | id que cresce sozinho |
| `VARCHAR(n)` | `String` | texto com limite |
| `NUMERIC(10,2)` | `BigDecimal` | decimal exato, para dinheiro |
| `TIMESTAMPTZ` | `Instant` | momento com fuso |
| `BOOLEAN` | `Boolean` | verdade ou falso |

Tabela: A ponte entre os dois mundos. O capítulo 20 faz essa tradução
automaticamente.

## As quatro operações

```sql title="Create, read, update, delete" numbered
-- create
INSERT INTO product (name, price, quantity, status)
VALUES ('Teclado mecânico', 349.90, 12, 'ATIVO');

-- read
SELECT id, name, price FROM product WHERE price > 100;
SELECT * FROM product WHERE id = 1;
SELECT * FROM product ORDER BY name LIMIT 10 OFFSET 0;

-- update
UPDATE product SET price = 299.90 WHERE id = 1;

-- delete
DELETE FROM product WHERE id = 1;
```

Repare no `WHERE` das duas últimas. Sem ele, `UPDATE` altera **todas** as
linhas e `DELETE` apaga a tabela inteira.

:::pitfall
`DELETE FROM product;` sem `WHERE` é a instrução mais destrutiva da carreira
de qualquer programador — e todos nós a executamos uma vez, sempre em
produção, sempre numa sexta. O hábito que protege: escreva o `WHERE`
**primeiro**, depois volte e escreva o `DELETE`.
:::

:::story A sexta em que faltou o WHERE
O chamado dizia: "remover os produtos de teste da homologação".

Carlos abriu o terminal do banco e digitou `DELETE FROM product`. Antes de
escrever o `WHERE`, o dedo encostou no Enter.

`DELETE 11482`

Ele leu o número três vezes, como se ler mudasse alguma coisa. Depois olhou
para o topo da janela, onde estava o nome da conexão. Não dizia
`homologacao`.

O que salvou a Aurora Comércio naquela sexta não foi o Carlos, nem o
processo, nem a revisão de código. Foi o *backup* automático da noite
anterior e uma hora e quarenta de restauração, com Marina do lado, em
silêncio, tomando café.

Na segunda, sem alarde, ela acrescentou uma linha na configuração do terminal
do banco de produção: um prompt vermelho com a palavra PRODUÇÃO em caixa
alta.

— Não é que a gente confie menos em você — disse. — É que ninguém deveria
precisar de atenção para não destruir uma empresa.
:::

:::art caption="A instrução mais destrutiva de uma carreira cabe em três palavras."
src="a-instrucao-mais-destrutiva-de-uma-carreira-cabe-em-tres-palavras.png"
Charge editorial minimalista: terminal de computador ocupando o centro da
composição, mostrando a linha "DELETE FROM product" e, abaixo, em destaque,
"DELETE 11482". Um dedo ainda pousado sobre a tecla Enter de um teclado. No
canto superior da janela, uma pequena aba com a palavra "PRODUÇÃO". Ao lado,
um desenvolvedor jovem petrificado, completamente sem expressão. Fundo
branco, poucos elementos, tensão silenciosa, estética editorial de
tecnologia.
:::

## Chave estrangeira: a integridade que o banco cobra

```sql title="A relação do capítulo 18, em SQL" numbered
CREATE TABLE category (
    id   BIGSERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE
);

ALTER TABLE product
    ADD COLUMN category_id BIGINT,
    ADD CONSTRAINT fk_product_category
        FOREIGN KEY (category_id) REFERENCES category (id);
```

Feito isso, o banco passa a **recusar** um produto apontando para uma
categoria que não existe, e a recusar apagar uma categoria que ainda tem
produtos. Essa garantia vale mais que qualquer validação de código, porque ela
não depende de o programa estar correto.

:::key
Toda regra que você pode expressar no banco (`NOT NULL`, `UNIQUE`,
`FOREIGN KEY`, `CHECK`) é uma regra que continua valendo quando alguém mexe
nos dados por fora da sua aplicação — um script, um estagiário, outro
sistema. Valide nos dois lugares.
:::

## Índice: por que uma busca é rápida

```sql title="Duas buscas, desempenhos diferentes" numbered
SELECT * FROM product WHERE id = 500000;      -- instantâneo
SELECT * FROM product WHERE name = 'Teclado'; -- varre a tabela

CREATE INDEX idx_product_name ON product (name);
-- agora a segunda também é instantânea
```

Um índice é uma estrutura ordenada à parte que o banco consulta para não
precisar ler todas as linhas. Ele acelera a leitura e **desacelera a
escrita** — cada `INSERT` precisa atualizar o índice também. Por isso não se
indexa tudo: indexa-se o que se busca.

:::diagram type="flowchart" caption="Sem índice, o banco lê tudo. Com índice, ele consulta um atalho ordenado."
nodes:
  - { id: q,   type: io,       text: "WHERE name = 'Teclado'" }
  - { id: d,   type: decision, text: "existe índice?" }
  - { id: idx, type: process,  text: "consulta o índice: ~20 leituras" }
  - { id: seq, type: process,  text: "varre a tabela: 1.000.000 leituras" }
  - { id: r,   type: start,    text: "linha encontrada" }
edges:
  - { from: q,   to: d }
  - { from: d,   to: idx, label: "sim" }
  - { from: d,   to: seq, label: "não" }
  - { from: idx, to: r }
  - { from: seq, to: r }
:::

## Conectando a aplicação

```properties title="application.properties"
spring.datasource.url=jdbc:postgresql://localhost:5432/catalog
spring.datasource.username=postgres
spring.datasource.password=senha

spring.jpa.hibernate.ddl-auto=validate
spring.jpa.show-sql=true
```

E a dependência no `pom.xml`:

```xml title="pom.xml"
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
    <scope>runtime</scope>
</dependency>
```

:::pitfall
`spring.jpa.hibernate.ddl-auto=update` aparece em todo tutorial e **não deve
ir para produção**. Ele deixa o Hibernate alterar o esquema sozinho: uma
renomeação de campo pode criar uma coluna nova e deixar a antiga com os dados
para trás. Em produção use `validate` e faça as mudanças por migração
versionada (Flyway) — assunto do capítulo 42.
:::

## O SQL não vai embora

O capítulo 20 traz o JPA, que escreve SQL por você. Isso não dispensa saber
SQL — dispensa **digitar** SQL. Quando a consulta gerada estiver lenta, quando
o log mostrar mil consultas onde deveria haver uma (capítulo 30), quem lê SQL
resolve em minutos e quem não lê troca de framework.

:::term Transação
Um conjunto de operações que acontece por inteiro ou não acontece. Se o
`INSERT` do pedido funciona e o do item falha, a transação desfaz os dois.
:::

:::summary
- Docker sobe um PostgreSQL descartável em um comando.
- `CREATE TABLE` declara regras que o banco garante: tipo, tamanho,
  obrigatoriedade, unicidade.
- `INSERT`, `SELECT`, `UPDATE`, `DELETE` são o CRUD; `UPDATE` e `DELETE` sem
  `WHERE` são catástrofe.
- Chave estrangeira garante integridade mesmo contra alterações feitas fora da
  aplicação.
- Índice acelera leitura e custa escrita: indexe o que você busca.
:::

:::checkpoint
Você sobe um banco, cria tabelas com restrições, escreve as quatro operações
em SQL, cria um índice e conecta a aplicação Spring ao banco.
:::

:::milestone
O projeto tem onde guardar: a tabela `product` existe e a aplicação conhece a
URL do banco. Falta traduzir a classe Java em linha de tabela — capítulo 20.
:::

:::exercise level=1
Crie a tabela `category` e insira três categorias. Depois associe dois
produtos a categorias diferentes com `UPDATE`.

:::answer
```sql
INSERT INTO category (name) VALUES ('Periféricos'), ('Monitores');
UPDATE product SET category_id = 1 WHERE id = 1;
```
Tente agora `UPDATE product SET category_id = 99 WHERE id = 1;` e leia o
erro: `violates foreign key constraint`. O banco acabou de impedir um dado
inconsistente que o seu código Java nem sabia que estava errado.
:::

:::exercise level=2
Escreva a consulta que devolve o nome da categoria junto de cada produto.
Dica: `JOIN`.

:::answer
```sql
SELECT p.name AS produto, c.name AS categoria
FROM product p
JOIN category c ON c.id = p.category_id
ORDER BY c.name, p.name;
```
Um produto sem categoria **não aparece** nessa consulta. Para incluí-lo, use
`LEFT JOIN` — e essa diferença de uma palavra é a origem de metade dos
relatórios que "perdem" registros.
:::

:::exercise level=3
Descubra o que `EXPLAIN ANALYZE` faz e rode-o na busca por nome antes e depois
de criar o índice. Compare o tempo e o tipo de varredura.

:::answer
Antes, o plano mostra `Seq Scan on product` — varredura sequencial. Depois,
`Index Scan using idx_product_name`. Em uma tabela de um milhão de linhas a
diferença costuma ser de três ordens de magnitude. Saber ler um plano de
execução é a habilidade que separa quem "otimiza no chute" de quem otimiza.
:::
