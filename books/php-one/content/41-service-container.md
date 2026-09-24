---
title: "Service Container e injeção de dependência"
number: 41
slug: service-container
part: p9
kicker: "Dedé abriu o contêiner de vinte linhas ao lado do contêiner do Laravel. A estagiária reconheceu a reflexão antes dele apontar."
goal: >-
  Entender o mecanismo que monta os objetos da aplicação, declarar
  dependência pelo construtor, escolher entre bind, singleton e scoped, e
  trocar uma implementação no teste sem tocar em quem a usa.
---

:::story A mesma linha
Dedé dividiu a tela em duas. À esquerda, o `mini.php` do capítulo das
quarenta linhas. À direita, um arquivo do próprio Laravel, dentro de
`vendor/`, com mais de mil e quinhentas linhas.

— Procura — disse ele.

Tainá rolou a da direita por um tempo. Parou num método chamado `build`.

```php
$reflector = new ReflectionClass($concrete);
// ...
$constructor = $reflector->getConstructor();
// ...
$dependencies = $constructor->getParameters();
```

— É o nosso.

— É o nosso com quinze anos de gente reclamando.

— O que são as outras mil e quatrocentas linhas?

— Cada reclamação.

Ela rolou mais um pouco.

— Tem um `singleton` aqui.

— O nosso também tinha. Lembra do `$feitos`?

— Guardava tudo.

— Então. O nosso só sabia fazer singleton.
:::

## O `new` espalhado pelo código é o problema

O `EmprestimoController` precisa avisar o leitor quando um empréstimo é
feito. A primeira versão é direta:

```php
public function store(RealizarEmprestimoRequest $request)
{
    // ... o empréstimo ...

    $enviador = new EnviadorDeWhatsApp(
        new Client(['timeout' => 5]),
        'https://api.provedor.com.br',
        'chave-fixa-no-codigo',
    );

    $enviador->enviar($leitor->telefone, 'Empréstimo feito.');
}
```

Funciona, e tem três problemas que crescem em direções diferentes.

**O controller sabe demais.** Ele sabe que o aviso é por WhatsApp, qual
biblioteca HTTP o enviador usa, qual o timeout, qual a URL do provedor. Nada
disso é assunto de quem registra um empréstimo.

**Trocar custa uma busca.** Quando a biblioteca trocar de provedor — e vai
trocar, porque a verba do edital cobre só um ano de mensagens —, o `new
EnviadorDeWhatsApp` precisa ser procurado e trocado em todos os lugares em
que aparece. São quatro hoje.

**Testar é impossível.** Todo teste que passa por esse método manda uma
mensagem de verdade para o telefone de alguém. Ou falha, porque o servidor
de teste não tem internet — e o teste falha por um motivo que não tem nada a
ver com o que ele queria provar.

O problema não é o `new`. É **quem** faz o `new`. A classe que usa o
enviador não deveria ser a classe que o monta.

## Pedir em vez de montar

A troca é pequena no código e grande no desenho: a classe **declara o que
precisa**, e alguém de fora entrega.

```php title="app/Http/Controllers/EmprestimoController.php" numbered
public function __construct(
    private readonly EnviadorDeAviso $avisos,
) {}

public function store(RealizarEmprestimoRequest $request)
{
    // ... o empréstimo ...

    $this->avisos->enviar($leitor, 'Empréstimo feito.');
}
```

O controller não sabe mais nada sobre WhatsApp. Ele sabe que existe
alguém que envia avisos, e que esse alguém tem um método `enviar`.

:::term Injeção de dependência
Entregar a um objeto as coisas de que ele precisa, em vez de deixá-lo
criá-las. O nome é pomposo para uma ideia que cabe numa frase: **peça no
construtor, não construa dentro**.
:::

Quem entrega? Alguém precisa fazer o `new` em algum momento. Num programa
pequeno, é o `index.php`, à mão. Num projeto Laravel, é o **Service
Container** — o mesmo mecanismo que entregou o `StoreLivroRequest` ao
`store` no capítulo @cap:validation-e-form-requests, e o `Livro` ao `show`
no capítulo @cap:rotas-e-controllers.

## O contêiner monta o grafo

Quando o Laravel precisa de um `EmprestimoController`, ele faz o que o
contêiner de vinte linhas do capítulo
@cap:um-framework-de-quarenta-linhas fazia:

1. Olha o construtor por reflexão.
2. Vê que ele pede um `EnviadorDeAviso`.
3. Tenta construir um `EnviadorDeAviso`, olhando o construtor **dele**.
4. Repete, descendo, até chegar em classes sem dependências.
5. Monta tudo de baixo para cima e entrega.

O resultado é um **grafo**: o controller depende do enviador, que depende
do cliente HTTP, que depende da configuração. Ninguém escreve esse grafo à
mão. Cada classe declara só o seu vizinho imediato, e o contêiner encadeia.

:::diagram type="flowchart" caption="Cada classe declara só o vizinho de baixo. O contêiner percorre a cadeia inteira."
nodes:
  - { id: c, type: process, text: "EmprestimoController" }
  - { id: s, type: process, text: "EmprestimoService" }
  - { id: e, type: process, text: "EnviadorDeAviso" }
  - { id: h, type: process, text: "cliente HTTP" }
  - { id: r, type: io,      text: "config('avisos')" }
edges:
  - { from: c, to: s }
  - { from: c, to: e }
  - { from: s, to: e }
  - { from: e, to: h }
  - { from: e, to: r }
:::

### Autowiring, e onde ele para

Quando o tipo pedido é uma **classe concreta** com dependências que também
são classes concretas, o contêiner resolve sozinho. Isso tem nome:
*autowiring*. A maior parte das classes de um projeto Laravel nunca precisa
de nenhuma configuração para ser injetada.

Ele para em dois lugares, e os dois são o mesmo que parava o contêiner de
vinte linhas:

**Tipos primitivos.** Um construtor que pede `string $chave` não tem como
ser adivinhado. Qual string?

**Interfaces.** `EnviadorDeAviso` é uma interface. O contêiner não sabe qual
das implementações você quer — nem se existe alguma.

```text
Target [App\Avisos\EnviadorDeAviso] is not instantiable while
building [App\Http\Controllers\EmprestimoController].
```

A mensagem é boa: diz o que ele tentou construir e para quem. A resposta é
dizer ao contêiner o que fazer.

## `bind`, `singleton` e `scoped`

O contêiner aceita instruções: "quando pedirem X, entregue Y". Existem três
formas, e a diferença entre elas é **quantas vezes o objeto é criado**.

```php
$this->app->bind(EnviadorDeAviso::class, EnviadorDeWhatsApp::class);
```

**`bind`** cria um objeto novo **toda vez** que alguém pede. Duas classes
que pedem `EnviadorDeAviso` na mesma requisição recebem duas instâncias
diferentes.

```php
$this->app->singleton(ClienteDoProvedor::class, fn () =>
    new ClienteDoProvedor(
        config('avisos.url'),
        config('avisos.chave'),
    ));
```

**`singleton`** cria **uma vez** e entrega a mesma instância para sempre —
para todas as requisições que aquele processo atender.

```php
$this->app->scoped(LeitorAtual::class);
```

**`scoped`** cria uma vez **por requisição** e descarta no fim.

| | Instâncias | Serve para |
|---|---|---|
| `bind` | uma por pedido | objetos baratos, sem estado |
| `singleton` | uma por processo | conexões, clientes caros de criar |
| `scoped` | uma por requisição | estado da requisição atual |

Tabela: A escolha errada entre `singleton` e `scoped` não dá erro. Dá um
comportamento que só aparece com dois usuários ao mesmo tempo.

:::pitfall
`singleton` guardando estado de requisição é o defeito clássico do
contêiner.

```php
$this->app->singleton(LeitorAtual::class);
```

Com o PHP tradicional, cada requisição começa do zero e o processo morre no
fim — o singleton vive uma requisição só, e o defeito não aparece. Mas os
workers de fila do capítulo @cap:events-jobs-e-filas e servidores de
aplicação que mantêm o processo vivo **reaproveitam o processo**. O leitor
da primeira requisição continua lá na segunda.

A Rosângela abre o aplicativo e vê os empréstimos do Wellington. Não por
invasão — por um `singleton` que devia ser `scoped`.
:::

## Service Provider: onde as instruções moram

As instruções ao contêiner precisam ficar em algum lugar que rode antes de
qualquer requisição. Esse lugar é o **service provider**, e o capítulo
@cap:o-que-e-o-laravel já o apresentou de passagem.

```text
$ php artisan make:provider AvisoServiceProvider
```

```php title="app/Providers/AvisoServiceProvider.php" numbered
<?php

declare(strict_types=1);

namespace App\Providers;

use App\Avisos\EnviadorDeAviso;
use App\Avisos\EnviadorDeWhatsApp;
use App\Avisos\ClienteDoProvedor;
use Illuminate\Support\ServiceProvider;

class AvisoServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(
            ClienteDoProvedor::class,
            fn () => new ClienteDoProvedor(
                url: config('avisos.url'),
                chave: config('avisos.chave'),
                timeout: config('avisos.timeout', 5),
            ),
        );

        $this->app->bind(
            EnviadorDeAviso::class,
            EnviadorDeWhatsApp::class,
        );
    }
}
```

O Laravel 11 registra o provider novo em `bootstrap/providers.php`, e o
`make:provider` já acrescenta a linha.

Repare onde os primitivos foram parar: a URL, a chave e o timeout vêm do
`config()`, que vem do `.env` — o caminho do capítulo
@cap:configuracao-ambiente-e-artisan. O provider é o **único** lugar do
projeto que sabe como montar o cliente do provedor. Trocar de provedor é
mudar este arquivo.

### `register` e `boot`

Um provider tem dois métodos, e a diferença entre eles é de ordem.

**`register`** roda primeiro, em todos os providers, e serve **só** para
ensinar o contêiner. Nele, você ainda não pode pedir nada ao contêiner,
porque outros providers podem não ter registrado o que você precisa.

**`boot`** roda depois de todos os `register`. Nele, o contêiner está
completo, e você pode usá-lo — registrar eventos, configurar o
`preventLazyLoading`, ligar observadores.

A regra prática: se a linha começa com `$this->app->bind` ou `singleton`,
vai no `register`. Se usa alguma coisa, vai no `boot`.

## Interface no construtor, implementação no provider

O ganho de tudo isso está numa troca de uma linha. A interface:

```php title="app/Avisos/EnviadorDeAviso.php" numbered
interface EnviadorDeAviso
{
    public function enviar(Leitor $leitor, string $texto): void;
}
```

E duas implementações. A real conversa com o provedor. A outra existe para
desenvolvimento:

```php title="app/Avisos/EnviadorNoLog.php" numbered
final class EnviadorNoLog implements EnviadorDeAviso
{
    public function enviar(Leitor $leitor, string $texto): void
    {
        Log::info('aviso', [
            'leitor' => $leitor->id,
            'texto' => $texto,
        ]);
    }
}
```

```php title="app/Providers/AvisoServiceProvider.php" numbered
$this->app->bind(
    EnviadorDeAviso::class,
    $this->app->isProduction()
        ? EnviadorDeWhatsApp::class
        : EnviadorNoLog::class,
);
```

Em desenvolvimento, nenhum aviso sai do computador de ninguém. Em produção,
sai. Nenhum controller, nenhum service e nenhuma linha de regra de negócio
sabe da diferença.

É a interface do capítulo @cap:heranca-interfaces-e-traits cumprindo o que
aquele capítulo prometeu: um contrato que o Laravel pede o tempo todo. O
contêiner é o motivo pelo qual as interfaces valem tanto num projeto
Laravel — sem ele, alguém teria de escolher a implementação à mão em cada
lugar.

:::key
A pergunta que decide se vale criar uma interface: **existe, ou vai
existir, uma segunda implementação?** Uma real e uma de teste contam como
duas.

`EnviadorDeAviso` tem três: WhatsApp, log e o falso do teste. Vale.
`CalculadoraDeMulta` tem uma, e a de teste seria igual à real — porque ela
é pura. Não vale: injete a classe concreta, e o autowiring resolve.
:::

## Trocar a implementação no teste

O terceiro problema do começo do capítulo era testar. Com o enviador vindo
do contêiner, o teste pode pôr outro no lugar:

```php title="tests/Feature/EmprestimoTest.php" numbered
test('avisa o leitor ao emprestar', function () {
    $falso = new EnviadorFalso();
    $this->app->instance(EnviadorDeAviso::class, $falso);

    $this->postJson('/api/emprestimos', [
        'exemplar_id' => 2117,
        'leitor_id' => 47,
    ])->assertCreated();

    expect($falso->enviados)->toHaveCount(1)
        ->and($falso->enviados[0]['leitor'])->toBe(47);
});
```

```php title="tests/Fakes/EnviadorFalso.php" numbered
final class EnviadorFalso implements EnviadorDeAviso
{
    public array $enviados = [];

    public function enviar(Leitor $leitor, string $texto): void
    {
        $this->enviados[] = [
            'leitor' => $leitor->id,
            'texto' => $texto,
        ];
    }
}
```

`$this->app->instance()` diz ao contêiner: "a partir de agora, quando
pedirem `EnviadorDeAviso`, entregue **este objeto aqui**". O controller
recebe o falso, e o teste confere o que ficou guardado nele.

Nenhuma linha do controller mudou para permitir o teste. Essa é a
diferença entre código testável e código que precisa ser adaptado para
teste — e o capítulo @cap:testes volta a ela com mais calma.

## As duas formas de usar o contêiner errado

**O *service locator*.** O contêiner está sempre acessível pela função
`app()`, e isso permite escrever:

```php
public function store(RealizarEmprestimoRequest $request)
{
    $avisos = app(EnviadorDeAviso::class);
    // ...
}
```

Funciona, e desfaz metade do ganho. A dependência sumiu do construtor, e
quem lê a classe não sabe mais do que ela precisa sem ler cada método. O
teste ainda consegue trocar, mas só se souber que a troca é necessária.

A regra: `app()` no meio do código é sintoma. Os lugares legítimos são o
provider, e código de framework que não tem construtor sob seu controle.

**As *facades* sem entender o que são.** `Log::info()`, `Cache::get()`,
`DB::transaction()` parecem chamadas estáticas, e não são. Cada *facade* é
uma classe pequena que, na chamada, pede ao contêiner o objeto real e
repassa o método para ele.

```php
Log::info('x');
// é, na prática,
app('log')->info('x');
```

Elas são convenientes e são um *service locator* com roupa bonita — a
dependência não aparece no construtor. O Laravel compensa com métodos de
teste próprios (`Log::spy()`, `Cache::fake()`), e por isso o custo é menor
do que parece. Para as dependências **do seu domínio** — o enviador, o
service de empréstimo —, construtor. Para a infraestrutura do framework,
*facade* é aceitável e é o idioma do ecossistema.

:::note Na sua carreira
Injeção de dependência é um dos assuntos em que a distância entre o nome e
a ideia mais atrapalha. Em entrevista, a pergunta vem com "IoC", "DI",
"inversão de controle", e a pessoa que sabe usar trava no vocabulário.

A resposta que funciona em qualquer entrevista é concreta: "a classe pede
no construtor o que precisa, e quem monta decide qual implementação
entregar; no Laravel, quem monta é o contêiner, e eu registro as escolhas
num provider". Uma frase, e ela mostra que você usa, não que decorou.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/Avisos/
    EnviadorDeAviso.php      # interface
    EnviadorDeWhatsApp.php   # produção
    EnviadorNoLog.php        # desenvolvimento
    ClienteDoProvedor.php
  app/Providers/
    AvisoServiceProvider.php # a única escolha, num lugar
  config/avisos.php
  tests/Fakes/
    EnviadorFalso.php
:::

:::summary
- O problema não é o `new`; é quem o faz. A classe que usa não deveria ser
  a que monta.
- Injeção de dependência é pedir no construtor em vez de construir dentro.
- O contêiner lê construtores por reflexão e monta o grafo inteiro; é o
  contêiner de vinte linhas com quinze anos de uso.
- Autowiring resolve classes concretas; para interfaces e primitivos, o
  contêiner precisa de instrução.
- `bind` cria sempre; `singleton` cria uma vez por processo; `scoped`, uma
  vez por requisição.
- `singleton` com estado de requisição vaza dado entre usuários quando o
  processo é reaproveitado.
- Providers ensinam o contêiner no `register` e usam o contêiner no
  `boot`.
- Interface vale quando há, ou vai haver, uma segunda implementação — e a
  de teste conta.
- `$this->app->instance()` troca a implementação no teste sem tocar no
  código.
- `app()` no meio do código é *service locator*; *facades* são isso com
  método de teste.
:::

:::checkpoint
Você declara dependências pelo construtor, registra num provider qual
implementação atende a cada interface, escolhe entre `bind`, `singleton` e
`scoped` pelo tempo de vida do estado, e troca uma implementação no teste
sem alterar nenhuma linha de quem a usa.
:::

:::exercise level=1
Diga se cada registro deveria ser `bind`, `singleton` ou `scoped`:

1. O cliente HTTP do provedor de mensagens, com conexão reaproveitável.
2. Um objeto que guarda o usuário autenticado da requisição.
3. Uma calculadora de multa sem estado, barata de criar.
4. O leitor de configuração da biblioteca, carregado de um arquivo.

:::answer
1. `singleton`. Criar custa, e reaproveitar a conexão é o objetivo.
2. `scoped`. Ele é, por definição, estado da requisição atual. Como
   `singleton`, vazaria entre requisições num worker.
3. Nenhum registro. É uma classe concreta sem dependências primitivas, e
   o autowiring resolve sozinho — com o comportamento de `bind`.
4. `singleton`, **se** o conteúdo não muda enquanto o processo vive. Se a
   configuração pode mudar e o worker não reinicia, o singleton vai servir
   a versão velha até o deploy seguinte.

O item 3 é o ponto do exercício: a maior parte das classes não precisa ser
registrada. Um provider com cinquenta `bind` de classes concretas é
configuração que o contêiner já fazia sozinho.
:::

:::exercise level=2
Este service funciona e não é testável sem mandar e-mail de verdade.
Reescreva-o com injeção de dependência e mostre o registro no provider.

```php
class LembreteDeDevolucao
{
    public function enviarParaAtrasados(): int
    {
        $mailer = new SmtpMailer(
            env('SMTP_HOST'), env('SMTP_USER'), env('SMTP_PASS'),
        );

        $atrasados = Emprestimo::emAtraso()->with('leitor')->get();

        foreach ($atrasados as $e) {
            $mailer->send($e->leitor->email, 'Devolva o livro');
        }

        return $atrasados->count();
    }
}
```

:::answer
```php title="app/Avisos/LembreteDeDevolucao.php" numbered
final class LembreteDeDevolucao
{
    public function __construct(
        private readonly EnviadorDeAviso $avisos,
    ) {}

    public function enviarParaAtrasados(): int
    {
        $atrasados = Emprestimo::emAtraso()
            ->with('leitor')
            ->get();

        foreach ($atrasados as $e) {
            $this->avisos->enviar(
                $e->leitor,
                'Devolva o livro',
            );
        }

        return $atrasados->count();
    }
}
```

O registro já existe — é o `bind` de `EnviadorDeAviso` no
`AvisoServiceProvider`. O `LembreteDeDevolucao` em si não precisa de
registro nenhum: é concreto, e o autowiring entrega o enviador.

Três correções vieram juntas, e a terceira é de outro capítulo: o `env()`
fora de `config/`, que devolveria nulo depois do `config:cache`. Ele sumiu
porque a montagem do cliente sumiu daqui — foi para o provider, que lê de
`config('avisos')`.

E a troca de canal veio de graça: o lembrete agora vai pelo enviador da
biblioteca, que hoje é WhatsApp, e não por um e-mail que metade dos
leitores não tem.
:::

:::exercise level=3
Em produção, o aplicativo começou a mostrar, raramente, o nome de outro
leitor no cabeçalho da tela de empréstimos. Não é reproduzível na máquina
de ninguém. O projeto tem, num provider:

```php
$this->app->singleton(ContextoDoLeitor::class, function ($app) {
    return new ContextoDoLeitor(
        $app['request']->user()?->leitor,
    );
});
```

Explique por que o defeito só aparece em produção, por que é raro, e
corrija. Depois diga que outro sintoma o mesmo defeito produziria nos
workers de fila.

:::answer
**Por que só em produção.** Em desenvolvimento, `php artisan serve` atende
cada requisição num ambiente em que o estado não sobrevive entre elas de
forma perceptível para uma pessoa testando sozinha. Em produção, se a
aplicação roda com um servidor que mantém o processo vivo entre
requisições, o singleton criado na primeira requisição daquele processo
**continua lá**. A requisição seguinte, de outra pessoa, recebe o
`ContextoDoLeitor` com o leitor da primeira.

**Por que é raro.** Depende de qual processo atende qual requisição e de
quem chegou primeiro em cada um. Com muitos processos e pouca carga, a
mesma pessoa tende a cair em processos que ela mesma "inaugurou".

**A correção:**

```php
$this->app->scoped(ContextoDoLeitor::class, function ($app) {
    return new ContextoDoLeitor(
        $app['request']->user()?->leitor,
    );
});
```

O `scoped` é descartado no fim de cada requisição e de cada job.

**Nos workers de fila:** o worker é um processo que vive horas e executa
milhares de jobs. Um singleton com o leitor do primeiro job faria o
lembrete de devolução do segundo job ser enviado com o nome — ou para o
telefone — do primeiro leitor. O defeito na tela é constrangedor; na fila,
é uma mensagem para a pessoa errada, com dado de outra.
:::
