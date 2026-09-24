---
title: "Banco de dados"
number: 20
slug: banco-de-dados
part: p4
kicker: "Um lugar que não esquece, não se contradiz e aguenta dez pessoas escrevendo ao mesmo tempo."
goal: >-
  Instalar o PostgreSQL, modelar uma tabela, escrever SQL suficiente para
  entender o que o ORM vai gerar, e saber o que uma transação garante.
---

A lista do capítulo @cap:primeira-api some quando o servidor reinicia. A
primeira reação de todo mundo é gravar num arquivo — e vale entender por que
essa reação está errada antes de instalar coisa nenhuma.

Um arquivo JSON resolve a persistência e nada mais. Duas requisições
simultâneas sobrescrevem uma à outra. Buscar um produto exige ler o arquivo
inteiro. Não existe "gravar as duas coisas ou nenhuma". E qualquer falha no
meio da escrita deixa um arquivo pela metade, que na próxima leitura não
carrega.

O banco de dados relacional resolve esses quatro problemas há cinquenta
anos.

## Instalando

A forma mais rápida, se você tem Docker:

```text
$ docker run --name pg-sabia -e POSTGRES_PASSWORD=senha \
    -e POSTGRES_DB=catalogo -p 5432:5432 -d postgres:16
```

Sem Docker, baixe o instalador em <https://postgresql.org/download>. No
macOS, o Postgres.app é a opção com menos atrito.

```text
$ psql "postgresql://postgres:senha@localhost/catalogo"
psql (16.4)
catalogo=#
```

:::practice
Rode `\dt` para listar tabelas (nenhuma ainda), `\l` para listar bancos e
`\q` para sair. Esses três comandos resolvem noventa por cento das vezes em
que você precisa olhar o banco durante o desenvolvimento — e são mais
rápidos que abrir uma ferramenta gráfica.
:::

## A tabela

```sql title="criar_tabela.sql" numbered
CREATE TABLE produto (
    id          BIGSERIAL PRIMARY KEY,
    nome        VARCHAR(120)  NOT NULL,
    preco       NUMERIC(10,2) NOT NULL CHECK (preco > 0),
    estoque     INTEGER       NOT NULL DEFAULT 0 CHECK (estoque >= 0),
    ativo       BOOLEAN       NOT NULL DEFAULT TRUE,
    criado_em   TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
```

Cada palavra dessa declaração é uma decisão, e todas voltam no capítulo
@cap:sqlalchemy em forma de código Python.

| Escolha | Por quê |
|---|---|
| `BIGSERIAL PRIMARY KEY` | identificador único gerado pelo banco |
| `NUMERIC(10,2)` | dinheiro exato — nunca `FLOAT` |
| `NOT NULL` | o campo não aceita ausência |
| `DEFAULT 0` | valor quando ninguém informa |
| `TIMESTAMPTZ` | instante **com fuso** |

Tabela: `NUMERIC` guarda decimal em base 10, e é a contraparte no banco do
`Decimal` do capítulo @cap:variaveis-e-tipos.

:::warning
`TIMESTAMP` sem o `TZ` guarda uma data e hora sem dizer de onde. Dois
servidores em fusos diferentes gravam instantes diferentes com o mesmo texto,
e a ordenação por data passa a mentir. Use `TIMESTAMPTZ` sempre, e guarde em
UTC.
:::

## `NOT NULL` é uma decisão de negócio

A pergunta "este campo pode faltar?" parece técnica e é de negócio. Um
produto sem preço existe? Um produtor sem e-mail existe?

Deixar tudo aceitando nulo parece flexível e é o contrário: empurra a
pergunta para cada consulta que lê o campo, para sempre. Cada coluna que
aceita nulo é um `if` a mais em todo código que a toca.

:::key
A regra prática: comece com `NOT NULL` em tudo e remova quando alguém
apresentar um caso real de ausência. O caminho contrário — começar permissivo
e apertar depois — exige limpar os dados já gravados, e isso nunca é uma
migração tranquila.
:::

## SQL: o mínimo que você precisa entender

A consulta abaixo é o que o programa pede ao banco. Vale saber escrevê-la e
vale saber lê-la: no dia em que ela estiver lenta, o Python não vai estar na
tela. A consulta vai.

```sql title="as_quatro_operacoes.sql" numbered
INSERT INTO produto (nome, preco, estoque)
VALUES ('Tomate italiano', 8.90, 120);

SELECT id, nome, preco FROM produto
WHERE estoque > 0
ORDER BY nome
LIMIT 20;

UPDATE produto SET preco = 9.50 WHERE id = 1;

DELETE FROM produto WHERE id = 1;
```

Quatro comandos, os mesmos quatro verbos do CRUD. A correspondência é
direta e é o motivo de "CRUD" e "SQL" aparecerem sempre na mesma frase.

:::pitfall
`UPDATE` e `DELETE` **sem** `WHERE` atingem a tabela inteira. Não há
confirmação, não há desfazer, e o banco não acha isso estranho — é um
comando válido. O hábito que salva: escreva primeiro o `WHERE`, depois volte
e escreva o começo do comando.
:::

## Índice: por que a busca fica lenta

```sql
SELECT * FROM produto WHERE nome = 'Tomate italiano';
```

Sem índice, o banco lê **todas** as linhas e compara uma a uma. Com dez
linhas, é instantâneo. Com dez milhões, é o suporte ligando.

```sql
CREATE INDEX idx_produto_nome ON produto (nome);
```

:::diagram type="flowchart" caption="Sem índice, o banco lê tudo. Com índice, ele consulta um atalho ordenado."
nodes:
  - { id: q,  type: io,       text: "WHERE nome = 'X'" }
  - { id: d,  type: decision, text: "existe índice?" }
  - { id: s,  type: process,  text: "lê a tabela inteira" }
  - { id: i,  type: process,  text: "busca na árvore do índice" }
  - { id: r,  type: io,       text: "linhas" }
edges:
  - { from: q, to: d }
  - { from: d, to: s, label: "não" }
  - { from: d, to: i, label: "sim" }
  - { from: s, to: r }
  - { from: i, to: r }
:::

O índice não é grátis: ele ocupa espaço e torna toda escrita um pouco mais
lenta, porque precisa ser atualizado junto. A regra: indexe o que aparece em
`WHERE`, em `JOIN` e em `ORDER BY` — e nada além disso, sem medir.

A chave primária ganha índice automaticamente. Chave estrangeira, na maioria
dos bancos, **não** — e essa ausência é a causa mais comum de listagem lenta
em sistema pequeno.

## Transação: tudo ou nada

Aqui está a garantia que nenhum arquivo JSON oferece.

```sql title="transacao.sql" numbered
CREATE TABLE movimento (
  id          BIGSERIAL PRIMARY KEY,
  produto_id  BIGINT NOT NULL REFERENCES produto(id),
  quantidade  INTEGER NOT NULL,
  criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

BEGIN;

UPDATE produto SET estoque = estoque - 10 WHERE id = 1;
INSERT INTO movimento (produto_id, quantidade) VALUES (1, -10);

COMMIT;
```

Entre `BEGIN` e `COMMIT`, ou as duas linhas acontecem, ou nenhuma. Se o
servidor cair no meio, o banco desfaz tudo ao voltar. Se alguém consultar o
estoque durante a transação, vê o valor antigo — não vê o estado pela
metade.

As quatro letras de ACID descrevem essa promessa:

| Letra | Promessa |
|---|---|
| Atomicidade | tudo ou nada |
| Consistência | as regras da tabela continuam valendo |
| Isolamento | uma transação não enxerga o meio da outra |
| Durabilidade | depois do `COMMIT`, sobrevive à queda de energia |

Tabela: São quatro promessas caras de implementar e é exatamente por elas
que se usa um banco de dados.

:::key
A transação é a unidade de trabalho do negócio, não a unidade técnica. "Dar
baixa no estoque e registrar o movimento" é uma operação só do ponto de
vista da cooperativa; o fato de serem dois comandos SQL é detalhe. Essa
fronteira é o que define, no capítulo @cap:service, onde a transação começa
e termina.
:::

## Conectando do Python

```text
$ pip install "psycopg[binary]"
```

```python title="conexao_crua.py" numbered
import psycopg

url = "postgresql://postgres:senha@localhost/catalogo"

with psycopg.connect(url) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO produto (nome, preco) VALUES (%s, %s)",
            ("Cenoura", "5.25"),
        )
        cur.execute("SELECT id, nome, preco FROM produto")
        for linha in cur.fetchall():
            print(linha)
```

Os dois `with` do capítulo @cap:excecoes aparecem aqui com um papel a mais:
o `with` da conexão faz `COMMIT` ao sair sem erro e `ROLLBACK` se uma
exceção escapar.

:::warning
Repare no `%s` e na tupla separada. **Nunca** monte SQL com `f-string`:

```python
cur.execute(f"SELECT * FROM produto WHERE nome = '{nome}'")
```

Se `nome` vier de uma requisição e contiver `'; DROP TABLE produto; --`, o
banco executa o que foi mandado. Isso se chama injeção de SQL, tem quase
trinta anos, e continua sendo uma das falhas mais exploradas do mundo. Com
`%s`, o valor viaja separado do comando e nunca é interpretado como comando.
:::

:::story A planilha e o banco, lado a lado
— E se a gente perder tudo? — perguntou Dona Neuza.

— A gente faz cópia de segurança todo dia — disse Bia.

— A planilha eu abro e vejo. Esse negócio aí eu não vejo.

Bia pensou um instante e abriu o `psql`. Digitou `SELECT * FROM produto;` e
virou a tela. As linhas apareceram em colunas, com cabeçalho, alinhadas.

— É uma planilha — disse Dona Neuza.

— É uma planilha que sabe dizer não. — Bia digitou de novo, agora com um
preço negativo. O banco recusou, com uma linha vermelha e o nome da regra
violada. — A sua abre e aceita. Essa aqui abre, olha, e não deixa.

Dona Neuza leu a mensagem de erro com atenção, de óculos na ponta do nariz.

— Ela recusa também se eu mandar? — perguntou.

— Recusa a senhora, recusa a mim e recusa o sistema.
:::

:::summary
- Arquivo não resolve concorrência, busca, atomicidade nem escrita parcial.
- `NUMERIC` para dinheiro, `TIMESTAMPTZ` para instante, `NOT NULL` por
  padrão.
- Ler SQL é obrigatório mesmo usando ORM; escrever, quase nunca.
- `UPDATE` e `DELETE` sem `WHERE` atingem tudo.
- Índice acelera leitura e custa em escrita; chave estrangeira não ganha um
  sozinha.
- Transação é a unidade de trabalho do negócio, e ACID é o que ela promete.
- Valor nunca entra em SQL por `f-string`.
:::

:::milestone
O banco existe, a tabela existe e o Python conversa com ele. O código
continua feio — SQL cru dentro de rota seria pior que a lista na memória — e
o capítulo @cap:sqlalchemy resolve isso.
:::

:::exercise level=1
Crie a tabela `produtor` com `id`, `nome` (obrigatório), `cidade`
(obrigatório), `email` (único) e `criado_em` com valor padrão.

:::answer
```sql
CREATE TABLE produtor (
    id         BIGSERIAL PRIMARY KEY,
    nome       VARCHAR(100) NOT NULL,
    cidade     VARCHAR(100) NOT NULL,
    email      VARCHAR(160) NOT NULL UNIQUE,
    criado_em  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```
`UNIQUE` cria um índice sozinho — é assim que o banco consegue conferir a
unicidade sem varrer a tabela a cada inserção.
:::

:::exercise level=2
Escreva a consulta que devolve os cinco produtos mais caros com estoque
disponível, mostrando nome e preço.

:::answer
```sql
SELECT nome, preco
FROM produto
WHERE estoque > 0 AND ativo = TRUE
ORDER BY preco DESC
LIMIT 5;
```
A ordem em que o banco trabalha não é a ordem em que você escreve: ele filtra
com o `WHERE`, depois ordena, e só então corta com o `LIMIT`. Saber isso é o
que explica por que `LIMIT 5` numa tabela grande ainda pode ser lento — o
`ORDER BY` precisou tocar todas as linhas que passaram no filtro.
:::

:::exercise level=3
A cooperativa quer registrar a venda de 10 caixas: baixar o estoque do
produto e gravar um movimento. Escreva a transação e depois explique o que
acontece, em cada uma das duas linhas, se o servidor cair exatamente entre
elas.

:::answer
```sql
BEGIN;

UPDATE produto
   SET estoque = estoque - 10
 WHERE id = 1 AND estoque >= 10;

INSERT INTO movimento (produto_id, quantidade, tipo)
VALUES (1, -10, 'venda');

COMMIT;
```

Se o servidor cair entre as duas linhas, **nada aconteceu**. O `UPDATE`
ficou registrado apenas no log de transação, sem `COMMIT`; ao reiniciar, o
banco desfaz. Ninguém vê estoque baixado sem movimento correspondente, nem
por um instante.

Repare no `AND estoque >= 10` dentro do `WHERE`. Ele é a proteção contra
estoque negativo feita **no mesmo comando** que altera — e não num `SELECT`
anterior. Entre um `SELECT` de conferência e um `UPDATE` separado existe uma
janela em que outra transação pode ter vendido as mesmas caixas. Condição e
alteração juntas no mesmo comando fecham essa janela, porque o banco avalia
a linha travada.

O que ainda falta é saber se a venda aconteceu: se ninguém tinha as 10
caixas, o `UPDATE` afeta zero linhas e o `INSERT` grava um movimento que não
existiu. Conferir o número de linhas afetadas, e desfazer quando for zero, é
a parte que o capítulo @cap:service vai escrever em Python.
:::
