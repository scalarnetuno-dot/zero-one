---
title: "Paginação, filtros e buscas"
number: 39
slug: paginacao-filtros-e-buscas
part: p8
kicker: "A busca por \"acafrao\" não encontrava \"Açafrão\". Metade do acervo tinha sido cadastrada em teclados de licitação, sem cedilha."
goal: >-
  Entregar uma listagem que aguenta o acervo inteiro: paginada com teto do
  servidor, ordenada de forma estável, filtrável sem escada de if, e com uma
  busca que encontra o livro que a pessoa digitou do jeito que deu.
---

:::story Só uma alteraçãozinha
— É só uma alteraçãozinha — disse Seu Juvenal, e Tainá, sem levantar os
olhos, virou uma página do caderno.

— A busca. Tem que achar por tudo. Título, autor, assunto. E o pessoal
digita sem acento, então tem que achar sem acento também.

— Sem acento como?

— Uma moça procurou "acafrao" ontem e não achou. Eu sei que tem, eu doei.

Dedé digitou na tela de homologação: `acafrao`. Zero resultados. Digitou
`açafrão`. Um resultado: *O Açafrão e Outras Especiarias*.

— Achou — disse Seu Juvenal.

— Com acento.

Vera, do balcão, sem se virar:

— Procura "acafrao" de novo, mas no Sistema.

Dedé abriu o Sistema de 2009. Digitou. Quatro resultados — o livro do Seu
Juvenal e três outros, todos com "acafrao" no título, sem cedilha e sem
til.

— Os computadores de 2012 vieram de uma licitação — disse Vera. — Teclado
americano. Durante dois anos ninguém conseguiu digitar cedilha. Eu cadastrei
uns mil e quinhentos livros assim.

— Então a busca precisa achar os dois jeitos nos dois sentidos — disse
Tainá. — Quem digita sem acento acha os com acento, e quem digita com
acento acha os sem.

Seu Juvenal sorriu.

— Viu? Alteraçãozinha.
:::

## Listagem sem limite é uma negação de serviço que você publicou

O `index` do capítulo @cap:o-crud-completo começou assim:

```php
return Livro::all();
```

Com quarenta livros, funciona. Com os quatro mil do acervo, a resposta tem
alguns megabytes, leva segundos para sair, e cada requisição carrega quatro
mil objetos na memória do servidor. Com oito mil exemplares e quinhentos mil
empréstimos no histórico, a rota de empréstimos derruba o processo.

E não é preciso má intenção. Basta o aplicativo carregar a lista ao abrir,
e cem pessoas abrirem o aplicativo às nove da manhã.

:::key
Toda rota que devolve uma coleção tem um **teto**, e quem decide o teto é o
servidor. Uma listagem sem teto é uma negação de serviço que você mesmo
publicou, esperando alguém chamar.
:::

## Três paginadores

O Laravel tem três formas de fatiar uma consulta, e cada uma responde a uma
pergunta diferente.

**`paginate`** traz a página e **conta o total**:

```php
Livro::orderBy('titulo')->paginate(20);
```

```sql
SELECT COUNT(*) AS aggregate FROM livros;
SELECT * FROM livros ORDER BY titulo LIMIT 20 OFFSET 40;
```

Duas consultas. O `meta` da resposta tem `total` e `last_page`, e o
aplicativo consegue mostrar "página 3 de 202".

**`simplePaginate`** traz a página e **não conta**:

```sql
SELECT * FROM livros ORDER BY titulo LIMIT 21 OFFSET 40;
```

Uma consulta. Ele pede 21 para saber se existe uma próxima página, e
devolve 20. O cliente sabe se há "próxima", mas não quantas páginas são.

**`cursorPaginate`** não usa `OFFSET`:

```sql
SELECT * FROM livros
WHERE (titulo, id) > ('Memórias Póstumas', 1832)
ORDER BY titulo, id LIMIT 21;
```

Ele guarda, num token opaco, o último registro da página atual, e pede "os
próximos depois deste". O `OFFSET` some.

| | `paginate` | `simplePaginate` | `cursorPaginate` |
|---|---|---|---|
| total e última página | sim | não | não |
| pular para a página 50 | sim | sim | não |
| custo na página 1 | médio | baixo | baixo |
| custo na página 2.000 | alto | alto | baixo |
| estável com inserções | não | não | sim |

Tabela: A coluna do meio raramente é a certa: ela tem o custo do `OFFSET`
sem a vantagem do total.

O custo alto do `OFFSET` na página distante é o que o `EXPLAIN` do capítulo
@cap:duas-tabelas-conversando mostraria: para devolver as linhas 40.000 a
40.020, o banco **lê e descarta** as primeiras 40.000. A página 1 é rápida,
e cada página seguinte é um pouco mais lenta que a anterior.

Para o acervo, que uma pessoa folheia e em que "página 3 de 202" ajuda,
`paginate`. Para o histórico de empréstimos de um leitor, que o aplicativo
rola infinitamente para baixo, `cursorPaginate`.

## Ordenação estável: o desempate que ninguém lembra

```php
Livro::orderBy('ano')->paginate(20);
```

Quarenta livros foram publicados em 1938. Página 1 mostra vinte deles;
página 2 mostra... **vinte deles**, possivelmente os mesmos.

Quando a coluna do `ORDER BY` tem valores repetidos, o banco não promete
nenhuma ordem entre os empates. Ele pode devolver os quarenta em uma ordem
na primeira consulta e em outra na segunda — e com `LIMIT` e `OFFSET`, isso
significa livro repetido numa página e livro sumido na outra.

A correção é sempre a mesma: **terminar o `ORDER BY` com uma coluna
única**.

```php
Livro::orderBy('ano')->orderBy('id')->paginate(20);
```

:::pitfall
Esse defeito não aparece em desenvolvimento. Com os quarenta livros da
factory, o MySQL tende a devolver os empates na ordem de inserção, todas as
vezes. Com o acervo real, depois de alguns meses de alterações e de um
`OPTIMIZE TABLE`, a ordem dos empates muda.

É o defeito da esteira vermelha do capítulo
@cap:testes-de-feature-http-e-banco, que passava em toda máquina local.
:::

## Filtro opcional sem escada de `if`

A listagem aceita filtros, todos opcionais:

```text
GET /api/livros?assunto=literatura&disponivel=1&ano_min=1900
```

A primeira versão costuma ser esta:

```php
$consulta = Livro::query();

if ($request->assunto) {
    $consulta->where('assunto', $request->assunto);
}

if ($request->ano_min) {
    $consulta->where('ano', '>=', $request->ano_min);
}

if ($request->disponivel) {
    $consulta->whereHas('exemplares', fn ($q) =>
        $q->where('estado', StatusExemplar::Bom));
}
```

Ela tem um defeito que o capítulo @cap:conversao-automatica já mostrou:
`if ($request->ano_min)` é falso quando `ano_min` é `0`. Para ano, ninguém
percebe. Para `?multa_min=0` ou `?disponivel=0`, o filtro some quando o
cliente pediu explicitamente zero.

O query builder tem um método para "aplique isto só se":

```php
$consulta = Livro::query()
    ->when(
        $request->filled('assunto'),
        fn ($q) => $q->where('assunto', $request->assunto),
    )
    ->when(
        $request->filled('ano_min'),
        fn ($q) => $q->where(
            'ano', '>=', $request->integer('ano_min'),
        ),
    )
    ->when(
        $request->has('disponivel'),
        fn ($q) => $request->boolean('disponivel')
            ? $q->whereHas('exemplaresDisponiveis')
            : $q->whereDoesntHave('exemplaresDisponiveis'),
    );
```

`filled` confere se o campo veio **e não está vazio** — e o `0` conta como
preenchido. `has` confere só se veio, o que permite distinguir
`?disponivel=0` ("só os indisponíveis") de nenhum filtro ("todos").

### O filtro ganha classe

Com cinco filtros, o controller volta a ficar grande. E os filtros são
**entrada**, então também precisam de validação. As duas coisas se resolvem
juntas — um Form Request que valida e entrega um objeto tipado:

```php title="app/Http/Requests/ListarLivrosRequest.php" numbered
class ListarLivrosRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'busca' => ['nullable', 'string', 'max:100'],
            'assunto' => ['nullable', 'string', 'max:40'],
            'disponivel' => ['nullable', 'boolean'],
            'ano_min' => ['nullable', 'integer', 'min:1400'],
            'sort' => ['nullable', Rule::in(FiltroDeLivros::ORDENS)],
            'por_pagina' => ['nullable', 'integer', 'between:1,100'],
        ];
    }

    public function filtro(): FiltroDeLivros
    {
        return new FiltroDeLivros(
            busca: $this->validated('busca'),
            assunto: $this->validated('assunto'),
            disponivel: $this->has('disponivel')
                ? $this->boolean('disponivel')
                : null,
            anoMin: $this->validated('ano_min'),
            ordem: $this->validated('sort') ?? 'titulo',
            porPagina: $this->validated('por_pagina') ?? 20,
        );
    }
}
```

```php title="app/Acervo/FiltroDeLivros.php" numbered
final readonly class FiltroDeLivros
{
    public const ORDENS = [
        'titulo', '-titulo', 'ano', '-ano', 'recentes',
    ];

    public function __construct(
        public ?string $busca,
        public ?string $assunto,
        public ?bool $disponivel,
        public ?int $anoMin,
        public string $ordem,
        public int $porPagina,
    ) {}
}
```

O `?bool $disponivel` tem três estados, e os três significam coisas
diferentes: `true`, `false` e "não filtrar". É a distinção entre `null` e
`false` do capítulo @cap:variaveis-e-tipos, com uma consequência de negócio.

E o model ganha um escopo que recebe o filtro inteiro:

```php title="app/Models/Livro.php" numbered
public function scopeFiltrar(
    Builder $q,
    FiltroDeLivros $f,
): void {
    $q->when($f->assunto, fn ($q, $a) =>
            $q->where('assunto', $a))
      ->when($f->anoMin !== null, fn ($q) =>
            $q->where('ano', '>=', $f->anoMin))
      ->when($f->disponivel !== null, fn ($q) =>
            $f->disponivel
                ? $q->whereHas('exemplaresDisponiveis')
                : $q->whereDoesntHave('exemplaresDisponiveis'))
      ->when($f->busca, fn ($q, $b) => $q->buscar($b))
      ->ordenarPor($f->ordem);
}
```

O controller fica com o tamanho que deveria ter:

```php title="app/Http/Controllers/LivroController.php" numbered
public function index(ListarLivrosRequest $request)
{
    $filtro = $request->filtro();

    $livros = Livro::filtrar($filtro)
        ->with('autores')
        ->paginate($filtro->porPagina)
        ->withQueryString();

    return LivroResource::collection($livros);
}
```

O `withQueryString()` faz os links de próxima e anterior página
carregarem os filtros. Sem ele, o link da página 2 perde o
`assunto=literatura`, e a pessoa que filtrou volta a ver o acervo inteiro.

## Busca por texto: `LIKE`, acento e o índice que não é usado

A busca da Casa Amarela procura um termo no título ou no nome do autor. A
forma direta:

```php
public function scopeBuscar(Builder $q, string $termo): void
{
    $q->where(fn ($q) => $q
        ->where('titulo', 'like', "%{$termo}%")
        ->orWhereHas('autores', fn ($q) =>
            $q->where('nome', 'like', "%{$termo}%")));
}
```

Duas coisas nesse trecho, uma boa e uma ruim.

A boa: o `where` interno com uma função agrupa as duas condições entre
parênteses. Sem ele, o `orWhere` escaparia dos outros filtros:

```sql
-- sem o agrupamento
WHERE assunto = 'literatura' AND titulo LIKE '%x%'
   OR EXISTS (autor LIKE '%x%')

-- com o agrupamento
WHERE assunto = 'literatura'
  AND (titulo LIKE '%x%' OR EXISTS (autor LIKE '%x%'))
```

A primeira devolve livros de **qualquer** assunto cujo autor bata com o
termo. É o `OR` fora de parênteses, o defeito de precedência do capítulo
@cap:operadores, agora em SQL.

A ruim: `LIKE '%termo%'` **não usa índice**. Um índice em `titulo` funciona
como a ordem alfabética de um dicionário, e permite achar o que **começa**
com uma palavra. Achar o que **contém** uma palavra no meio obriga o banco a
ler todas as linhas.

| Padrão | Usa índice? |
|---|---|
| `titulo = 'Dom Casmurro'` | sim |
| `titulo LIKE 'Dom%'` | sim |
| `titulo LIKE '%Casmurro%'` | não |

Tabela: O `%` no começo é o que mata o índice.

Com quatro mil livros, ler todas as linhas leva milissegundos e não importa.
Com quatro milhões, importa. A resposta para volume é o índice `FULLTEXT`
do MySQL, que quebra o texto em palavras e indexa cada uma:

```php
$t->fullText(['titulo']);
```

```php
$q->whereFullText('titulo', $termo);
```

Para o acervo da Casa Amarela, `LIKE` basta, e vale saber em que número ele
deixa de bastar. Medir é o assunto do capítulo @cap:cache-logs-e-medicao.

### O acento

O MySQL tem uma resposta pronta para o problema do Seu Juvenal, e ela mora
na **collation** da coluna — a regra que o banco usa para comparar texto:

```sql
SELECT 'acafrao' = 'Açafrão' COLLATE utf8mb4_0900_ai_ci;
-- 1
```

O `ai` é *accent insensitive*; o `ci`, *case insensitive*. Com essa
collation, `a` e `á` e `A` são iguais para comparação — e o `LIKE` também
passa a ignorar acento e caixa.

O Laravel cria as tabelas com `utf8mb4_unicode_ci` por padrão, que ignora
caixa e é **parcialmente** insensível a acento, com diferenças entre
versões do MySQL que já causaram muita tarde perdida. A decisão explícita é
declarar a collation na coluna que vai ser buscada:

```php title="..._ajustar_collation_de_titulo.php" numbered
Schema::table('livros', function (Blueprint $t) {
    $t->string('titulo', 200)
        ->collation('utf8mb4_0900_ai_ci')
        ->change();
});
```

:::pitfall
A collation resolve a comparação e **não resolve o que foi gravado**. Os
mil e quinhentos títulos da licitação continuam sem cedilha no banco, e a
tela continua mostrando "O Acafrao e Outras Especiarias" para quem
encontrar.

Corrigir o texto gravado é outro trabalho, manual, que a Vera faz aos
poucos, quando o livro passa pelo balcão. A busca parar de depender disso é
o que permite que ela faça aos poucos.

E um segundo cuidado: o teste que roda em SQLite não tem essa collation. A
busca sem acento passa no MySQL e falha no SQLite, ou o contrário. O
capítulo @cap:testes-de-feature-http-e-banco trata de onde o SQLite mente.
:::

## Ordenar por campo do cliente sem abrir o banco para ele

O cliente quer escolher a ordem: `?sort=-ano`. A tentação é passar direto:

```php
$q->orderBy($request->sort);
```

O Laravel escapa o nome da coluna, então isso não é injeção de SQL no
sentido clássico. Mas o cliente pode ordenar por **qualquer coluna** —
inclusive `observacao_interna`, ou `documento`, e deduzir pelo resultado o
que não deveria ver. Pode ordenar por uma coluna sem índice numa tabela
grande e fazer cada requisição custar um segundo.

A resposta é uma lista de permissão que traduz o nome do contrato para a
consulta:

```php title="app/Models/Livro.php" numbered
public function scopeOrdenarPor(Builder $q, string $ordem): void
{
    match ($ordem) {
        'titulo' => $q->orderBy('titulo'),
        '-titulo' => $q->orderByDesc('titulo'),
        'ano' => $q->orderBy('ano'),
        '-ano' => $q->orderByDesc('ano'),
        'recentes' => $q->orderByDesc('created_at'),
    };

    $q->orderBy('id');
}
```

O `match` do capítulo @cap:condicionais garante que um valor fora da lista
não passa em silêncio: ele lança `UnhandledMatchError`. Não chega a
acontecer, porque o `Rule::in` do Form Request já recusou com `422` — mas se
alguém um dia esquecer a validação, a consulta quebra em vez de ordenar
errado.

E o `orderBy('id')` no fim é o desempate da seção anterior, aplicado a
todas as ordens de uma vez.

:::key
O nome que o cliente usa para ordenar é **contrato**, não coluna. O
`recentes` do contrato é `created_at` hoje e pode ser `adquirido_em`
amanhã, sem que nenhum cliente perceba.
:::

## O teto é do servidor

O último parâmetro é `por_pagina`. O cliente pode pedir 10, 20, 50. E vai
pedir 999.999, por acidente ou não.

```text
GET /api/livros?por_pagina=999999
```

Duas respostas possíveis, e as duas são razoáveis:

**Recusar com `422`.** O `between:1,100` do Form Request faz isso. O
cliente sabe exatamente qual é o limite e ajusta.

**Limitar em silêncio.** `min($porPagina, 100)`. O cliente pediu um milhão
e recebeu cem, e o `meta.per_page` da resposta diz isso.

A Casa Amarela recusa, porque um aplicativo que pede 999.999 tem um defeito
que alguém precisa ver. O que não é aceitável é a terceira opção — obedecer.

:::note Na sua carreira
Paginação, filtro e ordenação são as partes da API que o cliente mais usa e
que menos aparecem na conversa de planejamento. Ninguém escreve "a listagem
precisa ter desempate" numa história de usuário.

É por isso que eles costumam ser o primeiro problema em produção de uma API
nova: não quebram no primeiro dia, quebram quando o volume chega. Se você
estiver revisando uma listagem, as quatro perguntas cabem num minuto: tem
teto? A ordem termina em coluna única? Os filtros tratam zero? O `sort` tem
lista de permissão?
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/Acervo/
    FiltroDeLivros.php          # objeto tipado, três estados
  app/Http/Requests/
    ListarLivrosRequest.php     # valida filtros e teto
  app/Models/
    Livro.php                   # scopes filtrar, buscar, ordenarPor
  database/migrations/
    ..._ajustar_collation_de_titulo.php
:::

:::summary
- Toda coleção tem teto, e o teto é do servidor.
- `paginate` conta o total; `simplePaginate` não conta; `cursorPaginate`
  dispensa o `OFFSET` e fica rápido em qualquer profundidade.
- `ORDER BY` em coluna com repetição precisa de desempate por coluna única,
  ou páginas perdem e repetem registros.
- `when` aplica filtro opcional sem escada de `if`; `filled` trata o zero
  como valor.
- Filtros são entrada: validam num Form Request e viajam num objeto
  tipado.
- `orWhere` fora de agrupamento escapa dos outros filtros.
- `LIKE '%x%'` não usa índice; `FULLTEXT` resolve volume.
- Collation `ai_ci` ignora acento e caixa na comparação, e não corrige o que
  foi gravado.
- O `sort` do cliente passa por lista de permissão que traduz contrato para
  coluna.
:::

:::checkpoint
Você entrega `GET /livros` com busca sem acento, filtros opcionais que
tratam zero, ordenação por lista de permissão com desempate, e teto de cem
por página — e sabe escolher entre os três paginadores para uma listagem
nova.
:::

:::exercise level=1
Qual paginador você usaria em cada caso, e por quê?

1. O histórico de empréstimos no aplicativo, com rolagem infinita.
2. A listagem do acervo no painel da Vera, com "página 3 de 202".
3. Uma exportação noturna que percorre os quinhentos mil empréstimos.

:::answer
1. `cursorPaginate`. A rolagem infinita não precisa de total nem de pular
   páginas, e o cursor não repete nem perde registro quando um empréstimo
   novo entra no topo enquanto a pessoa rola.
2. `paginate`. O total é o que a tela mostra, e pular para uma página é
   útil. O custo do `COUNT` sobre quatro mil livros é irrelevante.
3. Nenhum dos três. Exportação não é paginação de API: é o `chunkById` ou o
   `lazyById` do Eloquent, que percorrem a tabela em blocos usando o `id`
   como cursor, sem `OFFSET` e sem carregar tudo na memória.

O item 3 é o que pega. O instinto de usar `paginate` num laço de página em
página funciona, e fica mais lento a cada página, pela mesma razão do
`OFFSET` na página 2.000.
:::

:::exercise level=2
Esta busca de leitores está em produção. Encontre os quatro defeitos
relacionados ao capítulo.

```php
public function index(Request $request)
{
    $q = Leitor::query();

    if ($request->nome) {
        $q->where('nome', 'like', "%{$request->nome}%")
          ->orWhere('documento', $request->nome);
    }

    if ($request->bloqueado) {
        $q->whereNotNull('bloqueado_em');
    }

    return $q->orderBy($request->get('sort', 'nome'))
        ->paginate($request->get('por_pagina', 20));
}
```

:::answer
**Um: o `orWhere` sem agrupamento.** Se outros filtros forem acrescentados,
a busca por documento escapa deles. Hoje, o filtro de bloqueado já está
depois e é aplicado com `AND` sobre só uma metade do `OR`.

**Dois: `if ($request->bloqueado)`.** `?bloqueado=0` é falso, e o filtro
some — em vez de mostrar os não bloqueados, mostra todos.

**Três: `orderBy` com valor do cliente.** Qualquer coluna, inclusive
`documento` — e sem desempate, então leitores com o mesmo nome trocam de
página.

**Quatro: `por_pagina` sem teto.** `?por_pagina=999999` devolve a tabela
inteira de leitores, com dados pessoais, numa requisição.

E um quinto, fora do capítulo mas grave: a rota devolve o paginador de
models crus, sem resource. O documento de todos os leitores está na
resposta.

A versão corrigida segue o molde do `ListarLivrosRequest`: Form Request com
`between:1,100` e `Rule::in` para o `sort`, `when` com `has`/`boolean`, o
`OR` dentro de um `where(fn ...)`, e `LeitorResource::collection`.
:::

:::exercise level=3
A Vera quer uma ordenação nova: "os mais emprestados primeiro". Em
`/api/livros?sort=populares`.

Escreva o caso no `ordenarPor`, diga o que precisa existir no banco para
ele funcionar bem com o acervo inteiro, e responda: esse número deveria ser
calculado a cada requisição?

:::answer
A primeira versão, correta e ingênua:

```php
'populares' => $q
    ->withCount('emprestimos')
    ->orderByDesc('emprestimos_count'),
```

Isso exige um relacionamento `emprestimos` em `Livro` — um
`hasManyThrough` via exemplares, que é o caso em que o capítulo
@cap:relacionamentos disse que ele compensa.

**O custo.** O `withCount` vira uma subconsulta que conta empréstimos para
**cada livro do acervo** antes de ordenar, porque o banco não sabe quais
são os vinte mais populares sem contar todos. Com quinhentos mil
empréstimos, cada requisição conta quinhentos mil registros. O índice em
`emprestimos.exemplar_id` ajuda a subconsulta, e não evita a contagem
inteira.

**Deveria ser calculado a cada requisição? Não.** A popularidade muda
algumas dezenas de vezes por dia, e a listagem é consultada milhares. As
saídas são duas:

Uma coluna `total_emprestimos` em `livros`, incrementada a cada empréstimo
pelo evento do capítulo @cap:events-jobs-e-filas, com índice. A ordenação
vira `orderByDesc('total_emprestimos')`, instantânea.

Ou o cache do capítulo @cap:cache-logs-e-medicao, se "populares" for
sempre a mesma lista e a paginação não importar.

A primeira é melhor para ordenação, porque combina com filtros. E tem um
custo: a coluna é uma cópia de algo que já está nos empréstimos, e cópia
pode divergir. Um comando noturno que recalcula e compara é o seguro.
:::
