---
title: "Funções anônimas e closures"
number: 25
slug: funcoes-anonimas-e-closures
part: p5
kicker: "O relatório funcionou até alguém pôr um namespace no arquivo. Depois disso, o PHP não achava mais uma função que estava três linhas acima."
goal: >-
  Passar funções como valor sem depender do nome escrito num texto, usar
  $this e static dentro de closures, fabricar funções a partir de outras, e
  combinar pequenas regras numa só — o formato em que o volume 2 vai
  entregar rotas, filtros e middlewares.
---

:::story Três linhas acima
Tainá tinha feito o que o capítulo de namespaces mandava: pôs
`namespace CasaAmarela\Relatorios;` no topo do script de atrasados, junto
com os outros. Rodou para conferir.

```text
PHP Fatal error: Uncaught TypeError: array_filter(): Argument #2
($callback) must be a valid callback or null, function
"estaAtrasado" not found or invalid function name
```

— A função está ali — disse ela, apontando a tela. — Três linhas acima.
`function estaAtrasado`.

Dedé leu a linha do `array_filter`.

```php
$atrasados = array_filter($emprestimos, 'estaAtrasado');
```

— Você passou um texto.

— Passei o nome da função.

— Passou um texto com o nome. O PHP procura esse texto como nome de
função global. A sua agora se chama
`CasaAmarela\Relatorios\estaAtrasado`.

— E antes funcionava.

— Antes o arquivo não tinha endereço.
:::

## Função é valor

O capítulo @cap:funcoes mostrou o essencial: uma função pode ser guardada
numa variável, passada a outra e chamada depois. `array_map` e
`array_filter` recebem funções, e o `callable` na assinatura diz que o
parâmetro aceita "qualquer coisa que dê para chamar".

O problema do script da Tainá está nessa expressão, "qualquer coisa". Para
o PHP, `callable` aceita várias formas diferentes:

| Forma | Exemplo | Resolvida quando |
|---|---|---|
| texto com nome de função | `'estaAtrasado'` | na chamada, como nome global |
| texto com classe e método | `'Relatorio::gerar'` | na chamada |
| array objeto + método | `[$relatorio, 'filtrar']` | na chamada |
| closure | `fn($e) => ...` | já é a função |
| sintaxe de primeira classe | `estaAtrasado(...)` | onde está escrita |

Tabela: As três primeiras são nomes escritos em texto, que o PHP procura
na hora de chamar. As duas últimas são a própria função.

Um nome escrito em texto não sabe em que arquivo foi escrito. Ele não
passa pelo `use` nem pelo `namespace` do capítulo
@cap:namespaces-e-autoload, não é encontrado pelo "renomear" do editor,
e o PHPStan não consegue conferir se a função existe.

## `(...)`: a função, não o nome

Desde o PHP 8.1, qualquer função ou método vira um valor escrevendo `(...)`
depois do nome, no lugar dos argumentos:

```php title="atrasados.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Relatorios;

function estaAtrasado(array $e): bool
{
    return $e['dias'] > 14;
}

$emprestimos = [
    ['leitor' => 'Marlene', 'dias' => 20],
    ['leitor' => 'Iolanda', 'dias' => 3],
];

$atrasados = array_filter($emprestimos, estaAtrasado(...));
echo count($atrasados), "\n";

var_dump(estaAtrasado(...) instanceof \Closure);
```

```text
$ php atrasados.php
1
bool(true)
```

`estaAtrasado(...)` não chama a função: devolve um objeto `Closure` que a
representa. O nome é resolvido **ali**, na linha em que está escrito, com o
namespace do arquivo — igual a uma chamada normal. Renomear a função
renomeia esta linha; apagar a função faz o PHPStan acusar esta linha.

Com métodos, a mesma coisa:

```php
array_map($formatador->reais(...), $multas);
array_map(Dinheiro::emCentavos(...), $valores);
```

:::key
Para passar uma função a outra, passe a **função**: `nome(...)`,
`$objeto->metodo(...)`, `Classe::metodo(...)`, ou uma closure. Nunca o
nome dela num texto. O texto funciona até o dia em que o arquivo ganha um
endereço, e aí quebra na execução, não na leitura.
:::

## `Closure` como tipo

A assinatura também pode ser mais exigente que `callable`:

```php
function aplicarEm(array $itens, \Closure $operacao): array
{
    return array_map($operacao, $itens);
}
```

`\Closure` aceita só objetos de função — closures e `(...)` —, e recusa
texto e array. Quem chamar `aplicarEm($x, 'strtoupper')` recebe um
`TypeError` na chamada, com a linha certa, em vez de um erro dentro do
`array_map`.

A barra antes de `Closure` é a do capítulo @cap:namespaces-e-autoload: num
arquivo com namespace, `Closure` sem barra seria procurada como
`CasaAmarela\Relatorios\Closure`, que não existe.

## `$this` dentro da closure

Uma closure criada dentro de um método enxerga o objeto em que nasceu:

```php title="relatorio.php" numbered
<?php

declare(strict_types=1);

final class RelatorioDeAtraso
{
    public function __construct(private int $limiteEmDias) {}

    public function filtro(): \Closure
    {
        return fn(array $e): bool => $e['dias'] > $this->limiteEmDias;
    }
}

$relatorio = new RelatorioDeAtraso(14);
$emprestimos = [['dias' => 20], ['dias' => 3], ['dias' => 15]];

echo count(array_filter($emprestimos, $relatorio->filtro())), "\n";
```

```text
$ php relatorio.php
2
```

`$this->limiteEmDias` dentro da arrow function é o objeto `$relatorio`. A
closure **leva o objeto junto** — a função devolvida continua ligada a ele
depois que o método terminou.

Às vezes isso não é o que se quer. Uma closure que não precisa do objeto,
mas o carrega, mantém o objeto vivo na memória enquanto ela existir. Para
dizer que ela não usa `$this`, existe `static`:

```php
public function filtroSemObjeto(): \Closure
{
    return static fn(array $e): bool => $e['dias'] > 14;
}
```

Uma closure `static` não recebe `$this`. Se tentar usar, quebra:

```text
Error: Using $this when not in object context
```

A regra prática: closure que usa o objeto, normal; closure que não usa,
`static`. No volume 2, o framework guarda closures por muito tempo — rotas,
eventos, filas —, e a closure que carrega um objeto sem precisar dele
carrega também tudo que ele segura.

## Fabricar funções

Uma função pode **devolver** uma closure. O resultado é uma fábrica: você
passa a configuração uma vez, e recebe uma função pronta para usar muitas.

A Márcia pediu o relatório de atrasados com cortes diferentes: mais de 7
dias para o aviso gentil, mais de 14 para a cobrança, mais de 30 para
bloquear o leitor. A primeira versão tinha três funções quase iguais. A
segunda tem uma que fabrica as três:

```php title="filtros.php" numbered
<?php

declare(strict_types=1);

function atrasadoMaisQue(int $dias): \Closure
{
    return fn(array $e): bool => $e['dias'] > $dias;
}

$paraAviso = atrasadoMaisQue(7);
$paraCobranca = atrasadoMaisQue(14);
$paraBloqueio = atrasadoMaisQue(30);

$emprestimos = [['dias' => 9], ['dias' => 20], ['dias' => 41]];

echo count(array_filter($emprestimos, $paraAviso)), "\n";
echo count(array_filter($emprestimos, $paraCobranca)), "\n";
echo count(array_filter($emprestimos, $paraBloqueio)), "\n";
```

```text
$ php filtros.php
3
2
1
```

Cada closure devolvida guardou o seu `$dias`. É o `use` por valor do
capítulo @cap:funcoes, só que a arrow function faz a captura sozinha, e
cada chamada de `atrasadoMaisQue` cria uma captura nova.

:::term Closure
Uma função junto com as variáveis que ela capturou onde foi criada — por
`use`, pela captura automática da arrow function, ou pelo `$this` do
objeto em que nasceu. Em PHP, é um objeto da classe `Closure`.

A fábrica de funções é o uso de closure que mais aparece em framework: uma
configuração vira uma função pronta.
:::

## Combinar regras

O relatório de cobrança precisava de mais de uma condição ao mesmo tempo:
atrasado mais de 14 dias, leitor não isento, livro que não seja da
referência. Três funções pequenas, e uma que combina:

```php title="combinar.php" numbered
<?php

declare(strict_types=1);

function todos(\Closure ...$regras): \Closure
{
    return function (array $e) use ($regras): bool {
        foreach ($regras as $regra) {
            if (!$regra($e)) {
                return false;
            }
        }
        return true;
    };
}

$paraCobrar = todos(
    fn(array $e): bool => $e['dias'] > 14,
    fn(array $e): bool => !$e['isento'],
    fn(array $e): bool => $e['colecao'] !== 'referencia',
);

$emprestimos = [
    ['dias' => 20, 'isento' => false, 'colecao' => 'geral'],
    ['dias' => 20, 'isento' => true, 'colecao' => 'geral'],
    ['dias' => 3, 'isento' => false, 'colecao' => 'geral'],
];

echo count(array_filter($emprestimos, $paraCobrar)), "\n";
```

```text
$ php combinar.php
1
```

`\Closure ...$regras` é um parâmetro **variádico**: os três pontos antes
do nome dizem que a função aceita quantos argumentos vierem naquela
posição, e os junta num array — aqui, um array de closures. É o mesmo
`...` do desempacotamento do capítulo @cap:arrays, no sentido contrário.
`todos` devolve uma closure nova que passa a entrega por cada regra e para
na primeira que recusa.

Cada regra continua pequena, com nome se precisar, testável sozinha. A
combinação é outra função. Acrescentar uma quarta condição é acrescentar um
argumento.

:::pitfall
Closure demais esconde o que o código faz. Uma cadeia de seis funções
anônimas encaixadas, cada uma devolvendo outra, é tão difícil de ler
quanto o laço de oitenta linhas que ela substituiu.

A régua: se a closure tem mais de três linhas, ou se alguém vai precisar
procurar por ela, ela ganha nome — uma função, ou um método de uma classe.
A closure anônima é para o que cabe numa linha e só faz sentido ali.
:::

## O que o volume 2 vai entregar assim

Três coisas do Laravel, que você vai escrever no volume 2, são exatamente
o que este capítulo mostrou:

```php
// uma rota: um caminho e a função que responde
Route::get('/saude', fn() => ['ok' => true]);

// um filtro de coleção: a mesma ideia do array_filter
$atrasados = $emprestimos->filter(fn($e) => $e->emAtraso());

// filtro opcional: a closure só roda se a condição valer
$consulta->when($cidade, fn($q) => $q->where('cidade', $cidade));
```

Nenhuma das três é sintaxe nova. São funções recebendo funções — e o
framework, do outro lado, guardando essas closures e chamando-as na hora
certa, como o `todos` deste capítulo guarda as regras e as chama por
entrega.

:::note Na sua carreira
Em revisão de código, `'nomeDaFuncao'` passado como texto é um dos poucos
padrões que dá para apontar sem conhecer o sistema: ele quebra com
namespace, some do "renomear" do editor e escapa da análise estática.
Trocar por `nomeDaFuncao(...)` é uma mudança de uma linha, sem risco, que
torna o código conferível. É uma boa primeira contribuição num projeto que
você ainda não conhece.
:::

:::tree title="Onde estamos agora"
acervo/
  src/
    Relatorios/
      filtros.php            # atrasadoMaisQue, todos
      RelatorioDeAtraso.php  # filtro() devolve closure
  scripts/
    atrasados.php            # estaAtrasado(...) no lugar do texto
:::

:::summary
- `callable` aceita texto com nome de função; o texto é procurado como nome
  global na hora de chamar e quebra com namespace.
- `nome(...)` e `$obj->metodo(...)` devolvem a função como `Closure`,
  resolvida onde está escrita.
- `\Closure` como tipo recusa texto e array; a barra é por causa do
  namespace.
- Closure criada num método carrega `$this`; `static fn` não carrega, e
  recusa `$this`.
- Função que devolve closure é uma fábrica: a configuração entra uma vez.
- Regras pequenas se combinam numa closure nova. Mais de três linhas, dê
  nome.
:::

:::checkpoint
Você passa funções a outras sem texto com nome, escreve uma fábrica de
filtros e uma função que combina regras, e reconhece, numa rota ou num
filtro do Laravel, uma closure fazendo o que você já faz à mão.
:::

:::exercise level=1
Diga o que cada linha faz num arquivo com `namespace CasaAmarela;` e uma
função `formatar()` declarada nele:

```php
array_map('formatar', $multas);
array_map(formatar(...), $multas);
array_map('strtoupper', $titulos);
```

:::answer
A primeira quebra: `'formatar'` é procurada como função global, e a
função se chama `CasaAmarela\formatar`.

A segunda funciona: `formatar(...)` é resolvida com o namespace do arquivo.

A terceira funciona, por um detalhe: `strtoupper` é uma função global do
PHP, e o texto a encontra. Mesmo assim, `strtoupper(...)` é a forma que o
PHPStan confere e que sobrevive a qualquer mudança no arquivo.
:::

:::exercise level=2
Escreva `algum(\Closure ...$regras): \Closure`, o irmão de `todos`, que
aceita a entrega se **qualquer** regra aceitar. Use-o para achar os
empréstimos atrasados mais de 30 dias **ou** de leitores com multa acima de
R$ 5,00.

:::answer
```php
function algum(\Closure ...$regras): \Closure
{
    return function (array $e) use ($regras): bool {
        foreach ($regras as $regra) {
            if ($regra($e)) {
                return true;
            }
        }
        return false;
    };
}

$paraRevisar = algum(
    atrasadoMaisQue(30),
    fn(array $e): bool => $e['multa_em_centavos'] > 500,
);
```

`atrasadoMaisQue(30)` já é uma closure — a fábrica devolveu. As duas
formas se misturam sem conversão. E `todos` e `algum` se combinam:
`todos(algum(...), naoIsento(...))`.
:::

:::exercise level=3
Esta classe registra ouvintes para o evento "empréstimo feito":

```php
final class Avisos
{
    private array $ouvintes = [];

    public function quando(\Closure $ouvinte): void
    {
        $this->ouvintes[] = $ouvinte;
    }

    public function disparar(array $emprestimo): void
    {
        foreach ($this->ouvintes as $o) {
            $o($emprestimo);
        }
    }
}
```

Um colega registra, dentro de um método do relatório mensal, que carrega
oito mil empréstimos na memória:

```php
$this->avisos->quando(fn($e) => error_log("emprestimo {$e['id']}"));
```

Diga o que essa linha mantém vivo, e corrija.

:::answer
A arrow function foi criada dentro de um método do relatório, e por isso
carrega `$this` — o relatório inteiro, com os oito mil empréstimos. Ela
fica guardada em `$ouvintes` enquanto `Avisos` existir. O relatório, que
deveria sumir da memória quando terminasse, fica preso a uma closure que
nem usa `$this`.

```php
$this->avisos->quando(
    static fn(array $e) => error_log("emprestimo {$e['id']}"),
);
```

`static` diz que a closure não precisa do objeto, e o PHP não o captura.
Num script que roda e termina, a diferença é pequena. Num processo que fica
de pé — o worker do volume 2 —, cada closure que carrega um objeto sem
precisar é memória que só cresce.
:::
