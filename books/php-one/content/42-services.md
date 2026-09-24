---
title: "Services: onde a regra de negócio mora"
number: 42
slug: services
part: p9
kicker: "Vera leu o método em voz alta e corrigiu uma regra que a equipe tinha entendido errado havia quatro meses. Levou dezoito segundos."
goal: >-
  Decidir onde cada regra vive, tirar a regra de empréstimo do controller e
  pô-la num service que é uma fronteira de transação e não conhece HTTP, e
  saber quantas camadas o projeto realmente precisa.
---

## Controller com oitocentas linhas começa com vinte

O `EmprestimoController::store` do capítulo @cap:o-crud-completo tinha
duas regras — exemplar disponível e limite por leitor — e cabia numa tela.
Desde então:

- o Form Request tirou a validação de lá;
- o handler do capítulo @cap:erros-padronizados tirou a montagem do erro;
- o enviador do capítulo anterior acrescentou o aviso.

E ainda faltam nove das onze regras da Vera. Se cada uma entrar no
controller, o método chega a cento e cinquenta linhas antes do fim da
parte. O painel Blade, que também empresta, tem uma cópia. O comando
`biblioteca:multas`, que precisa saber se um leitor tem pendência, tem uma
terceira versão de uma das regras.

Nenhum controller nasce com oitocentas linhas. Ele chega lá vinte linhas
por vez, cada uma razoável, e cada uma posta ali porque era o lugar mais
perto de onde a pessoa estava editando.

:::key
O sintoma não é o tamanho. É a **mesma regra em dois lugares**. No momento
em que o painel e a API conferem o limite de empréstimos cada um do seu
jeito, a regra já está errada em um deles — só não se sabe qual.
:::

## A regra que envolve duas entidades não cabe no model

A primeira tentativa de tirar a regra do controller costuma ser o model.
Parece natural: o empréstimo sabe se emprestar.

```php
class Emprestimo extends Model
{
    public static function realizar(
        Exemplar $exemplar,
        Leitor $leitor,
    ): self {
        // ...
    }
}
```

Olhe o que "realizar um empréstimo" precisa consultar:

| Regra | Pergunta a quem |
|---|---|
| exemplar disponível | `Exemplar` |
| não é da referência | `Exemplar` |
| não é o último do título | `Livro`, contando `Exemplar` |
| limite de três | `Emprestimo`, filtrando por `Leitor` |
| nenhum atrasado | `Emprestimo`, filtrando por `Leitor` |
| multa acima de cinco reais | `Multa`, filtrando por `Leitor` |
| leitor ativo | `Leitor` |

Tabela: Sete das onze regras, e elas atravessam cinco entidades. Nenhuma
delas é dona da operação.

O `Emprestimo::realizar` precisaria conhecer todos os outros models, e o
`Emprestimo` passaria a ser o lugar onde mora a regra de circulação inteira
da biblioteca. É o "model gigante" do capítulo @cap:eloquent, e ele chega
lá pelo mesmo caminho do controller: uma regra razoável por vez.

A régua que funciona:

**Regra que fala de uma entidade só fica nela.** "O exemplar está
disponível?" é uma pergunta sobre o exemplar — `$exemplar->disponivel()`.
"O empréstimo está em atraso?" é sobre o empréstimo — `$e->emAtraso()`.

**Regra que coordena várias entidades vai para um service.** "Este leitor
pode levar este exemplar agora?" não pertence a nenhuma das duas.

## O service

```php title="app/Emprestimos/EmprestimoService.php" numbered
<?php

declare(strict_types=1);

namespace App\Emprestimos;

use App\Avisos\EnviadorDeAviso;
use App\Models\Emprestimo;
use App\Models\Exemplar;
use App\Models\Leitor;
use Illuminate\Support\Facades\DB;

final class EmprestimoService
{
    public function __construct(
        private readonly RegrasDeCirculacao $regras,
        private readonly EnviadorDeAviso $avisos,
    ) {}

    public function realizar(
        int $exemplarId,
        int $leitorId,
        ?Autorizacao $autorizacao = null,
    ): Emprestimo {
        $emprestimo = DB::transaction(function () use (
            $exemplarId, $leitorId, $autorizacao,
        ) {
            $exemplar = Exemplar::with('livro')
                ->lockForUpdate()
                ->findOrFail($exemplarId);

            $leitor = Leitor::lockForUpdate()
                ->findOrFail($leitorId);

            $this->exigirExemplarEmprestavel(
                $exemplar, $autorizacao,
            );
            $this->exigirLeitorEmDia($leitor);

            $prazo = $this->regras->prazoPara($leitor);

            $emprestimo = Emprestimo::create([
                'exemplar_id' => $exemplar->id,
                'leitor_id' => $leitor->id,
                'retirado_em' => now(),
                'devolver_ate' => now()->addDays($prazo),
                'autorizado_por' => $autorizacao?->usuarioId,
            ]);

            $exemplar->marcarEmprestado();

            return $emprestimo;
        });

        $this->avisos->enviar(
            $emprestimo->leitor,
            "Empréstimo feito. Devolva até "
                . $emprestimo->devolver_ate->format('d/m') . '.',
        );

        return $emprestimo;
    }

    // ...
}
```

Três coisas para ler com atenção.

**A assinatura recebe números, não `Request`.** O service não sabe se foi
chamado pela API, pelo painel, pelo comando Artisan ou por um teste.

**O método público é a transação.** Tudo que precisa ser verdade junto está
dentro do `DB::transaction`. O aviso está **fora** — e isso é uma decisão:
se o provedor de mensagens cair, o empréstimo não deve ser desfeito. A
leitora está com o livro na mão.

**As conferências têm nome.** `exigirExemplarEmprestavel` e
`exigirLeitorEmDia` são métodos privados que lançam as exceções de domínio
do capítulo @cap:erros-padronizados:

```php title="app/Emprestimos/EmprestimoService.php" numbered
private function exigirLeitorEmDia(Leitor $leitor): void
{
    if (!$leitor->ativo()) {
        throw new LeitorInativo($leitor->id);
    }

    if ($leitor->emprestimos()->emAtraso()->exists()) {
        throw new LeitorComAtraso($leitor->id);
    }

    $multa = $leitor->multaEmAberto();

    if ($multa->maiorQue($this->regras->multaMaxima())) {
        throw new LeitorComPendencia($leitor->id, $multa);
    }

    $abertos = $leitor->emprestimos()->emAberto()->count();
    $limite = $this->regras->limitePara($leitor, now());

    if ($abertos >= $limite) {
        throw new LimiteDeEmprestimosAtingido(
            $leitor->id, $limite, $abertos,
        );
    }
}
```

Cada `if` é uma frase da Vera. Leia de cima para baixo e é o capítulo
@cap:condicionais, com cláusulas de guarda, sem `else` nenhum.

E o `RegrasDeCirculacao` guarda os números — prazo, limite, multa máxima —
que dependem de configuração e de calendário:

```php title="app/Emprestimos/RegrasDeCirculacao.php" numbered
final class RegrasDeCirculacao
{
    public function limitePara(
        Leitor $leitor,
        DateTimeInterface $quando,
    ): int {
        return (int) $quando->format('n') === 1
            ? config('biblioteca.limite_em_janeiro')
            : config('biblioteca.limite_por_leitor');
    }

    public function prazoPara(Leitor $leitor): int
    {
        return $leitor->infantil()
            ? config('biblioteca.prazo_em_dias_infantil')
            : config('biblioteca.prazo_em_dias');
    }

    public function multaMaxima(): Dinheiro
    {
        return Dinheiro::emCentavos(500);
    }
}
```

Ela é pura — recebe o que precisa, não consulta o banco, não guarda
estado. É o que o capítulo @cap:testes vai testar em milissegundos.

:::story Dezoito segundos
Dedé projetou o `EmprestimoService` na parede da sala de reunião. Vera
tinha vindo entregar as fichas de papel do mês e ficou na porta.

— Lê pra mim — disse ela.

— Tudo?

— A parte do exemplar.

Dedé rolou até o `exigirExemplarEmprestavel` e leu, traduzindo o código em
voz alta:

— Se não está disponível, não sai. Se é da referência, não sai. Se é da
coleção do Seu Juvenal, não sai. Se chegou há menos de sete dias, não sai.
Se é o último exemplar do título, não sai.

— Para.

Dedé parou.

— O último não é "não sai". É "sai com autorização". Eu autorizo, ou a
Neide quando eu não estou. Se a pessoa precisa pro trabalho da escola, sai.

Tainá abriu o caderno na página da primeira semana. Estava escrito:
*"último exemplar — só c/ autoriz."*. Ela tinha anotado certo. Alguém, no
caminho entre o caderno e o código, tinha perdido a segunda metade da
frase.

— Desde quando está assim? — perguntou Márcia.

— Desde outubro — disse Dedé. — Quatro meses.

Vera já estava saindo.

— E a Dona Marlene?

— A Dona Marlene é o quê?

— É autorização também. Eu olho pra ela e autorizo.
:::

## A regra corrigida, e a regra que não era regra

A correção da Vera coube em dezoito segundos porque a regra cabia numa
tela e estava escrita na ordem em que ela pensa. Num controller de
oitocentas linhas, com a regra dividida entre três arquivos, ninguém teria
lido para ela — e ela não teria achado.

```php title="app/Emprestimos/EmprestimoService.php" numbered
private function exigirExemplarEmprestavel(
    Exemplar $exemplar,
    ?Autorizacao $autorizacao,
): void {
    if (!$exemplar->disponivel()) {
        throw new ExemplarIndisponivel(
            $exemplar->tombo, $exemplar->estado,
        );
    }

    if ($exemplar->daReferencia() || $exemplar->daColecaoFechada()) {
        throw new ExemplarNaoCircula($exemplar->tombo);
    }

    if ($exemplar->emExposicao(now())) {
        throw new ExemplarEmExposicao(
            $exemplar->tombo, $exemplar->exposicaoAte(),
        );
    }

    if ($exemplar->livro->ultimoDisponivel($exemplar)
        && $autorizacao === null) {
        throw new UltimoExemplarExigeAutorizacao(
            $exemplar->tombo,
        );
    }
}
```

E a segunda frase da Vera resolve um problema que a equipe carregava desde
o capítulo @cap:condicionais: a regra da Dona Marlene. Ela nunca foi uma
regra. Era a Vera **exercendo julgamento** — e julgamento não se programa,
se registra.

O objeto `Autorizacao` é esse registro:

```php title="app/Emprestimos/Autorizacao.php" numbered
final readonly class Autorizacao
{
    public function __construct(
        public int $usuarioId,
        public string $motivo,
    ) {}
}
```

Quem autorizou e por quê. Ele vai gravado no empréstimo (`autorizado_por`),
e o relatório de fim de mês consegue responder "quantos empréstimos saíram
por autorização, e de quem". A exceção da Dona Marlene virou dado, com
nome, e parou de ser uma lenda do balcão.

:::key
Nem toda regra do especialista é uma regra do sistema. Algumas são
**julgamento** — decisões que a pessoa toma olhando o caso. Tentar
programá-las produz `if ($leitor->nome === 'Marlene')`.

O sistema não precisa decidir o julgamento. Precisa **permitir** que ele
seja exercido por quem tem autoridade e **registrar** que foi.
:::

## O service não conhece HTTP

Com o service pronto, o controller volta ao tamanho que devia ter:

```php title="app/Http/Controllers/EmprestimoController.php" numbered
public function store(
    RealizarEmprestimoRequest $request,
    EmprestimoService $emprestimos,
) {
    $emprestimo = $emprestimos->realizar(
        $request->integer('exemplar_id'),
        $request->integer('leitor_id'),
    );

    return (new EmprestimoResource($emprestimo))
        ->response()
        ->setStatusCode(201)
        ->header(
            'Location',
            route('emprestimos.show', $emprestimo),
        );
}
```

O controller traduz HTTP para chamada de método, e resultado de método
para HTTP. As exceções que o service lança atravessam o controller sem
serem tocadas e chegam ao handler, que as transforma em `409`.

A lista do que o service **não** pode ter:

- `Request` ou `$request` em qualquer lugar;
- `abort()`, `response()`, status HTTP;
- `session()`, `redirect()`, `back()`;
- `auth()->user()` — quem é o usuário é um parâmetro, não uma consulta.

O último é o mais tentador. `auth()->user()` funciona dentro do service
quando ele é chamado pela API, e devolve `null` quando é chamado pelo
comando Artisan às três da manhã. O service passa a depender de estar
dentro de uma requisição, e ninguém percebe até o comando falhar.

O painel Blade do capítulo @cap:blade chamava um `RegistroDeEmprestimo`,
que era um esboço disto. Ele agora chama o mesmo `EmprestimoService` —
e passa a `Autorizacao` quando a Vera marca a caixa "autorizado por mim".
A API do aplicativo nunca passa: o leitor não autoriza a si mesmo.

## Um método público, uma transação

`renovar()` e `devolver()` seguem o mesmo molde:

```php title="app/Emprestimos/EmprestimoService.php" numbered
public function devolver(
    int $emprestimoId,
    DateTimeImmutable $quando,
): Emprestimo {
    return DB::transaction(function () use (
        $emprestimoId, $quando,
    ) {
        $emprestimo = Emprestimo::with('exemplar')
            ->lockForUpdate()
            ->findOrFail($emprestimoId);

        if ($emprestimo->devolvido()) {
            throw new EmprestimoJaDevolvido($emprestimoId);
        }

        $multa = $this->regras->multaPor(
            $emprestimo->prazo(), $quando,
        );

        $emprestimo->registrarDevolucao($quando, $multa);
        $emprestimo->exemplar->marcarDisponivel();

        return $emprestimo;
    });
}
```

O `$quando` vem de fora pelo motivo do capítulo
@cap:enums-datas-e-valores: quem chama decide que horas são. A API passa
`now()`; o teste passa uma data fixa; a Vera, digitando as devoluções da
caixa de devolução do fim de semana na segunda, passa a data em que o livro
foi deixado na caixa.

:::pitfall
`DB::transaction` dentro de um método **privado** é a forma mais comum de
quebrar a fronteira.

```php
public function devolverVarios(array $ids): void
{
    foreach ($ids as $id) {
        $this->devolverUm($id); // transação lá dentro
    }
}
```

Se o quinto falhar, os quatro primeiros já foram confirmados. Quem chamou
`devolverVarios` recebe uma exceção e não sabe que metade aconteceu. A
regra: **a transação é do método público**, porque é ele que promete uma
operação inteira a quem chama.
:::

## Repository: quando ajuda e quando é burocracia

Em quase todo tutorial de arquitetura em PHP aparece uma camada a mais:

```php
interface EmprestimoRepository
{
    public function find(int $id): ?Emprestimo;
    public function save(Emprestimo $e): void;
    public function emAbertoDoLeitor(int $leitorId): Collection;
}

class EloquentEmprestimoRepository implements EmprestimoRepository
{
    public function find(int $id): ?Emprestimo
    {
        return Emprestimo::find($id);
    }
    // ...
}
```

A promessa é isolar o banco: o service fala com o repositório, e o
repositório pode ser trocado por outro — outro banco, outra fonte, uma
implementação em memória para teste.

Num projeto Laravel, essa promessa precisa ser pesada contra o que o
Eloquent já é. O model **já é** um repositório: `Emprestimo::find`,
`Emprestimo::emAberto()`, `$e->save()`. O repositório acima é um arquivo que
repassa cada método para outro, com uma interface na frente e um `bind` no
provider.

**Ele ajuda quando** a fonte do dado realmente pode mudar — o acervo que
hoje está no banco e amanhã vem de uma API da prefeitura —, ou quando a
consulta é complicada o bastante para merecer nome e teste próprios.

**Ele é burocracia quando** existe para "seguir a arquitetura", em um
projeto com um banco que não vai mudar, e cada método é uma linha que
chama o Eloquent.

A Casa Amarela não tem repositório. Os scopes do capítulo @cap:eloquent dão
nome às consultas, e o capítulo @cap:testes mostra como testar as regras
sem precisar de um repositório falso: separando a regra pura da consulta.

## Nem todo projeto precisa de todas as camadas

```text
Route → Controller → Service → Model → Banco
```

Cinco camadas. Para a Casa Amarela, cada uma tem um motivo:

| Camada | Existe porque |
|---|---|
| Controller | traduz HTTP; há dois clientes (API e painel) |
| Service | a regra atravessa cinco entidades e três portas |
| Model | o dado e as perguntas de uma entidade só |

Tabela: A pergunta não é "qual é a arquitetura certa", é "o que cada camada
compra neste projeto".

E para as rotas do CRUD do acervo? `LivroController::store` recebe o Form
Request e chama `Livro::create`. Não há regra que atravesse entidades, não
há segundo cliente, não há transação com duas escritas. Um `LivroService`
com um método `criar` que chama `Livro::create` seria uma camada que só
repassa — e seria a primeira coisa que o capítulo seguinte chamaria de
sintoma.

:::term Action class
Uma alternativa ao service quando ele começa a juntar operações sem relação
entre si: uma classe por operação, com um método só.

`RealizarEmprestimo`, `RenovarEmprestimo`, `DevolverEmprestimo` em vez de
`EmprestimoService` com os três. Funciona melhor quando cada operação tem
dependências diferentes; é excesso quando as três compartilham tudo.
:::

## Service sem propósito: como reconhecer

Três sinais, e basta um:

**Todo método tem uma linha**, e a linha chama o model. O service não faz
nada que o controller não pudesse fazer direto.

**O nome é o nome de uma tabela** — `LivroService`, `UsuarioService` —, e
os métodos são `criar`, `atualizar`, `apagar`, `listar`. É o CRUD de novo,
com um arquivo a mais.

**Ele recebe `Request`.** Aí não é um service; é o controller em outro
arquivo.

O `EmprestimoService` passa nos três: seus métodos coordenam várias
entidades, o nome é de uma operação de negócio, e ele não sabe o que é
HTTP.

:::note Na sua carreira
Arquitetura em entrevista costuma virar uma lista de camadas recitada. O
que impressiona quem está do outro lado é o contrário: saber dizer **por
que não** pôr uma camada.

"Criei service para empréstimo porque a regra atravessa cinco entidades e
três portas de entrada; não criei para o cadastro de livro porque ele é uma
linha de Eloquent, e uma camada que só repassa é custo sem benefício." Essa
frase mostra critério. "Sempre uso Controller, Service e Repository" mostra
que você seguiu um tutorial.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/Emprestimos/
    EmprestimoService.php       # realizar, renovar, devolver
    RegrasDeCirculacao.php      # pura: prazo, limite, multa
    Autorizacao.php             # o julgamento, registrado
    ExemplarNaoCircula.php
    ExemplarEmExposicao.php
    UltimoExemplarExigeAutorizacao.php
    LeitorInativo.php
    LeitorComAtraso.php
    EmprestimoJaDevolvido.php
  app/Http/Controllers/
    EmprestimoController.php    # traduz HTTP, e só
:::

:::summary
- O sintoma não é o tamanho do controller; é a mesma regra em dois lugares.
- Regra de uma entidade fica no model; regra que coordena várias vai para um
  service.
- O método público do service é a fronteira da transação; efeitos que não
  devem desfazer a operação ficam fora dela.
- O service recebe valores, não `Request`; não conhece `abort`, sessão nem
  `auth()`.
- Exceções de domínio atravessam o controller intactas e o handler as
  traduz.
- Algumas regras do especialista são julgamento: o sistema permite e
  registra, não decide.
- `DB::transaction` em método privado quebra a promessa do método público.
- Repository sobre Eloquent é repasse, exceto quando a fonte do dado pode
  mesmo mudar.
- Cada camada precisa de um motivo no projeto; o CRUD simples não precisa
  de service.
:::

:::checkpoint
A regra de empréstimo está num service que você consegue ler em voz alta
para quem entende do negócio, a transação é a do método público, o
controller só traduz HTTP, e você sabe justificar, para cada camada do
projeto, por que ela existe — e por que o cadastro de livro não tem
service.
:::

:::exercise level=1
Diga onde cada regra deve morar — no model, no `RegrasDeCirculacao`, no
`EmprestimoService` ou no Form Request:

1. Um exemplar está em exposição se chegou há menos de sete dias.
2. O limite de empréstimos é cinco em janeiro e três no resto do ano.
3. `leitor_id` precisa ser um inteiro que existe na tabela.
4. Um leitor com empréstimo atrasado não pode levar outro livro.
5. O prazo de devolução é sete dias para leitores infantis.

:::answer
1. Model `Exemplar`, num método `emExposicao($quando)`. É uma pergunta sobre
   um exemplar só, e depende de um dado dele.
2. `RegrasDeCirculacao`. É um número que depende de configuração e de
   calendário, e não de consulta.
3. Form Request. É formato, com um pé no banco.
4. `EmprestimoService`. A pergunta envolve o leitor e os empréstimos dele,
   e precisa ser feita dentro da transação.
5. `RegrasDeCirculacao`, consultando `$leitor->infantil()` — que por sua vez
   mora no model `Leitor`.

O item 5 mostra a divisão em duas partes: "este leitor é infantil?" é
pergunta do model; "qual o prazo para infantil?" é regra de circulação.
:::

:::exercise level=2
Escreva o `renovar()` do `EmprestimoService` com as regras: só renova se
não estiver atrasado; no máximo duas renovações; não renova se houver
reserva para o livro. A nova data é contada a partir de hoje, com o prazo
do leitor.

:::answer
```php title="app/Emprestimos/EmprestimoService.php" numbered
public function renovar(
    int $emprestimoId,
    DateTimeImmutable $quando,
): Emprestimo {
    return DB::transaction(function () use (
        $emprestimoId, $quando,
    ) {
        $e = Emprestimo::with(['leitor', 'exemplar.livro'])
            ->lockForUpdate()
            ->findOrFail($emprestimoId);

        if ($e->devolvido()) {
            throw new EmprestimoJaDevolvido($e->id);
        }

        if ($e->emAtraso($quando)) {
            throw new RenovacaoDeAtrasado($e->id);
        }

        if ($e->renovacoes >= 2) {
            throw new RenovacaoEsgotada($e->id, 2);
        }

        if ($e->exemplar->livro->temReservaAtiva()) {
            throw new LivroReservado($e->exemplar->livro_id);
        }

        $dias = $this->regras->prazoPara($e->leitor);

        $e->renovarAte($quando->modify("+{$dias} days"));

        return $e;
    });
}
```

O `2` solto merece ir para o `RegrasDeCirculacao` na próxima vez que alguém
passar por aqui — a Vera já mencionou que nas férias escolares são três.

A reserva é conferida no **livro**, não no exemplar: quem reserva quer "um
*Dom Casmurro*", qualquer um. Conferir no exemplar deixaria renovar sempre,
porque ninguém reserva um tombo específico.
:::

:::exercise level=3
Um projeto que você acabou de assumir tem esta estrutura para o cadastro de
autores:

```text
AutorController → AutorService → AutorRepositoryInterface
                                → EloquentAutorRepository → Autor
```

O `AutorService` tem `listar`, `buscar`, `criar`, `atualizar` e `apagar`;
cada um chama o método de mesmo nome no repositório, que chama o Eloquent.
São quatro arquivos e um `bind` para um CRUD.

A pessoa que escreveu defende que "é a arquitetura do projeto" e que
"assim fica fácil trocar o banco". Escreva a sua posição na revisão,
incluindo o que você **não** mudaria agora.

:::answer
**A posição.** As duas camadas do meio não compram nada neste caso. O
service não coordena entidades, não abre transação com duas escritas, não
aplica regra; o repositório repassa ao Eloquent, que já é um repositório.
São dois arquivos e uma interface por onde toda mudança no cadastro de
autor precisa passar, sem proteger nada.

**Sobre trocar o banco.** A troca de banco que o Laravel precisa — MySQL
para PostgreSQL — o Eloquent já faz sem repositório. A troca que o
repositório permitiria — banco para outra coisa — não está no horizonte de
ninguém, e se estiver, é mais barato introduzir o repositório naquele dia,
para aquela entidade, do que manter a camada em todas por hipótese.

**O que eu não mudaria agora.** Não reescreveria os outros módulos que
seguem o mesmo padrão. "É a arquitetura do projeto" é um argumento real:
consistência tem valor, e um projeto com metade das entidades num padrão e
metade em outro é mais difícil de ler que um projeto inteiro num padrão
excessivo.

A proposta que eu levaria para a equipe é outra: **para código novo**,
camada só quando tiver motivo escrito — "service porque a regra atravessa
X e Y". O padrão antigo morre sozinho, módulo a módulo, quando alguém
precisar mexer num deles de verdade.

E eu anotaria uma pergunta para fazer em particular, não na revisão: se o
padrão veio de uma decisão com motivo que eu não conheço. Às vezes vem.
:::
