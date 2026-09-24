---
title: "PDO: o PHP conversando com o banco"
number: 15
slug: pdo
part: p2
kicker: "A estagiária digitou cinco caracteres no campo de busca e a tela devolveu o acervo inteiro."
goal: >-
  Conectar o PHP ao MySQL, ler e gravar com consultas preparadas, entender
  na prática por que a concatenação é um defeito de segurança, e tratar a
  falha de conexão sem entregar a senha.
---

O banco existe, as tabelas existem, as consultas funcionam no terminal.
Falta a parte em que o PHP faz as perguntas.

## Conectar

```php title="conexao.php" numbered
<?php

$dsn = 'mysql:host=127.0.0.1;port=3306'
     . ';dbname=casa_amarela;charset=utf8mb4';

$pdo = new PDO($dsn, 'root', 'senha', [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES => false,
]);

echo "conectado\n";
```

```text
$ php conexao.php
conectado
```

`PDO` é a interface padrão do PHP para banco de dados. O mesmo código
funciona com MySQL, PostgreSQL e SQLite trocando só a primeira linha — o que
não significa que o SQL seja o mesmo, e é por isso que este livro ensinou
SQL antes.

:::term DSN
*Data Source Name*: o texto que descreve onde está o banco. Começa com o
nome do driver (`mysql:`), seguido de pares `chave=valor` separados por
ponto e vírgula.

O `charset=utf8mb4` não é opcional. Sem ele, a conexão pode negociar uma
codificação diferente da do banco, e o acento que estava certo no MySQL
chega errado no PHP — o segundo José de Alencar do capítulo @cap:strings,
nascendo do outro lado do cabo.
:::

As três opções do array merecem uma frase cada, porque as três mudam o
comportamento de forma importante.

**`ERRMODE_EXCEPTION`** faz o PDO lançar uma exceção quando algo dá errado.
O padrão histórico era ficar calado e devolver `false`, o que produz o
programa que segue em frente com um erro de banco que ninguém viu. Ligue
sempre.

**`FETCH_ASSOC`** faz cada linha voltar como array de chaves nomeadas —
`['titulo' => 'O Cortiço']`. Sem isso, o padrão traz **cada valor
duplicado**, uma vez pelo nome e outra pela posição, o que dobra o tamanho
do resultado e confunde todo `foreach`.

**`EMULATE_PREPARES => false`** faz o PDO mandar a consulta preparada para o
servidor de verdade, em vez de montá-la em PHP e mandar o texto pronto. A
diferença aparece daqui a três seções, e ela é de segurança.

## Perguntar

```php title="listar.php" numbered
<?php

require 'conexao.php';

$sql = 'SELECT id, titulo, ano FROM livros ORDER BY titulo';

foreach ($pdo->query($sql) as $livro) {
    echo $livro['id'], ' - ', $livro['titulo'], "\n";
}
```

```text
$ php listar.php
3 - Grande Sertão
1 - O Cortiço
4 - O Pequeno Príncipe
2 - Vidas Secas
```

`query()` executa uma consulta e devolve algo que dá para percorrer com
`foreach`, uma linha por vez. Cada linha é um array com as colunas que o
`SELECT` pediu.

Repare que `query()` serve para consulta **sem valor de fora**. No instante
em que houver um valor vindo do usuário, ela deixa de servir — e é sobre
isso o resto do capítulo.

## Cinco caracteres

:::story Cinco caracteres
Na quinta, em homologação, Tainá estava testando a tela de busca do Sistema
antiga, para documentar o que precisava ser refeito.

Digitou "sertao". Vieram dois livros.

Digitou "xxxxx". Não veio nada.

Digitou `' OR '1'='1`.

Vieram quatro mil.

Ela chamou o Cléber, que olhou a tela por um tempo e disse a frase que
resume o problema:

— Mas você não pode digitar isso.

— O campo deixou.

— Mas não pode.

— Cléber, o campo deixou.

Ele pediu que ela não fizesse de novo. Tainá perguntou se podia fazer em
produção, para mostrar para o Dr. Aurélio.

A resposta demorou.

— Não. Mas escreve num e-mail pra mim.
:::

O `login.php` do Sistema já tinha aparecido. A busca é o mesmo problema com
outra consequência:

```php title="busca_do_sistema.php" numbered
<?php

require 'conexao.php';

$termo = $_GET['q'] ?? '';

$sql = "SELECT id, titulo FROM livros
        WHERE titulo LIKE '%{$termo}%'";

foreach ($pdo->query($sql) as $livro) {
    echo $livro['titulo'], "\n";
}
```

Com `$termo = 'sertao'`, a consulta que chega ao banco é:

```sql
SELECT id, titulo FROM livros WHERE titulo LIKE '%sertao%'
```

Com `$termo = "' OR '1'='1"`, a consulta que chega ao banco é:

```sql
SELECT id, titulo FROM livros WHERE titulo LIKE '%' OR '1'='1%'
```

Leia com calma. A aspa simples que a Tainá digitou **fechou** a aspa que o
programa tinha aberto. A partir dali, o que ela digitou deixou de ser um
valor procurado e passou a ser parte do comando. O `OR '1'='1'` é uma
condição sempre verdadeira, e o `WHERE` passou a aceitar todas as linhas.

:::term Injeção de SQL
Quando um dado vindo de fora é interpretado como parte do comando em vez de
como valor. O nome descreve o mecanismo: o atacante **injeta** instrução
dentro de uma frase que deveria ser só texto.

Não é um defeito do MySQL nem do PHP. É consequência de montar comando
grudando texto — e acontece igual em qualquer linguagem e qualquer banco.
:::

Quatro mil títulos vazando é o caso simpático. A mesma porta aceita
`'; DROP TABLE emprestimos; --`, aceita ler a tabela de usuários, e aceita
uma condição que devolve a senha de alguém caractere a caractere. O limite
não é o que o campo de busca faz: é o que o usuário do banco tem permissão
de fazer.

:::warning
Não teste isto em sistema que não seja seu, nem em produção — nem para
provar um ponto, nem com boa intenção. Rodar a consulta acima contra um
sistema de terceiros é acesso não autorizado, e o fato de o campo ter
deixado não muda isso.

O lugar certo é o banco `casa_amarela` que você criou na sua máquina. Rode
lá, veja acontecer, e depois conserte.
:::

## O valor nunca é comando

```php title="busca_segura.php" numbered
<?php

require 'conexao.php';

$termo = $_GET['q'] ?? '';

$sql = 'SELECT id, titulo FROM livros WHERE titulo LIKE ?';

$consulta = $pdo->prepare($sql);
$consulta->execute(['%' . $termo . '%']);

foreach ($consulta as $livro) {
    echo $livro['titulo'], "\n";
}
```

O `?` é um **marcador de posição**. A consulta vai para o servidor **sem** o
valor, é analisada e transformada em plano de execução, e só depois o valor
é enviado — separadamente, já como valor.

Com `$termo = "' OR '1'='1"`, o banco procura livros cujo título contenha
literalmente o texto `' OR '1'='1`. Não encontra nenhum. A aspa não fecha
nada porque, quando ela chega, não há mais comando para fechar: ele já foi
analisado.

:::key
Essa é a ideia central, e ela vale para o resto da sua carreira:
**consulta preparada não escapa o valor — ela separa o valor do comando.**

Existem funções de escape, e elas funcionam, e não são o caminho. Escapar
depende de você lembrar de fazê-lo em todos os pontos, com a função certa
para o banco certo, com a codificação certa. Separar depende de você usar
`prepare` — e o dia em que você esquecer, o erro é visível no código, não
invisível no resultado.
:::

Repare no detalhe do `%`: ele está no **valor**, em `'%' . $termo . '%'`, e
não na consulta. Ele faz parte do que se procura, não do comando.

Marcadores também podem ter nome, o que compensa a partir do terceiro:

```php title="nomeados.php" numbered
<?php

require 'conexao.php';

$sql = 'SELECT titulo, ano FROM livros
        WHERE assunto = :assunto
          AND ano >= :desde
        ORDER BY ano';

$consulta = $pdo->prepare($sql);
$consulta->execute([
    'assunto' => 'literatura',
    'desde' => 1900,
]);

foreach ($consulta as $livro) {
    echo $livro['ano'], ' ', $livro['titulo'], "\n";
}
```

```text
1938 Vidas Secas
1956 Grande Sertão
```

Com `?`, a ordem do array precisa bater com a ordem dos marcadores. Com
`:nome`, não precisa — e a chamada fica legível sem consultar a consulta.

:::pitfall
Há um lugar onde marcador **não** funciona: nomes de tabela e de coluna.

```php
// não funciona
$consulta = $pdo->prepare('SELECT * FROM livros ORDER BY ?');
$consulta->execute([$_GET['ordem']]);
```

O banco precisa saber por qual coluna ordenar **para montar o plano**, e o
plano é montado antes de o valor chegar. O que o código acima faz é ordenar
por uma constante de texto, o que não ordena nada.

Como a ordenação vem de fora com frequência — o usuário clica no cabeçalho
da tabela —, a saída é uma **lista de permitidos**:

```php
$colunas = ['titulo', 'ano', 'autor'];
$ordem = $_GET['ordem'] ?? 'titulo';

if (!in_array($ordem, $colunas, true)) {
    $ordem = 'titulo';
}

$sql = "SELECT * FROM livros ORDER BY {$ordem}";
```

É o único caso deste livro em que um valor externo entra na consulta por
concatenação — e ele só é seguro porque o valor foi **substituído** por um
item de uma lista fixa, não validado. A diferença importa: validar aceita o
que passou no teste; substituir só deixa passar o que você escreveu.
:::

## O formato do que volta

Três formas de receber o resultado, para três perguntas diferentes:

```php title="formas.php" numbered
<?php

require 'conexao.php';

$c = $pdo->prepare('SELECT id, titulo FROM livros WHERE id = ?');
$c->execute([1]);
$livro = $c->fetch();

print_r($livro);

$c = $pdo->prepare('SELECT id, titulo FROM livros WHERE ano > ?');
$c->execute([1900]);
$livros = $c->fetchAll();

echo count($livros), " livros\n";

$c = $pdo->prepare('SELECT COUNT(*) FROM livros WHERE assunto = ?');
$c->execute(['literatura']);
$total = $c->fetchColumn();

echo $total, "\n";
```

```text
Array
(
    [id] => 1
    [titulo] => O Cortiço
)
3 livros
3
```

`fetch()` traz **uma** linha e avança; devolve `false` quando acabou.
`fetchAll()` traz todas de uma vez, num array de arrays. `fetchColumn()`
traz um valor só — feito para `COUNT`, `SUM`, `MAX` e para quando você
quer um campo de uma linha.

:::pitfall
`fetchAll()` carrega o resultado inteiro na memória do PHP. Numa consulta
que devolve vinte linhas, é o que você quer. Numa que devolve oitocentos
mil, é o `Allowed memory size exhausted` aparecendo com nome e sobrenome.

Quando o resultado for grande, percorra com `foreach` direto no objeto da
consulta, que traz uma linha por vez. E quando o resultado for grande porque
a consulta não tem filtro, o problema não era a memória.
:::

E `fetch()` devolvendo `false` merece cuidado:

```php
$livro = $c->fetch();

if ($livro === false) {
    echo "livro nao encontrado\n";
}
```

O `=== false` é obrigatório. Um `if (!$livro)` trataria como "não
encontrado" qualquer resultado falso. Uma linha de banco nunca é falsa, então
aqui funcionaria — e o hábito é o mesmo que fez quatro leitores sem multa
aparecerem no relatório de pendências da Vera.

## Gravar

```php title="cadastrar.php" numbered
<?php

require 'conexao.php';

$sql = 'INSERT INTO livros (titulo, autor, assunto, ano)
        VALUES (:titulo, :autor, :assunto, :ano)';

$consulta = $pdo->prepare($sql);
$consulta->execute([
    'titulo' => 'Memórias Póstumas de Brás Cubas',
    'autor' => 'Machado de Assis',
    'assunto' => 'literatura',
    'ano' => 1881,
]);

$id = (int) $pdo->lastInsertId();

echo "livro ", $id, " cadastrado\n";
```

```text
livro 5 cadastrado
```

`lastInsertId()` devolve o valor que o `AUTO_INCREMENT` atribuiu. Ele vem
como texto, daí o `(int)` — o mesmo motivo da coluna `DECIMAL`: o PHP recebe
do banco aquilo que cabe com segurança em texto.

Para `UPDATE` e `DELETE`, o que interessa é quantas linhas foram atingidas:

```php title="devolver.php" numbered
<?php

require 'conexao.php';

$sql = 'UPDATE emprestimos
        SET devolvido_em = NOW()
        WHERE id = ? AND devolvido_em IS NULL';

$consulta = $pdo->prepare($sql);
$consulta->execute([3315]);

if ($consulta->rowCount() === 0) {
    echo "emprestimo inexistente ou ja devolvido\n";
} else {
    echo "devolucao registrada\n";
}
```

`rowCount()` devolve o número de linhas alteradas. Zero não é erro — é
informação, e aqui é a informação que separa "não existe" de "já foi
devolvido antes". Sem essa checagem, o programa diria "devolução registrada"
para um empréstimo que não existe.

E a transação do capítulo anterior, em PHP:

```php title="emprestar.php" numbered
<?php

require 'conexao.php';

$pdo->beginTransaction();

try {
    $c = $pdo->prepare(
        'INSERT INTO emprestimos
           (exemplar_id, leitor_id, retirado_em, devolver_ate)
         VALUES (?, ?, NOW(), ?)'
    );
    $c->execute([1, 1, '2027-02-18']);

    $c = $pdo->prepare(
        'UPDATE exemplares SET estado = ? WHERE id = ?'
    );
    $c->execute(['emprestado', 1]);

    $pdo->commit();
    echo "emprestimo registrado\n";
} catch (PDOException $e) {
    $pdo->rollBack();
    throw $e;
}
```

O `try` executa o bloco; se qualquer coisa lá dentro lançar um erro, o
`catch` recebe o objeto do erro e roda o `rollBack()`, desfazendo as duas
gravações. O `throw $e` no fim repassa o problema adiante em vez de
escondê-lo — desfazer a transação e fingir que nada aconteceu seria pior do
que o defeito original.

Essa estrutura de `try`/`catch` é o assunto de um trecho do livro
mais adiante; por ora ela aparece porque uma transação sem ela é uma
transação que não protege nada.

## Quando a conexão falha

```php title="conexao_ruim.php" numbered
<?php

$dsn = 'mysql:host=127.0.0.1;dbname=casa_amarela;charset=utf8mb4';

$pdo = new PDO($dsn, 'root', 'senha_errada');
```

```text
PHP Fatal error: Uncaught PDOException: SQLSTATE[HY000] [1045]
Access denied for user 'root'@'localhost' (using password: YES)
in /app/conexao_ruim.php:5
Stack trace:
#0 /app/conexao_ruim.php(5): PDO->__construct('mysql:host=127....',
'root', 'senha_errada')
```

Leia a última linha do rastro. **A senha está ali.**

O PDO recebe a senha como argumento do construtor, e o rastro de pilha do
PHP mostra os argumentos das funções. Se essa mensagem for parar numa tela
com os erros ligados, a senha do banco foi publicada.

:::warning
Duas regras, e a segunda é a que salva.

**Primeira:** `display_errors` desligado em produção, como o capítulo
@cap:primeiro-programa estabeleceu. Isso impede a mensagem de chegar ao
navegador.

**Segunda:** envolva a conexão e troque a exceção por uma sua:

```php
try {
    $pdo = new PDO($dsn, $usuario, $senha, $opcoes);
} catch (PDOException $e) {
    throw new RuntimeException(
        'Falha ao conectar ao banco de dados',
        0
    );
}
```

A nova exceção não carrega os argumentos do construtor. O motivo real
continua disponível no log do PHP, que é onde a equipe procura, e some do
rastro que qualquer outra parte do sistema possa exibir.

E o motivo de a segunda regra existir mesmo com a primeira: `display_errors`
é uma configuração de servidor, e configuração de servidor muda quando
alguém migra de hospedagem numa sexta-feira.
:::

## O acervo, lido pelo PHP

Juntando tudo, a busca da Casa Amarela:

```php title="buscar.php" numbered
<?php

require 'conexao.php';

function buscarLivros(
    PDO $pdo,
    string $termo,
    int $limite = 20,
): array {
    $sql = 'SELECT l.id, l.titulo, l.autor,
                   COUNT(e.id) AS exemplares
            FROM livros l
            LEFT JOIN exemplares e ON e.livro_id = l.id
            WHERE l.titulo LIKE :termo OR l.autor LIKE :termo
            GROUP BY l.id, l.titulo, l.autor
            ORDER BY l.titulo
            LIMIT :limite';

    $consulta = $pdo->prepare($sql);
    $consulta->bindValue('termo', '%' . $termo . '%');
    $consulta->bindValue('limite', $limite, PDO::PARAM_INT);
    $consulta->execute();

    return $consulta->fetchAll();
}

foreach (buscarLivros($pdo, 'assis') as $livro) {
    printf("%-35s %s (%d)\n",
        $livro['titulo'], $livro['autor'], $livro['exemplares']);
}
```

```text
Memórias Póstumas de Brás Cubas     Machado de Assis (0)
```

Três coisas novas nessa versão.

O mesmo marcador `:termo` aparece **duas vezes** na consulta e é informado
uma vez só. Isso funciona apenas com marcadores nomeados; com `?`, seriam
dois marcadores e dois valores.

`bindValue()` informa um valor por vez, em vez de passar o array inteiro
para `execute()`. Ele existe aqui por causa da terceira novidade.

`PDO::PARAM_INT` no `limite` é obrigatório e é uma das armadilhas mais
irritantes do PDO. Com `EMULATE_PREPARES => false`, todo valor é enviado
como texto por padrão — e `LIMIT '20'`, com aspas, é erro de sintaxe no
MySQL. O `PARAM_INT` diz ao driver para enviar como número.

:::pitfall
O sintoma dessa armadilha é enganoso: a consulta funciona perfeitamente
enquanto você testa com `execute([...])` e `EMULATE_PREPARES` ligado, e
quebra quando alguém desliga a emulação por segurança.

A mensagem é `You have an error in your SQL syntax near ''20''` — com duas
aspas, que é a pista. Sempre que um erro de sintaxe apontar para um valor
entre aspas duplas, o problema é um número sendo enviado como texto.
:::

:::note Na sua carreira
Quando você encontrar uma injeção de SQL num sistema, o mais difícil não é
o conserto: é a conversa.

Três coisas que funcionam, aprendidas na prática. **Registre por escrito,
com data e horário.** **Descreva o impacto em linguagem de negócio** — "dá
para ler o cadastro completo de mil e duzentos moradores" comunica; "há uma
concatenação de string no `WHERE`" não. E **traga o conserto junto com o
problema**, porque uma falha relatada sem solução vira uma tarefa para
outra pessoa e entra na fila.

E uma que não funciona: demonstrar em produção. A Tainá perguntou antes, e
essa é a parte da história que vale copiar. Depois da demonstração, a
conversa deixa de ser sobre a falha e passa a ser sobre o seu acesso.
:::

:::summary
- `PDO` conecta com um DSN; o `charset=utf8mb4` não é opcional.
- Ligue `ERRMODE_EXCEPTION`, `FETCH_ASSOC` e `EMULATE_PREPARES => false`.
- Concatenar valor externo no SQL permite que ele vire comando.
- Consulta preparada não escapa o valor: separa o valor do comando.
- Nome de tabela e de coluna não aceitam marcador — só lista de permitidos.
- `fetch` traz uma linha, `fetchAll` traz todas, `fetchColumn` traz um
	valor; `rowCount` diz quantas foram alteradas.
- `lastInsertId` devolve o identificador gerado, como texto.
- `beginTransaction` + `try`/`catch` + `rollBack` fazem duas gravações
	virarem uma.
- O rastro de uma falha de conexão contém a senha: troque a exceção.
:::

:::milestone
Fim da Parte 2. O acervo da Casa Amarela mora num banco de dados, com regras
que o banco garante, e o PHP lê e grava sem abrir buraco. A partir daqui o
projeto tem dados de verdade — e um arquivo só deixa de dar conta.
:::

:::checkpoint
Você conecta ao MySQL pelo PHP, escreve consultas preparadas com marcadores
posicionais e nomeados, sabe reconhecer e consertar uma concatenação
perigosa, e trata a falha de conexão sem vazar credencial.
:::

:::exercise level=1
Escreva um programa que receba um assunto pela linha de comando e liste os
livros daquele assunto, com título e ano, ordenados por ano. Use consulta
preparada.

:::answer
```php
<?php

require 'conexao.php';

$assunto = $argv[1] ?? 'literatura';

$sql = 'SELECT titulo, ano FROM livros
        WHERE assunto = ?
        ORDER BY ano';

$consulta = $pdo->prepare($sql);
$consulta->execute([$assunto]);

foreach ($consulta as $livro) {
    echo $livro['ano'] ?? '????', ' ', $livro['titulo'], "\n";
}
```

```text
$ php por_assunto.php literatura
1881 Memórias Póstumas de Brás Cubas
1890 O Cortiço
1938 Vidas Secas
1956 Grande Sertão
```

O `?? '????'` cobre a coluna `ano`, que aceita nulo. Sem ele, um livro sem
ano imprimiria nada e a linha ficaria torta — e o PHP ainda emitiria um
aviso ao concatenar nulo.
:::

:::exercise level=2
O trecho abaixo tem duas falhas: uma de segurança e uma de comportamento.
Encontre as duas e reescreva.

```php
$id = $_GET['id'];

$sql = "SELECT * FROM leitores WHERE id = $id";
$leitor = $pdo->query($sql)->fetch();

echo "Bem-vindo, " . $leitor['nome'];
```

:::answer
**Falha de segurança:** `$id` vem da URL e é grudado no comando. Com
`?id=1 OR 1=1`, a consulta devolve o primeiro leitor da tabela, seja ele
quem for. Com `?id=1 UNION SELECT ...`, devolve o que o atacante quiser.

**Falha de comportamento:** `fetch()` devolve `false` quando não encontra
ninguém, e a linha seguinte lê `$leitor['nome']` de um `false`. O resultado
é um aviso e a frase "Bem-vindo, " sem nome — e, com os erros desligados em
produção, só a frase truncada.

```php
<?php

require 'conexao.php';

$id = (int) ($_GET['id'] ?? 0);

$consulta = $pdo->prepare(
    'SELECT id, nome FROM leitores WHERE id = ?'
);
$consulta->execute([$id]);

$leitor = $consulta->fetch();

if ($leitor === false) {
    http_response_code(404);
    echo "Leitor não encontrado";
    return;
}

echo "Bem-vindo, ", htmlspecialchars($leitor['nome']);
```

Quatro mudanças, e duas delas não estavam no enunciado.

O `(int)` na borda converte o valor antes de qualquer uso. Ele sozinho já
fecharia a injeção neste caso — e
não é suficiente como estratégia, porque o próximo campo vai ser um texto.

O `SELECT *` virou `SELECT id, nome`: não há motivo para trazer documento e
data de cadastro para escrever uma saudação.

E o `htmlspecialchars` na saída escapa o nome antes de colocá-lo numa
página. Sem ele, um leitor cadastrado com `<script>` no nome executa código
no navegador de quem abrir a tela. É a mesma ideia da consulta preparada,
na outra fronteira: **dado não vira comando**.
:::

:::exercise level=3
Implemente a função `emprestar(PDO $pdo, int $exemplarId, int $leitorId):
int`, que registra um empréstimo e devolve o identificador criado. Ela
precisa recusar o empréstimo se o exemplar já estiver emprestado, e não pode
deixar estado inconsistente se algo falhar no meio.

Depois explique por que conferir a disponibilidade com um `SELECT` antes do
`INSERT` não é suficiente.

:::answer
```php
<?php

function emprestar(PDO $pdo, int $exemplarId, int $leitorId): int
{
    $devolverAte = date('Y-m-d', strtotime('+14 days'));

    $pdo->beginTransaction();

    try {
        $c = $pdo->prepare(
            'SELECT id FROM exemplares
             WHERE id = ? AND estado = ?
             FOR UPDATE'
        );
        $c->execute([$exemplarId, 'bom']);

        if ($c->fetch() === false) {
            $pdo->rollBack();
            throw new RuntimeException('Exemplar indisponivel');
        }

        $c = $pdo->prepare(
            'INSERT INTO emprestimos
               (exemplar_id, leitor_id, retirado_em, devolver_ate)
             VALUES (?, ?, NOW(), ?)'
        );
        $c->execute([$exemplarId, $leitorId, $devolverAte]);

        $id = (int) $pdo->lastInsertId();

        $c = $pdo->prepare(
            'UPDATE exemplares SET estado = ? WHERE id = ?'
        );
        $c->execute(['emprestado', $exemplarId]);

        $pdo->commit();

        return $id;
    } catch (PDOException $e) {
        $pdo->rollBack();
        throw $e;
    }
}
```

**Por que o `SELECT` sozinho não basta** é a pergunta que vale o exercício,
e a resposta é a corrida do capítulo @cap:do-arquivo-ao-banco, agora dentro
do banco.

Entre o `SELECT` que confere e o `INSERT` que grava existe um intervalo. Se
a Vera e a Neide emprestarem o mesmo exemplar nesse intervalo, os dois
`SELECT` respondem "disponível", os dois `INSERT` gravam, e o exemplar sai
duas vezes. O intervalo dura microssegundos e acontece — foi exatamente o
que a Vera descreveu no primeiro dia: *"quando duas pessoas emprestam ao
mesmo tempo, some um"*.

O `FOR UPDATE` no fim do `SELECT` é o que fecha isso. Ele diz ao banco:
*trave esta linha até o fim da minha transação*. A segunda requisição fica
esperando no `SELECT`, e quando chega a vez dela o estado já é
`emprestado` — então ela recusa, corretamente.

Duas observações honestas sobre esta versão.

O prazo de catorze dias está calculado em PHP, na primeira linha, e chega
ao banco como valor. A alternativa seria `DATE_ADD(CURDATE(), INTERVAL 14
DAY)` dentro do SQL — que funciona e enterra uma regra de negócio num lugar
difícil de conferir. O prazo é decisão da Casa Amarela, não do banco, e ele
muda em janeiro — e regra que muda precisa morar onde alguém consiga
conferi-la.

E `throw` dentro do `try` com `rollBack` antes dele é redundante com o
`catch` de baixo apenas se a exceção for `PDOException`. Como
`RuntimeException` não é, o `rollBack` explícito antes dele é necessário. É
o tipo de detalhe que some quando o tratamento de erro do projeto for
uniforme.
:::
