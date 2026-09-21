---
title: "Enums, datas e objetos de valor"
number: 23
slug: enums-datas-e-valores
part: p4
kicker: "A Vera ficou até as onze fechando o inventário. Sete leitores acordaram devendo oitenta centavos."
goal: >-
  Fechar conjuntos de opções com `enum`, guardar data com fuso e sem
  surpresa usando `DateTimeImmutable`, e dar a dinheiro um tipo com regra
  própria em vez de um inteiro solto.
---

:::story Onze da noite de terça
O inventário de fevereiro atrasou, e a Vera ficou até as onze registrando a
pilha de devoluções que tinha se acumulado no balcão.

Na quinta, sete leitores receberam aviso de multa de oitenta centavos.

— Eles devolveram no prazo — disse Vera. — Eu registrei tudo na terça.

Dedé abriu a tabela.

```text
mysql> SELECT id, devolver_ate, devolvido_em FROM emprestimos
    ->  WHERE id IN (4471, 4472, 4473);
+------+--------------+---------------------+
| id   | devolver_ate | devolvido_em        |
+------+--------------+---------------------+
| 4471 | 2026-03-10   | 2026-03-11 02:03:11 |
| 4472 | 2026-03-10   | 2026-03-11 02:03:47 |
| 4473 | 2026-03-10   | 2026-03-11 02:04:12 |
+------+--------------+---------------------+
```

— Duas da manhã? Eu fui embora às onze.

— O servidor acha que são duas.

— O servidor está onde?

Dedé conferiu a configuração da hospedagem antes de responder, o que foi
uma boa ideia.

— Na Virgínia.
:::

## String solta é um `if` esperando erro de digitação

O `Exemplar` do projeto guarda o estado assim:

```php
private string $estado = 'bom';
```

O construtor confere a lista, e isso resolve o nascimento. Mas dentro da
classe, e em qualquer lugar que receba esse valor, `'bom'` é apenas uma
string entre todas as strings possíveis:

```php
if ($exemplar->estado() === 'emprestad') {
```

O PHP aceita. O tipo está certo — é uma string. A condição nunca é
verdadeira, o bloco nunca roda, e nada reclama nunca.

Este é o buraco que sobrou depois de três capítulos fechando buracos: o tipo
`string` diz o formato e não diz o **conjunto**.

## `enum`: o conjunto vira tipo

```php title="src/Acervo/StatusExemplar.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Acervo;

enum StatusExemplar: string
{
    case Bom = 'bom';
    case Emprestado = 'emprestado';
    case Restauro = 'restauro';
    case Extraviado = 'extraviado';
}
```

Cada `case` é um valor, e só existem quatro. Não há um quinto, não há como
inventar um, e o erro de digitação deixa de compilar:

```php
if ($exemplar->status() === StatusExemplar::Emprestad) {
```

```text
Fatal error: Undefined constant StatusExemplar::Emprestad
```

O `: string` depois do nome faz dele um **enum com valor atrelado**: cada
caso carrega um texto, que é o que vai para o banco.

| | Quando usar |
|---|---|
| `enum Status` (puro) | o conjunto só existe dentro do programa |
| `enum Status: string` | o valor precisa ser guardado ou transmitido |

Tabela: Na dúvida, atrelado. Um enum puro que um dia precisa ir ao banco
obriga a inventar a conversão na mão, e é aí que alguém guarda o nome do
caso em vez do valor.

Três operações cobrem o uso diário:

```php
$status = StatusExemplar::from('restauro');
echo $status->name, ' / ', $status->value, "\n";
```

```text
Restauro / restauro
```

`name` é o nome do caso no código; `value` é o texto atrelado. Os dois
existem, e confundir os dois é o erro da próxima seção.

```php
var_dump(StatusExemplar::tryFrom('emprestadoo'));
```

```text
NULL
```

```php
StatusExemplar::from('emprestadoo');
```

```text
Fatal error: Uncaught ValueError: "emprestadoo" is not a valid backing
value for enum StatusExemplar
```

:::key
`from()` quando o valor **tem** que ser válido — veio da sua própria tabela,
e se não for válido o banco está corrompido e você quer saber agora.

`tryFrom()` quando o valor veio de fora — formulário, parâmetro de busca,
arquivo da editora. Aí `null` é uma resposta possível, e o lugar de tratar é
a validação da entrada.

Trocar os dois de lugar é o defeito mais comum com enums: `from()` num
parâmetro de URL transforma um usuário curioso num erro fatal.
:::

E `cases()` devolve todos, na ordem em que foram escritos — é o que monta um
`<select>` sem ninguém repetir a lista no HTML:

```php
foreach (StatusExemplar::cases() as $caso) {
    echo $caso->value, "\n";
}
```

## Comportamento junto da opção

Um enum não é só uma lista. Ele aceita métodos:

```php title="src/Acervo/StatusExemplar.php" numbered
    public function disponivel(): bool
    {
        return $this === self::Bom;
    }

    public function rotulo(): string
    {
        return match ($this) {
            self::Bom => 'Disponível',
            self::Emprestado => 'Emprestado',
            self::Restauro => 'Em restauro',
            self::Extraviado => 'Extraviado',
        };
    }
```

```php
echo StatusExemplar::Restauro->rotulo(), "\n";
```

```text
Em restauro
```

O `match` aqui faz um trabalho que o `if` não faz: se alguém acrescentar um
quinto caso ao enum e esquecer do `rotulo()`, a chamada com esse caso lança
`UnhandledMatchError` na hora. O `if/else` devolveria a última opção em
silêncio.

:::key
Comparar enum é com `===`, e funciona porque cada caso é um objeto único:
existe **uma** `StatusExemplar::Bom` no programa inteiro, e todas as
variáveis que a contêm apontam para ela.

É a mesma identidade que atrapalhava ao comparar dois `Leitor` carregados do
banco, agora trabalhando a favor.
:::

## O enum no banco

A gravação usa `value`; a leitura usa `tryFrom` ou `from`:

```php title="src/Acervo/repositorio.php" numbered
$c = $pdo->prepare(
    'UPDATE exemplares SET estado = ? WHERE tombo = ?'
);

$c->execute([$status->value, $tombo]);
```

```php
$status = StatusExemplar::from($linha['estado']);
```

:::pitfall
Nunca guarde `$status->name`.

O `name` é o identificador no código: `Restauro`, com maiúscula, escrito em
PHP. Renomear um caso é uma alteração de código normal — e, no dia em que
alguém renomear, o banco fica com milhares de linhas apontando para um nome
que não existe mais.

O `value` é o contrato com o mundo de fora. Ele não muda porque alguém
achou um nome melhor.
:::

## Data sem fuso é informação incompleta

A tabela da Casa Amarela guarda `2026-03-11 02:03:11`. Isso não é uma hora:
é um número esperando alguém dizer onde.

Às onze da noite de terça em São Paulo, já são duas da manhã de quarta no
servidor da Virgínia. Os dois estão certos, e o relatório que compara a data
de devolução com o prazo está errado por um dia.

```php title="fuso.php" numbered
<?php

declare(strict_types=1);

$saoPaulo = new DateTimeZone('America/Sao_Paulo');

$devolucao = new DateTimeImmutable('2026-03-10 23:00:00', $saoPaulo);

$emUtc = $devolucao->setTimezone(new DateTimeZone('UTC'));

echo 'local: ', $devolucao->format('Y-m-d H:i T'), "\n";
echo 'utc:   ', $emUtc->format('Y-m-d H:i T'), "\n";
```

```text
local: 2026-03-10 23:00 -03
utc:   2026-03-11 02:00 UTC
```

É o mesmo instante, escrito de dois jeitos. O defeito da Casa Amarela não
foi o servidor estar na Virgínia — foi o programa guardar uma hora sem dizer
de onde, e depois comparar essa hora com uma data de São Paulo.

:::key
A regra que evita a classe inteira de problema, e que quase todo sistema
sério segue:

**guarde em UTC, converta na exibição.** O banco recebe o instante em UTC; a
tela recebe o fuso de quem está olhando.

Data de vencimento, aniversário e feriado são diferentes: são datas sem
hora, e converter fuso nelas é que estraga. `devolver_ate` é uma `DATE` por
esse motivo.
:::

## `DateTimeImmutable`, e por que a outra dá problema

O PHP tem duas classes de data. Uma muda; a outra, não.

```php title="mutavel.php" numbered
<?php

$prazo = new DateTime('2026-03-10');
$aviso = $prazo;

$aviso->modify('+14 days');

echo $prazo->format('Y-m-d'), "\n";
```

```text
2026-03-24
```

O `$prazo` mudou, e ninguém pediu. `$aviso = $prazo` não copiou nada — são
duas variáveis com o mesmo objeto, como qualquer objeto do PHP, e `modify()`
alterou o original.

A versão imutável responde a mesma chamada de outro jeito:

```php title="imutavel.php" numbered
<?php

$prazo = new DateTimeImmutable('2026-03-10');
$aviso = $prazo->add(new DateInterval('P14D'));

echo 'prazo: ', $prazo->format('Y-m-d'), "\n";
echo 'aviso: ', $aviso->format('Y-m-d'), "\n";
```

```text
prazo: 2026-03-10
aviso: 2026-03-24
```

`add()` não alterou nada: devolveu **outro** objeto. Guardar o resultado
deixa de ser opcional, e é isso que torna a classe segura de passar adiante.

`DateInterval` descreve uma duração com um texto curto: `P14D` é "período de
catorze dias", `P1M` é um mês, `PT2H` é duas horas — o `T` separa a parte de
data da parte de hora.

:::pitfall
Uma função que recebe `DateTime` pode modificar a data de quem chamou, e
nada na assinatura avisa.

```php
function vencimento(DateTime $retirada): DateTime
{
    return $retirada->modify('+14 days');
}
```

Essa função devolve o prazo **e** estraga o `$retirada` de quem passou. O
defeito aparece longe: na linha em que alguém imprime a data de retirada e
ela está catorze dias no futuro.

Use `DateTimeImmutable` em tudo que é novo. `DateTime` continua existindo
porque o PHP não quebra código antigo, não porque alguém a recomende.
:::

## Dinheiro não é um `int` solto

O projeto guarda multa em centavos desde o capítulo
@cap:conversao-automatica, e essa decisão está certa. O problema é outro: `int` é o tipo de tudo. Um `int` de centavos e um `int` de dias são o
mesmo tipo para o PHP e para o PHPStan.

```php
$total = $multaEmCentavos + $diasDeAtraso;
```

Isso passa em tudo. Soma centavos com dias, devolve um inteiro, e o número
chega ao recibo.

Um **objeto de valor** fecha essa porta:

```php title="src/Emprestimos/Dinheiro.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Emprestimos;

final class Dinheiro
{
    private function __construct(
        public readonly int $centavos,
    ) {
        if ($centavos < 0) {
            throw new \InvalidArgumentException('Valor negativo');
        }
    }

    public static function emCentavos(int $centavos): self
    {
        return new self($centavos);
    }

    public static function zero(): self
    {
        return new self(0);
    }

    public function mais(self $outro): self
    {
        return new self($this->centavos + $outro->centavos);
    }

    public function vezes(int $fator): self
    {
        return new self($this->centavos * $fator);
    }

    public function formatado(): string
    {
        $reais = $this->centavos / 100;

        return 'R$ ' . number_format($reais, 2, ',', '.');
    }
}
```

```php
$multa = Dinheiro::emCentavos(80)->vezes(9);

echo $multa->formatado(), "\n";
```

```text
R$ 7,20
```

Três decisões, e cada uma paga uma conta.

**O construtor é privado**, e quem cria é a `emCentavos()`. O nome do método
diz a unidade — ninguém vai passar `7.20` achando que são reais, porque não
existe uma porta que aceite reais.

**Os métodos devolvem `self`**, um objeto novo. Somar não altera nenhum dos
dois lados, exatamente como a data imutável.

**A soma só aceita `Dinheiro`.** `$multa->mais($diasDeAtraso)` não compila —
e era essa a linha que o `int` solto deixava passar.

:::term Objeto de valor
Um tipo definido pelo que ele **vale**, não por qual ele é: dois `Dinheiro`
de 720 centavos são intercambiáveis, e nenhum dos dois tem identidade
própria.

Por isso ele nasce imutável e se compara por conteúdo — ao contrário de um
`Leitor`, que tem `id` e continua sendo a mesma pessoa mesmo quando muda de
nome.
:::

:::note Na sua carreira
"Tipo demais" é uma crítica que você vai ouvir, e às vezes ela tem razão. A
defesa que funciona não é teórica: é mostrar a linha que deixou de ser
possível.

Para o `Dinheiro`, a linha é `$multa + $dias`. Para o enum, é
`=== 'emprestad'`. Para a data imutável, é a função que altera o argumento
de quem chamou.

Traga a linha. Em revisão de código, um exemplo de defeito impedido vale
mais que qualquer argumento sobre desenho — e, se você não encontrar a
linha, talvez o tipo realmente não precise existir ainda.
:::

:::tree title="Onde estamos agora"
acervo/
  src/
    Acervo/
      StatusExemplar.php    # enum com valor atrelado
      Exemplar.php          # guarda StatusExemplar, não string
      Livro.php
      Classificacao.php
    Emprestimos/
      StatusEmprestimo.php  # enum
      Dinheiro.php          # objeto de valor, imutável
      Multa.php
    Circulacao/
    Leitores/
:::

:::milestone
Fim da Parte 4. O projeto tem contratos declarados, erros com nome de
domínio, tipos conferidos antes de rodar e valores que recusam a operação
sem sentido. Nada disso é enfeite: é a lista exata de coisas que o Laravel
vai supor que você já tem.
:::

:::summary
- `string` diz o formato e não diz o conjunto; `enum` diz os dois.
- Enum atrelado (`enum X: string`) tem `value` para o mundo de fora e `name`
  para o código.
- `from()` para valor que tem de ser válido; `tryFrom()` para valor que veio
  de fora.
- `cases()` devolve a lista; `match` dentro do enum cobra o caso novo em vez
  de escondê-lo.
- Guarde `value` no banco, nunca `name`.
- Data sem fuso é número: guarde o instante em UTC, converta na exibição.
- Data de vencimento é `DATE`, sem hora e sem fuso.
- `DateTimeImmutable` devolve objeto novo; `DateTime` altera o de quem
  chamou, e nada na assinatura avisa.
- Centavos em `int` continua certo — e `int` solto soma com qualquer outro
  `int`. Um objeto de valor fecha essa porta.
:::

:::checkpoint
Você substitui strings soltas por enums atrelados, escolhe entre `from` e
`tryFrom` pelo lugar de onde o valor veio, explica por que a devolução da
Vera virou quarta-feira, e escreve um objeto de valor imutável que recusa a
operação sem sentido.
:::

:::exercise level=1
Escreva `StatusEmprestimo` como enum atrelado, com os casos: em aberto,
devolvido, renovado e em atraso.

Depois responda: por que "em atraso" é um caso problemático nessa lista?

:::answer
```php title="src/Emprestimos/StatusEmprestimo.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Emprestimos;

enum StatusEmprestimo: string
{
    case EmAberto = 'em_aberto';
    case Devolvido = 'devolvido';
    case Renovado = 'renovado';
    case EmAtraso = 'em_atraso';
}
```

"Em atraso" é problemático porque **não é um estado guardado: é uma
conclusão**. Um empréstimo entra em atraso sozinho, à meia-noite, sem que
ninguém rode nada — e um valor guardado numa coluna não muda sozinho.

Guardar `em_atraso` obriga alguém a manter isso atualizado: uma tarefa
noturna, um gatilho, uma correção quando a tarefa falha. É a coluna
`quantidade` de novo, com outra roupa.

A saída é calcular: o empréstimo está `EmAberto`, e `emAtraso()` é um método
que compara `devolver_ate` com hoje. Três casos na lista, e a quarta
informação nasce certa todas as vezes.
:::

:::exercise level=2
Escreva `PrazoDeEmprestimo`, um objeto de valor que recebe a data de
retirada e a quantidade de dias, e sabe responder:

- qual é a data de devolução;
- se uma data qualquer está atrasada em relação a ele;
- quantos dias de atraso existem até uma data.

Use `DateTimeImmutable`. Cuidado com o caso em que não há atraso.

:::answer
```php title="src/Emprestimos/PrazoDeEmprestimo.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Emprestimos;

final class PrazoDeEmprestimo
{
    public readonly \DateTimeImmutable $devolverAte;

    public function __construct(
        public readonly \DateTimeImmutable $retirada,
        public readonly int $dias,
    ) {
        if ($dias < 1) {
            throw new \InvalidArgumentException('Prazo inválido');
        }

        $this->devolverAte = $retirada->add(
            new \DateInterval("P{$dias}D")
        );
    }

    public function atrasadoEm(\DateTimeImmutable $quando): bool
    {
        return $quando > $this->devolverAte;
    }

    public function diasDeAtraso(\DateTimeImmutable $quando): int
    {
        if (!$this->atrasadoEm($quando)) {
            return 0;
        }

        return $this->devolverAte->diff($quando)->days;
    }
}
```

O cuidado que o enunciado pede está no `diasDeAtraso`: sem o `if`, uma
devolução adiantada devolveria um número positivo, porque `diff()` não tem
sinal — ele responde a distância, não a direção. Uma devolução três dias
antes viraria três dias de multa.

Duas observações sobre o desenho. A `$devolverAte` é calculada no construtor
e guardada como `readonly`: ela é consequência dos outros dois campos e
nunca vai divergir deles. E os três métodos recebem a data de fora em vez de
chamar `new DateTimeImmutable('now')` por dentro — o que torna a classe
testável sem esperar amanhecer.
:::

:::exercise level=3
Este relatório roda todo dia primeiro e cobra as multas do mês anterior.
Encontre os três defeitos relacionados a este capítulo e reescreva o trecho.

```php title="cobranca.php" numbered
$emprestimos = $pdo->query(
    "SELECT * FROM emprestimos WHERE devolvido_em IS NOT NULL"
)->fetchAll();

$total = 0;

foreach ($emprestimos as $e) {
    if ($e['status'] == 'atrasado') {
        $dias = (strtotime($e['devolvido_em'])
              - strtotime($e['devolver_ate'])) / 86400;

        $total = $total + ($dias * 0.8);
    }
}

echo "Total: R$ " . $total;
```

:::answer
**Um: a string `'atrasado'` com comparação frouxa.** Se a coluna guarda
`em_atraso`, a condição nunca é verdadeira e o relatório cobra zero — sem
erro nenhum. Com enum, o valor vem de `StatusEmprestimo::tryFrom()` e a
comparação é por identidade.

**Dois: a diferença de datas em segundos, dividida por 86.400.** Isso ignora
fuso e ignora que nem todo dia tem 86.400 segundos — os dias de mudança de
horário têm 82.800 ou 90.000. O resultado é um `float` com casas decimais
que ninguém pediu, e o arredondamento decide a multa. `DateTimeImmutable` e
`diff()->days` respondem em dias de calendário.

**Três: dinheiro em `float`.** `$dias * 0.8` acumula erro a cada soma, e o
total impresso no fim de um mês com trezentas multas não fecha com a soma
dos avisos individuais. A conta é em centavos, e o tipo é `Dinheiro`.

```php title="cobranca.php" numbered
<?php

declare(strict_types=1);

use CasaAmarela\Emprestimos\Dinheiro;
use CasaAmarela\Emprestimos\StatusEmprestimo;

$c = $pdo->prepare(
    'SELECT devolver_ate, devolvido_em, status
       FROM emprestimos
      WHERE devolvido_em IS NOT NULL
        AND status = ?'
);

$c->execute([StatusEmprestimo::Devolvido->value]);

$utc = new DateTimeZone('UTC');
$total = Dinheiro::zero();

foreach ($c as $linha) {
    $prazo = new DateTimeImmutable($linha['devolver_ate'], $utc);
    $volta = new DateTimeImmutable($linha['devolvido_em'], $utc);

    if ($volta <= $prazo) {
        continue;
    }

    $dias = $prazo->diff($volta)->days;

    $total = $total->mais(Dinheiro::emCentavos(80)->vezes($dias));
}

echo 'Total: ', $total->formatado(), "\n";
```

Um quarto defeito, de brinde, que não é deste capítulo mas fica visível
depois da reescrita: o `SELECT *` virou a lista das três colunas usadas. Um
relatório que lê a tabela inteira toda noite fica mais lento a cada coluna
que alguém acrescenta, por um motivo que não tem nada a ver com ele.
:::
