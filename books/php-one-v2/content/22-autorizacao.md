---
title: "Autorização: Gates e Policies"
number: 22
slug: autorizacao
part: p5
kicker: "O leitor ligou animado: tinha descoberto que, trocando um número no endereço, dava para ver os livros de todo mundo."
goal: >-
  Responder "o que você pode" — inclusive quando o recurso é de outra
  pessoa: separar papel de permissão, escrever Policies por recurso,
  restringir listagens por quem pergunta, e testar cada permissão, porque
  ninguém testa à mão.
---

:::story O número no endereço
O leitor se chamava Caio, tinha dezesseis anos e fazia um curso técnico de
informática. Ligou numa quinta, às cinco da tarde.

— Oi, é que eu achei uma coisa no aplicativo. Não sei se é pra ser assim.

Tainá pôs no viva-voz.

— Na tela dos meus empréstimos, se eu abro pelo navegador, aparece no
endereço `leitor_id=212`. Que sou eu. Aí eu troquei pra 211.

— E?

— Apareceram os livros da Dona Iolanda. Ela tá com três. Um é de receita.
Aí eu fui trocando. Tem gente com livro atrasado desde novembro.

Dedé, do outro lado da mesa, já estava com a rota aberta.

```php
public function index(Request $request)
{
    return EmprestimoResource::collection(
        Emprestimo::where('leitor_id', $request->leitor_id)
            ->paginate(),
    );
}
```

— Caio — disse Tainá —, você anotou quantos números testou?

— Uns trinta. Eu parei porque achei que podia dar problema.

— Deu.

— Pra mim?

— Não. Pra gente. Obrigada por ligar.
:::

## Autenticação diz quem; autorização diz o quê

A rota do Caio estava atrás do `auth:sanctum`. Ela sabia exatamente quem
estava perguntando — o leitor 212, com token válido. E respondeu sobre o
leitor 211, porque o número veio do cliente e ninguém conferiu se quem
perguntava tinha direito à resposta.

São duas perguntas, feitas em sequência:

**Autenticação:** quem é você? Respondida pelo token. Falhou, `401`.

**Autorização:** você pode fazer **isto**, com **esta coisa**? Respondida
por regra. Falhou, `403` — ou `404`, pelo critério do capítulo
@cap:erros-padronizados.

O capítulo anterior resolveu a primeira. Esta é a segunda, e ela é mais
difícil por um motivo: a autenticação é igual para toda a API, e a
autorização é **diferente para cada recurso**.

:::term Autorização em nível de objeto
Conferir, para cada registro acessado, se quem pergunta tem direito
**àquele registro específico** — e não só àquele tipo de registro.

A falha disso tem nome na lista de riscos de API mais citada do mercado,
e é o primeiro item dela: *Broken Object Level Authorization*. É o defeito
do Caio: o leitor tinha direito a ver empréstimos, e o sistema não
conferiu **quais**.
:::

:::art caption="O sistema sabia quem estava perguntando. Não conferiu o que ele podia ver."
src="o-sistema-sabia-quem-estava-perguntando-nao-conferiu-o-que-ele-podia-ver.png"
Charge editorial minimalista em fundo branco: um adolescente de moletom e
fone de ouvido, sentado com o notebook no colo, gira com o dedo um pequeno
mostrador numérico, como o de um cadeado, que troca "212" por "211". A
cada número, uma porta diferente se abre numa fileira de portas idênticas
ao fundo, cada uma com uma pilha de livros e o nome de um leitor na
plaquinha; atrás de uma delas aparece um livro de receitas. O
adolescente, em vez de entrar, pega o telefone para avisar. Poucos elementos, humor seco, estética de revista de tecnologia.
:::

## Gate para a regra solta, Policy para o recurso

O Laravel oferece dois lugares para escrever permissão.

**Gate** é uma regra com nome, solta, que não pertence a nenhum model:

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    Gate::define(
        'ver-relatorios',
        fn (Usuario $u) => $u->papel !== Papel::Leitor,
    );
}
```

```php
Gate::authorize('ver-relatorios');
```

**Policy** é uma classe que reúne todas as permissões **sobre um tipo de
recurso**:

```text
$ php artisan make:policy EmprestimoPolicy --model=Emprestimo
```

```php title="app/Policies/EmprestimoPolicy.php" numbered
<?php

declare(strict_types=1);

namespace App\Policies;

use App\Auth\Papel;
use App\Models\Emprestimo;
use App\Models\Usuario;

class EmprestimoPolicy
{
    public function view(Usuario $u, Emprestimo $e): bool
    {
        return $this->ehEquipe($u)
            || $e->leitor_id === $u->leitor_id;
    }

    public function create(Usuario $u): bool
    {
        return $this->ehEquipe($u);
    }

    public function renovar(Usuario $u, Emprestimo $e): bool
    {
        return $this->ehEquipe($u)
            || $e->leitor_id === $u->leitor_id;
    }

    public function devolver(Usuario $u, Emprestimo $e): bool
    {
        return $this->ehEquipe($u);
    }

    private function ehEquipe(Usuario $u): bool
    {
        return in_array(
            $u->papel,
            [Papel::Atendente, Papel::Admin],
            true,
        );
    }
}
```

Cada método é uma pergunta: pode ver este? Pode criar? Pode renovar este?
Os que recebem o `Emprestimo` são sobre **um registro**; o `create` não
recebe, porque o registro ainda não existe.

O Laravel encontra a policy sozinho pelo nome: `Emprestimo` →
`EmprestimoPolicy`, na pasta `app/Policies`. Nada a registrar.

Repare no `create`. O leitor **não** pode criar empréstimo pela API — quem
empresta é o balcão, com o livro na mão. O aplicativo mostra o acervo,
reserva, renova. É uma decisão da Vera que o capítulo
@cap:o-que-e-uma-api-rest não tinha como saber, e que a policy registra
numa linha.

## `authorize`, `can` e o `403` que sai sozinho

No controller:

```php title="app/Http/Controllers/EmprestimoController.php" numbered
public function show(Emprestimo $emprestimo)
{
    Gate::authorize('view', $emprestimo);

    return new EmprestimoResource($emprestimo);
}
```

`Gate::authorize` chama o método `view` da policy do `Emprestimo` com o
usuário autenticado. Se devolver `false`, lança `AuthorizationException`,
que o handler do capítulo @cap:erros-padronizados transforma em `403`.

Existe a forma que pergunta sem lançar, para quando a resposta muda o
comportamento em vez de interromper:

```php
if ($request->user()->can('renovar', $emprestimo)) {
    // mostra o botão
}
```

E o Form Request tem o `authorize()` que o capítulo
@cap:validation-e-form-requests deixou em `true`, com uma dívida anotada:

```php title="app/Http/Requests/RealizarEmprestimoRequest.php" numbered
public function authorize(): bool
{
    return $this->user()->can('create', Emprestimo::class);
}
```

Para o `create`, que não tem registro, passa-se a **classe**, e o Laravel
sabe qual policy usar por ela.

Dívida paga. E com uma vantagem de ordem: o `authorize()` roda **antes** das
regras de validação. Quem não tem permissão recebe `403` sem descobrir
quais campos a rota espera.

## O recurso é dele?

A correção da rota do Caio tem duas partes, porque a rota tinha dois
defeitos.

O primeiro é a pergunta sobre **um registro**, e a policy resolve:
`GET /emprestimos/312` passa a conferir se o 312 é do leitor.

O segundo é mais sutil. A listagem `GET /emprestimos?leitor_id=211`
aceitava um **filtro** vindo do cliente, e o filtro decidia de quem eram os
dados. A policy não ajuda aqui: não há um registro para perguntar sobre,
há uma consulta.

:::key
Na listagem, quem decide o escopo é o servidor, a partir de quem está
autenticado. **Nunca** um parâmetro.

O `leitor_id` que vem do cliente pode ser um filtro a mais — para a
bibliotecária escolher de qual leitor ver —, mas só depois de a consulta já
estar restrita ao que quem pergunta tem direito de ver.
:::

## Listagem com escopo

```php title="app/Models/Emprestimo.php" numbered
public function scopeVisivelPara(Builder $q, Usuario $u): void
{
    if ($u->papel === Papel::Leitor) {
        $q->where('leitor_id', $u->leitor_id);
    }
}
```

```php title="app/Http/Controllers/EmprestimoController.php" numbered
public function index(ListarEmprestimosRequest $request)
{
    $emprestimos = Emprestimo::visivelPara($request->user())
        ->when(
            $request->filled('leitor_id'),
            fn ($q) => $q->where(
                'leitor_id',
                $request->integer('leitor_id'),
            ),
        )
        ->with('exemplar.livro')
        ->orderByDesc('retirado_em')
        ->orderByDesc('id')
        ->cursorPaginate(20);

    return EmprestimoResource::collection($emprestimos);
}
```

A ordem das duas restrições é o ponto. O `visivelPara` vem **primeiro** e
restringe ao leitor autenticado. O filtro de `leitor_id` vem **depois**, e
para um leitor comum ele só pode estreitar o que já estava restrito. O Caio
pedindo `?leitor_id=211` recebe:

```sql
WHERE leitor_id = 212 AND leitor_id = 211
```

Uma lista vazia. Não um erro, não uma confirmação de que o 211 existe —
nada. A bibliotecária, sem a primeira restrição, recebe os empréstimos do
211.

:::pitfall
O escopo tem que estar em **toda** consulta que devolve dado do leitor, e
isso inclui as que ninguém chama de listagem: a exportação em CSV, a busca
por tombo, o contador de "você tem três livros" no cabeçalho, o endpoint
de estatística.

O defeito do Caio costuma voltar por uma dessas portas secundárias, meses
depois, numa rota nova que alguém escreveu copiando a consulta sem o
`visivelPara`. É por isso que o teste do fim do capítulo existe — e por
isso ele precisa ser escrito para toda rota nova, não só para as que
parecem sensíveis.
:::

## `before`: o admin, e o cuidado com ele

Uma policy pode ter um método que roda antes de todos os outros:

```php title="app/Policies/LivroPolicy.php" numbered
class LivroPolicy
{
    public function before(Usuario $u, string $habilidade): ?bool
    {
        return $u->papel === Papel::Admin ? true : null;
    }

    public function create(Usuario $u): bool
    {
        return $u->papel === Papel::Atendente;
    }

    public function update(Usuario $u, Livro $livro): bool
    {
        return $u->papel === Papel::Atendente;
    }

    public function delete(Usuario $u, Livro $livro): bool
    {
        return false;
    }
}
```

`before` devolvendo `true` libera tudo; devolvendo `null`, deixa o método
específico decidir. O admin pode tudo sobre livros; a atendente cadastra e
edita; ninguém mais apaga.

O `before` é conveniente e é um lugar onde regra some. Se amanhã a Vera
disser que nem o admin pode apagar livro com empréstimo em aberto, essa
regra **não pode** morar no `delete` — o `before` libera antes de o
`delete` ser consultado. Ou o `before` ganha uma exceção, ou a regra vai
para o service. É o tipo de coisa que precisa estar escrita no próprio
arquivo, num comentário curto, para a próxima pessoa não cair.

## Papel não é permissão

As policies acima perguntam o **papel** diretamente: `Papel::Atendente`,
`Papel::Admin`. Funciona com três papéis, e envelhece mal por um motivo
previsível: o dia em que a Casa Amarela contratar uma voluntária que pode
cadastrar livros e **não** pode ver documento de leitor.

A voluntária não é atendente nem leitora. Um quarto papel obriga a revisar
todas as policies, procurando cada `Papel::Atendente` e decidindo se ele
vale para ela.

A separação que envelhece bem: o papel é uma **coleção de permissões**, e
as policies perguntam pela permissão.

```php title="app/Auth/Papel.php" numbered
enum Papel: string
{
    case Leitor = 'leitor';
    case Atendente = 'atendente';
    case Admin = 'admin';

    public function permite(Permissao $p): bool
    {
        return in_array($p, $this->permissoes(), true);
    }

    /** @return list<Permissao> */
    public function permissoes(): array
    {
        return match ($this) {
            self::Leitor => [],
            self::Atendente => [
                Permissao::CadastrarAcervo,
                Permissao::VerDadosDeLeitor,
                Permissao::RegistrarCirculacao,
            ],
            self::Admin => Permissao::cases(),
        };
    }
}
```

```php
public function create(Usuario $u): bool
{
    return $u->papel->permite(Permissao::CadastrarAcervo);
}
```

A voluntária vira um caso novo no enum, com a lista dela. Nenhuma policy
muda. O `match` do capítulo @cap:enums-datas-e-valores garante que o caso
novo não fica sem lista: sem a linha, a chamada lança
`UnhandledMatchError`.

E o `habilidades()` que o `createToken` do capítulo anterior chamava vem
daqui: são os nomes das permissões, gravados no token. Um token de leitor
não carrega `registrar-circulacao`, e o `tokenCan` pode conferir isso
mesmo antes de consultar o papel.

:::pitfall
Gravar o papel ou as habilidades **no token** tem um custo: o token é
emitido no login e dura trinta dias. Se a Vera tirar a permissão de uma
atendente na segunda, o token dela continua com as habilidades antigas até
expirar.

Duas saídas, e as duas são usadas juntas. A policy confere o papel **atual**
no banco — `$u->papel` é lido a cada requisição —, e o token é só uma
segunda restrição. E mudar o papel de alguém revoga os tokens dessa
pessoa, como a troca de senha do capítulo anterior.
:::

## Testar permissão é obrigatório

Ninguém testa permissão à mão, porque testar à mão exige três contas, dois
papéis e a paciência de trocar de login a cada tentativa. O Caio testou
porque tinha dezesseis anos e uma tarde livre.

A suíte do capítulo @cap:testes-de-feature-http-e-banco trata disso em
detalhe. O formato já cabe aqui:

```php title="tests/Feature/EmprestimoAutorizacaoTest.php" numbered
test('leitor não vê empréstimo de outro leitor', function () {
    $caio = Usuario::factory()->leitor()->create();
    $iolanda = Leitor::factory()->create();
    $alheio = Emprestimo::factory()
        ->for($iolanda)
        ->create();

    $this->actingAs($caio)
        ->getJson("/api/emprestimos/{$alheio->id}")
        ->assertForbidden();
});

test('filtro de leitor não amplia o escopo', function () {
    $caio = Usuario::factory()->leitor()->create();
    Emprestimo::factory()->count(3)->create();

    $this->actingAs($caio)
        ->getJson('/api/emprestimos?leitor_id=211')
        ->assertOk()
        ->assertJsonCount(0, 'data');
});
```

Dois testes, e os dois reproduzem o que o Caio fez. Se alguém, daqui a seis
meses, reescrever a listagem e esquecer o `visivelPara`, a esteira fica
vermelha antes de o aplicativo ser publicado.

:::note Na sua carreira
Autorização em nível de objeto é o defeito de segurança mais comum em API,
e o mais fácil de explicar a quem não é técnico: "trocando o número no
endereço, dá para ver o dado de outra pessoa".

Quando você fizer revisão de código numa rota que recebe um identificador,
faça duas perguntas, sempre: **quem garante que esse registro é de quem
pergunta?** e **quem garante que essa lista só tem o que ele pode ver?** Se
a resposta for "o aplicativo só mostra os dele", a rota está aberta — o
aplicativo é o único cliente que não vai tentar outro número.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/Auth/
    Papel.php                   # papel → lista de permissões
    Permissao.php               # enum
  app/Policies/
    EmprestimoPolicy.php        # ver e renovar só os próprios
    LivroPolicy.php             # atendente cadastra, ninguém apaga
    LeitorPolicy.php
  app/Models/
    Emprestimo.php              # scopeVisivelPara
  tests/Feature/
    EmprestimoAutorizacaoTest.php
:::

:::milestone
Fim da Parte 5. A regra de empréstimo mora num service que a Vera consegue
ler; a API sabe quem está perguntando, guarda senhas do jeito certo, revoga
tokens na hora; e cada recurso confere se quem pede tem direito àquele
registro — com um teste para o número trocado no endereço.

No caderno da Tainá: *"o aplicativo é o único cliente que não vai trocar o
número"*.
:::

:::summary
- Autenticação responde quem é você (`401`); autorização, o que você pode
  com esta coisa (`403`).
- Autorização em nível de objeto confere o registro, não só o tipo; a
  falha dela é o primeiro risco de API.
- Gate é regra solta com nome; Policy reúne as permissões de um recurso e é
  descoberta pelo nome.
- `Gate::authorize` lança e vira `403`; `can` pergunta sem lançar;
  `authorize()` do Form Request roda antes da validação.
- Listagem se restringe pelo usuário autenticado, no servidor; parâmetro do
  cliente só estreita.
- `before` libera antes do método específico, e regra que vale até para o
  admin não pode morar depois dele.
- Papel é uma coleção de permissões; policies perguntam pela permissão.
- Habilidade gravada no token envelhece; a policy confere o papel atual, e
  mudar o papel revoga os tokens.
- Permissão se testa com um teste para cada caso, porque ninguém testa à
  mão.
:::

:::checkpoint
O leitor vê e renova só os próprios empréstimos, a atendente cadastra e o
admin administra, toda listagem é restrita por quem pergunta antes de
qualquer filtro, e existe um teste para o número trocado no endereço — e
outro para o filtro que tenta ampliar o escopo.
:::

:::exercise level=1
Para cada requisição, diga o status esperado e qual mecanismo o produz:

1. Leitor 212 pede `GET /emprestimos/900`, que é do leitor 211.
2. Leitor 212 pede `POST /emprestimos`.
3. Atendente pede `DELETE /livros/12`.
4. Requisição sem token pede `GET /eu`.
5. Leitor 212 pede `GET /emprestimos?leitor_id=211`.

:::answer
1. `403`, pela `EmprestimoPolicy::view` chamada no `show` — ou `404`, se a
   equipe decidir que a existência de um empréstimo alheio não deve ser
   confirmada.
2. `403`, pelo `authorize()` do `RealizarEmprestimoRequest`, antes de
   qualquer validação.
3. `403`, pela `LivroPolicy::delete`, que devolve `false` — o `before` não
   libera, porque ela não é admin.
4. `401`, pelo `auth:sanctum`, antes de chegar a qualquer policy.
5. `200` com lista vazia, pelo `scopeVisivelPara`. Não é `403`: a pergunta
   é permitida, e a resposta é que não há nada que ele possa ver ali.

O item 5 costuma ser respondido como `403`. A diferença importa: um `403`
diria ao Caio que o filtro foi entendido e recusado; a lista vazia não diz
nada.
:::

:::exercise level=2
Escreva a `LeitorPolicy` com as regras: o leitor vê e edita só o próprio
cadastro; a equipe vê todos; só a equipe edita o perfil de outro leitor; o
documento só pode ser alterado por admin. E escreva como o
`UpdateLeitorRequest` usa a policy para o campo documento.

:::answer
```php title="app/Policies/LeitorPolicy.php" numbered
class LeitorPolicy
{
    public function view(Usuario $u, Leitor $l): bool
    {
        return $u->leitor_id === $l->id
            || $u->papel->permite(Permissao::VerDadosDeLeitor);
    }

    public function update(Usuario $u, Leitor $l): bool
    {
        return $u->leitor_id === $l->id
            || $u->papel->permite(Permissao::VerDadosDeLeitor);
    }

    public function alterarDocumento(Usuario $u, Leitor $l): bool
    {
        return $u->papel === Papel::Admin;
    }
}
```

```php title="app/Http/Requests/UpdateLeitorRequest.php" numbered
public function authorize(): bool
{
    $leitor = $this->route('leitor');

    if (!$this->user()->can('update', $leitor)) {
        return false;
    }

    return !$this->has('documento')
        || $this->user()->can('alterarDocumento', $leitor);
}
```

O `alterarDocumento` é uma habilidade que não corresponde a nenhuma rota —
é uma permissão sobre **um campo**. A policy aceita métodos com qualquer
nome, e é assim que permissões mais finas que o CRUD ganham lugar.

Uma alternativa seria aceitar o pedido e ignorar o documento em silêncio
para quem não é admin. É pior: o cliente acha que alterou e não alterou. A
recusa explícita diz o que aconteceu.
:::

:::exercise level=3
O relatório "leitores com mais de trinta dias de atraso" existe no painel,
para a equipe. Uma pessoa do time vai expô-lo na API para um futuro
aplicativo da equipe, em `GET /relatorios/atrasados`.

Liste tudo que precisa ser decidido e protegido antes de publicar a rota, e
escreva o teste que você exigiria na revisão.

:::answer
**Decisões e proteções:**

**Quem pode.** Um Gate `ver-relatorios` ou uma permissão
`VerRelatorios`, não "qualquer um da equipe" por papel direto — a
voluntária futura provavelmente não deve ver quem está devendo.

**O que sai.** O relatório do painel mostra nome, telefone e títulos. Na
API, um `RelatorioDeAtrasoResource` decide campo a campo. O documento não
sai. O telefone sai só se o aplicativo vai ligar para as pessoas — e aí
é uma decisão da Vera, não do time.

**Teto e paginação.** É uma lista de pessoas. Sem teto, é uma exportação da
base de devedores numa requisição.

**Registro de acesso.** Quem consultou e quando vai para o log, com o
incidente. É dado pessoal sensível — dívida — e a associação precisa poder
responder quem viu.

**Token.** Um token de leitor não pode ter a habilidade, mesmo que a policy
esteja certa — as duas camadas.

**O teste que eu exigiria:**

```php
test('só quem tem permissão vê o relatório', function (
    Papel $papel,
    int $status,
) {
    $u = Usuario::factory()->comPapel($papel)->create();

    $this->actingAs($u)
        ->getJson('/api/relatorios/atrasados')
        ->assertStatus($status);
})->with([
    'leitor' => [Papel::Leitor, 403],
    'atendente' => [Papel::Atendente, 200],
    'admin' => [Papel::Admin, 200],
]);
```

Mais um, conferindo que `documento` não aparece em nenhum item da
resposta. E, quando a voluntária for criada, a linha dela entra nesse
`with` — e o teste obriga alguém a decidir o status esperado.
:::
