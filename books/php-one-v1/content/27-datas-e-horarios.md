---
title: "Datas e horários"
number: 27
slug: datas-e-horarios
part: p5
kicker: "O defeito do domingo tinha quatro anos. O conserto tinha nove linhas. O teste do conserto falhava depois das nove da noite."
goal: >-
  Calcular prazo que não cai em dia fechado, contar dias de atraso sem
  errar por causa da hora, tratar "agora" como uma dependência que se passa
  e se troca no teste, fazer conta com mês sem cair no dia 31, e ler a data
  que uma pessoa digita.
---

:::story O defeito do domingo
Na primeira semana do projeto, a Vera tinha listado os defeitos do Sistema
sem tirar os olhos da etiqueta que colava: "quando alguém devolve no
domingo, ele cobra multa, e domingo a gente nem abre". Há quatro anos.

A Tainá puxou o defeito para si.

— O prazo são catorze dias — explicou a Vera. — Se o décimo quarto cai no
domingo, a pessoa só pode devolver na segunda. E o Sistema cobra a segunda.
Um dia de multa, toda vez. Eu devolvo o dinheiro do meu bolso quando
reclamam.

— Do seu bolso?

— É mais rápido que explicar.

A Tainá escreveu a correção, escreveu o teste, e o teste passou. Às dez e
meia da noite, rodando tudo de novo antes de abrir o pedido de revisão, o
mesmo teste falhou.

```text
Empréstimo com prazo hoje não deveria estar atrasado.
Esperado: false. Obtido: true.
```

Ela rodou outra vez. Falhou. Na manhã seguinte, passou.

— Eu não mexi em nada — disse ela ao Dedé.

— Você não. O relógio mexeu.
:::

## O prazo que não cai em dia fechado

O capítulo @cap:enums-datas-e-valores deixou três regras: data com fuso,
`DateTimeImmutable` sempre, e UTC no banco com conversão na tela. Este
capítulo usa as três e acrescenta o que falta para calcular prazo de
verdade.

A regra da Vera, escrita:

```php title="prazo.php" numbered
<?php

declare(strict_types=1);

const DOMINGO = 7;

function proximoDiaAberto(
    DateTimeImmutable $dia,
    array $feriados,
): DateTimeImmutable {
    while (
        (int) $dia->format('N') === DOMINGO
        || in_array($dia->format('Y-m-d'), $feriados, true)
    ) {
        $dia = $dia->modify('+1 day');
    }
    return $dia;
}

$feriados = ['2026-04-03', '2026-04-21'];
$fuso = new DateTimeZone('America/Sao_Paulo');

foreach (['2026-03-22', '2026-04-03', '2026-04-21'] as $data) {
    $prazo = new DateTimeImmutable($data, $fuso);
    $aberto = proximoDiaAberto($prazo, $feriados);
    echo $prazo->format('D d/m'), ' -> ';
    echo $aberto->format('D d/m'), "\n";
}
```

```text
$ php prazo.php
Sun 22/03 -> Mon 23/03
Fri 03/04 -> Sat 04/04
Tue 21/04 -> Wed 22/04
```

`format('N')` devolve o dia da semana como número, de 1, segunda, a 7,
domingo. O `while`, e não um `if`, é o que trata o feriado que cai no
sábado antes de um domingo: o laço anda até achar um dia aberto, quantos
forem os fechados em seguida.

Os feriados estão num array porque mudam todo ano e cada cidade tem os
seus. No volume 2, eles vão para uma tabela, e a Vera cadastra os do ano
em janeiro.

## Dias de atraso, sem a hora no meio

O prazo é uma **data**: dia 24. A devolução é um **instante**: dia 27, às
9h15. Subtrair um do outro direto mistura as duas coisas, e o resultado
muda com o horário em que o livro chegou ao balcão.

```php title="atraso.php" numbered
<?php

declare(strict_types=1);

function diasDeAtraso(
    DateTimeImmutable $prazo,
    DateTimeImmutable $devolvidoEm,
): int {
    $dia = $devolvidoEm->setTimezone($prazo->getTimezone())
        ->setTime(0, 0);
    $intervalo = $prazo->diff($dia);

    return $intervalo->invert === 1 ? 0 : $intervalo->days;
}

$fuso = new DateTimeZone('America/Sao_Paulo');
$prazo = new DateTimeImmutable('2026-03-24', $fuso);

foreach (['2026-03-20 15:00', '2026-03-24 17:50',
          '2026-03-27 09:15'] as $quando) {
    $devolvido = new DateTimeImmutable($quando, $fuso);
    echo $quando, ': ', diasDeAtraso($prazo, $devolvido), "\n";
}

$utc = new DateTimeImmutable(
    '2026-03-25 01:30',
    new DateTimeZone('UTC'),
);
echo 'utc 25/03 01:30: ', diasDeAtraso($prazo, $utc), "\n";
```

```text
$ php atraso.php
2026-03-20 15:00: 0
2026-03-24 17:50: 0
2026-03-27 09:15: 3
utc 25/03 01:30: 0
```

Três passos, cada um por um motivo.

**`setTimezone` antes de tudo.** A última linha é a mesma devolução que o
banco guardaria em UTC: 1h30 do dia 25 em UTC é 22h30 do dia 24 em São
Paulo. Dentro do prazo. Sem a conversão, seria um dia de multa para quem
devolveu na hora certa.

**`setTime(0, 0)`** apaga a hora e deixa só o dia. É o que faz a devolução
das 17h50 do dia 24 valer "dia 24", e não "dia 24 e dezessete horas
depois do prazo".

**`diff`** devolve um `DateInterval`. `days` é o total de dias entre as duas
datas, sempre positivo; `invert` vale `1` quando a segunda data é
**anterior** à primeira — quando o livro voltou antes do prazo.

:::key
Prazo, aniversário, feriado: **data**. Retirada, devolução, pagamento:
**instante**. Antes de comparar um com o outro, converta o instante para o
fuso da data e jogue fora a hora. A maior parte dos defeitos de "um dia a
mais" em sistema brasileiro nasce de pular um dos dois passos.
:::

## "Agora" é uma dependência

De volta ao teste que falhava de noite. A versão que a Tainá tinha escrito
perguntava ao PHP que dia era:

```php
public function estaAtrasado(): bool
{
    $hoje = new DateTimeImmutable('today');
    return $hoje > $this->devolverAte;
}
```

Dois problemas numa linha.

**O fuso.** `new DateTimeImmutable('today')` sem fuso usa o fuso padrão do
PHP, e no contêiner de testes da Vertexo ele era o de fábrica:

```text
$ php -r 'echo date_default_timezone_get();'
UTC
```

Às 21h em São Paulo, já é meia-noite em UTC. A partir dali, "hoje" para o
PHP é o dia seguinte, e o empréstimo com prazo hoje aparece atrasado. De
manhã, os dois fusos concordam de novo e o teste passa.

**O relógio.** Mesmo com o fuso certo, o teste depende da hora em que roda.
Um teste que dá resultado diferente conforme a hora não prova nada — e o
que diz "hoje" dentro do método não deixa nenhum teste escolher a hora.

A saída é a mesma do capítulo @cap:heranca-interfaces-e-traits para tudo
que vem de fora: uma interface, e quem precisa recebe pelo construtor.

```php title="relogio.php" numbered
<?php

declare(strict_types=1);

interface Relogio
{
    public function agora(): DateTimeImmutable;
}

final class RelogioDoSistema implements Relogio
{
    public function __construct(private DateTimeZone $fuso)
    {
    }

    public function agora(): DateTimeImmutable
    {
        return new DateTimeImmutable('now', $this->fuso);
    }
}

final class RelogioParado implements Relogio
{
    public function __construct(private DateTimeImmutable $instante)
    {
    }

    public function agora(): DateTimeImmutable
    {
        return $this->instante;
    }
}
```

O sistema no ar usa o `RelogioDoSistema`, com o fuso de São Paulo vindo da
configuração. O teste usa o `RelogioParado`, e escolhe a hora:

```php title="relogio.php (continuação)" numbered
final class Emprestimo
{
    public function __construct(
        private DateTimeImmutable $devolverAte,
        private Relogio $relogio,
    ) {
    }

    public function estaAtrasado(): bool
    {
        $hoje = $this->relogio->agora()->setTime(0, 0);
        return $hoje > $this->devolverAte;
    }
}

$fuso = new DateTimeZone('America/Sao_Paulo');
$prazo = new DateTimeImmutable('2026-03-24', $fuso);

$noite = new RelogioParado(
    new DateTimeImmutable('2026-03-24 22:30', $fuso),
);
$depois = new RelogioParado(
    new DateTimeImmutable('2026-03-25 08:00', $fuso),
);

var_dump((new Emprestimo($prazo, $noite))->estaAtrasado());
var_dump((new Emprestimo($prazo, $depois))->estaAtrasado());
```

```text
bool(false)
bool(true)
```

Agora o teste das dez e meia da noite roda às dez e meia da noite de
qualquer dia, inclusive às nove da manhã.

:::term Relógio injetado
"Agora" tratado como dependência: um objeto que responde que horas são,
recebido pelo construtor. No sistema, ele pergunta ao sistema operacional;
no teste, responde sempre o mesmo instante.

A ideia é tão comum que virou padrão da comunidade PHP — a PSR-20, com a
interface `ClockInterface` e um único método, `now()`. É a mesma interface
deste capítulo com os nomes em inglês.
:::

O fuso padrão também tem conserto, na configuração do PHP ou no começo do
programa:

```php
date_default_timezone_set('America/Sao_Paulo');
```

Mas note a ordem: o relógio injetado resolve o problema **com** ou **sem**
essa linha. O fuso padrão é uma rede de segurança; o fuso explícito, no
relógio e nas datas, é a regra.

## Um mês depois do dia 31

A carteirinha da Casa Amarela é renovada todo mês. A Tainá escreveu o
óbvio:

```php
$renovada = new DateTimeImmutable('2026-01-31');
echo $renovada->modify('+1 month')->format('Y-m-d');
```

```text
2026-03-03
```

Não é defeito do PHP. "Um mês depois de 31 de janeiro" seria 31 de
fevereiro, que não existe; o PHP soma os dias que sobram e chega a 3 de
março. Toda linguagem precisa escolher alguma coisa, e o PHP escolheu essa.

Quando a regra é "o último dia do mês seguinte", ela precisa ser dita:

```php
echo $renovada->modify('last day of next month')->format('Y-m-d');
```

```text
2026-02-28
```

:::pitfall
`+1 month` só surpreende do dia 29 em diante — e os testes costumam usar
dia 10. Em qualquer regra com mês, escreva um teste com 31 de janeiro. Se
a regra de negócio não diz o que fazer nesse dia, pergunte à Vera antes de
escolher: é uma decisão dela, não do PHP.
:::

## A data que alguém digitou

No balcão, a Vera digita a data de devolução dos livros que chegaram pela
caixa de coleta no fim de semana: `24/03/2026`. O construtor de
`DateTimeImmutable` não é o lugar certo para isso — ele entende dezenas de
formatos e adivinha os ambíguos. Para texto digitado, diga o formato:

```php title="entrada.php" numbered
<?php

declare(strict_types=1);

function lerDataBr(
    string $texto,
    DateTimeZone $fuso,
): ?DateTimeImmutable {
    $data = DateTimeImmutable::createFromFormat(
        '!d/m/Y',
        $texto,
        $fuso,
    );
    $avisos = DateTimeImmutable::getLastErrors();
    if ($data === false || $avisos !== false) {
        return null;
    }
    return $data;
}

$fuso = new DateTimeZone('America/Sao_Paulo');
$textos = ['24/03/2026', '31/02/2026', '2026-03-24', '24/3/2026'];
foreach ($textos as $t) {
    $d = lerDataBr($t, $fuso);
    $saida = $d?->format('Y-m-d H:i') ?? 'inválida';
    echo str_pad($t, 11), $saida, "\n";
}
```

```text
24/03/2026 2026-03-24 00:00
31/02/2026 inválida
2026-03-24 inválida
24/3/2026  2026-03-24 00:00
```

Dois detalhes que fazem a diferença.

**O `!` no começo do formato** zera tudo que o texto não informa. Sem ele,
a hora que falta vem do relógio: `24/03/2026` vira "24 de março, às
9h55" — a hora em que o script rodou —, e a comparação com o prazo erra
conforme a hora do dia.

**`getLastErrors()`.** `31/02/2026` **não** devolve `false`: o PHP faz a
mesma conta do mês e devolve 3 de março, anotando um aviso. O aviso fica em
`getLastErrors()`, que devolve `false` quando não houve nenhum. Conferir só o
`false` do `createFromFormat` deixaria passar 31 de fevereiro.

`$d?->format(...)` é o operador *nullsafe*: chama o método só se `$d` não
for `null` e, se for, o resultado inteiro vira `null`, sem erro. O `??`
troca esse `null` pelo texto. Juntos, dizem numa linha "formate se existir;
senão, escreva inválida".

:::note Na sua carreira
Datas são a área em que mais código "funciona na minha máquina": a sua
máquina está no fuso de São Paulo, o servidor está em UTC, o teste roda de
manhã, e ninguém trabalha em 31 de janeiro.

Três perguntas fecham a maior parte dos defeitos antes de eles existirem:
**em que fuso** está este instante? isto é **data** ou **instante**? de
onde vem o **agora**? Quando a resposta da terceira for "de dentro da
função", você tem um teste que vai falhar às nove da noite.
:::

## O que o volume 2 faz com data

O Laravel usa uma biblioteca chamada **Carbon**, que estende o
`DateTimeImmutable` com nomes mais curtos: `now()->addDays(14)`,
`$prazo->isSunday()`, `$prazo->diffInDays($devolucao)`. Por baixo, cada
um é uma das chamadas deste capítulo.

O fuso padrão vira uma linha da configuração do projeto. E o relógio
injetado ganha uma forma pronta: nos testes do volume 2, uma chamada
congela o `now()` do framework inteiro num instante escolhido. É o
`RelogioParado`, aplicado a tudo de uma vez.

:::tree title="Onde estamos agora"
acervo/
  src/
    Tempo/
      Relogio.php            # interface: agora()
      RelogioDoSistema.php   # fuso de São Paulo
      RelogioParado.php      # para os testes
    Circulacao/
      CalendarioDaBiblioteca.php   # domingos e feriados
:::

:::summary
- `format('N')` dá o dia da semana (7 é domingo); um `while` pula dias
  fechados em sequência.
- Prazo é data; devolução é instante. Converta o instante para o fuso da
  data, zere a hora e só então compare.
- `diff()` devolve `days` sempre positivo e `invert` para o sentido.
- "Agora" é dependência: receba um `Relogio` pelo construtor. O teste passa
  um relógio parado. A PSR-20 padroniza a ideia.
- `+1 month` de 31 de janeiro é 3 de março. Diga a regra por extenso.
- Data digitada: `createFromFormat` com `!`, e confira `getLastErrors()`.
:::

:::checkpoint
Você calcula um prazo que respeita dias fechados, conta atraso sem errar por
causa da hora ou do fuso, escreve código de data que um teste consegue
rodar em qualquer horário, e valida a data que uma pessoa digitou.
:::

:::exercise level=1
Para cada valor, diga se é **data** ou **instante** e em que coluna do
banco ele iria — `DATE` ou `DATETIME` em UTC:

1. a data de nascimento do leitor;
2. a hora em que o exemplar foi retirado;
3. o prazo de devolução;
4. a hora em que a multa foi paga.

:::answer
1. Data, `DATE`. Ninguém faz aniversário em UTC.
2. Instante, `DATETIME` em UTC.
3. Data, `DATE` — o prazo é o dia inteiro, na cidade da biblioteca.
4. Instante, `DATETIME` em UTC.
:::

:::exercise level=2
Escreva `prazoDeDevolucao(DateTimeImmutable $retirada, int $dias,
array $feriados): DateTimeImmutable`, que soma os dias à data da retirada
— sem a hora — e empurra o resultado para o próximo dia aberto. Teste com
uma retirada no sábado 7 de março de 2026, às 16h, e catorze dias.

:::answer
```php
function prazoDeDevolucao(
    DateTimeImmutable $retirada,
    int $dias,
    array $feriados,
): DateTimeImmutable {
    $prazo = $retirada->setTime(0, 0)->modify("+{$dias} days");
    return proximoDiaAberto($prazo, $feriados);
}
```

Sábado, 7 de março, mais catorze dias é sábado, 21 de março — aberto, e o
prazo fica ali. Com quinze dias, cairia no domingo 22 e iria para a
segunda, 23.

O `setTime(0, 0)` vem antes da soma para o prazo ser uma data, e não "dia
21 às 16h". Sem isso, a comparação do `estaAtrasado` passaria a depender
da hora da retirada.
:::

:::exercise level=3
O relatório de atrasados roda à 1h da manhã, pelo agendador, num servidor
em UTC. Ele usa `new DateTimeImmutable('today')` para saber que dia é, e
lista os empréstimos com prazo anterior a hoje. A Vera reclama que, toda
manhã, a lista traz gente que ainda está no prazo. Explique o defeito com
horários e datas concretos, e escreva a correção.

:::answer
À 1h da manhã em UTC, em São Paulo são 22h **do dia anterior**. Na
madrugada de 25 de março, UTC, o `today` do servidor é 25; em São Paulo,
ainda é 24. Todo empréstimo com prazo no dia 24 entra na lista como
atrasado, embora o dia 24 ainda não tenha acabado na cidade da
biblioteca.

A correção é não perguntar ao servidor que dia é:

```php
$hoje = $relogio->agora()->setTime(0, 0);
```

com `$relogio` sendo um `RelogioDoSistema` criado com o fuso de São Paulo.
O teste do relatório passa um `RelogioParado` em `2026-03-25 01:00` UTC e
confere que o prazo do dia 24 **não** está na lista.

A outra metade da correção é de conversa, não de código: perguntar à Vera
se o relatório deveria rodar às 7h de São Paulo, que é quando ela o lê.
:::
