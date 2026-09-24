---
title: "Validation e Form Requests"
number: 14
slug: validation-e-form-requests
part: p4
kicker: "O mesmo livro estava três vezes no acervo. O ISBN era igual nos três — a não ser pelos hífens."
goal: >-
  Recusar a entrada inválida na porta, tirar as regras de forma de dentro do
  controller, fazer o PATCH parcial funcionar sem apagar campo, e saber
  dizer o que não é validação e por isso não vai para lá.
---

:::story Três Dom Casmurro
Vera pediu o relatório de títulos duplicados porque a contagem do acervo
não batia com a do inventário de papel. Dedé rodou a consulta esperando
zero.

```text
mysql> SELECT titulo, isbn FROM livros
    ->  WHERE titulo LIKE 'Dom Casmurro%';
+--------------+-------------------+
| titulo       | isbn              |
+--------------+-------------------+
| Dom Casmurro | 9788535910667     |
| Dom Casmurro | 978-85-359-1066-7 |
| Dom Casmurro | 978 8535910667    |
+--------------+-------------------+
```

— Mas o ISBN é `unique` — disse Tainá. — Eu vi na migration.

— É. E os três são diferentes.

— São o mesmo número.

— Pra você.

Vera olhou por cima do ombro dele.

— O primeiro fui eu. O segundo foi a Neide, que copia da ficha
catalográfica. O terceiro não sei, mas tem espaço, então foi alguém com
pressa.

— E qual é o certo?

— O livro — disse Vera. — Os três são o mesmo livro. Eu tenho dois
exemplares dele na estante, não seis.
:::

## Validação não é regra de negócio

Antes de qualquer código, uma separação que este capítulo inteiro depende
dela. Existem duas perguntas diferentes que uma requisição precisa
responder antes de virar gravação:

**O pedido está bem formado?** O título veio? É texto? Cabe em duzentos
caracteres? O ISBN tem treze dígitos? O `exemplar_id` é um número que existe
na tabela?

**O pedido é permitido agora?** O exemplar está disponível? O leitor já está
com três livros? Deve multa acima de cinco reais?

A primeira pergunta é sobre **o formato do que chegou**, e pode ser
respondida olhando só para o corpo da requisição e, no máximo, para a
existência de um registro. A segunda é sobre **o estado do mundo**, e
depende de coisas que mudam entre um segundo e o outro.

| Pergunta | Exemplo | Resposta errada | Onde mora |
|---|---|---|---|
| bem formado? | ISBN com 13 dígitos | `422` | validação |
| permitido agora? | exemplar disponível | `409` | regra de negócio |

Tabela: Os dois status do capítulo @cap:o-que-e-uma-api-rest, agora com
endereço no código. O `422` diz "corrija o que mandou"; o `409` diz "o que
você mandou está certo e o mundo não deixa".

:::key
Validação olha para **o pedido**. Regra de negócio olha para **o mundo**.

Quando você não sabe onde uma conferência vai, faça a pergunta: se o
cliente mandar exatamente o mesmo corpo daqui a cinco minutos, a resposta
pode mudar? Se pode, não é validação.
:::

Essa separação importa porque as duas coisas têm vidas diferentes. A regra
de formato quase nunca muda — um ISBN vai continuar tendo treze dígitos. A
regra de negócio muda toda vez que a Vera lembra de uma exceção, e ela
precisa ser testada sem HTTP, o que é o assunto do capítulo
@cap:services.

## Regras onde o dado entra

No capítulo anterior, a validação ficou dentro do controller:

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

    // ...
}
```

Ela funciona. O `validate()` confere, e, se algo falhar, lança uma
`ValidationException` que o Laravel transforma em `422` sem que o seu
método continue. É a mesma interrupção do binding que devolve `404`: o
código depois da linha só roda se a linha passou.

O que está errado não é o comportamento, é o **endereço**. São três
problemas, e eles pioram com o tempo.

**O controller cresce pelo lado errado.** O método `store` tem uma
responsabilidade — receber o pedido e entregar a resposta — e agora tem
quinze linhas de regras de formato antes de começar a fazer isso.

**As regras se repetem.** O `update` tem quase as mesmas, com uma diferença
no `unique` que alguém vai esquecer de sincronizar. E a tela da Vera, no
painel Blade, tem uma terceira cópia.

**As regras não têm nome.** Para saber o que a API aceita num `POST
/livros`, alguém precisa abrir o controller e ler um array no meio de um
método. Não existe um lugar que se chame "o que é um livro válido".

## Form Request: o controller que volta a ter quatro linhas

O Laravel tem uma classe cujo único trabalho é responder à primeira
pergunta:

```text
$ php artisan make:request StoreLivroRequest

   INFO  Request [app/Http/Requests/StoreLivroRequest.php]
         created successfully.
```

```php title="app/Http/Requests/StoreLivroRequest.php" numbered
<?php

declare(strict_types=1);

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class StoreLivroRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'titulo' => ['required', 'string', 'max:200'],
            'autor' => ['required', 'string', 'max:150'],
            'assunto' => ['required', 'string', 'max:40'],
            'isbn' => [
                'nullable', 'digits:13', 'unique:livros,isbn',
            ],
            'ano' => [
                'nullable', 'integer', 'min:1400',
                'max:' . now()->year,
            ],
        ];
    }
}
```

E o controller:

```php title="app/Http/Controllers/LivroController.php" numbered
public function store(StoreLivroRequest $request)
{
    $livro = Livro::create($request->validated());

    return response()
        ->json($livro, 201)
        ->header('Location', route('livros.show', $livro));
}
```

A mudança está no **tipo do parâmetro**. Quando o Laravel vai chamar o
`store`, ele vê que o método pede um `StoreLivroRequest`, constrói esse
objeto a partir da requisição e **roda a validação antes de entregar**. Se
falhar, o método nunca é chamado.

É o contêiner do capítulo @cap:um-framework-de-quarenta-linhas lendo o tipo
do parâmetro por reflexão, com um passo a mais no meio. O capítulo
@cap:service-container abre essa caixa por inteiro.

:::term Form Request
Uma classe que representa um tipo de pedido — "criar livro", "realizar
empréstimo" — e carrega as regras de formato dele. O controller declara que
recebe esse tipo, e a validação acontece antes do método começar.
:::

O `validated()` devolve **só os campos que têm regra**. Se o cliente mandar
`observacao_interna` ou `perfil`, eles não estão em `rules()` e não chegam ao
`create`. É uma segunda camada de proteção atrás do `$fillable` do
capítulo @cap:eloquent, e a mais importante das duas: ela barra na porta,
antes de o dado chegar perto do model.

:::pitfall
`$request->all()` depois de um Form Request devolve **tudo que veio**, não
só o que passou. A validação aconteceu, mas o resultado dela foi ignorado.

```php
Livro::create($request->all());       // o corpo inteiro
Livro::create($request->validated()); // só o que tem regra
```

As duas linhas têm o mesmo tamanho, e a primeira desfaz metade do trabalho
do capítulo. Numa revisão de código, `all()` depois de Form Request é um
defeito, não um estilo.
:::

### O `authorize()` que devolve `true`

O método `authorize()` pergunta se **esta pessoa** pode fazer **este
pedido**. Por enquanto, ele devolve `true` para todo mundo — ainda não
existe "esta pessoa", porque a API não tem login.

Deixá-lo em `true` é uma decisão honesta para este capítulo, e uma dívida
anotada: o capítulo @cap:autorizacao volta a ele. Se `authorize()` devolver
`false`, o Laravel responde `403` sem chamar o controller, e é por isso que
ele existe aqui e não em outro lugar.

## Normalizar antes de conferir

As três linhas de *Dom Casmurro* passaram pelo `unique` porque `unique`
compara texto, e `9788535910667` e `978-85-359-1066-7` são textos
diferentes. A regra estava certa. O dado chegou em três formas.

A correção é a lição do capítulo @cap:strings, agora com endereço:
**normalizar na entrada**. O Form Request tem um gancho que roda antes das
regras:

```php title="app/Http/Requests/StoreLivroRequest.php" numbered
protected function prepareForValidation(): void
{
    $this->merge([
        'isbn' => $this->filled('isbn')
            ? preg_replace('/\D/', '', $this->input('isbn'))
            : null,
        'titulo' => $this->filled('titulo')
            ? $this->normalizarEspacos($this->input('titulo'))
            : $this->input('titulo'),
    ]);
}

private function normalizarEspacos(string $texto): string
{
    return trim(preg_replace('/\s+/u', ' ', $texto));
}
```

`\D` é "qualquer coisa que não seja dígito". Hífen, espaço e ponto saem, e
os três ISBNs viram o mesmo — que o `unique` então recusa.

:::http title="O segundo Dom Casmurro, agora"
POST /api/livros
Content-Type: application/json

{"titulo": "Dom  Casmurro", "autor": "Machado de Assis",
 "assunto": "literatura", "isbn": "978-85-359-1066-7"}
---
422 Unprocessable Content
Content-Type: application/json

{
  "message": "The isbn has already been taken.",
  "errors": {
    "isbn": ["The isbn has already been taken."]
  }
}
:::

Duas coisas nessa resposta. A mensagem está em inglês — a correção vem daqui
a duas seções. E o `422` voltou **com o ISBN normalizado** conferido: o
banco nunca viu o hífen.

:::key
A ordem é **normalizar, depois conferir, depois gravar**. Conferir antes de
normalizar deixa passar variações; normalizar depois de gravar deixa o banco
sujo e obriga toda consulta a limpar de novo.

E o dado que o banco guarda é sempre o normalizado. A formatação com hífens,
se a tela quiser mostrar, é trabalho da saída — do capítulo
@cap:api-resources.
:::

Os três registros que já estão lá não somem sozinhos. Eles precisam de uma
migração de dados que normalize a coluna, junte os exemplares no registro
que sobrar e apague os outros — e essa migração precisa ser conferida com a
Vera antes de rodar, porque "qual dos três fica" é uma pergunta de negócio.

## `sometimes`, `nullable` e o `PATCH` que apaga campo

Duas palavras que parecem sinônimas e que produzem, quando confundidas, o
defeito do capítulo anterior.

**`nullable`** diz: o campo pode vir com o valor `null`. Não diz nada sobre
o campo **não vir**.

**`sometimes`** diz: só aplique as outras regras **se o campo estiver
presente** no corpo.

| Corpo | `['required']` | `['nullable']` | `['sometimes', 'required']` |
|---|---|---|---|
| `{}` | falha | passa | passa |
| `{"autor": null}` | falha | passa | falha |
| `{"autor": ""}` | falha | passa, vira `null` | falha |
| `{"autor": "Machado"}` | passa | passa | passa |

Tabela: A terceira coluna é o `PATCH` correto: campo ausente é ignorado;
campo presente precisa ser válido. A segunda coluna é o `PATCH` que apaga o
autor quando o formulário manda o campo vazio.

A linha do `""` surpreende. O Laravel tem um middleware global que
**converte string vazia em `null`** antes de a validação rodar, e por isso
`nullable` aceita uma string vazia e grava nulo. É conveniente num formulário
HTML, e é o caminho exato pelo qual um campo obrigatório some.

Com isso, o `update` do capítulo anterior ganha a sua própria classe:

```php title="app/Http/Requests/UpdateLivroRequest.php" numbered
class UpdateLivroRequest extends FormRequest
{
    public function rules(): array
    {
        $obrigatorio = $this->isMethod('PUT')
            ? 'required'
            : 'sometimes';

        return [
            'titulo' => [$obrigatorio, 'string', 'max:200'],
            'autor' => [$obrigatorio, 'string', 'max:150'],
            'assunto' => [$obrigatorio, 'string', 'max:40'],
            'isbn' => [
                'sometimes', 'nullable', 'digits:13',
                Rule::unique('livros', 'isbn')
                    ->ignore($this->route('livro')),
            ],
            'ano' => ['sometimes', 'nullable', 'integer'],
        ];
    }
}
```

O `$this->route('livro')` é o model que o binding já carregou — o Form
Request enxerga os parâmetros da rota. E o `ignore` resolve o defeito
clássico do `unique` na edição.

:::pitfall
Sem o `ignore`, editar o título de um livro e reenviar o mesmo ISBN produz
`422`: "The isbn has already been taken". Tomado **pelo próprio livro**.

É o erro que todo projeto Laravel encontra na primeira tela de edição, e a
correção de pressa é tirar o `unique` do `update`. Aí o `PATCH` passa a
aceitar o ISBN de outro livro, e a duplicata que este capítulo começou
consertando volta pela outra porta.
:::

## Regra própria, e quando ela já existe

As regras prontas do Laravel cobrem mais do que parece, e vale procurar
antes de escrever:

```php
'estado' => ['required', Rule::enum(StatusExemplar::class)],
'exemplar_id' => ['required', 'integer', 'exists:exemplares,id'],
'devolver_ate' => ['required', 'date', 'after:today'],
'capa' => ['nullable', 'image', 'max:2048'],
```

O `Rule::enum` é o mais valioso dos quatro: ele usa o enum do capítulo
@cap:enums-datas-e-valores como fonte da verdade. Se um caso novo for
acrescentado ao enum, a validação passa a aceitá-lo sem ninguém lembrar de
atualizar uma lista de strings.

Quando nenhuma regra pronta serve, uma classe resolve. O ISBN tem dígito
verificador — o último número é calculado a partir dos outros doze —, e
treze dígitos quaisquer não são um ISBN:

```php title="app/Rules/Isbn13.php" numbered
<?php

declare(strict_types=1);

namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\ValidationRule;

class Isbn13 implements ValidationRule
{
    public function validate(
        string $atributo,
        mixed $valor,
        Closure $falhar,
    ): void {
        if (!preg_match('/^\d{13}$/', (string) $valor)) {
            $falhar('O :attribute precisa ter 13 dígitos.');
            return;
        }

        $soma = 0;

        foreach (str_split(substr($valor, 0, 12)) as $i => $d) {
            $soma += (int) $d * ($i % 2 === 0 ? 1 : 3);
        }

        $verificador = (10 - $soma % 10) % 10;

        if ($verificador !== (int) $valor[12]) {
            $falhar('O :attribute não é um ISBN válido.');
        }
    }
}
```

```php
'isbn' => ['nullable', new Isbn13(), 'unique:livros,isbn'],
```

A regra é uma classe pequena, testável sozinha e reaproveitada nos dois
Form Requests. Repare que ela **não consulta o banco**: conferir se o ISBN
existe no acervo é trabalho do `unique`, e misturar as duas coisas
produziria uma regra que só funciona com banco ligado.

:::note
O `:attribute` é um marcador que o Laravel troca pelo nome do campo. O nome
pode ser traduzido, o que leva à próxima seção.
:::

## `422`, `errors` e o campo que o cliente destaca

A resposta de erro de validação tem um formato fixo, e é o formato que o
aplicativo do leitor vai ler:

```json
{
  "message": "O título é obrigatório. (e mais 1 erro)",
  "errors": {
    "titulo": ["O título é obrigatório."],
    "isbn": ["O ISBN não é um ISBN válido."]
  }
}
```

A chave `errors` é um mapa de **nome do campo** para **lista de mensagens**.
É por ela que a tela sabe qual caixa pintar de vermelho — e é por isso que o
nome do campo é contrato: renomear `titulo` para `title` quebra o destaque
em todo cliente publicado.

As mensagens em português vêm de dois lugares. O idioma padrão do projeto
vai no `.env`, e o arquivo de tradução é publicado uma vez:

```text
$ php artisan lang:publish
```

E o nome do campo, que aparece dentro da mensagem, o Form Request declara:

```php title="app/Http/Requests/StoreLivroRequest.php" numbered
public function attributes(): array
{
    return [
        'titulo' => 'título',
        'isbn' => 'ISBN',
    ];
}

public function messages(): array
{
    return [
        'isbn.unique' => 'Este ISBN já está no acervo.',
    ];
}
```

A mensagem do `unique` merece texto próprio porque ela é a única que pede
uma ação diferente: a pessoa não precisa corrigir o que digitou; precisa
procurar o livro que já existe.

:::pitfall
O formato do `422` do Laravel é **diferente** do formato dos outros erros
que a API devolve hoje. O `abort(409, ...)` do capítulo anterior produz
`{"message": "..."}`, sem `errors`; o `404` produz outro formato; um `500`,
um terceiro.

Três formatos de erro na mesma API é o assunto inteiro do capítulo
@cap:erros-padronizados. Por enquanto, anote: o cliente vai ter que tratar
cada um de um jeito, e isso vai ser consertado.
:::

## O empréstimo, e o que **não** entra no Form Request

```php title="app/Http/Requests/RealizarEmprestimoRequest.php" numbered
class RealizarEmprestimoRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'exemplar_id' => [
                'required', 'integer', 'exists:exemplares,id',
            ],
            'leitor_id' => [
                'required', 'integer', 'exists:leitores,id',
            ],
        ];
    }
}
```

É tudo. Nenhuma das onze regras da Vera está aqui, e a tentação de pôr é
enorme — o Form Request tem acesso ao banco, e a regra
"exemplar precisa estar disponível" cabe numa closure de três linhas.

Três motivos para resistir.

**A conferência seria falsa.** O Form Request roda antes do controller,
fora da transação e sem trava na linha. Entre a validação dizer "disponível"
e o empréstimo ser gravado, a Neide pode ter emprestado o mesmo exemplar no
balcão. A conferência que vale é a que roda **dentro** da transação, com o
`lockForUpdate` do capítulo anterior.

**O status seria errado.** Uma regra de validação que falha devolve `422`,
que diz "corrija o seu pedido". Mas o pedido está certo — o exemplar existe,
o número é inteiro. O mundo é que não deixa. É `409`.

**A regra ficaria presa ao HTTP.** O comando `biblioteca:multas`, o painel
Blade e um script de importação também emprestam livros. Se a regra morar
no Form Request, cada um desses caminhos precisa reescrevê-la.

:::key
O `exists` fica no Form Request porque ele responde "esse identificador
aponta para alguma coisa?" — é formato, com um pé no banco. O "essa coisa
pode ser emprestada agora?" fica fora, porque a resposta muda a cada
segundo e precisa de trava para ser verdade.

A fronteira é incômoda, e é incômoda em todo framework. Na dúvida, deixe a
conferência no service: ela vai ser redundante às vezes, mas nunca vai ser
falsa.
:::

## Validar também o que sai

Uma nota curta, porque a ferramenta chega no próximo capítulo. Validar a
entrada protege o banco do cliente; ninguém está protegendo o cliente do
banco.

O `LivroController::show` devolve o model inteiro. Se amanhã alguém
acrescentar uma coluna `observacao_interna` à tabela, ela sai na resposta
sem que nenhuma linha do controller mude. A entrada tem uma lista de
permissão — o `rules()`. A saída ainda não tem nenhuma.

:::note Na sua carreira
Validação é o primeiro lugar em que uma pessoa revisora experiente olha num
projeto novo, porque diz muito em pouco espaço.

Regras no controller dizem que o projeto cresceu sem pausa para arrumar.
`$request->all()` diz que alguém confia no cliente. `unique` sem `ignore` no
`update` diz que ninguém testou a edição. E regra de negócio dentro do Form
Request diz que a equipe ainda não separou "formato" de "estado" — que é a
conversa mais produtiva que você pode puxar numa primeira semana.

Nenhuma dessas observações exige conhecer o domínio. É por isso que elas
são uma boa porta de entrada para contribuir num projeto que você ainda
não entende.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/Http/Requests/
    StoreLivroRequest.php         # regras + normalização
    UpdateLivroRequest.php        # PUT × PATCH, unique com ignore
    RealizarEmprestimoRequest.php # só formato
  app/Rules/
    Isbn13.php                    # dígito verificador
  app/Http/Controllers/
    LivroController.php           # store e update com 4 linhas
  lang/pt_BR/validation.php
:::

:::summary
- Validação responde se o pedido está bem formado; regra de negócio, se o
  mundo permite. A primeira dá `422`; a segunda, `409`.
- O teste da fronteira: se o mesmo corpo, daqui a cinco minutos, pode ter
  outra resposta, não é validação.
- Form Request é uma classe por tipo de pedido; o controller a recebe por
  tipo, e a validação roda antes do método.
- `validated()` devolve só o que tem regra; `all()` depois de Form Request
  desfaz a proteção.
- `prepareForValidation` normaliza antes de conferir; o banco guarda sempre
  a forma normalizada.
- `nullable` aceita `null`; `sometimes` ignora o ausente. `PATCH` pede
  `sometimes`.
- `unique` no `update` precisa de `ignore`, ou acusa o próprio registro.
- `Rule::enum` usa o enum como fonte da verdade; regra própria é uma classe
  pequena e sem banco.
- `errors` é um mapa de campo para mensagens, e o nome do campo é contrato.
:::

:::checkpoint
Você move as regras de formato para Form Requests, normaliza a entrada
antes de conferir, implementa `PATCH` que não apaga campo ausente, e sabe
explicar a uma pessoa do time por que "exemplar disponível" não é uma regra
de validação.
:::

:::exercise level=1
Classifique cada conferência como **validação** (Form Request, `422`) ou
**regra de negócio** (service, `409`):

1. O e-mail do leitor tem formato de e-mail.
2. O leitor não tem multa acima de cinco reais.
3. O `exemplar_id` existe na tabela.
4. O exemplar não está em restauro.
5. A data de devolução informada é posterior a hoje.
6. O leitor não está com três livros.

:::answer
1. Validação. O formato não muda com o tempo.
2. Regra de negócio. A multa pode ser paga daqui a cinco minutos.
3. Validação. É uma conferência de que o identificador aponta para algo —
   formato, com um pé no banco.
4. Regra de negócio. O estado do exemplar muda, e a conferência precisa de
   trava para ser verdade.
5. Validação. "Depois de hoje" depende do relógio, mas não do estado de
   nenhum registro: o mesmo corpo, amanhã, só pode passar a falhar, e pelo
   motivo certo.
6. Regra de negócio. É o caso clássico: o leitor devolve um livro e o
   mesmo pedido passa.

O item 5 é o que gera discussão, e a discussão é boa. O teste dos cinco
minutos ajuda: o que muda a resposta ali é o calendário, não uma ação de
outra pessoa no sistema.
:::

:::exercise level=2
Escreva o `prepareForValidation` e as regras de um `StoreLeitorRequest` com
`nome`, `documento` (CPF) e `telefone`. O CPF chega com ou sem pontos e
hífen; o telefone, com ou sem parênteses. O banco guarda só dígitos, e o
documento é único.

:::answer
```php title="app/Http/Requests/StoreLeitorRequest.php" numbered
class StoreLeitorRequest extends FormRequest
{
    protected function prepareForValidation(): void
    {
        $this->merge([
            'documento' => $this->soDigitos('documento'),
            'telefone' => $this->soDigitos('telefone'),
            'nome' => $this->filled('nome')
                ? trim(preg_replace(
                    '/\s+/u', ' ', $this->input('nome'),
                ))
                : null,
        ]);
    }

    public function rules(): array
    {
        return [
            'nome' => ['required', 'string', 'max:150'],
            'documento' => [
                'required', 'digits:11',
                'unique:leitores,documento',
            ],
            'telefone' => ['nullable', 'digits_between:10,11'],
        ];
    }

    private function soDigitos(string $campo): ?string
    {
        return $this->filled($campo)
            ? preg_replace('/\D/', '', $this->input($campo))
            : null;
    }
}
```

`digits:11` confere o tamanho e que só há dígitos, mas não confere o dígito
verificador do CPF — para isso, uma regra própria como a `Isbn13`.

E um detalhe que costuma escapar: o `soDigitos` devolve `null` quando o
campo não veio, e não string vazia. Assim o `required` do documento falha
com a mensagem certa, em vez de falhar no `digits:11` com uma mensagem que
confunde quem preencheu.
:::

:::exercise level=3
Uma pessoa do time propôs esta regra para o `RealizarEmprestimoRequest`,
argumentando que "assim o erro aparece no campo certo da tela":

```php
'exemplar_id' => [
    'required',
    'exists:exemplares,id',
    function ($atributo, $valor, $falhar) {
        $e = Exemplar::find($valor);
        if ($e->estado !== StatusExemplar::Bom) {
            $falhar('Exemplar indisponível.');
        }
    },
],
```

O argumento tem mérito. Escreva a resposta de revisão: o que está certo na
motivação, os dois defeitos concretos, e como atender ao desejo de destacar
o campo sem mover a regra.

:::answer
**O que está certo.** A motivação é legítima: o aplicativo sabe destacar um
campo a partir do `errors`, e um `409` com uma frase solta obriga a tela a
decidir sozinha onde mostrar. A pessoa está pensando no cliente, que é o
que a API existe para servir.

**Primeiro defeito: a conferência não é verdade.** A closure roda antes da
transação e sem trava. Entre ela dizer "disponível" e o `create`, o balcão
pode ter emprestado o exemplar. A regra passaria a dar uma falsa sensação de
segurança — e a conferência real, dentro da transação, continuaria
necessária, agora duplicada.

**Segundo defeito: o status mente.** O cliente recebe `422`, que manda
corrigir o pedido. O pedido está correto. Um aplicativo que trata `422`
limpando o campo e pedindo outro valor vai mostrar à leitora que ela
"digitou errado" o livro que está segurando na mão.

Há um terceiro, menor: se `exists` falhar, a closure ainda roda, `find`
devolve `null`, e `$e->estado` explode com erro de propriedade em nulo. A
ordem das regras não interrompe a lista por padrão.

**Como atender ao desejo.** A resposta de `409` pode carregar o campo. O
capítulo @cap:erros-padronizados define o formato único de erro da API, e
ele tem espaço para isso:

```json
{
  "tipo": "exemplar-indisponivel",
  "mensagem": "O exemplar 2117 está emprestado.",
  "campos": {"exemplar_id": ["Exemplar indisponível."]}
}
```

A tela destaca o campo, o status diz a verdade, e a regra continua morando
onde tem trava. A revisão termina com uma proposta, não com uma recusa.
:::
