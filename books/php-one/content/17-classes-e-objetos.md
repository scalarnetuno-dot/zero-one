---
title: "Classes e objetos"
number: 17
slug: classes-e-objetos
part: p3
kicker: "O relatório mostrou um exemplar do livro nenhum. O dado estava certo no banco — o array é que tinha perdido a chave."
goal: >-
  Trocar o array associativo por um tipo com nome quando o formato é
  conhecido: declarar uma classe, criar objetos com construtor promovido,
  usar propriedades tipadas, comparar objetos e reconhecer quando o objeto
  não compensa.
---

:::story Um exemplar do livro nenhum
A Vera imprimiu o relatório dos exemplares em restauro para levar à reunião
da associação. Onze linhas. Na sexta, o tombo 2117 aparecia com o título em
branco.

— Que livro é esse?

— Esse é... — Dedé rolou a tela — ...nenhum.

— Como assim nenhum?

No banco, o 2117 era um *Vidas Secas* de capa dura, com o `livro_id` certo e
a chave estrangeira no lugar. O problema estava trinta linhas acima, no PHP.
O relatório montava um índice de títulos com uma consulta separada, e essa
consulta trazia só os livros de literatura.

O *Vidas Secas* estava classificado como didático desde 2011.

— E o sistema não reclamou?

— Reclamou. — Dedé abriu o log e leu em voz alta. — *Warning: Undefined
array key 431.*

— Isso apareceu na minha tela?

— Isso apareceu num arquivo que ninguém abre.
:::

## O array aceita qualquer chave

Um array associativo não tem formato. Ele aceita o que você pedir, e o que
você pedir errado.

```php title="chaves.php" numbered
<?php

$livro = ['id' => 12, 'titulo' => 'Dom Casmurro', 'ano' => 1899];

echo '[', $livro['titlo'], "]\n";
```

```text
Warning: Undefined array key "titlo" in /app/chaves.php on line 5
[]
```

Um aviso, um valor nulo e o programa segue. Se esse `echo` estiver dentro de
um relatório de onze linhas, o resultado é uma linha em branco no meio de
dez certas.

A escrita é pior, porque nem avisa:

```php
$livro['preco'] = 39.90;
$livro['titulo_'] = 'Dom Casmurro';
```

Silêncio nos dois casos. O array agora tem cinco chaves, duas delas
inventadas, e nada no programa sabe que isso é um problema.

:::key
O array é a estrutura certa quando o formato é **desconhecido ou variável**:
as linhas que voltaram de uma consulta, os filtros que o usuário marcou, uma
lista de qualquer tamanho.

Ele fica ruim quando o formato é **conhecido e repetido** — quando as mesmas
quatro chaves atravessam sete funções, e cada função precisa confiar que as
outras seis escreveram o nome certo.
:::

## Uma classe é um formato com nome

```php title="Livro.php" numbered
<?php

class Livro
{
    public string $titulo;
    public int $ano;
}
```

Três palavras novas, e nenhuma é complicada.

`class` declara um formato. `Livro` é o nome dele. Dentro das chaves estão
as **propriedades**: os campos que todo livro tem, cada um com o tipo que
aceita.

Criar um é `new`:

```php title="catalogo.php" numbered
<?php

require 'Livro.php';

$livro = new Livro();
$livro->titulo = 'Dom Casmurro';
$livro->ano = 1899;

echo $livro->titulo, "\n";
```

```text
Dom Casmurro
```

A seta `->` é como se chega numa propriedade. Não é ponto: em PHP o ponto
junta texto, e essa é a primeira coisa que a memória de quem vem de outra
linguagem insiste em errar.

:::term Classe e objeto
A **classe** é a ficha de catalogação em branco: diz quais campos existem e
o que cabe em cada um. O **objeto** é uma ficha preenchida.

Uma classe, muitos objetos. O molde não guarda dado nenhum; cada objeto
guarda os seus.
:::

Agora repita o erro da seção anterior:

```php
echo '[', $livro->titlo, "]\n";
```

```text
Warning: Undefined property: Livro::$titlo
in /app/catalogo.php on line 10
[]
```

Ainda é um aviso — mas note a diferença na mensagem: ela diz o nome da
classe. Não é mais "alguma chave em algum array": é `Livro::$titlo`, e a
classe `Livro` está num arquivo só, com as propriedades listadas em cinco
linhas.

E a escrita mudou de comportamento:

```php
$livro->preco = 39.90;
```

```text
Deprecated: Creation of dynamic property Livro::$preco is deprecated
in /app/catalogo.php on line 11
```

O PHP avisa que criar propriedade fora da lista é um recurso em extinção.
O array nunca avisou nada.

## O objeto que nasce pela metade

Existe um problema no código acima, e ele aparece quando alguém esquece uma
linha:

```php title="catalogo.php" numbered
<?php

require 'Livro.php';

$livro = new Livro();
$livro->titulo = 'Dom Casmurro';

echo $livro->ano;
```

```text
Fatal error: Uncaught Error: Typed property Livro::$ano must not be
accessed before initialization in /app/catalogo.php:8
```

Uma propriedade tipada não tem valor padrão. Ela não é `null`, não é `0`:
ela **não existe ainda**, e o PHP prefere parar a inventar um valor.

Isso é bom, e é insuficiente. O erro acontece na hora da leitura, que pode
ser trinta linhas — ou três telas — depois do lugar onde o objeto foi
montado errado.

O lugar certo de exigir os dados é o nascimento do objeto.

## O construtor

```php title="Livro.php" numbered
<?php

class Livro
{
    public string $titulo;
    public int $ano;

    public function __construct(string $titulo, int $ano)
    {
        $this->titulo = $titulo;
        $this->ano = $ano;
    }
}
```

`__construct` é um método com nome reservado: o PHP chama ele sozinho,
sempre que alguém escreve `new Livro(...)`, passando os argumentos adiante.

`$this` é o objeto em que o método está rodando naquele momento. Dentro do
construtor de um livro, `$this` é aquele livro — e `$this->titulo` é a
propriedade dele, não o parâmetro.

```php
$livro = new Livro('Dom Casmurro', 1899);
```

Agora o objeto nasce inteiro ou não nasce:

```php
$livro = new Livro('Dom Casmurro');
```

```text
Fatal error: Uncaught ArgumentCountError: Too few arguments
to function Livro::__construct(), 1 passed and exactly 2 expected
```

E nasce com os tipos certos:

```php
$livro = new Livro('Dom Casmurro', 'mil oitocentos');
```

```text
Fatal error: Uncaught TypeError: Livro::__construct():
Argument #2 ($ano) must be of type int, string given
```

:::pitfall
`'mil oitocentos'` foi recusado. `'1899'` não seria: um texto que *é* um
número inteiro passa pela porta e chega do outro lado convertido, como
`int(1899)`.

Isso é a conversão automática do PHP trabalhando onde você não pediu. Ela
não vai te salvar de receber `'1899'` de um formulário — vai te entregar o
inteiro certo, e essa é justamente a razão de você não perceber quando ela
entrega o errado.
:::

## O construtor em uma linha

Escrever o nome de cada propriedade três vezes — na declaração, no parâmetro
e na atribuição — é trabalho de datilógrafo. O PHP 8 resolve isso:

```php title="Livro.php" numbered
<?php

class Livro
{
    public function __construct(
        public string $titulo,
        public int $ano,
    ) {}
}
```

Isto faz **exatamente** o que a versão anterior fazia. Escrever `public`
antes do parâmetro diz ao PHP: declare essa propriedade e guarde esse valor
nela. As três linhas do corpo somem porque não sobrou nada para fazer.

A vírgula depois do último parâmetro é permitida e recomendada: acrescentar
um campo amanhã vira uma linha nova em vez de duas linhas alteradas.

:::term Promoção de propriedade
*Constructor property promotion*, no nome oficial. Está no PHP desde a
versão 8.0 e é a forma normal de escrever uma classe de dados hoje.

Você vai encontrar muito código com a versão longa — ela não está errada,
só é anterior. As duas produzem o mesmo objeto.
:::

## Um exemplar sem livro deixa de ser possível

Era essa a pergunta da Vera. No Sistema, um exemplar é um array, e um array
com a chave `livro_id` faltando é um array normal.

Com uma classe, o problema muda de lugar:

```php title="Exemplar.php" numbered
<?php

class Exemplar
{
    public function __construct(
        public int $tombo,
        public Livro $livro,
        public string $estado = 'bom',
    ) {}
}
```

Duas coisas a reparar.

A primeira: o tipo de `$livro` é `Livro`. Uma classe é um tipo tão válido
quanto `int` ou `string`, e o PHP fiscaliza do mesmo jeito.

A segunda: `$estado` tem `= 'bom'`, um valor padrão. Quem não informar,
recebe `'bom'` — que é o estado em que um exemplar entra no acervo. Padrão é
para o que tem resposta óbvia; `$tombo` e `$livro` não têm.

```php
$exemplar = new Exemplar(2117);
```

```text
Fatal error: Uncaught ArgumentCountError: Too few arguments to
function Exemplar::__construct(), 1 passed and exactly 2 expected
```

Não é mais uma questão de disciplina da equipe. É uma questão de o programa
rodar.

## Do banco para o objeto

As consultas continuam devolvendo arrays — é isso que o PDO faz, e está
certo: naquele ponto o formato ainda é o do banco.

A tradução acontece numa função, num lugar só:

```php title="acervo.php" numbered
<?php

require 'Livro.php';
require 'Exemplar.php';

function livroDeLinha(array $linha): Livro
{
    return new Livro($linha['titulo'], (int) $linha['ano']);
}
```

```php title="listar.php" numbered
<?php

require 'conexao.php';
require 'acervo.php';

$linhas = $pdo->query(
    'SELECT titulo, ano FROM livros ORDER BY titulo'
)->fetchAll();

$livros = [];

foreach ($linhas as $linha) {
    $livros[] = livroDeLinha($linha);
}

echo $livros[0]->titulo, "\n";
```

O `(int)` na conversão do ano não é decoração: o MySQL devolve números como
texto, e `'1899'` viraria `int` na porta do construtor de qualquer jeito.
Escrever a conversão deixa a intenção visível e faz o programa se comportar
igual no dia em que a tipagem ficar estrita.

:::key
A fronteira é sempre a mesma: **array até a tradução, objeto depois dela**.

Uma função que recebe `array $linha` e devolve um objeto é o único lugar do
programa que precisa saber como as colunas se chamam. Quando a coluna mudar
de nome, é lá que você vai.
:::

## Comparar objetos

Dois sinais, duas perguntas diferentes.

```php title="comparar.php" numbered
<?php

require 'Livro.php';

$a = new Livro('Dom Casmurro', 1899);
$b = new Livro('Dom Casmurro', 1899);
$c = $a;

var_dump($a == $b);
var_dump($a === $b);
var_dump($a === $c);
```

```text
bool(true)
bool(false)
bool(true)
```

- `==` pergunta: **são iguais?** Mesma classe e propriedades iguais uma a
  uma.
- `===` pergunta: **são o mesmo?** O mesmo objeto, não uma cópia com o mesmo
  conteúdo.

`$c = $a` não copiou nada. As duas variáveis apontam para o mesmo objeto, e
é por isso que `$a === $c` é verdadeiro.

:::pitfall
Para coisas que o banco identifica por `id`, nenhuma das duas perguntas é a
que você quer. Dois objetos `Leitor` carregados em momentos diferentes podem
ter o mesmo `id` e nomes diferentes — porque alguém corrigiu o cadastro no
meio.

`==` diria que são diferentes. `===` também. E são a mesma pessoa.

Quando a identidade vem de um `id`, compare o `id`.
:::

## `__toString`, e o atalho que cobra depois

Um objeto não vira texto sozinho:

```php
echo $livro;
```

```text
Fatal error: Uncaught Error: Object of class Livro could not be
converted to string
```

Você pode ensinar a ele:

```php title="Livro.php" numbered
<?php

class Livro
{
    public function __construct(
        public string $titulo,
        public int $ano,
    ) {}

    public function __toString(): string
    {
        return "{$this->titulo} ({$this->ano})";
    }
}
```

```text
$ php catalogo.php
Dom Casmurro (1899)
```

`__toString` é útil para log e mensagem de erro. É um dos vários métodos com
dois sublinhados na frente que o PHP chama sozinho em situações específicas.

E é aqui que convém parar.

:::pitfall
Existe um desses métodos, o `__get`, que intercepta a leitura de qualquer
propriedade que não exista e deixa você decidir o que devolver. Com ele, um
objeto volta a aceitar `$livro->titlo` sem reclamar.

Ou seja: ele desfaz, em quatro linhas, exatamente o que este capítulo
inteiro foi fazer. Um erro que o PHP apontava com nome e linha volta a ser
uma tela em branco.

Isso não quer dizer que `__get` nunca sirva. Quer dizer que ele é a resposta
para um problema bem específico, e que "não quero declarar as propriedades"
não é esse problema.
:::

## Quando o objeto não vale a pena

Nem toda estrutura merece uma classe, e a régua é a mesma do começo do
capítulo, ao contrário.

**Formato que você não controla.** O JSON de uma integração, um CSV cujas
colunas mudam a cada exportação, os filtros que vieram de um formulário. Aí
o array é honesto: o formato é mesmo variável, e fingir que não é só empurra
a surpresa para outro lugar.

**Classe que não recusa nada.** Se a classe tem seis propriedades públicas,
nenhuma regra, nenhum cálculo e nenhum tipo interessante, ela é um array com
mais linhas e uma ficha de catalogação. O ganho aparece quando o tipo
**impede** alguma coisa — como o `Exemplar` que não nasce sem `Livro`.

**Script de uma vez só.** O programa que roda uma tarde para conferir uma
importação não precisa de modelagem. Ele precisa acabar.

:::note Na sua carreira
"Vamos criar uma classe para isso" é uma proposta que costuma ser aceita sem
discussão e executada sem ganho — e, três meses depois, o projeto tem
quarenta classes que só guardam e devolvem.

Quando você propuser a troca, traga junto a falha concreta que ela impede.
"Uma classe `Exemplar` teria impedido o relatório em branco da sexta" é um
argumento. "Fica mais organizado" é uma preferência, e preferência não
sobrevive à primeira semana apertada.

O mesmo vale ao contrário: quando alguém propuser, pergunte qual erro real
some. Se a resposta for demorada, a classe provavelmente ainda não tem
trabalho para fazer.
:::

:::tree title="Onde estamos agora"
acervo/
  composer.json
  composer.lock
  vendor/
  .gitignore
  Livro.php       # classe, com __toString
  Exemplar.php    # classe, exige um Livro
  acervo.php      # traduz linha do banco em objeto
  conexao.php
  multa.php
  listar.php
  buscar.php
  cadastrar.php
  emprestar.php
  devolver.php
  recibo.php
:::

:::summary
- Array não tem formato: aceita chave errada na leitura com um aviso e na
  escrita em silêncio.
- `class` declara um formato com nome; `new` cria um objeto; `->` chega numa
  propriedade.
- Propriedade tipada não tem valor padrão — ler antes de atribuir é erro
  fatal, e isso é a favor.
- `__construct` é chamado pelo `new`; `$this` é o objeto que está rodando.
- Promoção de propriedade escreve o construtor e as propriedades numa
  declaração só.
- Uma classe é um tipo: `Exemplar` pode exigir um `Livro`, e o PHP cobra.
- Array até a tradução, objeto depois dela — e a tradução mora num lugar só.
- `==` compara conteúdo, `===` compara identidade; para entidade com `id`,
  compare o `id`.
- Classe sem regra nenhuma é array com mais linhas.
:::

:::checkpoint
Você declara uma classe com construtor promovido, cria objetos a partir das
linhas do banco, sabe por que um `Exemplar` não pode nascer sem `Livro`,
distingue `==` de `===` entre objetos e consegue defender — ou recusar — a
troca de um array por uma classe com um exemplo concreto.
:::

:::exercise level=1
Escreva a classe `Leitor` com `nome` (texto), `documento` (texto) e
`cadastroEm` (texto no formato `Y-m-d`), usando construtor promovido.

Depois responda: por que `documento` é `string` e não `int`, se ele é uma
sequência de onze dígitos?

:::answer
```php title="Leitor.php" numbered
<?php

class Leitor
{
    public function __construct(
        public string $nome,
        public string $documento,
        public string $cadastroEm,
    ) {}
}
```

`documento` é texto porque **não é um número**: é um identificador feito de
dígitos. Dois testes rápidos separam uma coisa da outra.

O primeiro: faz sentido somar dois documentos? Não.

O segundo, mais prático: o CPF `012.345.678-90` guardado como inteiro vira
`12345678 90` sem o zero da frente, porque zero à esquerda não existe em
número. O acervo já teve esse problema com o `tombo` até alguém perceber que
os tombos antigos começavam por zero.
:::

:::exercise level=2
Pegue o `listar.php` da seção da tradução e acrescente a montagem de
`Exemplar` a partir de uma consulta com `JOIN`, usando a classe `Exemplar`
que exige um `Livro`.

A consulta:

```sql
SELECT e.tombo, e.estado, l.titulo, l.ano
FROM exemplares e
JOIN livros l ON l.id = e.livro_id
ORDER BY l.titulo
```

Depois imprima cada exemplar numa linha, usando o `__toString` do `Livro`.

:::answer
```php title="acervo.php" numbered
<?php

require 'Livro.php';
require 'Exemplar.php';

function exemplarDeLinha(array $linha): Exemplar
{
    return new Exemplar(
        (int) $linha['tombo'],
        new Livro($linha['titulo'], (int) $linha['ano']),
        $linha['estado'],
    );
}
```

```php title="listar.php" numbered
<?php

require 'conexao.php';
require 'acervo.php';

$sql = 'SELECT e.tombo, e.estado, l.titulo, l.ano
        FROM exemplares e
        JOIN livros l ON l.id = e.livro_id
        ORDER BY l.titulo';

foreach ($pdo->query($sql) as $linha) {
    $exemplar = exemplarDeLinha($linha);
    echo $exemplar->tombo, ' — ', $exemplar->livro, "\n";
}
```

```text
2117 — Vidas Secas (1938)
 843 — Dom Casmurro (1899)
```

O `echo $exemplar->livro` funciona porque o `Livro` tem `__toString`.

E repare no que sumiu: não existe mais um índice de títulos montado à parte,
que é de onde nasceu o relatório em branco. O `JOIN` traz o título junto com
o exemplar, e o construtor não deixa passar um sem o outro.
:::

:::exercise level=3
Este código roda sem erro e imprime algo inesperado. Diga o que ele imprime
e por quê, antes de rodar.

```php title="carrinho.php" numbered
<?php

require 'Livro.php';

$original = new Livro('Dom Casmurro', 1899);
$copia = $original;

$copia->ano = 1900;

echo $original->ano, "\n";
var_dump($original == $copia);
```

Depois, pesquise o que a palavra `clone` faz e explique por que ela também
não resolveria o caso em que `Livro` guardasse um objeto dentro.

:::answer
Imprime `1900` e `bool(true)`.

`$copia = $original` não copiou o objeto. Objetos são atribuídos por
referência: as duas variáveis apontam para o mesmo objeto, e mudar o ano por
uma das pontas muda pelas duas. Por isso `==` responde `true` — está
comparando o objeto com ele mesmo.

`clone $original` cria um objeto novo com as mesmas propriedades. Ele
resolve este caso: `$copia = clone $original` faria o `echo` imprimir
`1899`.

Onde ele não resolve: a cópia é **rasa**. Se `Livro` guardasse um objeto
`Editora` dentro, a cópia receberia a mesma `Editora` — não uma cópia dela.
Mudar o nome da editora pela cópia mudaria pelo original, e você teria o
mesmo problema um nível abaixo, agora mais difícil de enxergar.

A saída que evita a discussão inteira é um objeto que não muda depois de
criado. Sem alteração, cópia e original não têm como divergir.
:::
