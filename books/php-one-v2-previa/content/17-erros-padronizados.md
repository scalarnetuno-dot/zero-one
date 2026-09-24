---
title: "Erros padronizados"
number: 17
slug: erros-padronizados
part: p4
kicker: "O leitor ligou dizendo que deu erro. O log tinha 4.200 linhas e nenhuma pista de qual delas era dele."
goal: >-
  Fazer toda resposta de erro da API ter o mesmo formato, traduzir as
  exceções do domínio em status numa linha, nunca vazar detalhe interno, e
  entregar ao suporte um número que leva direto à linha certa do log.
---

:::story Deu erro
O telefone da biblioteca tocou às 10h20. Vera atendeu, ouviu, e passou para
Tainá sem dizer nada, o que já era uma forma de dizer.

— Oi, é o Wellington. Eu tentei pegar um livro pelo aplicativo e deu erro.

— Que erro?

— Deu erro. Apareceu "Server Error". Aí eu tentei de novo e deu de novo.

— Que horas foi isso?

— Agora. Quer dizer, uns dez minutos atrás. Ou quinze.

Tainá abriu o `laravel.log` de homologação, que naquela semana também
atendia os primeiros testes com leitores de verdade. Quatro mil e duzentas
linhas desde as nove. Procurou "Wellington": nada — o log não tinha nome de
ninguém. Procurou "ERROR": trinta e uma ocorrências entre 10h00 e 10h20.

Escolheu a que parecia mais com empréstimo. Um `QueryException` com um
*stack trace* de oitenta linhas. Passou quarenta minutos nele, achou a
causa, abriu a tarefa.

Dedé leu a tarefa depois do almoço.

— Esse erro é do importador noturno. Rodou de novo às dez porque o Cléber
disparou à mão.

— E o do Wellington?

— Deve ser um dos outros trinta.

Wellington ligou de novo às 14h. Tinha conseguido pegar o livro no balcão.
Queria saber se o aplicativo ia cobrar duas vezes.
:::

## Três formatos de erro na mesma API

Faça o inventário do que a API da Casa Amarela devolve hoje quando algo dá
errado. São quatro situações, e cada uma sai de um jeito:

```json
// 422, validação do Form Request
{"message": "O título é obrigatório.",
 "errors": {"titulo": ["O título é obrigatório."]}}

// 409, abort() no controller
{"message": "Exemplar indisponível"}

// 404, route model binding
{"message": "No query results for model [App\\Models\\Livro] 99999"}

// 500, com APP_DEBUG=true
{"message": "SQLSTATE[23000]: Integrity constraint violation...",
 "exception": "Illuminate\\Database\\QueryException",
 "file": "/var/www/vendor/laravel/framework/...",
 "line": 822,
 "trace": [ ... 80 itens ... ]}
```

Quatro formatos parecidos o bastante para enganar e diferentes o bastante
para quebrar. O aplicativo precisa de um `if` para cada um — e o `if` que
lê `message` para decidir o que fazer quebra no dia em que alguém traduzir
a frase.

E o último vaza, na ordem: o SQL com o nome da tabela e da restrição, o
nome da classe interna, o caminho do projeto no servidor, a versão do
framework pela estrutura de pastas, e oitenta linhas de caminho de
execução. É um mapa do sistema entregue a quem fez a requisição.

:::key
Um formato de erro, para a API inteira, é mais importante do que o formato
ser perfeito. O cliente escreve o tratamento **uma vez** e confia nele.

Três formatos certos, cada um num canto, são piores que um formato só,
imperfeito, em todos os lugares.
:::

## O formato

A Casa Amarela adota um formato com quatro chaves:

```json
{
  "tipo": "exemplar-indisponivel",
  "mensagem": "O exemplar 2117 está emprestado.",
  "campos": { "exemplar_id": ["Exemplar indisponível."] },
  "incidente": "01JHQ4Z8K3M2X9V7B5N1P0R6TW"
}
```

**`tipo`** é um identificador estável, em texto, que o cliente usa para
decidir. Ele **nunca muda**, nem quando a mensagem é reescrita. É o que o
`if` do aplicativo compara.

**`mensagem`** é para uma pessoa ler. Pode mudar, ser traduzida, ganhar
acento. Nenhum código deve decidir nada com base nela.

**`campos`** é opcional e aparece quando o erro tem um campo culpado —
sempre no `422`, às vezes no `409`. É o mesmo mapa do `errors` do capítulo
@cap:validation-e-form-requests.

**`incidente`** é opcional e aparece quando a falha é do servidor. É o
número que o Wellington lê para a Tainá pelo telefone.

:::trivia
Existe uma especificação para isso, a RFC 9457, *Problem Details for HTTP
APIs*, com as chaves `type`, `title`, `status`, `detail` e `instance`. O
formato da Casa Amarela é uma versão em português da mesma ideia.

Se a sua API vai ser consumida por muitas equipes que você não conhece,
seguir a RFC ao pé da letra poupa uma conversa em cada integração. Se é o
aplicativo de uma biblioteca, as chaves em português são mais fáceis de
ler, e o que importa é a disciplina — um formato, sempre.
:::

## O handler, onde toda exceção termina

No Laravel 11, o lugar em que toda exceção não capturada chega é o
`bootstrap/app.php`, no bloco `withExceptions`. É o
`set_exception_handler` do capítulo @cap:excecoes, com o framework em
volta.

```php title="bootstrap/app.php" numbered
->withExceptions(function (Exceptions $exceptions) {
    $exceptions->shouldRenderJsonWhen(
        fn (Request $r) => $r->is('api/*') || $r->expectsJson(),
    );

    $exceptions->render(
        fn (Throwable $e, Request $r) => $r->is('api/*')
            ? RespostaDeErro::para($e)
            : null,
    );
})
```

O `render` recebe toda exceção. Se a requisição é da API, uma classe
decide a resposta. Se não é, devolve `null`, e o Laravel faz o que faria
normalmente — mostra a página de erro do painel Blade.

A classe que decide é uma tradução, e uma tradução é um `match`:

```php title="app/Http/RespostaDeErro.php" numbered
final class RespostaDeErro
{
    public static function para(Throwable $e): JsonResponse
    {
        return match (true) {
            $e instanceof ValidationException
                => self::validacao($e),
            $e instanceof ExcecaoDeDominio
                => self::dominio($e),
            $e instanceof ModelNotFoundException,
            $e instanceof NotFoundHttpException
                => self::corpo(404, 'nao-encontrado',
                    'O recurso pedido não existe.'),
            $e instanceof AuthenticationException
                => self::corpo(401, 'nao-autenticado',
                    'É preciso entrar para continuar.'),
            $e instanceof AuthorizationException
                => self::corpo(403, 'sem-permissao',
                    'Você não tem permissão para isso.'),
            $e instanceof ThrottleRequestsException
                => self::corpo(429, 'muitas-requisicoes',
                    'Muitas tentativas. Aguarde um pouco.'),
            default => self::falhaInterna($e),
        };
    }

    // ...
}
```

Uma lista, uma leitura. Quem quer saber o que a API responde para cada
tipo de falha lê um arquivo.

## Exceção de domínio vira status numa linha

As três exceções do capítulo @cap:excecoes — `ExemplarIndisponivel`,
`LimiteDeEmprestimosAtingido`, `LeitorComPendencia` — já carregam dados. O
que falta é dizerem, cada uma, o seu `tipo`. Uma classe mãe resolve:

```php title="app/Emprestimos/ExcecaoDeDominio.php" numbered
abstract class ExcecaoDeDominio extends RuntimeException
{
    abstract public function tipo(): string;

    public function status(): int
    {
        return 409;
    }

    public function campos(): ?array
    {
        return null;
    }
}
```

```php title="app/Emprestimos/ExemplarIndisponivel.php" numbered
final class ExemplarIndisponivel extends ExcecaoDeDominio
{
    public function __construct(
        public readonly int $tombo,
        public readonly StatusExemplar $estado,
    ) {
        parent::__construct(sprintf(
            'O exemplar %d está %s.',
            $tombo,
            mb_strtolower($estado->rotulo()),
        ));
    }

    public function tipo(): string
    {
        return 'exemplar-indisponivel';
    }

    public function campos(): array
    {
        return ['exemplar_id' => ['Exemplar indisponível.']];
    }
}
```

E a tradução, no `RespostaDeErro`, é genérica:

```php
private static function dominio(ExcecaoDeDominio $e): JsonResponse
{
    return self::corpo(
        $e->status(),
        $e->tipo(),
        $e->getMessage(),
        $e->campos(),
    );
}
```

Uma exceção nova do domínio — `ReservaExpirada`, digamos — herda de
`ExcecaoDeDominio`, declara o seu `tipo`, e sai da API no formato certo sem
que ninguém toque no handler.

:::http title="O mesmo erro, antes e agora"
POST /api/emprestimos
Content-Type: application/json

{"exemplar_id": 2117, "leitor_id": 47}
---
409 Conflict
Content-Type: application/json

{
  "tipo": "exemplar-indisponivel",
  "mensagem": "O exemplar 2117 está emprestado.",
  "campos": { "exemplar_id": ["Exemplar indisponível."] }
}
:::

É a resposta que o exercício 3 do capítulo
@cap:validation-e-form-requests prometeu: o status diz a verdade, e a tela
sabe qual campo destacar.

Com isso, os `abort(409, ...)` do controller do capítulo
@cap:o-crud-completo podem ser trocados por `throw new
ExemplarIndisponivel(...)`. E o controller deixa de conhecer status HTTP
para regra de negócio — o que o capítulo @cap:services vai transformar em
princípio.

:::pitfall
A tentação, depois de ter o handler, é usar exceção para tudo — inclusive
para o que não é erro. "Livro não tem exemplares" não é exceção; é uma
lista vazia. "Leitor sem empréstimos" é `[]`, com `200`.

A régua é a do capítulo @cap:excecoes: exceção é para quando a operação
**não pode continuar**. Uma consulta que não encontrou nada continuou e
terminou bem.
:::

## O `404` do binding: útil e genérico demais

O `404` automático do route model binding é um presente, e vem com uma
mensagem que não deveria sair:

```text
No query results for model [App\Models\Livro] 99999
```

Ela revela o namespace e o nome da classe interna. Não é uma falha grave —
não abre porta nenhuma —, mas é informação que o cliente não precisa e que
um curioso anota.

O `match` acima já troca a mensagem pela genérica. E existe uma decisão a
tomar sobre **quando o `404` é a resposta certa para outra coisa**: o leitor
47 pede o empréstimo 312, que existe e é de outra pessoa. A resposta é `403`
ou `404`?

| Resposta | Diz ao cliente |
|---|---|
| `403` | "isso existe, e não é seu" |
| `404` | "isso não existe para você" |

Tabela: Os dois estão corretos em HTTP. O primeiro confirma a existência
do recurso, e isso às vezes é informação demais.

Para empréstimos, confirmar que o número 312 existe diz pouco. Para uma
rota como `/leitores?documento=...`, confirmar que um CPF está cadastrado
na biblioteca diz muito. A regra da Casa Amarela: `404` quando a existência
do recurso é, ela mesma, um dado pessoal. O capítulo @cap:autorizacao
aplica.

## `500` não vaza nada

A última linha do `match` — o `default` — é a mais importante, porque é a
que ninguém planejou:

```php title="app/Http/RespostaDeErro.php" numbered
private static function falhaInterna(Throwable $e): JsonResponse
{
    $status = $e instanceof HttpExceptionInterface
        ? $e->getStatusCode()
        : 500;

    return self::corpo(
        $status,
        'falha-interna',
        'Algo deu errado do nosso lado. Informe o '
            . 'código ao suporte.',
        incidente: Incidente::atual(),
    );
}
```

A resposta tem uma frase honesta e um número. Nenhuma linha de SQL, nenhum
nome de classe, nenhum caminho de arquivo.

O detalhe continua existindo — **no log**, onde quem precisa pode ler. O
Laravel registra a exceção antes de chamar o `render`, e o que vai para o
cliente e o que vai para o log são decisões separadas.

:::warning
Nada disso vale com `APP_DEBUG=true`. Com ele ligado, o Laravel acrescenta à
resposta a exceção, o arquivo, a linha e o *trace* completo, por cima do
que o handler montou, para ajudar em desenvolvimento.

Em produção, `APP_DEBUG=false` é a primeira linha da lista do capítulo
@cap:git-ci-e-deploy, e a que mais aparece em relatório de invasão. Há
buscadores que indexam páginas de erro do Laravel com o modo de depuração
ligado — e elas trazem, com frequência, o conteúdo do `.env`.
:::

## Código de incidente: o número que o suporte pede

O Wellington não tinha como dizer qual das 31 linhas era a dele. Com o
incidente, ele tem: está na tela do aplicativo, e o aplicativo pode até
oferecer um botão para copiar.

```php title="app/Support/Incidente.php" numbered
final class Incidente
{
    public static function atual(): string
    {
        if (!Context::has('incidente')) {
            Context::add('incidente', (string) Str::ulid());
        }

        return Context::get('incidente');
    }
}
```

`Context` é uma área de dados que vive durante a requisição, e o Laravel
**acrescenta tudo o que estiver nela a cada linha de log** escrita depois.
Quando a exceção é registrada, a linha sai com o incidente anexado:

```text
[2026-02-10 10:14:07] production.ERROR: SQLSTATE[23000]...
{"exception":"...","incidente":"01JHQ4Z8K3M2X9V7B5N1P0R6TW"}
```

E a busca que levou quarenta minutos passa a levar um comando:

```text
$ grep 01JHQ4Z8K3M2X9V7B5N1P0R6TW storage/logs/laravel.log
```

O ULID é um identificador único que começa pelo instante em que foi gerado,
então os incidentes do mesmo minuto ficam próximos numa ordenação. É um
detalhe pequeno que ajuda quando alguém diz "foi mais ou menos às dez".

Por enquanto, o incidente nasce no momento do erro. No capítulo
@cap:middleware, ele passa a nascer **no início de toda requisição**, e cada
linha de log daquela requisição — não só a do erro — carrega o mesmo
número. É a diferença entre achar a exceção e achar a história inteira que
levou até ela.

## `401` e `403` não são a mesma coisa

A lista do handler tem os dois, e eles são confundidos o bastante para
merecer seção própria.

**`401 Unauthorized`** quer dizer: **não sei quem você é**. Faltou o token,
ou ele expirou, ou é inválido. O cliente deve mandar a pessoa entrar de
novo.

**`403 Forbidden`** quer dizer: **sei quem você é, e você não pode**. O
token é válido. Entrar de novo não resolve nada.

O nome oficial do `401` é infeliz — ele diz *unauthorized* e significa "não
autenticado". A confusão vem daí, e a consequência é concreta: um aplicativo
que recebe `401` quando deveria receber `403` manda a pessoa para a tela de
login, ela entra, tenta de novo, volta para a tela de login. Ciclo
infinito, com a pessoa convencida de que a senha está errada.

| Status | Pergunta que falhou | O cliente faz |
|---|---|---|
| `401` | quem é você? | pede login |
| `403` | você pode? | mostra "sem permissão" |
| `404` | isso existe? | mostra "não encontrado" |
| `409` | o mundo permite? | explica e oferece saída |
| `422` | o pedido está certo? | destaca os campos |

Tabela: Cinco status, cinco perguntas, cinco comportamentos da tela. É a
tabela que o aplicativo do leitor implementa, e é a razão de cada uma
existir.

:::note Na sua carreira
O formato de erro de uma API é a parte do contrato que mais custa mudar
depois, porque todo cliente o trata em um lugar central — e mudar esse
lugar central muda o comportamento de todas as telas ao mesmo tempo.

Se você estiver no começo de uma API, gaste uma tarde nisso antes de ter
vinte rotas. Se estiver numa API que já tem três formatos, o caminho é o de
sempre: o formato novo passa a sair em todas as rotas, com os campos antigos
mantidos ao lado até o último cliente migrar. É trabalhoso e é invisível, e
é o tipo de coisa que diferencia quem mantém sistema de quem só escreve
rota.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  bootstrap/app.php            # withExceptions → RespostaDeErro
  app/Http/
    RespostaDeErro.php         # um match, a API inteira
  app/Support/
    Incidente.php              # ULID no Context
  app/Emprestimos/
    ExcecaoDeDominio.php       # tipo(), status(), campos()
    ExemplarIndisponivel.php
    LimiteDeEmprestimosAtingido.php
    LeitorComPendencia.php
:::

:::milestone
Fim da Parte 4. A API da Casa Amarela recusa entrada malformada na porta,
devolve só o que decidiu devolver, lista o acervo inteiro com busca, filtro
e teto, e responde todo erro no mesmo formato — com um número que leva o
suporte à linha certa do log.

No caderno da Tainá, uma linha nova: *"o cliente não lê a mensagem, lê o
tipo"*.
:::

:::summary
- Um formato de erro para a API inteira vale mais que três formatos
  corretos.
- `tipo` é estável e o cliente decide por ele; `mensagem` é para gente e
  pode mudar.
- O `render` no `withExceptions` recebe toda exceção; um `match` traduz tipo
  em resposta.
- Exceções de domínio herdam de uma classe mãe com `tipo`, `status` e
  `campos`; uma nova sai no formato certo sem tocar no handler.
- O `404` do binding precisa de mensagem genérica; `403` ou `404` para
  recurso alheio é uma decisão sobre o que a existência revela.
- `500` não leva SQL, classe, arquivo nem *trace*; o detalhe vai para o
  log.
- `APP_DEBUG=true` em produção anula o handler e vaza o sistema.
- O incidente no `Context` aparece em toda linha de log e na resposta, e
  transforma uma busca de quarenta minutos num `grep`.
- `401` é "não sei quem é você"; `403` é "sei, e você não pode".
:::

:::checkpoint
Toda resposta de erro da API tem o mesmo formato, as exceções de domínio
viram `409` sem `abort` no controller, nenhuma falha interna vaza detalhe,
e você consegue explicar, para cada um dos cinco status de erro, o que a
tela do cliente deve fazer ao recebê-lo.
:::

:::exercise level=1
Para cada situação, dê o status e o `tipo` que a API da Casa Amarela
devolve:

1. O token do aplicativo expirou.
2. O leitor tenta renovar um empréstimo que já foi renovado duas vezes.
3. O corpo do `POST /emprestimos` veio sem `leitor_id`.
4. O banco de dados está fora do ar.
5. Uma atendente tenta apagar um livro, e só admin pode.

:::answer
1. `401`, `nao-autenticado`. O aplicativo leva a pessoa ao login.
2. `409`, com um tipo de domínio — algo como `renovacao-esgotada`. O pedido
   está certo; a regra não deixa.
3. `422`, com `campos.leitor_id`. O tipo pode ser `validacao`.
4. `500` — ou `503`, se a falha for detectada como indisponibilidade —,
   `falha-interna`, com `incidente`. Nenhuma menção a banco na mensagem.
5. `403`, `sem-permissao`. Ela está autenticada; o papel dela não permite.

O item 4 é o que mais tenta vazar: "banco de dados indisponível" parece
uma mensagem honesta e útil. Ela diz a quem está atacando que o ataque
funcionou.
:::

:::exercise level=2
Escreva `LeitorComPendencia` herdando de `ExcecaoDeDominio`. Ela carrega o
id do leitor e a multa em aberto como `Dinheiro`, e a mensagem deve dizer o
valor formatado.

Depois responda: o valor da multa deve aparecer na resposta da API? Para
quem?

:::answer
```php title="app/Emprestimos/LeitorComPendencia.php" numbered
final class LeitorComPendencia extends ExcecaoDeDominio
{
    public function __construct(
        public readonly int $leitorId,
        public readonly Dinheiro $multa,
    ) {
        parent::__construct(sprintf(
            'Há uma multa de %s em aberto.',
            $multa->formatado(),
        ));
    }

    public function tipo(): string
    {
        return 'leitor-com-pendencia';
    }
}
```

**Deve aparecer?** Para o próprio leitor e para a equipe, sim: é a
informação que permite resolver. O leitor quer saber quanto pagar.

O cuidado é que a mensagem vai para **quem fez a requisição**, e no painel
da atendente quem fez a requisição é a atendente — que tem direito ao dado.
No aplicativo, só o próprio leitor consegue pedir empréstimo em nome dele,
então só ele vê.

Se algum dia existir uma rota em que um leitor aja em nome de outro —
reserva para um dependente, por exemplo —, essa mensagem passa a vazar a
dívida de uma pessoa para outra. Vale anotar o risco na classe, porque é o
tipo de coisa que a pessoa que criar a rota nova não vai lembrar de
conferir.
:::

:::exercise level=3
Uma pessoa do time propõe tirar o `RespostaDeErro` e, em vez dele, pôr um
`try/catch` em cada controller, "para cada rota ter controle total da sua
resposta de erro".

Escreva os argumentos a favor que ela provavelmente tem, os três custos
concretos da proposta, e o caso em que um `try/catch` no controller é, de
fato, a escolha certa.

:::answer
**A favor, provavelmente.** Localidade: quem lê o controller vê o que
acontece em cada falha, sem abrir outro arquivo. Flexibilidade: uma rota
específica pode querer uma resposta diferente para a mesma exceção.

**Custo um: o formato diverge.** Trinta controllers com `try/catch` são
trinta lugares montando o JSON de erro, e em seis meses são quatro formatos
diferentes. É o problema que o capítulo começou resolvendo.

**Custo dois: o `default` some.** O handler central garante que **toda**
exceção não prevista vira um `500` seguro com incidente. O `try/catch` no
controller trata as que o autor lembrou; a que ele não lembrou sobe sem
tratamento — ou, pior, é capturada por um `catch (\Throwable $e)` que
devolve a mensagem crua.

**Custo três: o controller volta a crescer e a conhecer status.** Cada
método ganha dez linhas de `catch` que não são a responsabilidade dele.

**Quando o `try/catch` no controller é certo:** quando a exceção muda **o
caminho** e não só a resposta. O painel Blade do capítulo @cap:blade captura
`ExemplarIndisponivel` para devolver a pessoa ao formulário com o erro no
campo — ali, o comportamento é outro, não só o formato. E quando uma rota
precisa tentar uma alternativa: se a capa não for encontrada no
armazenamento, devolver a capa padrão.

A régua: o controller captura quando **faz algo diferente** com a falha.
Quando só vai formatar, o handler já faz.
:::
