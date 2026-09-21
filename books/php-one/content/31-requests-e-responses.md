---
title: "Requests e responses"
number: 31
slug: requests-e-responses
part: p6
kicker: "A estagiária enviou uma capa de livro chamada ../teste.php. O Sistema guardou, e o servidor executou."
goal: >-
  Entrar e sair da aplicação com objetos: ler o dado certo do `Request`,
  devolver resposta com status e cabeçalho corretos, e receber arquivo sem
  confiar em nada que o cliente mandou.
---

:::story A capa que era um programa
O Sistema deixava a bibliotecária anexar a capa do livro. Dedé pediu à Tainá
que tentasse quebrar, antes de decidir como fazer o mesmo no projeto novo.

Ela criou um arquivo de uma linha:

```php
<?php echo 'oi, sou uma capa';
```

Renomeou para `../teste.php`, anexou como capa e salvou. O Sistema
respondeu que a capa tinha sido enviada com sucesso.

Depois ela abriu o endereço do site com `/teste.php` no fim.

```text
oi, sou uma capa
```

— Dedé.

— Fala.

— Eu acabei de subir um programa pro servidor da biblioteca.

Dedé olhou por cima do monitor.

— Pelo formulário de capa?

— Pelo formulário de capa.
:::

## `Request` é um objeto

Dentro do Laravel, você não toca em `$_GET`, `$_POST` nem `$_SERVER`. Tudo
que chegou está num objeto que o contêiner entrega para quem declarar o
tipo:

```php title="app/Http/Controllers/LivroController.php" numbered
use Illuminate\Http\Request;

public function index(Request $request)
{
    $busca = $request->query('q');
    $pagina = $request->integer('pagina', 1);

    return Livro::buscar($busca)->paginate(20, page: $pagina);
}
```

A diferença não é cosmética. O objeto sabe responder perguntas que as
superglobais não sabem:

| Método | Responde |
|---|---|
| `input('campo')` | o valor, venha da URL ou do corpo |
| `query('campo')` | só o que veio na URL |
| `post('campo')` | só o que veio no corpo |
| `header('Accept')` | um cabeçalho, com o nome de verdade |
| `bearerToken()` | o token do `Authorization`, já separado |
| `expectsJson()` | se o cliente quer JSON de volta |
| `file('capa')` | o arquivo enviado, como objeto |

Tabela: `input()` é o mais usado e o menos preciso; ele procura nos dois
lugares. Quando importa de onde o valor veio, use `query()` ou `post()`.

E o corpo JSON — que no PHP cru exigia `php://input` — já está lá:

```php
$request->input('exemplar_id');
```

O Laravel lê o `Content-Type`, decodifica o JSON e põe tudo no mesmo lugar.
A pedra do capítulo @cap:o-que-e-http deixa de existir dentro do framework;
ela continua existindo em todo PHP que não usa framework, e é por isso que
valia conhecer o mecanismo.

## O dado certo, já no tipo certo

```php
$request->string('estado')->toString();
$request->integer('pagina');
$request->boolean('somente_disponiveis');
$request->date('devolvido_em');
$request->enum('status', StatusExemplar::class);
```

Tudo que chega por HTTP é texto. Estes métodos fazem a conversão na
fronteira, que é onde ela deve acontecer — e o `enum()` recusa um valor que
não é um dos casos, em vez de deixar a string solta seguir viagem.

E existe um terceiro grupo, o único que **filtra**:

```php
$dados = $request->validate([
    'exemplar_id' => ['required', 'integer'],
    'leitor_id' => ['required', 'integer'],
]);
```

`validate()` devolve **apenas os campos declarados**, já conferidos. Se o
pedido não passar, ele interrompe ali e responde `422` com a lista de
problemas, sem entrar no resto do método.

:::pitfall
A diferença entre `$request->all()` e o retorno do `validate()` é uma falha
de segurança esperando o dia certo.

```php
Livro::create($request->all());
```

O cliente manda `titulo`, `ano` — e `id`, `criado_em` ou qualquer coluna que
ele descubra que existe. Com `all()`, tudo isso chega ao banco.

Use o retorno do `validate()`, que só contém o que você declarou. É a
diferença entre "o que o cliente mandou" e "o que eu aceito receber".
:::

## Devolver: array, model ou resposta

O jeito mais curto já apareceu: devolva um array ou um objeto, e o Laravel
converte.

```php
return $livro;                    // 200, JSON do model
return Livro::all();              // 200, JSON da coleção
return ['status' => 'ok'];        // 200, JSON do array
```

Quando você precisa decidir status ou cabeçalho, o caminho é explícito:

```php
return response()->json($emprestimo, 201)
    ->header('Location', route('emprestimos.show', $emprestimo));
```

```php
return response()->noContent();   // 204, corpo vazio
```

```php
abort(404, 'Exemplar não encontrado');
```

| Situação | O que devolver |
|---|---|
| leitura que deu certo | o model ou a coleção |
| criação | `response()->json($x, 201)` com `Location` |
| alteração sem corpo de volta | `response()->noContent()` |
| erro de estado do sistema | `abort(409, ...)` ou a exceção de domínio |

Tabela: A regra do capítulo @cap:o-que-e-uma-api-rest continua valendo, e
agora ela tem sintaxe.

:::key
`response()->noContent()` existe porque `return null` de um método de
controller devolve `200` com o corpo `""` — e um corpo vazio com `200` é uma
resposta que o cliente precisa interpretar.

O `204` diz a mesma coisa no lugar onde o cliente já está olhando: o número.
:::

## A mesma rota, duas respostas

O painel da Vera e o aplicativo do leitor podem chamar a mesma rota. O que
muda é o que cada um sabe exibir.

```php
if ($request->expectsJson()) {
    return response()->json(['erro' => 'Exemplar indisponível'], 409);
}

return back()->withErrors(['exemplar' => 'Exemplar indisponível']);
```

`expectsJson()` olha o cabeçalho `Accept` que o cliente enviou. É a mesma
negociação que o capítulo de HTTP descreveu, agora com uma pergunta em vez
de uma leitura de cabeçalho à mão.

Na prática, você vai escrever esse `if` poucas vezes: separar as rotas em
`api.php` e `web.php` já resolve a maior parte. Ele serve para o caso em que
a rota é mesmo uma só.

## Upload: não confie em nada que veio junto

Volte à capa da Tainá. O Sistema fazia o equivalente a isto:

```php
$nome = $_FILES['capa']['name'];

move_uploaded_file($_FILES['capa']['tmp_name'], 'capas/' . $nome);
```

Há três decisões erradas em duas linhas, e todas têm a mesma raiz: **o
cliente escolheu**.

**O nome do arquivo veio do cliente.** `../teste.php` sobe um nível e sai da
pasta de capas.

**A extensão veio do cliente.** Um `.php` guardado dentro da pasta pública é
um programa que o servidor executa quando alguém pedir.

**O conteúdo nunca foi conferido.** Nada garantiu que o arquivo é mesmo uma
imagem.

A versão do Laravel decide as três coisas do lado de cá:

```php title="app/Http/Controllers/CapaController.php" numbered
public function __invoke(Request $request, Livro $livro)
{
    $request->validate([
        'capa' => ['required', 'image', 'max:2048'],
    ]);

    $caminho = $request->file('capa')->store('capas', 'public');

    $livro->update(['capa' => $caminho]);

    return response()->json(['capa' => $caminho], 201);
}
```

```text
{"capa":"capas/kR8mZ2qXv1nB7dLp0sYw.jpg"}
```

`store()` **gera** o nome, a partir de um valor aleatório, e escolhe a
extensão a partir do tipo real do arquivo — não do que veio escrito. O nome
original do cliente é descartado.

A regra `image` confere o conteúdo, não o nome. E `max:2048` é o tamanho em
quilobytes, que é o limite que impede alguém de encher o disco com uma
requisição.

:::pitfall
Existe um método parecido e perigoso:

```php
$request->file('capa')->storeAs('capas', $request->file('capa')
    ->getClientOriginalName());
```

`getClientOriginalName()` devolve exatamente o texto que o cliente enviou —
incluindo `../teste.php`. O nome do método é honesto: *client original*. É
um dado do cliente, como qualquer campo de formulário.

Se você precisar mesmo preservar o nome original — e às vezes precisa, para
exibir —, guarde-o **numa coluna**, como texto, e deixe o nome no disco ser
gerado.
:::

E uma quarta proteção, que não está no código e sim na estrutura: a pasta de
upload não fica dentro de `public/`. Ela fica em `storage/`, fora do alcance
do servidor web, e os arquivos são servidos por uma rota ou por um link
declarado. Um `.php` que chegue lá não é executado por ninguém, porque
ninguém consegue pedi-lo pela URL.

:::note Na sua carreira
A conversa sobre upload costuma terminar em "mas o formulário só deixa
escolher imagem". Vale saber responder isso sem soar arrogante, porque a
frase é dita de boa-fé.

O formulário é HTML que roda na máquina de quem está do outro lado. Ele pode
ser alterado no próprio navegador, ou simplesmente ignorado — a requisição
pode ser montada com `curl`, sem formulário nenhum. Tudo que acontece antes
de chegar no seu servidor é sugestão.

É a mesma ideia do capítulo @cap:o-que-e-http, e vale para validação de
formato, campo obrigatório e limite de tamanho: **o cliente confere para ser
gentil; o servidor confere porque é o único que pode.**
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/Http/Controllers/
    LivroController.php
    CapaController.php      # upload com nome gerado
    DevolucaoController.php # 204 sem corpo
    EmprestimoController.php # 201 com Location
  storage/app/public/
    capas/                  # fora do alcance direto da web
:::

:::summary
- Dentro do Laravel, a requisição é um objeto; superglobal não se usa.
- `input()` procura na URL e no corpo; `query()` e `post()` são precisos.
- O corpo JSON já vem decodificado, sem `php://input`.
- `string()`, `integer()`, `boolean()`, `date()` e `enum()` convertem na
  fronteira.
- `validate()` devolve só os campos declarados; `all()` devolve o que o
  cliente quis mandar.
- Array e model viram JSON sozinhos; `response()->json()` quando o status
  ou o cabeçalho importa.
- `noContent()` é o `204`; `return null` é um `200` com corpo vazio.
- `expectsJson()` decide o formato quando a rota atende os dois mundos.
- No upload, o nome, a extensão e o tipo vêm do cliente: gere o nome,
  confira o conteúdo e guarde fora de `public/`.
:::

:::checkpoint
Você lê dados da requisição com o método certo para cada origem, devolve
respostas com status e cabeçalho corretos, recebe um arquivo sem usar nada
que o cliente escolheu, e sabe explicar por que a validação do formulário
não conta.
:::

:::exercise level=1
Para cada trecho, diga o que está errado e corrija:

```php
$id = $_GET['livro_id'];
```

```php
return null;  // devolução registrada, nada a devolver
```

```php
Livro::create($request->all());
```

:::answer
**Primeiro.** Superglobal dentro do framework. Além de contornar o objeto
`Request`, ela devolve texto sem conversão e não é substituível em teste.

```php
$id = $request->integer('livro_id');
```

**Segundo.** `return null` produz `200` com corpo vazio. O cliente recebe
sucesso e um corpo que precisa interpretar.

```php
return response()->noContent();
```

**Terceiro.** Atribuição em massa do que o cliente mandou. Qualquer coluna
que ele adivinhe entra.

```php
$dados = $request->validate([
    'titulo' => ['required', 'string', 'max:200'],
    'ano' => ['nullable', 'integer'],
]);

Livro::create($dados);
```
:::

:::exercise level=2
Escreva o método `store` do `EmprestimoController` para devolver `201` com o
cabeçalho `Location`, e o `__invoke` do `DevolucaoController` para devolver
`204`.

A devolução aceita um campo opcional `estado`, que precisa ser um dos casos
de `StatusExemplar`.

:::answer
```php title="app/Http/Controllers/EmprestimoController.php" numbered
public function store(
    Request $request,
    RegistroDeEmprestimo $emprestimos,
) {
    $dados = $request->validate([
        'exemplar_id' => ['required', 'integer'],
        'leitor_id' => ['required', 'integer'],
    ]);

    $emprestimo = $emprestimos->registrar(
        exemplarId: $dados['exemplar_id'],
        leitorId: $dados['leitor_id'],
    );

    return response()
        ->json($emprestimo, 201)
        ->header(
            'Location',
            route('emprestimos.show', $emprestimo),
        );
}
```

```php title="app/Http/Controllers/DevolucaoController.php" numbered
public function __invoke(Request $request, Emprestimo $emprestimo)
{
    $estado = $request->enum('estado', StatusExemplar::class)
        ?? StatusExemplar::Bom;

    $this->devolucoes->registrar($emprestimo, $estado);

    return response()->noContent();
}
```

O `enum()` faz três coisas numa linha: lê o campo, recusa valor que não é um
dos casos e devolve o objeto do enum, não texto. Quando o campo não vem,
devolve `null`, e o `??` põe o padrão.

Repare no que ficou de fora dos dois métodos: a regra. O empréstimo confere
limite e disponibilidade dentro do serviço; a devolução calcula multa e muda
o estado do exemplar dentro do dela. Os controllers traduzem e devolvem.
:::

:::exercise level=3
Um sistema aceita upload de comprovante em PDF. O código atual:

```php
$arquivo = $request->file('comprovante');
$nome = $arquivo->getClientOriginalName();

if (str_ends_with($nome, '.pdf')) {
    $arquivo->move(public_path('comprovantes'), $nome);
}
```

Liste todos os problemas e reescreva. Depois responda: qual deles continua
existindo mesmo se o nome for gerado e a extensão conferida?

:::answer
**Os problemas.**

O nome vem do cliente e não é limpo: `../../public/x.php.pdf` não termina em
nada útil, mas `..%2Fx.pdf` e variações de caminho conseguem sair da pasta
dependendo do sistema de arquivos.

A conferência é pelo **nome**, não pelo conteúdo. `virus.php.pdf` termina em
`.pdf` e continua sendo o que está dentro dele.

O destino é `public/`, ou seja, dentro do alcance do servidor web.

Não há limite de tamanho: um arquivo de dois gigabytes é aceito até o disco
acabar.

Não há tratamento para o `if` falso: o arquivo é silenciosamente descartado
e o usuário recebe sucesso.

E `move()` no diretório público, com nome previsível, permite a um segundo
envio sobrescrever o comprovante de outra pessoa.

**A reescrita.**

```php
$request->validate([
    'comprovante' => ['required', 'file', 'mimes:pdf', 'max:5120'],
]);

$caminho = $request->file('comprovante')
    ->store('comprovantes', 'local');

$pagamento->update([
    'comprovante' => $caminho,
    'comprovante_nome' => $request->file('comprovante')
        ->getClientOriginalName(),
]);
```

O nome original vai para uma **coluna**, para ser exibido, e não para o
disco. O disco recebe um nome gerado, num disco `local`, que fica fora de
`public/`.

**O que continua existindo.** O conteúdo. `mimes:pdf` confere o tipo do
arquivo, e um PDF pode conter JavaScript, um anexo embutido ou um exploit
para o leitor de quem abrir.

Nenhuma validação de upload torna o arquivo seguro — ela só garante que ele
é o **tipo** que você esperava. Servir arquivo enviado por terceiro para
outros usuários é uma decisão de produto, e as mitigações são outras:
varredura antivírus, servir com `Content-Disposition: attachment` para não
abrir no navegador, e servir de um domínio diferente do da aplicação.
:::
