---
title: "SQL: as cinco frases que resolvem o dia"
number: 13
slug: sql-do-zero
part: p2
kicker: "Um UPDATE sem WHERE numa sexta-feira devolveu oito mil livros que ninguém tinha devolvido."
goal: >-
  Criar tabela escolhendo o tipo de cada coluna com critério, inserir,
  consultar com filtro e ordenação, e alterar exatamente as linhas que você
  quis alterar.
---

:::story O Nonato voltou
O Nonato voltou de férias numa segunda, e às 9h40 estava numa sala com
quatro pessoas e um projetor mostrando a estrutura do banco da Casa Amarela.

Ele tinha escrito aquilo em 2009, num fim de semana, aos vinte e três anos,
por mil e duzentos reais.

— Essa coluna aqui — disse Tainá, apontando. — `devolvido`. É só um zero ou
um um?

— É.

— E a data da devolução fica onde?

Nonato olhou a tela por um tempo.

— Não fica.

— E se alguém perguntar quando um livro voltou?

— Ninguém perguntou em quinze anos.

Márcia, sem levantar os olhos:

— A prestação de contas do edital pede o movimento do acervo por mês.

Nonato olhou de novo para a tela, mais tempo dessa vez.

— Então agora alguém perguntou.
:::

Um campo que guarda "sim ou não" custa um byte e joga fora a data. Um campo
que guarda a data custa três bytes e responde as duas perguntas: quem tem
data devolveu; quem não tem, não devolveu.

Essa decisão de dois bytes é o assunto deste capítulo. Ela se chama
**escolher o tipo da coluna**, acontece uma vez, e a Casa Amarela conviveu
quinze anos com a versão errada dela.

## Desenhar a ficha antes de preencher

```sql
mysql> USE casa_amarela;
Database changed

mysql> CREATE TABLE livros (
    ->   id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    ->   titulo  VARCHAR(200) NOT NULL,
    ->   autor   VARCHAR(150) NOT NULL,
    ->   isbn    CHAR(13)     NULL,
    ->   assunto VARCHAR(40)  NOT NULL,
    ->   ano     SMALLINT     NULL,
    ->   PRIMARY KEY (id),
    ->   UNIQUE KEY uk_livros_isbn (isbn)
    -> ) ENGINE=InnoDB;
Query OK, 0 rows affected (0.04 sec)
```

Dez linhas que decidem muita coisa. Vale destrinchar em quatro partes.

**O nome e a lista de colunas.** `CREATE TABLE livros` cria o maço de fichas;
cada linha de dentro dos parênteses é um campo impresso na ficha, com nome e
tipo.

**`NOT NULL` e `NULL`.** `NOT NULL` significa "esta coluna nunca pode ficar
em branco" — o banco recusa a gravação. `NULL` significa "pode ficar em
branco", e é uma afirmação sobre o negócio: nem todo livro tem ISBN, porque
o ISBN só existe desde 1970 e a Casa Amarela tem edições anteriores.

**`PRIMARY KEY (id)`.** Uma coluna que identifica a linha, sem repetir e sem
ficar vazia. É o número de tombo do papel, promovido a regra do banco.

**`UNIQUE KEY`.** Diz que não pode haver duas linhas com o mesmo ISBN. É
diferente de chave primária: uma tabela tem uma chave primária e pode ter
quantas restrições de unicidade quiser.

:::term DDL e DML
Comandos SQL se dividem em duas famílias. **DDL** (*Data Definition
Language*) mexe na estrutura: `CREATE`, `ALTER`, `DROP`. **DML** (*Data
Manipulation Language*) mexe nos dados: `INSERT`, `SELECT`, `UPDATE`,
`DELETE`.

A diferença prática é que DDL é caro de desfazer e DML não. Criar uma tabela
errada custa uma tarde; inserir uma linha errada custa um `DELETE`.
:::

O `AUTO_INCREMENT` faz o banco atribuir o próximo número livre sozinho:
você insere um livro sem informar `id` e ele vira 1, o próximo vira 2. Isso
poupa a pergunta "qual foi o último?", que num sistema com dois atendentes é
a corrida do capítulo @cap:do-arquivo-ao-banco de novo.

E o `ENGINE=InnoDB` no fim escolhe o mecanismo de armazenamento. É o padrão
no MySQL 8 e é o que você quer: é o único que faz transação e que garante
chave estrangeira. Escrever explicitamente custa doze caracteres e evita
herdar o padrão de um servidor antigo.

Para conferir o que ficou gravado:

```sql
mysql> DESCRIBE livros;
+---------+------------------+------+-----+---------+----------------+
| Field   | Type             | Null | Key | Default | Extra          |
+---------+------------------+------+-----+---------+----------------+
| id      | int unsigned     | NO   | PRI | NULL    | auto_increment |
| titulo  | varchar(200)     | NO   |     | NULL    |                |
| autor   | varchar(150)     | NO   |     | NULL    |                |
| isbn    | char(13)         | YES  | UNI | NULL    |                |
| assunto | varchar(40)      | NO   |     | NULL    |                |
| ano     | smallint         | YES  |     | NULL    |                |
+---------+------------------+------+-----+---------+----------------+
6 rows in set (0.00 sec)
```

`DESCRIBE` mostra a estrutura de uma tabela. É o primeiro comando a rodar
quando você abre um banco que não conhece — antes de ler qualquer código.

## O tipo é uma decisão de negócio

A escolha de cada tipo foi deliberada, e cada uma responde uma pergunta
sobre a Casa Amarela.

| Tipo | Guarda | Quando usar |
|---|---|---|
| `INT` | inteiro até ~2,1 bilhões | identificador, contagem, centavos |
| `SMALLINT` | inteiro até 32.767 | ano, quantidade pequena |
| `VARCHAR(n)` | texto de tamanho variável, até `n` | título, nome, endereço |
| `CHAR(n)` | texto de tamanho **fixo** | ISBN, UF, código de tamanho conhecido |
| `TEXT` | texto longo, sem limite prático | observação, descrição |
| `DATE` | só a data | data de publicação, prazo |
| `DATETIME` | data e hora | quando o empréstimo aconteceu |
| `DECIMAL(p,s)` | número exato com casas | valor monetário |
| `BOOLEAN` | verdadeiro ou falso | apelido de `TINYINT(1)` |

Tabela: Não há `FLOAT` nesta lista de propósito. Ele existe e serve para
medida física — peso, temperatura, coordenada — e nunca para dinheiro, pelo
motivo do capítulo @cap:conversao-automatica.

Quatro dessas escolhas merecem explicação, porque são onde as pessoas erram.

**`VARCHAR(200)` e não `VARCHAR(255)`.** O número 255 virou hábito por um
motivo histórico que não existe mais: até o MySQL 5.0, um `VARCHAR` de até
255 caracteres usava um byte a menos de controle. Hoje isso não muda nada em
disco, e o número que você escreve passou a ser o que ele parece ser: uma
**afirmação sobre o negócio**. `VARCHAR(200)` diz "título de livro não passa
de duzentos caracteres". Se passar, o banco recusa — e é bom que recuse,
porque um título de oitocentos caracteres é quase sempre um erro de
importação.

**`CHAR(13)` para ISBN.** ISBN tem treze dígitos, sempre. `CHAR` é para
tamanho fixo e é ligeiramente mais eficiente nesse caso. E repare que ele é
texto, não número: um ISBN pode começar com zero, e zero à esquerda morre em
coluna numérica.

**`DATETIME` e não `TIMESTAMP`.** Os dois guardam data e hora. A diferença é
que `TIMESTAMP` converte para UTC ao gravar e converte de volta ao ler,
usando o fuso configurado no servidor — o que é ótimo para sistema
internacional e é uma armadilha quando alguém muda a configuração do
servidor e todas as datas antigas mudam de valor. `DATETIME` guarda o que
você mandou. Para uma biblioteca de bairro, `DATETIME` é mais previsível.

**`DECIMAL(10,2)` para dinheiro, se você usar dinheiro no banco.** Ele
guarda o número em base decimal, exato, com dez dígitos no total e dois
depois da vírgula. É a escolha certa quando o valor mora no banco.

:::pitfall
Há um detalhe de PHP que decide essa escolha e quase nunca é mencionado: uma
coluna `DECIMAL` **volta para o PHP como string**. O PHP não tem tipo
decimal exato, então o driver devolve `"7.20"` em vez de um número — porque
convertê-lo para `float` desfaria a exatidão que a coluna garantia.

Isso significa que você precisa decidir o que fazer com aquela string em
todo lugar onde ela aparece. A alternativa é guardar `INT` em centavos, que
volta como inteiro e fecha a conta dos dois lados. É a escolha deste livro, e a coluna se chama
`multa_em_centavos`.

`DECIMAL` continua certo — em sistema financeiro sério é o que se usa, com
uma classe que trata a string. A escolha aqui é por coerência, não por
superioridade.
:::

:::key
A regra que evita a maior parte dos problemas de esquema: **`NOT NULL` por
padrão, `NULL` por exceção justificada.**

Toda coluna começa proibida de ficar vazia. Quando você quiser permitir,
pare e escreva numa frase por que aquele dado pode não existir. "Nem todo
livro tem ISBN" é uma justificativa. "Vai que um dia falta" não é — esse é o
caminho para uma tabela em que metade das colunas aceita nulo e nenhuma
consulta pode confiar em nada.
:::

## Inserir

```sql
mysql> INSERT INTO livros (titulo, autor, isbn, assunto, ano)
    -> VALUES ('O Cortiço', 'Aluísio Azevedo', '9788572326972',
    ->         'literatura', 1890);
Query OK, 1 row affected (0.01 sec)
```

A lista de colunas vem primeiro, os valores depois, na mesma ordem. O `id`
não foi informado porque o `AUTO_INCREMENT` cuida dele.

Texto vai entre **aspas simples**. Número vai sem aspas. Essa é a única
regra de formatação que você precisa guardar agora, e é a mesma que vai
causar o problema de segurança do capítulo seguinte.

Várias linhas de uma vez:

```sql
mysql> INSERT INTO livros (titulo, autor, assunto, ano) VALUES
    ->   ('Vidas Secas', 'Graciliano Ramos', 'literatura', 1938),
    ->   ('Grande Sertão', 'Guimarães Rosa', 'literatura', 1956),
    ->   ('O Pequeno Príncipe', 'Saint-Exupéry', 'infantil', 1943);
Query OK, 3 rows affected (0.01 sec)
Records: 3  Duplicates: 0  Warnings: 0
```

Três linhas num comando só. Repare que `isbn` foi omitido: como a coluna
aceita `NULL`, o banco grava nulo sem reclamar. Se você omitisse `titulo`,
que é `NOT NULL`, a história seria outra:

```sql
mysql> INSERT INTO livros (autor, assunto) VALUES ('Alguém', 'geral');
ERROR 1364 (HY000): Field 'titulo' doesn't have a default value
```

Essa recusa é o trabalho do esquema aparecendo. O erro veio na hora da
gravação, com o nome da coluna, e não seis meses depois numa tela que mostra
um título em branco.

## Consultar

```sql
mysql> SELECT id, titulo, ano FROM livros;
+----+--------------------+------+
| id | titulo             | ano  |
+----+--------------------+------+
|  1 | O Cortiço          | 1890 |
|  2 | Vidas Secas        | 1938 |
|  3 | Grande Sertão      | 1956 |
|  4 | O Pequeno Príncipe | 1943 |
+----+--------------------+------+
4 rows in set (0.00 sec)
```

`SELECT` escolhe as colunas, `FROM` escolhe a tabela. Existe `SELECT *`, que
traz todas as colunas, e é conveniente no terminal e ruim em programa:
quando alguém acrescentar uma coluna `TEXT` de observação, o seu programa
passa a trazê-la em toda consulta sem nunca usá-la.

E existe o `WHERE`, que é onde a consulta começa a valer alguma coisa:

```sql
mysql> SELECT titulo, ano FROM livros
    -> WHERE assunto = 'literatura' AND ano > 1900;
+---------------+------+
| titulo        | ano  |
+---------------+------+
| Vidas Secas   | 1938 |
| Grande Sertão | 1956 |
+---------------+------+
2 rows in set (0.00 sec)
```

O `WHERE` é a linha que decide quais linhas entram. Ele aceita as
comparações de sempre — `=`, `<>`, `>`, `<`, `>=`, `<=` — e mais três que
valem conhecer:

```sql
mysql> SELECT titulo FROM livros WHERE titulo LIKE '%Sert%';
mysql> SELECT titulo FROM livros WHERE ano BETWEEN 1930 AND 1950;
mysql> SELECT titulo FROM livros
    -> WHERE assunto IN ('infantil', 'juvenil');
mysql> SELECT titulo FROM livros WHERE isbn IS NULL;
```

`LIKE` procura por pedaço de texto, com `%` valendo por "qualquer coisa".
`BETWEEN` é atalho para dois comparadores. `IN` é atalho para vários `OR`.

E a última é a que pega todo mundo: para comparar com nulo, **não** se usa
`= NULL`. Usa-se `IS NULL`. O motivo é que, em SQL, `NULL` não é um valor —
é a ausência de valor —, e a comparação `algo = NULL` não devolve nem
verdadeiro nem falso: devolve desconhecido, e o `WHERE` descarta o
desconhecido junto com o falso.

:::pitfall
Escreva `SELECT ... WHERE isbn = NULL` e o MySQL não dá erro nenhum.
Devolve zero linhas, calado, mesmo havendo três livros sem ISBN.

É o pior tipo de defeito: sintaxe válida, execução sem aviso, resposta
errada. Quando uma consulta devolver zero linhas e você tiver certeza de que
deveria devolver alguma, o `= NULL` é o primeiro suspeito.
:::

Ordenar, contar e limitar:

```sql
mysql> SELECT titulo, ano FROM livros
    -> ORDER BY ano DESC
    -> LIMIT 2;
+--------------------+------+
| titulo             | ano  |
+--------------------+------+
| Grande Sertão      | 1956 |
| O Pequeno Príncipe | 1943 |
+--------------------+------+
2 rows in set (0.00 sec)

mysql> SELECT COUNT(*) FROM livros WHERE assunto = 'literatura';
+----------+
| COUNT(*) |
+----------+
|        3 |
+----------+
1 row in set (0.00 sec)
```

`ORDER BY` ordena — `ASC` é crescente e é o padrão, `DESC` é decrescente.
`LIMIT` corta o resultado. `COUNT(*)` conta linhas sem trazê-las, o que é a
diferença entre perguntar "quantos são?" e carregar oito mil registros para
contá-los em PHP.

:::key
A ordem em que o SQL é **escrito** não é a ordem em que ele é **executado**.
O banco aplica primeiro o `FROM`, depois o `WHERE`, depois o `SELECT` das
colunas, depois o `ORDER BY` e por último o `LIMIT`.

Isso explica um comportamento que confunde: o `WHERE` não enxerga apelidos
criados no `SELECT`, porque ele rodou antes deles existirem. E explica por
que `LIMIT 10` numa tabela de um milhão de linhas pode ser lento — ele corta
no fim, depois de o banco já ter encontrado e ordenado tudo que o filtro
alcançou.
:::

## Alterar e remover

:::story Sexta-feira, 2013
— Eu já fiz isso — disse Nonato, quando o assunto chegou em `UPDATE`.

Ninguém tinha perguntado.

— Sexta-feira, 2013. A Vera pediu pra marcar como devolvido um empréstimo
que tinha voltado no sábado anterior e ninguém registrou.

Ele digitou no quadro branco, de cabeça, com a letra de quem escreveu aquilo
muitas vezes desde então:

```text
UPDATE emprestimos SET devolvido = 1
```

— Faltou o quê?

— O `WHERE` — disse Tainá.

— Faltou o `WHERE`.

Oito mil e quatrocentos empréstimos foram devolvidos às 17h48 de uma
sexta-feira. Entre eles, os mil e duzentos que estavam de fato em aberto.

— E aí?

— E aí a biblioteca não tinha backup.

Nonato apagou o quadro.

— Tem desde sábado.
:::

```sql
mysql> UPDATE livros SET assunto = 'juvenil' WHERE id = 4;
Query OK, 1 row affected (0.01 sec)
Rows matched: 1  Changed: 1  Warnings: 0
```

`UPDATE` altera, `SET` diz o quê, `WHERE` diz onde. Sem `WHERE`, altera
**todas as linhas da tabela**, e o MySQL não pergunta se você tem certeza.

Repare na segunda linha da resposta: `Rows matched: 1`. Esse número é a sua
confirmação de que o `WHERE` alcançou o que você queria. Quando ele vier
muito maior do que o esperado, alguma coisa já aconteceu.

```sql
mysql> DELETE FROM livros WHERE id = 4;
Query OK, 1 row affected (0.00 sec)
```

`DELETE` remove linhas. Sem `WHERE`, esvazia a tabela.

:::art caption="Uma linha sem `WHERE`, às 17h48 de uma sexta-feira."
src="uma-linha-sem-where-as-17h48-de-uma-sexta-feira.jpg"
Charge editorial minimalista em fundo branco: um desenvolvedor de uns
quarenta anos, de camisa xadrez, diante de um quadro branco onde escreveu
de cabeça, com letra firme, "UPDATE emprestimos SET devolvido = 1" — e nada
depois. Na parede, um relógio marca 17h48 e uma folhinha de calendário
mostra "SEXTA". Ao fundo, um fichário de empréstimos com todas as fichas
saltando ao mesmo tempo, cada uma com um carimbo de "DEVOLVIDO". Sentada,
uma estagiária com a caneta parada no ar sobre o caderno. Poucos elementos,
humor seco, estética de revista de tecnologia.
:::

:::warning
Três hábitos que evitam a sexta-feira do Nonato, em ordem de eficácia.

**Escreva o `WHERE` primeiro.** Comece a digitar pelo fim: `WHERE id = 4`, e
só depois volte e escreva o `UPDATE ... SET` na frente. Parece bobagem e é o
hábito que mais funciona, porque elimina a janela em que o comando está
sintaticamente completo e perigoso.

**Rode como `SELECT` antes.** Troque `UPDATE livros SET ...` por
`SELECT * FROM livros`, mantendo o mesmo `WHERE`. O que aparecer é
exatamente o que seria alterado. Confira, depois troque o começo.

**Ligue a rede de proteção.** O cliente do MySQL aceita a opção
`--safe-updates` (ou `-U`), que **recusa** `UPDATE` e `DELETE` sem `WHERE`
que use chave:

```text
$ mysql -u root -p -U casa_amarela

mysql> DELETE FROM livros;
ERROR 1175 (HY000): You are using safe update mode and you
tried to update a table without a WHERE that uses a KEY column
```

Coloque no seu arquivo de configuração do MySQL e esqueça que existe. No dia
em que ela salvar você, terá valido por todos os dias em que atrapalhou.
:::

E existe uma quarta proteção, que é de outra natureza: **não apagar**. Em
vez de `DELETE`, muita tabela ganha uma coluna `removido_em DATETIME NULL`,
e "remover" passa a ser preencher essa data. Nada some, dá para desfazer, e
dá para responder "quem apagou e quando". O custo é que toda consulta passa
a precisar de `WHERE removido_em IS NULL`, e esquecer isso uma vez traz os
registros apagados de volta para a tela.

:::note Na sua carreira
A primeira vez que você derrubar dado de produção, vai existir uma
tentação forte de consertar em silêncio antes que alguém perceba. Não faça
isso — e não por moral, por matemática: o tempo entre o erro e o aviso é a
variável que mais decide o tamanho do estrago.

O que funciona, em ordem: **pare de mexer**, avise quem responde pelo
sistema, diga o que aconteceu em uma frase e o que você já sabe sobre o
alcance ("um `UPDATE` sem `WHERE` na tabela de empréstimos, às 17h48, 8.412
linhas"). Só então discuta o conserto.

E repare no que o Nonato fez de certo em 2013: ele passou a contar a
história. Uma equipe em que o erro grave é contado por quem o cometeu é uma
equipe onde o próximo erro aparece rápido.
:::

:::summary
- `CREATE TABLE` desenha a ficha; `DESCRIBE` mostra o que ficou.
- O tipo da coluna é decisão de negócio: `VARCHAR(200)` afirma um limite,
	`CHAR(13)` afirma um formato, `DATE` afirma que hora não importa.
- `NOT NULL` por padrão; `NULL` só com justificativa escrita.
- Chave primária identifica a linha; `AUTO_INCREMENT` a preenche sozinho;
	`UNIQUE` impede repetição em outra coluna.
- Coluna `DECIMAL` volta para o PHP como texto — daí a opção por `INT` em
	centavos.
- `WHERE` decide quais linhas entram; nulo se compara com `IS NULL`, nunca
	com `= NULL`.
- `COUNT(*)` conta sem trazer; `ORDER BY` ordena; `LIMIT` corta no fim.
- `UPDATE` e `DELETE` sem `WHERE` alcançam a tabela inteira, sem perguntar.
:::

:::milestone
O acervo da Casa Amarela existe fora do PHP. A tabela `livros` está criada,
com tipos escolhidos e regras que o banco garante, e você consulta e altera
o que quiser pelo terminal.
:::

:::exercise level=1
Crie a tabela `leitores` com: identificador automático, nome obrigatório de
até 120 caracteres, documento único de 11 caracteres, data de cadastro, e
telefone opcional. Depois insira dois leitores e liste-os ordenados por
nome.

:::answer
```sql
CREATE TABLE leitores (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome         VARCHAR(120) NOT NULL,
  documento    CHAR(11)     NOT NULL,
  cadastro_em  DATE         NOT NULL,
  telefone     VARCHAR(20)  NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_leitores_documento (documento)
) ENGINE=InnoDB;

INSERT INTO leitores (nome, documento, cadastro_em, telefone)
VALUES
  ('Marlene Coutinho', '11122233344', '2009-03-14', NULL),
  ('Juvenal Pereira',  '55566677788', '2011-08-02', '31 9999-1234');

SELECT id, nome, cadastro_em FROM leitores ORDER BY nome;
```

```text
+----+------------------+-------------+
| id | nome             | cadastro_em |
+----+------------------+-------------+
|  2 | Juvenal Pereira  | 2011-08-02  |
|  1 | Marlene Coutinho | 2009-03-14  |
+----+------------------+-------------+
```

Três decisões que valem defender: `CHAR(11)` porque documento tem tamanho
fixo e pode começar com zero; `DATE` e não `DATETIME` porque a hora do
cadastro não interessa a ninguém; e telefone como `VARCHAR` opcional, porque
gente sem telefone existe e porque telefone tem parêntese, traço e espaço —
ele nunca é número.
:::

:::exercise level=2
Sem rodar, diga quantas linhas cada comando abaixo alteraria numa tabela
`livros` com 4.000 registros, dos quais 91 são de referência e 12 não têm
ISBN. Depois diga qual deles você não rodaria nunca.

```sql
UPDATE livros SET assunto = 'referencia' WHERE assunto = 'referência';
UPDATE livros SET ano = 2000 WHERE isbn = NULL;
UPDATE livros SET assunto = 'geral';
DELETE FROM livros WHERE id = 99999;
```

:::answer
**O primeiro:** zero ou muitas, e ninguém sabe sem olhar. Ele depende de
como os 91 registros de referência foram gravados — com acento ou sem. É um
comando de limpeza legítimo, e a forma certa de rodá-lo é conferir antes
com `SELECT COUNT(*) FROM livros WHERE assunto = 'referência';`.

**O segundo:** zero linhas, sempre, mesmo com doze livros sem ISBN. O
`= NULL` não compara com nada. O comando roda, responde `Rows matched: 0` e
não faz nada — e quem o escreveu vai passar meia hora procurando o defeito
em outro lugar. O certo é `WHERE isbn IS NULL`.

**O terceiro:** 4.000 linhas. Todas. É o comando do Nonato, com outro nome
de coluna.

**O quarto:** zero linhas, e sem consequência nenhuma. `DELETE` com `WHERE`
que não encontra ninguém simplesmente não apaga nada.

**O que eu não rodaria nunca é o terceiro** — e vale notar por que ele é
diferente do segundo. O segundo é inofensivo por acidente: ele está errado e
o erro dele o torna inócuo. O terceiro está sintaticamente perfeito e é
justamente por isso que ele destrói a tabela sem uma pergunta sequer.
:::

:::exercise level=3
A tabela `emprestimos` do Sistema, escrita em 2009, é esta:

```sql
CREATE TABLE emprestimos (
  id          INT NOT NULL AUTO_INCREMENT,
  livro_id    INT NOT NULL,
  leitor      VARCHAR(120) NOT NULL,
  data        VARCHAR(20) NOT NULL,
  devolvido   TINYINT(1) NOT NULL DEFAULT 0,
  multa       FLOAT NULL,
  PRIMARY KEY (id)
);
```

Aponte cinco problemas e escreva a versão que você proporia. Para cada
mudança, diga qual pergunta ela passa a permitir.

:::answer
**1. `leitor VARCHAR(120)` guarda o nome, não o leitor.** Dois leitores
homônimos são a mesma pessoa para essa tabela, e um leitor que muda de nome
some do próprio histórico. Vira `leitor_id INT UNSIGNED NOT NULL`, apontando
para a tabela `leitores`.
*Passa a permitir:* "quais empréstimos são desta pessoa?", com certeza.

**2. `data VARCHAR(20)` guarda data como texto.** Ordenar por essa coluna
ordena alfabeticamente: `10/03/2011` vem antes de `09/04/2011`. E qualquer
coisa cabe ali, inclusive `ontem`. Vira `retirado_em DATETIME NOT NULL`.
*Passa a permitir:* "quantos empréstimos em fevereiro?", que é literalmente
o que a prestação de contas do edital pede.

**3. `devolvido TINYINT(1)` joga fora a data da devolução.** É a coluna da
cena de abertura. Vira `devolvido_em DATETIME NULL` — quem tem data
devolveu, quem não tem está em aberto.
*Passa a permitir:* "quanto tempo os livros ficam fora, em média?" e
"quantos dias este ficou atrasado?".

**4. `multa FLOAT` é dinheiro em ponto flutuante.** Soma acumula erro e o
fechamento do mês não bate por centavos — é o mesmo defeito das mil multas
de cinquenta centavos, agora gravado em disco. Vira `multa_em_centavos INT
UNSIGNED NULL`.
*Passa a permitir:* somar oito mil multas e chegar ao mesmo número que o
caixa.

**5. Falta a data prevista de devolução.** O prazo é catorze dias, mas
catorze dias muda — em janeiro é outro, e o prazo de um empréstimo de 2011
era o de 2011. Calcular a partir da data de retirada aplica a regra de hoje
ao passado. Vira `devolver_ate DATE NOT NULL`, gravado no momento do
empréstimo.
*Passa a permitir:* "estava atrasado?", respondido com a regra vigente na
época.

```sql
CREATE TABLE emprestimos (
  id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  exemplar_id       INT UNSIGNED NOT NULL,
  leitor_id         INT UNSIGNED NOT NULL,
  retirado_em       DATETIME     NOT NULL,
  devolver_ate      DATE         NOT NULL,
  devolvido_em      DATETIME     NULL,
  multa_em_centavos INT UNSIGNED NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB;
```

Há uma sexta mudança escondida aí, e ela é a maior de todas: `livro_id`
virou `exemplar_id`. Empresta-se o objeto físico, não o título — é a
distinção do capítulo @cap:o-que-vamos-construir chegando ao banco, quinze
anos depois de a Vera ter descrito o problema no balcão.

E falta ainda uma coisa que esta versão não tem: nada impede que
`leitor_id` aponte para um leitor que não existe. Isso é trabalho de chave
estrangeira.
:::
