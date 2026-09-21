---
title: "Relacionamentos"
number: 35
slug: relacionamentos
part: p7
kicker: "A listagem do acervo levava quatro segundos. O log mostrou 143 consultas para mostrar 47 livros."
goal: >-
  Modelar as ligações do domínio com o tipo certo de relacionamento,
  reconhecer o N+1 contando consultas, e corrigi-lo provando a correção com
  o mesmo contador.
---

:::story Cento e quarenta e três
A tela do acervo demorava. Não travava — demorava, uns quatro segundos, o
suficiente para a Vera clicar de novo achando que não tinha pego.

Dedé tinha ligado o registro de consultas na semana anterior, por outro
motivo. Abriu o log depois de carregar a tela uma vez e rolou até o começo.

```text
$ grep -c "select" storage/logs/laravel.log
143
```

— Cento e quarenta e três consultas.

— Pra quantos livros?

— Quarenta e sete. É a primeira página.

Tainá fez a conta em voz alta.

— Quarenta e sete vezes três, mais duas.

— Mais duas.

— E o que são as três?

— Autor, exemplares e empréstimos abertos. Uma por livro, uma de cada vez.
:::

## A chave estrangeira mora do lado que tem muitos

Antes de qualquer código, a pergunta que decide tudo: **quem aponta para
quem?**

Um livro tem vários exemplares; um exemplar pertence a um livro. A coluna
`livro_id` está em `exemplares`, porque é lá que existem muitos. O contrário
exigiria uma coluna com uma lista dentro, que é o que o modelo relacional
não faz.

| Do lado da tabela | No model | Quem tem a coluna |
|---|---|---|
| um livro tem vários exemplares | `hasMany` | `exemplares` |
| um exemplar pertence a um livro | `belongsTo` | `exemplares` |

Tabela: Os dois métodos descrevem a **mesma** chave estrangeira, de pontos
de vista opostos. Quem tem a coluna usa `belongsTo`.

```php title="app/Models/Livro.php" numbered
public function exemplares(): HasMany
{
    return $this->hasMany(Exemplar::class);
}
```

```php title="app/Models/Exemplar.php" numbered
public function livro(): BelongsTo
{
    return $this->belongsTo(Livro::class);
}
```

O Laravel adivinha o nome da coluna a partir do nome do método e da classe:
`livro()` com `Livro::class` procura `livro_id`. Quando o nome fugir do
padrão, o segundo argumento diz qual é.

```php
$livro->exemplares;
```

```sql
SELECT * FROM exemplares WHERE livro_id = ?
```

```php
$exemplar->livro;
```

```sql
SELECT * FROM livros WHERE id = ? LIMIT 1
```

:::key
Repare que ler `$livro->exemplares` **dispara uma consulta**. Não é um campo:
é uma chamada com cara de propriedade.

Essa é a origem do problema deste capítulo, e a razão de o defeito ser
difícil de ver: ele não parece uma consulta. Parece um ponto.
:::

## Muitos para muitos

Um livro pode ter dois autores; um autor escreveu vários livros. Nenhuma das
duas tabelas pode guardar a coluna, então o relacionamento ganha uma tabela
própria:

```php title="..._create_autor_livro_table.php" numbered
Schema::create('autor_livro', function (Blueprint $t) {
    $t->foreignId('autor_id')->constrained();
    $t->foreignId('livro_id')->constrained();
    $t->string('papel', 20)->default('autor');
    $t->primary(['autor_id', 'livro_id']);
});
```

O nome `autor_livro` não é escolha: é a convenção — os dois nomes no
singular, em ordem alfabética, separados por sublinhado. Fugir dela custa
um argumento a mais em cada lado.

```php title="app/Models/Livro.php" numbered
public function autores(): BelongsToMany
{
    return $this->belongsToMany(Autor::class)
        ->withPivot('papel')
        ->withTimestamps();
}
```

```php
$livro->autores;
```

```sql
SELECT autores.*, autor_livro.livro_id AS pivot_livro_id,
       autor_livro.autor_id AS pivot_autor_id,
       autor_livro.papel AS pivot_papel
FROM autores
INNER JOIN autor_livro ON autores.id = autor_livro.autor_id
WHERE autor_livro.livro_id = ?
```

:::pitfall
Sem o `withPivot('papel')`, a coluna existe na tabela, é gravada
corretamente e **não vem** na consulta. `$livro->autores->first()->pivot->papel`
devolve `null`, e nada reclama.

O `withPivot` é a lista do que a tabela do meio devolve. É o mesmo
comportamento do `$fillable`, na outra direção: o Laravel só traz o que
você declarou.

Quando a tabela do meio ganha colunas — papel, ordem, data, quem cadastrou —
ela deixou de ser uma ligação e virou uma entidade. Aí vale considerar um
model próprio para ela, em vez de empurrar tudo para o pivô.
:::

Para gravar:

```php
$livro->autores()->attach($autor->id, ['papel' => 'tradutor']);
$livro->autores()->detach($autor->id);
$livro->autores()->sync([3, 7, 12]);
```

O `sync` é o que mais assusta: ele deixa a lista **exatamente** como você
mandou, removendo o que não estiver ali. É o certo para um formulário com
caixas de seleção, e é uma perda de dados quando usado achando que
acrescenta.

## N+1: cem consultas atrás de um ponto

```php title="app/Http/Controllers/AcervoController.php" numbered
$livros = Livro::orderBy('titulo')->paginate(47);

foreach ($livros as $livro) {
    echo $livro->titulo;
    echo $livro->autores->pluck('nome')->join(', ');
    echo $livro->exemplares->count();
}
```

Cada `$livro->autores` e cada `$livro->exemplares` dispara a sua própria
consulta. Para 47 livros:

| Consultas | De onde vêm |
|---|---|
| 1 | a contagem do `paginate` |
| 1 | a lista de livros |
| 47 | os autores, um livro por vez |
| 47 | os exemplares, um livro por vez |
| 47 | os empréstimos abertos, um livro por vez |
| **143** | |

Tabela: É a conta que a Tainá fez em voz alta. O nome disso é **N+1**: uma
consulta para trazer a lista, mais uma por item.

:::term N+1
O padrão em que uma consulta que traz N registros provoca N consultas
adicionais, uma para cada.

Ele não dá erro, não aparece em teste com três registros e cresce
linearmente com o banco. É o defeito de desempenho mais comum de qualquer
projeto com ORM, em qualquer linguagem.
:::

## `with`, `load` e `withCount`

A correção é dizer **antes** o que você vai precisar:

```php
$livros = Livro::with(['autores', 'exemplares'])
    ->withCount('exemplares')
    ->orderBy('titulo')
    ->paginate(47);
```

```sql
SELECT COUNT(*) FROM livros;

SELECT *, (SELECT COUNT(*) FROM exemplares
           WHERE exemplares.livro_id = livros.id) AS exemplares_count
FROM livros ORDER BY titulo ASC LIMIT 47 OFFSET 0;

SELECT autores.*, ... FROM autores
INNER JOIN autor_livro ON ...
WHERE autor_livro.livro_id IN (1, 2, 3, ..., 47);

SELECT * FROM exemplares WHERE livro_id IN (1, 2, 3, ..., 47);
```

Quatro consultas. O Laravel traz a lista, junta os identificadores e busca
os relacionados de uma vez, com `IN`.

| | Antes | Depois |
|---|---|---|
| consultas | 143 | 4 |
| tempo | ~4 s | ~40 ms |

Tabela: E o número **para de crescer** com o tamanho da página. Com 200
livros por página continuam sendo quatro.

Três métodos, três momentos:

**`with()`** carrega junto, antes de a coleção existir. É o normal.

**`load()`** carrega depois, num objeto que você já tem em mãos. Serve
quando a decisão de precisar do relacionamento vem depois da consulta.

**`withCount()`** traz só o número, sem os registros. Para mostrar "3
exemplares", trazer os três é desperdício.

:::pitfall
O N+1 mais difícil de achar não está no controller: está na **serialização**.

Um resource que faz `'autores' => $this->autores->pluck('nome')` dispara a
consulta no momento em que a resposta é montada — depois de o controller ter
terminado, longe de onde alguém procuraria.

É por isso que a ferramenta de diagnóstico é o contador de consultas, e não
a leitura do controller.
:::

## A proteção que transforma o N+1 em erro

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    Model::preventLazyLoading(! $this->app->isProduction());
}
```

Com isso, ler um relacionamento que não foi carregado **lança exceção** fora
de produção:

```text
Attempted to lazy load [autores] on model [App\Models\Livro]
but lazy loading is disabled.
```

O efeito é transformar um problema de desempenho, que ninguém vê, num erro
de desenvolvimento, que ninguém consegue ignorar. É a mesma ideia do
`preventSilentlyDiscardingAttributes` do capítulo anterior, aplicada a outro
silêncio.

Em produção ele fica desligado de propósito: uma consulta a mais é melhor
que uma tela quebrada.

## Um pulo a mais, e o polimórfico

Um leitor tem empréstimos; cada empréstimo é de um exemplar; cada exemplar é
de um livro. Para chegar de leitor a livro são dois pulos, e existe um
método que os faz de uma vez.

Ele vale a pena quando a pergunta é feita com frequência — "quais livros
este leitor já levou?" — e não vale quando aparece uma vez num relatório. Na
dúvida, escreva a consulta com `JOIN`, que você sabe ler.

O relacionamento **polimórfico** é para quando o mesmo tipo de registro
aponta para coisas diferentes: um comentário que pode ser sobre um livro ou
sobre um autor, um anexo que pode pertencer a qualquer coisa.

Ele resolve um problema real e cobra caro: a coluna que guarda o tipo é
texto, não há chave estrangeira possível, e o banco deixa de garantir a
integridade que garantia. Use quando o ganho for claro — e saiba que a
conferência passou a ser sua.

## Apagar em cascata

```php
$t->foreignId('livro_id')->constrained()->cascadeOnDelete();
```

Isso diz ao banco: apagar um livro apaga os exemplares dele. E, se os
empréstimos também estiverem em cascata, apaga o histórico junto.

:::pitfall
Apagar um livro do acervo não deveria apagar o registro de que a Dona
Marlene levou aquele exemplar em 2019.

Empréstimo é um **fato histórico**. A prestação de contas do edital conta
empréstimos, e um livro removido do acervo não desfaz o que aconteceu.

Para entidades com histórico, a exclusão certa quase nunca é a física. O
Laravel oferece a lógica:

```php
use Illuminate\Database\Eloquent\SoftDeletes;

class Livro extends Model
{
    use SoftDeletes;
}
```

O `delete()` passa a preencher uma coluna `deleted_at`, e todas as consultas
passam a ignorar quem a tem preenchida. O registro sai das telas e continua
no banco, junto com tudo que aponta para ele.
:::

A cascata continua sendo a escolha certa para o que é **parte** de outra
coisa e não tem vida própria: os itens de um pedido, as opções de uma
enquete, as linhas de uma configuração.

:::note Na sua carreira
"A tela está lenta" é um relato, não um diagnóstico — e a diferença entre
quem resolve em dez minutos e quem passa a tarde é ter um número antes de
ter uma hipótese.

Conte as consultas primeiro. Se forem dezenas para uma tela, é N+1, e a
correção é uma linha. Se forem três consultas levando quatro segundos, é
índice ou volume, e a correção é outra. As duas parecem iguais para quem
está esperando a tela carregar.

E vale como resposta em entrevista: quando perguntarem o que você faz com
uma página lenta, "eu meço antes" é uma resposta melhor que qualquer lista
de otimizações.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/Models/
    Livro.php        # hasMany exemplares, belongsToMany autores
    Autor.php
    Exemplar.php     # belongsTo livro, hasMany emprestimos
    Leitor.php       # hasMany emprestimos
    Emprestimo.php   # belongsTo exemplar, belongsTo leitor
  database/migrations/
    ..._create_autores_table.php
    ..._create_autor_livro_table.php
:::

:::milestone
Fim da Parte 7. O acervo tem models com tipos, escopos e relações; as
consultas que o ORM produz são as mesmas que você escreveria à mão; e a
listagem que levava quatro segundos leva quarenta milissegundos, com a
prova contada em consultas.
:::

:::summary
- A chave estrangeira mora na tabela que tem muitos; quem tem a coluna usa
  `belongsTo`.
- Ler um relacionamento dispara consulta: é uma chamada com cara de
  propriedade.
- Muitos para muitos usa tabela do meio com nome convencionado — os dois
  singulares em ordem alfabética.
- `withPivot` declara quais colunas da tabela do meio voltam; sem ele, elas
  chegam nulas em silêncio.
- `sync` deixa a lista exatamente como mandada, removendo o resto.
- N+1 é uma consulta para a lista mais uma por item; não dá erro e cresce
  com o banco.
- `with` carrega antes, `load` carrega depois, `withCount` traz só o número.
- O N+1 mais escondido está na serialização, não no controller.
- `preventLazyLoading` transforma o problema silencioso em erro fora de
  produção.
- Cascata serve para o que é parte de outra coisa; histórico pede exclusão
  lógica.
:::

:::checkpoint
Você modela relacionamentos nos dois sentidos e o muitos-para-muitos com
atributos, identifica um N+1 contando consultas em vez de lendo código,
corrige com `with` e `withCount`, e prova a correção com o mesmo contador.
:::

:::exercise level=1
Diga qual relacionamento declarar em cada model, e em qual tabela fica a
chave estrangeira:

1. Um leitor tem vários empréstimos.
2. Um empréstimo tem uma multa; a multa pertence a um empréstimo.
3. Um exemplar passou por vários empréstimos.

:::answer
1. `Leitor::emprestimos()` é `hasMany`; `Emprestimo::leitor()` é
   `belongsTo`. A coluna `leitor_id` fica em `emprestimos`.
2. `Emprestimo::multa()` é `hasOne`; `Multa::emprestimo()` é `belongsTo`. A
   coluna `emprestimo_id` fica em `multas` — do lado que aponta, mesmo sendo
   um para um.
3. `Exemplar::emprestimos()` é `hasMany`; `Emprestimo::exemplar()` é
   `belongsTo`. A coluna `exemplar_id` fica em `emprestimos`.

O caso 2 é o que confunde. Num relacionamento de um para um, os dois lados
poderiam ter a coluna, e a escolha é de desenho: ela fica do lado
**opcional**. Nem todo empréstimo gera multa, então `emprestimos` não deve
carregar uma coluna quase sempre nula apontando para uma linha que não
existe.
:::

:::exercise level=2
Esta tela mostra os empréstimos em aberto com o nome do leitor, o título do
livro e o tombo. Ela faz N+1 duplo.

```php
$emprestimos = Emprestimo::whereNull('devolvido_em')->get();

foreach ($emprestimos as $e) {
    echo $e->leitor->nome;
    echo $e->exemplar->livro->titulo;
    echo $e->exemplar->tombo;
}
```

Conte as consultas para 30 empréstimos, corrija e conte de novo.

:::answer
**Antes.** Uma para a lista. Trinta para os leitores. Trinta para os
exemplares. E trinta para os livros — porque `$e->exemplar->livro` só
acontece depois que o exemplar chegou.

Total: **91 consultas**.

**A correção** precisa carregar dois níveis, e a notação é o ponto:

```php
$emprestimos = Emprestimo::whereNull('devolvido_em')
    ->with(['leitor', 'exemplar.livro'])
    ->get();
```

**Depois.** Uma para os empréstimos. Uma para os leitores, com `IN`. Uma
para os exemplares, com `IN`. Uma para os livros, com `IN`.

Total: **4 consultas**, e o número não muda com trezentos empréstimos.

O `exemplar.livro` é a parte que se esquece: carregar `exemplar` sozinho
resolve dois terços do problema e deixa o terceiro N+1 no lugar — que é
pior que não ter corrigido nada, porque agora parece resolvido.
:::

:::exercise level=3
A associação pediu para "limpar o acervo": remover os livros que não são
emprestados há mais de dez anos.

Escreva a consulta que encontra esses livros e responda: o que exatamente
acontece com os exemplares e com o histórico de empréstimos em cada uma das
três opções — cascata física, exclusão lógica, e uma terceira que você
proponha?

:::answer
**A consulta:**

```php
$candidatos = Livro::whereDoesntHave(
    'exemplares.emprestimos',
    fn ($q) => $q->where('retirado_em', '>=', now()->subYears(10)),
)->get();
```

`whereDoesntHave` vira um `NOT EXISTS` com subconsulta — e repare que ele
inclui os livros que **nunca** foram emprestados, o que provavelmente é
desejado e precisa ser confirmado com a Vera antes de rodar.

**Cascata física.** Apaga o livro, os exemplares e, se a cascata continuar,
os empréstimos. O relatório de "mais emprestados de 2019" passa a devolver
números diferentes dos que foram impressos em 2019. É a pior opção, e é a
que parece mais limpa.

**Exclusão lógica.** O livro ganha `deleted_at`, some das telas e das
consultas. Os empréstimos continuam, mas apontam para um livro que as
consultas normais não trazem — então o relatório histórico passa a mostrar
linhas com título em branco, que é o defeito do capítulo
@cap:classes-e-objetos voltando.

Resolve-se, mas exige que os relatórios históricos peçam explicitamente os
registros removidos. É uma decisão que precisa estar escrita em algum lugar.

**A terceira: não apagar.** O que a associação quer não é remover o
registro; é parar de mostrar o livro na tela de quem procura o que levar
para casa. Isso é um **estado**, não uma exclusão:

```php
$livro->update(['situacao' => SituacaoLivro::Desativado]);
```

O acervo ativo filtra por situação. O histórico continua completo, o título
continua aparecendo nos relatórios, e a operação tem volta — alguém pode
reativar o livro na semana seguinte sem restaurar backup.

A pergunta que leva a essa resposta, e que vale para quase todo pedido de
"apagar": **o que a pessoa quer parar de ver, e por quanto tempo?**
:::
