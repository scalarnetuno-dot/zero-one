---
title: "API Resources"
number: 15
slug: api-resources
part: p4
kicker: "A coluna foi criada para a equipe anotar o que não dizia na frente do leitor. Durante onze dias, o leitor leu."
goal: >-
  Separar o formato da resposta da estrutura da tabela, decidir campo a
  campo o que sai, carregar relacionamentos sem voltar ao N+1, e tratar a
  resposta como um contrato que outra pessoa já está usando.
---

:::story Onze dias
A mensagem chegou pelo formulário de contato do aplicativo, numa
segunda-feira.

> Bom dia. Queria saber quem escreveu no meu cadastro que eu "devolve
> molhado, conferir sempre". Não devolvi molhado. Foi a chuva de dezembro e
> eu avisei. Att., Rosângela.

Tainá leu em voz alta. Dedé abriu o aplicativo no celular dela, entrou no
perfil, e lá estava, logo abaixo do telefone, num campo que a tela
mostrava sem rótulo nenhum:

```text
devolve molhado, conferir sempre
```

— Isso é a `observacao_interna` — disse ele. — O Cléber criou a coluna na
semana retrasada, pra Vera anotar essas coisas.

— E por que aparece no aplicativo?

— Porque o `show` devolve o model. E o model tem a coluna.

— Desde quando?

Dedé olhou a data da migration.

— Onze dias.

Vera, que estava na porta, perguntou quantas pessoas tinham anotação.

— Trinta e oito.

— Então são trinta e oito ligações — disse ela. — A da Rosângela eu faço
pessoalmente.
:::

## O model não é o JSON

Até aqui, os controllers devolvem o model direto:

```php
public function show(Leitor $leitor)
{
    return $leitor;
}
```

O Laravel sabe transformar um model em JSON, e faz isso incluindo **todas
as colunas da tabela**. É conveniente no primeiro dia e é uma armadilha a
partir do segundo, porque amarra duas coisas que mudam por motivos
diferentes:

**A tabela muda por motivo interno.** A equipe precisa de uma coluna para
anotações, de uma coluna para controlar importação, de um campo novo para
um relatório. Essas mudanças são decididas pela equipe, na hora que ela
quiser.

**A resposta é um contrato externo.** O aplicativo do leitor foi publicado
na loja com um formato em mente, e a versão antiga dele continua instalada
em celulares que não atualizam há meses. O formato da resposta só pode
mudar com aviso, e às vezes não pode mudar.

Quando o JSON é o retrato da tabela, **toda migration vira uma mudança de
contrato**, sem que ninguém perceba. A `observacao_interna` foi uma migration
de três linhas, revisada e aprovada. Ninguém pensou em API, porque não
havia nada na alteração que dissesse "API".

:::key
A resposta de uma API é uma **lista de permissão**, escrita campo a campo.
O que não está na lista não sai — inclusive o que for criado depois.

É a mesma lógica do `rules()` do capítulo anterior, na outra direção. A
entrada tem uma lista do que pode entrar; a saída precisa de uma lista do
que pode sair.
:::

Existe o `$hidden` no model, que esconde colunas da serialização. Ele
resolve o caso da senha, e é o primeiro que todo mundo aprende. Mas é uma
**lista de proibição**: ele esconde o que você lembrou de esconder. A
coluna criada na semana que vem não está nele.

## `JsonResource`

```text
$ php artisan make:resource LeitorResource
```

```php title="app/Http/Resources/LeitorResource.php" numbered
<?php

declare(strict_types=1);

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class LeitorResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'nome' => $this->nome,
            'telefone' => $this->telefone,
            'membro_desde' => $this->created_at->toDateString(),
        ];
    }
}
```

```php title="app/Http/Controllers/LeitorController.php" numbered
public function show(Leitor $leitor)
{
    return new LeitorResource($leitor);
}
```

:::http title="O mesmo leitor, agora com lista de permissão"
GET /api/leitores/47
---
200 OK
Content-Type: application/json

{
  "data": {
    "id": 47,
    "nome": "Rosângela Pires",
    "telefone": "21987654321",
    "membro_desde": "2014-03-11"
  }
}
:::

Quatro campos. A `observacao_interna` não está, o `documento` não está, o
`perfil` não está, o `updated_at` não está. E a coluna que alguém criar no
mês que vem também não vai estar.

Dentro do `toArray`, `$this->id` lê a propriedade do model que o resource
envolve. O resource é um **invólucro**: ele repassa as leituras para o
model e decide o que devolver.

Repare no `membro_desde`. A tabela tem `created_at`, que é um nome de
banco — diz quando a linha foi inserida. O contrato tem `membro_desde`, que
é um nome de domínio — diz o que aquilo significa para o leitor. No dia em
que os cadastros antigos forem importados do Sistema com a data original, a
coluna vai mudar e o nome do contrato continua fazendo sentido.

### O envelope `data`

O resource devolve o objeto dentro de uma chave `data`. Parece cerimônia, e
é uma decisão com motivo: sobra espaço no nível de cima para coisas que não
são o recurso — a paginação, os links, avisos de depreciação.

```json
{
  "data": [ ... ],
  "links": { "next": "..." },
  "meta": { "total": 4031 }
}
```

Uma API que começa sem envelope e precisa acrescentar metadados depois tem
duas escolhas ruins: quebrar todo cliente, mudando o formato da raiz; ou
enfiar os metadados em cabeçalhos HTTP, onde ninguém procura. Com o
envelope desde o primeiro dia, a decisão não precisa ser tomada.

## Coleções

Para uma lista, o mesmo resource, aplicado a cada item:

```php title="app/Http/Controllers/LivroController.php" numbered
public function index()
{
    $livros = Livro::orderBy('titulo')->paginate(20);

    return LivroResource::collection($livros);
}
```

Quando o que chega ao `collection` é um paginador, o resource monta o
envelope completo sozinho — `data`, `links` e `meta` —, com os números que
o paginador calculou. O capítulo @cap:paginacao-filtros-e-buscas trata do
paginador em si.

Existe também a classe `ResourceCollection`, para quando a coleção precisa
de campos próprios no nível de cima. Na maior parte dos casos, o
`::collection` basta, e é um arquivo a menos.

## `whenLoaded`: o relacionamento que só aparece se foi carregado

O `LivroResource` precisa mostrar os autores e a contagem de exemplares
disponíveis. A primeira versão costuma ser esta:

```php
'autores' => $this->autores->pluck('nome'),
```

E é o N+1 da serialização que o capítulo @cap:relacionamentos avisou:
`$this->autores` dispara uma consulta **para cada livro**, no momento em que
a resposta é montada, depois de o controller ter terminado.

A versão certa pergunta antes de tocar:

```php title="app/Http/Resources/LivroResource.php" numbered
class LivroResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'titulo' => $this->titulo,
            'isbn' => $this->isbn,
            'ano' => $this->ano,
            'assunto' => $this->assunto,
            'autores' => AutorResource::collection(
                $this->whenLoaded('autores'),
            ),
            'exemplares_disponiveis' => $this->whenCounted(
                'exemplaresDisponiveis',
            ),
        ];
    }
}
```

`whenLoaded('autores')` confere se o relacionamento **já foi carregado** —
por `with` ou `load`. Se foi, entrega. Se não foi, a chave inteira **some da
resposta**, sem consulta. O `whenCounted` faz o mesmo para o `withCount`.

A consequência é que **quem decide o que vem é o controller**, pela consulta
que ele fez:

```php
// na listagem: autores e contagem
Livro::with('autores')
    ->withCount(['exemplares as exemplares_disponiveis_count'
        => fn ($q) => $q->where('estado', StatusExemplar::Bom)])
    ->paginate(20);

// na busca rápida do balcão: só o livro
Livro::where('isbn', $isbn)->first();
```

O resource é o mesmo nos dois. A resposta muda de tamanho conforme o que o
controller carregou, e nunca por uma consulta escondida.

:::pitfall
`whenLoaded` resolve o N+1, e cria uma forma sutil de inconsistência: o
mesmo recurso, em dois endpoints, vem com campos diferentes. Um cliente que
programou contra a listagem espera `autores`; na busca rápida, a chave não
existe.

Isso é aceitável se for **documentado** — "a busca por ISBN não traz
autores" — e é um defeito se for acidental. Na dúvida, decida por endpoint
o que vem, escreva na documentação do capítulo
@cap:documentacao-da-api, e teste. O capítulo
@cap:testes-de-feature-http-e-banco tem um teste para exatamente isso.
:::

Com o `preventLazyLoading` do capítulo @cap:relacionamentos ligado, tocar
`$this->autores` sem `whenLoaded` num relacionamento não carregado lança
exceção em desenvolvimento. Os dois mecanismos se completam: um protege a
resposta, o outro avisa quando alguém esquece.

## O campo que não pode sair, nunca

Nem todo campo é público para todo mundo. O leitor pode ver o próprio
telefone e não pode ver o telefone de outro leitor. A bibliotecária vê os
dois, e vê também o documento.

O `when` inclui um campo sob condição:

```php title="app/Http/Resources/LeitorResource.php" numbered
public function toArray(Request $request): array
{
    $proprio = $request->user()?->leitor_id === $this->id;
    $equipe = $request->user()?->ehEquipe() ?? false;

    return [
        'id' => $this->id,
        'nome' => $this->nome,
        'telefone' => $this->when(
            $proprio || $equipe,
            $this->telefone,
        ),
        'documento' => $this->when($equipe, $this->documento),
        'membro_desde' => $this->created_at->toDateString(),
    ];
}
```

O `$request->user()` ainda devolve `null` — a API não tem login até o
capítulo @cap:autenticacao. O `?->` garante que, por enquanto, ninguém é
"próprio" nem "equipe", e os dois campos simplesmente não saem. Quando o
login chegar, o resource já está pronto para ele.

:::key
Existem três categorias de campo, e cada uma pede um tratamento:

**Público:** sai sempre. Título, ano, nome.

**Condicional:** sai para quem tem direito. Telefone, documento. Vai no
`when`.

**Interno:** não sai nunca, para ninguém, por esta API.
`observacao_interna`, `senha`, `importado_do_sistema`. Não aparece no
resource — e o teste do capítulo @cap:testes-de-feature-http-e-banco garante
que continua não aparecendo.
:::

A `observacao_interna` não pertence nem ao segundo grupo. A equipe vê a
anotação no **painel Blade**, que é outra porta, com outra tela e outra
permissão. A API do aplicativo nunca precisa dela, e por isso ela não
existe para a API.

## Um formato, a API inteira

O envelope, os nomes, as datas: tudo isso vira convenção da API, e vale
escrever uma vez.

| Decisão | Escolha da Casa Amarela |
|---|---|
| nomes de campo | `snake_case`, em português |
| datas | `AAAA-MM-DD` para dia; ISO 8601 com fuso para instante |
| dinheiro | objeto `{centavos, formatado}` |
| enum | o `value`, nunca o `name` |
| ausência | chave presente com `null`, exceto em `whenLoaded` |

Tabela: Cinco decisões que a equipe toma uma vez e que o cliente aprende
uma vez. A pior escolha em cada linha é não escolher, e deixar cada
resource decidir.

O dinheiro merece uma linha de código, porque o objeto `Dinheiro` do
capítulo @cap:enums-datas-e-valores não sabe virar JSON sozinho:

```php title="app/Http/Resources/EmprestimoResource.php" numbered
public function toArray(Request $request): array
{
    return [
        'id' => $this->id,
        'status' => $this->status->value,
        'retirado_em' => $this->retirado_em->toIso8601String(),
        'devolver_ate' => $this->devolver_ate->toDateString(),
        'devolvido_em' => $this->devolvido_em?->toIso8601String(),
        'em_atraso' => $this->emAtraso(),
        'multa' => $this->when(
            $this->multa_em_centavos !== null,
            fn () => [
                'centavos' => $this->multa_em_centavos->centavos,
                'formatado' => $this->multa_em_centavos->formatado(),
            ],
        ),
        'exemplar' => new ExemplarResource(
            $this->whenLoaded('exemplar'),
        ),
    ];
}
```

O `em_atraso` é o caso do exercício do capítulo
@cap:enums-datas-e-valores: não é uma coluna, é uma conclusão calculada
pelo model. Para o cliente, não existe diferença — ele recebe um booleano e
não precisa saber se foi lido ou calculado. É a vantagem de ter o contrato
separado da tabela, vista pelo lado bom.

O dinheiro sai com as duas formas. O aplicativo usa `centavos` para somar e
`formatado` para mostrar, e nunca precisa formatar moeda em JavaScript —
que é o lugar onde a vírgula e o ponto costumam trocar de lugar.

## Mudar a resposta sem quebrar quem já usa

O aplicativo da versão 1.0 está instalado. A equipe decidiu que `assunto`,
que hoje é texto, vai virar um objeto com `id` e `nome`. O que fazer?

**Acrescentar é seguro.** Um campo novo não quebra nenhum cliente bem
escrito, porque cliente bem escrito ignora o que não conhece.

**Mudar o tipo ou o nome quebra.** O aplicativo 1.0 espera texto em
`assunto` e vai receber um objeto.

A saída é **acrescentar ao lado, depois retirar**:

```php
'assunto' => $this->assunto->nome,       // mantém, marcado para sair
'assunto_detalhado' => new AssuntoResource($this->assunto),
```

O campo antigo continua; o novo aparece ao lado. A documentação marca o
antigo como depreciado, com data. Quando o aplicativo 1.0 deixar de ter
usuários — e isso se mede, não se adivinha —, o campo antigo sai.

Versionar a API inteira (`/api/v2/livros`) por causa de um campo é
desproporcional: duplica rotas, controllers e testes para resolver um
problema que uma chave a mais resolve. O capítulo
@cap:documentacao-da-api volta a isso, com o plano completo.

:::note Na sua carreira
O vazamento de dado mais comum em API não é ataque: é um `return $model`
e uma migration feita meses depois por outra pessoa.

Ele não aparece em revisão, porque a migration não toca na API e o
controller não mudou. Não aparece em teste manual, porque ninguém olha o
JSON inteiro. Aparece quando uma Rosângela lê o que escreveram sobre ela.

Se você entrar num projeto que devolve model cru, o primeiro resource que
você escrever vai parecer burocracia para quem está lá. Escreva mesmo
assim, e escreva o teste que confere que a coluna interna não sai. É o tipo
de contribuição que ninguém agradece até o dia em que ela evitou uma
ligação.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/Http/Resources/
    LivroResource.php        # whenLoaded, whenCounted
    AutorResource.php
    ExemplarResource.php
    LeitorResource.php       # telefone e documento condicionais
    EmprestimoResource.php   # dinheiro como objeto, em_atraso
  app/Http/Controllers/      # nenhum devolve model cru
:::

:::summary
- O model é o esquema interno; o JSON é um contrato externo. Os dois mudam
  por motivos diferentes e precisam de código diferente.
- Uma resposta é uma lista de permissão campo a campo; `$hidden` é uma lista
  de proibição e não protege o que for criado depois.
- `JsonResource::toArray` declara o que sai; o envelope `data` deixa espaço
  para `links` e `meta`.
- `::collection` com um paginador monta o envelope completo sozinho.
- `whenLoaded` e `whenCounted` incluem o relacionamento só se ele já foi
  carregado; quem decide é a consulta do controller.
- Campos são públicos, condicionais (`when`) ou internos — e os internos não
  aparecem no resource.
- Convenções de formato — datas, dinheiro, enum, ausência — são decididas
  uma vez para a API inteira.
- Acrescentar campo é seguro; renomear ou mudar o tipo quebra. A saída é
  acrescentar ao lado e retirar depois.
:::

:::checkpoint
Nenhum controller da API devolve model cru. Você escreve resources com
campos públicos, condicionais e ausentes por decisão, carrega
relacionamentos sem N+1 na serialização, e sabe planejar a mudança de um
campo sem quebrar o aplicativo que já está instalado.
:::

:::exercise level=1
Para cada coluna da tabela `exemplares`, diga se ela entra no
`ExemplarResource` como pública, condicional (para quem?) ou não entra:

`id`, `livro_id`, `tombo`, `estado`, `adquirido_em`, `preco_de_compra`,
`fornecedor`, `created_at`, `updated_at`.

:::answer
- `id`: pública. É o identificador que o cliente usa para as outras rotas.
- `livro_id`: não entra como número solto. O livro vem como objeto
  aninhado com `whenLoaded('livro')`, ou por um link. Número de chave
  estrangeira é detalhe do esquema.
- `tombo`: pública. É o número colado no livro, e a Vera fala dele.
- `estado`: pública, pelo `value` do enum. É o que o leitor quer saber.
- `adquirido_em`: condicional, para a equipe. Ao leitor não interessa.
- `preco_de_compra`: não entra. É informação de gestão, e o painel mostra.
- `fornecedor`: não entra, pelo mesmo motivo.
- `created_at`, `updated_at`: não entram. São datas de controle do banco;
  se algum dia fizer sentido expor "cadastrado em", entra com nome de
  domínio.

O `livro_id` é o que mais divide opiniões. Expor o número não é errado, e
muitas APIs fazem. O ponto é decidir e ser consistente: se `exemplar` traz
`livro_id`, `emprestimo` deveria trazer `exemplar_id` pelo mesmo critério.
:::

:::exercise level=2
Esta listagem de empréstimos em atraso ficou lenta depois que o resource
ganhou dois campos. Encontre o problema e corrija sem mudar o formato da
resposta.

```php
public function atrasados()
{
    return EmprestimoResource::collection(
        Emprestimo::emAtraso()->get()
    );
}
```

```php
// dentro do EmprestimoResource
'leitor' => $this->leitor->nome,
'livro' => $this->exemplar->livro->titulo,
```

:::answer
Os dois campos tocam relacionamentos sem `whenLoaded`, e o controller não
carregou nada. Para 60 empréstimos atrasados: uma consulta da lista, 60 de
leitores, 60 de exemplares e 60 de livros — 181.

A correção tem duas metades, e as duas são necessárias.

No controller, carregar:

```php
Emprestimo::emAtraso()
    ->with(['leitor', 'exemplar.livro'])
    ->get()
```

No resource, proteger:

```php
'leitor' => $this->whenLoaded(
    'leitor',
    fn () => $this->leitor->nome,
),
'livro' => $this->whenLoaded(
    'exemplar',
    fn () => $this->exemplar->livro->titulo,
),
```

Só o controller resolve hoje; só o resource impede que o problema volte no
próximo endpoint que usar o mesmo resource sem carregar. A segunda forma do
`whenLoaded`, com uma função, serve para quando o valor é derivado do
relacionamento e não o relacionamento inteiro.

O formato não mudou: `leitor` continua sendo um texto e `livro` também.
:::

:::exercise level=3
O aplicativo do leitor, versão 1.0, lê `devolver_ate` como texto no formato
`DD/MM/AAAA` — um erro da primeira versão da API, que formatava a data para
exibição. A equipe quer trocar pelo formato `AAAA-MM-DD` da convenção.

Existem 1.300 instalações da versão 1.0. A 1.1, que já sabe ler os dois
formatos, está na loja há três semanas.

Escreva o plano: o que muda no resource hoje, como decidir quando terminar a
transição, e o que você não faria.

:::answer
**Hoje: acrescentar ao lado.**

```php
'devolver_ate' => $this->devolver_ate->format('d/m/Y'),
'devolver_ate_iso' => $this->devolver_ate->toDateString(),
```

O campo antigo continua idêntico; o novo segue a convenção. A versão 1.1 é
atualizada para ler `devolver_ate_iso` quando ele existir.

**Decidir quando terminar: medir.** O aplicativo manda a própria versão num
cabeçalho — se não manda, esse é o primeiro ajuste, na 1.2. Com o log
estruturado do capítulo @cap:cache-logs-e-medicao, conta-se quantas
requisições por dia ainda vêm da 1.0. A transição termina quando o número
for zero, ou pequeno o bastante para que a biblioteca aceite avisar as
pessoas pessoalmente.

**O que acontece depois, em dois passos.** Primeiro, `devolver_ate` passa
a ter o formato novo e `devolver_ate_iso` continua existindo, marcado como
depreciado. Depois, numa versão futura, `devolver_ate_iso` sai. É
cerimônia, e é o que faz o nome certo terminar no campo certo.

**O que não fazer.**

Trocar o formato de `devolver_ate` hoje: 1.300 aplicativos passam a mostrar
data errada ou quebrar.

Criar `/api/v2`: duplica a API inteira por causa de um campo.

Decidir pelo cabeçalho de versão **dentro do resource**, devolvendo formatos
diferentes para cada cliente: funciona, e cria um resource com `if` por
versão que ninguém vai ter coragem de apagar. Um campo a mais é mais
simples, mais visível e mais fácil de retirar.
:::
