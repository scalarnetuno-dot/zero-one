---
title: "Funções"
number: 7
slug: funcoes
part: p1
kicker: "Uma regra que mora em dez lugares muda em nove. O décimo é sempre o que gera o boleto."
goal: >-
  Extrair regra para função, usar parâmetros e retorno com intenção,
  entender escopo sem recorrer a `global`, e escrever funções que podem ser
  testadas sem subir nada.
---

:::story Cinquenta centavos
A diretoria da Casa Amarela aprovou, em ata, o aumento da multa diária de
R$ 0,50 para R$ 0,80. Seu Juvenal mandou mensagem no sábado:

> *"É só trocar o número, né? Pra segunda dá?"*

Dedé abriu o Sistema e deu uma busca por `0.5`.

Sete resultados.

O cálculo da tela de devolução. O do relatório de pendências. O do recibo
impresso. O do e-mail de cobrança. Um dentro de um `if` que só roda em
dezembro, por algum motivo. Um comentado, com a data `// 2014` do lado. E um
sétimo, em `funcoes2_NOVO_final.php`, escrito como `50/100`.

Ele trocou os seis primeiros. Na segunda, a Vera ligou dizendo que o recibo
impresso continuava com o valor antigo.

O recibo não usava nenhum dos sete. Tinha o próprio, escrito como
`$dias * 0.50`, dentro de uma string de HTML, numa linha com quatrocentos e
doze caracteres.
:::

Essa história não é sobre PHP. É sobre a diferença entre **escrever uma
regra** e **espalhar uma conta**.

## Uma regra em dez lugares

Código duplicado não dá erro. Não aparece no log, não quebra teste, não
reclama na revisão — especialmente quando as cópias são levemente
diferentes, como `0.5`, `50/100` e `0.50`.

Ele só se manifesta quando a regra muda. E regra sempre muda: é o único
requisito garantido de qualquer sistema.

:::key
A pergunta que identifica duplicação problemática não é "esse código é
parecido?". É: **"quando essa regra mudar, quantos lugares eu preciso
lembrar?"**. Se a resposta for maior que um, você tem uma função esperando
para nascer.
:::

## Dê um nome à decisão

```php title="multa.php" numbered
<?php

function multaEmCentavos(int $diasDeAtraso): int
{
    if ($diasDeAtraso <= 0) {
        return 0;
    }

    return min($diasDeAtraso * 80, 2000);
}

echo multaEmCentavos(0), "\n";
echo multaEmCentavos(3), "\n";
echo multaEmCentavos(90), "\n";
```

```text
0
240
2000
```

`function`, nome, parênteses, tipos, corpo. `return` devolve o valor e
encerra a função na hora — o que vier depois não roda.

O valor está em centavos pelo motivo do capítulo @cap:variaveis-e-tipos, e o
teto de R$ 20,00 está ali porque a ata da diretoria também definiu isso. Os
dois números vão sair daqui no capítulo
@cap:configuracao-ambiente-e-artisan; por ora, o importante é que eles estão
**num lugar só**.

:::anatomy title="As partes de uma função"
lang: php
code: |
  function multaEmCentavos(
      int $dias,
      int $porDia = 80,
  ): int {
      return min($dias * $porDia, 2000);
  }
notes:
  - { line: 1, text: "O nome é um verbo ou uma pergunta. `multa()` é ambíguo; `multaEmCentavos()` não." }
  - { line: 2, text: "`int $dias` é obrigatório: quem chama precisa informar." }
  - { line: 3, text: "`= 80` é o valor padrão. Parâmetro com padrão vem depois dos obrigatórios." }
  - { line: 3, text: "A vírgula final é permitida desde o PHP 8 e evita ruído no diff." }
  - { line: 4, text: "`: int` é o tipo de retorno. Sem ele, a função promete qualquer coisa." }
:::

## Um contrato pequeno

```php title="chamadas.php" numbered
<?php

function registrarDevolucao(
    int $emprestimoId,
    int $diasDeAtraso,
    bool $isentarMulta = false,
    bool $notificarLeitor = true,
): void {
    // ...
}

registrarDevolucao(812, 9);
registrarDevolucao(812, 9, true, false);
registrarDevolucao(812, 9, isentarMulta: true);
registrarDevolucao(
    emprestimoId: 812,
    diasDeAtraso: 9,
    notificarLeitor: false,
);
```

A terceira e a quarta chamadas usam **argumentos nomeados**, um recurso do
PHP 8. Compare a segunda com a terceira: `registrarDevolucao(812, 9, true,
false)` obriga quem lê a abrir a função para descobrir o que são aquele
`true` e aquele `false`.

:::key
Quando uma chamada tem um `true` ou um `false` solto, nomeie o argumento. É
o ganho de legibilidade mais barato que existe — zero custo de execução,
zero linhas a mais — e resolve para sempre a dúvida de quem lê o código daqui
a seis meses, que provavelmente é você.
:::

Argumentos nomeados também deixam pular os do meio: na terceira chamada,
`$isentarMulta` foi informado sem mencionar `$notificarLeitor`.

:::pitfall
Ao adotar argumentos nomeados, o **nome do parâmetro vira contrato
público**. Renomear `$isentarMulta` para `$semMulta` passa a quebrar quem
chama — e o erro só aparece em execução, com uma mensagem sobre argumento
desconhecido. Em código de biblioteca isso é sério; em código de aplicação,
é um incômodo gerenciável. Vale saber antes de renomear.
:::

## Retorno: prometa um tipo só

```php title="retorno.php" numbered
<?php

function buscarLeitor(int $id): ?array
{
    $leitores = [47 => ['nome' => 'Marlene']];

    return $leitores[$id] ?? null;
}
```

`?array` significa "array ou `null`". É um contrato honesto: quem chama sabe
que precisa tratar a ausência.

O que você **não** quer é uma função que devolve coisas de naturezas
diferentes conforme o humor:

:::compare left="Promessa quebrada" right="Promessa honesta" lang="php"
function buscar($id) {
    if (!$id) return false;
    if ($erro) return "erro";
    return $dados;
}
---
function buscar(int $id): ?Leitor
{
    return $this->leitores[$id]
        ?? null;
}
:::

Do lado esquerdo, quem chama precisa testar três tipos diferentes e ainda
distinguir `false` de `"erro"` de array vazio. É o tipo de função que gera,
em quem a consome, um `if` de cinco linhas em cada ponto de uso.

Do lado direito, há uma resposta: o objeto ou nada. E o caso de erro — que
existe e é real — vira uma exceção no capítulo @cap:excecoes, que é o lugar
dele.

Existe também `: void`, para funções que não devolvem nada, e `: never`,
para funções que nunca retornam porque sempre lançam exceção ou encerram o
programa. Os dois aparecem no capítulo @cap:tipagem-estrita.

## O relatório que perdeu uma variável

:::story O relatório que zerou
Tainá escreveu a função de totalização do relatório mensal. Testou. Deu
zero.

```php
$totalGeral = 0;

function somar(int $valor): void
{
    $totalGeral += $valor;
}

foreach ($multas as $m) {
    somar($m);
}

echo $totalGeral;
```

— Não faz sentido — ela disse. — Eu somei oito mil reais e ele imprime zero.

Dedé olhou por dois segundos.

— Ele imprime zero porque a `$totalGeral` de dentro da função não é a de
fora. São duas variáveis com o mesmo nome, e a de dentro morre quando a
função termina.

— Mas em Python isso daria erro.

— Em PHP dá um aviso e continua. É pior.
:::

```text
PHP Warning: Undefined variable $totalGeral in /app/rel.php
on line 5
```

Um aviso. Não um erro fatal. O programa seguiu, somou zero com zero oito mil
vezes, e imprimiu um número plausível.

## O relatório que perdeu uma variável

Em PHP, o escopo de função é **fechado**. Diferente de JavaScript e de
Python, uma função não enxerga as variáveis de fora — nem para ler.

```php title="escopo.php" numbered
<?php

$prazo = 14;

function diasDeEmprestimo(): int
{
    return $prazo;    // Warning: Undefined variable
}
```

Existe uma palavra-chave que quebra essa regra:

```php
function somar(int $valor): void
{
    global $totalGeral;
    $totalGeral += $valor;
}
```

Isso funciona. E é quase sempre a resposta errada.

:::warning
Uma função que lê ou escreve variável global não pode ser testada sozinha,
não pode ser chamada duas vezes com confiança, e não pode ser lida sem
conhecer o programa inteiro. Pior: ela cria uma dependência **invisível** —
nada na assinatura diz que aquela função precisa de `$totalGeral`.

A regra que este livro segue do capítulo @cap:services em diante: **tudo que
a função precisa entra por parâmetro; tudo que ela produz sai por retorno.**
:::

A versão correta não precisa de nada além do que já foi visto:

```php title="correto.php" numbered
<?php

function somarMultas(array $multas): int
{
    $total = 0;

    foreach ($multas as $valor) {
        $total += $valor;
    }

    return $total;
}

$totalGeral = somarMultas($multas);
```

Ou, já que `array_sum` existe:

```php
$totalGeral = array_sum($multas);
```

## Uma função que dá para provar

A função `multaEmCentavos()` do começo do capítulo tem uma propriedade que
vale nomear: dado o mesmo `$diasDeAtraso`, ela devolve **sempre** o mesmo
resultado, e não mexe em nada fora dela.

Isso se chama **função pura**, e a consequência prática aparece no capítulo
@cap:testes:

```php title="tests/MultaTest.php" numbered
<?php

test('multa tem teto de vinte reais', function () {
    expect(multaEmCentavos(90))->toBe(2000);
});

test('sem atraso não há multa', function () {
    expect(multaEmCentavos(0))->toBe(0);
    expect(multaEmCentavos(-3))->toBe(0);
});
```

Quatro linhas, sem banco, sem servidor, sem configuração. Rodam em
milissegundos e provam a regra que a diretoria aprovou em ata.

Compare com o que seria testar a mesma regra dentro daquela string de HTML
de quatrocentos e doze caracteres do recibo. Não é que fosse difícil: é que
não existe ponto de entrada. A função não é uma formalidade — ela é o que
torna a regra **alcançável**.

:::note Na sua carreira
"Extrair função" é a refatoração mais segura que existe e a mais subestimada
em entrevista técnica. Quando pedirem para você melhorar um trecho de
código, comece por aí — antes de propor arquitetura, padrão de projeto ou
microsserviço.

E há um efeito colateral em código legado: você não precisa de permissão
para extrair uma função. Não muda comportamento, não muda banco, não muda
contrato. É a única melhoria que dá para fazer numa terça-feira comum,
enquanto conserta outra coisa, sem abrir reunião.
:::

## Closures e arrow functions

Uma função também pode ser um valor:

```php title="closure.php" numbered
<?php

$formatar = function (int $centavos): string {
    return 'R$ ' . number_format($centavos / 100, 2, ',', '.');
};

echo $formatar(2000), "\n";
```

```text
R$ 20,00
```

Closures não enxergam o escopo de fora automaticamente — a mesma regra de
antes. Para capturar uma variável, você pede:

```php title="use.php" numbered
<?php

$multaPorDia = 80;

$calcular = function (int $dias) use ($multaPorDia): int {
    return $dias * $multaPorDia;
};
```

`use ($x)` captura **por valor**, no momento em que a closure é criada.
Alterar `$multaPorDia` depois não muda nada dentro dela. Para capturar por
referência existe `use (&$x)`, que é raro e quase sempre um sintoma.

As **arrow functions** encurtam o caso comum:

```php
$calcular = fn(int $dias): int => $dias * $multaPorDia;
```

Uma expressão só, sem `use` — a arrow function captura automaticamente o que
precisa, sempre por valor. É a forma que aparece no resto do livro, e a
única que cabe confortavelmente dentro de `array_map`.

## Callables: comportamento como argumento

```php title="callable.php" numbered
<?php

function aplicarEm(array $itens, callable $operacao): array
{
    $saida = [];

    foreach ($itens as $item) {
        $saida[] = $operacao($item);
    }

    return $saida;
}

$centavos = [50, 240, 2000];

print_r(aplicarEm($centavos, fn($c) => $c / 100));
```

Essa função não sabe o que vai ser feito com os itens — ela só sabe que algo
será. É exatamente o que `array_map` faz, e é o mesmo mecanismo que o
capítulo @cap:service-container vai usar para montar objetos sem saber quais.

:::art caption="Quadrinho: o pedido pequeno, em quatro quadros."
Tira editorial em quatro quadros, traço simples, fundo branco, sem cenário
detalhado. QUADRO 1: um coordenador de projeto sorridente, de crachá, diz
"É só trocar um número". QUADRO 2: o desenvolvedor, sentado, pergunta "Em
quantos lugares?". QUADRO 3: o coordenador, ainda sorrindo, responde "Um
lugar. Acho." — e atrás dele, fora do foco dele, uma pilha de papéis
desmorona. QUADRO 4: o desenvolvedor olhando para a tela, com sete abas
abertas, expressão neutra, e a legenda embaixo do quadro: "CAPÍTULO 7 —
FUNÇÕES". Humor seco, personagens expressivos, poucos elementos.
:::

:::summary
- Regra duplicada não dá erro; ela só aparece quando a regra muda.
- O nome da função é um verbo ou uma pergunta, e diz a unidade do valor.
- Argumento nomeado elimina o `true` solto na chamada.
- Prometa um tipo de retorno só; ausência é `?Tipo`, erro é exceção.
- Escopo de função em PHP é fechado — e `global` é um sintoma, não uma
  solução.
- Tudo que entra por parâmetro, tudo que sai por retorno: é o que torna a
  função testável.
- `fn() =>` é a forma curta; `use ($x)` captura por valor.
:::

:::checkpoint
Você extrai uma regra repetida para uma função, escolhe entre parâmetro e
retorno em vez de estado global, e consegue escrever um teste de quatro
linhas que prova a regra.
:::

:::exercise level=1
Escreva `diasDeAtraso(string $devolverAte, string $hoje): int`, que devolva
zero quando ainda estiver no prazo.

:::answer
```php
<?php

function diasDeAtraso(string $devolverAte, string $hoje): int
{
    $limite = new DateTimeImmutable($devolverAte);
    $agora = new DateTimeImmutable($hoje);

    if ($agora <= $limite) {
        return 0;
    }

    return (int) $limite->diff($agora)->days;
}
```
Receber a data de hoje **como parâmetro**, em vez de chamar `new
DateTimeImmutable()` lá dentro, é o que permite testar a função em qualquer
dia do ano sem mexer no relógio da máquina. É a aplicação direta da regra do
capítulo — e o capítulo @cap:enums-datas-e-valores volta a ela.
:::

:::exercise level=2
Escreva uma função que receba a lista de empréstimos e uma closure de
critério, e devolva só os que passam. Depois use-a para filtrar os atrasados
há mais de trinta dias.

:::answer
```php
<?php

function filtrar(array $itens, callable $criterio): array
{
    return array_values(array_filter($itens, $criterio));
}

$criticos = filtrar(
    $emprestimos,
    fn(array $e): bool => $e['dias'] > 30
);
```
O `array_values` no retorno não é detalhe: `array_filter` **preserva as
chaves originais**, então filtrar os itens 0, 3 e 7 devolve um array com
essas chaves — e o que parecia uma lista deixa de ser uma lista. O capítulo
@cap:arrays explica por que isso importa na hora de virar JSON.
:::

:::exercise level=3
A função abaixo está em produção na Casa Amarela há dois anos. Ela funciona.
Liste quatro problemas e proponha a assinatura que você usaria no lugar.

```php
function processa($id) {
    global $conexao, $config;
    $r = mysqli_query($conexao, "SELECT * FROM emprestimo
         WHERE id = $id");
    $e = mysqli_fetch_assoc($r);
    if (!$e) return false;
    $dias = (time() - strtotime($e['devolver_ate'])) / 86400;
    if ($dias > 0) {
        mysqli_query($conexao, "UPDATE emprestimo SET multa =
            " . ($dias * $config['multa']) . " WHERE id = $id");
        mail($e['email'], 'Multa', 'Você tem multa');
    }
    return true;
}
```

:::answer
**1. Nome sem significado.** `processa` não diz o que faz. E o que ela faz
são três coisas: calcula multa, grava e envia e-mail. Um nome honesto para
isso não existe — o que é justamente o sinal de que são três funções.

**2. Duas dependências invisíveis.** `global $conexao, $config` não aparecem
na assinatura. Quem lê `processa(812)` não tem como saber que a função
precisa de banco configurado e de um array global existindo.

**3. Injeção de SQL.** `WHERE id = $id` concatena o parâmetro direto na
consulta. Se `$id` vier de uma requisição, qualquer pessoa executa o que
quiser no banco. É o assunto do capítulo @cap:banco-de-dados-e-sql, e é a
falha mais grave da lista.

**4. Retorno mentiroso.** Devolve `true`/`false`, e `false` significa
"empréstimo não encontrado" — mas `true` significa tanto "calculei a multa e
avisei" quanto "não havia multa, não fiz nada". Quem chama não consegue
distinguir.

E há um quinto, que é de desenho e explica os outros: **a função tem três
responsabilidades e nenhum jeito de testar**. Não dá para verificar o cálculo
da multa sem banco, e não dá para verificar a gravação sem enviar e-mail de
verdade para o endereço que estiver na linha.

A assinatura que eu usaria separa as três:

```php
function multaEmCentavos(
    DateTimeImmutable $devolverAte,
    DateTimeImmutable $hoje,
    int $porDiaEmCentavos,
    int $tetoEmCentavos,
): int;

function registrarMulta(
    Emprestimo $emprestimo,
    int $centavos,
): void;

function notificarMulta(Leitor $leitor, int $centavos): void;
```

A primeira é pura e testável em quatro linhas. A segunda toca o banco e
nada mais. A terceira toca e-mail e nada mais — e no capítulo
@cap:events-jobs-e-filas ela sai da requisição e vai para uma fila.

Quem orquestra as três é uma quarta função, de quatro linhas, que vira o
serviço do capítulo @cap:services. Repare que nenhuma das quatro precisa de
`global`.
:::

:::story A piada final
Terça, 9h15. Seu Juvenal mandou mensagem:

> *"A diretoria reconsiderou. Volta pra 0,50."*

Dedé abriu o projeto novo, mudou um número, rodou os testes, subiu.

Levou quarenta segundos.

Ele respondeu "feito" e, por hábito, abriu o Sistema antigo numa aba, só
para conferir. O recibo impresso continuava com 0,80.

Deixou assim. É o último lugar do mundo que ainda usa aquele arquivo, e o
Dedé decidiu que a data em que ele for desligado vai ser feriado.
:::
