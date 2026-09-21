---
title: "Duas tabelas conversando"
number: 14
slug: duas-tabelas-conversando
part: p2
kicker: "Quatro milhões de linhas lidas para devolver três resultados. Desde 2011."
goal: >-
  Ligar tabelas com chave estrangeira, responder perguntas que atravessam
  mais de uma com `JOIN` e `GROUP BY`, descobrir por que uma consulta é
  lenta com `EXPLAIN`, e gravar duas coisas ou nenhuma.
---

A tabela `emprestimos` do capítulo anterior tem uma coluna `leitor_id` e
nenhuma garantia de que o número guardado ali corresponda a um leitor que
exista. Nada impede gravar `leitor_id = 99999` numa biblioteca com mil e
duzentos leitores.

E, uma vez gravado, ninguém descobre — até o dia em que um relatório mostra
um empréstimo sem nome.

## A ligação que o banco garante

```sql
mysql> CREATE TABLE exemplares (
    ->   id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
    ->   livro_id  INT UNSIGNED NOT NULL,
    ->   tombo     INT UNSIGNED NOT NULL,
    ->   estado    VARCHAR(20)  NOT NULL DEFAULT 'bom',
    ->   PRIMARY KEY (id),
    ->   UNIQUE KEY uk_exemplares_tombo (tombo),
    ->   CONSTRAINT fk_exemplares_livro
    ->     FOREIGN KEY (livro_id) REFERENCES livros (id)
    -> ) ENGINE=InnoDB;
Query OK, 0 rows affected (0.05 sec)
```

As três últimas linhas antes do fecha-parênteses são a novidade. Elas dizem:
*a coluna `livro_id` desta tabela aponta para a coluna `id` da tabela
`livros`, e o banco se encarrega de que isso continue verdadeiro.*

Teste:

```sql
mysql> INSERT INTO exemplares (livro_id, tombo) VALUES (99999, 5000);
ERROR 1452 (23000): Cannot add or update a child row: a foreign
key constraint fails (`casa_amarela`.`exemplares`, CONSTRAINT
`fk_exemplares_livro` FOREIGN KEY (`livro_id`) REFERENCES
`livros` (`id`))
```

O banco recusou. Não houve aviso, não houve linha gravada pela metade, não
houve dado ruim esperando ser descoberto em 2029.

E a proteção vale para os dois lados:

```sql
mysql> DELETE FROM livros WHERE id = 1;
ERROR 1451 (23000): Cannot delete or update a parent row: a
foreign key constraint fails
```

Não dá para apagar um livro que tem exemplares. O banco protege a ligação
independentemente de qual programa esteja mexendo — inclusive de você, no
terminal, às seis da tarde.

:::term Integridade referencial
A garantia de que toda referência aponta para algo que existe. É o que
separa um banco de dados de um conjunto de planilhas: a regra é do banco,
não do programa, e por isso vale para todos os programas ao mesmo tempo —
inclusive o script de importação que alguém escreveu às pressas.
:::

Dá para escolher o que acontece quando o lado apontado é removido:

| Cláusula | O que faz |
|---|---|
| `ON DELETE RESTRICT` | recusa a remoção (é o padrão) |
| `ON DELETE CASCADE` | apaga em cascata as linhas que apontavam |
| `ON DELETE SET NULL` | zera a coluna, se ela aceitar nulo |

Tabela: `CASCADE` resolve um problema e cria outro maior — apagar um livro
por engano passa a apagar em silêncio todos os exemplares e todos os
empréstimos dele.

:::key
Use `RESTRICT` por padrão, que é o padrão. `CASCADE` só quando a linha
apontada **não existe sem** a linha que aponta: o item de um pedido não
existe sem o pedido, e apagar o pedido pode levá-lo junto.

Um exemplar não é desse tipo. Ele é um objeto físico que continua na estante
mesmo se alguém apagar o registro do título.
:::

:::pitfall
Uma diferença entre bancos que custa caro quando se troca de um para outro:
**no MySQL com InnoDB, criar uma chave estrangeira cria automaticamente um
índice na coluna**, se ainda não houver um. No PostgreSQL, não — e lá a
ausência desse índice é uma das causas mais comuns de `DELETE` lento, porque
cada remoção precisa varrer a tabela filha inteira procurando referências.

Se você vier de um e for para o outro, confira.
:::

## O esquema inteiro

Com isso, o domínio da Casa Amarela cabe em quatro tabelas:

```sql title="esquema.sql"
CREATE TABLE livros (
  id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
  titulo  VARCHAR(200) NOT NULL,
  autor   VARCHAR(150) NOT NULL,
  isbn    CHAR(13)     NULL,
  assunto VARCHAR(40)  NOT NULL,
  ano     SMALLINT     NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_livros_isbn (isbn)
) ENGINE=InnoDB;

CREATE TABLE exemplares (
  id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
  livro_id INT UNSIGNED NOT NULL,
  tombo    INT UNSIGNED NOT NULL,
  estado   VARCHAR(20)  NOT NULL DEFAULT 'bom',
  PRIMARY KEY (id),
  UNIQUE KEY uk_exemplares_tombo (tombo),
  FOREIGN KEY (livro_id) REFERENCES livros (id)
) ENGINE=InnoDB;

CREATE TABLE leitores (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome        VARCHAR(120) NOT NULL,
  documento   CHAR(11)     NOT NULL,
  cadastro_em DATE         NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_leitores_documento (documento)
) ENGINE=InnoDB;

CREATE TABLE emprestimos (
  id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  exemplar_id       INT UNSIGNED NOT NULL,
  leitor_id         INT UNSIGNED NOT NULL,
  retirado_em       DATETIME     NOT NULL,
  devolver_ate      DATE         NOT NULL,
  devolvido_em      DATETIME     NULL,
  multa_em_centavos INT UNSIGNED NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (exemplar_id) REFERENCES exemplares (id),
  FOREIGN KEY (leitor_id) REFERENCES leitores (id)
) ENGINE=InnoDB;
```

Repare no que **não** existe aqui: não há coluna `quantidade` em `livros`, e
não há coluna `disponivel` em `exemplares`. Os dois são calculáveis a partir
de `emprestimos`, e número calculado não diverge da realidade.

:::key
A regra de arrumação que o esquema acima segue tem nome pomposo —
*normalização* — e três perguntas práticas:

1. **Cada coluna guarda uma coisa só?** Um campo `autor` com
	 `"Machado de Assis; Aluísio Azevedo"` guarda dois, e nenhuma consulta vai
	 conseguir separá-los de forma confiável.
2. **Cada tabela fala de um assunto só?** Se `emprestimos` tivesse
	 `leitor_nome`, o nome passaria a existir em dois lugares e eles
	 divergiriam na primeira correção de grafia.
3. **Nada guardado pode ser calculado?** `quantidade` pode. Fora.

Responder sim às três cobre a esmagadora maioria dos casos. O resto da
teoria existe e raramente muda uma decisão prática.
:::

## A pergunta que envolve duas tabelas

O esquema está arrumado e criou um problema: o título do livro não está mais
na mesma tabela que o exemplar. Para listar exemplares com título, é preciso
juntar as duas.

```sql
mysql> SELECT e.tombo, l.titulo
    -> FROM exemplares e
    -> JOIN livros l ON l.id = e.livro_id;
+-------+---------------+
| tombo | titulo        |
+-------+---------------+
|   812 | O Cortiço     |
|   907 | O Cortiço     |
|   344 | Vidas Secas   |
|  1120 | Grande Sertão |
+-------+---------------+
4 rows in set (0.00 sec)
```

Leia a partir do `FROM`: *comece pelos exemplares, e para cada um deles
encontre o livro cujo `id` é igual ao `livro_id` do exemplar.*

O `e` e o `l` depois dos nomes de tabela são **apelidos**. Eles existem para
que `e.tombo` e `l.titulo` digam de qual tabela cada coluna veio — o que
deixa de ser conveniência e passa a ser obrigação quando duas tabelas têm
colunas com o mesmo nome, como `id`.

O `ON` é a condição da junção, e é a parte que ninguém pode esquecer:

:::pitfall
Um `JOIN` sem `ON` — ou com um `ON` que não liga nada — produz o **produto
cartesiano**: cada linha de um lado combinada com cada linha do outro.

Com 8.000 exemplares e 4.000 livros, isso são 32 milhões de linhas. O
comando não dá erro. Ele começa a devolver resultado, e a máquina para.

Quando uma consulta que deveria trazer dezenas trouxer milhões, olhe o `ON`
antes de qualquer outra coisa.
:::

Três tabelas seguem a mesma forma:

```sql
mysql> SELECT l.titulo, le.nome, em.devolver_ate
    -> FROM emprestimos em
    -> JOIN exemplares e ON e.id = em.exemplar_id
    -> JOIN livros l ON l.id = e.livro_id
    -> JOIN leitores le ON le.id = em.leitor_id
    -> WHERE em.devolvido_em IS NULL
    -> ORDER BY em.devolver_ate;
+---------------+------------------+--------------+
| titulo        | nome             | devolver_ate |
+---------------+------------------+--------------+
| O Cortiço     | Marlene Coutinho | 2027-02-18   |
| Grande Sertão | Juvenal Pereira  | 2027-02-24   |
+---------------+------------------+--------------+
2 rows in set (0.00 sec)
```

Essa é a lista de pendências da Vera, em uma consulta, sem laço nenhum. É
literalmente o relatório que levava quatro décimos de segundo percorrendo
listas na memória, agora feito pelo banco — que foi construído para isso e
não fica mais lento quando a biblioteca crescer.

## A linha que não tem par

```sql
mysql> SELECT l.titulo, COUNT(e.id) AS exemplares
    -> FROM livros l
    -> JOIN exemplares e ON e.livro_id = l.id
    -> GROUP BY l.id, l.titulo;
```

Essa consulta tem um defeito silencioso: livros **sem nenhum exemplar** não
aparecem. O `JOIN` só devolve linhas que acharam par dos dois lados, e um
livro recém-cadastrado, cujos exemplares ainda não chegaram, simplesmente
some do relatório.

O conserto é uma palavra:

```sql
mysql> SELECT l.titulo, COUNT(e.id) AS exemplares
    -> FROM livros l
    -> LEFT JOIN exemplares e ON e.livro_id = l.id
    -> GROUP BY l.id, l.titulo
    -> ORDER BY exemplares DESC;
+--------------------+------------+
| titulo             | exemplares |
+--------------------+------------+
| O Cortiço          |          2 |
| Vidas Secas        |          1 |
| Grande Sertão      |          1 |
| O Pequeno Príncipe |          0 |
+--------------------+------------+
4 rows in set (0.00 sec)
```

`LEFT JOIN` traz **todas** as linhas da tabela da esquerda, tenham par ou
não. Quando não têm, as colunas do lado direito vêm nulas.

:::key
A diferença entre `JOIN` e `LEFT JOIN` não é técnica, é de pergunta.

`JOIN` responde *"quais pares existem?"*. `LEFT JOIN` responde *"o que tem a
tabela da esquerda, com o que houver da direita?"*.

O erro clássico é usar `JOIN` quando a pergunta era a segunda — e o sintoma
é um relatório em que faltam exatamente as linhas mais interessantes: o
livro sem exemplar, o leitor que nunca pegou nada, o mês sem movimento.
:::

Repare no `COUNT(e.id)` e não `COUNT(*)`. Num `LEFT JOIN`, a linha do livro
sem exemplar existe, então `COUNT(*)` contaria `1`. `COUNT(e.id)` ignora
nulos e devolve `0`, que é a resposta certa.

## Agrupar para contar

```sql
mysql> SELECT l.assunto,
    ->        COUNT(*) AS emprestimos
    -> FROM emprestimos em
    -> JOIN exemplares e ON e.id = em.exemplar_id
    -> JOIN livros l ON l.id = e.livro_id
    -> WHERE em.retirado_em >= '2027-02-01'
    ->   AND em.retirado_em <  '2027-03-01'
    -> GROUP BY l.assunto
    -> ORDER BY emprestimos DESC;
+------------+-------------+
| assunto    | emprestimos |
+------------+-------------+
| infantil   |         214 |
| literatura |         188 |
| referencia |          12 |
+------------+-------------+
3 rows in set (0.01 sec)
```

`GROUP BY` junta as linhas que têm o mesmo valor na coluna indicada e
produz **uma linha por grupo**. As funções de agregação — `COUNT`, `SUM`,
`AVG`, `MIN`, `MAX` — operam dentro de cada grupo.

Essa é a resposta que a prestação de contas do edital pede, e ela substitui
o programa PHP de três laços aninhados do capítulo @cap:repeticoes por nove
linhas que o banco resolve em centésimos de segundo.

Repare também no filtro de data: `>= '2027-02-01' AND < '2027-03-01'`, em
vez de `BETWEEN '2027-02-01' AND '2027-02-28'`. A segunda forma perde os
empréstimos do dia 28 depois das 00h00, porque a coluna é `DATETIME` e
`'2027-02-28'` significa meia-noite em ponto. O intervalo meio aberto —
inclui o início, exclui o fim — não tem esse problema e nem precisa saber
quantos dias o mês tem.

:::pitfall
Para filtrar **depois** de agrupar, o `WHERE` não serve: ele roda antes do
`GROUP BY` e não enxerga o resultado da contagem. Existe `HAVING` para isso:

```sql
GROUP BY l.assunto
HAVING COUNT(*) > 50
```

A regra: `WHERE` filtra linhas, `HAVING` filtra grupos. Colocar
`COUNT(*) > 50` no `WHERE` dá erro; colocar `assunto = 'infantil'` no
`HAVING` funciona e é mais lento, porque o banco agrupa tudo para depois
jogar fora.
:::

## Quatro milhões de linhas

:::story A busca de 2011
— Quanto tempo demora a busca do Sistema? — perguntou Márcia.

— Depende — disse Vera.

— Depende de quê?

— Da hora. De manhã é rápido. Depois do almoço trava.

Dedé pediu a consulta. Nonato lembrava de cabeça:

```sql
SELECT * FROM livros WHERE titulo LIKE '%sertao%'
```

Ele rodou com uma palavra na frente:

```text
mysql> EXPLAIN SELECT * FROM livros
    -> WHERE titulo LIKE '%sertao%';
+------+------+------+-------------+
| type | key  | rows | Extra       |
+------+------+------+-------------+
| ALL  | NULL | 4000 | Using where |
+------+------+------+-------------+
```

— `type: ALL` — disse ele. — Ele lê a tabela inteira.

— Quatro mil linhas é muito?

— Para um livro, não. O problema é o `exemplares`, que faz a mesma coisa com
oito mil, e o `emprestimos`, com quatrocentos mil desde 2009. Cada busca
soma.

Márcia anotou.

— E depois do almoço?

— Depois do almoço tem quinze pessoas usando ao mesmo tempo.
:::

`EXPLAIN` na frente de qualquer `SELECT` mostra o plano de execução: o que o
banco pretende fazer antes de fazer. A saída real tem doze colunas; as
quatro acima são as que decidem quase tudo.

| Coluna | O que significa |
|---|---|
| `type` | como as linhas são alcançadas. `ALL` é varredura completa |
| `key` | qual índice foi usado. `NULL` é nenhum |
| `rows` | quantas linhas o banco estima que vai **ler** |
| `Extra` | avisos, entre eles `Using filesort` e `Using temporary` |

Tabela: A leitura rápida: `type: ALL` com `rows` alto é uma consulta que vai
piorar sozinha conforme a tabela crescer.

Um **índice** é uma estrutura à parte que o banco mantém ordenada, para não
precisar varrer tudo. É a diferença entre procurar uma palavra folheando o
livro inteiro e procurá-la no índice remissivo do fim.

```sql
mysql> CREATE INDEX idx_emprestimos_leitor
    -> ON emprestimos (leitor_id);
Query OK, 0 rows affected (0.09 sec)

mysql> EXPLAIN SELECT * FROM emprestimos WHERE leitor_id = 47;
+------+------------------------+------+
| type | key                    | rows |
+------+------------------------+------+
| ref  | idx_emprestimos_leitor |    7 |
+------+------------------------+------+
```

De 400.000 linhas lidas para 7. O `type` saiu de `ALL` para `ref`, e a
consulta passou a custar o mesmo com quatrocentos mil ou com quatro milhões
de empréstimos.

Mas repare no que o índice **não** conserta: a busca do Nonato continua
lendo tudo.

```sql
mysql> CREATE INDEX idx_livros_titulo ON livros (titulo);

mysql> EXPLAIN SELECT * FROM livros WHERE titulo LIKE '%sertao%';
+------+------+------+
| type | key  | rows |
+------+------+------+
| ALL  | NULL | 4000 |
+------+------+------+
```

O índice existe e não foi usado. O motivo é a posição do `%`: um índice
guarda os valores **ordenados**, e ordenação só ajuda quem sabe o começo da
palavra. `LIKE 'sertao%'` usa o índice; `LIKE '%sertao%'` não pode usar,
porque o trecho procurado pode estar em qualquer posição.

:::key
Índice acelera leitura e **custa escrita**: cada `INSERT`, `UPDATE` e
`DELETE` precisa atualizar todos os índices da tabela. Uma tabela com oito
índices grava sensivelmente mais devagar que a mesma tabela com dois.

A regra prática: crie índice para as colunas que aparecem em `WHERE`, em
`JOIN` e em `ORDER BY` de consultas que rodam muito. Não crie por precaução.
E confira com `EXPLAIN` se ele está sendo usado — índice criado e ignorado é
o pior dos dois mundos: custa a escrita e não paga a leitura.
:::

Para busca por trecho no meio do texto, o caminho no MySQL é outro: um
índice `FULLTEXT`, que indexa palavras em vez de valores inteiros. É a saída
para a busca da Vera, e ela combina com a chave de busca normalizada do
capítulo @cap:strings — o índice encontra a palavra, a normalização garante
que "SERTAO" e "Sertão" sejam a mesma palavra.

## Tudo ou nada

Registrar um empréstimo são duas gravações: a linha em `emprestimos` e a
mudança de estado do exemplar. Se a primeira funcionar e a segunda falhar, o
sistema fica com um empréstimo cujo exemplar continua marcado como
disponível — e alguém empresta o mesmo livro duas vezes.

```sql
mysql> START TRANSACTION;
Query OK, 0 rows affected (0.00 sec)

mysql> INSERT INTO emprestimos
    ->   (exemplar_id, leitor_id, retirado_em, devolver_ate)
    -> VALUES (1, 1, NOW(), '2027-02-18');
Query OK, 1 row affected (0.00 sec)

mysql> UPDATE exemplares SET estado = 'emprestado' WHERE id = 1;
Query OK, 1 row affected (0.00 sec)

mysql> COMMIT;
Query OK, 0 rows affected (0.01 sec)
```

Entre o `START TRANSACTION` e o `COMMIT`, nada do que foi feito existe para
os outros programas. No `COMMIT`, tudo passa a existir de uma vez. E se algo
der errado no meio:

```sql
mysql> ROLLBACK;
```

O banco desfaz tudo que aconteceu desde o `START TRANSACTION`, como se nada
tivesse sido digitado.

:::term Transação
Um conjunto de operações tratado como uma só: ou todas acontecem, ou nenhuma
acontece. É o que impede que uma falha no meio de uma sequência deixe o
banco num estado que a regra de negócio proíbe.

É também a resposta definitiva para a corrida do capítulo
@cap:do-arquivo-ao-banco: enquanto uma transação mexe numa linha, as outras
esperam por aquela linha — e não pelo arquivo inteiro.
:::

:::warning
O MySQL, por padrão, roda em *autocommit*: cada comando é uma transação
sozinha, confirmada na hora. Isso significa que, sem `START TRANSACTION`, o
`UPDATE` sem `WHERE` da sexta-feira do Nonato **já estava confirmado** no
instante em que ele apertou Enter. Não havia o que desfazer.

Com transação aberta, teria havido — e `ROLLBACK` teria salvado a
sexta-feira. Vale como argumento prático para abrir transação em qualquer
alteração manual que você faça em produção, mesmo de uma linha só.
:::

:::note Na sua carreira
"Depende da hora" é o tipo de relato que costuma ser descartado como
impressão, e quase sempre é a informação mais valiosa do chamado.

A Vera não sabia dizer "a consulta faz varredura completa e a contenção
aparece sob concorrência". Ela sabia dizer que de manhã era rápido e depois
do almoço travava — o que é exatamente a mesma frase, na linguagem de quem
usa.

Quando alguém descrever um problema por **quando** ele acontece, em vez de
**o que** acontece, anote o quando. Horário, dia do mês, fim de semana,
fechamento: esses padrões apontam para carga, para tarefa agendada ou para
volume acumulado, e eles são a metade do diagnóstico que não está no código.
:::

:::summary
- Chave estrangeira faz o banco garantir que toda referência aponta para
	algo que existe — para todos os programas, não só o seu.
- `RESTRICT` por padrão; `CASCADE` só quando o filho não existe sem o pai.
- `JOIN` traz os pares; `LEFT JOIN` traz tudo da esquerda, com nulo onde não
	houver par.
- `JOIN` sem `ON` produz produto cartesiano, sem erro nenhum.
- `GROUP BY` produz uma linha por grupo; `WHERE` filtra linhas, `HAVING`
	filtra grupos.
- Intervalo de data meio aberto (`>=` e `<`) evita perder o último dia.
- `EXPLAIN` mostra o plano: `type: ALL` com `rows` alto é varredura.
- Índice acelera leitura e custa escrita; `LIKE '%termo%'` não usa índice
	comum.
- Transação faz duas gravações virarem uma; sem ela, o MySQL confirma tudo
	na hora.
:::

:::milestone
O domínio da Casa Amarela existe em quatro tabelas ligadas, com as regras
garantidas pelo banco. As cinco perguntas que a Vera fez no balcão passaram
a ter resposta de uma linha cada.
:::

:::exercise level=1
Escreva a consulta que lista, para cada exemplar, o tombo, o título do livro
e o estado — ordenada por título. Depois altere-a para mostrar apenas os
exemplares em restauro.

:::answer
```sql
SELECT e.tombo, l.titulo, e.estado
FROM exemplares e
JOIN livros l ON l.id = e.livro_id
ORDER BY l.titulo;

SELECT e.tombo, l.titulo, e.estado
FROM exemplares e
JOIN livros l ON l.id = e.livro_id
WHERE e.estado = 'restauro'
ORDER BY l.titulo;
```

O `JOIN` é o certo aqui, e não o `LEFT JOIN`: todo exemplar tem livro, e a
chave estrangeira garante isso. Onde a ligação é obrigatória, os dois
devolvem o mesmo resultado — e o `JOIN` diz a quem lê que a obrigatoriedade
existe.
:::

:::exercise level=2
As cinco perguntas que a Vera fez no balcão eram: qual exemplar está com a
Dona Marlene, qual está rasgado, qual sumiu, quantos estão livres, e quais
os mais emprestados do mês. Escreva as cinco consultas.

:::answer
```sql
-- 1. qual exemplar está com a Dona Marlene
SELECT e.tombo, l.titulo, em.devolver_ate
FROM emprestimos em
JOIN exemplares e ON e.id = em.exemplar_id
JOIN livros l ON l.id = e.livro_id
JOIN leitores le ON le.id = em.leitor_id
WHERE le.nome = 'Marlene Coutinho'
  AND em.devolvido_em IS NULL;

-- 2. quais estão rasgados
SELECT e.tombo, l.titulo
FROM exemplares e
JOIN livros l ON l.id = e.livro_id
WHERE e.estado = 'danificado';

-- 3. quais sumiram
SELECT e.tombo, l.titulo
FROM exemplares e
JOIN livros l ON l.id = e.livro_id
WHERE e.estado = 'extraviado';

-- 4. quantos exemplares deste livro estão livres
SELECT COUNT(*) AS livres
FROM exemplares e
LEFT JOIN emprestimos em
  ON em.exemplar_id = e.id AND em.devolvido_em IS NULL
WHERE e.livro_id = 1
  AND e.estado = 'bom'
  AND em.id IS NULL;

-- 5. os mais emprestados do mês
SELECT l.titulo, COUNT(*) AS vezes
FROM emprestimos em
JOIN exemplares e ON e.id = em.exemplar_id
JOIN livros l ON l.id = e.livro_id
WHERE em.retirado_em >= '2027-02-01'
  AND em.retirado_em <  '2027-03-01'
GROUP BY l.id, l.titulo
ORDER BY vezes DESC
LIMIT 10;
```

A quarta é a mais interessante, e merece atenção.

Ela usa `LEFT JOIN` com a condição de "em aberto" **dentro do `ON`**, e
depois filtra `em.id IS NULL` no `WHERE`. Isso é o idioma para "traga o que
**não** tem par": o `LEFT JOIN` traz todos os exemplares, com empréstimo
aberto quando houver, e o `IS NULL` fica só com os que não têm nenhum.

Se a condição `devolvido_em IS NULL` fosse para o `WHERE` em vez do `ON`,
ela eliminaria justamente as linhas sem par — e a consulta devolveria zero
sempre.

E repare que a quinta responde a pergunta do capítulo
@cap:o-que-vamos-construir: ela conta por **livro**, agrupando os
empréstimos de todos os exemplares daquele título. Contar por exemplar seria
`GROUP BY e.id`, e responderia outra coisa.
:::

:::exercise level=3
A operação de devolução faz três coisas: grava a data em `emprestimos`,
calcula a multa, e muda o estado do exemplar para disponível. Escreva-a como
transação e responda: o que acontece se a conexão cair entre a segunda e a
terceira? E o que aconteceria sem a transação?

:::answer
```sql
START TRANSACTION;

UPDATE emprestimos
SET devolvido_em = NOW(),
    multa_em_centavos = 720
WHERE id = 3315
  AND devolvido_em IS NULL;

UPDATE exemplares
SET estado = 'bom'
WHERE id = (SELECT exemplar_id FROM emprestimos WHERE id = 3315);

COMMIT;
```

**Se a conexão cair antes do `COMMIT`**, o banco desfaz tudo sozinho. Não
existe estado intermediário: o empréstimo continua aberto, o exemplar
continua emprestado, e a devolução pode ser refeita do começo. O
atendimento repete a operação e ninguém fica sabendo.

**Sem a transação**, cada `UPDATE` é confirmado no instante em que roda. A
queda entre os dois deixa o banco num estado que a regra de negócio proíbe:
empréstimo devolvido, exemplar marcado como emprestado. O livro volta para a
estante e o sistema recusa emprestá-lo de novo, para sempre, até alguém
descobrir e corrigir na mão.

Esse estado é pior do que a falha inteira, por um motivo que vale guardar:
**a falha avisa, o estado inconsistente não.** A operação que cai no meio
mostra um erro na tela e alguém repete. A que grava pela metade termina
dizendo "devolvido com sucesso".

Duas observações sobre a consulta.

O `AND devolvido_em IS NULL` do primeiro `UPDATE` não é decoração: ele
impede que uma devolução registrada duas vezes sobrescreva a data original e
recalcule a multa. Quando `Rows matched` vier `0`, é porque alguém já
devolveu.

E a multa aparece aqui como número pronto, o que é uma simplificação: ela
depende de `devolver_ate`, da data de hoje e da regra vigente. Calcular
regra de negócio dentro do SQL é possível e quase sempre indesejável — o
cálculo mora no PHP, que é onde ele pode ser conferido linha a linha.
:::
