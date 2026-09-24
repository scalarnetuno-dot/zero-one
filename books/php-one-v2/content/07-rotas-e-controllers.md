---
title: "Rotas e controllers"
number: 7
slug: rotas-e-controllers
part: p2
kicker: "O índice do Sistema tinha 137 linhas, e cada linha era um nome de arquivo. Ninguém nunca leu esse índice inteiro."
goal: >-
  Registrar as rotas da API desenhadas antes, com nome, restrição e busca
  automática do registro — mantendo os controllers pequenos e sabendo
  justificar o formato escolhido para cada um.
---

:::story Cento e trinta e sete
Tainá tentou desenhar o mapa do Sistema para entender o que faltava
migrar. Começou listando as telas.

```text
$ ls *.php | wc -l
137
```

— Cento e trinta e sete telas?

— Cento e trinta e sete arquivos — disse Dedé. — Alguns são tela, alguns
são pedaço de tela, e uns quinze não são chamados por ninguém.

— Como a gente sabe quais quinze?

Dedé ficou um tempo olhando a lista.

— A gente não sabe. Ninguém apaga porque ninguém tem certeza.
:::

## O arquivo de rotas é o índice

No Sistema, o índice da aplicação é a saída do `ls`. Num projeto Laravel, é
um arquivo que alguém escreveu de propósito — e é a diferença entre saber o
que existe e adivinhar.

O esqueleto vem com `routes/web.php` e `routes/console.php`. O arquivo de
API não vem: ele é instalado quando você precisa dele.

```text
$ php artisan install:api
```

```text
   INFO  API scaffolding installed. Please add the
   [Laravel\Sanctum\HasApiTokens] trait to your User model.
```

O comando cria `routes/api.php`, registra o arquivo no `bootstrap/app.php` e
instala o pacote de autenticação por token.

## `web.php` e `api.php`: dois mundos

Os dois arquivos existem porque atendem clientes diferentes, e a diferença
não é organizacional — é de comportamento.

| | `web.php` | `api.php` |
|---|---|---|
| prefixo na URL | nenhum | `/api` |
| sessão e cookie | sim | não |
| proteção CSRF | sim | não faz sentido |
| quem consome | navegador | aplicativo, script, outro sistema |
| erro devolve | página HTML | JSON |

Tabela: Uma rota no arquivo errado não dá erro. Ela se comporta de um jeito
que ninguém explica — uma API que exige token de formulário, ou uma tela que
perde o login a cada clique.

:::key
A pergunta que decide o arquivo não é "isso devolve JSON?". É: **quem chama
isso tem uma sessão aberta num navegador?**

O painel da Vera tem. O aplicativo do leitor não tem — ele carrega a
credencial em cada requisição, como o capítulo @cap:o-que-e-http descreveu.
:::

## As rotas da Casa Amarela

O desenho do capítulo @cap:o-que-e-uma-api-rest, agora escrito:

```php title="routes/api.php" numbered
<?php

declare(strict_types=1);

use App\Http\Controllers\DevolucaoController;
use App\Http\Controllers\EmprestimoController;
use App\Http\Controllers\ExemplarController;
use App\Http\Controllers\LivroController;
use Illuminate\Support\Facades\Route;

Route::apiResource('livros', LivroController::class);

Route::get('livros/{livro}/exemplares', [
    ExemplarController::class, 'porLivro',
])->name('livros.exemplares');

Route::post('emprestimos', [EmprestimoController::class, 'store'])
    ->name('emprestimos.store');

Route::post(
    'emprestimos/{emprestimo}/devolucao',
    DevolucaoController::class,
)->name('emprestimos.devolucao');
```

```text
$ php artisan route:list --path=api
```

```text
  GET|HEAD   api/livros ................... livros.index
  POST       api/livros ................... livros.store
  GET|HEAD   api/livros/{livro} ........... livros.show
  PUT|PATCH  api/livros/{livro} ........... livros.update
  DELETE     api/livros/{livro} ........... livros.destroy
  GET|HEAD   api/livros/{livro}/exemplares  livros.exemplares
  POST       api/emprestimos .............. emprestimos.store
  POST       api/emprestimos/{emprestimo}/devolucao
                                           emprestimos.devolucao
```

Quatro linhas de arquivo viraram oito rotas, e a tabela acima é o índice que
o Sistema nunca teve.

`Route::apiResource` registra as cinco operações de um recurso de uma vez.
Ele é irmão do `Route::resource`, que registra sete — as duas extras
devolvem formulários HTML, e API não tem formulário.

## Parâmetros e restrições

`{livro}` casa com qualquer coisa que não seja barra. Isso é generoso demais
quando o parâmetro é um número:

```php
Route::get('livros/{livro}', [LivroController::class, 'show'])
    ->whereNumber('livro');
```

Agora `/api/livros/abc` não casa com essa rota, e o `404` acontece no
roteador — antes de existir uma consulta ao banco com um texto no lugar de
um identificador.

:::pitfall
A ordem das rotas importa, e o defeito é silencioso.

```php
Route::get('livros/{livro}', [LivroController::class, 'show']);
Route::get('livros/destaques', [LivroController::class, 'destaques']);
```

A segunda rota nunca roda. O roteador testa na ordem em que foram
registradas, e `destaques` casa com `{livro}` — então a aplicação vai
procurar um livro cujo identificador é a palavra `destaques`, e devolver
`404` para uma rota que existe.

Duas saídas: **caminho fixo antes de caminho com parâmetro**, sempre; ou
restringir o parâmetro, o que resolve os dois problemas com uma linha.
:::

## O parâmetro que já vem virado registro

O controller poderia receber o número e buscar o livro:

```php
public function show(int $id)
{
    $livro = Livro::findOrFail($id);
    // ...
}
```

Três linhas iguais a essas em cada método, em cada controller. O Laravel
oferece outro caminho: se o nome do parâmetro da rota casar com o nome do
parâmetro do método, e o tipo for um model, ele busca sozinho.

```php
public function show(Livro $livro)
{
    return $livro;
}
```

```text
GET /api/livros/12   → o livro 12
GET /api/livros/999  → 404, sem entrar no método
```

:::term Route model binding
O framework lê o tipo do parâmetro, busca o registro pela chave primária e
entrega o objeto pronto. Quando não encontra, devolve `404` antes de chamar
o seu código.

É conveniência com um efeito colateral bom: o `404` de registro inexistente
passa a ser tratado num lugar só, em vez de depender de cada método lembrar.
:::

Dá para buscar por outra coluna, quando o identificador público não é o
número:

```php
Route::get('exemplares/{exemplar:tombo}', ...);
```

Aí o `{exemplar:tombo}` procura pela coluna `tombo`, que é o número colado
na etiqueta e o que a Vera digita.

## Nome de rota: a URL que muda sem quebrar nada

Toda rota do exemplo tem `->name()`, e o `apiResource` gera os nomes
sozinho. O ganho aparece quando alguém precisa montar uma URL:

```php
route('livros.show', ['livro' => 12]);
// http://localhost:8000/api/livros/12
```

Em vez de escrever o caminho à mão em dezessete lugares. No dia em que
`/api/livros` virar `/api/acervo`, os dezessete continuam funcionando, e o
`route:list` continua sendo o índice.

O nome também é o que permite referenciar a rota em outros pontos do
framework — redirecionamento, autorização, e o cabeçalho `Location` de um
`201`.

## Três formatos de controller, e o que cada um comunica

```text
$ php artisan make:controller LivroController --api
```

**Controller de recurso** agrupa as operações de um substantivo. Os nomes
dos métodos são convenção — `index`, `store`, `show`, `update`, `destroy` —
e quem abrir o arquivo já sabe o que vai encontrar.

```php title="app/Http/Controllers/LivroController.php" numbered
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Models\Livro;

class LivroController extends Controller
{
    public function index()
    {
        return Livro::query()->orderBy('titulo')->paginate(20);
    }

    public function show(Livro $livro)
    {
        return $livro;
    }
}
```

**Controller invocável** tem um método só, o `__invoke`, e é registrado
pelo nome da classe. Ele comunica uma coisa: *esta classe faz uma ação, e só
uma*.

```php title="app/Http/Controllers/DevolucaoController.php" numbered
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Models\Emprestimo;
use App\Services\RegistroDeDevolucao;
use Illuminate\Http\Request;

class DevolucaoController extends Controller
{
    public function __construct(
        private readonly RegistroDeDevolucao $devolucoes,
    ) {}

    public function __invoke(Request $req, Emprestimo $emprestimo)
    {
        $this->devolucoes->registrar(
            $emprestimo,
            $req->string('estado', 'bom')->toString(),
        );

        return response()->noContent();
    }
}
```

**Controller comum**, com métodos de nome livre, é o que sobra: útil quando
as ações não formam um recurso nem são uma só.

:::key
A escolha entre os três é uma mensagem para quem lê depois.

Recurso diz "aqui moram as operações de um substantivo". Invocável diz "esta
é uma ação isolada, com nome próprio". Comum não diz nada — e por isso é o
que se usa quando não há nada a dizer.
:::

## O controller não precisa saber de tudo

Repare no `DevolucaoController`: ele recebe o empréstimo pronto, chama um
serviço e devolve `204`. Sete linhas úteis.

É esse o tamanho certo. Um controller tem três trabalhos, e nenhum deles é
regra de negócio:

1. **traduzir a requisição** em argumentos;
2. **chamar quem sabe fazer**;
3. **traduzir o resultado** em resposta.

:::pitfall
O sintoma de que a regra vazou para o controller é o construtor:

```php
public function __construct(
    private Calculadora $calc,
    private Estoque $estoque,
    private Notificador $notificador,
    private Auditoria $auditoria,
    private Relatorio $relatorio,
    private Cache $cache,
    private Fila $fila,
    private Log $log,
) {}
```

Oito dependências não são um problema de injeção. São o aviso de que esse
controller está orquestrando um processo de negócio — e processo de negócio
tem nome, tem teste próprio e não depende de HTTP para existir.

A correção não é diminuir a lista: é mover o processo para uma classe que o
controller chama com uma linha.
:::

E lógica **dentro do arquivo de rotas** é a mesma doença, um andar acima.
Uma função anônima com quinze linhas em `routes/api.php` não tem teste, não
tem nome e impede o `route:cache` — que recusa rotas com função anônima,
porque não há como guardar uma função num arquivo de cache.

:::note Na sua carreira
Numa entrevista ou numa revisão, "controller gordo" é uma crítica fácil de
fazer e difícil de justificar. A justificativa que funciona é sempre a
mesma pergunta: **como eu testo isso sem subir uma requisição?**

Se a regra estiver no controller, a resposta é "não testo" — e aí a
discussão deixa de ser sobre estética e passa a ser sobre o custo de
verificar se a multa está certa.

Vale também para o caso contrário. Quando alguém propuser quebrar um
controller de sete linhas em quatro classes, a mesma pergunta responde: se
já dá para testar e já dá para ler, a divisão está resolvendo um problema
que não existe.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  routes/
    api.php      # as oito rotas da API, com nome
    web.php
    console.php
  app/
    Http/Controllers/
      LivroController.php       # recurso
      ExemplarController.php
      EmprestimoController.php
      DevolucaoController.php   # invocável
    Services/
      RegistroDeDevolucao.php
:::

:::summary
- `routes/api.php` é instalado por `install:api`, ganha o prefixo `/api` e
  não tem sessão nem CSRF.
- A pergunta que escolhe o arquivo é se quem chama tem sessão de navegador.
- `apiResource` registra as cinco operações de um recurso, com nomes.
- Caminho fixo vem antes de caminho com parâmetro — ou o parâmetro é
  restringido.
- Route model binding busca o registro pelo tipo do parâmetro e devolve
  `404` antes de entrar no método.
- `{exemplar:tombo}` busca por outra coluna quando o identificador público
  não é o id.
- Nome de rota permite mudar a URL sem caçar strings pelo projeto.
- Recurso, invocável e comum comunicam coisas diferentes a quem lê.
- Controller traduz, chama e devolve; oito dependências no construtor
  indicam processo de negócio no lugar errado.
:::

:::checkpoint
Você registra um conjunto de rotas REST com nomes e restrições, sabe por que
uma rota fixa depois de uma com parâmetro nunca roda, usa binding para
receber o registro pronto, e justifica o formato de controller que escolheu.
:::

:::exercise level=1
Diga o que está errado em cada bloco e corrija:

```php
Route::get('emprestimos/{emprestimo}', [C::class, 'show']);
Route::get('emprestimos/atrasados', [C::class, 'atrasados']);
```

```php
Route::get('leitores/{leitor}', function ($id) {
    $leitor = Leitor::find($id);

    if (!$leitor) {
        return response()->json(['erro' => 'não existe'], 404);
    }

    return $leitor;
});
```

:::answer
**Primeiro bloco: ordem.** A rota de atrasados nunca roda — `atrasados` casa
com `{emprestimo}`. Corrige invertendo, ou restringindo:

```php
Route::get('emprestimos/atrasados', [C::class, 'atrasados']);
Route::get('emprestimos/{emprestimo}', [C::class, 'show'])
    ->whereNumber('emprestimo');
```

Com o `whereNumber`, a ordem deixa de importar — e essa é a correção mais
segura, porque não depende de ninguém lembrar dela ao acrescentar a próxima
rota.

**Segundo bloco: três problemas.**

A função anônima no arquivo de rotas impede o `route:cache` e não tem como
ser testada isoladamente.

A busca e o `404` à mão repetem, em cada rota, o que o binding faz sozinho.

E o parâmetro se chama `{leitor}` mas a função recebe `$id` — funciona por
posição e quebra no dia em que alguém acrescentar outro parâmetro.

```php
Route::get('leitores/{leitor}', [LeitorController::class, 'show'])
    ->whereNumber('leitor')
    ->name('leitores.show');
```

```php
public function show(Leitor $leitor)
{
    return $leitor;
}
```
:::

:::exercise level=2
Registre as rotas que faltam do desenho da Casa Amarela: renovações de um
leitor, empréstimos de um leitor e a busca no acervo.

Dê nome a todas, restrinja os parâmetros numéricos e diga em qual arquivo
cada uma vai.

:::answer
```php title="routes/api.php" numbered
Route::get('livros', [LivroController::class, 'index'])
    ->name('livros.index');

Route::post(
    'leitores/{leitor}/renovacoes',
    RenovacaoController::class,
)->whereNumber('leitor')->name('leitores.renovacoes');

Route::get('leitores/{leitor}/emprestimos', [
    EmprestimoController::class, 'porLeitor',
])->whereNumber('leitor')->name('leitores.emprestimos');
```

As três vão em `routes/api.php`: quem consome é o aplicativo do leitor, que
não tem sessão de navegador.

A busca **não** ganha rota própria. Ela é a `livros.index` com parâmetros de
consulta — `/api/livros?q=machado&assunto=literatura` —, e é a mesma decisão
do capítulo de REST: filtro combinável não vira endereço.

A renovação é um controller invocável: é uma ação só, tem nome próprio e
cria um recurso. E repare que ela é `POST` mesmo sendo uma operação que a
Vera chamaria de "atualizar" — o substantivo escondido ali é a renovação, e
ela nasce a cada vez.
:::

:::exercise level=3
Este controller chegou para revisão. Ele funciona e os testes de requisição
passam.

```php
class EmprestimoController extends Controller
{
    public function store(Request $request)
    {
        $exemplar = Exemplar::find($request->exemplar_id);
        $leitor = Leitor::find($request->leitor_id);

        if (!$exemplar || !$leitor) {
            return response()->json(['erro' => 'inválido'], 404);
        }

        if ($exemplar->estado !== 'bom') {
            return response()->json(['erro' => 'indisponível'], 409);
        }

        $abertos = Emprestimo::where('leitor_id', $leitor->id)
            ->whereNull('devolvido_em')->count();

        $limite = date('n') == 1 ? 5 : 3;

        if ($abertos >= $limite) {
            return response()->json(['erro' => 'limite'], 409);
        }

        $emprestimo = Emprestimo::create([
            'exemplar_id' => $exemplar->id,
            'leitor_id' => $leitor->id,
            'retirado_em' => now(),
            'devolver_ate' => now()->addDays(14),
        ]);

        $exemplar->update(['estado' => 'emprestado']);

        return response()->json($emprestimo, 201);
    }
}
```

Aponte os quatro problemas e mostre como fica o método depois.

:::answer
**Um: a regra de negócio inteira está aqui.** Limite por leitor, regra de
janeiro, prazo, mudança de estado do exemplar. Nada disso depende de HTTP, e
tudo isso precisa ser testado sem subir requisição — hoje não dá.

**Dois: os números estão soltos.** `14`, `3`, `5` e `'bom'` são as mesmas
regras que ganharam endereço em `config/biblioteca.php`. Aqui elas
divergiram do arquivo de configuração no momento em que foram escritas.

**Três: não há transação.** Entre criar o empréstimo e alterar o exemplar
existe um intervalo. Se a segunda operação falhar, fica um empréstimo aberto
para um exemplar que continua marcado como disponível — a corrida do
capítulo @cap:pdo, de volta.

**Quatro: a validação é feita com `if`.** Campo ausente vira `null`, `find`
devolve `null`, e a resposta é `404` para um pedido que era `422`. Os dois
códigos dizem coisas diferentes para quem consome.

```php title="app/Http/Controllers/EmprestimoController.php" numbered
public function store(
    RegistrarEmprestimoRequest $request,
    RegistroDeEmprestimo $emprestimos,
) {
    $emprestimo = $emprestimos->registrar(
        exemplarId: $request->integer('exemplar_id'),
        leitorId: $request->integer('leitor_id'),
    );

    return response()
        ->json($emprestimo, 201)
        ->header('Location', route('emprestimos.show', $emprestimo));
}
```

O controller voltou a ter três trabalhos. A validação de formato saiu para
uma classe de requisição; a regra saiu para um serviço que abre transação,
lê a configuração e lança as exceções de domínio do capítulo
@cap:excecoes; e o `Location` do `201` apareceu, que o original não tinha.

Vale dizer o que **não** é problema no código original: ele não está errado.
Ele faz a coisa certa e a faz num lugar onde ninguém consegue verificar
sozinho — e é essa a diferença entre funcionar hoje e continuar funcionando
em março.
:::
