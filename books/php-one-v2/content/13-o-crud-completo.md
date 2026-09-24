---
title: "O CRUD completo"
number: 13
slug: o-crud-completo
part: p4
kicker: "Seu Juvenal perguntou se aquilo não era só um CRUD. A resposta tinha onze itens e estava no caderno da estagiária."
goal: >-
  Ligar rotas, controllers, models e banco com as cinco operações
  devolvendo o status certo, fazer uma operação de negócio caber num
  commit, e terminar sabendo listar o que ainda está errado.
---

:::story Só um CRUD
A tela de cadastro de livro ficou pronta na quarta. Dedé mostrou: listar,
abrir, editar, apagar.

— Bonito — disse Seu Juvenal. — Mas isso não é só um CRUD?

Tainá virou o caderno na página da primeira semana e leu em voz alta.

— Se ela for sócia. Se não tiver livro atrasado. Se não dever multa acima
de cinco reais. Se não estiver com três livros já. Se o exemplar não for da
referência. Se não for o último exemplar do título. Se for menor de doze, o
responsável assina. Se o livro chegou essa semana, fica em exposição. Se for
período de prova, o prazo cai para sete. Se for da coleção do senhor, não
sai. E se for a Dona Marlene, sai.

Ela parou.

— Onze.

— Pois é — disse Dedé. — Em qual das cinco telas isso cabe?

Seu Juvenal pensou um pouco.

— Na de emprestar.

— A de emprestar não está aí.
:::

:::art caption="O CRUD cabe em cinco telas. A regra de emprestar, não."
src="o-crud-cabe-em-cinco-telas-a-regra-de-emprestar-nao.png"
Charge editorial minimalista em fundo branco: um quadro com cinco caixas
pequenas e organizadas, rotuladas "listar", "abrir", "criar", "editar" e
"apagar". Diante do quadro, uma estagiária lê em voz alta um caderno aberto
de onde escorre, até o chão e pela sala, uma tira de papel comprida como um
rolo de recibo, cheia de linhas que começam com "SE". Um senhor de boné
olha para as cinco caixas e depois para a tira, coçando a cabeça. Um
desenvolvedor, de braços cruzados, aponta para o espaço vazio onde faltaria
uma sexta caixa. Poucos elementos, humor seco, estética de revista de tecnologia.
:::

## As cinco rotas e o que cada uma promete

O CRUD do acervo são cinco operações, e o desenho delas foi feito no
capítulo @cap:o-que-e-uma-api-rest. Agora elas viram código.

```php title="routes/api.php" numbered
Route::apiResource('livros', LivroController::class);
```

| Método | Rota | Promete | Devolve |
|---|---|---|---|
| `index` | `GET /livros` | a lista, paginada | `200` |
| `store` | `POST /livros` | criar um novo | `201` + `Location` |
| `show` | `GET /livros/{livro}` | um item | `200` ou `404` |
| `update` | `PUT/PATCH /livros/{livro}` | alterar | `200` ou `404` |
| `destroy` | `DELETE /livros/{livro}` | remover | `204` ou `404` |

Tabela: Cinco linhas que qualquer pessoa que já consumiu uma API consegue
adivinhar sem documentação. É o valor inteiro da convenção.

## Criar

```php title="app/Http/Controllers/LivroController.php" numbered
public function store(Request $request)
{
    $dados = $request->validate([
        'titulo' => ['required', 'string', 'max:200'],
        'autor' => ['required', 'string', 'max:150'],
        'assunto' => ['required', 'string', 'max:40'],
        'isbn' => ['nullable', 'string', 'size:13', 'unique:livros'],
        'ano' => ['nullable', 'integer', 'min:1400'],
    ]);

    $livro = Livro::create($dados);

    return response()
        ->json($livro, 201)
        ->header('Location', route('livros.show', $livro));
}
```

:::http title="A criação, de ponta a ponta"
POST /api/livros
Content-Type: application/json

{"titulo": "Vidas Secas", "autor": "Graciliano Ramos",
 "assunto": "literatura", "ano": 1938}
---
201 Created
Location: /api/livros/4031
Content-Type: application/json

{
  "id": 4031,
  "titulo": "Vidas Secas",
  "autor": "Graciliano Ramos",
  "assunto": "literatura",
  "ano": 1938,
  "created_at": "2026-01-21T14:02:55.000000Z"
}
:::

Três decisões estão nessas dez linhas.

**O recurso volta no corpo.** O cliente acabou de criar uma coisa e precisa
do `id` para continuar. Devolver vazio obrigaria uma segunda requisição.

**O `Location` aponta para onde ela mora.** É o que permite ao cliente
consultá-la depois sem montar a URL à mão.

**A validação está no controller.** Funciona, e é a primeira coisa que este
capítulo vai listar como problema no fim.

## Ler um: `404` é uma resposta

```php
public function show(Livro $livro)
{
    return $livro;
}
```

Duas linhas, e o `404` já está tratado: o binding do capítulo
@cap:rotas-e-controllers procura o registro e interrompe antes de entrar no
método quando não acha.

:::key
`404` não é falha da aplicação. É a resposta correta para uma pergunta sobre
uma coisa que não existe.

A distinção importa no monitoramento: um sistema que trata `404` como erro
enche o painel de alertas toda vez que alguém digita um endereço errado, e
o alerta que importa fica perdido no meio.
:::

## `PUT` e `PATCH` não são a mesma coisa

O `apiResource` aponta os dois verbos para o mesmo método. A diferença entre
eles é sua para implementar — e ignorá-la produz um defeito específico.

**`PUT` substitui o recurso inteiro.** O que não vier no corpo deixa de
existir.

**`PATCH` altera o que veio.** O que não vier fica como estava.

```text
PATCH /api/livros/4031
{"assunto": "didatico"}
```

Se o método tratar isso como `PUT`, o livro perde autor, ISBN e ano — porque
não vieram.

```php title="app/Http/Controllers/LivroController.php" numbered
public function update(Request $request, Livro $livro)
{
    $regras = [
        'titulo' => ['string', 'max:200'],
        'autor' => ['string', 'max:150'],
        'assunto' => ['string', 'max:40'],
        'isbn' => ['nullable', 'string', 'size:13'],
        'ano' => ['nullable', 'integer', 'min:1400'],
    ];

    if ($request->isMethod('PUT')) {
        $regras['titulo'][] = 'required';
        $regras['autor'][] = 'required';
        $regras['assunto'][] = 'required';
    }

    $livro->update($request->validate($regras));

    return $livro;
}
```

Com `PUT`, os campos obrigatórios voltam a ser obrigatórios — quem manda o
recurso inteiro precisa mandá-lo inteiro. Com `PATCH`, o `update` só toca no
que veio.

:::pitfall
A maioria das APIs implementa só um dos dois e aceita os dois verbos, o que
produz o pior resultado possível: o cliente lê na documentação que `PUT`
substitui, manda um `PUT` parcial esperando que o resto seja apagado — e o
resto fica.

Se você for implementar um só, **implemente `PATCH` e recuse `PUT`** com
`405`. Uma recusa clara é melhor que um verbo que mente.
:::

## Apagar

```php
public function destroy(Livro $livro)
{
    $livro->delete();

    return response()->noContent();
}
```

Quatro linhas, e uma pergunta atrás delas: **apagar de verdade?**

Um livro com histórico de empréstimos não deveria sumir, pelo motivo do
capítulo @cap:relacionamentos. Com `SoftDeletes`, o `delete()` acima passa a
preencher `deleted_at`, e a resposta `204` continua a mesma para quem chama.

O cliente não precisa saber a diferença. A API promete que o recurso sai das
listagens, e ela cumpre.

## Uma operação de negócio, um `commit`

O empréstimo não é uma das cinco. Ele escreve em dois lugares, e os dois
precisam acontecer juntos:

```php title="app/Http/Controllers/EmprestimoController.php" numbered
public function store(Request $request)
{
    $dados = $request->validate([
        'exemplar_id' => [
            'required', 'integer', 'exists:exemplares,id',
        ],
        'leitor_id' => [
            'required', 'integer', 'exists:leitores,id',
        ],
    ]);

    $emprestimo = DB::transaction(function () use ($dados) {
        $exemplar = Exemplar::lockForUpdate()
            ->findOrFail($dados['exemplar_id']);

        if ($exemplar->estado !== StatusExemplar::Bom) {
            abort(409, 'Exemplar indisponível');
        }

        $abertos = Emprestimo::emAberto()
            ->where('leitor_id', $dados['leitor_id'])
            ->count();

        if ($abertos >= config('biblioteca.limite_por_leitor')) {
            abort(409, 'Limite de empréstimos atingido');
        }

        $emprestimo = Emprestimo::create([
            'exemplar_id' => $exemplar->id,
            'leitor_id' => $dados['leitor_id'],
            'retirado_em' => now(),
            'devolver_ate' => now()->addDays(
                config('biblioteca.prazo_em_dias'),
            ),
        ]);

        $exemplar->update(['estado' => StatusExemplar::Emprestado]);

        return $emprestimo;
    });

    return response()
        ->json($emprestimo, 201)
        ->header('Location', route('emprestimos.show', $emprestimo));
}
```

`DB::transaction` abre a transação, executa a função e confirma no fim. Se
qualquer exceção subir — inclusive o `abort` —, ele desfaz tudo e a exceção
segue.

O `lockForUpdate()` é o `SELECT ... FOR UPDATE` do capítulo @cap:pdo,
escrito em Eloquent. Ele trava a linha do exemplar até o fim da transação, e
é o que impede a Vera e a Neide de emprestarem o mesmo exemplar no mesmo
segundo.

:::key
A régua da transação não é "quantas consultas". É: **quantas dessas
gravações precisam ser verdade ao mesmo tempo?**

Criar o empréstimo sem mudar o exemplar produz um livro emprestado que o
sistema acha disponível. Mudar o exemplar sem criar o empréstimo produz um
livro indisponível que ninguém pegou. As duas metades sozinhas são piores
que nenhuma.
:::

## "É só um CRUD"

O acervo está no ar. As cinco rotas funcionam, o empréstimo respeita duas
regras e a transação fecha. É um bom lugar para parar e ser honesto sobre o
que este capítulo deixou errado — de propósito, porque escrever primeiro a
versão errada é o único jeito de a correção fazer sentido.

**A validação está no controller.** Quinze linhas de regras no meio de um
método que deveria ter três. E elas se repetem no `store` e no `update`,
com uma diferença que alguém vai esquecer de sincronizar.

**A resposta é o model cru.** O JSON devolvido é o retrato da tabela:
`created_at`, `updated_at`, `livro_id`. No dia em que a coluna mudar de
nome, o aplicativo publicado quebra — e ele nem devia saber que existem
colunas.

**A regra de negócio está no controller.** Duas das onze regras da Vera
estão ali dentro, e não têm como ser testadas sem subir uma requisição. As
outras nove não estão em lugar nenhum.

**O erro é uma frase.** `abort(409, 'Exemplar indisponível')` devolve texto.
Quem consome não consegue decidir nada sem ler a frase, e a frase muda.

**Não há autenticação.** Qualquer pessoa com o endereço cria empréstimo em
nome de qualquer leitor.

Cinco itens. Nenhum deles é um acidente de escrita — cada um é o assunto de
uma decisão que ainda não foi tomada.

:::note Na sua carreira
"É só um CRUD" é dito com frequência e quase sempre está errado, mas a
resposta "não é" não convence ninguém.

O que convence é o caderno da Tainá: uma lista de regras reais, ditas por
quem faz o trabalho, e a pergunta de onde cada uma vai morar. Onze regras
não cabem em cinco telas — e quando você mostra isso numa reunião, a
conversa sobre prazo muda de assunto sozinha.

O trabalho de levantar essa lista costuma caber a você, porque ninguém mais
vai fazer. E é o trabalho que transforma uma estimativa em dias numa
estimativa em regras, que é a única que sobrevive à segunda semana.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/Http/Controllers/
    LivroController.php       # as cinco operações
    ExemplarController.php
    EmprestimoController.php  # com a regra dentro, por enquanto
  app/Models/
    Livro.php                 # SoftDeletes
    Exemplar.php
    Emprestimo.php
  routes/api.php
:::

:::summary
- `apiResource` entrega cinco operações que qualquer consumidor adivinha
  sem documentação.
- Criação devolve `201`, o recurso no corpo e o `Location` apontando para
  ele.
- `404` é resposta, não falha; tratá-lo como erro polui o monitoramento.
- `PUT` substitui e `PATCH` altera; os dois chegam ao mesmo método, e a
  diferença é sua para implementar.
- Implementar um só e aceitar os dois verbos é pior que recusar um com
  `405`.
- Exclusão de entidade com histórico é lógica, e o cliente não precisa
  saber.
- `DB::transaction` confirma no fim e desfaz em qualquer exceção;
  `lockForUpdate` trava a linha disputada.
- A régua da transação é quantas gravações precisam ser verdade ao mesmo
  tempo.
- O CRUD deste capítulo tem cinco defeitos nomeados, e nenhum deles é de
  digitação.
:::

:::checkpoint
Você entrega as cinco operações com os status corretos, sabe explicar a
diferença entre `PUT` e `PATCH` pelo que acontece com os campos ausentes,
envolve uma operação de negócio numa transação com a linha travada, e
consegue listar por escrito o que ainda está errado no que acabou de
entregar.
:::

:::exercise level=1
Para cada requisição, diga o que a API deve responder:

1. `POST /api/livros` com o título faltando.
2. `GET /api/livros/99999`, que não existe.
3. `DELETE /api/livros/4031`, que existe e tem empréstimos no histórico.
4. `PUT /api/livros/4031` com só o campo `assunto`.
5. `POST /api/emprestimos` para um exemplar já emprestado.

:::answer
1. `422`, com a lista de campos que falharam. Não é `400`: o JSON estava
   correto.
2. `404`, e o binding devolve isso sem entrar no método.
3. `204`. O registro some das listagens por exclusão lógica, e o histórico
   continua. Quem chama não vê diferença.
4. `422`. `PUT` substitui o recurso inteiro, então os campos obrigatórios
   são obrigatórios — mandar só o `assunto` é um pedido incompleto.
5. `409`. O pedido está correto e o estado do sistema não permite. É a
   diferença do capítulo @cap:o-que-e-uma-api-rest entre conteúdo inválido e
   realidade incompatível.

O par que mais erra é o 4 e o 5. Os dois recusam, e os dois dizem coisas
diferentes: no 4, o cliente corrige o que mandou; no 5, ele recarrega a tela
porque outra pessoa pegou o livro primeiro.
:::

:::exercise level=2
Escreva o `destroy` do `ExemplarController` com a regra: um exemplar
emprestado não pode ser removido.

Depois responda: por que essa conferência **não** pode ficar na tela, e o
que acontece se ela ficar só lá?

:::answer
```php title="app/Http/Controllers/ExemplarController.php" numbered
public function destroy(Exemplar $exemplar)
{
    if ($exemplar->estado === StatusExemplar::Emprestado) {
        abort(409, 'Exemplar emprestado não pode ser removido');
    }

    $exemplar->delete();

    return response()->noContent();
}
```

A conferência não pode ficar só na tela porque **a tela não é o único
caminho até essa operação**. A mesma rota é alcançável por `curl`, pelo
aplicativo, por um script de importação e por qualquer integração futura.

Se ela ficar só na tela, o resultado é um exemplar removido com empréstimo
aberto: a Dona Marlene está com o livro e o sistema não sabe de quem
cobrar. E o pior é que ninguém vai descobrir na hora — vai descobrir na
conferência de inventário, meses depois, com um número que não fecha.

É a mesma ideia do capítulo @cap:requests-e-responses sobre validação de
formulário: o cliente confere para ser gentil, o servidor confere porque é o
único que pode.
:::

:::exercise level=3
Este `update` passou na revisão e está em produção há duas semanas. Um
cliente relatou que "às vezes o livro perde o autor".

```php
public function update(Request $request, Livro $livro)
{
    $livro->update($request->all());

    return $livro;
}
```

Explique o que acontece, por que é intermitente, e escreva as três correções
em ordem de urgência.

:::answer
**O que acontece.** São dois defeitos que se combinam.

O `$request->all()` entrega ao `update` tudo que veio. Se o cliente mandar
`{"autor": null}` — o que um formulário com o campo vazio faz —, o autor vai
a nulo. E se mandar campos que não existem na tabela, o `$fillable` os
descarta em silêncio, então metade do pedido some sem aviso.

**Por que é intermitente.** Depende de qual tela do aplicativo fez a
chamada. A tela de edição completa manda todos os campos e funciona; a tela
rápida de mudar o assunto manda dois campos, e a biblioteca de formulário do
aplicativo inclui os campos vazios como `null`. Ninguém reproduz o defeito
testando pela tela principal.

**As três correções, em ordem.**

**Primeira, hoje:** trocar `all()` pelo retorno da validação, que só devolve
o que foi declarado.

```php
$dados = $request->validate([
    'titulo' => ['sometimes', 'required', 'string', 'max:200'],
    'autor' => ['sometimes', 'required', 'string', 'max:150'],
    'assunto' => ['sometimes', 'required', 'string', 'max:40'],
]);

$livro->update($dados);
```

O `sometimes` é a peça que faz o `PATCH` funcionar: a regra só é aplicada se
o campo **vier**. Um `autor` ausente é ignorado; um `autor` presente e nulo
é recusado com `422`.

**Segunda, nesta semana:** distinguir `PUT` de `PATCH`, para que o verbo
signifique alguma coisa.

**Terceira, quando der:** um teste que mande exatamente o corpo da tela
rápida — dois campos e três nulos — e confira que o autor continua lá. Sem
ele, a primeira correção some na próxima alteração desse método.

E uma observação que não é correção: o defeito passou na revisão porque
`update($request->all())` é uma linha curta e familiar. Código errado que
parece limpo atravessa mais revisões que código certo e feio.
:::
