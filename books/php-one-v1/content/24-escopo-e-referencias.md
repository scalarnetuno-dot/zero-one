---
title: "Escopo e referências"
number: 24
slug: escopo-e-referencias
part: p5
kicker: "A lista de devoluções do dia tinha Dom Casmurro duas vezes. Iracema, que tinha voltado às dez, não estava nela."
goal: >-
  Saber exatamente o que uma função recebe quando você passa uma variável,
  um array e um objeto; usar referência só quando ela é a resposta; e
  reconhecer os dois defeitos que o & deixa para trás.
---

:::story Dom Casmurro duas vezes
A Vera imprimiu a lista de devoluções do dia às cinco e meia, como fazia
toda tarde, e foi conferindo com a pilha no carrinho.

— Dom Casmurro aparece duas vezes — disse ela. — E a Iracema não aparece.
Eu recebi a Iracema às dez.

Tainá abriu o script que gerava a lista. Era dela, de terça.

```php
foreach ($devolvidos as &$d) {
    $d['titulo'] = mb_strtoupper($d['titulo']);
}

foreach ($devolvidos as $d) {
    echo $d['titulo'], "\n";
}
```

— Eu só pus em maiúsculas — disse ela. — O segundo laço só imprime.

Dedé olhou o `&` do primeiro laço por um tempo.

— O segundo laço não só imprime.

— Ele não tem `&`.

— Ele não. O primeiro deixou um aberto.
:::

## Escopo, de novo, com mais cuidado

O capítulo @cap:funcoes mostrou a regra: uma função não enxerga as
variáveis de fora, e as de dentro morrem quando ela termina. Quem quer um
valor de fora recebe por parâmetro; quem quer devolver, devolve com
`return`.

Essa regra tem uma pergunta escondida, que o PHP responde de três jeitos
diferentes conforme o tipo do valor: **o que exatamente a função recebe?**
Uma cópia do valor, ou o próprio valor que estava do lado de fora?

A resposta curta:

| Você passa | A função recebe | Alterar lá dentro muda o de fora? |
|---|---|---|
| `int`, `string`, `bool`, `float` | uma cópia | não |
| array | uma cópia | não |
| objeto | o mesmo objeto | **sim** |
| qualquer coisa com `&` | a própria variável | sim |

Tabela: A terceira linha é a que surpreende quem vem do capítulo de
arrays. A quarta é a que este capítulo pede para usar pouco.

O resto do capítulo é essa tabela, uma linha por vez.

## Valores e arrays: a cópia

```php title="copia.php" numbered
<?php

declare(strict_types=1);

function aplicarDesconto(array $emprestimo): array
{
    $emprestimo['multa'] = intdiv($emprestimo['multa'], 2);
    return $emprestimo;
}

$e = ['leitor' => 47, 'multa' => 720];
$comDesconto = aplicarDesconto($e);

echo $e['multa'], "\n";
echo $comDesconto['multa'], "\n";
```

```text
$ php copia.php
720
360
```

A função recebeu uma cópia do array, alterou a cópia e a devolveu. O `$e`
de fora continua com 720. É o comportamento do capítulo @cap:arrays: um
array atribuído a outra variável — ou passado a uma função — é copiado.

Copiar oito mil exemplares a cada chamada parece caro, e não é. O PHP só
copia de verdade **no momento em que alguém escreve** na cópia. Enquanto a
função só lê, as duas variáveis apontam para os mesmos dados na memória. O
nome disso é *copy-on-write*, e é a razão de passar array por valor ser o
padrão seguro e barato.

## A referência: `&`

Um `&` antes do parâmetro muda o acordo. A função passa a receber a
**própria variável** de quem chamou:

```php title="referencia.php" numbered
<?php

declare(strict_types=1);

function aplicarDesconto(array &$emprestimo): void
{
    $emprestimo['multa'] = intdiv($emprestimo['multa'], 2);
}

$e = ['leitor' => 47, 'multa' => 720];
aplicarDesconto($e);

echo $e['multa'], "\n";
```

```text
$ php referencia.php
360
```

Não há `return`. A função mudou o `$e` de fora diretamente.

:::term Referência
Um segundo nome para a mesma variável. Com `&`, o parâmetro da função e a
variável de quem chamou deixam de ser duas coisas: mudar uma é mudar a
outra.

O PHP usa referência em pouquíssimas funções da própria biblioteca — `sort`
é a mais conhecida: ela ordena o array que você passou, no lugar, e devolve
só `true`.
:::

As duas versões fazem a mesma conta. A primeira diz, na assinatura, que
devolve um array novo. A segunda diz que muda o que recebeu — e quem lê a
chamada `aplicarDesconto($e);`, sem nada à esquerda, precisa abrir a
função para saber que o `$e` mudou.

:::key
Referência troca uma linha a menos por uma pergunta a mais em cada
chamada. O padrão deste livro — e do Laravel — é receber, calcular e
devolver. `&` fica para o caso raro em que devolver não serve.
:::

## O `&` que fica aberto

O defeito da lista da Vera tem uma causa só, e ela explica por que a regra
acima é regra.

```php title="devolucoes.php" numbered
<?php

declare(strict_types=1);

$devolvidos = [
    ['titulo' => 'O Cortiço'],
    ['titulo' => 'Dom Casmurro'],
    ['titulo' => 'Iracema'],
];

foreach ($devolvidos as &$d) {
    $d['titulo'] = mb_strtoupper($d['titulo']);
}

foreach ($devolvidos as $d) {
    echo $d['titulo'], "\n";
}
```

```text
$ php devolucoes.php
O CORTIÇO
DOM CASMURRO
DOM CASMURRO
```

O primeiro laço, com `&$d`, faz de `$d` um segundo nome para cada item, um
de cada vez. Quando ele termina, `$d` **continua** sendo o segundo nome do
último item — o da Iracema. A referência não se desfaz com o fim do laço.

O segundo laço usa o mesmo nome, `$d`, sem `&`. A cada volta ele **atribui**
o item atual a `$d`. Mas `$d` é a Iracema. Na primeira volta, a Iracema vira
O Cortiço. Na segunda, vira Dom Casmurro. Na terceira, o laço lê a posição
da Iracema — que agora é Dom Casmurro — e a escreve nela mesma.

A lista não perdeu um livro por um erro de digitação. Perdeu porque uma
variável continuou sendo apelido de outra depois que ninguém mais lembrava
disso.

A correção mínima é desfazer a referência assim que o laço termina:

```php
foreach ($devolvidos as &$d) {
    $d['titulo'] = mb_strtoupper($d['titulo']);
}
unset($d);
```

`unset($d)` apaga o nome `$d`, e com ele o apelido. O item da Iracema não é
tocado.

A correção que este livro prefere não usa `&`:

```php
$devolvidos = array_map(
    fn(array $d): array => [
        ...$d,
        'titulo' => mb_strtoupper($d['titulo']),
    ],
    $devolvidos,
);
```

O `array_map` do capítulo @cap:funcoes devolve um array novo. Não sobra
apelido nenhum para o próximo laço tropeçar.

:::pitfall
O defeito só aparece quando o **mesmo nome** é reusado depois, no mesmo
escopo. Por isso ele passa em todo teste que roda o primeiro laço sozinho,
e aparece no dia em que alguém acrescenta, trinta linhas abaixo, um
`foreach` inocente com o nome que estava sobrando.

O PHPStan do capítulo @cap:tipagem-estrita não acusa. A regra da casa
acusa: `foreach` com `&` termina com `unset`, sempre, na linha seguinte ao
fechamento.
:::

## Objetos: o mesmo objeto

Agora a linha da tabela que muda tudo o que vem no volume 2.

```php title="objeto.php" numbered
<?php

declare(strict_types=1);

final class Exemplar
{
    public function __construct(
        public readonly int $tombo,
        public string $estado = 'bom',
    ) {}
}

function marcarEmprestado(Exemplar $e): void
{
    $e->estado = 'emprestado';
}

$ex = new Exemplar(2117);
marcarEmprestado($ex);

echo $ex->estado, "\n";
```

```text
$ php objeto.php
emprestado
```

Não há `&` em lugar nenhum, e o `$ex` de fora mudou.

Um objeto não é copiado quando é passado a uma função, nem quando é
atribuído a outra variável. O que a variável guarda é uma **identificação**
do objeto — um número que diz ao PHP onde ele está. Passar `$ex` para a
função passa uma cópia desse número, e a cópia aponta para o mesmo objeto.

```php
$a = new Exemplar(2117);
$b = $a;
$b->estado = 'restauro';

echo $a->estado;   // restauro
var_dump($a === $b);   // bool(true)
```

`$a === $b` entre objetos pergunta se é **o mesmo** objeto — a comparação
do capítulo @cap:classes-e-objetos. Aqui é: há um objeto, com dois nomes.

:::key
Array passado é copiado; objeto passado é compartilhado. Uma função que
recebe um objeto e muda uma propriedade dele muda o objeto de quem chamou,
sem `&` e sem `return`.

No volume 2, isso é o dia a dia: o Laravel entrega ao seu código o objeto
da requisição, o model do banco, o usuário autenticado. Todos são objetos,
e todos são o mesmo objeto que o framework e as outras partes do seu código
estão segurando.
:::

É também a razão do `readonly` do capítulo @cap:encapsulamento. Um objeto
compartilhado que ninguém pode mudar por fora — como o `Dinheiro` do
capítulo @cap:enums-datas-e-valores — não tem esse problema: qualquer
"alteração" devolve um objeto novo.

## `clone`, e a cópia que só vai um nível

Quando é preciso mesmo uma cópia independente de um objeto, existe
`clone`:

```php title="clone.php" numbered
<?php

declare(strict_types=1);

final class Leitor
{
    public function __construct(public string $nome) {}
}

final class Emprestimo
{
    public function __construct(
        public Leitor $leitor,
        public int $dias,
    ) {}
}

$original = new Emprestimo(new Leitor('Marlene'), 14);
$copia = clone $original;

$copia->dias = 7;
$copia->leitor->nome = 'Iolanda';

echo $original->dias, ' ', $original->leitor->nome, "\n";
```

```text
$ php clone.php
14 Iolanda
```

O `dias` foi copiado: mudar na cópia não mudou o original. O `leitor` não:
`clone` copia as propriedades, e a propriedade `leitor` guarda a
identificação de um objeto. A cópia recebeu a mesma identificação — e, com
ela, o mesmo leitor.

Para descer um nível, a classe declara o que o `clone` deve fazer:

```php
public function __clone(): void
{
    $this->leitor = clone $this->leitor;
}
```

`__clone` roda na cópia, logo depois de ela ser feita. Na prática, este
livro quase não usa `clone`: objetos de valor imutáveis, que devolvem outro
objeto a cada mudança, dispensam a pergunta.

## `static` e `global`: o escopo que dura demais

Existem dois jeitos de uma variável sobreviver ao fim da função, e o
capítulo @cap:encapsulamento já avisou sobre um deles.

`global` puxa uma variável do arquivo para dentro da função:

```php
function totalizar(int $valor): void
{
    global $total;
    $total += $valor;
}
```

A função passa a depender de um nome que não aparece na assinatura, e
qualquer outro arquivo pode mudá-lo. É o `$total_geral` do capítulo
@cap:funcoes, "consertado" do jeito errado.

`static` dentro de uma função guarda o valor entre uma chamada e outra:

```php title="cache.php" numbered
<?php

declare(strict_types=1);

function multaDiaria(): int
{
    static $valor = null;

    if ($valor === null) {
        echo "(lendo config)\n";
        $valor = 80;
    }

    return $valor;
}

echo multaDiaria(), "\n";
echo multaDiaria(), "\n";
```

```text
$ php cache.php
(lendo config)
80
80
```

A segunda chamada não leu a configuração. Útil para um valor caro de
calcular que nunca muda durante o programa — e perigoso para qualquer coisa
que mude, porque não há como avisar a função de que o valor guardado ficou
velho.

:::note
No PHP que atende o navegador, cada requisição começa do zero: `static` e
`global` morrem no fim dela. No volume 2 aparecem processos que **não**
terminam — o worker de fila, por exemplo —, e ali um `static` guardado na
primeira tarefa continua lá na milésima. O que parece inofensivo numa
requisição vira um dado de uma pessoa aparecendo para outra.
:::

:::note Na sua carreira
"O PHP passa objeto por referência" é uma frase que você vai ouvir em
entrevista e ler em tutorial. É quase certa, e o quase importa: o PHP passa
a **identificação** do objeto por valor. A diferença aparece num caso só —
reatribuir o parâmetro dentro da função (`$e = new Exemplar(9)`) não muda a
variável de fora; com `&`, mudaria.

Saber explicar esse caso em uma frase é o tipo de detalhe que separa quem
decorou de quem entendeu.
:::

:::tree title="Onde estamos agora"
acervo/
  src/
    Acervo/Exemplar.php      # estado muda por método, não por fora
    Emprestimos/Dinheiro.php # imutável: nada a clonar
  scripts/
    devolucoes.php           # array_map no lugar do foreach com &
:::

:::summary
- Escalares e arrays são passados por cópia; objetos, pela identificação —
  a função recebe o mesmo objeto.
- Copiar array é barato: o PHP só copia de verdade quando alguém escreve.
- `&` faz do parâmetro um segundo nome para a variável de fora. Use pouco.
- `foreach` com `&` deixa o apelido vivo depois do laço; `unset` na linha
  seguinte, ou `array_map` no lugar.
- `clone` copia um nível; objetos dentro continuam compartilhados.
  `__clone` desce mais um.
- `global` e `static` fazem a variável durar mais que a função. Em processo
  que não termina, duram demais.
:::

:::checkpoint
Você prevê, olhando a assinatura, se uma função pode alterar o que
recebeu; reproduz e corrige o `foreach` com `&` que duplica o último item;
e explica por que um objeto passado a uma função volta alterado sem `&`.
:::

:::exercise level=1
Diga o que cada trecho imprime:

```php
function a(int $x): void { $x = 10; }
$n = 1; a($n); echo $n;

function b(array $l): void { $l[] = 'novo'; }
$lista = []; b($lista); echo count($lista);

function c(Exemplar $e): void { $e->estado = 'restauro'; }
$ex = new Exemplar(1); c($ex); echo $ex->estado;
```

:::answer
`1`, `0` e `restauro`.

Inteiro e array são copiados: as funções `a` e `b` mudaram as cópias. O
objeto não é copiado: `c` mudou o mesmo exemplar que `$ex` identifica.
:::

:::exercise level=2
Este trecho da importação soma a multa de cada leitor. Diga o que ele
imprime, por que, e reescreva sem `&`.

```php
$leitores = [
    ['nome' => 'A', 'multa' => 100],
    ['nome' => 'B', 'multa' => 200],
];

foreach ($leitores as &$l) {
    $l['multa'] += 50;
}

$total = 0;
foreach ($leitores as $l) {
    $total += $l['multa'];
}
echo $total;
```

:::answer
Imprime `300`, e o certo seria `400`.

O primeiro laço soma 50 a cada leitor — A fica com 150, B com 250 — e
deixa `$l` como apelido do último item, o B. O segundo laço atribui cada
item a `$l`. Na primeira volta, o B vira uma cópia do A: multa 150. Na
segunda, o laço lê o B, que agora vale 150. O total sai `150 + 150`, e o
array termina com os dois leitores com multa de 150. A multa do B, 250,
sumiu sem erro nenhum.

```php
$leitores = array_map(
    fn(array $l): array => [...$l, 'multa' => $l['multa'] + 50],
    $leitores,
);
$total = array_sum(array_column($leitores, 'multa'));
```

`array_sum(array_column(...))` soma a coluna `multa` de todos: 400. Sem
apelido, sem ordem de laço para importar.
:::

:::exercise level=3
Um colega escreveu, no service de empréstimo:

```php
function renovar(Emprestimo $e, int $dias): Emprestimo
{
    $novo = $e;
    $novo->dias += $dias;
    return $novo;
}
```

Ele diz que a função "não altera o original, porque devolve um novo".
Explique o que acontece, e escreva duas versões corretas — uma com `clone`
e uma imutável.

:::answer
`$novo = $e` não cria outro objeto: cria outro nome para o mesmo. A função
altera o empréstimo recebido **e** devolve esse mesmo empréstimo. Quem
chamou e guardou o original para comparar "antes e depois" vê os dois
iguais.

Com `clone`:

```php
function renovar(Emprestimo $e, int $dias): Emprestimo
{
    $novo = clone $e;
    $novo->dias += $dias;
    return $novo;
}
```

Imutável, com a classe desenhada para isso:

```php
final class Emprestimo
{
    public function __construct(
        public readonly Leitor $leitor,
        public readonly int $dias,
    ) {}

    public function renovadoPor(int $dias): self
    {
        return new self($this->leitor, $this->dias + $dias);
    }
}
```

A segunda torna o defeito impossível: não há como alterar um `readonly`, e
o nome do método diz que volta outro empréstimo.
:::
