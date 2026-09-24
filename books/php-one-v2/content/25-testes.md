---
title: "Testes: o que estamos tentando provar"
number: 25
slug: testes
part: p7
kicker: "A multa por devolução adiantada tinha sido corrigida em outubro. Em fevereiro, voltou por outro caminho. Havia correção; não havia teste."
goal: >-
  Escrever testes rápidos sobre a regra de negócio, sem banco e sem HTTP:
  separar a decisão da consulta, cobrir as onze condições com uma tabela de
  casos, escolher o dublê certo, e transformar cada defeito corrigido num
  teste que impede a volta dele.
---

:::story Três dias adiantada
A Dona Marlene devolveu *O Tempo e o Vento* três dias antes do prazo, numa
sexta, pela caixa de devolução do lado de fora. Na segunda, a Neide
registrou as devoluções da caixa no painel, informando a data em que os
livros tinham sido deixados.

Na terça, a Dona Marlene recebeu pelo aplicativo um aviso de multa de
R$ 2,40.

— Três dias de multa — disse Vera, com o celular da Dona Marlene na mão —
por devolver três dias antes.

Dedé reconheceu o número antes de abrir o código. Tainá também.

— O `diff` sem sinal — disse ela. — A gente corrigiu isso. Em outubro. Eu
lembro, foi o exercício do `PrazoDeEmprestimo`.

— Corrigiu no `PrazoDeEmprestimo` — disse Dedé, abrindo o arquivo novo. —
Esse aqui é o registro de devolução da caixa. Alguém escreveu o cálculo de
novo.

— Quem?

Dedé olhou o histórico.

— Eu. Em janeiro. Com pressa.

Ele leu o trecho em voz alta:

```php
$dias = $devolverAte->diff($deixadoEm)->days;
$multa = $dias * config('biblioteca.multa_diaria_em_centavos');
```

— E por que não quebrou nada quando você escreveu? — perguntou Vera.

— Porque não tinha nada pra quebrar. A correção de outubro estava no
código. Não estava em nenhum teste.
:::

## Teste não prova que está certo

Existe uma expectativa sobre teste automatizado que o torna decepcionante:
a de que ele prova que o código está correto. Não prova. Um teste confere
**um caso**, e o programa tem infinitos.

O que o teste prova é mais modesto e mais útil: **que um comportamento
específico continua acontecendo**. Hoje, amanhã, depois da próxima
alteração de qualquer pessoa. A correção de outubro era um comportamento —
"devolução adiantada não gera multa" — que existia só na memória de quem
corrigiu. Um teste teria transformado essa memória em algo que a esteira
confere a cada commit.

:::key
Um teste é uma frase sobre o sistema, escrita de um jeito que o computador
consegue conferir. "Devolução adiantada não gera multa." Se a frase deixar
de ser verdade, alguém fica sabendo **antes** da Dona Marlene.
:::

A pergunta que organiza este capítulo e o próximo não é "como testar". É
**o que estamos tentando provar** — e a resposta a essa pergunta decide que
tipo de teste escrever, e onde.

## Pest ou PHPUnit: escolha uma e siga

O PHP tem um framework de testes dominante, o PHPUnit, e o Laravel vem com
uma camada sobre ele, o Pest, que troca classes e métodos por funções:

```php title="tests/Unit/DinheiroTest.php" numbered
<?php

use App\Emprestimos\Dinheiro;

test('soma centavos sem perder precisão', function () {
    $total = Dinheiro::emCentavos(10)
        ->mais(Dinheiro::emCentavos(20));

    expect($total->centavos)->toBe(30);
});
```

A mesma coisa em PHPUnit:

```php title="tests/Unit/DinheiroTest.php" numbered
final class DinheiroTest extends TestCase
{
    public function test_soma_centavos_sem_perder_precisao(): void
    {
        $total = Dinheiro::emCentavos(10)
            ->mais(Dinheiro::emCentavos(20));

        $this->assertSame(30, $total->centavos);
    }
}
```

Os dois rodam pelo mesmo comando, produzem o mesmo relatório e testam a
mesma coisa. O Pest é mais curto e lê melhor em português, porque o nome do
teste é uma frase entre aspas, com acento. O PHPUnit é o que você vai
encontrar na maior parte do código PHP mais antigo.

A Casa Amarela usa Pest. A escolha certa é a que o projeto já usa; a errada
é misturar as duas.

```text
$ php artisan test

   PASS  Tests\Unit\DinheiroTest
  ✓ soma centavos sem perder precisão                    0.01s

  Tests:    1 passed (1 assertions)
  Duration: 0.08s
```

## Arrumar, agir, afirmar

Todo teste tem três partes, e vale escrevê-las separadas por uma linha em
branco:

```php title="tests/Unit/PrazoDeEmprestimoTest.php" numbered
test('devolução adiantada não gera dias de atraso', function () {
    $prazo = new PrazoDeEmprestimo(
        retirada: new DateTimeImmutable('2026-02-02 10:00'),
        dias: 14,
    );

    $dias = $prazo->diasDeAtraso(
        new DateTimeImmutable('2026-02-13 18:00'),
    );

    expect($dias)->toBe(0);
});
```

**Arrumar**: montar o mundo em que o teste acontece — o prazo, com datas
fixas.

**Agir**: fazer **uma** coisa, a que está sendo testada.

**Afirmar**: conferir o resultado.

Um teste com duas ações está testando duas coisas, e quando falhar, não vai
dizer qual. Um teste sem afirmação passa sempre, e é pior que nenhum teste,
porque dá a sensação de cobertura.

Repare nas datas. Fixas, escritas no teste. Um teste que usa `now()` passa
hoje e falha no dia 31 de um mês, ou na virada do horário de verão, ou
quando roda perto da meia-noite — e cada uma dessas falhas custa uma manhã
para ser entendida. O `PrazoDeEmprestimo` recebe a data de fora desde o
capítulo @cap:enums-datas-e-valores, e é esta a razão.

## Testar a regra sem banco e sem HTTP

O `EmprestimoService` do capítulo @cap:services tem as onze condições da
Vera. Testá-lo como está exige banco: ele busca o exemplar, conta
empréstimos, soma multas. Cada teste precisaria inserir livro, exemplar,
leitor e empréstimos, e rodar dentro de uma transação. Funciona, e cada
teste leva cem milissegundos. Com os cinquenta casos que as onze regras
pedem, são cinco segundos — e a pessoa para de rodar a suíte antes de cada
commit.

Mas repare no que o service faz: ele **consulta** e depois **decide**. A
consulta precisa do banco. A decisão não — ela só precisa dos números que a
consulta trouxe. O que está impedindo o teste rápido é que as duas coisas
estão no mesmo método.

A separação:

```php title="app/Emprestimos/SituacaoDoPedido.php" numbered
final readonly class SituacaoDoPedido
{
    public function __construct(
        public StatusExemplar $estadoDoExemplar,
        public bool $daReferencia,
        public bool $daColecaoFechada,
        public ?DateTimeImmutable $adquiridoEm,
        public bool $ultimoDisponivel,
        public bool $leitorAtivo,
        public bool $leitorInfantil,
        public int $emprestimosAbertos,
        public int $emprestimosAtrasados,
        public Dinheiro $multaEmAberto,
    ) {}
}
```

```php title="app/Emprestimos/PoliticaDeEmprestimo.php" numbered
final class PoliticaDeEmprestimo
{
    public function __construct(
        private readonly RegrasDeCirculacao $regras,
    ) {}

    public function exigirPermitido(
        SituacaoDoPedido $s,
        DateTimeImmutable $quando,
        ?Autorizacao $autorizacao,
    ): void {
        // as mesmas guardas do capítulo de services,
        // lendo de $s em vez de consultar o banco
    }
}
```

O service passa a ter duas etapas: dentro da transação, monta a
`SituacaoDoPedido` com as consultas travadas; depois, entrega à política,
que decide. A política não conhece banco, não conhece Eloquent, não conhece
HTTP. Recebe um objeto e uma data, e lança uma exceção ou não lança.

:::key
Código difícil de testar costuma estar dizendo alguma coisa sobre o
desenho. Aqui, dizia que consulta e decisão estavam misturadas.

A separação não foi feita **para** o teste. Ela deixa a regra mais clara
para a Vera ler, e o teste ficou rápido como consequência.
:::

## As onze condições em menos de um segundo

Com a decisão isolada, uma tabela de casos cobre todas as condições. O
Pest chama isso de *dataset*:

```php title="tests/Unit/PoliticaDeEmprestimoTest.php" numbered
function situacao(array $muda = []): SituacaoDoPedido
{
    return new SituacaoDoPedido(...array_merge([
        'estadoDoExemplar' => StatusExemplar::Bom,
        'daReferencia' => false,
        'daColecaoFechada' => false,
        'adquiridoEm' => new DateTimeImmutable('2020-01-01'),
        'ultimoDisponivel' => false,
        'leitorAtivo' => true,
        'leitorInfantil' => false,
        'emprestimosAbertos' => 0,
        'emprestimosAtrasados' => 0,
        'multaEmAberto' => Dinheiro::zero(),
    ], $muda));
}
```

A função `situacao()` monta um pedido **que passa**, e cada teste muda só o
que interessa. É o que torna a tabela legível: cada linha diz o que tem de
diferente do caso normal.

```php title="tests/Unit/PoliticaDeEmprestimoTest.php" numbered
test('recusa o pedido', function (
    array $muda,
    string $excecao,
) {
    $politica = new PoliticaDeEmprestimo(new RegrasDeCirculacao());

    $politica->exigirPermitido(
        situacao($muda),
        new DateTimeImmutable('2026-03-10'),
        autorizacao: null,
    );
})->throws(ExcecaoDeDominio::class)->with([
    'exemplar emprestado' => [
        ['estadoDoExemplar' => StatusExemplar::Emprestado],
        ExemplarIndisponivel::class,
    ],
    'exemplar da referência' => [
        ['daReferencia' => true],
        ExemplarNaoCircula::class,
    ],
    'chegou há três dias' => [
        ['adquiridoEm' => new DateTimeImmutable('2026-03-07')],
        ExemplarEmExposicao::class,
    ],
    'último sem autorização' => [
        ['ultimoDisponivel' => true],
        UltimoExemplarExigeAutorizacao::class,
    ],
    'leitor com atraso' => [
        ['emprestimosAtrasados' => 1],
        LeitorComAtraso::class,
    ],
    'multa de R$ 5,01' => [
        ['multaEmAberto' => Dinheiro::emCentavos(501)],
        LeitorComPendencia::class,
    ],
    'três abertos em março' => [
        ['emprestimosAbertos' => 3],
        LimiteDeEmprestimosAtingido::class,
    ],
    // ... e as outras
]);
```

O `throws` confere a classe mãe; para conferir a classe exata de cada caso,
o corpo do teste captura e compara — uma linha a mais que fica a cargo do
exercício 2.

E as **bordas**, que é onde as regras erram:

```php title="tests/Unit/PoliticaDeEmprestimoTest.php" numbered
test('permite no limite exato de cada regra', function (
    array $muda,
    string $quando,
) {
    $politica = new PoliticaDeEmprestimo(new RegrasDeCirculacao());

    $politica->exigirPermitido(
        situacao($muda),
        new DateTimeImmutable($quando),
        autorizacao: null,
    );

    expect(true)->toBeTrue();
})->with([
    'multa de exatamente R$ 5,00' => [
        ['multaEmAberto' => Dinheiro::emCentavos(500)],
        '2026-03-10',
    ],
    'dois abertos em março' => [
        ['emprestimosAbertos' => 2], '2026-03-10',
    ],
    'quatro abertos em janeiro' => [
        ['emprestimosAbertos' => 4], '2026-01-15',
    ],
    'chegou há exatamente sete dias' => [
        ['adquiridoEm' => new DateTimeImmutable('2026-03-03')],
        '2026-03-10',
    ],
    'último com autorização' => [
        ['ultimoDisponivel' => true], '2026-03-10',
    ],
]);
```

"Acima de cinco reais" — R$ 5,00 passa, R$ 5,01 não. "Três livros" — dois
passam, três não. "Uma semana em exposição" — o sétimo dia é o primeiro em
que sai, ou o último em que não sai? A Vera respondeu: sai no oitavo. O
teste de borda é o lugar em que a ambiguidade da frase vira decisão
escrita.

:::pitfall
O último caso da lista, "último com autorização", está **errado** como está
escrito: ele passa `autorizacao: null` na chamada, igual aos outros, e por
isso deveria falhar. O teste vai acusar isso na primeira execução.

É de propósito, e é um defeito comum em tabela de casos: quando um caso
precisa de um parâmetro que os outros não precisam, a tabela precisa ganhar
uma coluna. Sem ela, o nome do caso promete uma coisa e o corpo testa
outra. O exercício 2 conserta.
:::

```text
$ php artisan test --filter=PoliticaDeEmprestimo

   PASS  Tests\Unit\PoliticaDeEmprestimoTest
  ✓ recusa o pedido with (exemplar emprestado)          0.01s
  ✓ recusa o pedido with (exemplar da referência)
  ...
  ✗ permite no limite exato de cada regra with
    (último com autorização)

  Tests:    1 failed, 22 passed (23 assertions)
  Duration: 0.14s
```

Vinte e três casos, catorze centésimos de segundo — e o vermelho que a
armadilha acima prometeu. O tempo é o número que importa aqui: é ele que
torna possível rodar a suíte a cada vez que o arquivo é salvo.

## Dublês: fake, stub, spy, mock

Nem tudo que o código usa pode ser separado como a política. O
`EmprestimoService` usa o `EnviadorDeAviso`, e o teste não deve mandar
WhatsApp. Um objeto que substitui outro no teste se chama **dublê**, e
existem quatro tipos, que diferem no que sabem fazer:

| Dublê | O que é | Exemplo |
|---|---|---|
| stub | devolve respostas prontas | um relógio que sempre diz 10h |
| fake | implementação simples de verdade | `EnviadorFalso`, que guarda numa lista |
| spy | registra as chamadas para conferir depois | `Log::spy()` |
| mock | espera chamadas específicas, e falha se não vierem | `Mockery::mock()` |

Tabela: Os nomes se confundem em conversa e em documentação. A distinção
que importa é a da última coluna: o que o teste confere depois.

O `EnviadorFalso` do capítulo @cap:service-container é um fake. O teste
confere o **resultado** — o que ficou na lista:

```php
expect($falso->enviados)->toHaveCount(1);
```

O mesmo teste com um mock confere a **chamada**:

```php
$mock = Mockery::mock(EnviadorDeAviso::class);
$mock->shouldReceive('enviar')
    ->once()
    ->with(
        Mockery::type(Leitor::class),
        Mockery::pattern('/Devolva/'),
    );
```

Os dois testam a mesma coisa hoje. A diferença aparece na próxima
alteração: se alguém trocar `enviar($leitor, $texto)` por
`enviar(new Aviso($leitor, $texto))`, o mock quebra — ele estava amarrado
ao formato da chamada. O fake, se for atualizado junto com a interface,
continua conferindo o que importa: um aviso foi enviado.

:::key
Prefira conferir **o que aconteceu** a conferir **como aconteceu**. Um teste
amarrado ao "como" quebra a cada refatoração que não mudou nada, e um teste
que quebra sem motivo ensina o time a ignorar teste vermelho.

O fake ganha na maior parte dos casos. O mock é a ferramenta certa quando
**a chamada é o comportamento** — "o sistema de pagamento foi chamado uma
vez e só uma" é uma afirmação sobre a chamada.
:::

## Factory como fixture

Os testes de unidade da política não precisaram de model nenhum. Os que
precisam — um teste do `LeitorResource`, uma regra do model `Exemplar` —
podem usar as factories do capítulo @cap:migrations-seeders-e-factories
**sem banco**:

```php title="tests/Unit/ExemplarTest.php" numbered
test('exemplar em exposição até o sétimo dia', function () {
    $exemplar = Exemplar::factory()->make([
        'adquirido_em' => '2026-03-03',
    ]);

    expect($exemplar->emExposicao(
        new DateTimeImmutable('2026-03-09'),
    ))->toBeTrue();

    expect($exemplar->emExposicao(
        new DateTimeImmutable('2026-03-11'),
    ))->toBeFalse();
});
```

O `make()` monta o model com os dados da factory e os que você passou,
**sem gravar**. O `create()` grava. Para teste de unidade, `make()`: é
instantâneo e não depende de o banco estar de pé.

A factory entrega um exemplar plausível em todos os campos, e o teste
declara só o que importa para ele — a data de aquisição. Quem lê sabe na
hora do que o teste depende.

## O teste que reproduz o defeito de ontem

A correção da multa da Dona Marlene tem duas partes, e a segunda é a que
não foi feita em outubro.

A primeira é o código: o registro de devolução da caixa deixa de calcular
sozinho e passa a usar o `PrazoDeEmprestimo`, que é onde o cálculo mora.

A segunda é o teste, escrito **antes** da correção, para ver falhar:

```php title="tests/Unit/DevolucaoDaCaixaTest.php" numbered
test('devolução adiantada pela caixa não gera multa', function () {
    // o caso da Dona Marlene, em fevereiro
    $regras = new RegrasDeCirculacao();
    $prazo = new PrazoDeEmprestimo(
        new DateTimeImmutable('2026-02-02 10:00'),
        14,
    );

    $multa = $regras->multaPor(
        $prazo,
        new DateTimeImmutable('2026-02-13 18:00'),
    );

    expect($multa)->toEqual(Dinheiro::zero());
});
```

```text
  ✗ devolução adiantada pela caixa não gera multa
  Failed asserting that Dinheiro(240) is equal to Dinheiro(0).
```

Vermelho. É o que se quer ver: o teste reproduz o defeito. Aplica-se a
correção, e ele fica verde. A partir daqui, a Dona Marlene está protegida
por uma linha que roda a cada commit — e o comentário no teste diz de onde
ele veio, para que ninguém o apague achando que é redundante.

:::note
Cobertura — a porcentagem de linhas do código que algum teste executou —
é um **mapa**, não uma nota. Ela mostra onde não há teste nenhum, e isso é
útil. Ela não mostra se os testes que existem conferem alguma coisa.

Um projeto com meta de 90% de cobertura costuma ganhar testes que executam
tudo e afirmam nada, escritos para bater a meta. A Casa Amarela não tem meta
de cobertura. Tem uma regra: **todo defeito corrigido ganha um teste que o
reproduz**. A cobertura sobe sozinha, e sobe onde os defeitos estavam.
:::

:::note Na sua carreira
A pergunta "você escreve testes?" em entrevista tem uma resposta que
funciona melhor que "sim": contar um defeito que voltou. Todo mundo que
trabalha há algum tempo tem um. O que o entrevistador quer ouvir é que você
entendeu por que ele voltou — não havia teste — e o que faz hoje
diferente: o teste vem antes da correção, e é escrito para falhar primeiro.

E se a vaga for num projeto sem teste nenhum, que é mais comum do que se
admite, essa mesma regra é o jeito de começar sem pedir permissão: não
precisa de uma semana dedicada. Precisa de um teste por defeito corrigido,
a partir de hoje.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/Emprestimos/
    SituacaoDoPedido.php          # o que a consulta trouxe
    PoliticaDeEmprestimo.php      # a decisão, sem banco
    EmprestimoService.php         # consulta, entrega, grava
  tests/Unit/
    DinheiroTest.php
    PrazoDeEmprestimoTest.php
    PoliticaDeEmprestimoTest.php  # onze condições, bordas
    ExemplarTest.php
    DevolucaoDaCaixaTest.php      # a Dona Marlene
  tests/Fakes/
    EnviadorFalso.php
:::

:::summary
- Teste não prova que o código está certo; prova que um comportamento
  continua acontecendo.
- Pest e PHPUnit fazem a mesma coisa; a escolha certa é a do projeto, e não
  se misturam.
- Arrumar, agir, afirmar: uma ação por teste, e sempre uma afirmação.
- Datas fixas no teste; `now()` produz falha que depende do dia.
- Separar consulta de decisão torna a regra testável sem banco e mais clara
  para quem a lê.
- Dataset cobre as condições numa tabela; os testes de borda transformam a
  ambiguidade da frase em decisão.
- Stub responde, fake funciona, spy registra, mock espera. Prefira conferir
  o resultado à chamada.
- `factory()->make()` monta sem gravar; é o que o teste de unidade usa.
- Todo defeito corrigido ganha um teste escrito antes da correção, que
  falha primeiro.
- Cobertura é mapa, não meta.
:::

:::checkpoint
As onze condições de empréstimo e as bordas de cada uma rodam em menos de
um segundo, sem banco e sem HTTP; o aviso é conferido com um fake; e o
defeito da Dona Marlene tem um teste que falhou antes da correção e passa
depois dela.
:::

:::exercise level=1
Cada teste abaixo tem um problema. Diga qual:

```php
// 1
test('calcula multa', function () {
    $regras = new RegrasDeCirculacao();
    $regras->multaPor($prazo, now());
});

// 2
test('empréstimo e devolução', function () {
    $e = $service->realizar(2117, 47);
    $service->devolver($e->id, now());
    expect($e->fresh()->devolvido())->toBeTrue();
});

// 3
test('prazo infantil', function () {
    $leitor = Leitor::factory()->create(['infantil' => true]);
    expect((new RegrasDeCirculacao())->prazoPara($leitor))
        ->toBe(7);
});
```

:::answer
1. Não afirma nada — passa sempre. E usa `now()`, então o resultado, se
   fosse conferido, dependeria do dia.
2. Testa duas ações. Se falhar, não diz se o problema está no empréstimo ou
   na devolução. São dois testes, e o de devolução arruma o empréstimo sem
   passar pelo service.
3. Usa `create()` num teste que não precisa de banco. `make()` basta: a
   regra só lê o atributo do objeto. Com `create()`, o teste fica mais
   lento e passa a falhar se o banco de teste não estiver de pé.
:::

:::exercise level=2
Conserte o dataset de "permite no limite exato" para que o caso "último
com autorização" passe uma `Autorizacao` de verdade e os outros continuem
passando `null`. E, no teste de recusa, confira a classe **exata** da
exceção de cada caso, não só a mãe.

:::answer
O dataset ganha uma terceira coluna, e os casos que não precisam dela
passam `null`:

```php
test('permite no limite exato de cada regra', function (
    array $muda,
    string $quando,
    ?Autorizacao $autorizacao,
) {
    $politica = new PoliticaDeEmprestimo(new RegrasDeCirculacao());

    $politica->exigirPermitido(
        situacao($muda),
        new DateTimeImmutable($quando),
        $autorizacao,
    );

    expect(true)->toBeTrue();
})->with([
    'multa de exatamente R$ 5,00' => [
        ['multaEmAberto' => Dinheiro::emCentavos(500)],
        '2026-03-10', null,
    ],
    // ...
    'último com autorização' => [
        ['ultimoDisponivel' => true],
        '2026-03-10',
        new Autorizacao(usuarioId: 1, motivo: 'trabalho escolar'),
    ],
]);
```

E a recusa confere a classe exata:

```php
test('recusa o pedido', function (array $muda, string $esperada) {
    $politica = new PoliticaDeEmprestimo(new RegrasDeCirculacao());

    try {
        $politica->exigirPermitido(
            situacao($muda),
            new DateTimeImmutable('2026-03-10'),
            null,
        );
    } catch (ExcecaoDeDominio $e) {
        expect($e)->toBeInstanceOf($esperada);
        return;
    }

    $this->fail("Esperava {$esperada}, nada foi lançado");
})->with([ /* os mesmos casos */ ]);
```

Sem a conferência exata, um caso de "leitor com atraso" que por engano
lançasse `LeitorComPendencia` passaria — a mãe é a mesma. É o tipo de
defeito que só aparece quando a tela mostra "regularize sua multa" para
alguém que não deve nada.
:::

:::exercise level=3
O `EmprestimoService::devolver()` grava a devolução, calcula a multa,
libera o exemplar e dispara `ExemplarDevolvido`. A equipe quer testá-lo.

Divida o que precisa ser provado entre teste de unidade (sem banco) e teste
de feature com banco — que é o assunto do próximo capítulo —, e justifique
cada escolha. Diga também o que **não** vale a pena testar nesse método.

:::answer
**Unidade, sem banco:**

O cálculo da multa em todas as bordas: devolução no dia, um dia depois,
adiantada, depois do teto. Isso já está no `RegrasDeCirculacao::multaPor`,
e é lá que o teste mora — não no service.

A regra "empréstimo já devolvido não pode ser devolvido de novo", se ela
for extraída para o model ou para a política. Enquanto estiver dentro da
transação do service, testá-la exige banco.

**Feature, com banco:**

Que a devolução grava `devolvido_em` e a multa **e** libera o exemplar,
juntas — é uma afirmação sobre a transação, e só o banco a confirma.

Que uma falha no meio desfaz tudo: forçar uma exceção depois de gravar a
devolução e conferir que o exemplar continua emprestado.

Que o evento `ExemplarDevolvido` é disparado **depois** do commit — com
`Event::fake()` e a conferência de que ele não sai quando a transação é
desfeita.

**O que não vale testar:**

Que o `DB::transaction` do Laravel funciona. Que o `update` do Eloquent
grava. Que o `findOrFail` lança quando não acha. É código do framework, já
testado por quem o escreveu; um teste disso só confere que o Laravel está
instalado.

E testar de novo, no teste de feature, cada borda da multa. Uma devolução
com multa e uma sem bastam para provar que o service chama o cálculo; as
bordas já estão provadas na unidade. Repetir faz a suíte ficar lenta sem
provar nada novo — que é o erro que o próximo capítulo abre discutindo.
:::
