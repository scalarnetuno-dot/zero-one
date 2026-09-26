---
title: "Mirabel dentro do Laravel"
number: 12
slug: mirabel-dentro-do-laravel
part: p3
kicker: "Seis chamadas saíram do checkout numa tarde. A linha do comentário pedindo para não mexer ficou — por enquanto."
goal: >-
  Trocar as chamadas síncronas do checkout por um evento, rodar workers
  como comandos Artisan, não cair na armadilha do config:cache com as
  variáveis da biblioteca e testar o checkout sem RabbitMQ no ar.
---

:::story Trezentos e oitenta a hora
A Júlia marcou uma hora com o Marcelão antes de mexer no checkout. Ele
entrou na chamada de vídeo de dentro do carro.

— O `finalizarPedido`? Isso aí eu fiz correndo, na véspera da Black
Friday de 2023.

— Por que o `try/catch` da SEFAZ está vazio?

— Porque ela caía e derrubava o pedido. Aí eu pus o `try` e o pedido
parou de cair.

— E a nota?

— A nota o Seu Norberto emitia na mão, no dia seguinte. Ele reclamou por
uma semana e depois parou.

— Ele parou de reclamar ou parou de emitir?

O Marcelão pensou.

— Isso eu não sei.

A chamada durou onze minutos. No fim do mês, a Doce Mirabel recebeu uma
nota fiscal de R$ 380, referente a "consultoria técnica — 1 hora".
:::

O checkout do Marcelão é um controller Laravel, e a Mirabel não depende
do Laravel — ela lê o ambiente, abre a conexão sozinha e não conhece nada
do framework. As duas convivem sem adaptador. O que o Laravel acrescenta
são três cuidados: onde o evento é publicado, como o worker roda, e como
as variáveis chegam à biblioteca depois do deploy.

## O checkout, desmontado

A loja nova é um projeto Laravel com a Mirabel instalada como no capítulo
@cap:por-que-uma-biblioteca. O evento é o mesmo de antes, agora dentro do
namespace da aplicação:

```php title="app/Eventos/PedidoPago.php" numbered
<?php

declare(strict_types=1);

namespace App\Eventos;

use Mirabel\RabbitMQ\Event;

final class PedidoPago extends Event
{
    public static string $routingKey = 'pedido.pago';
    public static int $schemaVersion = 2;
}
```

O controller deixa de chamar seis serviços e passa a gravar o pedido e
publicar que ele foi pago:

```php title="app/Http/Controllers/CheckoutController.php" numbered
<?php

namespace App\Http\Controllers;

use App\Eventos\PedidoPago;
use App\Mensageria\Publicador;
use App\Models\Pedido;
use Illuminate\Http\Request;

class CheckoutController extends Controller
{
    public function finalizar(Request $request, Publicador $pub)
    {
        $dados = $request->validate([
            'total_centavos' => ['required', 'integer', 'min:1'],
            'cep' => ['required', 'regex:/^\d{5}-\d{3}$/'],
        ]);

        // o pagamento continua síncrono: sem ele, não existe pedido
        $pedido = Pedido::create($dados);

        $pub->publicar(new PedidoPago([
            'pedido' => $pedido->id,
            'total_centavos' => $pedido->total_centavos,
            'entrega' => ['cep' => $pedido->cep],
        ]), "pedido-{$pedido->id}-pago");

        return response()->json(['pedido' => $pedido->id], 201);
    }
}
```

A cobrança no gateway foi omitida do exemplo para caber na página — no
checkout de verdade ela continua ali, antes do `create`, porque é o único
passo da tabela do capítulo @cap:a-black-friday-que-durou-quatro-horas
que precisa acontecer antes da resposta. Estoque, nota, etiqueta, e-mail,
WhatsApp e pontos viraram consumidores do `pedido.pago`.

O `Publicador` injetado no método é uma classe pequena da aplicação, e ela
existe por um motivo que aparece na hora do teste:

```php title="app/Mensageria/Publicador.php" numbered
<?php

declare(strict_types=1);

namespace App\Mensageria;

use Illuminate\Support\Str;
use Mirabel\RabbitMQ\Event;

class Publicador
{
    public function publicar(Event $evento, string $chave): void
    {
        $conversa = request()->header('X-Request-Id')
            ?? (string) Str::uuid();

        $evento->publish(
            messageId: $chave,
            correlationId: $conversa,
            idempotencyKey: $chave,
        );
    }
}
```

Ele também concentra a política de identidade do capítulo
@cap:eventos-com-mirabel num lugar só: a chave estável vem do pedido, e o
`correlation_id` vem do cabeçalho `X-Request-Id` da requisição — que um
proxy ou balanceador costuma preencher —, ou de um UUID novo.
`Str::uuid()` gera um identificador aleatório de 36 caracteres.

```text
$ curl -X POST localhost:8000/api/checkout \
    -H 'content-type: application/json' \
    -H 'accept: application/json' \
    -d '{"total_centavos":8990,"cep":"37701-000"}'
{"pedido":1}
```

A resposta sai em menos de meio segundo no servidor de desenvolvimento, e
o tempo não depende mais de SEFAZ, ERP, transportadora nem WhatsApp. Se
qualquer um deles cair durante a Black Friday, o checkout nem fica
sabendo.

## O worker como comando Artisan

O `consumir.php` da Parte 3 funciona, mas dentro do Laravel um worker
precisa do framework carregado — banco, log, configuração. O jeito natural
é um comando Artisan:

```php title="app/Console/Commands/Consumir.php" numbered
<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Mirabel\RabbitMQ\Worker;

class Consumir extends Command
{
    protected $signature = 'rabbitmq:consume {worker}';

    protected $description = 'Roda um worker da Mirabel';

    public function handle(): int
    {
        $classe = 'App\\Workers\\' . $this->argument('worker');
        if (!is_subclass_of($classe, Worker::class)) {
            $this->error("{$classe} não é um worker.");

            return self::INVALID;
        }

        $this->info("consumindo com {$classe}");
        $this->laravel->make($classe)->subscribe();

        return self::SUCCESS;
    }
}
```

`$signature` define o nome do comando e o argumento `{worker}`.
`is_subclass_of()` confere se a classe existe e estende `Worker` — sem
isso, um erro de digitação viraria uma exceção confusa. `$this->laravel->make()`
cria o worker pelo container do Laravel, o que permite ao worker receber
dependências no construtor, como qualquer controller.

O worker, dentro da aplicação, pode usar o log do framework. A Mirabel
aceita qualquer logger no padrão PSR-3, a interface de log que o Laravel
implementa:

```php title="app/Workers/EmitirNotaFiscal.php" numbered
<?php

declare(strict_types=1);

namespace App\Workers;

use Illuminate\Support\Facades\Log;
use Mirabel\RabbitMQ\Envelope;
use Mirabel\RabbitMQ\Worker;
use Psr\Log\LoggerInterface;

final class EmitirNotaFiscal extends Worker
{
    public static string $queue = 'fiscal.pedidos-pagos';
    public static array $routingKeys = ['pedido.pago'];

    public function handle(Envelope $envelope): void
    {
        $pedido = $envelope->body['pedido'];
        Log::info('NF-e emitida', ['pedido' => $pedido]);
    }

    protected function logger(): LoggerInterface
    {
        return Log::channel();
    }
}
```

Sobrescrever `logger()` faz as mensagens da própria biblioteca —
reconexão, retry, mensagem enviada para a fila de erro — irem para o
`storage/logs/laravel.log`, junto com as da aplicação.

```text
$ php artisan rabbitmq:consume EmitirNotaFiscal
consumindo com App\Workers\EmitirNotaFiscal
```

E, depois de um checkout:

```text
[2026-09-25 23:51:14] local.INFO: NF-e emitida {"pedido":1}
```

## A variável que some no deploy

A Mirabel lê o ambiente com `getenv()`. O Laravel lê o `.env` e, em
desenvolvimento, copia os valores para o ambiente do processo — por isso
tudo funciona no seu notebook com as variáveis no `.env`.

Em produção, o deploy de um projeto Laravel roda `php artisan
config:cache`, que junta todos os arquivos de `config/` num arquivo só e,
a partir daí, **para de ler o `.env`**. Os valores de `config()` continuam
certos, porque foram guardados no cache. Os de `getenv()`, não:

```text
$ php artisan tinker --execute="var_dump(getenv('MB_RABBITMQ_PORT'));"
string(4) "5673"
$ php artisan config:cache
$ php artisan tinker --execute="var_dump(getenv('MB_RABBITMQ_PORT'));"
bool(false)
```

Com `false`, a biblioteca usa o padrão — `localhost`, porta 5672,
exchange `my-exchange`. Em produção, isso é um checkout que publica num
broker que não existe, ou, pior, num exchange em que ninguém escuta, sem
erro nenhum.

A correção é dar à biblioteca o que ela lê. As variáveis vão para um
arquivo de configuração, que o cache preserva:

```php title="config/mirabel_rabbitmq.php" numbered
<?php

return [
    'MB_RABBITMQ_HOST' => env('MB_RABBITMQ_HOST', '127.0.0.1'),
    'MB_RABBITMQ_PORT' => env('MB_RABBITMQ_PORT', 5672),
    'MB_RABBITMQ_USER' => env('MB_RABBITMQ_USER', 'guest'),
    'MB_RABBITMQ_PASSWORD' => env('MB_RABBITMQ_PASSWORD', 'guest'),
    'MB_RABBITMQ_EXCHANGE' =>
        env('MB_RABBITMQ_EXCHANGE', 'doce.eventos'),
];
```

E, no boot da aplicação, são exportadas de volta para o ambiente:

```php title="app/Support/MirabelEnvironment.php" numbered
<?php

declare(strict_types=1);

namespace App\Support;

final class MirabelEnvironment
{
    /** @param array<string, scalar|null> $variaveis */
    public static function exportar(array $variaveis): void
    {
        foreach ($variaveis as $nome => $valor) {
            if ($valor === null || getenv($nome) !== false) {
                continue;
            }

            if (is_bool($valor)) {
                $valor = $valor ? 'true' : 'false';
            }
            putenv("{$nome}={$valor}");
        }
    }
}
```

```php title="app/Providers/AppServiceProvider.php"
public function boot(): void
{
    MirabelEnvironment::exportar(config('mirabel_rabbitmq', []));
}
```

`putenv()` define uma variável de ambiente para o processo atual. A linha
13 garante que uma variável definida de verdade pelo servidor — no
Docker, no systemd — sempre ganha do arquivo: a ponte só preenche o que
está faltando.

```text
$ php artisan config:cache
$ php artisan tinker --execute="var_dump(getenv('MB_RABBITMQ_PORT'));"
string(4) "5673"
```

:::key
Toda biblioteca que lê `getenv()` sofre do mesmo problema dentro de um
Laravel com `config:cache`. A regra é a do framework: `env()` só dentro de
`config/`; todo o resto lê `config()` — e, quando uma biblioteca precisa
do ambiente, alguém copia `config()` para lá no boot.
:::

## Testar sem RabbitMQ

Um teste que precisa de um broker no ar é um teste que falha no CI, no
notebook de quem esqueceu o Docker e na máquina de quem só quer rodar a
suíte. O `Publicador` existe para isso: no teste, ele é trocado por um que
só anota o que teria publicado.

```php title="tests/Feature/CheckoutTest.php" numbered
<?php

namespace Tests\Feature;

use App\Eventos\PedidoPago;
use App\Mensageria\Publicador;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Mirabel\RabbitMQ\Event;
use Tests\TestCase;

class CheckoutTest extends TestCase
{
    use RefreshDatabase;

    public function test_checkout_publica_pedido_pago(): void
    {
        $publicador = new PublicadorFalso();
        $this->app->instance(Publicador::class, $publicador);

        $this->postJson('/api/checkout', [
            'total_centavos' => 8990,
            'cep' => '37701-000',
        ])->assertCreated();

        $this->assertCount(1, $publicador->publicados);
        [$evento, $chave] = $publicador->publicados[0];
        $this->assertInstanceOf(PedidoPago::class, $evento);
        $this->assertSame(8990, $evento->payload['total_centavos']);
        $this->assertSame('pedido-1-pago', $chave);
    }
}

class PublicadorFalso extends Publicador
{
    public array $publicados = [];

    public function publicar(Event $evento, string $chave): void
    {
        $this->publicados[] = [$evento, $chave];
    }
}
```

`$this->app->instance()` diz ao container do Laravel: quando alguém pedir
um `Publicador`, entregue **este** objeto. O controller recebe o falso sem
saber, e o teste confere o que ele teria mandado — o tipo do evento, o
total em centavos, a chave de idempotência.

```text
$ php artisan test
  PASS  Tests\Feature\CheckoutTest
  ✓ checkout publica pedido pago
```

O teste prova que o checkout **publica o evento certo**. Ele não prova que
o RabbitMQ entrega, e não precisa: isso a biblioteca prova com os testes
dela, que rodam contra um broker de verdade.

:::milestone
Você tem: o `CheckoutController` gravando o pedido e publicando
`PedidoPago` em vez de chamar seis serviços; o worker do fiscal rodando
como `php artisan rabbitmq:consume EmitirNotaFiscal`; as variáveis da
biblioteca sobrevivendo ao `config:cache`; e um teste de feature que roda
sem broker.
:::

:::summary
- A Mirabel não depende do Laravel e convive com ele sem adaptador; o
	checkout grava o pedido e publica `PedidoPago`, e o resto vira
	consumidor.
- Um `Publicador` da aplicação concentra a política de identidade e é o
	ponto de troca nos testes.
- Workers rodam como comando Artisan, criados pelo container, com o log do
	framework via `logger()`.
- `config:cache` faz o Laravel parar de ler o `.env`: `getenv()` volta
	`false` e a biblioteca cai nos padrões. A saída é config em `config/` e
	`putenv()` no boot.
- `$this->app->instance()` troca o publicador por um falso, e o teste de
	feature roda sem RabbitMQ.
:::

:::exercise level=1
Escreva um segundo teste: um checkout com CEP sem hífen (`37701000`) deve
responder 422 e **não** publicar nada.

:::answer
```php
public function test_cep_invalido_nao_publica_nada(): void
{
    $publicador = new PublicadorFalso();
    $this->app->instance(Publicador::class, $publicador);

    $this->postJson('/api/checkout', [
        'total_centavos' => 8990,
        'cep' => '37701000',
    ])->assertUnprocessable();

    $this->assertSame([], $publicador->publicados);
}
```

`assertUnprocessable()` confere o status 422, que o `validate()` do
Laravel devolve quando uma regra falha. A validação acontece antes do
`create` e do `publicar`, então nenhum pedido é gravado e nenhum evento
sai — que é exatamente o que o teste afirma.
:::

:::exercise level=2
O checkout grava o pedido e depois publica. Descreva o que acontece com o
pedido 40117 se o broker estiver fora do ar no momento do `publicar()`, e
se a ordem inversa — publicar antes de gravar — seria melhor.

:::answer
O `Pedido::create` já rodou: o pedido está no banco. O `publicar()`
tenta algumas vezes, desiste e lança exceção; o controller não trata, e o
cliente recebe erro 500. Resultado: um pedido pago e gravado cujo evento
nunca saiu — sem nota, sem etiqueta, sem e-mail, e o cliente achando que
a compra falhou.

Inverter não resolve, troca o defeito. Publicando antes, se o banco falhar
no `create`, sai um `pedido.pago` de um pedido que não existe, e o fiscal
emite nota de nada. O problema é que banco e broker são dois sistemas, e
não há transação que abrace os dois. É o mesmo problema da pasta de
arquivos, entre "fiz" e "apaguei", agora entre "gravei" e "publiquei".
:::
