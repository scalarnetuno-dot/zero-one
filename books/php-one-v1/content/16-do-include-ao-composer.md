---
title: "Do include ao Composer"
number: 16
slug: do-include-ao-composer
part: p3
kicker: "Duas funções com o mesmo nome em dois arquivos. A página funciona ou morre dependendo de qual deles entra primeiro."
goal: >-
  Entender o que `include` e `require` fazem, o que o `_once` resolve e o
  que ele não resolve, criar um projeto com Composer, instalar a primeira
  dependência e explicar a diferença entre `install` e `update` para
  alguém do time.
---

:::story Depende de qual entra primeiro
O recibo da Casa Amarela imprimia a data como `12/03/26`. O relatório de
atrasados, gerado no mesmo dia, imprimia `12/03/2026`.

Tainá perguntou qual dos dois estava certo.

— Os dois — disse Dedé. — Em arquivos diferentes.

O `funcoes2.php` tinha uma `formatarData()`. O `funcoes2_NOVO_final.php`
tinha outra, com um caractere a menos no formato. Nenhuma página do Sistema
incluía as duas, e foi assim que quinze anos passaram sem que ninguém
precisasse escolher.

Até a tela nova de renovação, que precisava das duas.

— E aí?

— E aí, na quarta-feira, ela funcionava. Na quinta, depois que alguém
trocou a ordem de dois `include`, parou.

— Parou como?

Dedé virou o monitor.

```text
Fatal error: Cannot redeclare function formatarData()
(previously declared in /app/funcoes2_NOVO_final.php:3)
in /app/funcoes2.php on line 2
```

— E na quarta funcionava por quê?

— Porque na quarta a ordem era a outra.
:::

## Um arquivo vira dois, e dois viram trinta

O projeto da Casa Amarela já tem o mesmo problema, em escala menor.

Todo programa que fala com o banco começa com a mesma linha:

```php
require 'conexao.php';
```

São seis arquivos hoje. Serão trinta antes de março. E o `conexao.php` não
é o único candidato a ser compartilhado: a `multaEmCentavos()` vai ser usada
pelo recibo, pelo relatório e pela tela de devolução.

Uma coisa mudou no `conexao.php` desde que ele nasceu: perdeu o
`echo "conectado\n"` do fim. Era uma linha simpática enquanto o arquivo
rodava sozinho, e é uma linha que suja a saída dos seis no momento em que
ele passa a ser incluído pelos seis.

```php title="conexao.php" numbered
<?php

$dsn = 'mysql:host=127.0.0.1;port=3306'
     . ';dbname=casa_amarela;charset=utf8mb4';

$pdo = new PDO($dsn, 'root', 'senha', [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES => false,
]);
```

:::key
Arquivo feito para ser incluído não imprime nada. Ele define — variáveis,
funções, configuração — e devolve o controle.

Um `echo` num arquivo incluído aparece na saída de todo mundo que o inclui,
inclusive no meio de um JSON e antes de um cabeçalho HTTP.
:::

## include e require

As duas palavras fazem a mesma coisa: pegam o conteúdo de outro arquivo e
executam ali, como se estivesse escrito no lugar. A diferença é o que
acontece quando o arquivo não existe.

Com `include`:

```php title="recibo.php" numbered
<?php

include 'taxas.php';
echo "cheguei aqui\n";
```

```text
Warning: include(taxas.php): Failed to open stream: No such file or
directory in /app/recibo.php on line 3

Warning: include(): Failed opening 'taxas.php' for inclusion
(include_path='.:/usr/share/php') in /app/recibo.php on line 3
cheguei aqui
```

Dois avisos — e o programa **continuou**. Imprimiu "cheguei aqui" sem as
taxas que ia usar.

Troque uma palavra:

```php title="recibo.php" numbered
<?php

require 'taxas.php';
echo "cheguei aqui\n";
```

```text
Warning: require(taxas.php): Failed to open stream: No such file or
directory in /app/recibo.php on line 3

Fatal error: Uncaught Error: Failed opening required 'taxas.php'
(include_path='.:/usr/share/php') in /app/recibo.php:3
```

O programa parou. Não imprimiu nada depois.

| | Arquivo não existe | O programa |
|---|---|---|
| `include` | aviso | continua |
| `require` | erro fatal | para |

Tabela: A escolha não é de estilo. É a resposta a uma pergunta: *este
programa faz sentido sem esse arquivo?*

Para o `conexao.php` a resposta é não — um programa de empréstimo sem banco
não tem o que fazer, e `require` é o certo. Para um arquivo de tradução
opcional, ou um `config.local.php` que só existe na sua máquina, `include`
é honesto.

:::pitfall
A tentação é usar `include` "para não quebrar". O resultado é um programa
que segue em frente sem metade do que precisava e falha trinta linhas
depois, com uma mensagem sobre variável indefinida que não tem nenhuma
relação visível com o arquivo que faltou.

Quebrar cedo, com o nome do arquivo que faltou, é mais barato.
:::

## O que o `_once` resolve

Existem `include_once` e `require_once`. Eles guardam a lista de arquivos já
carregados e ignoram o pedido repetido.

O problema real que isso resolve aparece assim que os seus arquivos passam a
incluir uns aos outros:

```php title="relatorio.php"
<?php

require 'conexao.php';
require 'multa.php';   // o multa.php também faz require 'conexao.php'
```

Sem `_once`, o `conexao.php` roda duas vezes: duas conexões abertas, e a
segunda sobrescrevendo o `$pdo` da primeira. Com `require_once`, roda uma.

```php title="relatorio.php"
<?php

require_once 'conexao.php';
require_once 'multa.php';
```

## O que o `_once` não resolve

Aqui mora a confusão que custou a quarta-feira do Dedé.

O `_once` compara **arquivos**, não nomes. Dois arquivos diferentes que
declaram a mesma função continuam sendo dois arquivos diferentes — e os dois
vão ser carregados.

Reproduza. Três arquivos pequenos, na mesma pasta:

```php title="funcoes2.php" numbered
<?php

function formatarData(string $iso): string
{
    return date('d/m/Y', strtotime($iso));
}
```

```php title="funcoes2_NOVO_final.php" numbered
<?php

function formatarData(string $iso): string
{
    return date('d/m/y', strtotime($iso));
}
```

A única diferença está no formato: `Y` imprime o ano com quatro dígitos, `y`
com dois. A função `date()` recebe esse formato e um instante em segundos;
`strtotime()` converte o texto `2026-03-12` para esse número de segundos.

```php title="renovar.php" numbered
<?php

include_once 'funcoes2.php';
include_once 'funcoes2_NOVO_final.php';

echo formatarData('2026-03-12'), "\n";
```

```text
Fatal error: Cannot redeclare function formatarData()
(previously declared in /app/funcoes2.php:3)
in /app/funcoes2_NOVO_final.php on line 3
```

O `_once` não impediu nada, porque nada foi incluído duas vezes. Foram dois
arquivos, uma vez cada, com a mesma função dentro.

## O remendo que congelou o defeito

A saída que alguém encontrou no Sistema, em 2017, foi cercar a segunda
declaração com uma pergunta:

```php title="funcoes2_NOVO_final.php" numbered
<?php

if (!function_exists('formatarData')) {
    function formatarData(string $iso): string
    {
        return date('d/m/y', strtotime($iso));
    }
}
```

`function_exists()` devolve `true` se uma função com aquele nome já foi
declarada. O `!` inverte: *declare só se ainda não existir*.

Rode o `renovar.php` de novo:

```text
12/03/2026
```

Funciona. E funciona com uma das duas versões descartada em silêncio, porque
a outra chegou primeiro.

Agora inverta as duas linhas do `renovar.php`:

```php title="renovar.php" numbered
<?php

include_once 'funcoes2_NOVO_final.php';
include_once 'funcoes2.php';

echo formatarData('2026-03-12'), "\n";
```

```text
Fatal error: Cannot redeclare function formatarData()
(previously declared in /app/funcoes2_NOVO_final.php:3)
in /app/funcoes2.php on line 2
```

Morreu — porque só um dos dois arquivos ganhou a cerca.

:::pitfall
`function_exists()` em volta de uma declaração é quase sempre a marca de um
conflito que ninguém quis resolver. Ele troca um erro fatal, que aponta os
dois arquivos e as duas linhas, por um comportamento que depende da ordem de
carregamento — e ordem de carregamento é a coisa que mais muda quando
alguém mexe num `include` sem olhar.

Quando encontrar um, a pergunta não é "posso tirar?". É: **quais são as duas
versões, e qual delas o sistema está usando hoje?**
:::

## O Composer não é um instalador

Com trinta arquivos, "quem inclui quem" vira trabalho de expediente
inteiro. Com uma biblioteca de terceiros, vira impossível: a biblioteca tem
os próprios arquivos, que incluem outros arquivos dela, e ela não sabe onde
você colocou a pasta.

O Composer resolve três problemas de uma vez, e só o primeiro é "baixar
coisas":

1. **Descobrir o que instalar.** Você pede uma biblioteca; ela depende de
   outras duas; uma delas exige uma versão que briga com o que você já tem.
   Escolher o conjunto que fecha é um problema de contas, não de download.
2. **Registrar exatamente o que foi instalado**, para que a sua máquina, a
   da Tainá e o servidor rodem o mesmo código.
3. **Carregar os arquivos** sem que você escreva um `require` por
   biblioteca.

:::term Dependência
Código que o seu projeto usa e não escreveu. Uma dependência tem nome,
versão e, quase sempre, dependências próprias — que passam a ser suas
também, sem você ter pedido.
:::

## O projeto ganha um nome

Até agora a pasta do projeto era uma pasta.

```text
$ composer init
```

O comando faz perguntas. As respostas do nosso projeto:

```text
Package name (<vendor>/<name>): casa-amarela/acervo
Description []: Sistema do acervo da Biblioteca Casa Amarela
Author [n to skip]: n
Minimum Stability []:
Package Type []: project
License []: proprietary

Would you like to define your dependencies interactively [yes]? no
Would you like to define your dev dependencies interactively [yes]? no
Add PSR-4 autoload mapping? [src/, n to skip]: n
```

A última resposta ficou em `n` porque o projeto ainda não tem nada para
mapear. As duas anteriores ficaram em `no` porque instalar pela linha de
comando é mais simples do que responder a um formulário.

O resultado é um arquivo:

```json title="composer.json"
{
    "name": "casa-amarela/acervo",
    "description": "Sistema do acervo da Biblioteca Casa Amarela",
    "type": "project",
    "license": "proprietary",
    "require": {}
}
```

Nove linhas, nenhuma mágica. `require` vazio quer dizer: este projeto não
depende de nada ainda.

## A primeira dependência

Há quatro capítulos que os dados do acervo aparecem na tela assim:

```php
var_dump($livros);
```

```text
array(2) { [0]=> array(3) { ["id"]=> int(12) ["titulo"]=>
string(12) "Dom Casmurro" ["ano"]=> int(1899) } [1]=> array(3) {
["id"]=> int(31) ["titulo"]=> string(18) "Memórias Póstumas"
["ano"]=> int(1881) } }
```

Informação completa, leitura impossível. Existe uma biblioteca que faz a
mesma coisa formatada, e ela é o primeiro pedido do projeto:

```text
$ composer require --dev symfony/var-dumper
```

```text
./composer.json has been updated
Running composer update symfony/var-dumper
Lock file operations: 3 installs, 0 updates, 0 removals
  - Locking symfony/deprecation-contracts (v3.5.1)
  - Locking symfony/polyfill-mbstring (v1.31.0)
  - Locking symfony/var-dumper (v7.2.3)
Writing lock file
Installing dependencies from lock file (including require-dev)
Package operations: 3 installs, 0 updates, 0 removals
  - Installing symfony/deprecation-contracts (v3.5.1)
  - Installing symfony/polyfill-mbstring (v1.31.0)
  - Installing symfony/var-dumper (v7.2.3)
Generating autoload files
```

Você pediu um pacote e recebeu três. Os outros dois são dependências do
primeiro: o `var-dumper` precisa deles, e o Composer trouxe sem perguntar
porque a alternativa seria perguntar quarenta vezes.

```text
$ composer show --tree
```

```text
casa-amarela/acervo project
`--symfony/var-dumper v7.2.3
    |--php >=8.2
    |--symfony/deprecation-contracts ^2.5|^3
    `--symfony/polyfill-mbstring ~1.0
```

Para usar, uma linha nova no começo do programa:

```php title="listar.php" numbered
<?php

require 'vendor/autoload.php';
require 'conexao.php';

$livros = $pdo->query(
    'SELECT id, titulo, ano FROM livros ORDER BY titulo LIMIT 2'
)->fetchAll();

dump($livros);
```

```text
array:2 [
  0 => array:3 [
    "id" => 12
    "titulo" => "Dom Casmurro"
    "ano" => 1899
  ]
  1 => array:3 [
    "id" => 31
    "titulo" => "Memórias Póstumas"
    "ano" => 1881
  ]
]
```

O `vendor/autoload.php` é o arquivo que o Composer gerou na última linha da
instalação. Ele sabe onde mora cada coisa que o Composer baixou, e é o único
`require` de biblioteca que você vai escrever no projeto inteiro.

:::key
`dump()` mostra e continua. `dd()` mostra e para — *dump and die*. O segundo
é o que você quer quando está caçando um valor no meio de um laço e não quer
rolar trezentas linhas de saída.
:::

## `composer.json` pede, `composer.lock` lembra

A instalação mexeu em dois arquivos. Eles parecem redundantes e não são.

O `composer.json` ganhou três linhas:

```json title="composer.json"
    "require-dev": {
        "symfony/var-dumper": "^7.2"
    }
```

Isso é um **pedido**: qualquer 7 ponto alguma coisa serve.

O `composer.lock` tem agora algumas centenas de linhas, e entre elas:

```json title="composer.lock"
        {
            "name": "symfony/var-dumper",
            "version": "v7.2.3",
            "source": {
                "type": "git",
                "reference": "a75bf8b0f8b9d0a92f0cb4e6c6b8"
            }
        }
```

Isso é um **registro**: foi esta versão, deste commit. Não é uma faixa, é um
ponto.

A diferença aparece nos dois comandos:

| Comando | Lê | Escreve | Quando |
|---|---|---|---|
| `composer install` | o `.lock` | nada | ao clonar e no deploy |
| `composer update` | o `.json` | o `.lock` | quando você **decide** atualizar |

Tabela: `install` reproduz. `update` decide. Confundir os dois é o defeito
de configuração mais caro que existe.

:::pitfall
`composer update` no servidor é a versão moderna de "funciona na minha
máquina". Ele ignora o `.lock`, resolve tudo de novo, e o servidor sobe com
versões que ninguém testou — às vezes lançadas naquela manhã.

No servidor, só `composer install`. E se o `.lock` não estiver no Git, esse
comando não tem o que ler: você voltou ao problema anterior por outro
caminho.
:::

## O acento circunflexo que você aceitou sem ler

O `^7.2` que apareceu no `composer.json` tem regra, e a regra vem da
numeração que quase todo pacote PHP segue: **maior.menor.correção**.

- **maior** muda quando algo quebra de propósito;
- **menor** muda quando algo é acrescentado sem quebrar;
- **correção** muda quando algo é consertado.

| Escrito | Aceita | Recusa |
|---|---|---|
| `^7.2` | 7.2.0, 7.4.1, 7.9.9 | 8.0.0 e 7.1.9 |
| `~7.2.3` | 7.2.3, 7.2.11 | 7.3.0 |
| `7.2.3` | só 7.2.3 | todo o resto |

Tabela: O `^` é o padrão do `composer require` porque aposta que o autor
respeita a numeração. O `~` é para quando você quer só correção. A versão
fixa é para quando a aposta já deu errado uma vez.

## `require` e `require-dev`

O `var-dumper` entrou com `--dev`, e isso tem consequência.

- **`require`** é o que o programa precisa para **funcionar**.
- **`require-dev`** é o que **você** precisa para trabalhar: depurador,
  teste, formatador.

No servidor, a instalação pula a segunda lista:

```text
$ composer install --no-dev
```

O resultado é menos código no disco, menos superfície para problema de
segurança e um servidor sem ferramenta de depuração instalada.

E aqui está a armadilha que vem junto:

```text
Fatal error: Uncaught Error: Call to undefined function dump()
in /app/listar.php on line 9
```

Um `dump()` esquecido numa linha que só roda no caso raro não quebra nada na
sua máquina — onde o pacote existe — e derruba a página em produção, onde
ele não existe. É um erro de cinco segundos para consertar e de duas horas
para descobrir, porque o caso raro não acontece quando você está olhando.

## A pasta que não vai para o Git

O Composer criou uma pasta `vendor/` com o código das três bibliotecas. Ela
não entra no repositório:

```text title=".gitignore"
/vendor/
```

A lógica é simples: `vendor/` é **resultado**, e resultado se reproduz. Quem
clona o projeto roda `composer install` e recebe exatamente o mesmo
conteúdo, porque o `.lock` diz exatamente qual era.

| Arquivo | Vai para o Git | Por quê |
|---|---|---|
| `composer.json` | sim | é a intenção do projeto |
| `composer.lock` | sim | é o que faz as máquinas coincidirem |
| `vendor/` | não | é resultado, e pesa |

:::note Na sua carreira
Em algum projeto alguém vai propor versionar a `vendor/` — geralmente depois
de um deploy que falhou porque a rede caiu no meio do `composer install`.

O argumento contra não é "é feio". É concreto: a `vendor/` de um projeto
médio tem dezenas de milhares de arquivos, e cada atualização vira uma
alteração que ninguém consegue revisar. O problema real era a rede no
deploy, e ele tem solução própria: instalar antes de publicar e publicar a
pasta pronta.

Quando discordar de uma decisão dessas, traga o problema que ela tentava
resolver junto com a sua alternativa. Discordar sem isso é pedir para a
pessoa admitir que errou na frente do time, e ninguém topa.
:::

:::tree title="Onde estamos agora"
acervo/
  composer.json   # o que o projeto pede
  composer.lock   # o que o projeto recebeu
  vendor/         # gerado pelo Composer, fora do Git
  .gitignore
  conexao.php     # cria o $pdo, sem imprimir nada
  multa.php
  buscar.php
  cadastrar.php
  emprestar.php
  devolver.php
  listar.php
  recibo.php
:::

:::summary
- `include` avisa e segue; `require` para. A escolha responde "o programa
  faz sentido sem esse arquivo?".
- `_once` impede o **mesmo arquivo** duas vezes. Não impede dois arquivos
  diferentes de declararem a mesma função.
- `function_exists()` em volta de uma declaração troca um erro claro por uma
  dependência silenciosa da ordem de carregamento.
- O Composer resolve o conjunto de versões, registra o que instalou e gera o
  carregador. Baixar é a parte fácil.
- `composer.json` é o pedido; `composer.lock` é o registro. `install`
  reproduz, `update` decide.
- `^7.2` aceita qualquer 7.x; `~7.2.3` aceita só correções de 7.2; a versão
  fixa não aceita nada.
- `require-dev` não vai para produção — e o `dump()` esquecido, sim.
- `vendor/` fica fora do Git; `composer.lock` fica dentro.
:::

:::checkpoint
Você cria um projeto com `composer init`, instala uma dependência, sabe
dizer o que cada um dos dois arquivos de configuração guarda, lê uma faixa
de versão e reconhece pela mensagem de erro quando um pacote de
desenvolvimento faltou em produção.
:::

:::exercise level=1
O `composer.json` de um projeto pede `"monolog/monolog": "^3.5"`. Quais
destas versões o `composer update` pode instalar: 3.5.0, 3.9.2, 4.0.0,
3.4.9?

E se, em vez de `update`, alguém rodar `composer install` numa máquina que
acabou de clonar o projeto — qual versão vai ser instalada?

:::answer
O `update` pode instalar **3.5.0 e 3.9.2**. O `^` aceita da versão pedida
até o próximo número maior, sem alcançá-lo: recusa a 4.0.0 por ser maior e a
3.4.9 por ser anterior ao pedido.

O `install` não escolhe nada. Ele instala **a versão escrita no
`composer.lock`** — que pode ser a 3.5.0, mesmo que a 3.9.2 já exista. É
essa indiferença ao que há de novo que faz duas máquinas rodarem o mesmo
código.
:::

:::exercise level=2
Crie os três arquivos da seção do remendo: `funcoes2.php`,
`funcoes2_NOVO_final.php` (com a cerca do `function_exists`) e `renovar.php`.

Antes de rodar, escreva num papel o que sai em cada uma das duas ordens de
`include_once`. Depois rode as duas e confira.

Em seguida, ponha a cerca também no `funcoes2.php` e rode as duas ordens de
novo. Explique o que mudou e por que isso é pior.

:::answer
Com a cerca só no `funcoes2_NOVO_final.php`:

- `funcoes2.php` primeiro: imprime `12/03/2026`. A segunda declaração é
  descartada pela cerca.
- `funcoes2_NOVO_final.php` primeiro: erro fatal `Cannot redeclare`, porque
  o `funcoes2.php` não tem cerca e tenta declarar por cima.

Com cerca nos dois, as duas ordens funcionam — e é aí que fica pior:

```text
ordem A → 12/03/2026
ordem B → 12/03/26
```

Nenhum erro, nenhum aviso, e o formato da data passa a ser decidido pela
ordem dos `include`. O recibo e o relatório podem divergir para sempre sem
que nada no sistema reclame. O erro fatal era a única coisa que ainda
contava a verdade.

A correção de verdade é escolher uma das duas funções, apagar a outra e
acertar as chamadas — trabalho de meia hora que ninguém fez em nove anos
porque a cerca fez a urgência sumir.
:::

:::exercise level=3
Na sexta-feira, o deploy da Casa Amarela subiu e a tela de empréstimo passou
a devolver erro. O log do servidor diz:

```text
Fatal error: Uncaught Error: Call to undefined function dump()
in /app/emprestar.php on line 47
```

A linha 47 fica dentro de um `if` que só roda quando o exemplar está marcado
como `extraviado` — situação que acontece umas duas vezes por mês.

Responda três coisas: o que aconteceu, por que a conferência na máquina do
Dedé não pegou, e quais duas mudanças evitam a repetição.

:::answer
**O que aconteceu.** Alguém deixou um `dump()` de depuração no código. O
`symfony/var-dumper` está em `require-dev`, e o servidor instala com
`--no-dev` — então a função não existe lá. O programa sobe normalmente e só
quebra quando aquele `if` é alcançado.

**Por que não pegou.** Na máquina do Dedé o pacote está instalado, então a
linha funciona. E o caminho do `extraviado` não é percorrido à mão: depende
de um dado raro que ninguém lembra de criar antes de subir.

**As duas mudanças.**

A primeira é de processo e não custa nada: procurar `dump(` e `dd(` antes de
subir. A versão automatizada disso é uma regra no passo de publicação que
recusa o deploy se encontrar qualquer uma das duas.

A segunda é de cobertura: alguma forma de percorrer o caminho do exemplar
extraviado sem esperar ele acontecer. Enquanto o único jeito de executar
aquele `if` for a vida real, a produção continua sendo o lugar onde ele é
conferido.

Uma resposta que aparece e não resolve: mover o `var-dumper` para `require`.
Isso conserta o sintoma instalando uma ferramenta de depuração no servidor —
e ferramenta de depuração em produção é serra de bancada na sala de espera:
funciona, e não é lá que ela mora.
:::
