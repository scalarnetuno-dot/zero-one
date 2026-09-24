---
title: "Tipagem estrita"
number: 22
slug: tipagem-estrita
part: p4
kicker: "A ferramenta rodou por dezoito segundos e devolveu quarenta e uma somas de data com texto. Nenhuma delas tinha dado erro em quinze anos."
goal: >-
  Ligar o modo estrito no lugar certo, declarar tipos que dizem alguma
  coisa, saber o que o PHP não confere em execução e rodar análise estática
  num projeto legado sem parar a empresa.
---

:::story Dezoito segundos
Dedé instalou o PHPStan numa quinta à tarde, apontou para a pasta do
Sistema e foi pegar café.

Quando voltou, a saída tinha parado de rolar.

```text
 [ERROR] Found 1.247 errors
```

— Mil duzentos e quarenta e sete — leu Tainá.

— Em catorze mil linhas. Podia ser pior.

Ele filtrou por um tipo só, os que falavam de soma. Sobraram quarenta e um.

```text
  213    Binary operation "+" between string and int
         results in an error.
```

— O que tem na 213?

— `$data_devolucao + 14`.

Tainá levou um segundo.

— Isso funciona?

— Isso nunca deu erro.

— Não foi o que eu perguntei.
:::

## A linha que muda o arquivo inteiro

Desde o capítulo @cap:classes-e-objetos, o PHP vem convertendo texto em
número na porta
das funções: `'1899'` entra como `int(1899)` e ninguém reclama. Isso se
chama **modo coercitivo**, e é o padrão.

Uma linha desliga:

```php title="src/Acervo/Livro.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Acervo;
```

`declare(strict_types=1)` precisa ser a **primeira instrução** do arquivo,
antes até do `namespace`. Só pode haver comentário antes dela.

Com o modo estrito ligado, a porta deixa de converter:

```php
multaEmCentavos('3');
```

```text
Fatal error: Uncaught TypeError: multaEmCentavos():
Argument #1 ($dias) must be of type int, string given
```

E deixa de converter até o que parece inofensivo:

```php
multaEmCentavos(2.5);
```

```text
Fatal error: Uncaught TypeError: multaEmCentavos():
Argument #1 ($dias) must be of type int, float given
```

No modo coercitivo, esse `2.5` viraria `2` em silêncio. A multa de dois
dias e meio custaria dois dias, e a diferença apareceria na prestação de
contas de março, não na tela.

:::key
Existe uma exceção, e ela é proposital: `int` continua sendo aceito onde se
espera `float`, mesmo no modo estrito. Todo inteiro é um número real exato,
então nada se perde.

O caminho contrário é que perde, e é o que o modo estrito recusa.
:::

## O detalhe que quase todo mundo erra

A declaração vale para **as chamadas escritas naquele arquivo** — não para a
função que ele declara.

Prove com dois arquivos:

```php title="multa.php" numbered
<?php

declare(strict_types=1);

function multaEmCentavos(int $dias): int
{
    return $dias * 80;
}
```

```php title="relatorio.php" numbered
<?php

require 'multa.php';

var_dump(multaEmCentavos('3'));
```

```text
int(240)
```

Passou. O `strict_types` do `multa.php` não protegeu nada: quem decide é o
arquivo onde a **chamada** está escrita, e o `relatorio.php` não declarou
nada.

Ponha a linha no `relatorio.php` e o mesmo código morre com `TypeError`.

:::pitfall
A consequência prática é que `strict_types` não é uma configuração do
projeto: é uma decisão arquivo por arquivo.

Um projeto com a linha em 90% dos arquivos tem 10% de arquivos que chamam
tudo de forma frouxa — e são justamente os antigos, que é onde os valores
estranhos moram. Por isso a regra de equipe costuma ser simples e sem
exceção: **todo arquivo novo começa com a linha**.
:::

## Union, nullable e o `mixed` que é uma desistência

Um parâmetro pode aceitar mais de um tipo:

```php
function soma(int|float $a, int|float $b): int|float
{
    return $a + $b;
}
```

E pode aceitar a ausência de valor:

```php
function buscarLeitor(int $id): ?Leitor
```

`?Leitor` é abreviação de `Leitor|null`. As duas formas são a mesma coisa;
a segunda é a que você escreve quando há mais tipos na lista.

Existe também o `mixed`, que aceita qualquer coisa:

```php
function processar(mixed $dado): mixed
```

Isso não é um tipo. É uma anotação dizendo que ninguém decidiu, e ela custa
duas vezes: o PHP não confere nada, e quem lê a função não fica sabendo de
nada.

:::key
`?Tipo` é honesto quando o `null` **significa** alguma coisa — "não
encontrei", "ainda não foi devolvido". Uma data de devolução nula é um
empréstimo em aberto, e isso é informação.

`?Tipo` é preguiça quando o `null` é só um jeito de não decidir o que
acontece no caso ruim. O sintoma aparece três linhas depois de cada
chamada, sempre igual: um `if ($x === null)` que ninguém sabe o que deveria
fazer.
:::

## Tipos de retorno

| Escreve | Quer dizer |
|---|---|
| `: void` | não devolve nada; `return;` sozinho é permitido |
| `: never` | não devolve **nunca** — sempre lança ou encerra |
| `: static` | devolve um objeto da mesma classe de quem chamou |

Tabela: `void` e `never` não são sinônimos. Uma função `void` termina; uma
função `never` não termina nunca pelo caminho normal.

```php title="src/Circulacao/Guarda.php" numbered
function recusar(string $motivo): never
{
    throw new \RuntimeException($motivo);
}
```

`never` é uma informação real para quem lê e para as ferramentas: o código
depois da chamada é inalcançável, e um `if/else` em que um dos lados chama
`recusar()` não precisa devolver nada nesse lado.

## O que o PHP não confere

O modo estrito confere o tipo do valor. Ele não confere o que tem dentro
dele.

```php
function totalDeMultas(array $multas): int
```

`array` de quê? Multas? Inteiros? Linhas do banco? O PHP aceita qualquer
array, inclusive um vazio, um de strings e um com três `null` dentro. A
anotação passou a impressão de rigor e não conferiu quase nada.

A saída é anotar o conteúdo num comentário que as ferramentas leem:

```php title="src/Emprestimos/Caixa.php" numbered
/**
 * @param list<Multa> $multas
 */
function totalDeMultas(array $multas): int
{
    $total = 0;

    foreach ($multas as $multa) {
        $total += $multa->centavos();
    }

    return $total;
}
```

`list<Multa>` quer dizer: um array de índices sequenciais em que todo valor
é uma `Multa`. O PHP ignora esse comentário. A ferramenta da próxima seção,
não — e é ela que passa a recusar a chamada com o array errado.

## PHPStan: o erro que aparece antes de rodar

```text
$ composer require --dev phpstan/phpstan
```

```neon title="phpstan.neon"
parameters:
    level: 5
    paths:
        - src
```

```text
$ vendor/bin/phpstan analyse
```

```text
 ------ -------------------------------------------------------------
  Line   src/Emprestimos/Caixa.php
 ------ -------------------------------------------------------------
  18     Parameter #1 $multas of function totalDeMultas expects
         list<CasaAmarela\Emprestimos\Multa>, list<string> given.
 ------ -------------------------------------------------------------

 [ERROR] Found 1 error
```

O programa não rodou. Ninguém abriu a tela, ninguém criou dado de teste, e
mesmo assim o erro tem arquivo, linha e a diferença exata entre o que a
função pede e o que a chamada entrega.

:::term Análise estática
Ler o código sem executá-lo, para deduzir o que pode acontecer. É o mesmo
trabalho que você faz ao revisar um *pull request* — com a diferença de que
a ferramenta lê os catorze mil arquivos toda vez e não fica com sono.
:::

Os níveis vão de 0 a 10, e cada um liga uma família de conferências:

| Nível | Passa a cobrar |
|---|---|
| 0 | classe, função e método que não existem |
| 3 | tipo de retorno e atribuição de propriedade |
| 5 | tipo dos argumentos nas chamadas |
| 6 | anotação de conteúdo ausente em `array` |
| 8 | chamada de método em coisa que pode ser `null` |

Tabela: Comece em 0 num projeto existente e suba um nível por vez. Começar
em 9 produz um relatório que ninguém lê.

## Tipar legado sem parar a empresa

Os 1.247 erros do Sistema não vão ser corrigidos nesta sprint, nem na
próxima. E deixar a ferramenta vermelha é o mesmo que não tê-la: em duas
semanas ninguém olha mais.

O mecanismo que resolve isso se chama **baseline**:

```text
$ vendor/bin/phpstan analyse --generate-baseline
```

```neon title="phpstan.neon"
includes:
    - phpstan-baseline.neon

parameters:
    level: 5
    paths:
        - src
```

O arquivo gerado é uma lista dos erros que existem hoje, com o pedido de
ignorá-los. A partir dele, a ferramenta volta a ficar verde — e passa a
reclamar **só do que for novo**.

O efeito na prática é o que faz a técnica valer: a dívida para de crescer no
dia em que você liga, sem que ninguém precise aprovar um mês de refatoração.
O código antigo vai saindo da lista quando alguém mexer nele por outro
motivo.

:::pitfall
Um baseline sem data de validade vira tapete. O acordo que costuma segurar é
numérico e público: a lista não pode crescer, e cada correção real sai dela
para sempre.

Quando o número não cai por três meses seguidos, ele não está medindo dívida
técnica — está medindo prioridade. E isso também é informação útil para
levar à reunião de terça.
:::

:::note Na sua carreira
A análise estática muda o que você consegue prometer. "Isso não quebra em
nenhum outro lugar" é uma frase que ninguém deveria dizer sobre um sistema
de catorze mil linhas — a não ser que uma ferramenta tenha conferido os
catorze mil.

É também a resposta mais forte para a pergunta que você vai ouvir ao propor
tipos: *"e o que a gente ganha com isso?"*. A resposta não é "código mais
bonito". É: o erro que hoje aparece na terça de manhã, na tela da Vera,
passa a aparecer na sua máquina, antes do commit, com a linha exata.
:::

:::tree title="Onde estamos agora"
acervo/
  composer.json      # phpstan em require-dev
  phpstan.neon       # nível 5, paths: src
  phpstan-baseline.neon
  src/               # todo arquivo com declare(strict_types=1)
    Acervo/
    Circulacao/
    Emprestimos/
    Leitores/
:::

:::summary
- `declare(strict_types=1)` é a primeira instrução do arquivo e desliga a
  conversão automática nas chamadas.
- Ela vale para as chamadas **escritas naquele arquivo**, não para a função
  declarada nele.
- `int` para `float` continua passando; o contrário, não.
- `?Tipo` é `Tipo|null`; use quando o `null` significa algo, não para adiar
  a decisão.
- `mixed` não é tipo: é a anotação de quem não decidiu.
- `void` termina, `never` não termina pelo caminho normal.
- `array` não diz nada sobre o conteúdo; `@param list<Multa>` diz, e a
  ferramenta lê.
- PHPStan encontra o erro antes de rodar; comece no nível 0 e suba.
- Baseline congela a dívida existente e faz a ferramenta cobrar só o que é
  novo.
:::

:::checkpoint
Você liga o modo estrito no lugar certo, explica por que a declaração num
arquivo não protege as chamadas feitas em outro, escolhe entre `?Tipo` e
decidir, anota o conteúdo de um `array` e roda análise estática com baseline
num projeto que tem mil erros.
:::

:::exercise level=1
Diga o que cada chamada faz, considerando que o arquivo que as escreve tem
`declare(strict_types=1)` e a função é `function prazo(int $dias): int`.

1. `prazo(14)`
2. `prazo('14')`
3. `prazo(14.0)`
4. `prazo(true)`
5. `prazo(null)`

Depois responda o que muda nas cinco se a linha do `strict_types` for
apagada.

:::answer
Com o modo estrito:

1. passa.
2. `TypeError` — string não vira int.
3. `TypeError` — float não vira int, nem quando é redondo.
4. `TypeError` — booleano não vira int.
5. `TypeError` — o parâmetro não é `?int`.

Sem a linha, as quatro primeiras passam: `'14'` vira `14`, `14.0` vira `14`,
`true` vira `1`. A quinta continua dando `TypeError`, porque `null` só é
aceito quando o tipo diz que aceita.

O caso 4 é o que costuma assustar mais: `prazo(true)` devolvendo um prazo de
um dia é o tipo de defeito que nunca aparece no caminho feliz e aparece no
dia em que uma variável de configuração vira booleana por engano.
:::

:::exercise level=2
Esta função existe no Sistema e o PHPStan reclama dela em três níveis
diferentes. Tipe-a inteira, incluindo o conteúdo dos arrays, e explique cada
decisão.

```php
function atrasados($emprestimos, $hoje = null)
{
    $fora = [];

    foreach ($emprestimos as $e) {
        if ($e['devolvido_em'] == null
            && $e['devolver_ate'] < $hoje) {
            $fora[] = $e;
        }
    }

    return $fora;
}
```

:::answer
```php title="src/Emprestimos/consultas.php" numbered
<?php

declare(strict_types=1);

/**
 * @param list<Emprestimo> $emprestimos
 * @return list<Emprestimo>
 */
function atrasados(
    array $emprestimos,
    \DateTimeImmutable $hoje,
): array
{
    $fora = [];

    foreach ($emprestimos as $emprestimo) {
        if ($emprestimo->emAberto()
            && $emprestimo->venceuAte($hoje)) {
            $fora[] = $emprestimo;
        }
    }

    return $fora;
}
```

**Os arrays viraram objetos.** `$e['devolvido_em']` é uma chave que pode
estar escrita errada e ninguém avisa; `$emprestimo->emAberto()` é um método
que existe ou não compila. Essa é a troca do capítulo
@cap:classes-e-objetos, agora cobrada pela ferramenta.

**O `$hoje` perdeu o valor padrão `null`.** Um parâmetro que aceita `null` e
é comparado com `<` esconde o caso em que ele chega nulo — e a comparação
com `null` é sempre falsa, então a função devolveria uma lista vazia sem
reclamar. Quem chama passa a data; a função não inventa.

**As comparações viraram métodos.** `== null` ficou `emAberto()`, e a
comparação de datas ficou `venceuAte()`. Além de dizer o que significam, os
dois tiram do caminho a comparação frouxa e a comparação de datas como
texto.

**O retorno ganhou `list<Emprestimo>`.** Sem isso, o PHPStan aceita que
alguém passe o resultado para uma função que espera outra coisa.
:::

:::exercise level=3
Você entra num projeto de 40 mil linhas sem nenhum tipo, sem testes, em
produção, com dois desenvolvedores e um *roadmap* cheio.

Escreva o plano de introdução de tipagem e análise estática em quatro
passos, cada um com o que você faria e o que responderia se a gerência
perguntasse "quanto tempo isso vai tomar do prazo".

:::answer
**Passo 1 — instalar e congelar.** PHPStan em `require-dev`, nível 0,
baseline gerado no mesmo dia. Custo: uma tarde. Resposta à gerência: nenhum
tempo do prazo, e a partir de hoje código novo com erro de tipo não entra.

**Passo 2 — regra de arquivo novo.** Todo arquivo criado nasce com
`declare(strict_types=1)` e com tipos em tudo. Custo: zero, porque é como
escrever o arquivo de qualquer jeito. Resposta: isso não é um projeto, é uma
convenção — como indentação.

**Passo 3 — subir um nível por trimestre.** Cada subida gera erros novos;
eles entram no baseline e saem de lá conforme o código é tocado. Custo: uma
tarde por trimestre para subir e regenerar. Resposta: o número de erros
congelados é público, e a gente vai olhar para ele na retrospectiva.

**Passo 4 — regra de toque.** Arquivo que alguém abrir por qualquer motivo
sai do baseline antes de ser fechado. Custo: diluído em trabalho que já
estava acontecendo. Resposta: não vai tomar tempo do prazo; vai tomar uns
vinte minutos de cada tarefa que já ia acontecer.

O que **não** entra no plano, e vale dizer por quê: uma tarefa chamada
"tipar o sistema". Ela nunca é priorizada, e quando é aprovada vira um mês
de alterações sem teste nenhum num sistema em produção — que é a forma mais
cara possível de introduzir tipos.
:::
