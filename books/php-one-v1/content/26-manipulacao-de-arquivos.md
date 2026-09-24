---
title: "Manipulação de arquivos"
number: 26
slug: manipulacao-de-arquivos
part: p5
kicker: "A planilha de doações tinha duzentas mil linhas. O script que a lia de uma vez parou na terceira, sem ler nenhuma."
goal: >-
  Ler e escrever arquivos sem depender da pasta de onde o script foi
  chamado, ler um arquivo grande uma linha por vez, separar a leitura do
  processamento com um gerador, tratar codificação e BOM, e gravar sem
  deixar meio arquivo para trás.
---

:::story Na linha três
O Seu Juvenal chegou com um pen drive e um sorriso.

— A doação da escola estadual. Tudo numa planilha. Duzentos mil livros.

— Duzentos mil? — perguntou a Vera. — A biblioteca tem quatro mil.

— Duzentos mil linhas. É o acervo inteiro deles, eles estão fechando. A
gente escolhe o que quer.

A Tainá exportou a planilha para CSV — nove megabytes — e rodou o script
de importação que tinha escrito para as doações pequenas, de cinquenta
linhas. O servidor de homologação da Vertexo tinha um limite de memória
baixo, configurado de propósito pelo Nonato anos antes.

```text
PHP Fatal error: Allowed memory size of 16777216 bytes exhausted
(tried to allocate 4096 bytes) in /srv/importar.php on line 3
```

— Linha três — disse ela. — É a linha que lê o arquivo.

Dedé olhou a linha.

```php
$linhas = file('doacoes.csv');
```

— Ela lê o arquivo inteiro para dentro da memória antes de você olhar a
primeira linha.

— E os livros do Seu Juvenal?

— Estão todos na memória. Por isso ela acabou.
:::

## O caminho relativo a quê

Antes da memória, uma armadilha que o script da Tainá tinha e ainda não
tinha mostrado. `file('doacoes.csv')` procura o arquivo **na pasta de onde
o PHP foi chamado**, não na pasta onde o script está:

```text
$ cd /srv && php importar.php
(funciona)

$ cd / && php /srv/importar.php
Warning: file(doacoes.csv): Failed to open stream: No such
file or directory in /srv/importar.php on line 5
```

O agendador de tarefas do servidor, que roda a importação de madrugada,
chama os scripts a partir da raiz. Todo caminho relativo quebra ali, e não
na máquina de quem testou.

O PHP dá a pasta do próprio arquivo numa constante:

```php
$caminho = __DIR__ . '/doacoes.csv';
```

`__DIR__` é a pasta do arquivo PHP em que a linha está escrita — sempre, de
onde quer que ele seja chamado. Todo caminho deste capítulo em diante começa
por ela, ou por uma configuração que diga onde os arquivos moram.

:::key
Caminho relativo é relativo à pasta de quem **chamou**, e isso muda entre
o terminal, o agendador e o servidor web. Monte o caminho a partir de
`__DIR__`, e o script encontra os arquivos de onde quer que rode.
:::

## Ler tudo e ler uma linha por vez

O capítulo @cap:do-arquivo-ao-banco usou `file_get_contents` e
`file_put_contents`: o arquivo inteiro vira um texto, ou um texto vira o
arquivo inteiro. Para um JSON de cinquenta livros, é o certo. Para uma
planilha de duzentas mil linhas, é o erro da história.

Medindo, no servidor sem o limite:

```php title="tudo.php" numbered
<?php

declare(strict_types=1);

$linhas = file(__DIR__ . '/doacoes.csv');

echo count($linhas), " linhas\n";
echo round(memory_get_peak_usage() / 1048576, 1), " MB\n";
```

```text
$ php tudo.php
200001 linhas
28.5 MB
```

Um arquivo de nove megabytes ocupa vinte e oito e meio na memória:
duzentos mil textos separados, cada um com o custo de ser um valor do PHP.
`memory_get_peak_usage()` devolve o máximo de memória que o script usou até
ali, em bytes.

A alternativa é abrir o arquivo e ler **uma linha de cada vez**:

```php title="linha-a-linha.php" numbered
<?php

declare(strict_types=1);

$arquivo = fopen(__DIR__ . '/doacoes.csv', 'r');
if ($arquivo === false) {
    throw new RuntimeException('doacoes.csv não abriu');
}

$total = 0;
try {
    while (($linha = fgets($arquivo)) !== false) {
        $total++;
    }
} finally {
    fclose($arquivo);
}

echo "{$total} linhas\n";
```

`fopen` abre o arquivo e devolve um **recurso**: um identificador que o
PHP usa para ler aos poucos. O `'r'` é o modo — leitura. `fgets` lê até o
fim da linha seguinte e devolve `false` quando o arquivo acaba. `fclose`
devolve o arquivo ao sistema.

O `finally` do capítulo @cap:excecoes está ali de propósito: se algo
falhar no meio da leitura, o arquivo é fechado do mesmo jeito.

## CSV, e o gerador que separa ler de usar

Uma planilha em CSV tem campos separados — por ponto e vírgula, quando vem
de um Excel em português — e aspas em volta dos que têm o separador dentro.
Separar à mão com `explode(';', $linha)` quebra no primeiro título com
ponto e vírgula. `fgetcsv` lê uma linha e já a devolve separada em campos.

E há uma forma de escrever "ler o CSV linha a linha" uma vez só, e usar em
qualquer lugar como se fosse um array:

```php title="csv.php" numbered
<?php

declare(strict_types=1);

function lerCsv(string $caminho): Generator
{
    $arquivo = fopen($caminho, 'r');
    if ($arquivo === false) {
        throw new RuntimeException("não abriu: {$caminho}");
    }

    $ler = fn() => fgetcsv($arquivo, separator: ';', escape: '');

    try {
        $cabecalho = $ler();
        while (($campos = $ler()) !== false) {
            yield array_combine($cabecalho, $campos);
        }
    } finally {
        fclose($arquivo);
    }
}

$total = 0;
$restauro = 0;

foreach (lerCsv(__DIR__ . '/doacoes.csv') as $livro) {
    $total++;
    if ($livro['estado'] === 'restauro') {
        $restauro++;
    }
}

echo "{$total} livros, {$restauro} para restauro\n";
echo round(memory_get_peak_usage() / 1048576, 1), " MB\n";
```

```text
$ php csv.php
200000 livros, 28571 para restauro
0.4 MB
```

Zero vírgula quatro megabytes, contra vinte e oito e meio. E o mesmo
resultado com o limite de dezesseis do servidor de homologação.

`yield` é o que faz de `lerCsv` um **gerador**. Uma função com `yield` não
roda inteira quando é chamada: ela devolve um objeto `Generator`, que o
`foreach` percorre. A cada volta, a função roda até o próximo `yield`,
entrega aquele valor, e **pausa** ali, com o arquivo aberto, até o
`foreach` pedir o seguinte.

:::term Gerador
Uma função com `yield`. Chamada, ela não roda: devolve um `Generator`. Cada
volta do `foreach` sobre ele executa a função até o próximo `yield` e
recebe o valor entregue. Só um valor existe na memória por vez.

Quem usa o gerador escreve um `foreach` comum, sem saber se os valores vêm
de um array, de um arquivo de nove megabytes ou de uma consulta ao banco.
:::

`array_combine($cabecalho, $campos)` junta as duas listas num array com
nome: `['titulo' => 'Livro 1', 'autor' => ...]`. O resto do programa lê
`$livro['estado']`, e não `$livro[3]`.

Os argumentos com nome — `separator: ';'` — são os do capítulo
@cap:funcoes. `escape: ''` desliga um caractere de escape antigo do CSV do
PHP que não existe no CSV do Excel, e que o PHP 8.4 passa a exigir que seja
informado.

:::key
O gerador separa **de onde os dados vêm** de **o que se faz com eles**. A
importação, a contagem e o relatório usam o mesmo `lerCsv`. Se amanhã as
doações chegarem de outro formato, muda o gerador, e nenhum `foreach`.

No volume 2, o Eloquent tem a mesma ideia com outro nome: percorrer uma
tabela de milhões de linhas sem carregá-la inteira.
:::

## Codificação, e três bytes no começo

Os títulos da planilha do Seu Juvenal chegaram assim:

```text
Livro nÃºmero 1
```

É o `ú` de "número" em UTF-8, lido como se fosse outra codificação — o
defeito do capítulo @cap:strings, agora vindo de um arquivo. Duas causas
aparecem com frequência em planilha exportada do Excel.

**O arquivo não está em UTF-8.** Excel antigo grava CSV em Windows-1252, a
codificação de antes do UTF-8 nos computadores brasileiros. A conversão é
uma linha, feita na entrada:

```php
$titulo = mb_convert_encoding($campos[0], 'UTF-8', 'Windows-1252');
```

**O arquivo está em UTF-8 e começa com um BOM.** BOM são três bytes
invisíveis — `EF BB BF` — que alguns programas põem no começo do arquivo
para anunciar que ele é UTF-8. O PHP não os remove. Eles grudam no primeiro
campo do cabeçalho, e `$livro['titulo']` passa a não existir, porque a
chave se chama, na verdade, `"\xEF\xBB\xBFtitulo"`.

```php
$bom = fread($arquivo, 3);
if ($bom !== "\xEF\xBB\xBF") {
    rewind($arquivo);
}
```

`fread` lê os três primeiros bytes. Se não forem o BOM, `rewind` volta ao
começo do arquivo e nada se perdeu. Essas quatro linhas entram no
`lerCsv`, logo depois do `fopen`.

:::pitfall
O BOM não aparece quando você abre o arquivo no editor, nem quando imprime
o cabeçalho no terminal. O sintoma é uma chave que "existe" e dá
`Undefined array key "titulo"`. Quando uma chave que você está vendo não é
encontrada, imprima-a com `var_dump(array_keys($linha))`: o
`string(9)` para uma palavra de seis letras entrega os três bytes a mais.
:::

## Escrever sem deixar meio arquivo

O relatório de doações escolhidas volta para o Seu Juvenal em CSV, para ele
abrir no Excel:

```php title="exportar.php" numbered
<?php

declare(strict_types=1);

function gravarCsv(string $caminho, array $linhas): void
{
    $temporario = $caminho . '.tmp';
    $arquivo = fopen($temporario, 'w');
    if ($arquivo === false) {
        throw new RuntimeException("não gravou: {$temporario}");
    }

    try {
        fwrite($arquivo, "\xEF\xBB\xBF");
        foreach ($linhas as $linha) {
            fputcsv($arquivo, $linha, separator: ';', escape: '');
        }
    } finally {
        fclose($arquivo);
    }

    rename($temporario, $caminho);
}

gravarCsv(__DIR__ . '/escolhidos.csv', [
    ['titulo', 'autor'],
    ['Vidas Secas', 'Graciliano Ramos'],
    ['O Cortiço', 'Aluísio Azevedo'],
]);
```

Três decisões.

**O BOM vai de propósito.** Aqui ele serve: é o que faz o Excel abrir o
acento certo.

**`fputcsv`** escreve cada linha com o separador e as aspas certas — o
inverso do `fgetcsv`.

**O arquivo é escrito com outro nome e renomeado no fim.** Se o script
morrer no meio — memória, queda de energia, um erro na linha oito mil —,
o que sobra é um `escolhidos.csv.tmp` pela metade, e o `escolhidos.csv` da
véspera continua inteiro. `rename` troca um arquivo pelo outro de uma vez:
quem abrir o arquivo nunca vê meio relatório.

O capítulo @cap:do-arquivo-ao-banco mostrou a outra metade do problema:
duas pessoas escrevendo no mesmo arquivo ao mesmo tempo. Para isso existe
`flock`, que tranca o arquivo enquanto alguém escreve — e existe o banco
de dados, que foi a resposta daquele capítulo e continua sendo a deste.
Arquivo serve para entrar e sair do sistema. Estado compartilhado mora no
banco.

## O que o volume 2 faz com arquivo

No volume 2, dois assuntos voltam com roupa de framework.

O **upload**: a capa do livro, enviada pela tela. O arquivo chega numa
pasta temporária, com um nome escolhido por quem enviou — e esse nome não
pode virar caminho, porque `../../.env` também é um nome.

O **armazenamento**: o Laravel dá uma camada, `Storage`, que grava em disco
local ou num serviço de arquivos na nuvem com o mesmo código. Por baixo,
são os `fopen`, `fwrite` e `rename` deste capítulo.

:::note Na sua carreira
"Funciona com o arquivo de teste" é a frase que antecede a maior parte dos
problemas com arquivo: o de teste tem cinquenta linhas, está em UTF-8 sem
BOM e fica na mesma pasta do script. O de produção tem duzentas mil, veio
do Excel de alguém e é lido pelo agendador a partir da raiz.

Antes de dar uma importação por pronta, teste com um arquivo grande, com
acento, com BOM, e chamando o script de outra pasta. São quatro minutos, e
é o que separa o script que funciona do que funciona na sua máquina.
:::

:::tree title="Onde estamos agora"
acervo/
  src/
    Importacao/
      Csv.php              # ler(): gerador, BOM, separador ;
                           # gravar(): temporário + rename
  scripts/
    importar-doacoes.php   # __DIR__, nunca caminho relativo
:::

:::summary
- Caminho relativo é relativo a quem chamou. `__DIR__` é a pasta do próprio
  arquivo.
- `file` e `file_get_contents` carregam o arquivo inteiro; `fopen` e
  `fgets` leem uma linha por vez. `fclose` no `finally`.
- `fgetcsv` separa os campos respeitando aspas; `fputcsv` escreve.
- Uma função com `yield` é um gerador: entrega um valor por vez e pausa.
  Separa a origem dos dados do que se faz com eles.
- Converta codificação na entrada; o BOM gruda no primeiro campo e precisa
  sair.
- Grave num temporário e renomeie no fim: nunca sobra meio arquivo.
:::

:::checkpoint
Você lê um CSV de duzentas mil linhas com memória constante, escreve a
leitura como um gerador reaproveitável, reconhece o BOM pelo sintoma da
chave que não existe, e grava um arquivo sem risco de deixá-lo pela metade.
:::

:::exercise level=1
Diga qual função você usaria em cada caso, e por quê:

1. Ler a configuração `biblioteca.json`, de 2 KB.
2. Contar as linhas de um log de 3 GB.
3. Gravar o relatório mensal que outras pessoas abrem a qualquer hora.

:::answer
1. `file_get_contents` e `json_decode`. O arquivo é pequeno e precisa
   inteiro de uma vez.
2. `fopen` e `fgets` num laço — ou um gerador. `file` tentaria pôr três
   gigabytes na memória.
3. Escrever num temporário e renomear. Quem abrir durante a gravação vê o
   relatório anterior inteiro, e não metade do novo.
:::

:::exercise level=2
Escreva um gerador `soOsEmRestauro(Generator $livros): Generator` que
recebe o gerador do `lerCsv` e só entrega os livros com `estado` igual a
`restauro`. Use os dois juntos para gravar um CSV só com esses livros.

:::answer
```php
function soOsEmRestauro(Generator $livros): Generator
{
    foreach ($livros as $livro) {
        if ($livro['estado'] === 'restauro') {
            yield $livro;
        }
    }
}

$restauro = soOsEmRestauro(lerCsv(__DIR__ . '/doacoes.csv'));
gravarCsv(__DIR__ . '/restauro.csv', $restauro);
```

Para isso funcionar, `gravarCsv` passa a aceitar `iterable` em vez de
`array` — o tipo que aceita array **e** gerador. O caminho inteiro, da
leitura à gravação, continua com um livro por vez na memória: nenhum dos
dois geradores guarda a lista.

Faltou o cabeçalho no arquivo gravado: ele precisa ser a primeira linha
passada a `gravarCsv`, e fica de exercício dentro do exercício.
:::

:::exercise level=3
A importação noturna das doações roda às 2h, pelo agendador, e grava as
escolhidas no banco. Na primeira noite, importou zero livros e não deu
erro nenhum. Liste as três causas mais prováveis, na ordem em que você
investigaria, e o que acrescentaria ao script para que a próxima falha não
seja silenciosa.

:::answer
Na ordem:

1. **Caminho relativo.** O agendador chama a partir da raiz, o `fopen`
   falha com um *warning* e devolve `false` — e, se o script não confere o
   `false`, o laço não roda nenhuma vez.
2. **BOM no cabeçalho.** `$livro['titulo']` não existe; se o script
   pula linhas sem título, pula todas.
3. **Codificação.** Títulos com acento quebrado falham numa validação e são
   descartados em silêncio.

O que eu acrescentaria:

- conferir o `false` do `fopen` e lançar exceção — o capítulo
  @cap:excecoes;
- contar linhas lidas, importadas e descartadas, e registrar as três ao
  fim;
- terminar com erro se lidas for maior que zero e importadas for zero.

A importação que "não deu erro" deu três: o sistema só não tinha como
contar nenhum deles. O capítulo @cap:erros-e-debug trata de fazer o PHP
contar.
:::
