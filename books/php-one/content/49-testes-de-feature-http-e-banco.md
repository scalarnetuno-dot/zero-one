---
title: "Testes de feature, HTTP e banco"
number: 49
slug: testes-de-feature-http-e-banco
part: p11
kicker: "A esteira ficou vermelha por três dias num teste que passava em toda máquina local. Faltava um ORDER BY — no teste e no código."
goal: >-
  Verificar o contrato da API de ponta a ponta e as garantias que só o banco
  dá: requisições reais contra rotas reais, banco isolado a cada teste,
  permissões provadas pelo lado da recusa, e fakes de infraestrutura que não
  escondem o que deveriam testar.
---

:::story Três dias vermelha
A esteira ficou vermelha numa segunda-feira à tarde, num teste que ninguém
tinha tocado.

```text
FAILED  Tests\Feature\EmprestimoListagemTest
  > lista os empréstimos do leitor
  Failed asserting that '2117' is identical to '2118'.
```

Tainá rodou na máquina dela: verde. Dedé rodou: verde. Cléber rodou três
vezes seguidas: verde, verde, verde.

— É a esteira — disse Cléber. — Deve ser cache.

Limparam o cache da esteira. Vermelho. Rodaram de novo sem mudar nada.
Verde. De novo. Vermelho.

Na terça, alguém sugeriu marcar o teste como "instável" e seguir em frente.
Tainá não deixou, e não soube explicar por quê — só achou que um teste que
às vezes falha estava tentando dizer alguma coisa.

Na quarta, ela leu o teste linha a linha, com o código da listagem aberto
ao lado.

```php
$this->getJson('/api/emprestimos')
    ->assertJsonPath('data.0.exemplar.tombo', 2117);
```

— Por que o primeiro tem que ser o 2117? — perguntou.

— Porque foi o primeiro que o teste criou — disse Dedé.

— E a listagem ordena por quê?

Dedé abriu o controller. Ordenava por `retirado_em`, decrescente. E a
factory criava os três empréstimos do teste no mesmo segundo.

— Três empréstimos com a mesma data — disse Tainá. — Sem desempate.

— Na nossa máquina, o MySQL devolve na ordem de inserção.

— E na esteira?

— Na esteira, o MySQL roda com outra configuração de memória.
:::

## `getJson`, `postJson` e o contrato verificado

O capítulo anterior testou a regra isolada: uma função recebe valores e
decide. Mas a regra isolada não prova que a API funciona. Entre a
requisição do aplicativo e a política de empréstimo existem a rota, o
middleware, o Form Request, a policy, o service, a transação, o resource e
o handler de erro — e qualquer um deles pode estar mal ligado.

O teste de feature faz o caminho inteiro. Ele manda uma requisição de
verdade para a aplicação, sem servidor web no meio, e confere a resposta:

```php title="tests/Feature/LivroTest.php" numbered
test('cria livro e devolve 201 com Location', function () {
    $atendente = Usuario::factory()->atendente()->create();

    $resposta = $this->actingAs($atendente)
        ->postJson('/api/livros', [
            'titulo' => 'Vidas Secas',
            'autor' => 'Graciliano Ramos',
            'assunto' => 'literatura',
            'isbn' => '978-85-01-00032-5',
        ]);

    $resposta->assertCreated()
        ->assertHeader('Location')
        ->assertJsonPath('data.titulo', 'Vidas Secas')
        ->assertJsonPath('data.isbn', '9788501000325');
});
```

O `postJson` monta a requisição com os cabeçalhos de JSON, a entrega ao
kernel do Laravel e devolve a resposta como objeto. As afirmações que
seguem conferem o **contrato**: o status, o cabeçalho, e dois campos do
corpo — um deles, o ISBN, já normalizado pelo `prepareForValidation` do
capítulo @cap:validation-e-form-requests.

As afirmações que mais se usam:

| Afirmação | Confere |
|---|---|
| `assertCreated()`, `assertOk()`, `assertNoContent()` | o status |
| `assertJsonPath('data.titulo', 'x')` | um campo, pelo caminho |
| `assertJsonStructure([...])` | que as chaves existem |
| `assertJsonValidationErrors(['isbn'])` | o `422` e o campo culpado |
| `assertJsonMissingPath('data.x')` | que uma chave **não** está lá |

Tabela: A última é a menos usada e a mais importante das cinco. Ela é
quem garante que o que não pode sair continua não saindo.

## `RefreshDatabase`: isolamento sem `TRUNCATE`

Teste de feature usa banco de verdade. E cada teste precisa começar com o
banco num estado conhecido, ou o resultado de um depende do que o outro
deixou para trás.

```php title="tests/Pest.php" numbered
pest()->extend(Tests\TestCase::class)
    ->use(Illuminate\Foundation\Testing\RefreshDatabase::class)
    ->in('Feature');
```

O `RefreshDatabase` faz duas coisas. Na primeira vez que a suíte roda, ele
executa todas as migrations num banco de teste vazio. Depois, **cada teste
roda dentro de uma transação que é desfeita no fim**. Nada do que o teste
gravou sobrevive a ele.

É rápido — desfazer uma transação custa quase nada — e tem uma
consequência: dentro do teste, tudo acontece numa transação só. O
`DB::transaction` do `EmprestimoService` vira uma transação **aninhada**, e
o Laravel a simula com *savepoints*. Funciona para quase tudo. Não funciona
para testar duas conexões disputando a mesma linha, porque as duas
enxergariam a mesma transação externa.

O banco de teste é **outro banco**, configurado no `phpunit.xml`:

```xml title="phpunit.xml" numbered
<env name="APP_ENV" value="testing"/>
<env name="DB_DATABASE" value="casa_amarela_teste"/>
<env name="QUEUE_CONNECTION" value="sync"/>
<env name="CACHE_STORE" value="array"/>
```

:::warning
O `RefreshDatabase` apaga o banco na primeira execução. Se o `.env` de
teste estiver apontando para o banco de desenvolvimento — ou, como na
quinta-feira do capítulo @cap:migrations-seeders-e-factories, para o de
produção —, ele apaga o banco errado.

O `phpunit.xml` com `DB_DATABASE` explícito é a proteção. E vale uma
conferência a mais no `TestCase`: se o nome do banco não terminar em
`_teste`, o teste se recusa a rodar.
:::

### SQLite em memória, e onde ele mente

Muitos projetos rodam os testes em SQLite em memória, porque é mais rápido
e não precisa de servidor:

```xml
<env name="DB_CONNECTION" value="sqlite"/>
<env name="DB_DATABASE" value=":memory:"/>
```

E o SQLite não é o MySQL. As diferenças que já atravessaram este livro:

- a collation `utf8mb4_0900_ai_ci` do capítulo
  @cap:paginacao-filtros-e-buscas não existe; a busca sem acento passa num
  e falha no outro;
- o SQLite aceita texto numa coluna `INTEGER` sem reclamar;
- `lockForUpdate` é ignorado — não há trava de linha;
- o tamanho de `VARCHAR(200)` não é conferido.

Um teste que passa no SQLite e falha no MySQL de produção é pior que um
teste lento, porque ele dá a certeza errada. A Casa Amarela roda os testes
no **mesmo MySQL** da produção, na mesma versão. A esteira do capítulo
@cap:git-ci-e-deploy sobe um MySQL de serviço para isso, e custa alguns
segundos por execução.

## `actingAs` e o teste de rota protegida

As rotas da API estão atrás do `auth:sanctum`. O teste não precisa fazer
login e guardar um token:

```php
$this->actingAs($usuario)->getJson('/api/eu');
```

O `actingAs` diz ao Laravel que as requisições seguintes vêm desse
usuário. Para testar as habilidades do token, o Sanctum tem a forma
própria:

```php
Sanctum::actingAs($usuario, ['ver-acervo']);
```

E o teste de que a rota **está** protegida é o mais simples de todos, e
precisa existir para cada grupo:

```php title="tests/Feature/ProtecaoTest.php" numbered
test('rotas do leitor exigem autenticação', function (
    string $metodo,
    string $rota,
) {
    $this->json($metodo, $rota)->assertUnauthorized();
})->with([
    ['GET', '/api/eu'],
    ['GET', '/api/emprestimos'],
    ['POST', '/api/emprestimos/1/renovacao'],
    ['POST', '/api/reservas'],
]);
```

Se alguém mover uma rota para fora do grupo protegido, por engano, num
rearranjo do arquivo de rotas, esse teste acusa.

## Testar `403` é testar o que ninguém testa à mão

O capítulo @cap:autorizacao terminou com dois testes do caso Caio. A suíte
completa segue o mesmo molde para cada recurso, e o molde tem três
perguntas:

1. O dono consegue?
2. Outro usuário do mesmo papel **não** consegue?
3. A equipe consegue?

```php title="tests/Feature/EmprestimoAutorizacaoTest.php" numbered
beforeEach(function () {
    $this->dono = Usuario::factory()->leitor()->create();
    $this->outro = Usuario::factory()->leitor()->create();
    $this->atendente = Usuario::factory()->atendente()->create();

    $this->emprestimo = Emprestimo::factory()
        ->for($this->dono->leitor)
        ->create();
});

test('dono vê o próprio empréstimo', function () {
    $this->actingAs($this->dono)
        ->getJson("/api/emprestimos/{$this->emprestimo->id}")
        ->assertOk();
});

test('outro leitor não vê', function () {
    $this->actingAs($this->outro)
        ->getJson("/api/emprestimos/{$this->emprestimo->id}")
        ->assertForbidden();
});

test('atendente vê', function () {
    $this->actingAs($this->atendente)
        ->getJson("/api/emprestimos/{$this->emprestimo->id}")
        ->assertOk();
});
```

O segundo é o que importa. Os outros dois quase sempre passam, porque o
caminho feliz é o que a pessoa testou na tela enquanto desenvolvia. O
segundo só passa se alguém lembrou de escrever a policy.

## O campo que nunca pode aparecer

O capítulo @cap:api-resources prometeu um teste para a
`observacao_interna`. Ele é curto e protege contra uma categoria inteira
de defeito:

```php title="tests/Feature/CamposInternosTest.php" numbered
test('observação interna nunca sai pela API', function (
    string $rota,
) {
    $leitor = Leitor::factory()->create([
        'observacao_interna' => 'SEGREDO-DE-TESTE',
    ]);
    $admin = Usuario::factory()->admin()->create();

    $corpo = $this->actingAs($admin)
        ->getJson(str_replace('{id}', $leitor->id, $rota))
        ->assertOk()
        ->getContent();

    expect($corpo)->not->toContain('SEGREDO-DE-TESTE');
})->with([
    '/api/leitores/{id}',
    '/api/leitores?busca=',
    '/api/leitores/{id}/emprestimos',
]);
```

Três detalhes de desenho.

O teste usa o **admin**, que é quem vê mais. Se nem o admin recebe a
observação pela API, ninguém recebe.

Ele procura o **valor**, não a chave. `assertJsonMissingPath` conferiria
que não há uma chave `observacao_interna`, e deixaria passar o dia em que
alguém a expusesse com outro nome — `notas`, `obs`.

E o valor é uma marca inconfundível. Um texto comum como "devolve molhado"
poderia aparecer por outro motivo; `SEGREDO-DE-TESTE`, não.

## `assertDatabaseHas` e o que ele prova

O fluxo de empréstimo precisa de um teste que confira o banco, porque a
promessa do service é sobre o banco — duas gravações, juntas:

```php title="tests/Feature/EmprestimoFluxoTest.php" numbered
test('empréstimo grava e trava o exemplar juntos', function () {
    $exemplar = Exemplar::factory()->disponivel()->create();
    $leitor = Leitor::factory()->emDia()->create();
    $atendente = Usuario::factory()->atendente()->create();

    $this->actingAs($atendente)
        ->postJson('/api/emprestimos', [
            'exemplar_id' => $exemplar->id,
            'leitor_id' => $leitor->id,
        ])
        ->assertCreated();

    $this->assertDatabaseHas('emprestimos', [
        'exemplar_id' => $exemplar->id,
        'leitor_id' => $leitor->id,
        'devolvido_em' => null,
    ]);

    expect($exemplar->fresh()->estado)
        ->toBe(StatusExemplar::Emprestado);
});
```

O `assertDatabaseHas` procura uma linha com aqueles valores. Ele prova que
a linha **existe**, e não prova que é a única — um defeito que gravasse o
empréstimo duas vezes passaria. Quando isso importa, `assertDatabaseCount`
completa.

E o teste da transação desfeita, que é o outro lado da mesma promessa:

```php
test('exemplar indisponível não grava nada', function () {
    $exemplar = Exemplar::factory()->emprestado()->create();
    $leitor = Leitor::factory()->emDia()->create();

    $this->actingAs(Usuario::factory()->atendente()->create())
        ->postJson('/api/emprestimos', [
            'exemplar_id' => $exemplar->id,
            'leitor_id' => $leitor->id,
        ])
        ->assertConflict()
        ->assertJsonPath('tipo', 'exemplar-indisponivel');

    $this->assertDatabaseCount('emprestimos', 1);
});
```

O `1` é o empréstimo que a factory `emprestado()` já criou. Nenhum novo.

Repare no que este teste **não** faz: conferir as onze condições. Elas
foram provadas na unidade, em catorze centésimos de segundo. Aqui basta um
`409` para provar que a exceção de domínio atravessa o controller e chega
ao handler no formato certo. Repetir as onze aqui custaria dois segundos e
não provaria nada novo.

## Fake de fila, e-mail e evento

O fluxo de empréstimo dispara `EmprestimoRealizado`, que manda um job para
a fila, que chama o enviador. O teste de feature quer provar o primeiro
elo, e não precisa executar os outros:

```php
test('empréstimo anuncia o evento', function () {
    Event::fake([EmprestimoRealizado::class]);

    // ... o POST do empréstimo ...

    Event::assertDispatched(
        EmprestimoRealizado::class,
        fn ($e) => $e->emprestimo->leitor_id === $leitor->id,
    );
});
```

`Event::fake` troca o disparador de eventos por um que só anota. Existem
os irmãos — `Queue::fake`, `Mail::fake`, `Notification::fake`,
`Storage::fake` —, e todos seguem o molde do fake do capítulo @cap:testes:
conferir o que aconteceu, sem executar.

:::pitfall
O `Queue::fake` confere que o job foi **enfileirado**. Ele não executa o
job — e por isso um job que quebraria na primeira linha passa em todos os
testes que usam o fake.

A suíte precisa de pelo menos um teste que **execute** cada job de
verdade, com o enviador falso injetado:

```php
test('aviso de véspera envia uma vez só', function () {
    $falso = new EnviadorFalso();
    $this->app->instance(EnviadorDeAviso::class, $falso);
    $e = Emprestimo::factory()->venceAmanha()->create();

    (new AvisarDevolucaoProxima($e->id))->handle($falso);
    (new AvisarDevolucaoProxima($e->id))->handle($falso);

    expect($falso->enviados)->toHaveCount(1);
});
```

É o teste da Dona Iolanda: o job rodando duas vezes, e uma mensagem só.
:::

## Suíte lenta: diagnosticar antes de culpar o banco

A suíte da Casa Amarela tem trezentos testes e leva quarenta segundos.
Antes de trocar o MySQL pelo SQLite, a pergunta do capítulo
@cap:cache-logs-e-medicao: **onde o tempo está?**

```text
$ php artisan test --profile

  Top 10 slowest tests:
  EmprestimoListagemTest > pagina 500 empréstimos     8.21s
  RelatorioTest > relatório anual completo            6.03s
  ...
```

Dois testes somam catorze dos quarenta segundos. O primeiro cria
quinhentos empréstimos com a factory — cada um criando leitor, exemplar e
livro próprios, duas mil gravações — para testar a paginação de vinte. Com
cinquenta empréstimos do mesmo leitor, a paginação é provada igual.

Depois de consertar os lentos, o que sobra se divide:

```text
$ php artisan test --parallel
```

O `--parallel` roda os testes em vários processos, cada um com o seu banco
de teste. Numa máquina com oito núcleos, os quarenta segundos viram oito.

:::key
Quanto tempo a suíte pode levar? A resposta prática: **o tempo que alguém
aceita esperar antes de cada commit**. Passou disso, as pessoas param de
rodar localmente, e a esteira vira o primeiro lugar em que o teste roda —
que é tarde.

Para um projeto do tamanho da Casa Amarela, menos de um minuto. A unidade
em menos de um segundo, para rodar a cada vez que o arquivo é salvo.
:::

## A correção da esteira vermelha

Voltando à história: o teste esperava o 2117 primeiro porque a pessoa que o
escreveu viu o 2117 primeiro na máquina dela. A listagem ordenava por
`retirado_em`, e os três empréstimos do teste tinham o mesmo valor. Sem
desempate, a ordem entre eles era do banco — e o banco, na esteira, com
outra configuração de memória, às vezes escolhia outra.

O defeito estava **nos dois lugares**. O código precisava do desempate do
capítulo @cap:paginacao-filtros-e-buscas — `orderByDesc('id')` depois da
data —, porque em produção dois empréstimos no mesmo segundo acontecem todo
sábado de manhã. E o teste precisava criar os empréstimos com datas
diferentes, para afirmar a ordem que a regra promete, e não a que o banco
por acaso produz.

O teste instável estava certo. Ele estava dizendo, três dias seguidos, que
a listagem de produção tinha um defeito.

:::note Na sua carreira
Teste instável — que às vezes passa e às vezes falha sem mudança no código
— é quase sempre um defeito real, só que um que depende de ordem, de
tempo ou de concorrência. São as três coisas que o teste manual nunca pega.

A reação comum é marcar o teste como instável, pular, e seguir. A reação
que separa quem investiga de quem só entrega é a da Tainá: desconfiar que o
teste está tentando dizer alguma coisa, e ler linha a linha até descobrir
o quê. Leva uma tarde. O defeito que ele esconde costuma levar uma semana
para ser achado em produção.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  phpunit.xml                      # banco _teste, fila sync
  tests/Pest.php                   # RefreshDatabase em Feature
  tests/Feature/
    ProtecaoTest.php               # 401 para cada rota do grupo
    LivroTest.php                  # CRUD, 201, 422
    EmprestimoFluxoTest.php        # banco, transação, 409
    EmprestimoAutorizacaoTest.php  # dono, outro, equipe
    CamposInternosTest.php         # SEGREDO-DE-TESTE
    AvisosTest.php                 # jobs executados de verdade
:::

:::summary
- Teste de feature faz o caminho inteiro — rota, middleware, Form Request,
  policy, service, resource, handler — sem servidor web.
- `assertJsonMissingPath` e a busca pelo valor garantem o que não pode
  sair.
- `RefreshDatabase` migra uma vez e desfaz cada teste numa transação; o
  banco de teste é outro, declarado no `phpunit.xml`.
- SQLite em memória não tem a collation, a trava nem a conferência de tipo
  do MySQL; teste no banco de produção.
- `actingAs` autentica; o teste de `401` protege o grupo de rotas.
- Permissão se prova pelo lado da recusa: dono, outro do mesmo papel,
  equipe.
- `assertDatabaseHas` prova que existe, não que é único.
- Não repita na feature o que a unidade provou; um caso por caminho basta.
- Fakes conferem o disparo; pelo menos um teste executa cada job de
  verdade.
- `--profile` antes de culpar o banco; `--parallel` depois.
- Teste instável é, quase sempre, um defeito de ordem, tempo ou
  concorrência.
:::

:::checkpoint
A suíte de feature cobre o CRUD, o fluxo de empréstimo com o banco, os
`422`, os `401` de cada grupo, os `403` por papel e por propriedade, e o
campo interno que nunca sai — e roda em menos de um minuto, no mesmo MySQL
da produção, falhando no dia em que o contrato mudar.
:::

:::exercise level=1
Diga se cada afirmação deve ser testada na unidade ou na feature:

1. Multa de R$ 5,01 impede empréstimo.
2. `POST /emprestimos` sem token responde `401`.
3. O `LeitorResource` não expõe o documento para outro leitor.
4. O `RegrasDeCirculacao` dá limite cinco em janeiro.
5. A devolução libera o exemplar na mesma transação.

:::answer
1. Unidade, na `PoliticaDeEmprestimo`. Na feature, no máximo um caso de
   `409` para provar que a exceção chega ao cliente.
2. Feature. É uma afirmação sobre o middleware e o arquivo de rotas.
3. Feature, com dois usuários autenticados. Dá para testar o resource
   isolado, mas a garantia real é que a rota usa aquele resource.
4. Unidade. É pura.
5. Feature, com banco. É uma afirmação sobre a transação.
:::

:::exercise level=2
Escreva o teste de feature da listagem de empréstimos que teria pegado o
defeito da história **de forma determinística** — falhando sempre, e não às
vezes, enquanto o desempate não existir.

:::answer
O truque é criar empréstimos com a **mesma** data, de propósito, em ordem
de id conhecida, e afirmar a ordem que a regra promete:

```php
test('empréstimos com a mesma data seguem o desempate', function () {
    $leitor = Usuario::factory()->leitor()->create();
    $mesmoInstante = '2026-03-07 10:00:00';

    $ids = Emprestimo::factory()
        ->count(5)
        ->for($leitor->leitor)
        ->create(['retirado_em' => $mesmoInstante])
        ->pluck('id')
        ->sortDesc()
        ->values()
        ->all();

    $recebidos = $this->actingAs($leitor)
        ->getJson('/api/emprestimos')
        ->assertOk()
        ->json('data.*.id');

    expect($recebidos)->toBe($ids);
});
```

Sem o `orderByDesc('id')` na listagem, a ordem entre os cinco depende do
banco, e o teste falha na maioria das execuções em vez de uma vez em
dez — cinco empates são muito mais difíceis de acertar por acaso do que
três.

A lição de fundo: o teste da história estava afirmando **o que foi
observado**. Este afirma **o que foi prometido** — a ordem do contrato —
e cria de propósito a situação em que a promessa é posta à prova.
:::

:::exercise level=3
Um projeto novo que você assumiu tem seiscentos testes de feature, nenhum
de unidade, e leva onze minutos. A equipe roda os testes só na esteira, e
um commit leva quinze minutos para ser confirmado. A proposta na mesa é
trocar o MySQL por SQLite em memória.

Escreva o plano, em ordem, com o que você mediria e o que faria em cada
etapa. Diga o que responder à proposta do SQLite.

:::answer
**Sobre o SQLite, primeiro.** Ele provavelmente reduz o tempo pela metade e
troca a velocidade por certeza: collation, trava de linha e tipo deixam de
ser testados. Eu não recusaria de saída — perguntaria se o projeto usa
alguma dessas coisas. Se usa busca sem acento, `lockForUpdate` ou depende
de tipo estrito de coluna, a resposta é não.

**Etapa 1: medir.** `--profile` para achar os mais lentos. Em suítes assim,
é comum que um décimo dos testes leve metade do tempo, quase sempre por
factory criando centenas de registros encadeados sem necessidade.

**Etapa 2: consertar os lentos.** Reduzir volume de dados onde o volume não
é o que está sendo testado; trocar `create()` por `make()` onde o banco não
importa; usar um `seed` compartilhado para dados de referência que todo
teste precisa.

**Etapa 3: paralelizar.** `--parallel` na esteira e nas máquinas. Isso
sozinho costuma dividir o tempo pelo número de núcleos.

**Etapa 4: mover para a unidade o que é regra.** Os testes de feature que
testam vinte variações da mesma regra passando por HTTP viram um teste de
feature — o caminho — e um dataset de unidade — as variações. É a etapa
mais demorada e a que mais reduz tempo, e só faz sentido depois de a
regra estar separada da consulta, como a `PoliticaDeEmprestimo`.

**O que eu mostraria na reunião:** o antes e depois de cada etapa, em
minutos. A proposta do SQLite era uma solução; o `--profile` é o
diagnóstico, e costuma apontar para uma causa mais barata e sem perda.
:::
