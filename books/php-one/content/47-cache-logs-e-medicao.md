---
title: "Cache, logs e o que se mede"
number: 47
slug: cache-logs-e-medicao
part: p10
kicker: "A página do acervo ficou rápida e passou a mostrar como disponível um livro que estava emprestado. Por seis horas, que era o tempo de validade do cache."
goal: >-
  Tornar a aplicação observável e rápida, nessa ordem: medir antes de
  otimizar, cachear com uma estratégia de invalidação escrita, e registrar
  logs estruturados que dá para procurar — sem nunca gravar o que não pode
  ser gravado.
---

:::story Seis horas
A reclamação veio pela Vera, que a ouviu no balcão.

— A menina diz que o aplicativo mostrou *A Hora da Estrela* disponível.
Ela atravessou o bairro pra pegar. Está emprestado desde ontem de manhã.

Dedé abriu o aplicativo. Lá estava: *A Hora da Estrela*, "1 disponível",
em verde.

Abriu o painel da Vera, que consultava o banco direto. Zero disponíveis.
Emprestado às 9h14 do dia anterior.

— Cache — disse ele.

— O quê? — perguntou Vera.

— Na semana passada a listagem do acervo estava lenta. O Cléber pôs um
cache. A lista fica guardada e só é refeita de tempos em tempos.

— De quanto em quanto tempo?

Dedé procurou.

```php
Cache::remember('acervo', 60 * 60 * 6, fn () => /* ... */);
```

— Seis horas.

— Então por seis horas o aplicativo mente.

— Até seis horas.

— E quem decidiu seis horas?

Dedé procurou na tarefa, no commit, na conversa do grupo. Não havia nada.

— Acho que ninguém — disse ele. — Acho que é um número que parecia
razoável.

— Pra quem atravessou o bairro não pareceu — disse Vera.
:::

## Uma fila existe porque esperar custa caro; um cache também

O capítulo anterior tirou da requisição o trabalho que não precisava
acontecer antes da resposta. O cache ataca o mesmo custo por outro lado:
**não refazer** o trabalho que já foi feito e cujo resultado não mudou.

A listagem dos mais emprestados do mês agrupa quinhentos mil empréstimos,
junta com exemplares e livros, e ordena. Leva oitocentos milissegundos. O
resultado muda algumas dezenas de vezes por dia, e é consultado alguns
milhares. Calcular a cada consulta é pagar oitocentos milissegundos
milhares de vezes para obter, quase sempre, a mesma resposta.

O cache guarda a resposta e a devolve até que ela precise ser recalculada.
E toda a dificuldade está nesse "até que".

:::key
Cachear é fácil. O difícil é responder: **quando esse valor deixa de ser
verdade, e quem avisa o cache?**

Um cache sem resposta para essa pergunta é um lugar onde a aplicação
guarda mentiras com prazo de validade.
:::

## Medir antes de otimizar

A história tem um detalhe que não está nela: ninguém mediu por que a
listagem do acervo estava lenta antes de pôr o cache. O cache resolveu a
lentidão e criou a mentira. Com uma medição, talvez a resposta tivesse sido
outra.

O Laravel dá três formas de medir, em ordem crescente de esforço.

**Contar consultas**, com o `DB::listen` do capítulo @cap:relacionamentos:

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    if ($this->app->isLocal()) {
        DB::listen(function (QueryExecuted $q) {
            if ($q->time > 100) {
                Log::channel('lentas')->warning('consulta lenta', [
                    'sql' => $q->sql,
                    'ms' => $q->time,
                ]);
            }
        });
    }
}
```

**O *slow query log* do MySQL**, que registra toda consulta acima de um
tempo, em produção, sem tocar no código:

```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 0.5;
```

**Ferramentas de inspeção em desenvolvimento.** O Telescope, do próprio
Laravel, grava cada requisição com as consultas, os jobs, os logs e as
exceções que ela produziu, e mostra num painel. O Debugbar põe o mesmo
resumo numa barra no rodapé de cada página do painel Blade. Os dois são
para desenvolvimento, e ficam em `require-dev` pelo motivo do capítulo
@cap:do-include-ao-composer.

A Tainá ligou o Telescope e abriu a listagem do acervo. A requisição levava
1,9 segundo e fazia quatro consultas. Três levavam dois milissegundos cada.
A quarta levava 1,8 segundo:

```sql
SELECT COUNT(*) FROM exemplares
WHERE livro_id = livros.id AND estado = 'bom'
```

A contagem de exemplares disponíveis, sem índice composto. O `EXPLAIN` do
capítulo @cap:duas-tabelas-conversando mostrou que o banco lia todos os
oito mil exemplares para cada livro da página.

```php
$t->index(['livro_id', 'estado']);
```

Uma migration de uma linha. A listagem caiu para quarenta milissegundos,
**sem cache**, e sem mentir.

:::pitfall
O cache esconde a lentidão, e esconder não é resolver. A consulta de 1,8
segundo continua lá, rodando a cada seis horas — e rodando na primeira
requisição depois que o cache expira, que é quem paga a conta inteira. Se
dez pessoas chegarem nesse segundo, as dez pagam: dez consultas de 1,8
segundo ao mesmo tempo.

Otimizar pela medição é mudar a causa. Cachear sem medir é pôr um tapete
em cima.
:::

## `Cache::remember` e a pergunta difícil

Há lugares em que o cache é a resposta certa, e os mais emprestados do mês
é um deles: a consulta é cara por natureza — agregar meio milhão de linhas
— e o resultado pode estar alguns minutos atrasado sem que ninguém atravesse
o bairro por isso.

```php title="app/Acervo/MaisEmprestados.php" numbered
final class MaisEmprestados
{
    public function doMes(CarbonImmutable $mes): Collection
    {
        return Cache::remember(
            $this->chave($mes),
            now()->addDay(),
            fn () => $this->calcular($mes),
        );
    }

    public function esquecer(CarbonImmutable $mes): void
    {
        Cache::forget($this->chave($mes));
    }

    private function chave(CarbonImmutable $mes): string
    {
        return 'mais-emprestados:' . $mes->format('Y-m');
    }

    private function calcular(CarbonImmutable $mes): Collection
    {
        return Livro::query()
            ->withCount(['emprestimos' => fn ($q) => $q
                ->whereBetween('retirado_em', [
                    $mes->startOfMonth(),
                    $mes->endOfMonth(),
                ])])
            ->orderByDesc('emprestimos_count')
            ->orderBy('id')
            ->limit(10)
            ->get();
    }
}
```

O `remember` procura a chave. Se achar, devolve. Se não achar, executa a
função, guarda o resultado com a validade informada e devolve. É o padrão
mais usado de cache, e o nome em inglês descreve bem: lembre-se disto.

Repare que a chave inclui o mês. O ranking de fevereiro e o de março são
entradas diferentes, e o de fevereiro, depois que fevereiro acaba, nunca
mais muda.

### Invalidação por tempo e por evento

Existem duas formas de um valor em cache deixar de valer.

**Por tempo.** A validade expira, e a próxima consulta recalcula. É
simples e é **cega**: não sabe se o valor mudou. Seis horas de validade
significa até seis horas de mentira, mesmo que o valor tenha mudado um
segundo depois de guardado.

**Por evento.** Quando algo que afeta o valor acontece, alguém apaga a
entrada. O próximo acesso recalcula com o dado novo.

```php title="app/Listeners/EsquecerMaisEmprestados.php" numbered
final class EsquecerMaisEmprestados
{
    public function __construct(
        private readonly MaisEmprestados $ranking,
    ) {}

    public function handle(EmprestimoRealizado $evento): void
    {
        $this->ranking->esquecer(
            CarbonImmutable::parse(
                $evento->emprestimo->retirado_em,
            ),
        );
    }
}
```

O evento do capítulo @cap:events-jobs-e-filas ganhou um segundo ouvinte, e
o ranking passa a estar sempre certo: o cache vale **até o próximo
empréstimo**, e nunca além.

E a validade de um dia continua lá, como rede de segurança: se algum
caminho alterar empréstimos sem disparar o evento — uma correção manual no
banco, um script de importação —, o erro dura no máximo um dia. Evento
como regra, tempo como seguro.

| Estratégia | O valor pode estar errado por | Custo |
|---|---|---|
| só tempo | até a validade inteira | nenhum código extra |
| só evento | para sempre, se um caminho esquecer | um listener por causa |
| evento + tempo | até a validade, só no caminho esquecido | os dois |

Tabela: A terceira linha é a que a Casa Amarela usa. O número da validade
passa a ser uma decisão sobre o pior caso, não sobre o caso comum.

:::pitfall
A disponibilidade de um exemplar **não** deve ser cacheada, e não por
falta de técnica. Ela muda a cada empréstimo e devolução, dezenas de vezes
por hora, e o custo de estar errada é uma pessoa atravessando o bairro.

A pergunta que decide o que cachear tem duas partes: **quanto custa
calcular** e **quanto custa estar errado**. Os mais emprestados custam caro
para calcular e quase nada para estar errados por alguns minutos. A
disponibilidade custa pouco para calcular — com o índice certo — e muito
para estar errada.
:::

## Cache de configuração, rota e view

Existe um segundo tipo de cache no Laravel, e ele não guarda dado: guarda o
**próprio framework já montado**.

```text
$ php artisan config:cache
$ php artisan route:cache
$ php artisan view:cache
```

O primeiro junta todos os arquivos de `config/` num só, já com os valores
do `.env` resolvidos — o capítulo @cap:configuracao-ambiente-e-artisan
mostrou o que isso faz com `env()` fora de `config/`. O segundo compila a
tabela de rotas. O terceiro converte todos os templates Blade em PHP
antecipadamente.

Juntos, eles economizam dezenas de milissegundos por requisição em
produção, e têm um custo que é o mesmo dos três: **a partir do momento em
que rodam, alterar o arquivo não muda nada**. Uma rota nova, uma
configuração nova, uma view alterada — nada disso entra até alguém rodar o
comando de novo.

É por isso que eles pertencem ao **roteiro de deploy**, logo depois do
código novo chegar, e nunca ao ambiente de desenvolvimento. O capítulo
@cap:git-ci-e-deploy põe cada um no seu lugar.

## Log não é `dd()`

O `dd()` — *dump and die* — imprime o valor e encerra a execução. É a
ferramenta mais usada de depuração em Laravel e a pior coisa que pode ir
para produção: esquecido num caminho raro, ele interrompe a requisição e
mostra ao usuário o conteúdo de uma variável interna.

```php
dd($leitor);
```

A esteira do capítulo @cap:git-ci-e-deploy procura `dd(`, `dump(` e
`var_dump(` no código e recusa o commit. É uma regra de uma linha que evita
uma categoria inteira de incidente.

O log é a ferramenta de produção. Ele grava sem interromper, num lugar que
só a equipe lê, com um nível que diz o quanto aquilo importa.

## Níveis, canais e o log que dá para procurar

Os níveis seguem uma escala que vem dos sistemas Unix e que toda
ferramenta de log entende:

| Nível | Quando | Exemplo na Casa Amarela |
|---|---|---|
| `debug` | detalhe para desenvolvimento | valores intermediários |
| `info` | aconteceu algo normal que vale registrar | empréstimo realizado |
| `warning` | algo estranho que não impediu | provedor lento, retentativa |
| `error` | uma operação falhou | job em `failed_jobs` |
| `critical` | uma parte do sistema está fora | banco inacessível |

Tabela: Em produção, o nível mínimo costuma ser `info`. Tudo que é `debug`
é descartado antes de ser escrito.

E o **canal** diz para onde vai: arquivo diário, saída padrão, um serviço
externo, um canal do Slack para os `critical`. O `config/logging.php`
declara os canais, e um canal `stack` pode mandar a mesma linha para
vários.

A diferença que mais importa, porém, não é o nível nem o canal. É o
formato da linha.

```php
// texto livre
Log::info("Leitor {$leitor->id} levou o exemplar {$tombo}");

// estruturado
Log::info('emprestimo-realizado', [
    'leitor' => $leitor->id,
    'tombo' => $tombo,
    'livro' => $livro->id,
]);
```

A primeira linha é fácil de ler e difícil de procurar. Para achar todos os
empréstimos do exemplar 2117, é preciso uma expressão regular que dependa
da frase exata — que alguém vai mudar.

A segunda tem uma mensagem fixa, que funciona como o `tipo` do capítulo
@cap:erros-padronizados, e os dados em campos separados. Com o log em JSON,
a busca vira uma consulta:

```php title="config/logging.php" numbered
'diario' => [
    'driver' => 'daily',
    'path' => storage_path('logs/laravel.log'),
    'level' => env('LOG_LEVEL', 'info'),
    'formatter' => JsonFormatter::class,
    'days' => 30,
],
```

```text
$ jq 'select(.context.tombo == 2117)' storage/logs/laravel-*.log
```

E cada linha já sai com o incidente do capítulo @cap:middleware, porque o
`Context` acrescenta tudo que tem a toda linha escrita durante a
requisição. Achar a exceção do Wellington é um `grep`; achar **tudo** que
aconteceu na requisição dele, incluindo o que deu certo antes de falhar, é
o mesmo `grep`.

## O que nunca entra no log

O middleware do capítulo @cap:middleware resolveu o log dele. A regra
geral é mais larga, e vale escrever como lista, porque é uma lista que se
confere:

- senha, em qualquer forma — inclusive errada, que costuma ser a certa com
  um caractere trocado;
- token, chave de API, cookie de sessão, cabeçalho `Authorization`;
- documento, CPF, número de cartão;
- o corpo inteiro de requisição ou resposta;
- dado de saúde, de dívida, de qualquer coisa que a pessoa não contaria a
  um desconhecido.

A Casa Amarela registra o **id** do leitor, nunca o nome nem o telefone. Se
alguém precisar saber quem é o leitor 47, consulta o banco — que tem
controle de acesso. O log é lido por mais gente, guardado por mais tempo,
copiado para mais lugares.

:::warning
A exceção é o caminho mais comum pelo qual dado sensível entra no log sem
ninguém escrever `Log::`. Uma `QueryException` traz o SQL **com os
valores**:

```text
SQLSTATE[23000]: Duplicate entry '12345678901' for key
'leitores_documento_unique' (SQL: insert into leitores
(nome, documento, ...) values (Rosângela Pires, 12345678901, ...))
```

O CPF foi para o log pela mensagem da exceção. O handler pode ser
configurado para limpar esses dados antes de registrar, e vale conferir,
de tempos em tempos, com uma busca por padrões — onze dígitos seguidos,
`@` —, o que está de fato sendo gravado.
:::

:::note Na sua carreira
"Medir antes de otimizar" é um conselho que todo mundo repete e pouca gente
segue, porque medir parece atrasar o conserto. A pessoa já tem uma
hipótese, e a hipótese parece certa.

O que acontece com frequência é a hipótese estar certa **pela metade**.
A tela está lenta por causa do banco, sim — mas não pela consulta que
parecia pesada, e sim por um índice que faltava numa que parecia
inofensiva. Dez minutos com o Telescope aberto economizam a tarde de
otimizar a consulta errada, e deixam um número para mostrar na reunião
seguinte, que vale mais que qualquer "agora está mais rápido".
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/Acervo/
    MaisEmprestados.php            # remember + esquecer
  app/Listeners/
    EsquecerMaisEmprestados.php    # invalidação por evento
  app/Providers/
    AppServiceProvider.php         # DB::listen em local
  config/logging.php               # JSON, diário, 30 dias
  database/migrations/
    ..._indice_livro_estado_em_exemplares.php
:::

:::milestone
Fim da Parte 10. O que não precisava esperar saiu da requisição; o que era
caro e podia estar um pouco atrasado ganhou cache com invalidação por
evento; o que era lento por falta de índice ficou rápido sem cache nenhum;
e cada linha de log tem um incidente, campos que dá para procurar e nada
que não possa ser lido.

No caderno da Tainá: *"quem decidiu esse número?"*.
:::

:::summary
- Cachear é fácil; o difícil é dizer quando o valor deixa de ser verdade e
  quem avisa.
- Medir vem antes: `DB::listen`, *slow query log*, Telescope. Muitas vezes a
  resposta é um índice, não um cache.
- Cache esconde lentidão; a primeira requisição depois da expiração paga a
  conta inteira.
- `Cache::remember` com chave que inclui o que diferencia o valor.
- Invalidação por tempo é cega; por evento é precisa e frágil; as duas
  juntas cobrem uma à outra.
- Decide-se o que cachear pelo custo de calcular e pelo custo de estar
  errado.
- `config:cache`, `route:cache` e `view:cache` congelam o framework e
  pertencem ao deploy.
- `dd()` não vai para produção; log estruturado tem mensagem fixa e dados
  em campos.
- Senha, token, documento e corpo de requisição nunca entram no log — nem
  pela mensagem de uma exceção.
:::

:::checkpoint
Você mede uma tela lenta antes de mexer nela, põe cache só onde o custo de
estar errado é pequeno e com invalidação por evento, mantém a
disponibilidade sempre fresca, e escreve logs estruturados que um `grep`
pelo incidente encontra — sem um único dado pessoal dentro.
:::

:::exercise level=1
Para cada valor, diga se vale cachear e, se sim, com que estratégia de
invalidação:

1. A lista de assuntos do acervo, que muda duas vezes por ano.
2. Quantos exemplares de um livro estão disponíveis agora.
3. O total de empréstimos de 2025, para o relatório anual.
4. O perfil do leitor autenticado, consultado em toda tela.

:::answer
1. Sim, por evento (ao salvar um assunto) e por tempo longo como seguro. É
   o caso ideal: muda raramente, é lido o tempo todo.
2. Não. Muda o tempo todo e custa caro estar errado. Com o índice certo, é
   uma consulta de milissegundos.
3. Sim, **sem invalidação**: 2025 acabou. O valor nunca mais muda — exceto
   por correção manual, e aí quem corrige esquece a chave à mão.
4. Provavelmente não. É uma consulta por chave primária, que o banco
   responde em menos de um milissegundo; o cache economizaria quase nada e
   criaria o risco de mostrar um telefone antigo depois de o leitor
   alterá-lo.

O item 4 é o mais comum em código real, e o motivo é que parece óbvio: "é
consultado toda hora". A frequência não basta. O que decide é o custo de
cada consulta.
:::

:::exercise level=2
Reescreva este trecho como log estruturado, e aponte o que ele grava que
não deveria:

```php
Log::info("Login de {$request->email} com senha "
    . "{$request->senha} às " . now()
    . " — resultado: " . ($ok ? 'ok' : 'falhou'));
```

:::answer
Grava a **senha**. Em texto. Inclusive as erradas, que costumam ser a certa
com um erro de digitação, e às vezes a senha de outro serviço que a pessoa
digitou por engano.

Grava também o e-mail, que é dado pessoal — aceitável em alguns logs de
segurança, desde que com prazo curto e acesso restrito. E grava `now()`, o
que é redundante: toda linha de log já tem data.

```php
Log::info('login', [
    'resultado' => $ok ? 'ok' : 'falhou',
    'usuario' => $usuario?->id,
    'ip' => $request->ip(),
]);
```

O id do usuário, quando existe, identifica sem expor. Para tentativas com
e-mail inexistente, `usuario` fica nulo, e o `ip` basta para investigar
ataque.

Se a equipe de segurança realmente precisar do e-mail tentado — para
detectar alguém testando uma lista —, ele vai num **canal separado**, com
retenção de poucos dias e acesso restrito, e nunca junto com a senha.
:::

:::exercise level=3
O painel da Vera tem uma tela "resumo do dia": empréstimos de hoje,
devoluções de hoje, atrasados, reservas pendentes. Ela leva 2,4 segundos.
Alguém propôs cachear por cinco minutos.

Descreva, em ordem, o que você faria antes de aceitar ou recusar a
proposta, e em que caso você aceitaria.

:::answer
**Primeiro, medir.** Abrir a tela com o Telescope — ou o `DB::listen` —
e ver quantas consultas e quanto tempo cada uma leva. A tela tem quatro
números; se forem quatro consultas e uma delas levar 2,3 segundos, o
problema é essa uma.

**Segundo, olhar a consulta lenta.** Rodar o `EXPLAIN`. Os suspeitos de
sempre: índice que falta — `retirado_em` sem índice para "empréstimos de
hoje" é um candidato forte —, função aplicada à coluna no `WHERE`
(`DATE(retirado_em) = ...` impede o uso de índice; `retirado_em BETWEEN
início AND fim` não impede), ou N+1 escondido.

**Terceiro, corrigir a causa e medir de novo.** Se a tela cair para cem
milissegundos, a proposta de cache perde o motivo.

**Quando eu aceitaria o cache.** Se, depois de tudo, sobrar uma consulta
cara por natureza — o número de atrasados agrega a tabela inteira de
empréstimos em aberto e não tem índice que a salve. Aí, cache **só nesse
número**, não na tela inteira, e com a pergunta respondida para a Vera:
"o número de atrasados pode estar até cinco minutos atrasado; os
empréstimos e devoluções de hoje são sempre exatos". Se ela disser que
cinco minutos de atraso no número de atrasados atrapalham o trabalho dela,
a resposta é outra: um contador mantido pelos eventos de empréstimo e
devolução.

A ordem importa porque o cache na tela inteira resolveria o sintoma, e a
Vera veria o empréstimo que acabou de fazer sumir do resumo por até cinco
minutos — o defeito da *Hora da Estrela*, no painel dela.
:::
