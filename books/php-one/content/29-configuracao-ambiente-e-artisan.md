---
title: "Configuração, ambiente e Artisan"
number: 29
slug: configuracao-ambiente-e-artisan
part: p6
kicker: "A multa passou a sair zerada em produção, e em nenhuma outra máquina. A causa foi um comando de otimização rodado no deploy."
goal: >-
  Configurar o projeto sem espalhar `env()` pelo código, entender por que o
  cache de configuração derruba quem faz isso, e usar o Artisan como
  modelo mental em vez de lista de comandos decorada.
---

:::story Oitenta centavos vezes zero
A tela de devolução passou a imprimir multa de R$ 0,00 para todo mundo. Só
em produção. Na máquina do Dedé, na da Tainá e no ambiente de homologação,
o valor saía certo.

— O que mudou no deploy de sexta?

Tainá abriu o passo a passo da publicação. Tinha uma linha nova, acrescentada
na semana anterior por recomendação de um artigo sobre desempenho.

```text
php artisan config:cache
```

— Isso é otimização. Não muda comportamento.

— Muda o comportamento de quem lê o `.env` no lugar errado.

Dedé procurou no código. Estava na calculadora de multas, linha 14:

```php
$centavos = env('MULTA_CENTAVOS', 0);
```

— O padrão é zero.

— O padrão é zero.
:::

## `config()` e `env()`: a diferença que derruba produção

O Laravel tem dois jeitos de ler configuração, e eles parecem sinônimos até
o dia em que não são.

**`env('CHAVE')`** lê direto do arquivo `.env`.

**`config('arquivo.chave')`** lê de um arquivo PHP dentro de `config/`, que
foi carregado quando a aplicação subiu.

A regra que o framework inteiro assume é curta:

:::key
**`env()` só dentro de `config/`. `config()` em todo o resto.**

Não é preferência de estilo. É o que faz a aplicação continuar funcionando
depois do `config:cache`, que é o comando que quase todo deploy roda.
:::

O motivo está no que o `config:cache` faz: ele lê todos os arquivos de
`config/`, resolve tudo — incluindo as chamadas a `env()` que estiverem lá
dentro — e grava o resultado num arquivo só. A partir daí, a aplicação nem
abre o `.env`.

E `env()` chamado fora de `config/` passa a devolver `null`.

```php
// dentro de config/biblioteca.php — certo
'multa_diaria_em_centavos' => (int) env('MULTA_CENTAVOS', 80),

// dentro de um service — devolve null depois do config:cache
$centavos = env('MULTA_CENTAVOS', 0);
```

No caso da Casa Amarela, `null` virou o valor padrão `0`, e o padrão zero
não deu erro: deu multa zerada, que é pior, porque erro alguém vê.

:::pitfall
O detalhe que faz esse defeito atravessar a revisão é que ele **funciona na
sua máquina**. Em desenvolvimento ninguém roda `config:cache`, o `.env` está
lá, e `env()` responde direito.

Ele só aparece onde você não está olhando. É por isso que a regra é regra e
não recomendação: não existe um caso em que `env()` fora de `config/` seja a
escolha certa.
:::

## O arquivo de configuração do projeto

As regras da Casa Amarela estavam espalhadas em constantes e números soltos.
Agora elas têm endereço:

```php title="config/biblioteca.php" numbered
<?php

declare(strict_types=1);

return [
    'prazo_em_dias' => (int) env('BIBLIOTECA_PRAZO_DIAS', 14),

    'prazo_em_dias_infantil' => 7,

    'limite_por_leitor' => (int) env('BIBLIOTECA_LIMITE', 3),

    'limite_em_janeiro' => 5,

    'multa_diaria_em_centavos' => (int) env('MULTA_CENTAVOS', 80),
];
```

```php
$prazo = config('biblioteca.prazo_em_dias');
$multa = config('biblioteca.multa_diaria_em_centavos');
```

O nome do arquivo vira o primeiro pedaço da chave, e o ponto desce pelo
array. Qualquer arquivo novo em `config/` é encontrado sozinho, sem
registrar nada.

Repare em quais valores passaram pelo `env()` e quais não. **Vai para o
`.env` o que muda de ambiente**; fica fixo no arquivo o que é regra do
negócio. O prazo de infantil é sete dias em qualquer servidor do mundo, e
transformá-lo em variável de ambiente só cria um lugar a mais para a regra
divergir.

:::pitfall
O segundo argumento de `env()` é o valor padrão, e ele é uma decisão de
segurança quando a chave for um segredo.

```php
// perigoso
'chave_api' => env('PARCEIRO_API_KEY', 'teste'),
'exigir_https' => env('EXIGIR_HTTPS', false),
```

Um padrão permissivo transforma "esqueci de configurar" em "subiu inseguro e
ninguém percebeu". Para segredo e para interruptor de segurança, o padrão
certo é `null` ou o valor mais restritivo — e a aplicação falhando alto na
inicialização é o comportamento desejado.
:::

## Ambientes

`APP_ENV` diz em qual ambiente a aplicação está rodando, e três nomes são
convenção:

| `APP_ENV` | Onde | O que costuma mudar |
|---|---|---|
| `local` | sua máquina | erro na tela, log verboso, e-mail não sai |
| `testing` | durante os testes | banco separado, nada externo é chamado |
| `production` | servidor | erro só no log, cache ligado, tudo otimizado |

Tabela: O valor é lido pelo framework, que ajusta comportamento sozinho — e
pode ser lido pelo seu código com `app()->environment('production')`.

Para ver o que a aplicação acha que é a realidade dela:

```text
$ php artisan about
```

```text
  Environment .................................................
  Application Name ............................... Casa Amarela
  Laravel Version ...................................... 12.0.0
  PHP Version ........................................... 8.3.14
  Environment ........................................ production
  Debug Mode ......................................... OFF
  Maintenance Mode ................................... OFF

  Cache .......................................................
  Config ............................................... CACHED
  Routes ............................................. NOT CACHED
```

Duas linhas dessa saída teriam encerrado a sexta-feira da história em trinta
segundos: **Config: CACHED**.

## Artisan: três ferramentas com um nome só

O `artisan` é um arquivo na raiz do projeto, e o que ele oferece se organiza
em três famílias.

**É um gerador.** `make:controller`, `make:model`, `make:migration`,
`make:command`. Ele escreve o arquivo no lugar certo, com o nome certo e o
esqueleto certo — poupando menos digitação do que parece e mais dúvida do
que parece.

**É um inspetor.** `about`, `route:list`, `config:show`, `db:show`. Estes
respondem perguntas sobre o estado do projeto, e são os que você vai usar em
servidor alheio às duas da tarde.

**É um controle remoto.** `migrate`, `queue:work`, `schedule:run`,
`cache:clear`, e os comandos que você mesmo escrever. Estes **fazem**
alguma coisa.

```text
$ php artisan route:list
```

```text
  GET|HEAD   /                    ......................
  GET|HEAD   saude                ......................
  GET|HEAD   up                   ......................
```

:::key
`route:list` é a única documentação de API que nunca mente, porque ela não é
escrita: é lida do código que está rodando.

Ao entrar num projeto Laravel desconhecido, é o primeiro comando a rodar.
Em dez segundos você tem o índice da aplicação inteira.
:::

## `tinker`: o console que conhece o projeto

```text
$ php artisan tinker
```

```text
Psy Shell v0.12.4 (PHP 8.3.14 — cli)

> config('biblioteca.multa_diaria_em_centavos')
= 80

> now()->addDays(config('biblioteca.prazo_em_dias'))->toDateString()
= "2026-01-27"

> app()->environment()
= "local"
```

É um console PHP com a aplicação **inteira carregada**: configuração, banco,
suas classes, tudo resolvido pelo contêiner. Serve para conferir uma regra,
olhar um dado e testar uma expressão sem criar arquivo.

:::pitfall
`tinker` em produção é uma ferramenta legítima e perigosa pelo mesmo motivo:
ele executa qualquer coisa, com as credenciais da aplicação, sem deixar
registro do que foi feito.

Consultar é razoável. Alterar dado por ali é uma alteração sem revisão, sem
histórico e sem forma de repetir — e no dia seguinte ninguém sabe explicar
por que aquele empréstimo está com data diferente.

Quando precisar corrigir dado em produção, escreva um comando. Ele tem
nome, tem código revisado e deixa rastro.
:::

## Um comando próprio

Todo dia de madrugada, a Casa Amarela precisa recalcular as multas dos
empréstimos vencidos.

```text
$ php artisan make:command FecharMultasDoDia
```

```php title="app/Console/Commands/FecharMultasDoDia.php" numbered
<?php

declare(strict_types=1);

namespace App\Console\Commands;

use App\Services\CalculadoraDeMultas;
use Illuminate\Console\Command;

class FecharMultasDoDia extends Command
{
    protected $signature = 'biblioteca:multas {--data=}';

    protected $description = 'Calcula as multas dos vencidos';

    public function handle(CalculadoraDeMultas $calculadora): int
    {
        $data = $this->option('data') ?? now()->toDateString();

        $resultado = $calculadora->fecharDia($data);

        $this->info("Dia {$data}: {$resultado->quantidade} multas");
        $this->info("Total: {$resultado->total->formatado()}");

        return self::SUCCESS;
    }
}
```

Três coisas para reparar.

**O `handle()` recebe a calculadora como parâmetro.** Ninguém passou nada:
o contêiner leu o tipo e resolveu, exatamente como o contêiner ingênuo do
capítulo @cap:um-framework-de-quarenta-linhas.

**O comando não calcula nada.** Ele lê a opção, chama o serviço e imprime o
resultado. Toda a regra mora numa classe que não sabe que existe terminal —
e por isso a mesma regra atende a tela, a API e o comando.

**Ele devolve um código.** `self::SUCCESS` é zero; `self::FAILURE` é um. É o
que o agendador do sistema operacional lê para saber se a tarefa da
madrugada deu certo.

```text
$ php artisan biblioteca:multas --data=2026-01-12
```

```text
Dia 2026-01-12: 7 multas
Total: R$ 12,80
```

Para rodar sozinho, o agendamento fica em `routes/console.php`:

```php title="routes/console.php" numbered
use Illuminate\Support\Facades\Schedule;

Schedule::command('biblioteca:multas')
    ->dailyAt('03:00')
    ->withoutOverlapping();
```

O `withoutOverlapping()` impede que uma execução comece enquanto a anterior
ainda estiver rodando — o que acontece no dia em que o banco está lento e a
tarefa de três da manhã ainda não terminou às três e um.

:::note Na sua carreira
"Funciona na minha máquina" tem uma versão moderna e mais difícil de
enxergar: funciona em todo lugar **menos** em produção, porque produção é o
único ambiente que roda os comandos de otimização.

A lista é curta e vale ter na cabeça: `config:cache` quebra quem usa `env()`
fora de `config/`; `route:cache` quebra rota que usa função anônima;
`view:cache` esconde alteração de template.

Quando um defeito só aparece em produção e não tem cheiro de dado, comece
pelo `php artisan about` e veja o que está em cache. Você vai parecer
adivinho umas três vezes por ano.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  config/
    biblioteca.php    # prazo, limite e multa
  app/
    Console/Commands/
      FecharMultasDoDia.php
    Services/
      CalculadoraDeMultas.php
  routes/
    console.php       # agendamento às 3h
    web.php
:::

:::summary
- `env()` só dentro de `config/`; `config()` no resto do código.
- `config:cache` resolve os arquivos de `config/` num só e faz a aplicação
  parar de ler o `.env` — `env()` fora dali passa a devolver `null`.
- O nome do arquivo em `config/` vira o primeiro pedaço da chave, e ele é
  encontrado sozinho.
- Vai para o `.env` o que muda de ambiente; regra de negócio fica fixa no
  arquivo de configuração.
- Padrão permissivo em segredo transforma esquecimento em falha silenciosa.
- `APP_ENV` distingue `local`, `testing` e `production`, e o framework ajusta
  comportamento sozinho.
- Artisan é gerador, inspetor e controle remoto; `about` e `route:list` são
  as duas primeiras coisas a rodar num projeto desconhecido.
- Comando próprio lê opções, chama o serviço e devolve código de saída — não
  contém regra.
:::

:::checkpoint
Você cria um arquivo de configuração e o lê com `config()`, explica por que
`env()` fora de `config/` quebra depois do deploy, inspeciona um projeto
desconhecido com `about` e `route:list`, e escreve um comando que delega o
trabalho a um serviço e devolve código de saída.
:::

:::exercise level=1
Classifique cada valor: vai para o `.env`, fica fixo em `config/`, ou não
deveria estar em configuração nenhuma?

1. A senha do banco.
2. O prazo de empréstimo, catorze dias.
3. O limite de três livros por leitor.
4. O endereço do servidor de e-mail.
5. O texto da mensagem de multa que aparece na tela.

:::answer
1. **`.env`.** Muda por ambiente e é segredo. Nunca com valor padrão.
2. **Fixo em `config/`.** É regra do negócio e é igual em todo lugar. Ter no
   `.env` só criaria a chance de homologação e produção discordarem sobre
   uma regra da Vera.
3. **Fixo em `config/`**, pelo mesmo motivo — com uma ressalva: se a
   associação um dia quiser mudar esse número sem publicar código, ele para
   de ser configuração e vira **dado**, guardado no banco e editável numa
   tela.
4. **`.env`.** Muda por ambiente, e em desenvolvimento costuma apontar para
   um servidor falso.
5. **Nenhuma das duas.** Texto de interface mora nos arquivos de tradução ou
   na view. Configuração é para valor que decide comportamento, não para
   frase que aparece na tela.

O critério dos cinco cabe numa pergunta: *duas máquinas diferentes precisam
de valores diferentes?* Se sim, `.env`. Se não, `config/`. Se a resposta for
"o cliente vai querer mudar isso sozinho", nenhum dos dois.
:::

:::exercise level=2
Escreva o comando `biblioteca:atrasados`, que lista os empréstimos vencidos
e ainda não devolvidos, com uma opção `--leitor=` para filtrar por leitor.

Use `$this->table()` para imprimir o resultado e devolva `FAILURE` quando
houver algum atrasado, para que o agendador registre o dia como anormal.

:::answer
```php title="app/Console/Commands/ListarAtrasados.php" numbered
<?php

declare(strict_types=1);

namespace App\Console\Commands;

use App\Services\ConsultaDeAtrasos;
use Illuminate\Console\Command;

class ListarAtrasados extends Command
{
    protected $signature = 'biblioteca:atrasados {--leitor=}';

    protected $description = 'Lista os vencidos em aberto';

    public function handle(ConsultaDeAtrasos $consulta): int
    {
        $leitor = $this->option('leitor');

        $linhas = $consulta->emAberto(
            $leitor === null ? null : (int) $leitor,
        );

        if ($linhas === []) {
            $this->info('Nenhum atrasado.');

            return self::SUCCESS;
        }

        $this->table(
            ['Tombo', 'Título', 'Leitor', 'Dias'],
            $linhas,
        );

        return self::FAILURE;
    }
}
```

Duas decisões merecem defesa.

**O `(int)` na opção.** Toda opção de linha de comando chega como texto,
como tudo que vem de fora. A conversão acontece na fronteira, e o serviço
recebe o tipo certo.

**O `FAILURE` com lista não vazia** é o pedido do enunciado e merece uma
ressalva honesta: código de saída diferente de zero costuma significar "o
comando falhou", não "o comando encontrou coisas". Se esse comando for
agendado junto com outros, um agendador que para na primeira falha vai parar
aqui.

A saída mais usada em produção é devolver `SUCCESS` sempre e emitir um
alerta separado quando o número passar de um limite — porque atraso é um
fato do negócio, não um defeito do programa.
:::

:::exercise level=3
Um projeto tem, espalhados pelo código, trinta e uma chamadas a `env()` fora
de `config/`. Ele nunca rodou `config:cache`, e a equipe quer começar a
rodar para ganhar desempenho no deploy.

Escreva o plano de migração em quatro passos, incluindo como descobrir as
chamadas e como garantir que nenhuma nova apareça.

:::answer
**Passo 1 — encontrar.** Uma busca resolve, e o resultado é a lista de
trabalho:

```text
$ grep -rn "env(" app/ routes/ database/ | grep -v "config/"
```

**Passo 2 — mover, não traduzir.** Para cada chamada, criar a chave
correspondente em `config/`, apontando para o mesmo `env()` com o mesmo
padrão, e trocar a chamada no código por `config()`. É importante que o
padrão seja **o mesmo** neste passo: mudar comportamento e mudar mecanismo
ao mesmo tempo é o jeito de não saber qual dos dois quebrou.

**Passo 3 — revisar os padrões, agora sozinhos.** Com tudo em `config/`, dá
para ler as trinta e uma linhas juntas e perguntar de cada uma se o padrão
faz sentido. É aqui que aparece o `env('MULTA_CENTAVOS', 0)` — e é aqui que
ele deve ser corrigido, não no passo anterior.

**Passo 4 — impedir a volta.** Sem isso, a chamada número trinta e dois
entra em duas semanas. Duas formas, e a segunda é a que segura:

A barata é uma linha na revisão de código. A confiável é uma regra
automática no passo de verificação, que recusa a alteração se encontrar
`env(` fora de `config/`. A mesma busca do passo 1, com código de saída.

E um quinto passo que não é migração: rodar `config:cache` **também** no
ambiente de homologação. Enquanto produção for o único lugar onde o comando
roda, produção continua sendo o lugar onde esse tipo de defeito é
descoberto.
:::
