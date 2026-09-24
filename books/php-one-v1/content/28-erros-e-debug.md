---
title: "Erros e debug"
number: 28
slug: erros-e-debug
part: p5
kicker: "A importação da madrugada não importou nada e terminou com sucesso. O PHP tinha avisado três vezes, para ninguém."
goal: >-
  Distinguir os níveis de erro do PHP, fazer o aviso que o programa ignora
  virar uma exceção que ele não pode ignorar, montar a configuração de erro
  de um script num lugar só, ler uma pilha de chamadas de baixo para cima,
  e registrar erro com contexto suficiente para alguém consertar.
---

:::story Zero livros, código zero
A primeira importação noturna das doações do Seu Juvenal rodou às 2h. De
manhã, a tabela de livros tinha os mesmos quatro mil títulos da véspera.

— Deu erro? — perguntou a Márcia.

— Não — disse a Tainá. — Terminou com sucesso. Código de saída zero.

— Então importou.

— Importou zero.

O Dedé abriu a configuração do agendador do servidor.

```text
0 2 * * * php /srv/acervo/scripts/importar-doacoes.php \
    > /dev/null 2>&1
```

— Esse `> /dev/null 2>&1` no fim — disse ele — manda tudo que o script
imprime para lugar nenhum. As mensagens normais e as de erro.

— E tinha erro?

— Vamos ver.

Rodou o script na mão, da raiz, do jeito que o agendador rodava:

```text
Warning: fopen(doacoes.csv): Failed to open stream: No such
file or directory in /srv/acervo/scripts/importar-doacoes.php
on line 7
```

— O PHP avisou — disse o Dedé. — Todas as noites. Para o `/dev/null`.
:::

:::art caption="O PHP avisou todas as noites. O aviso ia para lugar nenhum."
src="o-php-avisou-todas-as-noites-o-aviso-ia-para-lugar-nenhum.png"
Charge editorial minimalista em fundo branco, composição dividida entre
noite e manhã. À esquerda, de noite, um servidor pequeno sobre uma mesa,
com um relógio marcando 2h; dele sai um balão de fala com a palavra
"Warning", que escorrega direto para um buraco redondo no chão com uma
plaquinha "/dev/null". Dentro do buraco, uma pilha de balões iguais, um por
noite. À direita, de manhã, uma estagiária olha para uma tela onde se lê
apenas "código de saída: 0" com um visto verde, e ao lado dela uma gerente
de planilha na mão sorri satisfeita. Poucos elementos, humor seco, estética
de revista de tecnologia.
:::

## Os níveis de erro

Nem tudo que o PHP chama de erro para o programa. O mesmo arquivo pode
mostrar três problemas e chegar à última linha:

```php title="niveis.php" numbered
<?php

declare(strict_types=1);

$livro = ['titulo' => 'Vidas Secas'];

echo $livro['autor'], "\n";
echo $total, "\n";
$arquivo = fopen('/nao/existe.csv', 'r');
var_dump($arquivo);
echo "chegou ao fim\n";
```

```text
$ php niveis.php

Warning: Undefined array key "autor" in niveis.php on line 7

Warning: Undefined variable $total in niveis.php on line 8

Warning: fopen(/nao/existe.csv): Failed to open stream: No
such file or directory in niveis.php on line 9
bool(false)
chegou ao fim
```

Três avisos, e o programa segue com `null` onde esperava um autor, `null`
onde esperava um total e `false` onde esperava um arquivo. É o comportamento
que o PHP herdou da época em que uma página meio montada era melhor que
nenhuma.

| Nível | O que significa | O programa |
|---|---|---|
| `Deprecated` | isto vai deixar de funcionar numa versão futura | segue |
| `Warning` | algo deu errado, e o PHP improvisou um valor | segue |
| `Fatal error` | não há como continuar | para |
| exceção não capturada | o capítulo @cap:excecoes | para |

Tabela: Os níveis que você vai encontrar. Havia um quarto, `Notice`, que o
PHP 8 promoveu quase todo a `Warning`.

O `Deprecated` aparece ao usar um recurso com data de saída:

```text
$ php -r 'echo strlen(null);'

Deprecated: strlen(): Passing null to parameter #1 ($string)
of type string is deprecated in Command line code on line 1
0
```

Hoje funciona. Numa versão futura do PHP, é um `TypeError`. Um
`Deprecated` no log é uma tarefa com prazo, e o prazo é a próxima
atualização de versão — o que, na vida de um projeto, costuma ser mais cedo
do que parece.

:::key
**Warning não é "está tudo bem, só um aviso".** É o PHP dizendo que não
conseguiu fazer o que você pediu e pôs outro valor no lugar. Um programa
que deixa passar um warning continua rodando com um valor que ninguém
escolheu.
:::

## O aviso vira exceção

O capítulo @cap:excecoes ensinou a tratar exceção: ela para o programa se
ninguém a capturar, e carrega a pilha de chamadas. O warning não tem
nenhuma das duas qualidades. A solução é converter um no outro.

```php title="bootstrap.php" numbered
<?php

declare(strict_types=1);

error_reporting(E_ALL);
ini_set('display_errors', '0');
ini_set('log_errors', '1');
ini_set('error_log', __DIR__ . '/var/log/php.log');

set_error_handler(
    function (int $nivel, string $msg, string $arq, int $ln): bool {
        if ($nivel === E_DEPRECATED || $nivel === E_USER_DEPRECATED) {
            error_log("deprecated: {$msg} em {$arq}:{$ln}");
            return true;
        }
        throw new ErrorException($msg, 0, $nivel, $arq, $ln);
    },
);

set_exception_handler(function (Throwable $e): void {
    error_log((string) $e);
    fwrite(STDERR, "falhou: {$e->getMessage()}\n");
    exit(1);
});
```

Um arquivo, quatro decisões, e todo script da pasta `scripts/` começa por
ele:

```php
require __DIR__ . '/../bootstrap.php';
```

**`error_reporting(E_ALL)`** liga todos os níveis. Um nível desligado
não é um problema a menos: é um problema que você não vê.

**As três linhas de `ini_set`** são as do capítulo @cap:primeiro-programa,
agora no código: não mostrar erro na tela, e gravar tudo num arquivo que a
equipe sabe onde fica. Escritas aqui, elas valem mesmo num servidor cujo
`php.ini` ninguém conferiu.

**`set_error_handler`** registra uma função que o PHP chama no lugar de
imprimir o warning. Esta faz duas coisas: `Deprecated` vai para o log e o
programa segue — ele não está errado **hoje**, e uma biblioteca de terceiros
com um recurso antigo não pode derrubar a importação. Todo o resto vira
`ErrorException`, uma exceção que o PHP já traz pronta para isso, com o
nível, o arquivo e a linha do aviso original.

**`set_exception_handler`** é a última rede do capítulo @cap:excecoes:
registrar tudo, mostrar pouco, sair com código diferente de zero.

O mesmo script da história, agora com o `bootstrap.php`:

```text
$ php /srv/acervo/scripts/importar-doacoes.php > /dev/null
falhou: fopen(doacoes.csv): Failed to open stream: No such
file or directory
$ echo $?
1
```

A mensagem vai para a saída de erro, que o `> /dev/null` sozinho não
esconde, e o código de saída 1 diz ao agendador que a noite deu errado. No
log, a história inteira:

```text
[26-Sep-2025 02:00:03 UTC] ErrorException: fopen(doacoes.csv):
Failed to open stream: No such file or directory in
/srv/acervo/scripts/importar-doacoes.php:7
Stack trace:
#0 [internal function]: {closure}(2, 'fopen(doacoes.c...', ...)
#1 /srv/acervo/scripts/importar-doacoes.php(7):
   fopen('doacoes.csv', 'r')
#2 {main}
```

:::pitfall
O operador `@` na frente de uma chamada — `@fopen(...)` — silencia o
aviso daquela linha. Ele aparece muito em código antigo, sempre pelo mesmo
motivo: o aviso incomodava. É o `catch` vazio do capítulo @cap:excecoes
com um caractere só.

Se uma chamada pode falhar de um jeito esperado, confira o retorno dela,
como o `if ($arquivo === false)` do capítulo @cap:manipulacao-de-arquivos.
Se não pode, deixe o aviso virar exceção.
:::

## A pilha, lida de baixo para cima

Com os avisos virando exceções, as falhas passam a vir com uma **pilha de
chamadas** — o caminho que o programa fez até o erro. Na importação, uma
linha da planilha tinha o ano escrito por extenso:

```text
Fatal error: Uncaught InvalidArgumentException: ano inválido:
mil oitocentos in /srv/acervo/src/Importador.php:26
Stack trace:
#0 /srv/acervo/src/Importador.php(18):
   Importador->ano('mil oitocentos')
#1 /srv/acervo/src/Importador.php(11): Importador->gravar(Array)
#2 /srv/acervo/importar.php(12): Importador->importar(Array)
#3 {main}
  thrown in /srv/acervo/src/Importador.php on line 26
```

A primeira linha diz **o quê**: a exceção, a mensagem, e o arquivo e a
linha em que ela foi lançada. A pilha diz **por onde**, e se lê melhor de
baixo para cima, que é a ordem em que as coisas aconteceram:

1. `{main}` — o programa começou;
2. `importar.php`, linha 12, chamou `importar`;
3. `importar`, na linha 11 do `Importador`, chamou `gravar`;
4. `gravar`, na linha 18, chamou `ano` com `'mil oitocentos'`;
5. `ano` lançou a exceção, na linha 26.

O argumento entre parênteses, `'mil oitocentos'`, é muitas vezes a
resposta inteira. Quando não é, a pergunta seguinte é: **qual é a primeira
linha, de baixo para cima, que é código meu e que eu não esperava ver
ali?** Em projeto com framework, a pilha tem sessenta linhas, e cinquenta e
cinco são do framework. As cinco suas são as que importam.

:::key
A mensagem diz o quê; a pilha diz por onde; os argumentos dizem com o quê.
Leia as três antes de abrir o código. Metade das vezes o conserto aparece
antes.
:::

## Investigar: `var_dump`, e um passo além

Quando a pilha não basta, o recurso mais usado continua sendo o do
capítulo @cap:variaveis-e-tipos: parar o programa e olhar.

```php
var_dump($linha);
exit;
```

É rápido e funciona em qualquer servidor. O custo é que você precisa saber
onde pôr, e remover depois — um `var_dump` esquecido no código que sobe
para produção é um clássico com vítimas.

Três hábitos tornam esse jeito mais eficiente:

- **Reduza o caso.** Se a linha 81.407 da planilha quebra, faça um arquivo
  com a linha 81.407 e mais nenhuma. Um erro que se repete em um segundo se
  investiga dez vezes mais rápido que um que leva quatro minutos.
- **Uma hipótese por vez.** "Acho que é o BOM": imprima as chaves. Não era?
  Próxima hipótese. Mudar três coisas de uma vez e ver funcionar não diz
  qual das três consertou.
- **Escreva o que você descobriu.** No caderno, no pedido de revisão. A
  mesma falha volta daqui a oito meses, e quem vai investigar pode ser você.

O passo além é um **depurador**: o Xdebug, uma extensão do PHP que se liga
ao editor e deixa você parar o programa numa linha, ver todas as variáveis
e andar uma linha por vez. A instalação muda com o sistema e o editor, e
fica para quando o `var_dump` deixar de bastar. Quando deixar, vale a
tarde.

## Registrar com contexto

`error_log` grava um texto. Um texto como "falha ao importar" responde
pouco às 9h do dia seguinte: qual livro? qual linha? qual arquivo? O
registro que ajuda tem a mensagem **e** os dados.

```php title="src/Registro.php" numbered
<?php

declare(strict_types=1);

final class Registro
{
    public function __construct(private string $arquivo)
    {
    }

    public function info(string $mensagem, array $contexto = []): void
    {
        $this->gravar('info', $mensagem, $contexto);
    }

    public function erro(string $mensagem, array $contexto = []): void
    {
        $this->gravar('error', $mensagem, $contexto);
    }

    private function gravar(
        string $nivel,
        string $msg,
        array $ctx,
    ): void
    {
        $linha = json_encode([
            'quando' => date(DATE_ATOM),
            'nivel' => $nivel,
            'mensagem' => $msg,
            'contexto' => $ctx,
        ], JSON_UNESCAPED_UNICODE);

        file_put_contents(
            $this->arquivo,
            $linha . "\n",
            FILE_APPEND | LOCK_EX,
        );
    }
}
```

E a importação ganha o que o exercício 3 do capítulo
@cap:manipulacao-de-arquivos pedia — contar:

```php
$registro->erro('linha descartada', [
    'linha' => $numero,
    'motivo' => $e->getMessage(),
]);

// ...no fim do laço:
$registro->info('importação terminada', [
    'lidas' => $lidas,
    'importadas' => $importadas,
    'descartadas' => $descartadas,
]);

if ($lidas > 0 && $importadas === 0) {
    exit(1);
}
```

```text
{"quando":"2025-09-27T02:00:41+00:00","nivel":"error",
 "mensagem":"linha descartada","contexto":{"linha":81407,
 "motivo":"ano inválido: mil oitocentos"}}
{"quando":"2025-09-27T02:04:12+00:00","nivel":"info",
 "mensagem":"importação terminada","contexto":{"lidas":200000,
 "importadas":199312,"descartadas":688}}
```

Uma linha de JSON por evento. `FILE_APPEND` acrescenta no fim em vez de
apagar o arquivo, e `LOCK_EX` é o `flock` do capítulo @cap:manipulacao-de-arquivos numa
constante: dois scripts registrando ao mesmo tempo não misturam as linhas.

:::term Registro com contexto
Uma entrada de log com três partes: o **nível** (info, error...), uma
**mensagem fixa**, que se pode procurar, e um **contexto** com os dados
daquela ocorrência. "linha descartada" é igual em todas as 688 entradas; o
número da linha e o motivo mudam.

A comunidade PHP padronizou esse formato na PSR-3, a interface
`LoggerInterface`, com um método por nível e o `array $context` em todos.
:::

## O que o volume 2 faz com erro

O Laravel faz tudo isto antes da primeira linha sua rodar. Ele registra um
tratador que converte os warnings em `ErrorException` — o mesmo
`set_error_handler` deste capítulo —, manda os `Deprecated` para um log
separado, e tem uma última rede que decide o que mostrar: a página
detalhada com a pilha para quem está desenvolvendo, e uma resposta curta,
sem caminho de arquivo, para quem está usando.

O registro com contexto é o `Log::error('mensagem', [...])`, que implementa
a PSR-3. E o `var_dump` seguido de `exit` tem nome próprio no framework,
`dd()` — *dump and die*, "mostre e pare".

:::note Na sua carreira
O `> /dev/null 2>&1` da história não foi descuido de quem o escreveu. O
agendador manda por e-mail tudo que um script imprime, e alguém, um dia,
cansou de receber trezentos e-mails de aviso por mês. Silenciou a saída e
resolveu o problema que tinha.

O conserto de verdade é o deste capítulo: o script fica calado quando dá
certo, e quando dá errado registra com detalhe, sai com código diferente de
zero e alguém fica sabendo. Um sistema que avisa só quando precisa é
ouvido. Um que avisa o tempo todo acaba mandado para o `/dev/null`.
:::

:::tree title="Onde estamos agora"
acervo/
  bootstrap.php          # E_ALL, log, warning vira exceção
  src/
    Registro.php         # uma linha JSON por evento
    Importador.php       # conta lidas, importadas, descartadas
  scripts/
    importar-doacoes.php # require bootstrap; exit(1) se zerar
  var/
    log/                 # fora do Git
:::

:::summary
- `Warning` e `Deprecated` não param o programa; `Fatal error` e exceção
  não capturada param.
- Warning é o PHP improvisando um valor. Não o deixe passar.
- `set_error_handler` transforma warnings em `ErrorException`;
  `Deprecated` vai para o log.
- `bootstrap.php` junta num lugar: `E_ALL`, `display_errors` desligado,
  log ligado, tratador de erro, última rede.
- A pilha se lê de baixo para cima; procure a primeira linha que é sua.
- `@` é o `catch` vazio de um caractere.
- Registre com nível, mensagem fixa e contexto. A PSR-3 padroniza isso.
:::

:::checkpoint
Você reconhece os níveis de erro do PHP, faz um warning parar o programa em
vez de deixá-lo seguir com um valor improvisado, lê uma pilha de chamadas
até a linha que interessa, e deixa um script da madrugada falar quando dá
errado — e só quando dá errado.
:::

:::exercise level=1
Para cada mensagem, diga o nível e se o programa continua **sem** o
`bootstrap.php` deste capítulo:

1. `Undefined array key "isbn"`
2. `Passing null to parameter #1 ($string) of type string is deprecated`
3. `Uncaught TypeError: diasDeAtraso(): Argument #1 ($prazo) must be of
   type DateTimeImmutable, string given`
4. `file_get_contents(capa.jpg): Failed to open stream`

:::answer
1. `Warning`. Continua, com `null` no lugar do ISBN.
2. `Deprecated`. Continua.
3. Exceção (`TypeError`, um `Error`) não capturada. Para.
4. `Warning`. Continua, com `false` no lugar do conteúdo — e o `false`
   segue até alguém tentar usá-lo como texto.

Com o `bootstrap.php`, os itens 1 e 4 também param, e o 2 vai para o log.
:::

:::exercise level=2
Leia a pilha e responda: em que função o erro nasceu, com que valor, e
qual é a linha **do seu código** por onde você começaria a investigar?

```text
Fatal error: Uncaught ValueError: "emprestado " is not a valid
backing value for enum StatusExemplar
Stack trace:
#0 /srv/acervo/src/Acervo/Exemplar.php(41):
   StatusExemplar::from('emprestado ')
#1 /srv/acervo/src/Acervo/RepositorioDeExemplares.php(58):
   Exemplar::doBanco(Array)
#2 /srv/acervo/scripts/relatorio.php(19):
   RepositorioDeExemplares->todos()
#3 {main}
```

:::answer
Nasceu em `StatusExemplar::from`, o método do enum do capítulo
@cap:enums-datas-e-valores, chamado com `'emprestado '` — com um espaço no
fim.

`from` está certo em recusar: o valor não é um dos casos. A primeira linha
que é código seu é `Exemplar.php`, linha 41, mas a pergunta útil vai uma
linha além: **de onde veio o espaço?** O `doBanco` recebe o array do
repositório, que o leu do banco. O espaço está numa linha da tabela
`exemplares` — provavelmente importada do Sistema antigo.

Conserto em duas partes: limpar os dados (`UPDATE ... SET status =
TRIM(status)`) e decidir se o `doBanco` deve aceitar sujeira. A resposta
deste livro é não: o erro apareceu, e é bom que tenha aparecido.
:::

:::exercise level=3
A Márcia quer "um e-mail quando a importação der errado". Descreva o que
você mudaria no `bootstrap.php` e no script de importação, e diga por que
**não** mandaria um e-mail para cada linha descartada.

:::answer
O e-mail entra na última rede, e só nela: o `set_exception_handler` já é
chamado exatamente quando a importação falhou de vez. Depois do
`error_log`, ele chama o envio, com a mensagem e o nome do script — sem a
pilha, que fica no log. A outra condição de falha é a do fim do script:
lidas maior que zero e importadas zero. Em vez de `exit(1)` direto, ela
lança uma exceção, e cai na mesma rede.

Linha descartada não gera e-mail porque uma importação de duzentas mil
linhas com seiscentas descartadas mandaria seiscentos e-mails, e na
terceira noite alguém criaria uma regra para mandá-los para a lixeira — o
`/dev/null` da história, agora na caixa de entrada. O que vai para a
Márcia é o resumo: um e-mail por noite, com as três contagens, e só
quando as descartadas passarem de um limite que ela escolhe.
:::
