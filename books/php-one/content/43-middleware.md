---
title: "Middleware"
number: 43
slug: middleware
part: p9
kicker: "O middleware de log gravava o corpo inteiro de cada requisição. Durante três meses, isso incluiu o campo senha."
goal: >-
  Entender a pipeline que envolve toda rota, escolher entre middleware
  global, de grupo e de rota, pôr a ordem a favor, limitar tentativas, e
  escrever um middleware próprio sabendo o que não pertence a ele.
---

:::story O campo senha
Cléber tinha escrito o middleware em outubro, num projeto anterior da
Vertexo, e trouxe para a Casa Amarela porque "já estava testado". Ele
gravava no log cada requisição que chegava: método, caminho, tempo de
resposta e o corpo.

— O corpo pra quê? — perguntou Tainá, lendo o arquivo.

— Pra depurar. Quando o cliente diz que mandou uma coisa, a gente vê o que
ele mandou.

Tainá abriu o log de homologação e procurou por `/auth/login`. A primeira
ocorrência era de três dias antes.

```text
[2026-02-12 09:41:03] local.INFO: requisicao
{"metodo":"POST","caminho":"api/auth/login","ms":212,
 "corpo":{"email":"vera@casaamarela.org.br",
          "senha":"marmelada1994"}}
```

Ela virou a tela para o Cléber sem dizer nada.

— Ah — disse ele. — Mas é homologação.

— A Vera usa a mesma senha em tudo — disse Tainá. — Ela me contou.

Cléber ficou calado por um tempo.

— No outro projeto está em produção desde outubro.

— Com login?

— Com login.
:::

## A cebola

Toda requisição que chega ao Laravel atravessa uma sequência de camadas
antes de chegar ao controller, e atravessa as mesmas camadas no caminho de
volta, na ordem inversa. O capítulo @cap:um-framework-de-quarenta-linhas
construiu essa sequência com um `array_reduce` e chamou de cebola antes de
ela ter nome.

```php title="app/Http/Middleware/MedeTempo.php" numbered
final class MedeTempo
{
    public function handle(Request $request, Closure $next): Response
    {
        $inicio = hrtime(true);

        $resposta = $next($request);

        $ms = (hrtime(true) - $inicio) / 1_000_000;
        $resposta->headers->set(
            'Server-Timing', "app;dur={$ms}",
        );

        return $resposta;
    }
}
```

O `$next($request)` é a linha que divide o middleware em dois. Tudo antes
dela acontece **na ida**, antes do controller. Tudo depois acontece **na
volta**, com a resposta pronta nas mãos.

:::diagram type="flowchart" caption="A requisição desce pelas camadas até o controller; a resposta sobe pelas mesmas camadas, na ordem inversa."
nodes:
  - { id: req,  type: io,      text: "requisição" }
  - { id: m1,   type: process, text: "MedeTempo (ida)" }
  - { id: m2,   type: process, text: "auth:sanctum (ida)" }
  - { id: ctl,  type: process, text: "controller" }
  - { id: m2v,  type: process, text: "auth:sanctum (volta)" }
  - { id: m1v,  type: process, text: "MedeTempo (volta)" }
  - { id: resp, type: io,      text: "resposta" }
edges:
  - { from: req, to: m1 }
  - { from: m1, to: m2 }
  - { from: m2, to: ctl }
  - { from: ctl, to: m2v }
  - { from: m2v, to: m1v }
  - { from: m1v, to: resp }
:::

Um middleware pode também **não chamar** o `$next`. Nesse caso, a
requisição para ali, e a resposta que ele devolver é a que o cliente
recebe. É assim que o middleware de autenticação recusa quem não tem token:
o controller nunca é executado.

:::term Middleware
Uma camada que envolve a execução de uma rota, com acesso à requisição na
ida e à resposta na volta, e com o poder de interromper o caminho. Serve
para o que vale para **muitas rotas ao mesmo tempo** e não pertence a
nenhuma delas.
:::

## Global, de grupo e de rota

O Laravel 11 configura middleware no `bootstrap/app.php`, e existem três
alcances.

**Global** roda em toda requisição, web e API:

```php title="bootstrap/app.php" numbered
->withMiddleware(function (Middleware $middleware) {
    $middleware->append(MedeTempo::class);
})
```

**De grupo** roda em todas as rotas de um grupo. O Laravel já tem dois — o
`web`, que liga sessão, cookie e CSRF, e o `api`, que não liga nada disso,
porque a API não tem sessão:

```php title="bootstrap/app.php" numbered
$middleware->api(prepend: [
    ForcaJson::class,
    RegistraRequisicao::class,
]);
```

**De rota** roda onde for pedido:

```php title="routes/api.php" numbered
Route::post('auth/login', LoginController::class)
    ->middleware('throttle:login');

Route::middleware('auth:sanctum')->group(function () {
    Route::apiResource('emprestimos', EmprestimoController::class);
});
```

| Alcance | Custo de um erro | Exemplo |
|---|---|---|
| global | toda requisição, inclusive `/up` | medir tempo |
| grupo | toda a API, ou todo o painel | forçar JSON |
| rota | só onde foi pedido | limitar o login |

Tabela: Quanto maior o alcance, mais barato o middleware precisa ser. Uma
consulta ao banco num middleware global é uma consulta a mais em cada
requisição da aplicação inteira — inclusive na verificação de saúde que o
monitoramento faz a cada dez segundos.

## Ordem importa mais do que parece

Na cebola, a camada de fora vê tudo que a de dentro faz, e a de dentro não
vê nada que a de fora fez depois. Isso transforma a ordem em
comportamento.

O middleware que mede tempo precisa ser o **mais de fora**, para medir
tudo. Se ele estiver dentro do de autenticação, a consulta do token não
entra na medição — e o número que ele mostra é otimista.

O middleware que registra a requisição precisa estar **fora do de
autenticação** para registrar também as requisições recusadas com `401`. E
precisa estar **dentro** se quiser saber quem é o usuário. As duas coisas
não cabem num lugar só, e é por isso que o registro de correlação da
próxima seção faz o trabalho em duas metades.

:::pitfall
A ordem errada mais cara é autorização antes de autenticação. Um
middleware que confere "este usuário é admin?" antes de o usuário ter sido
identificado vê `null`, e o que ele faz com `null` depende de como foi
escrito:

```php
if ($request->user()?->papel !== Papel::Admin) {
    abort(403);
}
```

Esse recusa todo mundo — inclusive o admin, e a rota parece quebrada. A
versão escrita com pressa faz o contrário:

```php
if ($request->user() && !$request->user()->ehAdmin()) {
    abort(403);
}
```

Esse **deixa passar quem não está autenticado**, porque o `if` só recusa
usuário existente que não é admin. O Laravel resolve a ordem entre os
middlewares dele com uma lista de prioridade; os seus, você resolve.
:::

## `ForcaJson`: a API que sempre responde JSON

O handler do capítulo @cap:erros-padronizados responde em JSON quando a
requisição **pede** JSON — quando o cabeçalho `Accept` diz
`application/json`. Um cliente que esquece o cabeçalho recebe, num erro de
validação, um **redirecionamento** para a página anterior, que é o
comportamento do painel web.

```php title="app/Http/Middleware/ForcaJson.php" numbered
final class ForcaJson
{
    public function handle(Request $request, Closure $next): Response
    {
        $request->headers->set('Accept', 'application/json');

        return $next($request);
    }
}
```

Três linhas, e toda rota da API passa a se comportar como API,
independentemente do que o cliente mandou. É o exemplo ideal de
middleware: vale para um grupo inteiro, não depende de nenhuma regra de
negócio, e não consulta nada.

## `RegistraRequisicao`: o incidente que nasce no começo

No capítulo @cap:erros-padronizados, o código de incidente nascia no
momento do erro. Com um middleware, ele nasce no começo de toda
requisição — e toda linha de log escrita durante ela carrega o mesmo
número.

```php title="app/Http/Middleware/RegistraRequisicao.php" numbered
final class RegistraRequisicao
{
    private const CAMPOS_SENSIVEIS = [
        'senha', 'senha_confirmation', 'token', 'documento',
    ];

    public function handle(Request $request, Closure $next): Response
    {
        $id = $request->header('X-Request-Id')
            ?? (string) Str::ulid();

        Context::add('incidente', $id);

        $resposta = $next($request);

        $resposta->headers->set('X-Request-Id', $id);

        return $resposta;
    }

    public function terminate(
        Request $request,
        Response $resposta,
    ): void {
        Log::info('requisicao', [
            'metodo' => $request->method(),
            'caminho' => $request->path(),
            'status' => $resposta->getStatusCode(),
            'usuario' => $request->user()?->id,
            'campos' => array_keys(
                $request->except(self::CAMPOS_SENSIVEIS),
            ),
        ]);
    }
}
```

Quatro decisões nesse arquivo, e cada uma é uma resposta à cena do Cléber.

**O corpo não vai para o log.** Vão os **nomes** dos campos, sem os
valores. Para depurar "o cliente disse que mandou o título", saber que o
campo `titulo` veio é suficiente na maioria das vezes. Para o resto, existe
o incidente e a reprodução.

**Mesmo os nomes passam por uma lista de exclusão.** Não por segurança — o
nome `senha` não é segredo — mas porque a lista existe para ser lembrada: é
o lugar onde alguém procura quando acrescenta um campo sensível novo.

**O registro acontece no `terminate`.** Um middleware com método
`terminate` é chamado **depois que a resposta foi enviada** ao cliente. O
log não atrasa a resposta de ninguém.

**O identificador aceita o que veio de fora.** Se o aplicativo mandar um
`X-Request-Id`, ele é usado. O aplicativo pode então mostrar o mesmo número
que está no log do servidor — e, quando houver um balanceador de carga na
frente, ele pode gerar o número antes, e o rastro atravessa as duas
máquinas.

:::warning
A lista de campos sensíveis protege o **seu** middleware. Não protege o
resto.

O `Log::info('requisicao', $request->all())` que alguém escrever num
controller para investigar um defeito vai gravar a senha do mesmo jeito. O
capítulo @cap:cache-logs-e-medicao trata da regra geral — o que nunca entra
no log — e de como conferir que ela está sendo cumprida.
:::

E o que fazer com os três meses de senhas gravadas no log do outro projeto?
Apagar o log não basta, porque ele pode ter sido copiado para um serviço de
agregação, para um backup, para a máquina de quem investigou um defeito.
A resposta é a mesma do capítulo @cap:git-ci-e-deploy sobre segredo no
Git: **trocar o segredo**. Toda pessoa que fez login no período precisa
redefinir a senha.

## Throttle: o limite que protege de você mesmo

A rota de login aceita e-mail e senha. Sem limite, ela aceita também um
programa que tenta dez mil senhas por minuto contra o e-mail da Vera.

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    RateLimiter::for('login', function (Request $request) {
        return [
            Limit::perMinute(5)->by(
                mb_strtolower((string) $request->input('email'))
                    . '|' . $request->ip(),
            ),
            Limit::perMinute(30)->by($request->ip()),
        ];
    });
}
```

```php
Route::post('auth/login', LoginController::class)
    ->middleware('throttle:login');
```

Dois limites ao mesmo tempo. Cinco tentativas por minuto para a mesma
combinação de e-mail e endereço, que para o ataque dirigido a uma conta. E
trinta por minuto por endereço, que para quem tenta muitas contas de um
mesmo lugar.

Estourado o limite, o middleware não chama o `$next` e responde `429 Too
Many Requests`, com o cabeçalho `Retry-After` dizendo quantos segundos
esperar — e o handler do capítulo @cap:erros-padronizados já traduz para o
formato da API.

O nome da seção é "protege de você mesmo" porque o limite não serve só
para ataque. O aplicativo com um defeito de laço, que refaz a mesma
requisição sem parar, é mais comum que um atacante — e derruba o servidor
do mesmo jeito.

:::pitfall
Limitar só por endereço IP parece suficiente e tem um efeito colateral na
Casa Amarela: os seis computadores do balcão e da sala de leitura saem para
a internet pelo **mesmo** endereço. Cinco tentativas por minuto por IP
significaria que a Neide errar a senha três vezes bloqueia a Vera.

A chave do limite é uma decisão de negócio, e precisa ser conferida com
quem usa.
:::

## O que não colocar ali dentro

Middleware é tentador porque roda para muitas rotas sem que ninguém precise
lembrar. Essa mesma qualidade o torna invisível, e o que é invisível é
esquecido quando dá problema.

**Regra de negócio.** "Leitor bloqueado não pode fazer nada" parece
middleware — vale para todas as rotas do leitor. Mas é regra, muda com o
tempo, tem exceções ("pode devolver, claro"), e precisa ser testada sem
HTTP. Pertence ao service ou à policy do capítulo @cap:autorizacao.

**Consulta pesada em middleware global.** Um middleware que carrega "as
configurações da biblioteca do banco" em toda requisição faz uma consulta a
mais na verificação de saúde, no carregamento de cada imagem servida pelo
Laravel, em cada `404`.

**Coisa que só uma rota precisa.** Se só o `POST /emprestimos` precisa, é
código do `POST /emprestimos`.

A régua: middleware é para o que vale para **muitas rotas** e é
**independente do que a rota faz**. Medir tempo, forçar JSON, identificar a
requisição, limitar taxa, autenticar. Tudo que precisa saber o que a rota
faz está no lugar errado.

:::note Na sua carreira
Muitas das falhas de segurança que você vai investigar ao longo da
carreira não vão estar em código de segurança. Vão estar num middleware de
log, num tratamento de erro genérico, numa ferramenta de depuração
esquecida ligada — código de apoio, escrito com pressa, que ninguém revisa
com a atenção que dá a uma tela de login.

O hábito que ajuda é perguntar, para todo código que **grava** alguma
coisa — log, cache, fila, arquivo —: o que exatamente está sendo gravado, e
quem consegue ler depois? A pergunta leva dez segundos e teria poupado o
Cléber de uma conversa difícil.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  bootstrap/app.php                # withMiddleware: api(prepend: ...)
  app/Http/Middleware/
    MedeTempo.php                  # global, o mais de fora
    ForcaJson.php                  # grupo api
    RegistraRequisicao.php         # incidente no Context, terminate
  app/Providers/
    AppServiceProvider.php         # RateLimiter::for('login')
  routes/api.php                   # throttle:login
:::

:::summary
- Middleware envolve a rota: o que vem antes do `$next` roda na ida, o que
  vem depois roda na volta, e não chamar o `$next` interrompe.
- Global, de grupo e de rota: quanto maior o alcance, mais barato precisa
  ser.
- A ordem é comportamento; autorização antes de autenticação vê `null`.
- `ForcaJson` faz a API responder JSON mesmo sem o cabeçalho `Accept`.
- O incidente nasce no começo da requisição, vai para o `Context` e volta no
  cabeçalho `X-Request-Id`.
- Log de requisição registra nomes de campo, nunca o corpo; `terminate`
  registra depois de responder.
- Segredo gravado em log se resolve trocando o segredo.
- `throttle` com `RateLimiter::for` limita por chave; a chave é decisão de
  negócio.
- Regra de negócio, consulta pesada e coisa de uma rota só não pertencem a
  middleware.
:::

:::checkpoint
A API força JSON, identifica cada requisição com um número que aparece no
log e na resposta, registra requisições sem gravar valores, limita o login
por conta e por endereço, e você sabe explicar por que "leitor bloqueado"
não é um middleware.
:::

:::exercise level=1
Para cada necessidade, diga se é middleware e, se for, de qual alcance:

1. Recusar requisições sem token nas rotas do leitor.
2. Recusar empréstimo para leitor com multa acima de cinco reais.
3. Acrescentar o cabeçalho `X-Request-Id` em toda resposta da API.
4. Limitar a busca do acervo a sessenta requisições por minuto por
   endereço.
5. Converter o título do livro para maiúsculas antes de salvar.

:::answer
1. Middleware de grupo: `auth:sanctum` no grupo das rotas do leitor.
2. Não. É regra de negócio, e já está no `EmprestimoService`.
3. Middleware de grupo, no `api`. É o `RegistraRequisicao`.
4. Middleware de rota: `throttle` com um limitador `busca`.
5. Não. Normalização de entrada de um campo específico é trabalho do
   `prepareForValidation` do Form Request — e, sobre maiúsculas, é uma
   decisão que a Vera provavelmente não quer: o título se guarda como está
   na capa.

O item 5 aparece com frequência como middleware "que limpa a entrada", e
vira o lugar onde a normalização de todos os campos de todas as rotas se
acumula sem que ninguém saiba qual rota depende de qual limpeza.
:::

:::exercise level=2
Escreva um middleware `ExigeVersaoMinima` para as rotas do aplicativo: se o
cabeçalho `X-App-Versao` vier com versão menor que a mínima configurada em
`config('app.versao_minima')`, a resposta é `426 Upgrade Required` no
formato de erro da API. Sem o cabeçalho, deixa passar.

Diga em que alcance ele deve ser registrado.

:::answer
```php title="app/Http/Middleware/ExigeVersaoMinima.php" numbered
final class ExigeVersaoMinima
{
    public function handle(Request $request, Closure $next): Response
    {
        $versao = $request->header('X-App-Versao');
        $minima = config('app.versao_minima');

        if ($versao !== null
            && version_compare($versao, $minima, '<')) {
            return response()->json([
                'tipo' => 'versao-desatualizada',
                'mensagem' => 'Atualize o aplicativo para '
                    . 'continuar.',
            ], 426);
        }

        return $next($request);
    }
}
```

`version_compare` é a função do PHP que entende que `1.10` é maior que
`1.9` — comparar como texto daria o contrário.

**Alcance:** grupo, só nas rotas que o aplicativo usa. Não global, porque o
painel Blade e a `/up` não mandam o cabeçalho e não têm versão.

Deixar passar sem cabeçalho é deliberado: as versões mais antigas do
aplicativo não mandavam o cabeçalho, e recusá-las impediria justamente os
leitores que mais precisam de uma mensagem dizendo para atualizar. Uma
decisão melhor, numa segunda etapa, é tratar a ausência como "versão
anterior a 1.2".
:::

:::exercise level=3
Uma pessoa do time propõe um middleware `CarregaLeitor` para o grupo de
rotas do aplicativo: ele consulta o leitor do usuário autenticado, com os
empréstimos em aberto e a multa, e guarda no `Request` para os controllers
usarem. "Assim nenhum controller precisa buscar de novo."

Avalie a proposta: o que ela resolve, os três custos, e uma alternativa
que resolva o mesmo problema.

:::answer
**O que resolve.** Repetição real: vários controllers do aplicativo
precisam do leitor atual, e buscá-lo em cada um é chato.

**Custo um: consulta em toda rota do grupo.** O middleware carrega
empréstimos e multa inclusive para `GET /livros`, que não usa nada disso.
Três consultas a mais em cada busca do acervo, a rota mais usada do
aplicativo.

**Custo dois: dado velho dentro da transação.** O `EmprestimoService`
precisa ler os empréstimos em aberto **dentro** da transação, com trava.
Se ele passar a usar o que o middleware carregou antes, a conferência do
limite volta a ter a corrida do capítulo @cap:do-arquivo-ao-banco. Se não
usar, o middleware carregou à toa.

**Custo três: dependência invisível.** O controller passa a depender de
um atributo no `Request` que alguém pôs em outro arquivo. Uma rota nova no
grupo errado recebe `null`, e o erro aparece longe da causa.

**Alternativa.** O leitor atual é **uma** consulta, barata, e só as rotas
que precisam deveriam fazê-la. Um método no model `Usuario`:

```php
$leitor = $request->user()->leitor;
```

Com o relacionamento, isso é uma consulta, só onde é chamado. O que cada
rota precisa a mais — empréstimos, multa — ela carrega com `load`, com a
consulta visível no próprio controller. A repetição que sobra é uma linha,
e uma linha repetida que diz exatamente o que faz é melhor que uma camada
que faz mais do que parece.
:::
