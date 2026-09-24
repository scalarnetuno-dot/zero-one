---
title: "Exceções"
number: 21
slug: excecoes
part: p4
kicker: "A importação noturna nunca dava erro. Perdia duzentas e catorze linhas por noite, em silêncio, havia três meses."
goal: >-
  Entender a diferença entre `Error` e `Exception`, capturar pelo tipo em
  vez de pelo mundo, criar o vocabulário de erro do domínio com dados
  anexados e preservar a causa original de uma falha.
---

:::story Nunca deu erro
O Sistema importava, toda madrugada, o arquivo que a editora parceira
mandava com as novidades do mês. Cinco anos rodando, nenhum chamado aberto.

Tainá foi conferir um livro que a Vera jurava ter cadastrado e não
encontrou. Foi conferir o arquivo da editora: estava lá.

Ela contou as linhas do arquivo de outubro. Depois contou as linhas que
tinham entrado no banco.

— Faltam duzentas e catorze.

Dedé abriu o `importa_editora.php` e procurou o laço. Estava tudo bem
escrito, indentado, com nome de variável em português.

```php
    } catch (Exception $e) {
        continue;
    }
```

— Quanto tempo isso tem?

Tainá procurou no histórico do arquivo. A linha tinha sido acrescentada numa
sexta-feira de 2019, num *commit* chamado *"corrige erro da importação"*.

— Três anos.

— E o erro?

— Corrigido.
:::

## `Error`, `Exception` e o `Throwable` que cobre os dois

O PHP tem duas famílias de problema, e elas contam coisas diferentes.

:::tree title="A hierarquia, simplificada"
Throwable            # a interface que o catch entende
  Error              # defeito no programa
    TypeError
    ArgumentCountError
    DivisionByZeroError
  Exception          # condição do mundo
    LogicException   # a sua API foi usada errado
      InvalidArgumentException
      DomainException
    RuntimeException # só dá para saber rodando
      PDOException
      UnexpectedValueException
:::

`Error` é o que acontece quando o **programa** está errado: você chamou um
método em `null`, passou texto onde ia inteiro, dividiu por zero. Não é uma
condição do mundo, é um defeito, e defeito não se trata — se conserta.

`Exception` é o que acontece quando o **mundo** não colabora: o banco caiu,
o arquivo não veio, o exemplar já está emprestado. O programa está certo, a
situação é que é adversa.

Essa separação tem uma consequência prática que pega quase todo mundo uma
vez:

```php title="protegido.php" numbered
<?php

try {
    $exemplar = null;
    $exemplar->emprestar();
} catch (Exception $e) {
    echo "tratei\n";
}
```

```text
Fatal error: Uncaught Error:
Call to a member function emprestar() on null
```

O `catch` não pegou nada. `Error` não é `Exception` — as duas só se
encontram lá em cima, no `Throwable`.

:::key
`catch (Exception $e)` trata problemas do mundo e deixa os defeitos
passarem. Isso é o comportamento certo na maior parte do código: você quer
saber quando chamou um método em `null`, não quer engolir.
:::

## O `catch` que apaga a testemunha

O bloco do `importa_editora.php` tem quatro linhas e três defeitos.

```php
    } catch (Exception $e) {
        continue;
    }
```

**O primeiro é o silêncio.** A variável `$e` foi capturada e descartada.
Quem escreveu tinha, na mão, o arquivo, a linha, a mensagem do banco e a
pilha inteira de chamadas — e jogou fora.

**O segundo é a abrangência.** Ele trata qualquer `Exception`: o ISBN
duplicado, que é esperado, e a conexão de banco caída, que não é. Uma noite
em que o MySQL não sobe produz um arquivo importado com zero linhas e
nenhuma reclamação.

**O terceiro é o resultado.** No fim, o programa termina com sucesso. O
código de saída é zero, o agendador marca verde, e ninguém tem motivo para
olhar.

A versão que conta a verdade não é mais complicada:

```php title="importar.php" numbered
<?php

$gravadas = 0;
$rejeitadas = [];

foreach ($linhas as $numero => $linha) {
    try {
        gravar($pdo, $linha);
        $gravadas++;
    } catch (LinhaInvalida $e) {
        $rejeitadas[] = "linha {$numero}: {$e->getMessage()}";
    }
}

echo "gravadas: {$gravadas}\n";
echo 'rejeitadas: ' . count($rejeitadas) . "\n";

foreach ($rejeitadas as $motivo) {
    echo "  {$motivo}\n";
}

exit($rejeitadas === [] ? 0 : 1);
```

```text
gravadas: 1786
rejeitadas: 214
  linha 12: ISBN 9788525406958 já existe
  linha 19: ano ausente
  ...
```

Duas mudanças fizeram o trabalho. O `catch` passou a nomear **um tipo
específico** — só a linha inválida é tolerada; qualquer outra coisa sobe e
derruba o programa, que é o que se quer quando o banco caiu. E o resumo saiu
do silêncio: alguém, em algum momento, lê "214 rejeitadas" e abre um
chamado.

:::pitfall
`catch (\Throwable $e) { return false; }` é a forma mais completa desse
defeito, porque engole até os `Error`. Um `TypeError` numa linha sua vira
"deu falso", e o programa segue como se fosse uma condição normal de
negócio.

Quando encontrar um desses numa revisão, a pergunta não é "por que está
capturando?". É: **o que você faria se soubesse qual foi o erro?** Se a
resposta for "abriria um chamado", o `catch` está no lugar errado.
:::

## O vocabulário de erro do domínio

`RuntimeException('Exemplar indisponivel')` funciona, e tem um problema:
quem captura não consegue fazer nada com isso além de mostrar o texto.

Para reagir, o código de cima precisaria ler a frase — e frase muda, ganha
acento, vira plural, é traduzida.

Uma exceção é uma classe. Ela pode carregar dados:

```php title="src/Circulacao/ExemplarIndisponivel.php" numbered
<?php

namespace CasaAmarela\Circulacao;

class ExemplarIndisponivel extends \RuntimeException
{
    public function __construct(
        public readonly int $tombo,
        public readonly string $estado,
    ) {
        parent::__construct(
            "Exemplar {$tombo} indisponível: {$estado}"
        );
    }
}
```

`parent::__construct(...)` chama o construtor da classe de cima — aqui, o do
`RuntimeException`, que é quem guarda a mensagem. As duas propriedades
promovidas são acréscimo seu.

A Casa Amarela precisa de três:

| Exceção | Carrega | Quem reage |
|---|---|---|
| `ExemplarIndisponivel` | tombo, estado | a tela oferece a reserva |
| `LimiteDeEmprestimosAtingido` | limite, abertos | a tela lista o que devolver |
| `LeitorComPendencia` | leitorId, multaEmCentavos | a tela mostra o valor |

Tabela: Três situações previsíveis, três tipos, e em nenhuma delas quem
captura precisa ler a mensagem para decidir o que fazer.

E o uso fica direto:

```php title="emprestar.php" numbered
try {
    emprestar($pdo, $tombo, $leitorId);
} catch (LeitorComPendencia $e) {
    $valor = number_format($e->multaEmCentavos / 100, 2, ',', '.');
    echo "Regularize R$ {$valor} antes de levar outro livro.\n";
} catch (ExemplarIndisponivel $e) {
    echo "O {$e->tombo} está {$e->estado}. Quer reservar?\n";
}
```

:::key
A ordem dos `catch` importa: o PHP usa o **primeiro que serve**. Tipo mais
específico primeiro, mais genérico depois.

Um `catch (\RuntimeException $e)` escrito antes dos três nunca deixaria
nenhum deles ser alcançado — e o PHP não avisa, porque não há nada de
ilegal nisso.
:::

## `previous`: não perder a causa no caminho

Uma falha costuma atravessar camadas. O banco recusa, o repositório traduz,
a tela mostra — e a cada tradução existe o risco de a informação original
sumir.

O terceiro argumento do construtor de qualquer exceção é a **causa**:

```php title="emprestar.php" numbered
try {
    $c->execute([$exemplarId, $leitorId]);
} catch (\PDOException $e) {
    throw new \RuntimeException(
        'Falha ao registrar o empréstimo',
        0,
        $e,
    );
}
```

Se ninguém tratar, o PHP imprime as duas, na ordem em que aconteceram:

```text
Fatal error: Uncaught PDOException: SQLSTATE[HY000]: conexao recusada
in /app/emprestar.php:8
Stack trace:
#0 /app/emprestar.php(14): emprestar()
#1 {main}

Next RuntimeException: Falha ao registrar o empréstimo
in /app/emprestar.php:10
Stack trace:
#0 /app/emprestar.php(14): emprestar()
#1 {main}
```

A primeira é a causa; o `Next` é a tradução. Sem o terceiro argumento, o
log teria só a segunda — e "falha ao registrar o empréstimo" não diz se o
banco caiu, se a tabela sumiu ou se a senha mudou.

`getPrevious()` recupera a causa em código, e ele devolve `null` quando não
houve.

## `finally`: o que precisa ser devolvido

Existe um bloco que roda **sempre**: quando o `try` termina bem, quando uma
exceção sobe e até quando há um `return` no meio.

```php title="emprestar.php" numbered
function emprestar(PDO $pdo, int $exemplarId, int $leitorId): int
{
    $pdo->beginTransaction();

    try {
        // ... o SELECT FOR UPDATE, o INSERT e o UPDATE

        $pdo->commit();

        return $id;
    } catch (\PDOException $e) {
        $pdo->rollBack();

        throw new \RuntimeException('Falha no empréstimo', 0, $e);
    } finally {
        $pdo->exec('SET SESSION wait_timeout = DEFAULT');
    }
}
```

`finally` é o lugar de devolver o que foi pego emprestado: um arquivo
aberto, uma trava, uma configuração de sessão alterada. Não é o lugar de
tratar o erro — é o lugar de limpar a mesa, aconteça o que acontecer.

:::pitfall
Um `return` dentro do `finally` **substitui** o que o `try` ia devolver, e
descarta até uma exceção que estava subindo.

```php
function quanto(): int
{
    try {
        throw new \RuntimeException('quebrei');
    } finally {
        return 0;
    }
}
```

Essa função devolve zero e a exceção evapora. É o `catch` vazio outra vez,
disfarçado de arrumação.
:::

## Quando não capturar

Capturar é a exceção, não a regra. Três casos em que o certo é deixar subir.

**Quando você não vai fazer nada além de repassar.** Um `catch` que só
escreve no log e dá `throw` de novo acrescentou ruído e nenhuma informação.

**Quando o problema é um defeito.** `TypeError`, `ArgumentCountError`,
método chamado em `null` — tratar isso é esconder um erro que precisa ser
consertado no código.

**Quando a situação é previsível e frequente.** Exceção é cara e é
barulhenta. "O leitor não existe" numa busca não é uma falha: é uma resposta
possível, e o lugar dela é um `null` ou uma lista vazia.

:::key
A régua: exceção para o que **interrompe** o que estava sendo feito;
retorno normal para o que é **uma das respostas** possíveis.

"Não encontrei o leitor 913" é resposta. "O banco não respondeu" é
interrupção.
:::

## A última rede

Num programa que atende pessoas, uma exceção que chega até o topo não pode
virar um despejo de pilha na tela — ela mostra caminho de arquivo, nome de
tabela e às vezes credencial.

```php title="importar.php" numbered
set_exception_handler(function (\Throwable $e): void {
    error_log((string) $e);

    fwrite(STDERR, "A importação falhou. Procure o suporte.\n");

    exit(1);
});
```

`set_exception_handler` registra o que fazer com o que ninguém tratou. As
três linhas do corpo são o padrão: **registre tudo** onde a equipe procura,
**mostre pouco** para quem está na frente da tela, e **termine com código
diferente de zero**, para que o agendador saiba que deu errado.

:::note Na sua carreira
O `catch (Exception $e) { continue; }` da madrugada não foi preguiça. Alguém
tinha uma importação quebrando às três da manhã, um chamado aberto e uma
sexta-feira. A linha resolveu o chamado.

É o formato mais comum de dívida técnica: a correção que funciona contra o
sintoma exato que foi relatado. Ela passa na revisão porque o relato era "a
importação está quebrando" e a importação parou de quebrar.

O que teria pego isso em trinta segundos é uma pergunta de revisão que
custa pouco e você pode fazer sempre: **como a gente vai saber se isso
acontecer de novo?** Se a resposta for "não vai dar erro", a correção
apagou o aviso, não a causa.
:::

:::tree title="Onde estamos agora"
acervo/
  src/
    Circulacao/
      Emprestavel.php
      RegistraHistorico.php
      ExemplarIndisponivel.php         # com tombo e estado
      LimiteDeEmprestimosAtingido.php  # com limite e abertos
      LeitorComPendencia.php           # com leitorId e multa
    Acervo/
      Livro.php
      Classificacao.php
      Exemplar.php
    Leitores/
      Leitor.php
    Emprestimos/
      Multa.php
  importar.php
  emprestar.php
:::

:::summary
- `Error` é defeito do programa; `Exception` é condição do mundo; as duas
  são `Throwable`.
- `catch (Exception)` não pega `Error`, e isso é a favor.
- `catch` vazio apaga a única testemunha da falha e faz o programa terminar
  com sucesso.
- Capture o tipo específico; deixe o resto subir.
- Exceção é classe: anexe os dados de que quem captura precisa, em vez de
  obrigar a ler a mensagem.
- A ordem dos `catch` é do mais específico para o mais genérico.
- O terceiro argumento do construtor guarda a causa, e ela aparece no log
  como `Next`.
- `finally` devolve recursos e nunca deve conter `return`.
- Exceção para o que interrompe; retorno normal para o que é uma das
  respostas possíveis.
:::

:::checkpoint
Você distingue `Error` de `Exception`, reconhece num código de revisão o
`catch` que apaga informação, escreve uma família de exceções de domínio com
dados anexados, encadeia a causa original e sabe apontar três situações em
que o certo é não capturar.
:::

:::exercise level=1
Diga, para cada situação, se ela merece uma exceção ou um retorno normal —
e, quando for exceção, qual das duas famílias.

1. O leitor digitou um documento que não existe no cadastro.
2. O arquivo de configuração não foi encontrado na inicialização.
3. `emprestar()` recebeu um tombo negativo.
4. A consulta de livros por assunto não encontrou nenhum.
5. O MySQL recusou a conexão.

:::answer
1. **Retorno normal** — `null`. Não achar é uma das respostas possíveis de
   uma busca.
2. **Exceção**, família `Exception` (`RuntimeException`). O programa está
   certo, o mundo é que não tem o arquivo — e não há como continuar.
3. **Exceção**, família `Exception` (`InvalidArgumentException`). É uso
   errado da sua função, detectável na fronteira. Note que se o tipo fosse
   violado — texto onde vai `int` — aí seria `TypeError`, família `Error`,
   e não é você que lança.
4. **Retorno normal** — lista vazia. Zero resultados é um resultado, e
   `count()` de um array vazio é zero, o que já resolve a tela.
5. **Exceção**, família `Exception` (`PDOException`, que já vem pronta).

O padrão que aparece nos cinco: busca que não acha devolve vazio; coisa que
impede o trabalho de continuar lança.
:::

:::exercise level=2
Escreva `LimiteDeEmprestimosAtingido` com os dados anexados e ajuste a
função de empréstimo para lançá-la.

A regra da Vera: três livros por leitor, cinco em janeiro.

Depois escreva o `catch` que produz a mensagem final para o balcão, usando
os dados da exceção e não a mensagem dela.

:::answer
```php title="src/Circulacao/LimiteDeEmprestimosAtingido.php" numbered
<?php

namespace CasaAmarela\Circulacao;

class LimiteDeEmprestimosAtingido extends \RuntimeException
{
    public function __construct(
        public readonly int $leitorId,
        public readonly int $limite,
        public readonly int $abertos,
    ) {
        parent::__construct(
            "Leitor {$leitorId} tem {$abertos} de {$limite}"
        );
    }
}
```

```php title="emprestar.php" numbered
$limite = (int) date('n') === 1 ? 5 : 3;

$abertos = (int) $pdo->query(
    'SELECT COUNT(*) FROM emprestimos
     WHERE leitor_id = ' . $leitorId . ' AND devolvido_em IS NULL'
)->fetchColumn();

if ($abertos >= $limite) {
    throw new LimiteDeEmprestimosAtingido(
        $leitorId,
        $limite,
        $abertos,
    );
}
```

```php
} catch (LimiteDeEmprestimosAtingido $e) {
    echo "Limite de {$e->limite} livros atingido. ";
    echo "Devolva 1 dos {$e->abertos} para levar outro.\n";
}
```

Uma observação sobre a consulta: ela está concatenando `$leitorId`. Como o
valor veio de um `(int)`, é seguro — mas seguro por acidente, e acidente não
é política. A consulta preparada é o jeito de a segurança não depender de
alguém lembrar do `(int)` na próxima alteração.

E repare no que a mensagem do balcão **não** usa: `$e->getMessage()`. A
frase "Leitor 913 tem 3 de 3" serve para o log. Para a pessoa na fila, a
tela monta a frase dela, com os mesmos números.
:::

:::exercise level=3
Este código roda toda madrugada e nunca reclamou. Encontre os quatro
problemas e reescreva.

```php title="sincroniza.php" numbered
<?php

$arquivo = fopen('/tmp/editora.csv', 'r');

try {
    while (($linha = fgetcsv($arquivo)) !== false) {
        try {
            gravar($pdo, $linha);
        } catch (Throwable $e) {
            file_put_contents(
                '/tmp/erros.log',
                $e->getMessage(),
                FILE_APPEND,
            );
        }
    }
} catch (Exception $e) {
    echo "erro\n";
}

fclose($arquivo);
```

:::answer
**Um: o `catch (Throwable)` de dentro engole defeito.** Se `gravar()` tiver
um `TypeError`, todas as linhas falham do mesmo jeito e o programa termina
bem. O tipo capturado precisa ser o da linha inválida, e só ele.

**Dois: o log guarda só a mensagem.** `$e->getMessage()` descarta o tipo, o
arquivo, a linha e a causa encadeada. `(string) $e` guarda tudo, e
`error_log()` manda para onde a equipe já procura, em vez de um arquivo em
`/tmp` que ninguém abre.

**Três: nada conta.** Não há total de gravadas, total de rejeitadas nem
código de saída. Sem número, a diferença entre uma noite perfeita e uma
noite que perdeu duzentas linhas é invisível.

**Quatro: o `fclose` não acontece sempre.** Se o `while` lançar algo que o
`catch (Exception)` não pegue — um `Error`, por exemplo — o programa morre
com o arquivo aberto. O lugar do `fclose` é um `finally`.

```php title="sincroniza.php" numbered
<?php

$arquivo = fopen('/tmp/editora.csv', 'r');

if ($arquivo === false) {
    throw new RuntimeException('CSV da editora não chegou');
}

$gravadas = 0;
$rejeitadas = [];

try {
    while (($linha = fgetcsv($arquivo)) !== false) {
        try {
            gravar($pdo, $linha);
            $gravadas++;
        } catch (LinhaInvalida $e) {
            $rejeitadas[] = $e->getMessage();
            error_log((string) $e);
        }
    }
} finally {
    fclose($arquivo);
}

echo "gravadas: {$gravadas}, rejeitadas: ", count($rejeitadas), "\n";

exit($rejeitadas === [] ? 0 : 1);
```

O `catch (Exception)` de fora sumiu inteiro, e é a melhor parte da
mudança: não havia nada de útil a fazer ali. Qualquer falha que não seja
linha inválida agora derruba o programa com a mensagem completa — que é
exatamente o que se quer às três da manhã.
:::
